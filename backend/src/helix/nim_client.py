"""Async client for NVIDIA NIM microservices (LLM + embeddings).

This is a simple, configurable wrapper using httpx. In production you should
use authenticated TLS endpoints and handle retries / backoff thoroughly.
"""
from typing import Any, Dict, Optional
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "http://localhost:8001")
NIM_EMBEDDING_URL = os.getenv("NIM_EMBEDDING_URL", NIM_BASE_URL + "/embeddings")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")


class NimClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or NIM_BASE_URL
        self.embedding_url = NIM_EMBEDDING_URL
        self.api_key = api_key or NVIDIA_API_KEY
        self._client = httpx.AsyncClient(timeout=30.0)

    async def generate(self, prompt: str, model: str = "meta/llama-3.1-nemotron-nano-8B-v1", **kwargs) -> Dict[str, Any]:
        """Call the NIM LLM microservice. Adapt payload to your NIM deployment API."""
        url = f"{self.base_url}/v1/generate"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": model,
            "prompt": prompt,
            **kwargs,
        }

        resp = await self._client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Call embedding service; adapt to your embedding microservice format."""
        url = f"{self.embedding_url}/v1/embeddings"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {"model": "embed-nim", "input": texts}
        resp = await self._client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        # Expect data to contain embeddings; adapt as needed
        return data.get("data") or data.get("embeddings") or []

    async def close(self):
        await self._client.aclose()
