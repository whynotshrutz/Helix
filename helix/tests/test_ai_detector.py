"""Tests for AI keyword detector."""

import pytest
from helix.ai_detector import AIKeywordDetector


def test_ai_related_detection():
    """Test AI keyword detection."""
    prompts = {
        "Create a REST API": (False, set()),
        "Build an LLM chatbot": (True, {"llm"}),
        "Add semantic search with embeddings": (True, {"semantic search", "embedding"}),
        "Implement RAG with NIM": (True, {"rag", "nim"}),
        "Create logging module": (False, set()),
    }
    
    for prompt, (expected_is_ai, expected_keywords_subset) in prompts.items():
        is_ai, keywords = AIKeywordDetector.is_ai_related(prompt)
        assert is_ai == expected_is_ai, f"Failed for: {prompt}"
        if expected_keywords_subset:
            assert expected_keywords_subset.issubset(keywords), f"Keywords mismatch for: {prompt}"


def test_should_prompt_model_selection():
    """Test model selection prompt logic."""
    # AI-related without preferences -> should prompt
    assert AIKeywordDetector.should_prompt_model_selection("Build an LLM", has_user_preference=False)
    
    # AI-related with preferences -> should NOT prompt
    assert not AIKeywordDetector.should_prompt_model_selection("Build an LLM", has_user_preference=True)
    
    # Not AI-related -> should NOT prompt
    assert not AIKeywordDetector.should_prompt_model_selection("Create API", has_user_preference=False)


def test_get_model_selection_prompt():
    """Test model selection prompt generation."""
    keywords = {"llm", "embedder"}
    prompt = AIKeywordDetector.get_model_selection_prompt(keywords)
    
    assert "AI-Related Request Detected" in prompt
    assert "nvidia_nim" in prompt
    assert "agno" in prompt
    assert "openai_stub" in prompt