from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Documents Assistant"
    
    # CORS - Accept as string, split manually
    CORS_ORIGINS: str = "http://localhost:4200,http://localhost"
    
    # Keycloak Settings
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "ai-docs-assistant"
    KEYCLOAK_CLIENT_ID: str = "ai-docs-client"
    KEYCLOAK_PUBLIC_KEY: str = ""
    
    # Qdrant Settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "documents"
    EMBEDDING_DIMENSION: int = 768
    
    # Ollama Settings
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b" #"llama3.1:8b" #"qwen2.5:3b" #"phi3:mini"
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    
    # Document Settings
    UPLOAD_DIR: str = "app/uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()