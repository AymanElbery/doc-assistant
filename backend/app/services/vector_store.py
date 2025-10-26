from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from typing import List, Dict
from uuid import uuid4
from app.core.config import settings

class VectorStore:
    """Manage Qdrant vector database operations"""
    
    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if settings.QDRANT_COLLECTION not in collection_names:
            self.client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
    
    def upsert_documents(
        self,
        chunks: List[Dict[str, any]],
        embeddings: List[List[float]],
        filename: str,
        user_id: str
    ):
        """Insert document chunks with embeddings"""
        points = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "page": chunk["page"],
                    "filename": filename,
                    "chunk_index": i,
                    "user_id": user_id,
                    "doc_type": chunk["type"]
                }
            )
            points.append(point)
        
        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points
        )
    
    def search(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = None
    ) -> List[Dict[str, any]]:
        """Search for similar documents"""
        if limit is None:
            limit = settings.TOP_K_RESULTS
        
        results = self.client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            ),
            limit=limit
        )
        
        return [
            {
                "text": hit.payload["text"],
                "page": hit.payload["page"],
                "filename": hit.payload["filename"],
                "score": hit.score,
                "doc_type": hit.payload["doc_type"]
            }
            for hit in results
        ]
    
    def delete_user_documents(self, user_id: str):
        """Delete all documents for a user"""
        self.client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
        )

# Singleton instance
vector_store = VectorStore()