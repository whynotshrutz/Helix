"""Custom NVIDIA Embedder for Agno using direct httpx client.

This bypasses Agno's OpenAI wrapper to properly support NVIDIA's input_type parameter.
"""

import os
import httpx
from typing import List, Optional


class NvidiaEmbedder:
    """
    Custom embedder for NVIDIA Retrieval Embedding NIM.
    Compatible with Agno-style embed() API.
    
    NVIDIA embedding models require an 'input_type' parameter that Agno's
    OpenAI embedder doesn't support, so we use httpx directly.
    """

    def __init__(
        self,
        id: str = "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1",
        api_key: Optional[str] = None,
        base_url: str = "https://integrate.api.nvidia.com/v1",
        dimensions: Optional[int] = None,
        enable_batch: bool = True,
        batch_size: int = 100,
        input_type: str = "passage",  # "passage" for documents, "query" for queries
    ):
        """Initialize NVIDIA embedder.
        
        Args:
            id: Model ID (default: nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1)
            api_key: NVIDIA API key (defaults to NVIDIA_EMBED_API_KEY env var)
            base_url: NVIDIA API base URL (e.g., https://integrate.api.nvidia.com/v1)
            dimensions: Embedding dimensions (optional, model-dependent)
            enable_batch: Enable batch processing
            batch_size: Number of texts per batch
            input_type: "passage" for documents (ingestion) or "query" for search queries
        """
        # Get API key from env if not provided
        if api_key is None:
            api_key = os.getenv("NVIDIA_EMBED_API_KEY") or os.getenv("NVIDIA_API_KEY")
        
        if not api_key:
            raise ValueError(
                "NVIDIA API key is required. Set NVIDIA_EMBED_API_KEY or "
                "NVIDIA_API_KEY environment variable, or pass api_key parameter."
            )
        
        self.id = id
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.dimensions = dimensions
        self.enable_batch = enable_batch
        self.batch_size = batch_size
        self.input_type = input_type
        self.response = None  # Agno may access this attribute
        
        print(f"✅ Initialized NVIDIA Embedder: {id}")
        print(f"   Base URL: {base_url}")
        print(f"   Input type: {input_type}")
        print(f"   Batch processing: {'enabled' if enable_batch else 'disabled'}")
    
    async def embed(self, texts: List[str], input_type: Optional[str] = None) -> List[List[float]]:
        """
        Generate embeddings using NVIDIA NIM.
        
        Args:
            texts: List of strings to embed
            input_type: Override default input_type ("passage" or "query")
        
        Returns:
            List of embedding vectors
        """
        if input_type is None:
            input_type = self.input_type
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": self.id,
                "input": texts,
                "input_type": input_type or self.input_type,
                "encoding_format": "float"
            }
            
            if self.dimensions:
                payload["dimensions"] = self.dimensions
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            try:
                resp = await client.post(
                    f"{self.base_url}/embeddings",
                    json=payload,
                    headers=headers
                )
                resp.raise_for_status()
                data = resp.json()
                result = [item["embedding"] for item in data["data"]]
                # Store response like OpenAIEmbedder does
                self.response = data
                return result
            except httpx.HTTPStatusError as e:
                print(f"❌ NVIDIA embedding API error: {e.response.status_code}")
                print(f"   Response: {e.response.text}")
                raise
            except Exception as e:
                print(f"❌ Error calling NVIDIA embeddings: {e}")
                raise
    
    # Agno compatibility methods
    def get_embedding(self, text: str) -> List[float]:
        """Sync version - not recommended, use async embed() instead."""
        import asyncio
        return asyncio.run(self.embed([text]))[0]
    
    def get_embedding_and_usage(self, text: str):
        """Get embedding with usage info (sync)."""
        embedding = self.get_embedding(text)
        usage = {"total_tokens": len(text.split())}
        # Must return tuple (embedding, usage) like OpenAIEmbedder
        return embedding, usage
    
    async def async_get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text (async)."""
        embeddings = await self.embed([text])
        return embeddings[0]
    
    async def async_get_embedding_and_usage(self, text: str):
        """Get embedding with usage info (async) - PRIMARY METHOD Agno calls."""
        embedding = await self.async_get_embedding(text)
        usage = {"total_tokens": len(text.split())}
        # Must return tuple (embedding, usage) like OpenAIEmbedder
        return embedding, usage
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Sync batch embedding - not recommended, use async embed() instead."""
        import asyncio
        return asyncio.run(self.embed(texts))
    
    async def async_get_embeddings_batch_and_usage(self, texts: List[str]):
        """Get batch embeddings with usage info (async) - for batch operations."""
        embeddings = await self.embed(texts)
        # Create usage list (one per embedding)
        usage_list = [{"total_tokens": len(t.split())} for t in texts]
        # Must return tuple (embeddings, usage_list) like OpenAIEmbedder
        return embeddings, usage_list
