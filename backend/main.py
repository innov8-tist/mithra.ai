import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent.retriver_service import Retriver
from agent.pdf_image_process import process_documents
import shutil

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)