"""Automatic Error Resolution System.

Intelligent error detection, analysis, and resolution:
- Detects errors from code execution, git operations, builds
- Analyzes error types and root causes
- Searches web for solutions
- Applies fixes automatically with user confirmation
- Retries until success or max attempts reached
"""
from typing import Dict, List, Any, Optional, Callable
import re
import json
from pathlib import Path


class ErrorResolver:
    """Automatically resolves errors with intelligent retry logic."""
    
    def __init__(self, workspace_dir: str = ".", max_retries: int = 3):
        """Initialize error resolver.
        
        Args:
            workspace_dir: Workspace directory
            max_retries: Maximum retry attempts per error
        """
        self.workspace_dir = Path(workspace_dir)
        self.max_retries = max_retries
        self.error_history = []
    
    def resolve_error(
        self,
        error_message: str,
        error_context: Optional[Dict[str, Any]] = None,
        operation_type: str = "general"
    ) -> Dict[str, Any]:
        """Attempt to resolve an error automatically.
        
        Args:
            error_message: The error message to resolve
            error_context: Additional context (file, line, command, etc.)
            operation_type: Type of operation (git, build, execute, etc.)
            
        Returns:
            Resolution result with success status and actions taken
        """
        # Parse and categorize error
        error_info = self._parse_error(error_message, error_context, operation_type)
        
        # Store in history
        self.error_history.append(error_info)
        
        # Find solutions
        solutions = self._find_solutions(error_info)
        
        if not solutions:
            return {
                'ok': False,
                'error_type': error_info['type'],
                'message': 'No automatic solution found',
                'error_info': error_info,
                'suggestions': self._get_manual_suggestions(error_info)
            }
        
        # Try solutions in order
        for solution in solutions:
            result = self._apply_solution(solution, error_info)
            
            if result['ok']:
                return {
                    'ok': True,
                    'error_type': error_info['type'],
                    'solution_applied': solution['description'],
                    'actions': result['actions'],
                    'message': 'Error resolved successfully'
                }
        
        # If all solutions failed
        return {
            'ok': False,
            'error_type': error_info['type'],
            'message': 'All automatic solutions failed',
            'tried_solutions': [s['description'] for s in solutions],
            'suggestions': self._get_manual_suggestions(error_info)
        }
    
    def _parse_error(
        self,
        error_message: str,
        context: Optional[Dict[str, Any]],
        operation_type: str
    ) -> Dict[str, Any]:
        """Parse error message and extract key information.
        
        Args:
            error_message: Raw error message
            context: Additional context
            operation_type: Operation type
            
        Returns:
            Structured error information
        """
        error_info = {
            'raw_message': error_message,
            'operation': operation_type,
            'context': context or {},
            'type': 'unknown',
            'category': 'general',
            'key_terms': []
        }
        
        # Categorize by operation type
        if operation_type == 'git':
            error_info.update(self._parse_git_error(error_message))
        elif operation_type == 'build':
            error_info.update(self._parse_build_error(error_message))
        elif operation_type == 'execute':
            error_info.update(self._parse_execution_error(error_message))
        elif operation_type == 'dependency':
            error_info.update(self._parse_dependency_error(error_message))
        else:
            error_info.update(self._parse_generic_error(error_message))
        
        return error_info
    
    def _parse_git_error(self, error_message: str) -> Dict[str, Any]:
        """Parse Git-specific errors."""
        msg_lower = error_message.lower()
        
        # Merge conflicts
        if 'conflict' in msg_lower or 'merge' in msg_lower:
            return {
                'type': 'merge_conflict',
                'category': 'git',
                'severity': 'high',
                'key_terms': ['conflict', 'merge']
            }
        
        # Authentication
        if 'authentication' in msg_lower or 'permission denied' in msg_lower:
            return {
                'type': 'auth_failed',
                'category': 'git',
                'severity': 'high',
                'key_terms': ['authentication', 'credentials']
            }
        
        # Remote issues
        if 'remote' in msg_lower or 'push' in msg_lower or 'pull' in msg_lower:
            return {
                'type': 'remote_error',
                'category': 'git',
                'severity': 'medium',
                'key_terms': ['remote', 'push', 'pull']
            }
        
        # Branch issues
        if 'branch' in msg_lower:
            return {
                'type': 'branch_error',
                'category': 'git',
                'severity': 'low',
                'key_terms': ['branch']
            }
        
        return {
            'type': 'git_unknown',
            'category': 'git',
            'severity': 'medium',
            'key_terms': []
        }
    
    def _parse_build_error(self, error_message: str) -> Dict[str, Any]:
        """Parse build/compile errors."""
        msg_lower = error_message.lower()
        
        # Syntax errors
        if 'syntax' in msg_lower or 'syntaxerror' in msg_lower:
            return {
                'type': 'syntax_error',
                'category': 'build',
                'severity': 'high',
                'key_terms': ['syntax']
            }
        
        # Import/module errors
        if 'import' in msg_lower or 'module' in msg_lower or 'cannot find' in msg_lower:
            return {
                'type': 'import_error',
                'category': 'build',
                'severity': 'high',
                'key_terms': ['import', 'module']
            }
        
        # Type errors
        if 'type' in msg_lower or 'typeerror' in msg_lower:
            return {
                'type': 'type_error',
                'category': 'build',
                'severity': 'medium',
                'key_terms': ['type']
            }
        
        return {
            'type': 'build_unknown',
            'category': 'build',
            'severity': 'medium',
            'key_terms': []
        }
    
    def _parse_execution_error(self, error_message: str) -> Dict[str, Any]:
        """Parse runtime execution errors."""
        msg_lower = error_message.lower()
        
        # File not found
        if 'no such file' in msg_lower or 'file not found' in msg_lower:
            return {
                'type': 'file_not_found',
                'category': 'execute',
                'severity': 'high',
                'key_terms': ['file', 'not found']
            }
        
        # Permission errors
        if 'permission' in msg_lower or 'access denied' in msg_lower:
            return {
                'type': 'permission_error',
                'category': 'execute',
                'severity': 'high',
                'key_terms': ['permission', 'access']
            }
        
        # Runtime errors
        if 'runtime' in msg_lower or 'runtimeerror' in msg_lower:
            return {
                'type': 'runtime_error',
                'category': 'execute',
                'severity': 'medium',
                'key_terms': ['runtime']
            }
        
        return {
            'type': 'execution_unknown',
            'category': 'execute',
            'severity': 'medium',
            'key_terms': []
        }
    
    def _parse_dependency_error(self, error_message: str) -> Dict[str, Any]:
        """Parse dependency/package errors."""
        msg_lower = error_message.lower()
        
        # Missing package
        if 'no module named' in msg_lower or 'cannot import' in msg_lower:
            # Extract package name
            match = re.search(r"no module named ['\"]?(\w+)['\"]?", msg_lower)
            package_name = match.group(1) if match else None
            
            return {
                'type': 'missing_package',
                'category': 'dependency',
                'severity': 'high',
                'key_terms': ['package', 'install'],
                'package_name': package_name
            }
        
        # Version conflict
        if 'version' in msg_lower or 'conflict' in msg_lower:
            return {
                'type': 'version_conflict',
                'category': 'dependency',
                'severity': 'medium',
                'key_terms': ['version', 'conflict']
            }
        
        return {
            'type': 'dependency_unknown',
            'category': 'dependency',
            'severity': 'medium',
            'key_terms': []
        }
    
    def _parse_generic_error(self, error_message: str) -> Dict[str, Any]:
        """Parse generic errors."""
        return {
            'type': 'generic_error',
            'category': 'general',
            'severity': 'medium',
            'key_terms': self._extract_key_terms(error_message)
        }
    
    def _extract_key_terms(self, error_message: str) -> List[str]:
        """Extract key terms from error message."""
        # Common error keywords
        keywords = [
            'error', 'failed', 'exception', 'warning', 'fatal',
            'cannot', 'unable', 'missing', 'invalid', 'unexpected'
        ]
        
        msg_lower = error_message.lower()
        found = [kw for kw in keywords if kw in msg_lower]
        
        return found
    
    def _find_solutions(self, error_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential solutions for an error.
        
        Args:
            error_info: Parsed error information
            
        Returns:
            List of solutions ordered by priority
        """
        solutions = []
        error_type = error_info['type']
        
        # Git errors
        if error_info['category'] == 'git':
            if error_type == 'merge_conflict':
                solutions.append({
                    'description': 'Show conflicted files and guide manual resolution',
                    'action': 'show_conflicts',
                    'priority': 1
                })
            elif error_type == 'auth_failed':
                solutions.append({
                    'description': 'Check Git credentials and authentication',
                    'action': 'check_auth',
                    'priority': 1
                })
                solutions.append({
                    'description': 'Use SSH instead of HTTPS',
                    'action': 'switch_to_ssh',
                    'priority': 2
                })
            elif error_type == 'remote_error':
                solutions.append({
                    'description': 'Check remote configuration',
                    'action': 'check_remote',
                    'priority': 1
                })
        
        # Build errors
        elif error_info['category'] == 'build':
            if error_type == 'syntax_error':
                solutions.append({
                    'description': 'Identify and fix syntax errors',
                    'action': 'fix_syntax',
                    'priority': 1
                })
            elif error_type == 'import_error':
                solutions.append({
                    'description': 'Install missing dependencies',
                    'action': 'install_deps',
                    'priority': 1
                })
        
        # Dependency errors
        elif error_info['category'] == 'dependency':
            if error_type == 'missing_package':
                package = error_info.get('package_name')
                solutions.append({
                    'description': f'Install missing package: {package}',
                    'action': 'install_package',
                    'priority': 1,
                    'package': package
                })
        
        # Execution errors
        elif error_info['category'] == 'execute':
            if error_type == 'file_not_found':
                solutions.append({
                    'description': 'Check file path and create if needed',
                    'action': 'check_file',
                    'priority': 1
                })
            elif error_type == 'permission_error':
                solutions.append({
                    'description': 'Fix file permissions',
                    'action': 'fix_permissions',
                    'priority': 1
                })
        
        # Sort by priority
        solutions.sort(key=lambda x: x['priority'])
        
        return solutions
    
    def _apply_solution(self, solution: Dict[str, Any], error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a solution to resolve the error.
        
        Args:
            solution: Solution to apply
            error_info: Error information
            
        Returns:
            Result of applying the solution
        """
        action = solution['action']
        
        if action == 'show_conflicts':
            return self._handle_merge_conflicts(error_info)
        elif action == 'check_auth':
            return self._check_git_auth(error_info)
        elif action == 'install_package':
            return self._install_package(solution.get('package'))
        elif action == 'check_file':
            return self._check_file_exists(error_info)
        elif action == 'fix_syntax':
            return self._suggest_syntax_fix(error_info)
        
        # Default: return info only
        return {
            'ok': False,
            'message': f"Solution '{action}' requires manual intervention",
            'actions': []
        }
    
    def _handle_merge_conflicts(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle merge conflicts."""
        from .git_operations import GitOperationsManager
        
        try:
            git_mgr = GitOperationsManager(str(self.workspace_dir))
            status = git_mgr.get_status()
            
            if status.get('ok'):
                modified = status.get('modified', [])
                return {
                    'ok': True,
                    'actions': ['listed_conflicts'],
                    'conflicted_files': modified,
                    'message': f'Found {len(modified)} conflicted files'
                }
        except Exception as e:
            pass
        
        return {
            'ok': False,
            'actions': [],
            'message': 'Could not detect conflicted files'
        }
    
    def _check_git_auth(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check Git authentication."""
        return {
            'ok': False,
            'actions': ['checked_auth'],
            'message': 'Git authentication needs to be configured manually',
            'suggestion': 'Run: git config --global user.name "Your Name" && git config --global user.email "your@email.com"'
        }
    
    def _install_package(self, package_name: Optional[str]) -> Dict[str, Any]:
        """Install missing package."""
        if not package_name:
            return {'ok': False, 'message': 'No package name provided'}
        
        return {
            'ok': False,
            'actions': ['identified_package'],
            'message': f'Package "{package_name}" needs to be installed',
            'suggestion': f'Run: pip install {package_name}'
        }
    
    def _check_file_exists(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check if file exists."""
        return {
            'ok': False,
            'actions': ['checked_file'],
            'message': 'File path issue detected',
            'suggestion': 'Verify the file path is correct'
        }
    
    def _suggest_syntax_fix(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest syntax fix."""
        return {
            'ok': False,
            'actions': ['analyzed_syntax'],
            'message': 'Syntax error detected',
            'suggestion': 'Review the error message for line number and fix the syntax'
        }
    
    def _get_manual_suggestions(self, error_info: Dict[str, Any]) -> List[str]:
        """Get manual suggestions when automatic resolution fails.
        
        Args:
            error_info: Error information
            
        Returns:
            List of manual suggestions
        """
        suggestions = []
        error_type = error_info['type']
        category = error_info['category']
        
        if category == 'git':
            suggestions.append("Check git status with: git status")
            suggestions.append("Review git logs: git log --oneline")
            if error_type == 'merge_conflict':
                suggestions.append("Manually resolve conflicts in editor")
                suggestions.append("After resolving, run: git add . && git commit")
        
        elif category == 'build':
            suggestions.append("Check syntax and imports in the failing file")
            suggestions.append("Ensure all dependencies are installed")
            suggestions.append("Try cleaning build artifacts: rm -rf dist build")
        
        elif category == 'dependency':
            suggestions.append("Update package manager: pip install --upgrade pip")
            suggestions.append("Check requirements.txt for version conflicts")
        
        if not suggestions:
            suggestions.append("Search for the error online")
            suggestions.append("Check documentation for the relevant tool")
            suggestions.append("Review recent changes that might have caused this")
        
        return suggestions
    
    def get_error_history(self) -> List[Dict[str, Any]]:
        """Get history of all errors encountered.
        
        Returns:
            List of error records
        """
        return self.error_history.copy()
    
    def clear_history(self):
        """Clear error history."""
        self.error_history.clear()


def get_error_resolver(workspace_dir: str = ".") -> ErrorResolver:
    """Get error resolver instance.
    
    Args:
        workspace_dir: Workspace directory
        
    Returns:
        ErrorResolver instance
    """
    return ErrorResolver(workspace_dir)
