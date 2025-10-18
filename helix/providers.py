"""Provider abstraction layer for LLMs and embedders."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import requests
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    text: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    metadata: Dict[str, Any] = None


@dataclass
class EmbeddingResponse:
    """Standardized embedding response."""
    embeddings: List[List[float]]
    model: str
    provider: str
    metadata: Dict[str, Any] = None


@dataclass
class RerankResponse:
    """Standardized reranking response."""
    scores: List[float]
    ranked_indices: List[int]
    model: str
    provider: str
    metadata: Dict[str, Any] = None


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text from a prompt."""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Generate response from chat messages."""
        pass


class EmbedderClient(ABC):
    """Abstract base class for embedding clients."""
    
    @abstractmethod
    def embed(self, texts: List[str], **kwargs) -> EmbeddingResponse:
        """Generate embeddings for texts."""
        pass


class RerankerClient(ABC):
    """Abstract base class for reranking clients."""
    
    @abstractmethod
    def rerank(self, query: str, documents: List[str], **kwargs) -> RerankResponse:
        """Rerank documents based on relevance to query."""
        pass


class NvidiaNIMLLMClient(LLMClient):
    """NVIDIA NIM LLM client implementation."""
    
    def __init__(self, model: str, api_key: str, base_url: str, options: Dict[str, Any]):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.options = options
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text using NIM API via chat completions."""
        # Convert prompt to chat format (NIM prefers chat completions)
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Generate chat response using NIM API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "temperature": kwargs.get("temperature", 0.7),
            **self.options
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                model=self.model,
                provider="nvidia_nim",
                tokens_used=data.get("usage", {}).get("total_tokens"),
                metadata=data
            )
        except Exception as e:
            raise RuntimeError(f"NIM chat generation failed: {str(e)}")


class NvidiaNIMEmbedderClient(EmbedderClient):
    """NVIDIA NIM embedder client using NeMo Retriever."""
    
    def __init__(self, model: str, api_key: str, base_url: str, options: Dict[str, Any]):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.options = options
    
    def embed(self, texts: List[str], **kwargs) -> EmbeddingResponse:
        """Generate embeddings using NIM NeMo Retriever API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # NeMo Retriever expects 'input' field with list of texts
        payload = {
            "model": self.model,
            "input": texts,
            "input_type": kwargs.get("input_type", "query"),  # query or passage
            **self.options
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract embeddings from response
            embeddings = [item["embedding"] for item in data["data"]]
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=self.model,
                provider="nvidia_nim",
                metadata=data
            )
        except Exception as e:
            raise RuntimeError(f"NIM embedding generation failed: {str(e)}")


class NvidiaNIMRerankerClient(RerankerClient):
    """NVIDIA NIM reranker client using NeMo Retriever."""
    
    def __init__(self, model: str, api_key: str, base_url: str, options: Dict[str, Any]):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.options = options
    
    def rerank(self, query: str, documents: List[str], **kwargs) -> RerankResponse:
        """Rerank documents using NIM NeMo Retriever reranking API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": self.model,
            "query": {"text": query},
            "passages": [{"text": doc} for doc in documents],
            "top_n": kwargs.get("top_n", len(documents)),
            **self.options
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/ranking",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract scores and indices
            rankings = data.get("rankings", [])
            scores = [r["logit"] for r in rankings]
            ranked_indices = [r["index"] for r in rankings]
            
            return RerankResponse(
                scores=scores,
                ranked_indices=ranked_indices,
                model=self.model,
                provider="nvidia_nim",
                metadata=data
            )
        except Exception as e:
            raise RuntimeError(f"NIM reranking failed: {str(e)}")


class AgnoLLMClient(LLMClient):
    """Agno LLM client wrapper using Agno's model classes."""
    
    def __init__(self, model: str, options: Dict[str, Any]):
        self.model = model
        self.options = options
        self._agno_model = None
    
    def _get_agno_model(self):
        """Get Agno model instance."""
        if self._agno_model is None:
            try:
                # Import Agno models dynamically
                from agno.models.anthropic import Claude
                from agno.models.openai import OpenAIChat
                from agno.models.groq import Groq
                
                # Map model IDs to Agno model classes
                if "claude" in self.model.lower():
                    self._agno_model = Claude(id=self.model, **self.options)
                elif "gpt" in self.model.lower():
                    self._agno_model = OpenAIChat(id=self.model, **self.options)
                elif "groq" in self.model.lower():
                    self._agno_model = Groq(id=self.model, **self.options)
                else:
                    # Default to OpenAI-compatible
                    self._agno_model = OpenAIChat(id=self.model, **self.options)
            except ImportError:
                raise RuntimeError("Agno not installed. Install with: pip install agno")
        return self._agno_model
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate using Agno."""
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Chat using Agno."""
        try:
            agno_model = self._get_agno_model()
            # Use Agno's response method
            response = agno_model.response(messages=messages)
            
            return LLMResponse(
                text=response.content if hasattr(response, 'content') else str(response),
                model=self.model,
                provider="agno",
                metadata={"raw_response": response}
            )
        except Exception as e:
            raise RuntimeError(f"Agno generation failed: {str(e)}")


