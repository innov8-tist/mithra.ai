import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent.retriver_service import Retriver
from agent.pdf_image_process import process_documents
from agent.vision_magic_fill import analyze_with_gemini_vision
from agent.structured_data_filling import extract_form_data
import google.generativeai as genai
import shutil
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent / "user_details"
UPLOAD_DIR.mkdir(exist_ok=True)

PUBLIC_DIR = Path(__file__).parent / "public"
PUBLIC_DIR.mkdir(exist_ok=True)


class QueryRequest(BaseModel):
    query: str


class AutofillRequest(BaseModel):
    query: str
    autofill: bool = True


class BrowserRequest(BaseModel):
    url: str
    headless: bool = False


class LiveQueryRequest(BaseModel):
    screenshot_b64: str
    query: str


class VoiceTranscribeRequest(BaseModel):
    audio_base64: str
    language_code: str = "auto"  # Auto-detect language


class VisionMagicFillRequest(BaseModel):
    screenshot_b64: str
    fields: list[dict]
    url: str


@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(..., description="Upload multiple files")):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    saved_files = []
    processable_files = []
    supported_extensions = ('.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.txt', '.md')
    
    for file in files:
        # Save to user_details folder
        user_details_path = UPLOAD_DIR / file.filename
        with open(user_details_path, "wb") as f:
            content = await file.read()
            f.write(content)
        saved_files.append(file.filename)
        
        if file.filename.lower().endswith(supported_extensions):
            processable_files.append(file.filename)
    
    if processable_files:
        try:
            result = await process_documents()
            
            return {
                "message": "Upload completed and documents processed",
                "files": saved_files,
                "processed_files": processable_files,
                "extracted_data_saved": "public/user_data.txt"
            }
        except Exception as e:
            return {
                "message": "Upload completed but processing failed",
                "files": saved_files,
                "error": str(e)
            }
    
    return {"message": "Upload completed", "files": saved_files}


@app.post("/query")
async def query_documents(request: QueryRequest):
    """
    Intelligent query endpoint that routes to:
    - Web search for current/general information
    - RAG for personal document information
    """
    try:
        from agent.merge_web_rag_agent import merged_query
        import asyncio
        
        # Add timeout of 60 seconds
        result = await asyncio.wait_for(
            merged_query(request.query),
            timeout=60.0
        )
        return result
    except asyncio.TimeoutError:
        return {
            "query": request.query,
            "source": "error",
            "data": "Request timed out. The query is taking too long to process. Please try a simpler question.",
            "status": "timeout"
        }
    except Exception as e:
        return {
            "query": request.query,
            "source": "error",
            "data": f"Error processing query: {str(e)}",
            "status": "error"
        }


@app.post("/navigate")
async def navigate_service(request: QueryRequest):
    """
    Navigation endpoint that matches user query to government services
    Returns the link to the matched service
    """
    from agent.navigation_agent import navigate_to_service
    result = await navigate_to_service(request.query)
    return result


@app.post("/autofill")
async def autofill_service(request: AutofillRequest):
    """
    Autofill endpoint that:
    1. Matches user query to a service (navigation)
    2. Returns the service link (frontend will open CDP browser)
    """
    from agent.navigation_agent import navigate_to_service
    
    # Get the service link based on query
    navigation_result = await navigate_to_service(request.query)
    
    if navigation_result.get("success"):
        service_link = navigation_result["link"]
        
        return {
            "success": True,
            "link": service_link,
            "message": "Service found. Frontend will open CDP browser.",
            "query": request.query
        }
    else:
        return {
            "success": False,
            "error": navigation_result.get("error", "Service not found"),
            "query": request.query
        }


@app.post("/open-browser")
async def open_browser(request: BrowserRequest):
    """
    Open browser with CDP and navigate to URL
    """
    from agent.browser_automation import launch_and_navigate
    
    result = launch_and_navigate(request.url, request.headless)
    return result


@app.post("/close-browser")
async def close_browser():
    """
    Close the browser instance
    """
    from agent.browser_automation import close_browser_instance
    
    result = close_browser_instance()
    return result


