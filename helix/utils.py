"""Utility functions for Helix."""

import os
import re
import hashlib
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from datetime import datetime
import difflib


class SecretDetector:
    """Detects potential secrets in code."""
    
    # Patterns for common secrets
    SECRET_PATTERNS = [
        (r'(?i)(api[_-]?key|apikey)[\s]*[=:][\s]*["\']([^"\']+)["\']', "API Key"),
        (r'(?i)(secret[_-]?key|secretkey)[\s]*[=:][\s]*["\']([^"\']+)["\']', "Secret Key"),
        (r'(?i)(password|passwd|pwd)[\s]*[=:][\s]*["\']([^"\']+)["\']', "Password"),
        (r'(?i)(token)[\s]*[=:][\s]*["\']([^"\']+)["\']', "Token"),
        (r'(?i)(aws_access_key_id)[\s]*[=:][\s]*["\']([^"\']+)["\']', "AWS Access Key"),
        (r'(?i)(aws_secret_access_key)[\s]*[=:][\s]*["\']([^"\']+)["\']', "AWS Secret Key"),
        (r'(?i)(github[_-]?token)[\s]*[=:][\s]*["\']([^"\']+)["\']', "GitHub Token"),
        (r'(?i)-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----', "Private Key"),
    ]
    
    @classmethod
    def scan_text(cls, text: str) -> List[Tuple[str, str, int]]:
        """
        Scan text for potential secrets.
        
        Returns:
            List of (secret_type, matched_text, line_number) tuples
        """
        findings = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, secret_type in cls.SECRET_PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    # Don't flag obvious placeholders
                    matched_text = match.group(0)
                    if not cls._is_placeholder(matched_text):
                        findings.append((secret_type, matched_text, line_num))
        
        return findings
    
    @classmethod
    def _is_placeholder(cls, text: str) -> bool:
        """Check if text appears to be a placeholder."""
        placeholders = [
            "xxx", "yyy", "zzz", "example", "placeholder",
            "your_", "my_", "test_", "fake_", "dummy_",
            "...", "****", "XXXX"
        ]
        text_lower = text.lower()
        return any(p in text_lower for p in placeholders)
    
    @classmethod
    def scan_file(cls, filepath: Path) -> List[Tuple[str, str, int]]:
        """Scan a file for secrets."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return cls.scan_text(content)
        except Exception:
            return []


def generate_diff(original: str, modified: str, filename: str = "file") -> str:
    """Generate unified diff between original and modified content."""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=''
    )
    
    return ''.join(diff)


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to a URL-safe slug."""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    return slug[:max_length]


def generate_branch_name(task_summary: str, prefix: str = "helix") -> str:
    """Generate a branch name from task summary."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = slugify(task_summary, max_length=40)
    return f"{prefix}/{timestamp}-{slug}"


def safe_write_file(filepath: Path, content: str, backup: bool = True) -> None:
    """Safely write content to file with optional backup."""
    filepath = Path(filepath)
    
    # Create backup if file exists
    if backup and filepath.exists():
        backup_path = filepath.with_suffix(filepath.suffix + '.backup')
        backup_path.write_text(filepath.read_text())
    
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Write content
    filepath.write_text(content)


def run_command(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[int, str, str]:
    """
    Run a shell command and return exit code, stdout, stderr.
    
    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)


def hash_content(content: str) -> str:
    """Generate SHA256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count (1 token ≈ 4 chars)."""
    return len(text) // 4


class FileTree:
    """Generate a tree visualization of directory structure."""
    
    @classmethod
    def generate(cls, root_path: Path, max_depth: int = 3, exclude: Optional[List[str]] = None) -> str:
        """Generate file tree string."""
        if exclude is None:
            exclude = ['.git', '__pycache__', '.venv', 'node_modules', '.env']
        
        tree_lines = [str(root_path.name) + '/']
        cls._build_tree(root_path, tree_lines, '', max_depth, 0, exclude)
        return '\n'.join(tree_lines)
    
    @classmethod
    def _build_tree(cls, path: Path, lines: List[str], prefix: str, max_depth: int, current_depth: int, exclude: List[str]):
        """Recursively build tree structure."""
        if current_depth >= max_depth:
            return
        
        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            entries = [e for e in entries if e.name not in exclude]
        except PermissionError:
            return
        
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = '└── ' if is_last else '├── '
            lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")
            
            if entry.is_dir():
                extension = '    ' if is_last else '│   '
                cls._build_tree(entry, lines, prefix + extension, max_depth, current_depth + 1, exclude)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"