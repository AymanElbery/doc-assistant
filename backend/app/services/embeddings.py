from sentence_transformers import SentenceTransformer
from typing import List
import torch
from app.core.config import settings

class EmbeddingService:
    """Generate embeddings using local model"""
    
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=device
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embedding = self.model.encode(
            text,
            convert_to_tensor=True,
            normalize_embeddings=True
        )
        return embedding.cpu().tolist()
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = self.model.encode(
            texts,
            convert_to_tensor=True,
            normalize_embeddings=True,
            batch_size=32
        )
        return embeddings.cpu().tolist()

# Singleton instance
embedding_service = EmbeddingService()