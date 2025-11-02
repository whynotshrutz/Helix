"""Safety Manager for Helix - Handles user confirmations for destructive operations.

This module implements the interactive confirmation layer that asks users before
performing potentially destructive operations.
"""
from typing import Dict, Any, Optional, Callable
from enum import Enum
import json
from pathlib import Path


class OperationType(Enum):
    """Types of operations requiring confirmation."""
    READ = "read"  # Safe, no confirmation needed
    CREATE = "create"  # First-time creation needs confirmation
    UPDATE = "update"  # Overwriting existing files
    DELETE = "delete"  # Destructive operation
    EXECUTE = "execute"  # Code execution
    GIT_PUSH = "git_push"  # Push to remote
    GIT_PR = "git_pr"  # Create pull request
    GIT_DELETE = "git_delete"  # Delete branch/tag


class SafetyMode(Enum):
    """Safety modes for the agent."""
    STRICT = "strict"  # Ask for everything
    NORMAL = "normal"  # Ask only for destructive ops
    PERMISSIVE = "permissive"  # Ask only once per session
    UNSAFE = "unsafe"  # Never ask (dangerous!)


class SafetyManager:
    """Manages user confirmations and tracks approved operations.
    
    Features:
    - Tracks which operations have been confirmed in the session
    - Supports different safety modes
    - Provides clear confirmation prompts
    - Remembers user preferences per session
    """
    
    def __init__(self, mode: SafetyMode = SafetyMode.NORMAL, session_file: Optional[str] = None):
        """Initialize the safety manager.
        
        Args:
            mode: Safety mode to use
            session_file: Optional file to persist confirmations across runs
        """
        self.mode = mode
        self.session_file = session_file
        self.confirmed_operations: Dict[str, set] = {
            "files": set(),  # Confirmed file operations
            "git": set(),  # Confirmed git operations
            "code": set(),  # Confirmed code executions
        }
        self.first_time_operations: set = set()
        
        # Load session state if available
        if session_file and Path(session_file).exists():
            self._load_session()
    
    def needs_confirmation(
        self, 
        operation: OperationType, 
        target: str,
        details: Optional[str] = None
    ) -> tuple[bool, str]:
        """Check if an operation needs user confirmation.
        
        Args:
            operation: Type of operation
            target: Target of operation (file path, branch name, etc.)
            details: Additional details about the operation
            
        Returns:
            Tuple of (needs_confirmation, prompt_message)
        """
        # UNSAFE mode: never ask
        if self.mode == SafetyMode.UNSAFE:
            return False, ""
        
        # READ operations never need confirmation
        if operation == OperationType.READ:
            return False, ""
        
        # Check if already confirmed in this session
        operation_key = f"{operation.value}:{target}"
        
        if self.mode == SafetyMode.PERMISSIVE:
            # In permissive mode, ask only once per operation type
            if operation.value in self.first_time_operations:
                return False, ""
            self.first_time_operations.add(operation.value)
        
        # Generate confirmation prompt
        prompt = self._generate_prompt(operation, target, details)
        
        # STRICT mode: always ask
        if self.mode == SafetyMode.STRICT:
            return True, prompt
        
        # NORMAL mode: ask for destructive operations or first-time creates
        if operation in [OperationType.DELETE, OperationType.GIT_DELETE]:
            return True, prompt
        
        if operation in [OperationType.UPDATE, OperationType.GIT_PUSH, OperationType.GIT_PR]:
            category = self._get_category(operation)
            if operation_key not in self.confirmed_operations.get(category, set()):
                return True, prompt
        
        if operation == OperationType.CREATE:
            # First-time file creation needs confirmation
            if target not in self.confirmed_operations.get("files", set()):
                return True, prompt
        
        return False, ""
    
    def confirm_operation(self, operation: OperationType, target: str) -> None:
        """Mark an operation as confirmed.
        
        Args:
            operation: Type of operation
            target: Target that was confirmed
        """
        category = self._get_category(operation)
        operation_key = f"{operation.value}:{target}"
        
        if category not in self.confirmed_operations:
            self.confirmed_operations[category] = set()
        
        self.confirmed_operations[category].add(operation_key)
        
        # Save session state
        if self.session_file:
            self._save_session()
    
    def _get_category(self, operation: OperationType) -> str:
        """Get the category for an operation type."""
        if operation in [OperationType.CREATE, OperationType.UPDATE, OperationType.DELETE]:
            return "files"
        elif operation in [OperationType.GIT_PUSH, OperationType.GIT_PR, OperationType.GIT_DELETE]:
            return "git"
        elif operation == OperationType.EXECUTE:
            return "code"
        return "other"
    
    def _generate_prompt(self, operation: OperationType, target: str, details: Optional[str]) -> str:
        """Generate a user-friendly confirmation prompt.
        
        Args:
            operation: Type of operation
            target: Target of operation
            details: Additional details
            
        Returns:
            Confirmation prompt string
        """
        prompts = {
            OperationType.CREATE: f"📝 Create new file: {target}",
            OperationType.UPDATE: f"⚠️ Overwrite existing file: {target}",
            OperationType.DELETE: f"🗑️ DELETE file: {target} (cannot be undone!)",
            OperationType.EXECUTE: f"⚙️ Execute code: {target}",
            OperationType.GIT_PUSH: f"🚀 Push changes to remote: {target}",
            OperationType.GIT_PR: f"🔀 Create pull request: {target}",
            OperationType.GIT_DELETE: f"🗑️ DELETE branch/tag: {target} (cannot be undone!)",
        }
        
        prompt = prompts.get(operation, f"Perform operation on: {target}")
        
        if details:
            prompt += f"\n   Details: {details}"
        
        prompt += "\n   Proceed? (yes/no): "
        return prompt
    
    def _save_session(self) -> None:
        """Save session state to file."""
        if not self.session_file:
            return
        
        state = {
            "mode": self.mode.value,
            "confirmed_operations": {
                k: list(v) for k, v in self.confirmed_operations.items()
            },
            "first_time_operations": list(self.first_time_operations)
        }
        
        Path(self.session_file).parent.mkdir(parents=True, exist_ok=True)
        Path(self.session_file).write_text(json.dumps(state, indent=2))
    
    def _load_session(self) -> None:
        """Load session state from file."""
        if not self.session_file or not Path(self.session_file).exists():
            return
        
        try:
            state = json.loads(Path(self.session_file).read_text())
            self.mode = SafetyMode(state.get("mode", "normal"))
            self.confirmed_operations = {
                k: set(v) for k, v in state.get("confirmed_operations", {}).items()
            }
            self.first_time_operations = set(state.get("first_time_operations", []))
        except Exception as e:
            print(f"Warning: Failed to load session state: {e}")
    
    def reset_session(self) -> None:
        """Clear all confirmed operations for a fresh start."""
        self.confirmed_operations = {"files": set(), "git": set(), "code": set()}
        self.first_time_operations = set()
        
        if self.session_file and Path(self.session_file).exists():
            Path(self.session_file).unlink()
    
    def set_mode(self, mode: SafetyMode) -> None:
        """Change the safety mode.
        
        Args:
            mode: New safety mode
        """
        self.mode = mode
        if self.session_file:
            self._save_session()


# Global safety manager instance
_safety_manager: Optional[SafetyManager] = None


def get_safety_manager(
    mode: SafetyMode = SafetyMode.NORMAL,
    session_file: str = "./tmp/helix_safety_session.json"
) -> SafetyManager:
    """Get or create the global safety manager instance.
    
    Args:
        mode: Safety mode to use
        session_file: File to persist session state
        
    Returns:
        SafetyManager instance
    """
    global _safety_manager
    
    if _safety_manager is None:
        _safety_manager = SafetyManager(mode=mode, session_file=session_file)
    
    return _safety_manager


def ask_user_confirmation(prompt: str, timeout: int = 30) -> bool:
    """Ask user for confirmation (for CLI usage).
    
    Args:
        prompt: Confirmation prompt
        timeout: Timeout in seconds
        
    Returns:
        True if user confirmed, False otherwise
    """
    # In a real implementation, this would integrate with VS Code UI
    # For now, this is a placeholder that always returns True in automated mode
    print(f"\n{prompt}")
    
    # TODO: Integrate with VS Code extension to show confirmation dialog
    # For now, return True to allow operations
    return True
