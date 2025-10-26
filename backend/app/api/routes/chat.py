from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from app.api.dependencies import CurrentUser
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
import json

router = APIRouter()

# Relevance threshold (50%)
RELEVANCE_THRESHOLD = 0.5

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's question")
    stream: bool = Field(default=True, description="Whether to stream the response")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of relevant documents to retrieve")
    min_relevance: Optional[float] = Field(default=0.5, ge=0.0, le=1.0, description="Minimum relevance score (0-1)")

class ChatSource(BaseModel):
    filename: str
    page: Union[int, str]
    text: str
    score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource]
    has_relevant_context: bool
    max_relevance_score: float

@router.post("/chat", response_model=None)
async def chat(
    request: ChatRequest,
    current_user: CurrentUser = None
):
    """
    Process chat query with RAG (Retrieval-Augmented Generation).
    
    Returns "no answer" if relevance score is below threshold (default 50%).
    
    Args:
        request: Chat request with message and options
        current_user: Current authenticated user (injected by dependency)
    
    Returns:
        Streaming or non-streaming chat response with sources
    """
    
    user_id = current_user.get("sub")
    
    try:
        # Generate query embedding
        query_embedding = embedding_service.generate_embedding(request.message)
        
        # Search for relevant documents
        relevant_docs = vector_store.search(
            query_embedding=query_embedding,
            user_id=user_id,
            limit=request.top_k
        )
        
        if not relevant_docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No documents found. Please upload documents first."
            )
        
        # Check maximum relevance score
        max_score = max(doc["score"] for doc in relevant_docs)
        has_relevant_context = max_score >= request.min_relevance
        
        # Format sources
        sources = [
            {
                "filename": doc["filename"],
                "page": doc["page"],
                "text": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
                "score": doc["score"]
            }
            for doc in relevant_docs
        ]
        
        # If relevance is too low, return no answer message
        if not has_relevant_context:
            no_answer_message = (
                f"I couldn't find relevant information in your documents to answer this question. "
                f"The highest relevance score was {max_score:.1%}, which is below the {request.min_relevance:.0%} threshold. "
                f"Please try:\n"
                f"- Rephrasing your question\n"
                f"- Uploading more relevant documents\n"
                f"- Asking a question more related to your uploaded content"
            )
            
            if request.stream:
                async def generate_no_answer():
                    yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
                    yield f"data: {json.dumps({'type': 'no_answer', 'data': no_answer_message, 'max_score': max_score})}\n\n"
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(
                    generate_no_answer(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no"
                    }
                )
            else:
                return ChatResponse(
                    answer=no_answer_message,
                    sources=sources,
                    has_relevant_context=False,
                    max_relevance_score=max_score
                )
        
        # Proceed with normal LLM generation if relevance is sufficient
        if request.stream:
            # Streaming response
            async def generate():
                # First send sources
                yield f"data: {json.dumps({'type': 'sources', 'data': sources, 'max_score': max_score})}\n\n"
                
                # Then stream answer
                try:
                    async for chunk in llm_service.generate_stream(request.message, relevant_docs):
                        yield f"data: {json.dumps({'type': 'token', 'data': chunk})}\n\n"
                except Exception as e:
                    error_msg = f"Error generating response: {str(e)}"
                    yield f"data: {json.dumps({'type': 'error', 'data': error_msg})}\n\n"
                
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            # Non-streaming response
            answer = await llm_service.generate(request.message, relevant_docs)
            
            return ChatResponse(
                answer=answer,
                sources=sources,
                has_relevant_context=True,
                max_relevance_score=max_score
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
        )

@router.get("/history")
async def get_chat_history(
    current_user: CurrentUser = None,
    limit: int = 50
):
    """Get user's chat history (placeholder)"""
    return {"messages": [], "count": 0, "note": "Chat history feature coming soon"}

@router.delete("/history")
async def clear_chat_history(current_user: CurrentUser = None):
    """Clear user's chat history (placeholder)"""
    return {"status": "success", "message": "Chat history cleared"}