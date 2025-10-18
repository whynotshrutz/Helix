"""Tests for provider abstraction."""

import pytest
from helix.providers import ProviderRegistry, LLMResponse, EmbeddingResponse


def test_list_providers():
    """Test listing available providers."""
    providers = ProviderRegistry.list_providers()
    
    assert "llm" in providers
    assert "embedder" in providers
    assert "nvidia_nim" in providers["llm"]
    assert "agno" in providers["llm"]
    assert "openai_stub" in providers["llm"]


def test_get_stub_llm():
    """Test getting OpenAI stub LLM."""
    llm = ProviderRegistry.get_llm("openai_stub", "gpt-4", {})
    
    assert llm is not None
    
    response = llm.generate("Test prompt")
    assert isinstance(response, LLMResponse)
    assert response.provider == "openai_stub"
    assert "Test prompt" in response.text


def test_get_stub_embedder():
    """Test getting OpenAI stub embedder."""
    embedder = ProviderRegistry.get_embedder("openai_stub", "text-embedding-ada-002", {})
    
    assert embedder is not None
    
    response = embedder.embed(["test1", "test2"])
    assert isinstance(response, EmbeddingResponse)
    assert response.provider == "openai_stub"
    assert len(response.embeddings) == 2


def test_invalid_provider():
    """Test handling of invalid provider."""
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        ProviderRegistry.get_llm("invalid_provider", "model", {})


def test_nim_llm_requires_api_key():
    """Test that NIM provider requires API key."""
    with pytest.raises(ValueError, match="NIM requires 'api_key'"):
        ProviderRegistry.get_llm("nvidia_nim", "llama-3.1", {})


def test_chat_interface():
    """Test chat interface."""
    llm = ProviderRegistry.get_llm("openai_stub", "gpt-4", {})
    
    messages = [
        {"role": "user", "content": "Hello"}
    ]
    
    response = llm.chat(messages)
    assert isinstance(response, LLMResponse)
    assert "Hello" in response.text