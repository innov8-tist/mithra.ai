import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
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
    from agent.merge_web_rag_agent import merged_query
    result = await merged_query(request.query)
    return result


@app.post("/navigate")
async def navigate_service(request: QueryRequest):
    """
    Navigation endpoint that matches user query to government services
    Returns the link to the matched service
    """
    from agent.navigation_agent import navigate_to_service
    result = await navigate_to_service(request.query)
    return result


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