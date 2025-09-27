from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import List, Optional
import uvicorn
import os
import json
from pathlib import Path
import asyncio

from .settings import settings, Environment
from .anthropic_service import anthropic_files_service
from .document_service import document_processing_service
from .database import db_manager
from .migrations import migration_runner

# Configure logging with settings
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)
logger = logging.getLogger(__name__)

# Create FastAPI app with settings
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    debug=settings.debug
)

# Enable CORS with settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Log startup information
logger.info(f"Starting {settings.api_title} in {settings.environment} mode")
logger.info(f"Debug mode: {settings.debug}")
logger.info(f"CORS origins: {settings.cors_origins}")

# Ensure data directory exists
settings.ensure_data_directory()

async def process_document_background(extraction_id: int, file_path: Path, questions: List[str]):
    """
    Background task to process document with docling and anthropic
    """
    logger.info(f"🔄 Starting background processing for extraction ID: {extraction_id}")
    logger.info(f"   File: {file_path}")
    logger.info(f"   Questions: {len(questions)}")

    try:
        # Update status to processing
        db_manager.update_extraction_status(extraction_id, "processing")
        logger.info(f"   Status updated to 'processing'")

        # Process document to convert to markdown and answer questions
        document_info = await document_processing_service.process_document(
            file_path=file_path,
            questions=questions
        )
        logger.info(f"   Document processing completed")
        logger.info(f"   Markdown length: {document_info.get('markdown_length', 0)} characters")

        # Extract results
        markdown_content = document_info.get('markdown_content')
        answers_data = document_info.get('answers')
        error = document_info.get('error')

        if error:
            logger.error(f"   ❌ Document processing error: {error}")
            db_manager.update_extraction_status(extraction_id, "failed")
            return

        # Update extraction with markdown content
        if markdown_content:
            db_manager.update_extraction_status(extraction_id, "completed", markdown_content)
            logger.info(f"   ✅ Markdown content saved to database")
        else:
            logger.warning(f"   ⚠️ No markdown content generated")

        # Save question results if available
        if answers_data and isinstance(answers_data, dict) and "answers" in answers_data:
            logger.info(f"   💾 Saving {len(answers_data['answers'])} question results")
            for answer in answers_data["answers"]:
                question = answer.get("question", "")
                answer_text = answer.get("answer", "")
                confidence = answer.get("confidence")

                if question and answer_text:
                    result_id = db_manager.create_question_result(
                        extraction_id=extraction_id,
                        question=question,
                        answer=answer_text,
                        confidence=confidence
                    )
                    logger.info(f"     - Saved result ID {result_id}: {question[:50]}...")
        elif answers_data and isinstance(answers_data, dict) and "error" in answers_data:
            logger.error(f"   ❌ Question answering error: {answers_data['error']}")
        else:
            logger.info(f"   ℹ️ No questions were provided or answered")

        logger.info(f"✅ Background processing completed successfully for extraction ID: {extraction_id}")

    except Exception as e:
        logger.error(f"❌ Background processing failed for extraction ID {extraction_id}: {str(e)}")
        logger.error(f"   Error details: {type(e).__name__}: {str(e)}")
        try:
            db_manager.update_extraction_status(extraction_id, "failed")
        except Exception as db_error:
            logger.error(f"   Failed to update status to 'failed': {str(db_error)}")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and run migrations on startup"""
    try:
        logger.info("Initializing database and running migrations...")
        migration_runner.run_migrations()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

@app.get("/")
async def root():
    return {
        "message": f"{settings.api_title} is running",
        "environment": settings.environment,
        "version": settings.api_version
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "data_directory": str(settings.data_path),
        "max_file_size": settings.max_file_size
    }

@app.post("/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    questions: Optional[str] = Form(None)
):
    """
    Upload a document with optional form data and questions.
    Returns immediately after file is saved, then processes in background.
    """
    logger.info(f"📤 Received file upload request:")
    logger.info(f"  - Filename: {file.filename}")
    logger.info(f"  - Content Type: {file.content_type}")
    logger.info(f"  - Size: {file.size if hasattr(file, 'size') else 'Unknown'}")
    logger.info(f"  - Title: {title}")
    logger.info(f"  - Description: {description}")

    # Parse and log questions
    parsed_questions = []
    if questions:
        try:
            parsed_questions = json.loads(questions)
            logger.info(f"  - Questions received ({len(parsed_questions)} total):")
            for i, question in enumerate(parsed_questions, 1):
                logger.info(f"    {i}. {question}")
        except json.JSONDecodeError as e:
            logger.warning(f"  - Failed to parse questions JSON: {e}")
            logger.warning(f"  - Raw questions data: {questions}")
    else:
        logger.info("  - No questions provided")

    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Check file type
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.allowed_file_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_extension} not allowed. Allowed types: {settings.allowed_file_types}"
        )

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
        )

    logger.info(f"  - File content length: {len(content)} bytes")

    # Create file path using settings
    # TODO: Handle duplicate filenames - for now just overwrite
    file_path = settings.data_path / file.filename

    # Save file to local data directory
    try:
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"  - ✅ File saved locally to: {file_path}")
    except Exception as e:
        logger.error(f"  - ❌ Failed to save file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create extraction record in database
    try:
        extraction_id = db_manager.create_extraction(
            file_path=str(file_path),
            filename=file.filename,
            file_size=len(content),
            questions=parsed_questions
        )
        logger.info(f"  - ✅ Created extraction record with ID: {extraction_id}")
    except Exception as e:
        logger.error(f"  - ❌ Failed to create extraction record: {str(e)}")
        # Clean up the saved file
        try:
            file_path.unlink()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to create extraction record: {str(e)}")

    # Start background processing
    background_tasks.add_task(
        process_document_background,
        extraction_id=extraction_id,
        file_path=file_path,
        questions=parsed_questions
    )
    logger.info(f"  - 🚀 Background processing task queued for extraction ID: {extraction_id}")

    # Return immediate response
    response_data = {
        "message": "File uploaded successfully and will be processed shortly",
        "extraction_id": extraction_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "title": title,
        "description": description,
        "questions": parsed_questions,
        "file_size": len(content),
        "local_path": str(file_path),
        "status": "pending",
        "processing_info": "Document processing (markdown conversion and question answering) has been queued and will complete in the background. Check the extraction status using the extraction_id."
    }

    logger.info(f"📤 Upload completed - returning immediate response for extraction ID: {extraction_id}")
    return JSONResponse(
        status_code=200,
        content=response_data
    )

@app.get("/documents")
async def get_documents():
    """
    Get all documents
    """
    logger.info("Received request to get all documents")

    # List files in data directory
    documents = []
    if settings.data_path.exists():
        for file_path in settings.data_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in settings.allowed_file_types:
                documents.append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                })

    return JSONResponse(
        status_code=200,
        content={
            "message": "Documents retrieved successfully",
            "documents": documents,
            "total": len(documents),
            "environment": settings.environment
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
            },
            "environment": settings.environment
        }
    )

@app.get("/extractions")
async def get_extractions():
    """
    Get all document extractions from the database
    """
    logger.info("Received request to get all extractions")

    try:
        extractions = db_manager.get_all_extractions()
        return JSONResponse(
            status_code=200,
            content={
                "message": "Extractions retrieved successfully",
                "extractions": extractions,
                "total": len(extractions)
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve extractions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve extractions: {str(e)}")

@app.get("/extractions/{extraction_id}")
async def get_extraction(extraction_id: int):
    """
    Get a specific extraction by ID
    """
    logger.info(f"Received request to get extraction with ID: {extraction_id}")

    try:
        extraction = db_manager.get_extraction_by_id(extraction_id)
        if not extraction:
            raise HTTPException(status_code=404, detail="Extraction not found")

        return JSONResponse(
            status_code=200,
            content={
                "message": "Extraction retrieved successfully",
                "extraction": extraction
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve extraction {extraction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve extraction: {str(e)}")

@app.get("/anthropic/files")
async def list_anthropic_files():
    """
    List all files stored in Anthropic Files API
    """
    logger.info("Received request to list Anthropic files")

    if not anthropic_files_service.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="Anthropic API not configured. Please set ANTHROPIC_API_KEY."
        )

    try:
        files = await anthropic_files_service.list_files()
        return JSONResponse(
            status_code=200,
            content={
                "message": "Anthropic files retrieved successfully",
                "files": files or [],
                "total": len(files) if files else 0
            }
        )
    except Exception as e:
        logger.error(f"Failed to list Anthropic files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@app.get("/anthropic/files/{file_id}")
async def get_anthropic_file_metadata(file_id: str):
    """
    Get metadata for a specific file from Anthropic Files API
    """
    logger.info(f"Received request to get metadata for Anthropic file: {file_id}")

    if not anthropic_files_service.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="Anthropic API not configured. Please set ANTHROPIC_API_KEY."
        )

    try:
        file_metadata = await anthropic_files_service.get_file_metadata(file_id)
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")

        return JSONResponse(
            status_code=200,
            content={
                "message": "File metadata retrieved successfully",
                "file": file_metadata
            }
        )
    except Exception as e:
        logger.error(f"Failed to get file metadata for {file_id}: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="File not found")
        raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")

@app.delete("/anthropic/files/{file_id}")
async def delete_anthropic_file(file_id: str):
    """
    Delete a file from Anthropic Files API
    """
    logger.info(f"Received request to delete Anthropic file: {file_id}")

    if not anthropic_files_service.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="Anthropic API not configured. Please set ANTHROPIC_API_KEY."
        )

    try:
        success = await anthropic_files_service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete file")

        return JSONResponse(
            status_code=200,
            content={
                "message": "File deleted successfully",
                "file_id": file_id
            }
        )
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="File not found")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@app.get("/anthropic/status")
async def get_anthropic_status():
    """
    Get the status of Anthropic Files API integration
    """
    return JSONResponse(
        status_code=200,
        content={
            "anthropic_api_enabled": anthropic_files_service.is_enabled(),
            "api_key_configured": settings.anthropic_api_key is not None,
            "message": "Anthropic Files API is enabled" if anthropic_files_service.is_enabled()
                      else "Anthropic Files API is not configured. Set ANTHROPIC_API_KEY to enable."
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.is_development
    )