from typing import List, Dict, AsyncGenerator
import httpx
import json
from app.core.config import settings

class LLMService:
    """Interface with local LLM via vLLM OpenAI-compatible API"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
    
    def _build_prompt(self, query: str, context: List[Dict[str, any]]) -> str:
        """Build RAG prompt with context and citations"""
        context_text = "\n\n".join([
            f"[Source: {doc['filename']}, Page: {doc['page']}]\n{doc['text']}"
            for doc in context
        ])
        
        prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided context. 
Always cite your sources by mentioning the filename and page number.

Context:
{context_text}

Question: {query}

Answer (include citations with filename and page number):"""
        
        return prompt
    
    async def generate_stream(
        self,
        query: str,
        context: List[Dict[str, any]]
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from LLM"""
        prompt = self._build_prompt(query, context)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/completions",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "max_tokens": settings.MAX_TOKENS,
                    "temperature": settings.TEMPERATURE,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        
                        try:
                            json_data = json.loads(data)
                            if "choices" in json_data:
                                text = json_data["choices"][0].get("text", "")
                                if text:
                                    yield text
                        except json.JSONDecodeError:
                            continue
    
    async def generate(
        self,
        query: str,
        context: List[Dict[str, any]]
    ) -> str:
        """Generate non-streaming response from LLM"""
        prompt = self._build_prompt(query, context)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/completions",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "max_tokens": settings.MAX_TOKENS,
                    "temperature": settings.TEMPERATURE,
                    "stream": False
                }
            )
            
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["text"]

# Singleton instance
llm_service = LLMService()