from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pathlib import Path
import aiofiles
import os
from app.core.security import verify_token
from app.core.config import settings
from app.services.document_processor import DocumentProcessor
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token)
):
    """Upload and process document"""
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Create user directory
    user_id = current_user.get("sub")
    user_dir = Path(settings.UPLOAD_DIR) / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = user_dir / file.filename
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            
            # Check file size
            if len(content) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
                )
            
            await f.write(content)
        
        # Process document
        chunks = DocumentProcessor.process_document(str(file_path))
        
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content extracted from document"
            )
        
        # Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.generate_embeddings(texts)
        
        # Store in vector database
        vector_store.upsert_documents(
            chunks=chunks,
            embeddings=embeddings,
            filename=file.filename,
            user_id=user_id
        )
        
        return {
            "filename": file.filename,
            "chunks_processed": len(chunks),
            "status": "success"
        }
    
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@router.get("/documents")
async def list_documents(current_user: dict = Depends(verify_token)):
    """List user's uploaded documents"""
    user_id = current_user.get("sub")
    user_dir = Path(settings.UPLOAD_DIR) / user_id
    
    if not user_dir.exists():
        return {"documents": []}
    
    documents = []
    for file_path in user_dir.iterdir():
        if file_path.is_file():
            documents.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "uploaded_at": file_path.stat().st_mtime
            })
    
    return {"documents": documents}