@app.post("/voice-transcribe")
async def voice_transcribe(request: VoiceTranscribeRequest):
    """
    Transcribe audio using Sarvam AI
    Supports: Malayalam (ml-IN), English (en-IN), Hindi (hi-IN), and more
    """
    import httpx
    import base64
    import io
    
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
    if not SARVAM_API_KEY:
        return {"success": False, "error": "SARVAM_API_KEY not set in .env"}
    
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(request.audio_base64)
        
        # Try multiple languages if auto-detect
        languages_to_try = []
        if request.language_code == "auto":
            languages_to_try = ["ml-IN", "en-IN", "hi-IN"]  # Malayalam, English, Hindi
        else:
            languages_to_try = [request.language_code]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for lang_code in languages_to_try:
                try:
                    print(f"Trying transcription with language: {lang_code}")
                    
                    # Sarvam expects multipart/form-data with file upload
                    files = {
                        'file': ('audio.webm', audio_bytes, 'audio/webm')
                    }
                    data = {
                        'language_code': lang_code
                    }
                    
                    transcribe_response = await client.post(
                        "https://api.sarvam.ai/speech-to-text",
                        headers={
                            "api-subscription-key": SARVAM_API_KEY
                        },
                        files=files,
                        data=data
                    )
                    
                    if transcribe_response.status_code == 200:
                        transcribe_data = transcribe_response.json()
                        transcribed_text = transcribe_data.get("transcript", "")
                        
                        if transcribed_text and transcribed_text.strip():
                            print(f"✅ Transcribed ({lang_code}): {transcribed_text}")
                            
                            # Translate to English if not already English
                            translated_text = transcribed_text
                            if lang_code != "en-IN":
                                try:
                                    print(f"Translating from {lang_code} to en-IN...")
                                    translate_response = await client.post(
                                        "https://api.sarvam.ai/translate",
                                        headers={
                                            "api-subscription-key": SARVAM_API_KEY,
                                            "Content-Type": "application/json"
                                        },
                                        json={
                                            "input": transcribed_text,
                                            "source_language_code": lang_code,
                                            "target_language_code": "en-IN",
                                            "speaker_gender": "Male",
                                            "mode": "formal",
                                            "model": "mayura:v1",
                                            "enable_preprocessing": True
                                        }
                                    )
                                    
                                    if translate_response.status_code == 200:
                                        translate_data = translate_response.json()
                                        translated_text = translate_data.get("translated_text", transcribed_text)
                                        print(f"✅ Translated to English: {translated_text}")
                                    else:
                                        print(f"Translation failed: {translate_response.text}")
                                except Exception as e:
                                    print(f"Translation error: {e}")
                            
                            return {
                                "success": True,
                                "transcribed_text": transcribed_text,
                                "translated_text": translated_text,
                                "language": lang_code
                            }
                    else:
                        print(f"Failed with {lang_code}: {transcribe_response.text}")
                        
                except Exception as e:
                    print(f"Error with {lang_code}: {e}")
                    continue
            
            # If all languages failed
            return {
                "success": False,
                "error": "Could not transcribe audio in any supported language"
            }
                
    except Exception as e:
        import traceback
        print(f"Voice transcribe error: {e}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/live-query")
async def live_query(
    query: str = Form(None),
    screenshot: UploadFile = File(None)
):
    """
    Live agent endpoint that analyzes screenshot + query
    Returns text response and decision (fill or normal)
    """
    try:
        # Validate inputs
        if not query:
            return {
                "success": False,
                "error": "Query parameter is required. Make sure the 'query' field is checked in Postman form-data.",
                "text": "Missing query",
                "decision": "normal"
            }
        
        if not screenshot:
            return {
                "success": False,
                "error": "Screenshot file is required. Make sure the 'screenshot' field is checked in Postman form-data.",
                "text": "Missing screenshot",
                "decision": "normal"
            }
        
        from agent.live_agent import analyze_live_query
        import base64
        
        # Read image file and convert to base64
        image_data = await screenshot.read()
        
        if not image_data:
            raise HTTPException(status_code=400, detail="Screenshot file is empty")
        
        screenshot_b64 = base64.b64encode(image_data).decode('utf-8')
        
        result = await analyze_live_query(screenshot_b64, query)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": "Failed to process request",
            "decision": "normal"
        }


@app.get("/files")
async def list_files():
    files = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            file_info = {
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "type": file_path.suffix,
            }
            files.append(file_info)
    return {"files": files}


