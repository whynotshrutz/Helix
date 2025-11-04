"""Dynamic Workspace Scanner for VS Code Explorer Integration.

Provides real-time workspace scanning and navigation capabilities:
- Recursively scans all folders and files
- Dynamic directory traversal
- File type detection and categorization
- Excludes build/cache directories intelligently
- Provides structured workspace representation
"""
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import os
import mimetypes
import json


class WorkspaceScanner:
    """Scans and provides structured view of workspace files and folders."""
    
    # Common directories to exclude
    EXCLUDED_DIRS = {
        'node_modules', '__pycache__', '.git', 'venv', 'env',
        'dist', 'build', '.next', '.nuxt', 'out', 'coverage',
        '.pytest_cache', '.mypy_cache', 'vendor', 'target',
        'bin', 'obj', '.idea', '.vscode', '.vs', 'tmp'
    }
    
    # File patterns to exclude
    EXCLUDED_FILES = {
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
        '.class', '.o', '.obj', '.exe', '.map', '.min.js',
        '.lock', 'package-lock.json', 'yarn.lock', '.DS_Store'
    }
    
    def __init__(self, workspace_root: str, max_depth: int = 10, max_files: int = 1000):
        """Initialize workspace scanner.
        
        Args:
            workspace_root: Root directory to scan
            max_depth: Maximum directory depth to traverse
            max_files: Maximum files to process
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.max_depth = max_depth
        self.max_files = max_files
        self.scanned_files = 0
        
        # Initialize mime types
        mimetypes.init()
    
    def scan(self, include_hidden: bool = False, custom_excludes: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Scan workspace and return structured tree.
        
        Args:
            include_hidden: Whether to include hidden files/dirs
            custom_excludes: Additional directories/patterns to exclude
            
        Returns:
            Dictionary with workspace structure and metadata
        """
        excludes = self.EXCLUDED_DIRS.copy()
        if custom_excludes:
            excludes.update(custom_excludes)
        
        result = {
            'workspace': str(self.workspace_root),
            'tree': {},
            'files': [],
            'directories': [],
            'stats': {
                'total_files': 0,
                'total_dirs': 0,
                'total_size': 0,
                'file_types': {},
                'languages': {}
            }
        }
        
        # Scan from root
        tree_node = self._scan_directory(
            self.workspace_root,
            depth=0,
            include_hidden=include_hidden,
            excludes=excludes,
            result=result
        )
        
        result['tree'] = tree_node
        
        return result
    
    def _scan_directory(
        self,
        directory: Path,
        depth: int,
        include_hidden: bool,
        excludes: Set[str],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively scan a directory.
        
        Args:
            directory: Directory to scan
            depth: Current depth level
            include_hidden: Include hidden items
            excludes: Excluded directory names
            result: Result dict to accumulate stats
            
        Returns:
            Tree node representing this directory
        """
        if depth > self.max_depth or self.scanned_files >= self.max_files:
            return {'name': directory.name, 'type': 'directory', 'truncated': True}
        
        node = {
            'name': directory.name,
            'type': 'directory',
            'path': str(directory.relative_to(self.workspace_root)),
            'children': []
        }
        
        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except (PermissionError, OSError):
            node['error'] = 'Permission denied'
            return node
        
        for item in items:
            # Check scan limits
            if self.scanned_files >= self.max_files:
                break
            
            # Skip hidden files unless explicitly included
            if not include_hidden and item.name.startswith('.'):
                continue
            
            # Skip excluded directories
            if item.is_dir() and item.name in excludes:
                continue
            
            # Skip excluded file patterns
            if item.is_file() and any(item.name.endswith(ext) for ext in self.EXCLUDED_FILES):
                continue
            
            if item.is_dir():
                # Recursively scan subdirectory
                child_node = self._scan_directory(
                    item,
                    depth + 1,
                    include_hidden,
                    excludes,
                    result
                )
                node['children'].append(child_node)
                result['directories'].append(str(item.relative_to(self.workspace_root)))
                result['stats']['total_dirs'] += 1
                
            elif item.is_file():
                # Process file
                file_node = self._process_file(item, result)
                node['children'].append(file_node)
                self.scanned_files += 1
        
        return node
    
    def _process_file(self, file_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process a file and extract metadata.
        
        Args:
            file_path: Path to file
            result: Result dict to accumulate stats
            
        Returns:
            File node with metadata
        """
        try:
            stat = file_path.stat()
            file_size = stat.st_size
            
            # Detect file type
            extension = file_path.suffix.lower()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            language = self._detect_language(file_path)
            
            node = {
                'name': file_path.name,
                'type': 'file',
                'path': str(file_path.relative_to(self.workspace_root)),
                'size': file_size,
                'extension': extension,
                'mime_type': mime_type,
                'language': language
            }
            
            # Update stats
            result['files'].append(str(file_path.relative_to(self.workspace_root)))
            result['stats']['total_files'] += 1
            result['stats']['total_size'] += file_size
            
            # Track file types
            if extension:
                result['stats']['file_types'][extension] = \
                    result['stats']['file_types'].get(extension, 0) + 1
            
            # Track languages
            if language:
                result['stats']['languages'][language] = \
                    result['stats']['languages'].get(language, 0) + 1
            
            return node
            
        except (OSError, PermissionError) as e:
            return {
                'name': file_path.name,
                'type': 'file',
                'error': str(e)
            }
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            Language name or None
        """
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'JSX',
            '.tsx': 'TSX',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.sh': 'Shell',
            '.bash': 'Bash',
            '.ps1': 'PowerShell',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.json': 'JSON',
            '.xml': 'XML',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.sql': 'SQL',
            '.dockerfile': 'Dockerfile',
        }
        
        ext = file_path.suffix.lower()
        
        # Check by extension
        if ext in extension_map:
            return extension_map[ext]
        
        # Check by filename
        if file_path.name.lower() in ['dockerfile', 'makefile', 'rakefile']:
            return file_path.name.capitalize()
        
        return None
    
    def get_directory_contents(self, relative_path: str = "") -> Dict[str, Any]:
        """Get immediate contents of a specific directory.
        
        Args:
            relative_path: Relative path from workspace root
            
        Returns:
            Dictionary with directory contents
        """
        target_dir = self.workspace_root / relative_path if relative_path else self.workspace_root
        
        if not target_dir.exists():
            return {'ok': False, 'error': 'Directory not found'}
        
        if not target_dir.is_dir():
            return {'ok': False, 'error': 'Not a directory'}
        
        result = {
            'ok': True,
            'path': relative_path or '.',
            'absolute_path': str(target_dir),
            'files': [],
            'directories': []
        }
        
        try:
            for item in sorted(target_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                # Skip hidden and excluded
                if item.name.startswith('.') or item.name in self.EXCLUDED_DIRS:
                    continue
                
                rel_path = str(item.relative_to(self.workspace_root))
                
                if item.is_dir():
                    result['directories'].append({
                        'name': item.name,
                        'path': rel_path
                    })
                elif item.is_file():
                    result['files'].append({
                        'name': item.name,
                        'path': rel_path,
                        'size': item.stat().st_size,
                        'language': self._detect_language(item)
                    })
            
            return result
            
        except (PermissionError, OSError) as e:
            return {'ok': False, 'error': str(e)}
    
    def find_files(self, pattern: str = "*", language: Optional[str] = None) -> Dict[str, Any]:
        """Find files matching pattern or language.
        
        Args:
            pattern: Glob pattern (e.g., '*.py', 'src/**/*.js')
            language: Filter by language
            
        Returns:
            Dictionary with matching files
        """
        result = {
            'ok': True,
            'pattern': pattern,
            'language': language,
            'matches': []
        }
        
        try:
            # Use rglob for recursive patterns, glob for non-recursive
            if '**' in pattern:
                matches = self.workspace_root.glob(pattern)
            else:
                matches = self.workspace_root.rglob(pattern)
            
            for match in matches:
                if not match.is_file():
                    continue
                
                # Skip excluded
                if any(excluded in match.parts for excluded in self.EXCLUDED_DIRS):
                    continue
                
                detected_lang = self._detect_language(match)
                
                # Filter by language if specified
                if language and detected_lang != language:
                    continue
                
                result['matches'].append({
                    'name': match.name,
                    'path': str(match.relative_to(self.workspace_root)),
                    'size': match.stat().st_size,
                    'language': detected_lang
                })
                
                if len(result['matches']) >= self.max_files:
                    result['truncated'] = True
                    break
            
            result['count'] = len(result['matches'])
            return result
            
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def get_workspace_summary(self) -> str:
        """Get human-readable workspace summary.
        
        Returns:
            Formatted string with workspace overview
        """
        scan_result = self.scan()
        stats = scan_result['stats']
        
        output = [
            f"📂 WORKSPACE: {scan_result['workspace']}",
            "=" * 60,
            "",
            f"📊 Statistics:",
            f"  Files: {stats['total_files']}",
            f"  Directories: {stats['total_dirs']}",
            f"  Total size: {self._format_size(stats['total_size'])}",
            ""
        ]
        
        if stats['languages']:
            output.append("💻 Languages:")
            for lang, count in sorted(stats['languages'].items(), key=lambda x: -x[1]):
                output.append(f"  {lang}: {count} files")
            output.append("")
        
        if stats['file_types']:
            output.append("📝 Top file types:")
            top_types = sorted(stats['file_types'].items(), key=lambda x: -x[1])[:5]
            for ext, count in top_types:
                output.append(f"  {ext}: {count} files")
        
        return "\n".join(output)
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format.
        
        Args:
            size: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def get_workspace_scanner(workspace_dir: str = ".") -> WorkspaceScanner:
    """Get a workspace scanner instance.
    
    Args:
        workspace_dir: Workspace root directory
        
    Returns:
        WorkspaceScanner instance
    """
    return WorkspaceScanner(workspace_dir)
