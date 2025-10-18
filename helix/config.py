"""Configuration management for Helix."""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import json


@dataclass
class Config:
    """Runtime configuration for Helix."""
    
    # GitHub settings
    gh_token: Optional[str] = None
    gh_oauth_token: Optional[str] = None
    
    # Provider settings
    default_provider: str = "nvidia_nim"
    default_model: str = "meta/llama-3.1-70b-instruct"  # Meta Llama 3.1 70B via NVIDIA NIM
    default_embedder_provider: str = "nvidia_nim"
    default_embedder_model: str = "nvidia/nv-embedqa-e5-v5"  # NeMo Retriever embedding (commonly available)
    default_reranker_model: str = "nvidia/nv-rerankqa-mistral-4b-v3"  # NeMo Retriever reranking
    
    # User-selected overrides
    selected_provider: Optional[str] = None
    selected_model: Optional[str] = None
    selected_embedder_provider: Optional[str] = None
    selected_embedder_model: Optional[str] = None
    
    # NIM settings
    nim_api_key: Optional[str] = None
    nim_base_url: str = "https://integrate.api.nvidia.com/v1"
    
    # Agno settings
    agno_api_key: Optional[str] = None
    agno_db_path: str = "helix_agno.db"
    agno_use_mcp: bool = False  # Enable Model Context Protocol support
    
    # AWS settings
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-west-2"
    
    # Deployment settings
    deploy_target: str = "local"  # local, eks, sagemaker
    
    # GitOps settings
    require_human_confirmation: bool = False
    auto_push: bool = True
    create_pr: bool = False
    branch_prefix: str = "helix"
    
    # Test settings
    run_tests_before_push: bool = True
    run_static_checks: bool = True
    fail_on_test_failure: bool = True
    
    # Paths
    workspace_dir: Path = field(default_factory=lambda: Path.cwd())
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".helix" / "cache")
    
    # Logging
    log_level: str = "INFO"
    enable_metrics: bool = False
    
    # Additional options
    options: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            gh_token=os.getenv("GH_TOKEN"),
            gh_oauth_token=os.getenv("GH_OAUTH_TOKEN"),
            nim_api_key=os.getenv("NIM_API_KEY"),
            agno_api_key=os.getenv("AGNO_API_KEY"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_region=os.getenv("AWS_REGION", "us-west-2"),
            deploy_target=os.getenv("HELIX_DEPLOY_TARGET", "local"),
            require_human_confirmation=os.getenv("HELIX_REQUIRE_CONFIRMATION", "false").lower() == "true",
            auto_push=os.getenv("HELIX_AUTO_PUSH", "true").lower() == "true",
            create_pr=os.getenv("HELIX_CREATE_PR", "false").lower() == "true",
            log_level=os.getenv("HELIX_LOG_LEVEL", "INFO"),
            agno_use_mcp=os.getenv("AGNO_USE_MCP", "false").lower() == "true",
        )
    
    def get_provider(self) -> str:
        """Get the active provider (user-selected or default)."""
        return self.selected_provider or self.default_provider
    
    def get_model(self) -> str:
        """Get the active model (user-selected or default)."""
        return self.selected_model or self.default_model
    
    def get_embedder_provider(self) -> str:
        """Get the active embedder provider (user-selected or default)."""
        return self.selected_embedder_provider or self.default_embedder_provider
    
    def get_embedder_model(self) -> str:
        """Get the active embedder model (user-selected or default)."""
        return self.selected_embedder_model or self.default_embedder_model
    
    def save_user_preferences(self, filepath: Optional[Path] = None) -> None:
        """Save user model preferences to disk."""
        if filepath is None:
            filepath = self.cache_dir / "user_preferences.json"
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        prefs = {
            "provider": self.selected_provider,
            "model": self.selected_model,
            "embedder_provider": self.selected_embedder_provider,
            "embedder_model": self.selected_embedder_model,
        }
        
        with open(filepath, "w") as f:
            json.dump(prefs, f, indent=2)
    
    def load_user_preferences(self, filepath: Optional[Path] = None) -> None:
        """Load user model preferences from disk."""
        if filepath is None:
            filepath = self.cache_dir / "user_preferences.json"
        
        if not filepath.exists():
            return
        
        with open(filepath, "r") as f:
            prefs = json.load(f)
        
        self.selected_provider = prefs.get("provider")
        self.selected_model = prefs.get("model")
        self.selected_embedder_provider = prefs.get("embedder_provider")
        self.selected_embedder_model = prefs.get("embedder_model")