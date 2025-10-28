from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query, Depends
from fastapi.responses import FileResponse
from pathlib import Path
import aiofiles
import os
from typing import List, Optional
from app.api.dependencies import CurrentUser, get_current_user
from app.core.config import settings
from app.services.document_processor import DocumentProcessor
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer(auto_error=False)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: CurrentUser = None
):
    """
    Upload and process document.
    
    Args:
        file: The document file to upload
        current_user: Current authenticated user (injected by dependency)
    
    Returns:
        Upload status with processed chunk count
    """
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Get user ID from token
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )
    
    # Create user directory
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
            "status": "success",
            "user_id": user_id
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
async def list_documents(current_user: CurrentUser = None):
    """
    List user's uploaded documents with vector count.
    
    Args:
        current_user: Current authenticated user (injected by dependency)
    
    Returns:
        List of uploaded documents with metadata
    """
    user_id = current_user.get("sub")
    user_dir = Path(settings.UPLOAD_DIR) / user_id
    
    if not user_dir.exists():
        return {"documents": [], "count": 0}
    
    # Get vector counts from Qdrant
    vector_counts = vector_store.get_user_file_count(user_id)
    
    documents = []
    for file_path in user_dir.iterdir():
        if file_path.is_file():
            filename = file_path.name
            documents.append({
                "filename": filename,
                "size": file_path.stat().st_size,
                "uploaded_at": file_path.stat().st_mtime,
                "extension": file_path.suffix.lower(),
                "vector_count": vector_counts.get(filename, 0)
            })
    
    # Sort by upload time (most recent first)
    documents.sort(key=lambda x: x["uploaded_at"], reverse=True)
    
    return {
        "documents": documents,
        "count": len(documents)
    }

@router.delete("/documents/{filename}")
async def delete_document(
    filename: str,
    current_user: CurrentUser = None
):
    """
    Delete a user's document from both filesystem and vector database.
    
    Args:
        filename: Name of the file to delete
        current_user: Current authenticated user (injected by dependency)
    
    Returns:
        Deletion status with details
    """
    user_id = current_user.get("sub")
    user_dir = Path(settings.UPLOAD_DIR) / user_id
    file_path = user_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found"
        )
    
    # Security check - ensure file is within user directory
    try:
        file_path_resolved = file_path.resolve()
        user_dir_resolved = user_dir.resolve()
        if not str(file_path_resolved).startswith(str(user_dir_resolved)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid file path"
        )
    
    try:
        # Delete from vector database first
        vectors_deleted = vector_store.delete_by_filename(filename, user_id)
        
        # Delete file from filesystem
        os.remove(file_path)
        
        return {
            "filename": filename,
            "status": "deleted",
            "vectors_deleted": vectors_deleted,
            "message": f"Successfully deleted {filename} and {vectors_deleted} associated vectors"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )

@router.delete("/documents")
async def delete_all_documents(current_user: CurrentUser = None):
    """
    Delete ALL user's documents from both filesystem and vector database.
    Use with caution!
    
    Args:
        current_user: Current authenticated user (injected by dependency)
    
    Returns:
        Deletion status with counts
    """
    user_id = current_user.get("sub")
    user_dir = Path(settings.UPLOAD_DIR) / user_id
    
    if not user_dir.exists():
        return {
            "status": "success",
            "files_deleted": 0,
            "vectors_deleted": 0,
            "message": "No documents to delete"
        }
    
    try:
        files_deleted = 0
        
        # Delete all files
        for file_path in user_dir.iterdir():
            if file_path.is_file():
                os.remove(file_path)
                files_deleted += 1
        
        # Delete all vectors from Qdrant
        vectors_deleted = vector_store.delete_all_user_documents(user_id)
        
        return {
            "status": "success",
            "files_deleted": files_deleted,
            "vectors_deleted": vectors_deleted,
            "message": f"Successfully deleted {files_deleted} files and {vectors_deleted} vectors"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting all documents: {str(e)}"
        )

@router.get("/stats")
async def get_user_stats(current_user: CurrentUser = None):
    """
    Get user's document statistics including vector counts.
    
    Args:
        current_user: Current authenticated user (injected by dependency)
    
    Returns:
        User statistics
    """
    user_id = current_user.get("sub")
    user_dir = Path(settings.UPLOAD_DIR) / user_id
    
    # Get vector counts
    vector_counts = vector_store.get_user_file_count(user_id)
    total_vectors = sum(vector_counts.values())
    
    if not user_dir.exists():
        return {
            "total_documents": 0,
            "total_size": 0,
            "total_size_mb": 0,
            "total_vectors": total_vectors,
            "document_types": {},
            "vector_counts": vector_counts
        }
    
    documents = list(user_dir.iterdir())
    total_size = sum(f.stat().st_size for f in documents if f.is_file())
    
    # Count by type
    doc_types = {}
    for file_path in documents:
        if file_path.is_file():
            ext = file_path.suffix.lower()
            doc_types[ext] = doc_types.get(ext, 0) + 1
    
    return {
        "total_documents": len(documents),
        "total_size": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "total_vectors": total_vectors,
        "document_types": doc_types,
        "vector_counts": vector_counts,
        "user_id": user_id
    }
    
async def get_user_from_token_or_query(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None, description="Authentication token")
) -> dict:
    """
    Get user from either Authorization header or query parameter token.
    This allows iframe requests to include token in URL.
    """
    from app.core.security import verify_token_string
    
    # Try header first
    if credentials:
        try:
            user = await verify_token_string(credentials.credentials)
            return user
        except:
            pass
    
    # Try query parameter
    if token:
        try:
            user = await verify_token_string(token)
            return user
        except:
            pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
@router.get("/view/{filename}")
async def view_document(
    filename: str,
    page: int = Query(default=1, description="Page number to open"),
    token: Optional[str] = Query(None, description="Authentication token"),
    current_user: dict = Depends(get_user_from_token_or_query)
):
    """
    View/download a document file.
    Supports authentication via header or query parameter for iframe compatibility.
    
    Args:
        filename: Name of the file to view
        page: Page number (for frontend to handle)
        token: Optional JWT token in query parameter
        current_user: Current authenticated user
    
    Returns:
        File response to view/download
    """
    user_id = current_user.get("sub")
    user_dir = Path(settings.UPLOAD_DIR) / user_id
    file_path = user_dir / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found"
        )
    
    # Security check - ensure file is within user directory
    try:
        file_path_resolved = file_path.resolve()
        user_dir_resolved = user_dir.resolve()
        if not str(file_path_resolved).startswith(str(user_dir_resolved)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid file path"
        )
    
    # Determine media type
    ext = file_path.suffix.lower()
    media_types = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    media_type = media_types.get(ext, 'application/octet-stream')
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        }
    )

@router.options("/view/{filename}")
async def view_document_options(filename: str):
    """Handle CORS preflight requests"""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    }