class AgnoEmbedderClient(EmbedderClient):
    """Agno embedder client wrapper."""
    
    def __init__(self, model: str, options: Dict[str, Any]):
        self.model = model
        self.options = options
    
    def embed(self, texts: List[str], **kwargs) -> EmbeddingResponse:
        """Generate embeddings using Agno."""
        # Placeholder - integrate with actual Agno SDK
        embeddings = [[0.1] * 768 for _ in texts]  # Dummy embeddings
        return EmbeddingResponse(
            embeddings=embeddings,
            model=self.model,
            provider="agno"
        )


class OpenAIStubLLMClient(LLMClient):
    """OpenAI stub for testing."""
    
    def __init__(self, model: str, options: Dict[str, Any]):
        self.model = model
        self.options = options
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Stub generation."""
        return LLMResponse(
            text=f"[OpenAI Stub] Response to: {prompt[:100]}",
            model=self.model,
            provider="openai_stub"
        )
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Stub chat."""
        last_msg = messages[-1]["content"] if messages else "empty"
        return LLMResponse(
            text=f"[OpenAI Stub] Chat response to: {last_msg[:100]}",
            model=self.model,
            provider="openai_stub"
        )


class OpenAIStubEmbedderClient(EmbedderClient):
    """OpenAI embedder stub for testing."""
    
    def __init__(self, model: str, options: Dict[str, Any]):
        self.model = model
        self.options = options
    
    def embed(self, texts: List[str], **kwargs) -> EmbeddingResponse:
        """Stub embeddings."""
        embeddings = [[0.5] * 1536 for _ in texts]
        return EmbeddingResponse(
            embeddings=embeddings,
            model=self.model,
            provider="openai_stub"
        )


class ProviderRegistry:
    """Registry for LLM, embedder, and reranker providers."""
    
    _llm_providers = {
        "nvidia_nim": NvidiaNIMLLMClient,
        "agno": AgnoLLMClient,
        "openai_stub": OpenAIStubLLMClient,
    }
    
    _embedder_providers = {
        "nvidia_nim": NvidiaNIMEmbedderClient,
        "agno": AgnoEmbedderClient,
        "openai_stub": OpenAIStubEmbedderClient,
    }
    
    _reranker_providers = {
        "nvidia_nim": NvidiaNIMRerankerClient,
    }
    
    @classmethod
    def get_llm(cls, provider: str, model: str, options: Optional[Dict[str, Any]] = None) -> LLMClient:
        """Get an LLM client instance."""
        if options is None:
            options = {}
        
        if provider not in cls._llm_providers:
            raise ValueError(f"Unknown LLM provider: {provider}. Available: {list(cls._llm_providers.keys())}")
        
        client_class = cls._llm_providers[provider]
        
        # Provider-specific initialization
        if provider == "nvidia_nim":
            api_key = options.get("api_key")
            if not api_key:
                raise ValueError("NIM requires 'api_key' in options")
            base_url = options.get("base_url", "https://integrate.api.nvidia.com/v1")
            return client_class(model, api_key, base_url, options)
        else:
            return client_class(model, options)
    
    @classmethod
    def get_embedder(cls, provider: str, model: str, options: Optional[Dict[str, Any]] = None) -> EmbedderClient:
        """Get an embedder client instance."""
        if options is None:
            options = {}
        
        if provider not in cls._embedder_providers:
            raise ValueError(f"Unknown embedder provider: {provider}. Available: {list(cls._embedder_providers.keys())}")
        
        client_class = cls._embedder_providers[provider]
        
        # Provider-specific initialization
        if provider == "nvidia_nim":
            api_key = options.get("api_key")
            if not api_key:
                raise ValueError("NIM requires 'api_key' in options")
            base_url = options.get("base_url", "https://integrate.api.nvidia.com/v1")
            return client_class(model, api_key, base_url, options)
        else:
            return client_class(model, options)
    
    @classmethod
    def get_reranker(cls, provider: str, model: str, options: Optional[Dict[str, Any]] = None) -> RerankerClient:
        """Get a reranker client instance."""
        if options is None:
            options = {}
        
        if provider not in cls._reranker_providers:
            raise ValueError(f"Unknown reranker provider: {provider}. Available: {list(cls._reranker_providers.keys())}")
        
        client_class = cls._reranker_providers[provider]
        
        # Provider-specific initialization
        if provider == "nvidia_nim":
            api_key = options.get("api_key")
            if not api_key:
                raise ValueError("NIM requires 'api_key' in options")
            base_url = options.get("base_url", "https://integrate.api.nvidia.com/v1")
            return client_class(model, api_key, base_url, options)
        else:
            return client_class(model, options)
    
    @classmethod
    def list_providers(cls) -> Dict[str, List[str]]:
        """List all available providers."""
        return {
            "llm": list(cls._llm_providers.keys()),
            "embedder": list(cls._embedder_providers.keys()),
            "reranker": list(cls._reranker_providers.keys())
        }