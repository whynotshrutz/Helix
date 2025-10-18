"""Git and GitHub operations for Helix."""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import requests
from helix.utils import run_command, generate_diff, SecretDetector


class GitOpsError(Exception):
    """Custom exception for GitOps operations."""
    pass


class GitHubAuth:
    """Handle GitHub authentication."""
    
    def __init__(self, token: Optional[str] = None, oauth_token: Optional[str] = None):
        """
        Initialize GitHub authentication.
        
        Args:
            token: Personal Access Token
            oauth_token: OAuth token
        """
        self.token = token or oauth_token
        if not self.token:
            raise GitOpsError("No GitHub token provided. Set GH_TOKEN or GH_OAUTH_TOKEN.")
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers for GitHub API."""
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }


class GitOperations:
    """Git operations wrapper."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        if not (self.repo_path / ".git").exists():
            raise GitOpsError(f"Not a git repository: {repo_path}")
    
    def get_current_branch(self) -> str:
        """Get current branch name."""
        code, stdout, stderr = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.repo_path
        )
        if code != 0:
            raise GitOpsError(f"Failed to get current branch: {stderr}")
        return stdout.strip()
    
    def create_branch(self, branch_name: str) -> None:
        """Create and checkout a new branch."""
        code, stdout, stderr = run_command(
            ["git", "checkout", "-b", branch_name],
            cwd=self.repo_path
        )
        if code != 0:
            raise GitOpsError(f"Failed to create branch {branch_name}: {stderr}")
    
    def stage_files(self, files: List[Path]) -> None:
        """Stage files for commit."""
        file_paths = [str(f) for f in files]
        code, stdout, stderr = run_command(
            ["git", "add"] + file_paths,
            cwd=self.repo_path
        )
        if code != 0:
            raise GitOpsError(f"Failed to stage files: {stderr}")
    
    def commit(self, message: str, planner_id: Optional[str] = None) -> str:
        """
        Create a commit.
        
        Returns:
            Commit SHA
        """
        # Format commit message
        if planner_id:
            full_message = f"[helix] {message}\nplanner:{planner_id}"
        else:
            full_message = f"[helix] {message}"
        
        code, stdout, stderr = run_command(
            ["git", "commit", "-m", full_message],
            cwd=self.repo_path
        )
        if code != 0:
            raise GitOpsError(f"Failed to commit: {stderr}")
        
        # Get commit SHA
        code, stdout, stderr = run_command(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path
        )
        return stdout.strip()
    
    def get_diff(self, ref1: str = "HEAD", ref2: Optional[str] = None) -> str:
        """Get diff between two refs."""
        cmd = ["git", "diff", ref1]
        if ref2:
            cmd.append(ref2)
        
        code, stdout, stderr = run_command(cmd, cwd=self.repo_path)
        if code != 0:
            raise GitOpsError(f"Failed to get diff: {stderr}")
        return stdout
    
    def push(self, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> None:
        """Push branch to remote."""
        if branch is None:
            branch = self.get_current_branch()
        
        cmd = ["git", "push", remote, branch]
        if force:
            cmd.append("--force")
        
        # Set upstream on first push
        cmd.extend(["--set-upstream"])
        
        code, stdout, stderr = run_command(cmd, cwd=self.repo_path, timeout=120)
        if code != 0:
            raise GitOpsError(f"Failed to push: {stderr}")
    
    def get_remote_url(self, remote: str = "origin") -> str:
        """Get remote URL."""
        code, stdout, stderr = run_command(
            ["git", "remote", "get-url", remote],
            cwd=self.repo_path
        )
        if code != 0:
            raise GitOpsError(f"Failed to get remote URL: {stderr}")
        return stdout.strip()
    
    def parse_github_repo(self) -> Tuple[str, str]:
        """
        Parse GitHub owner and repo from remote URL.
        
        Returns:
            Tuple of (owner, repo_name)
        """
        url = self.get_remote_url()
        
        # Handle both HTTPS and SSH URLs
        if url.startswith("git@github.com:"):
            # SSH: git@github.com:owner/repo.git
            parts = url.replace("git@github.com:", "").replace(".git", "").split("/")
        elif "github.com" in url:
            # HTTPS: https://github.com/owner/repo.git
            parts = url.split("github.com/")[1].replace(".git", "").split("/")
        else:
            raise GitOpsError(f"Not a GitHub repository: {url}")
        
        if len(parts) < 2:
            raise GitOpsError(f"Invalid GitHub URL format: {url}")
        
        return parts[0], parts[1]


class GitHubOperations:
    """GitHub API operations."""
    
    def __init__(self, auth: GitHubAuth, owner: str, repo: str):
        self.auth = auth
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
    
    def create_pull_request(
        self,
        head_branch: str,
        base_branch: str = "main",
        title: Optional[str] = None,
        body: Optional[str] = None,
        test_report: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Returns:
            PR data from GitHub API
        """
        if title is None:
            title = f"[Helix] Automated changes from {head_branch}"
        
        if body is None:
            body = "Automated changes generated by Helix multi-agent system."
        
        # Append test report if available
        if test_report:
            body += "\n## Test Report\n"
            body += f"- Tests Run: {test_report.get('tests_run', 0)}\n"
            body += f"- Passed: {test_report.get('passed', 0)}\n"
            body += f"- Failed: {test_report.get('failed', 0)}\n"
            body += f"- Coverage: {test_report.get('coverage', 'N/A')}\n"
        
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls"
        data = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body
        }
        
        response = requests.post(url, headers=self.auth.get_headers(), json=data)
        
        if response.status_code not in (200, 201):
            raise GitOpsError(f"Failed to create PR: {response.text}")
        
        return response.json()
    
    def get_repository_info(self) -> Dict[str, Any]:
        """Get repository information."""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}"
        response = requests.get(url, headers=self.auth.get_headers())
        
        if response.status_code != 200:
            raise GitOpsError(f"Failed to get repo info: {response.text}")
        
        return response.json()


class DiffReviewer:
    """Review diffs for security issues."""
    
    @staticmethod
    def review(diff: str) -> Tuple[bool, List[str]]:
        """
        Review diff for security issues.
        
        Returns:
            Tuple of (is_safe, issues_found)
        """
        issues = []
        
        # Check for secrets
        secret_findings = SecretDetector.scan_text(diff)
        for secret_type, matched_text, line_num in secret_findings:
            issues.append(f"Potential {secret_type} found at line {line_num}: {matched_text[:50]}...")
        
        # Check for suspicious network calls
        suspicious_patterns = [
            (r'requests\.(post|put|patch)\s*\([^)]*http://[^)]*\)', "Insecure HTTP request"),
            (r'socket\.connect', "Direct socket connection"),
            (r'eval\s*\(', "Dangerous eval() call"),
            (r'exec\s*\(', "Dangerous exec() call"),
        ]
        
        for pattern, description in suspicious_patterns:
            import re
            if re.search(pattern, diff):
                issues.append(f"{description} detected")
        
        is_safe = len(issues) == 0
        return is_safe, issues


class GitOpsAgent:
    """High-level GitOps agent orchestrating Git and GitHub operations."""
    
    def __init__(self, repo_path: Path, github_token: Optional[str] = None, require_confirmation: bool = False):
        self.repo_path = Path(repo_path)
        self.git = GitOperations(repo_path)
        self.require_confirmation = require_confirmation
        
        # Initialize GitHub operations
        if github_token:
            self.auth = GitHubAuth(token=github_token)
            owner, repo = self.git.parse_github_repo()
            self.github = GitHubOperations(self.auth, owner, repo)
        else:
            self.auth = None
            self.github = None
    
    def execute_push_workflow(
        self,
        files: List[Path],
        task_summary: str,
        branch_name: Optional[str] = None,
        planner_id: Optional[str] = None,
        create_pr: bool = False,
        test_report: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute complete push workflow:
        1. Create branch
        2. Stage and commit files
        3. Review diff
        4. Push to remote
        5. Optionally create PR
        
        Returns:
            Dictionary with workflow results
        """
        results = {
            "success": False,
            "branch": None,
            "commit_sha": None,
            "pr_url": None,
            "issues": []
        }
        
        try:
            # Generate branch name if not provided
            if branch_name is None:
                from helix.utils import generate_branch_name
                branch_name = generate_branch_name(task_summary)
            
            # Create branch
            original_branch = self.git.get_current_branch()
            self.git.create_branch(branch_name)
            results["branch"] = branch_name
            
            # Stage files
            self.git.stage_files(files)
            
            # Get diff for review
            diff = self.git.get_diff()
            
            # Review diff
            is_safe, issues = DiffReviewer.review(diff)
            if not is_safe:
                results["issues"] = issues
                print(f"⚠️  Security issues detected in diff:")
                for issue in issues:
                    print(f"   - {issue}")
                
                if self.require_confirmation:
                    response = input("\nProceed anyway? (yes/no): ")
                    if response.lower() != "yes":
                        # Rollback
                        self.git.run_command(["git", "checkout", original_branch], cwd=self.repo_path)
                        self.git.run_command(["git", "branch", "-D", branch_name], cwd=self.repo_path)
                        return results
                else:
                    print("⛔ Auto-push disabled due to security issues.")
                    return results
            
            # Commit
            commit_sha = self.git.commit(task_summary, planner_id)
            results["commit_sha"] = commit_sha
            
            # Human confirmation if required
            if self.require_confirmation:
                print(f"\n📝 Ready to push branch: {branch_name}")
                print(f"   Commit: {commit_sha[:8]}")
                print(f"   Summary: {task_summary}")
                response = input("\nPush to remote? (yes/no): ")
                if response.lower() != "yes":
                    print("Push cancelled by user.")
                    return results
            
            # Push to remote
            if self.github:
                self.git.push(branch=branch_name)
                print(f"✅ Pushed to remote: {branch_name}")
                
                # Create PR if requested
                if create_pr:
                    pr_data = self.github.create_pull_request(
                        head_branch=branch_name,
                        title=f"[Helix] {task_summary}",
                        body=f"Automated changes generated by Helix.\nCommit: {commit_sha}",
                        test_report=test_report
                    )
                    results["pr_url"] = pr_data["html_url"]
                    print(f"✅ Created PR: {results['pr_url']}")
            else:
                print("⚠️  No GitHub token configured. Skipping push.")
            
            results["success"] = True
            
        except Exception as e:
            results["issues"].append(str(e))
            print(f"❌ GitOps workflow failed: {e}")
        
        return results