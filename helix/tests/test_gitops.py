"""Tests for Git operations."""

import pytest
from pathlib import Path
import tempfile
import subprocess

from helix.gitops import GitOperations, GitOpsError
from helix.utils import SecretDetector


def test_secret_detector():
    """Test secret detection."""
    code_with_secrets = '''
API_KEY = "sk-1234567890abcdef"
password = "mypassword123"
github_token = "ghp_XXXXXXXXXXXX"
'''
    
    findings = SecretDetector.scan_text(code_with_secrets)
    assert len(findings) > 0
    
    # Check that placeholders are not flagged
    code_with_placeholders = '''
API_KEY = "your_api_key_here"
password = "XXXX"
'''
    
    findings = SecretDetector.scan_text(code_with_placeholders)
    # Placeholders should be filtered out
    assert all("your_" in finding[1] or "XXXX" in finding[1] for finding in findings)


def test_git_operations_not_a_repo():
    """Test that GitOperations fails on non-repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(GitOpsError, match="Not a git repository"):
            GitOperations(Path(tmpdir))


@pytest.fixture
def git_repo():
    """Create a temporary git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        
        # Create initial commit
        (repo_path / "README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)
        
        yield repo_path


def test_git_get_current_branch(git_repo):
    """Test getting current branch."""
    git = GitOperations(git_repo)
    branch = git.get_current_branch()
    assert branch in ("master", "main")


def test_git_create_branch(git_repo):
    """Test creating a new branch."""
    git = GitOperations(git_repo)
    git.create_branch("test-branch")
    
    current = git.get_current_branch()
    assert current == "test-branch"


def test_git_commit(git_repo):
    """Test creating a commit."""
    git = GitOperations(git_repo)
    
    # Create a file
    test_file = git_repo / "test.txt"
    test_file.write_text("test content")
    
    # Stage and commit
    git.stage_files([test_file])
    commit_sha = git.commit("Test commit", planner_id="test_123")
    
    assert len(commit_sha) == 40  # SHA is 40 characters