@app.get("/files/{filename}")
async def view_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.post("/vision-magicfill")
async def vision_magic_fill(request: VisionMagicFillRequest):
    """
    Single endpoint: screenshot + fields → structured LLM extraction → fill_data
    """
    print(f"\n{'='*50}")
    print(f"Vision Magic Fill - {len(request.fields)} fields received")
    print(f"{'='*50}")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY not set in .env"}

    try:
        # Step 1: Get labels from Gemini Vision
        vision_labels = await analyze_with_gemini_vision(
            request.screenshot_b64, 
            request.fields
        )
        label_map = {item["index"]: item.get("label") for item in vision_labels}

        # Step 2: Merge labels into fields
        merged_fields = []
        for field in request.fields:
            merged = {**field}
            merged["label"] = label_map.get(field["index"])
            merged_fields.append(merged)

        # Step 3: Filter fillable fields
        fillable_fields = []
        skip_keywords = ['captcha', 'password', 'otp', 'confirm', 'security']
        
        for field in merged_fields:
            field_id = (field.get('id') or '').lower()
            field_name = (field.get('name') or '').lower()
            label = (field.get('label') or '').lower()
            field_type = field.get('type', '')
            
            if any(kw in field_id or kw in field_name or kw in label for kw in skip_keywords):
                continue
            if field.get('width', 0) == 0 or field.get('height', 0) == 0:
                continue
            if field_type == 'checkbox':
                continue
                
            fillable_fields.append(field)

        print(f"Fillable fields: {len(fillable_fields)}")

        # Step 4: Use structured LLM extraction
        extraction_result = await extract_form_data(fillable_fields)
        extracted_data = extraction_result.get('extracted', {})
        field_results = extraction_result.get('fields', [])
        
        print(f"Extracted data: {json.dumps(extracted_data, indent=2)}")

        # Step 5: Build fill_data
        fill_data = []
        
        def format_value(val, field_id: str, label: str, field_type: str = 'text') -> str:
            """Format value based on field hints"""
            if val is None or val == "null" or val == "":
                return None
            
            val_str = str(val)
            label_lower = label.lower()
            field_id_lower = field_id.lower() if field_id else ""
            
            # Aadhaar: remove spaces, keep only digits
            if 'aadhaar' in label_lower or 'uid' in field_id_lower or 'aadhar' in label_lower:
                return ''.join(c for c in val_str if c.isdigit())
            
            # Mobile/Phone: digits only
            if 'mobile' in label_lower or 'phone' in label_lower:
                return ''.join(c for c in val_str if c.isdigit())
            
            # Pincode: digits only
            if 'pin' in label_lower or 'zip' in label_lower:
                return ''.join(c for c in val_str if c.isdigit())
            
            # Date fields - convert DD/MM/YYYY to YYYY-MM-DD if field type is 'date'
            if field_type == 'date':
                import re
                match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', val_str)
                if match:
                    day, month, year = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            return val_str

        for field_result in field_results:
            field = field_result['field']
            value = field_result['value']
            
            field_id = field.get('id')
            label = field.get('label', '').replace(' *', '').strip()
            field_type = field.get('type')
            tag = field.get('tag')
            options = field.get('options')
            
            if not field_id or value is None:
                continue
            
            # Handle radio buttons
            if field_type == 'radio':
                label_lower = label.lower()
                value_lower = str(value).lower()
                
                # Click if the extracted value matches this radio option
                if value_lower == label_lower or value_lower in label_lower or label_lower in value_lower:
                    fill_data.append({"id": field_id, "action": "click"})
                # Also handle boolean true for gender radios
                elif value is True or value == "true":
                    fill_data.append({"id": field_id, "action": "click"})
                continue
            
            # Handle SELECT - match to option value
            if tag == 'SELECT' and options:
                val_str = str(value).lower()
                for opt in options:
                    if opt['value'] != '-1':
                        opt_label = opt['label'].lower()
                        if val_str == opt_label or val_str in opt_label or opt_label in val_str:
                            fill_data.append({"id": field_id, "value": opt['value'], "action": "select"})
                            break
                continue
            
            # Format and add text input
            formatted_value = format_value(value, field_id, label, field_type)
            if formatted_value:
                fill_data.append({"id": field_id, "value": formatted_value, "action": "fill"})

        print(f"\nFILL DATA FOR PLAYWRIGHT:")
        print(json.dumps(fill_data, indent=2))

        return {
            "success": True,
            "fill_data": fill_data,
            "extracted": extracted_data
        }

    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)