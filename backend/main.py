import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent.retriver_service import Retriver
from agent.pdf_image_process import process_documents
from agent.vision_magic_fill import analyze_with_gemini_vision
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
async def upload_files(files: list[UploadFile] = File(...)):
    saved_files = []
    processable_files = []
    supported_extensions = ('.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.txt', '.md')
    
    for file in files:
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        saved_files.append(file.filename)
        
        public_file_path = PUBLIC_DIR / file.filename
        shutil.copy2(file_path, public_file_path)
        
        if file.filename.lower().endswith(supported_extensions):
            processable_files.append(file.filename)
    
    if processable_files:
        try:
            result = await process_documents()
            return {
                "message": "Upload completed and documents processed",
                "files": saved_files,
                "processed_files": processable_files,
                "processing_result": result
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
    result = await Retriver(request.query)
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
    Magic Fill: screenshot + fields → Gemini Vision → labeled fields
    """
    print(f"\n{'='*50}")
    print(f"Vision Magic Fill - {len(request.fields)} fields received")
    print(f"URL: {request.url}")
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

        print(f"\n{'='*50}")
        print(f"MERGED FIELDS (after Gemini Vision labeling):")
        print(json.dumps(merged_fields, indent=2))
        print(f"{'='*50}\n")
        
        return {
            "success": True,
            "message": f"Found {len(merged_fields)} fields with labels",
            "fields": merged_fields,
            "fill_data": []  # Empty for now - not filling yet
        }

    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)