from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict
import uuid
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.collection_name = settings.QDRANT_COLLECTION
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise

    def upsert_documents(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]],
        filename: str,
        user_id: str
    ):
        """Insert or update documents in vector database"""
        points = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "page": chunk["page"],
                    "filename": filename,
                    "user_id": user_id,
                    "chunk_index": i,
                    "type": chunk.get("type", "unknown")
                }
            )
            points.append(point)
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} points for {filename}")
        except Exception as e:
            logger.error(f"Error upserting documents: {e}")
            raise

    def search(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """Search for relevant documents"""
        try:
            results = self.client.search(
                collection_name=self.collection_name,
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
            
            documents = []
            for result in results:
                documents.append({
                    "text": result.payload["text"],
                    "page": result.payload["page"],
                    "filename": result.payload["filename"],
                    "score": result.score,
                    "type": result.payload.get("type", "unknown")
                })
            
            return documents
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def delete_by_filename(self, filename: str, user_id: str) -> int:
        """
        Delete all vectors associated with a specific file for a user.
        Returns the number of points deleted.
        """
        try:
            # Get points to delete
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="filename",
                            match=MatchValue(value=filename)
                        ),
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=10000  # Large number to get all matching points
            )
            
            points_to_delete = scroll_result[0]  # First element is the list of points
            point_ids = [point.id for point in points_to_delete]
            
            if point_ids:
                # Delete points
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
                logger.info(f"Deleted {len(point_ids)} vectors for file: {filename} (user: {user_id})")
                return len(point_ids)
            else:
                logger.info(f"No vectors found for file: {filename} (user: {user_id})")
                return 0
                
        except Exception as e:
            logger.error(f"Error deleting vectors for file {filename}: {e}")
            raise

    def delete_all_user_documents(self, user_id: str) -> int:
        """
        Delete all vectors for a user.
        Returns the number of points deleted.
        """
        try:
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=10000
            )
            
            points_to_delete = scroll_result[0]
            point_ids = [point.id for point in points_to_delete]
            
            if point_ids:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
                logger.info(f"Deleted {len(point_ids)} vectors for user: {user_id}")
                return len(point_ids)
            else:
                logger.info(f"No vectors found for user: {user_id}")
                return 0
                
        except Exception as e:
            logger.error(f"Error deleting all user documents: {e}")
            raise

    def get_user_file_count(self, user_id: str) -> Dict[str, int]:
        """
        Get count of vectors per file for a user.
        Returns dict with filename as key and count as value.
        """
        try:
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=10000
            )
            
            points = scroll_result[0]
            file_counts = {}
            
            for point in points:
                filename = point.payload.get("filename", "unknown")
                file_counts[filename] = file_counts.get(filename, 0) + 1
            
            return file_counts
        except Exception as e:
            logger.error(f"Error getting user file count: {e}")
            return {}

# Global instance
vector_store = VectorStore()