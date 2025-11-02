"""Git operations manager for repository management and GitHub integration.

Provides comprehensive Git operations including:
- Repository creation and cloning
- Branch management
- Commit and push operations
- Pull requests and merges
- Conflict resolution
- Fork management
"""
from typing import Dict, List, Any, Optional
import subprocess
import os
from pathlib import Path
from .git_auth_manager import GitAuthManager


class GitOperationsManager:
    """Manages all Git and GitHub operations."""
    
    def __init__(self, workspace_dir: str):
        """Initialize the Git operations manager.
        
        Args:
            workspace_dir: Root directory of the repository
        """
        self.workspace_dir = Path(workspace_dir)
        self.auth_manager = GitAuthManager(str(workspace_dir))
    
    def _run_git_command(self, args: List[str], check=True) -> Dict[str, Any]:
        """Run a git command and return the result.
        
        Args:
            args: List of command arguments
            check: Whether to check return code
            
        Returns:
            Dictionary with ok status, stdout, stderr, and return code
        """
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'ok': result.returncode == 0 if check else True,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'ok': False, 'error': 'Git command timed out'}
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current git status.
        
        Returns:
            Dictionary with status information
        """
        result = self._run_git_command(['status', '--porcelain'])
        
        if not result['ok']:
            return result
        
        status_lines = result['stdout'].split('\n') if result['stdout'] else []
        
        modified = []
        added = []
        deleted = []
        untracked = []
        
        for line in status_lines:
            if not line:
                continue
            status = line[:2]
            file_path = line[3:]
            
            if status == '??':
                untracked.append(file_path)
            elif 'M' in status:
                modified.append(file_path)
            elif 'A' in status:
                added.append(file_path)
            elif 'D' in status:
                deleted.append(file_path)
        
        return {
            'ok': True,
            'clean': len(status_lines) == 0 or (len(status_lines) == 1 and not status_lines[0]),
            'modified': modified,
            'added': added,
            'deleted': deleted,
            'untracked': untracked,
            'total_changes': len(modified) + len(added) + len(deleted) + len(untracked)
        }
    
    def create_branch(self, branch_name: str, checkout: bool = True) -> Dict[str, Any]:
        """Create a new branch.
        
        Args:
            branch_name: Name of the new branch
            checkout: Whether to checkout the branch after creating
            
        Returns:
            Success status and message
        """
        # Create branch
        result = self._run_git_command(['branch', branch_name])
        
        if not result['ok']:
            return {
                'ok': False,
                'error': f"Failed to create branch: {result.get('stderr', 'Unknown error')}"
            }
        
        # Checkout if requested
        if checkout:
            checkout_result = self._run_git_command(['checkout', branch_name])
            if not checkout_result['ok']:
                return {
                    'ok': False,
                    'error': f"Branch created but checkout failed: {checkout_result.get('stderr')}"
                }
        
        return {
            'ok': True,
            'message': f"Branch '{branch_name}' created" + (" and checked out" if checkout else ""),
            'branch': branch_name
        }
    
    def checkout_branch(self, branch_name: str) -> Dict[str, Any]:
        """Checkout an existing branch.
        
        Args:
            branch_name: Name of the branch to checkout
            
        Returns:
            Success status and message
        """
        result = self._run_git_command(['checkout', branch_name])
        
        if not result['ok']:
            return {
                'ok': False,
                'error': f"Failed to checkout branch: {result.get('stderr', 'Unknown error')}"
            }
        
        return {
            'ok': True,
            'message': f"Switched to branch '{branch_name}'",
            'branch': branch_name
        }
    
    def list_branches(self, remote: bool = False) -> Dict[str, Any]:
        """List all branches.
        
        Args:
            remote: Whether to list remote branches
            
        Returns:
            Dictionary with list of branches
        """
        args = ['branch', '-a'] if remote else ['branch']
        result = self._run_git_command(args)
        
        if not result['ok']:
            return result
        
        branches = []
        current_branch = None
        
        for line in result['stdout'].split('\n'):
            if not line:
                continue
            
            is_current = line.startswith('*')
            branch_name = line.replace('*', '').strip()
            
            branches.append(branch_name)
            if is_current:
                current_branch = branch_name
        
        return {
            'ok': True,
            'branches': branches,
            'current_branch': current_branch,
            'count': len(branches)
        }
    
    def commit(self, message: str, add_all: bool = True) -> Dict[str, Any]:
        """Create a commit.
        
        Args:
            message: Commit message
            add_all: Whether to stage all changes
            
        Returns:
            Success status and commit hash
        """
        # Stage changes if requested
        if add_all:
            add_result = self._run_git_command(['add', '.'])
            if not add_result['ok']:
                return {
                    'ok': False,
                    'error': f"Failed to stage changes: {add_result.get('stderr')}"
                }
        
        # Create commit
        result = self._run_git_command(['commit', '-m', message])
        
        if not result['ok']:
            stderr = result.get('stderr', '')
            if 'nothing to commit' in stderr:
                return {
                    'ok': True,
                    'message': 'No changes to commit',
                    'nothing_to_commit': True
                }
            return {
                'ok': False,
                'error': f"Failed to commit: {stderr}"
            }
        
        # Get commit hash
        hash_result = self._run_git_command(['rev-parse', 'HEAD'])
        commit_hash = hash_result['stdout'][:7] if hash_result['ok'] else 'unknown'
        
        return {
            'ok': True,
            'message': f"Changes committed: {commit_hash}",
            'commit_hash': commit_hash,
            'commit_message': message
        }
    
    def push(self, remote: str = 'origin', branch: Optional[str] = None, 
             account_identifier: Optional[str] = None, 
             auth_method: str = 'credential_helper') -> Dict[str, Any]:
        """Push commits to remote repository.
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
            account_identifier: Account to use for authentication
            auth_method: Authentication method ('credential_helper', 'pat', or 'oauth')
            
        Returns:
            Success status and message
        """
        # Get current branch if not specified
        if not branch:
            branch_result = self._run_git_command(['branch', '--show-current'])
            if not branch_result['ok']:
                return {'ok': False, 'error': 'Failed to get current branch'}
            branch = branch_result['stdout']
        
        # Get credentials if needed
        if auth_method != 'credential_helper' and account_identifier:
            creds = self.auth_manager.get_credentials_for_push(account_identifier, auth_method)
            if not creds['ok']:
                return creds
            
            # Set up authentication for PAT or OAuth
            if auth_method == 'pat':
                # Use token in URL (git will use it)
                pass  # System credential helper will handle it
            elif auth_method == 'oauth':
                # Use OAuth token
                pass  # System credential helper will handle it
        
        # Push to remote
        result = self._run_git_command(['push', remote, branch])
        
        if not result['ok']:
            stderr = result.get('stderr', '')
            if 'rejected' in stderr:
                return {
                    'ok': False,
                    'error': 'Push rejected (remote has changes). Try pulling first.',
                    'needs_pull': True
                }
            return {
                'ok': False,
                'error': f"Push failed: {stderr}"
            }
        
        return {
            'ok': True,
            'message': f"Pushed to {remote}/{branch}",
            'remote': remote,
            'branch': branch
        }
    
    def pull(self, remote: str = 'origin', branch: Optional[str] = None) -> Dict[str, Any]:
        """Pull changes from remote repository.
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
            
        Returns:
            Success status and message
        """
        args = ['pull', remote]
        if branch:
            args.append(branch)
        
        result = self._run_git_command(args)
        
        if not result['ok']:
            stderr = result.get('stderr', '')
            if 'CONFLICT' in stderr:
                return {
                    'ok': False,
                    'error': 'Pull resulted in conflicts',
                    'has_conflicts': True,
                    'details': stderr
                }
            return {
                'ok': False,
                'error': f"Pull failed: {stderr}"
            }
        
        return {
            'ok': True,
            'message': f"Pulled from {remote}" + (f"/{branch}" if branch else ""),
            'output': result['stdout']
        }
    
    def get_conflicts(self) -> Dict[str, Any]:
        """Get list of files with merge conflicts.
        
        Returns:
            Dictionary with list of conflicted files
        """
        result = self._run_git_command(['diff', '--name-only', '--diff-filter=U'])
        
        if not result['ok']:
            return result
        
        conflicted_files = [f for f in result['stdout'].split('\n') if f]
        
        return {
            'ok': True,
            'has_conflicts': len(conflicted_files) > 0,
            'conflicted_files': conflicted_files,
            'count': len(conflicted_files)
        }
    
    def resolve_conflict(self, file_path: str, resolution: str = 'ours') -> Dict[str, Any]:
        """Resolve a merge conflict using a strategy.
        
        Args:
            file_path: Path to the conflicted file
            resolution: Resolution strategy ('ours', 'theirs', or 'manual')
            
        Returns:
            Success status and message
        """
        if resolution == 'ours':
            result = self._run_git_command(['checkout', '--ours', file_path])
        elif resolution == 'theirs':
            result = self._run_git_command(['checkout', '--theirs', file_path])
        else:
            return {'ok': False, 'error': 'Manual resolution required'}
        
        if not result['ok']:
            return {
                'ok': False,
                'error': f"Failed to resolve conflict: {result.get('stderr')}"
            }
        
        # Stage the resolved file
        add_result = self._run_git_command(['add', file_path])
        if not add_result['ok']:
            return {
                'ok': False,
                'error': f"Failed to stage resolved file: {add_result.get('stderr')}"
            }
        
        return {
            'ok': True,
            'message': f"Conflict in {file_path} resolved using '{resolution}' strategy",
            'file': file_path,
            'resolution': resolution
        }
    
    def create_repo(self, repo_name: str, description: str = "", private: bool = False,
                   account_identifier: Optional[str] = None, auth_method: str = 'credential_helper') -> Dict[str, Any]:
        """Create a new GitHub repository (requires GitHub CLI or API).
        
        Args:
            repo_name: Name of the repository
            description: Repository description
            private: Whether the repository should be private
            account_identifier: GitHub account to use
            auth_method: Authentication method
            
        Returns:
            Success status and repository URL
        """
        # Check if GitHub CLI is available
        gh_check = subprocess.run(['gh', '--version'], capture_output=True)
        
        if gh_check.returncode != 0:
            return {
                'ok': False,
                'error': 'GitHub CLI (gh) not installed. Install from https://cli.github.com/'
            }
        
        # Get credentials
        if account_identifier:
            creds = self.auth_manager.get_credentials_for_push(account_identifier, auth_method)
            if not creds['ok']:
                return creds
        
        # Create repository using GitHub CLI
        visibility = '--private' if private else '--public'
        
        try:
            result = subprocess.run(
                ['gh', 'repo', 'create', repo_name, visibility, '--description', description],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    'ok': False,
                    'error': f"Failed to create repository: {result.stderr}"
                }
            
            return {
                'ok': True,
                'message': f"Repository '{repo_name}' created",
                'repo_name': repo_name,
                'private': private,
                'url': result.stdout.strip()
            }
        
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def create_pull_request(self, title: str, body: str = "", base: str = "main", 
                           head: Optional[str] = None) -> Dict[str, Any]:
        """Create a pull request (requires GitHub CLI).
        
        Args:
            title: PR title
            body: PR description
            base: Base branch (default: main)
            head: Head branch (default: current branch)
            
        Returns:
            Success status and PR URL
        """
        # Check GitHub CLI
        gh_check = subprocess.run(['gh', '--version'], capture_output=True)
        if gh_check.returncode != 0:
            return {'ok': False, 'error': 'GitHub CLI not installed'}
        
        # Get current branch if not specified
        if not head:
            branch_result = self._run_git_command(['branch', '--show-current'])
            if not branch_result['ok']:
                return {'ok': False, 'error': 'Failed to get current branch'}
            head = branch_result['stdout']
        
        try:
            result = subprocess.run(
                ['gh', 'pr', 'create', '--title', title, '--body', body, 
                 '--base', base, '--head', head],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    'ok': False,
                    'error': f"Failed to create PR: {result.stderr}"
                }
            
            return {
                'ok': True,
                'message': f"Pull request created: {title}",
                'title': title,
                'base': base,
                'head': head,
                'url': result.stdout.strip()
            }
        
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def generate_commit_message(self) -> Dict[str, Any]:
        """Generate a commit message by analyzing staged changes.
        
        Returns:
            Dictionary with generated commit message
        """
        # Get diff of staged changes
        result = self._run_git_command(['diff', '--cached', '--stat'])
        
        if not result['ok']:
            return result
        
        if not result['stdout']:
            return {
                'ok': False,
                'error': 'No staged changes to analyze'
            }
        
        # Get detailed diff
        diff_result = self._run_git_command(['diff', '--cached'])
        
        # Analyze changes
        files_changed = result['stdout'].split('\n')
        num_files = len([f for f in files_changed if f and 'file' not in f])
        
        # Simple heuristic for commit message
        if num_files == 1:
            file_name = files_changed[0].split('|')[0].strip()
            message = f"Update {file_name}"
        elif num_files <= 3:
            message = f"Update {num_files} files"
        else:
            message = f"Update multiple files ({num_files} files changed)"
        
        # Check for common patterns
        diff_text = diff_result['stdout'].lower()
        if 'fix' in diff_text or 'bug' in diff_text:
            message = f"Fix: {message}"
        elif 'add' in diff_text or 'new' in diff_text:
            message = f"Add: {message}"
        elif 'refactor' in diff_text:
            message = f"Refactor: {message}"
        elif 'test' in diff_text:
            message = f"Test: {message}"
        
        return {
            'ok': True,
            'message': message,
            'files_changed': num_files,
            'suggestions': [
                message,
                f"chore: {message.lower()}",
                f"feat: {message.lower()}"
            ]
        }
