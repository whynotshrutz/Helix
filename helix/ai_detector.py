"""AI keyword detector for triggering model selection prompts."""

from typing import Set, Tuple
import re


class AIKeywordDetector:
    """Detects AI-related keywords in user prompts."""
    
    # Keywords that trigger AI/model selection prompt
    AI_KEYWORDS: Set[str] = {
        "ai", "agentic", "llm", "gpt", "llama", "model", "embedder",
        "embedding", "generative", "generator", "nim", "nemo",
        "sagemaker", "eks", "neural", "transformer", "bert",
        "language model", "ml model", "machine learning",
        "deep learning", "rag", "retrieval", "semantic search"
    }
    
    @classmethod
    def is_ai_related(cls, prompt: str) -> Tuple[bool, Set[str]]:
        """
        Check if prompt contains AI-related keywords.
        
        Args:
            prompt: User's natural language prompt
            
        Returns:
            Tuple of (is_ai_related: bool, matched_keywords: Set[str])
        """
        if not prompt:
            return False, set()
        
        # Normalize prompt
        normalized = prompt.lower()
        
        # Find matching keywords
        matched = set()
        for keyword in cls.AI_KEYWORDS:
            # Use word boundary matching to avoid false positives
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, normalized):
                matched.add(keyword)
        
        return len(matched) > 0, matched
    
    @classmethod
    def should_prompt_model_selection(cls, prompt: str, has_user_preference: bool) -> bool:
        """
        Determine if we should prompt user for model selection.
        
        Args:
            prompt: User's input
            has_user_preference: Whether user has already set preferences
            
        Returns:
            True if should prompt for model selection
        """
        is_ai, _ = cls.is_ai_related(prompt)
        
        # Only prompt if AI-related AND user hasn't set preferences
        return is_ai and not has_user_preference
    
    @classmethod
    def get_model_selection_prompt(cls, matched_keywords: Set[str]) -> str:
        """
        Generate a user-friendly prompt for model selection.
        
        Args:
            matched_keywords: Keywords that were detected
            
        Returns:
            Formatted prompt string
        """
        keywords_str = ", ".join(sorted(matched_keywords))
        
        return f"""
🤖 AI-Related Request Detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Detected keywords: {keywords_str}

Your request involves AI/ML components. Would you like to specify which model to use?

Available options:

LLM Providers:
  1. nvidia_nim (default) - NVIDIA NIM with Llama 3.1 Nemotron
  2. agno - Agno platform models
  3. openai_stub - OpenAI stub for testing

Embedder Providers:
  1. nvidia_nim (default) - NVIDIA NeMo Embeddings
  2. agno - Agno embeddings
  3. openai_stub - OpenAI embeddings stub

You can specify:
  --llm-provider <provider> --llm-model <model>
  --embedder-provider <provider> --embedder-model <model>

Or press Enter to use defaults (NVIDIA NIM).
"""


def demonstrate_detector():
    """Demonstration of the AI detector."""
    test_prompts = [
        "Create a REST API for user management",
        "Build an LLM-powered chatbot",
        "Implement semantic search with embeddings",
        "Add logging to the application",
        "Create a RAG system using NIM models",
    ]
    
    print("AI Keyword Detector Demo")
    print("=" * 50)
    
    for prompt in test_prompts:
        is_ai, keywords = AIKeywordDetector.is_ai_related(prompt)
        print(f"\nPrompt: {prompt}")
        print(f"AI-related: {is_ai}")
        if keywords:
            print(f"Keywords: {', '.join(keywords)}")


if __name__ == "__main__":
    demonstrate_detector()