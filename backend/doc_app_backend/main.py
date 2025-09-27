from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import List, Optional
import uvicorn
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Document API is running"}

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    Upload a document with optional form data
    """
    logger.info(f"Received file upload request:")
    logger.info(f"  - Filename: {file.filename}")
    logger.info(f"  - Content Type: {file.content_type}")
    logger.info(f"  - Size: {file.size if hasattr(file, 'size') else 'Unknown'}")
    logger.info(f"  - Title: {title}")
    logger.info(f"  - Description: {description}")

    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Create data directory path
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Create file path
    file_path = data_dir / file.filename

    # Read and save file content
    content = await file.read()
    logger.info(f"  - File content length: {len(content)} bytes")

    # Save file to data directory (this will replace if it exists)
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"  - File saved to: {file_path}")

    # Reset file position for potential future reads
    await file.seek(0)

    # Return stub response
    return JSONResponse(
        status_code=200,
        content={
            "message": "Document uploaded successfully",
            "filename": file.filename,
            "content_type": file.content_type,
            "title": title,
            "description": description,
            "id": "stub_document_id"
        }
    )

@app.get("/documents")
async def get_documents():
    """
    Get all documents
    """
    logger.info("Received request to get all documents")

    # Return stub response with empty document list
    return JSONResponse(
        status_code=200,
        content={
            "message": "Documents retrieved successfully",
            "documents": [],
            "total": 0
        }
    )

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Get a specific document by ID
    """
    logger.info(f"Received request to get document with ID: {document_id}")

    # Return stub response
    return JSONResponse(
        status_code=200,
        content={
            "message": "Document retrieved successfully",
            "document": {
                "id": document_id,
                "filename": "stub_document.pdf",
                "title": "Stub Document",
                "description": "This is a stub document response",
            }
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)