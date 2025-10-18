"""
Helix - An Agno-based multi-agent coding assistant.

Accepts natural-language prompts, generates code, runs tests,
and pushes changes to GitHub with comprehensive explanations.
"""

__version__ = "2.0.0"
__author__ = "Helix Team"

from helix.agno_agents import AgnoHelixOrchestrator
from helix.workflow import (
    WorkflowOrchestrator,
    WorkflowState,
    TaskComplexity,
    WorkflowPhase,
    IntelligentRouter,
    ParallelExecutor,
    ErrorRecovery
)
from helix.providers import ProviderRegistry
from helix.config import Config
from helix.gitops import GitOpsAgent

__all__ = [
    # Main orchestrators
    "AgnoHelixOrchestrator",
    "WorkflowOrchestrator",
    
    # Workflow components
    "WorkflowState",
    "TaskComplexity",
    "WorkflowPhase",
    "IntelligentRouter",
    "ParallelExecutor",
    "ErrorRecovery",
    
    # Core components
    "ProviderRegistry",
    "Config",
    "GitOpsAgent",
]