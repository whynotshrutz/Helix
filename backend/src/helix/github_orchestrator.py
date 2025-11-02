"""GitHub Automation for Helix - Full workflow automation.

This module provides GitHub integration for:
- Repository management (create, clone, manage)
- Branch operations (create, switch, delete)
- Commit and push operations
- Pull request automation
- Issue management
- GitHub Actions workflow triggering
"""
from typing import Optional, Dict, Any, List
import os
import subprocess
import requests
from pathlib import Path
from datetime import datetime
import json


class GitHubOrchestrator:
    """Manages GitHub operations and automation."""
    
    def __init__(
        self,
        github_token: Optional[str] = None,
        default_remote: str = "origin",
        default_branch: str = "main",
    ):
        """Initialize GitHub orchestrator.
        
        Args:
            github_token: GitHub Personal Access Token (or from GITHUB_TOKEN env)
            default_remote: Default remote name
            default_branch: Default branch name
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.default_remote = default_remote
        self.default_branch = default_branch
        
        if not self.github_token:
            print("Warning: GITHUB_TOKEN not set. GitHub API features will be limited.")
        
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
    
    # ========== Git Operations ==========
    
    def git_status(self, repo_path: str = ".") -> Dict[str, Any]:
        """Get git repository status.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Status information
        """
        try:
            result = self._run_git_command(["status", "--porcelain"], cwd=repo_path)
            
            if not result["ok"]:
                return result
            
            # Parse status output
            lines = result["output"].strip().split("\n")
            modified = []
            untracked = []
            staged = []
            
            for line in lines:
                if not line.strip():
                    continue
                
                status = line[:2]
                file_path = line[3:]
                
                if status[0] in ["M", "A", "D", "R", "C"]:
                    staged.append(file_path)
                if status[1] == "M":
                    modified.append(file_path)
                if status == "??":
                    untracked.append(file_path)
            
            # Get current branch
            branch_result = self._run_git_command(["branch", "--show-current"], cwd=repo_path)
            current_branch = branch_result["output"].strip() if branch_result["ok"] else "unknown"
            
            return {
                "ok": True,
                "current_branch": current_branch,
                "staged": staged,
                "modified": modified,
                "untracked": untracked,
                "clean": len(staged) == 0 and len(modified) == 0 and len(untracked) == 0,
            }
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def git_add(self, files: List[str], repo_path: str = ".") -> Dict[str, Any]:
        """Stage files for commit.
        
        Args:
            files: List of file paths (or [".", "-A"] for all)
            repo_path: Path to repository
            
        Returns:
            Result dict
        """
        try:
            cmd = ["add"] + files
            return self._run_git_command(cmd, cwd=repo_path)
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def git_commit(
        self,
        message: str,
        repo_path: str = ".",
        add_all: bool = False,
    ) -> Dict[str, Any]:
        """Create a git commit.
        
        Args:
            message: Commit message
            repo_path: Path to repository
            add_all: Whether to add all changes before committing
            
        Returns:
            Result dict with commit hash
        """
        try:
            # Add all if requested
            if add_all:
                add_result = self.git_add(["-A"], repo_path=repo_path)
                if not add_result["ok"]:
                    return add_result
            
            # Create commit
            result = self._run_git_command(
                ["commit", "-m", message],
                cwd=repo_path,
            )
            
            if not result["ok"]:
                return result
            
            # Get commit hash
            hash_result = self._run_git_command(
                ["rev-parse", "HEAD"],
                cwd=repo_path,
            )
            
            commit_hash = hash_result["output"].strip() if hash_result["ok"] else "unknown"
            
            return {
                "ok": True,
                "message": "Commit created successfully",
                "commit_hash": commit_hash,
                "commit_message": message,
            }
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def git_push(
        self,
        remote: Optional[str] = None,
        branch: Optional[str] = None,
        force: bool = False,
        repo_path: str = ".",
    ) -> Dict[str, Any]:
        """Push commits to remote repository.
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
            force: Whether to force push
            repo_path: Path to repository
            
        Returns:
            Result dict
        """
        try:
            remote = remote or self.default_remote
            
            # Get current branch if not specified
            if not branch:
                branch_result = self._run_git_command(
                    ["branch", "--show-current"],
                    cwd=repo_path,
                )
                branch = branch_result["output"].strip() if branch_result["ok"] else self.default_branch
            
            # Build push command
            cmd = ["push", remote, branch]
            if force:
                cmd.append("--force")
            
            result = self._run_git_command(cmd, cwd=repo_path)
            
            if result["ok"]:
                return {
                    "ok": True,
                    "message": f"Successfully pushed to {remote}/{branch}",
                    "remote": remote,
                    "branch": branch,
                }
            
            return result
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def git_pull(
        self,
        remote: Optional[str] = None,
        branch: Optional[str] = None,
        repo_path: str = ".",
    ) -> Dict[str, Any]:
        """Pull changes from remote repository.
        
        Args:
            remote: Remote name
            branch: Branch name
            repo_path: Path to repository
            
        Returns:
            Result dict
        """
        try:
            remote = remote or self.default_remote
            
            cmd = ["pull", remote]
            if branch:
                cmd.append(branch)
            
            return self._run_git_command(cmd, cwd=repo_path)
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def create_branch(
        self,
        branch_name: str,
        checkout: bool = True,
        repo_path: str = ".",
    ) -> Dict[str, Any]:
        """Create a new git branch.
        
        Args:
            branch_name: Name for new branch
            checkout: Whether to checkout the branch after creation
            repo_path: Path to repository
            
        Returns:
            Result dict
        """
        try:
            # Create branch
            cmd = ["branch", branch_name]
            result = self._run_git_command(cmd, cwd=repo_path)
            
            if not result["ok"]:
                return result
            
            # Checkout if requested
            if checkout:
                checkout_result = self.switch_branch(branch_name, repo_path=repo_path)
                if not checkout_result["ok"]:
                    return checkout_result
            
            return {
                "ok": True,
                "message": f"Branch '{branch_name}' created successfully",
                "branch_name": branch_name,
                "checked_out": checkout,
            }
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def switch_branch(self, branch_name: str, repo_path: str = ".") -> Dict[str, Any]:
        """Switch to a different branch.
        
        Args:
            branch_name: Branch to switch to
            repo_path: Path to repository
            
        Returns:
            Result dict
        """
        try:
            result = self._run_git_command(
                ["checkout", branch_name],
                cwd=repo_path,
            )
            
            if result["ok"]:
                return {
                    "ok": True,
                    "message": f"Switched to branch '{branch_name}'",
                    "branch_name": branch_name,
                }
            
            return result
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def delete_branch(
        self,
        branch_name: str,
        force: bool = False,
        repo_path: str = ".",
    ) -> Dict[str, Any]:
        """Delete a git branch.
        
        Args:
            branch_name: Branch to delete
            force: Whether to force delete
            repo_path: Path to repository
            
        Returns:
            Result dict
        """
        try:
            flag = "-D" if force else "-d"
            result = self._run_git_command(
                ["branch", flag, branch_name],
                cwd=repo_path,
            )
            
            if result["ok"]:
                return {
                    "ok": True,
                    "message": f"Branch '{branch_name}' deleted",
                    "branch_name": branch_name,
                }
            
            return result
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    # ========== GitHub API Operations ==========
    
    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False,
    ) -> Dict[str, Any]:
        """Create a pull request on GitHub.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Branch with changes
            base: Branch to merge into
            body: PR description
            draft: Whether to create as draft PR
            
        Returns:
            PR creation result
        """
        if not self.github_token:
            return {"ok": False, "error": "github_token_required"}
        
        try:
            url = f"{self.api_base}/repos/{owner}/{repo}/pulls"
            
            data = {
                "title": title,
                "head": head,
                "base": base,
                "draft": draft,
            }
            
            if body:
                data["body"] = body
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 201:
                pr_data = response.json()
                return {
                    "ok": True,
                    "message": "Pull request created successfully",
                    "pr_number": pr_data["number"],
                    "pr_url": pr_data["html_url"],
                    "pr_data": pr_data,
                }
            else:
                return {
                    "ok": False,
                    "error": "github_api_error",
                    "status_code": response.status_code,
                    "message": response.json().get("message", "Unknown error"),
                }
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """List pull requests.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            limit: Maximum PRs to return
            
        Returns:
            List of PRs
        """
        if not self.github_token:
            return {"ok": False, "error": "github_token_required"}
        
        try:
            url = f"{self.api_base}/repos/{owner}/{repo}/pulls"
            params = {"state": state, "per_page": limit}
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                prs = response.json()
                return {
                    "ok": True,
                    "count": len(prs),
                    "pull_requests": [
                        {
                            "number": pr["number"],
                            "title": pr["title"],
                            "state": pr["state"],
                            "url": pr["html_url"],
                            "created_at": pr["created_at"],
                            "author": pr["user"]["login"],
                        }
                        for pr in prs
                    ],
                }
            else:
                return {
                    "ok": False,
                    "error": "github_api_error",
                    "status_code": response.status_code,
                }
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create an issue on GitHub.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue description
            labels: List of labels
            
        Returns:
            Issue creation result
        """
        if not self.github_token:
            return {"ok": False, "error": "github_token_required"}
        
        try:
            url = f"{self.api_base}/repos/{owner}/{repo}/issues"
            
            data = {"title": title}
            
            if body:
                data["body"] = body
            if labels:
                data["labels"] = labels
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 201:
                issue_data = response.json()
                return {
                    "ok": True,
                    "message": "Issue created successfully",
                    "issue_number": issue_data["number"],
                    "issue_url": issue_data["html_url"],
                }
            else:
                return {
                    "ok": False,
                    "error": "github_api_error",
                    "status_code": response.status_code,
                }
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository info
        """
        if not self.github_token:
            return {"ok": False, "error": "github_token_required"}
        
        try:
            url = f"{self.api_base}/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "ok": True,
                    "name": data["name"],
                    "full_name": data["full_name"],
                    "description": data.get("description"),
                    "stars": data["stargazers_count"],
                    "forks": data["forks_count"],
                    "language": data.get("language"),
                    "default_branch": data["default_branch"],
                    "url": data["html_url"],
                }
            else:
                return {
                    "ok": False,
                    "error": "github_api_error",
                    "status_code": response.status_code,
                }
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    # ========== Utility Methods ==========
    
    def _run_git_command(
        self,
        args: List[str],
        cwd: str = ".",
    ) -> Dict[str, Any]:
        """Run a git command.
        
        Args:
            args: Git command arguments
            cwd: Working directory
            
        Returns:
            Command result
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode == 0:
                return {
                    "ok": True,
                    "output": result.stdout,
                }
            else:
                return {
                    "ok": False,
                    "error": "git_command_failed",
                    "message": result.stderr,
                    "returncode": result.returncode,
                }
        
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def parse_repo_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GitHub repository URL.
        
        Args:
            url: GitHub URL (https or ssh)
            
        Returns:
            Dict with owner and repo, or None
        """
        import re
        
        patterns = [
            r"github\.com[:/]([^/]+)/([^/\.]+)",  # HTTPS or SSH
            r"([^/]+)/([^/]+)$",  # owner/repo format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return {
                    "owner": match.group(1),
                    "repo": match.group(2),
                }
        
        return None


# Global orchestrator instance
_github_orchestrator: Optional[GitHubOrchestrator] = None


def get_github_orchestrator(**kwargs) -> GitHubOrchestrator:
    """Get or create global GitHub orchestrator instance.
    
    Args:
        **kwargs: Arguments for GitHubOrchestrator constructor
        
    Returns:
        GitHubOrchestrator instance
    """
    global _github_orchestrator
    
    if _github_orchestrator is None:
        _github_orchestrator = GitHubOrchestrator(**kwargs)
    
    return _github_orchestrator
