"""GitHub Integration Agent for Helix.

This module provides GitHub API integration using Composio for repository operations.
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class PullRequestInfo(BaseModel):
    title: str
    body: str
    base: str
    head: str
    draft: bool = False

class RepositoryInfo(BaseModel):
    name: str
    full_name: str
    description: Optional[str]
    url: str
    default_branch: str

class GitHubIntegrationAgent:
    """GitHub API integration agent using Composio."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub Integration Agent.
        
        Args:
            token: GitHub personal access token. If not provided, reads from GITHUB_TOKEN env var.
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token not found. Set GITHUB_TOKEN env var or pass token.")
        
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self._auth_status = None

    async def check_authentication(self) -> bool:
        """Verify GitHub API access."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/user",
                    headers=self.headers
                )
                self._auth_status = response.status_code == 200
                return self._auth_status
        except Exception as e:
            self._auth_status = False
            raise Exception(f"GitHub authentication failed: {str(e)}")

    async def list_repositories(
        self,
        filter_private: bool = False,
        sort_by: str = "updated",
        limit: int = 30
    ) -> List[RepositoryInfo]:
        """Retrieve user repositories with filtering.
        
        Args:
            filter_private: If True, only return private repositories
            sort_by: Field to sort by ('created', 'updated', 'pushed', 'full_name')
            limit: Maximum number of repositories to return
            
        Returns:
            List of RepositoryInfo objects
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/user/repos",
                    headers=self.headers,
                    params={
                        "sort": sort_by,
                        "per_page": limit,
                        "visibility": "private" if filter_private else "all"
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to list repositories: {response.text}")
                
                repos = response.json()
                return [
                    RepositoryInfo(
                        name=repo["name"],
                        full_name=repo["full_name"],
                        description=repo.get("description"),
                        url=repo["html_url"],
                        default_branch=repo["default_branch"]
                    )
                    for repo in repos
                ]
        except Exception as e:
            raise Exception(f"Error listing repositories: {str(e)}")

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        info: PullRequestInfo
    ) -> Dict:
        """Create a pull request with automated descriptions.
        
        Args:
            owner: Repository owner
            repo: Repository name
            info: PullRequest information
            
        Returns:
            Dictionary containing PR details including URL
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/repos/{owner}/{repo}/pulls",
                    headers=self.headers,
                    json={
                        "title": info.title,
                        "body": info.body,
                        "head": info.head,
                        "base": info.base,
                        "draft": info.draft
                    }
                )
                
                if response.status_code not in (200, 201):
                    raise Exception(f"Failed to create PR: {response.text}")
                
                return self.extract_pr_url(response.json())
        except Exception as e:
            raise Exception(f"Error creating pull request: {str(e)}")

    @staticmethod
    def extract_pr_url(response: Dict) -> Dict:
        """Parse PR URLs and details from API response.
        
        Args:
            response: GitHub API response for PR creation
            
        Returns:
            Dictionary containing PR URLs and key details
        """
        return {
            "pr_number": response["number"],
            "html_url": response["html_url"],
            "api_url": response["url"],
            "state": response["state"],
            "created_at": response["created_at"],
            "updated_at": response["updated_at"]
        }

    def get_authentication_status(self) -> Dict:
        """Get detailed authentication status report.
        
        Returns:
            Dictionary containing auth status details
        """
        return {
            "authenticated": bool(self._auth_status),
            "timestamp": datetime.utcnow().isoformat(),
            "api_base": self.api_base,
            "token_exists": bool(self.token),
            "token_prefix": self.token[:4] + "..." if self.token else None
        }

    async def update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = None
    ) -> Dict:
        """Update or create a file in the repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in the repository
            content: New file content
            message: Commit message
            branch: Branch name (defaults to repository's default branch)
            
        Returns:
            Dictionary containing commit details
        """
        try:
            import base64
            
            # First get the current file (if it exists) to get the SHA
            async with httpx.AsyncClient() as client:
                # Try to get existing file
                try:
                    existing = await client.get(
                        f"{self.api_base}/repos/{owner}/{repo}/contents/{path}",
                        headers=self.headers,
                        params={"ref": branch} if branch else {}
                    )
                    sha = existing.json()["sha"] if existing.status_code == 200 else None
                except:
                    sha = None

                # Prepare the update
                data = {
                    "message": message,
                    "content": base64.b64encode(content.encode()).decode(),
                    "branch": branch
                }
                if sha:
                    data["sha"] = sha

                # Update or create the file
                response = await client.put(
                    f"{self.api_base}/repos/{owner}/{repo}/contents/{path}",
                    headers=self.headers,
                    json=data
                )

                if response.status_code not in (200, 201):
                    raise Exception(f"Failed to update file: {response.text}")

                return response.json()["commit"]
        except Exception as e:
            raise Exception(f"Error updating file: {str(e)}")