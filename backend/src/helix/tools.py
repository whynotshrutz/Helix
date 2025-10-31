"""Tool implementations exposed to the Agno Agent.

Tools:
- FileReaderTool: read files from workspace
- SearchTool: search files by keyword/regex
- CodeExecutorTool: run snippets in a constrained subprocess (NOT fully secure)
- DocHelperTool: generate/explain documentation (calls model via agent)
- CodeAnalyzerTool: analyze entire directory structure and provide recommendations
- FileWriterTool: write/create files with safety confirmations

These are simple, clear implementations and should be hardened before production.
"""
from typing import Optional, Dict, Any, List
import os
import re
import tempfile
import subprocess
import shlex
from pathlib import Path
from collections import defaultdict
from .safety_manager import (
    get_safety_manager,
    OperationType,
    SafetyMode,
    ask_user_confirmation
)


def file_reader_tool(path: str, base_dir: str = ".") -> Dict[str, Any]:
    target = Path(base_dir) / Path(path)
    if not target.exists():
        return {"ok": False, "error": "file_not_found", "path": str(target)}
    if target.is_dir():
        files = [str(p) for p in target.rglob("*") if p.is_file()]
        return {"ok": True, "type": "dir", "files": files}
    try:
        content = target.read_text(encoding="utf-8")
        return {"ok": True, "type": "file", "path": str(target), "content": content}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def search_tool(query: str, base_dir: str = ".", use_regex: bool = False, max_results: int = 20) -> List[Dict[str, Any]]:
    results = []
    pattern = re.compile(query) if use_regex else None
    for p in Path(base_dir).rglob("*"):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if (use_regex and pattern.search(text)) or (not use_regex and query in text):
            snippet_idx = text.find(query) if not use_regex else pattern.search(text).start()
            snippet = text[max(0, snippet_idx - 80): snippet_idx + 80]
            results.append({"path": str(p), "snippet": snippet})
            if len(results) >= max_results:
                break
    return results


def code_executor_tool(code: str, language: str = "python", timeout: int = 5) -> Dict[str, Any]:
    """Execute code snippets in a Docker-based sandbox.

    If Docker executor is not available, falls back to local subprocess with warnings.
    """
    executor_url = os.getenv("CODE_EXECUTOR_URL", "http://localhost:8888")
    
    try:
        import httpx
        import asyncio
        
        async def _execute():
            async with httpx.AsyncClient(timeout=timeout + 2) as client:
                resp = await client.post(
                    f"{executor_url}/execute",
                    json={"code": code, "language": language, "timeout": timeout}
                )
                resp.raise_for_status()
                return resp.json()
        
        # Run async function in sync context
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context
            import asyncio
            task = asyncio.create_task(_execute())
            return asyncio.run(asyncio.wait_for(task, timeout=timeout + 3))
        else:
            return asyncio.run(_execute())
    except Exception as docker_err:
        # Fallback to local execution with warning
        print(f"Warning: Docker executor unavailable ({docker_err}), using local fallback")
        
        with tempfile.TemporaryDirectory() as td:
            if language == "python":
                file_path = Path(td) / "snippet.py"
                file_path.write_text(code, encoding="utf-8")
                cmd = ["python", str(file_path)]
            else:
                file_path = Path(td) / "snippet.sh"
                file_path.write_text(code, encoding="utf-8")
                cmd = ["bash", str(file_path)]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                return {"ok": True, "stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}
            except subprocess.TimeoutExpired:
                return {"ok": False, "error": "timeout"}
            except Exception as e:
                return {"ok": False, "error": str(e)}


def doc_helper_tool(code: str, request: str = "explain", max_lines: int = 200) -> Dict[str, Any]:
    """Local helper: by default, returns a short explanation or docstring suggestion.

    In production, this could call the agent/model to generate high-quality docs.
    """
    if request == "explain":
        lines = code.splitlines()
        snippet = "\n".join(lines[:max_lines])
        # Very naive explanation: return function names and TODOs
        funcs = re.findall(r"def\s+(\w+)\s*\(", code)
        classes = re.findall(r"class\s+(\w+)\s*[:\(]", code)
        return {"ok": True, "functions": funcs, "classes": classes, "snippet": snippet}
    elif request == "docstring":
        # stub docstring generator
        return {"ok": True, "docstring": f"Auto-generated docstring for snippet (length {len(code)})."}
    else:
        return {"ok": False, "error": "unknown_request"}


def file_writer_tool(path: str, content: str, base_dir: str = ".", confirm: bool = True) -> Dict[str, Any]:
    """Write or create a file with safety confirmations.
    
    Args:
        path: Relative path to file
        content: Content to write
        base_dir: Base directory for relative paths
        confirm: Whether to ask for confirmation (controlled by safety manager)
        
    Returns:
        Dict with ok status, operation type, and result
    """
    safety = get_safety_manager()
    target = Path(base_dir) / Path(path)
    
    # Determine operation type
    if target.exists():
        operation = OperationType.UPDATE
        details = f"Overwriting existing file ({target.stat().st_size} bytes → {len(content)} bytes)"
    else:
        operation = OperationType.CREATE
        details = f"Creating new file ({len(content)} bytes)"
    
    # Check if confirmation needed
    if confirm:
        needs_confirm, prompt = safety.needs_confirmation(operation, str(target), details)
        
        if needs_confirm:
            # Ask user for confirmation
            if not ask_user_confirmation(prompt):
                return {
                    "ok": False,
                    "error": "user_cancelled",
                    "message": "Operation cancelled by user"
                }
            
            # Mark as confirmed
            safety.confirm_operation(operation, str(target))
    
    # Perform the write operation
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "ok": True,
            "operation": operation.value,
            "path": str(target),
            "size": len(content),
            "message": f"Successfully {'created' if operation == OperationType.CREATE else 'updated'} {target.name}"
        }
    except Exception as e:
        return {
            "ok": False,
            "error": "write_failed",
            "message": str(e)
        }


def code_analyzer_tool(base_dir: str = ".", max_files: int = 100) -> Dict[str, Any]:
    """Analyze all code files in directory and provide comprehensive insights.
    
    Returns:
        - File count by language
        - Code quality metrics
        - Detected patterns and anti-patterns
        - Recommendations for improvement
    """
    code_extensions = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.jsx': 'react', '.tsx': 'react-typescript', '.java': 'java',
        '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp', '.go': 'go',
        '.rs': 'rust', '.rb': 'ruby', '.php': 'php'
    }
    
    stats = {
        'total_files': 0,
        'total_lines': 0,
        'languages': defaultdict(int),
        'files_by_language': defaultdict(list),
        'issues': [],
        'recommendations': [],
        'structure': {}
    }
    
    base_path = Path(base_dir)
    
    for file_path in base_path.rglob('*'):
        # Skip non-code files and directories
        if file_path.is_dir() or file_path.name.startswith('.'):
            continue
            
        # Skip node_modules, venv, etc.
        if any(part in ['node_modules', 'venv', '__pycache__', 'dist', 'build', '.git']
               for part in file_path.parts):
            continue
            
        # Check if it's a code file
        ext = file_path.suffix.lower()
        if ext not in code_extensions:
            continue
            
        if stats['total_files'] >= max_files:
            break
            
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            line_count = len(lines)
            
            language = code_extensions[ext]
            stats['total_files'] += 1
            stats['total_lines'] += line_count
            stats['languages'][language] += 1
            stats['files_by_language'][language].append({
                'path': str(file_path.relative_to(base_path)),
                'lines': line_count
            })
            
            # Basic code quality checks
            _analyze_code_quality(content, file_path, language, stats)
            
        except Exception as e:
            stats['issues'].append(f"Error reading {file_path}: {str(e)}")
    
    # Generate recommendations
    _generate_recommendations(stats)
    
    return {
        'ok': True,
        'summary': {
            'total_files': stats['total_files'],
            'total_lines': stats['total_lines'],
            'languages': dict(stats['languages'])
        },
        'files_by_language': dict(stats['files_by_language']),
        'issues': stats['issues'],
        'recommendations': stats['recommendations']
    }


def _analyze_code_quality(content: str, file_path: Path, language: str, stats: dict):
    """Analyze code quality and detect common issues."""
    lines = content.splitlines()
    
    # Check for TODO/FIXME comments
    todos = [i for i, line in enumerate(lines) if 'TODO' in line or 'FIXME' in line]
    if todos:
        stats['issues'].append(f"{file_path.name}: {len(todos)} TODO/FIXME comments found")
    
    # Check for long functions (Python-specific)
    if language == 'python':
        func_pattern = re.compile(r'^def\s+(\w+)\s*\(')
        current_func = None
        func_start = 0
        
        for i, line in enumerate(lines):
            if func_pattern.match(line.strip()):
                if current_func and (i - func_start) > 50:
                    stats['issues'].append(
                        f"{file_path.name}: Function '{current_func}' is too long ({i - func_start} lines)"
                    )
                current_func = func_pattern.match(line.strip()).group(1)
                func_start = i
    
    # Check for missing documentation
    if language == 'python' and len(lines) > 10:
        if not any('"""' in line or "'''" in line for line in lines[:10]):
            stats['issues'].append(f"{file_path.name}: Missing module docstring")
    
    # Check for hardcoded credentials (basic check)
    dangerous_patterns = ['password =', 'api_key =', 'secret =', 'token =']
    for i, line in enumerate(lines):
        if any(pattern in line.lower() for pattern in dangerous_patterns):
            if not line.strip().startswith('#'):
                stats['issues'].append(
                    f"{file_path.name}:{i+1}: Possible hardcoded credential detected"
                )


def _generate_recommendations(stats: dict):
    """Generate actionable recommendations based on analysis."""
    
    # Check code distribution
    if stats['total_files'] == 0:
        stats['recommendations'].append("No code files found in directory")
        return
    
    # Language-specific recommendations
    languages = stats['languages']
    
    if 'python' in languages:
        stats['recommendations'].append(
            "Python detected: Consider using pylint/flake8 for code quality checks"
        )
    
    if 'javascript' in languages or 'typescript' in languages:
        stats['recommendations'].append(
            "JavaScript/TypeScript detected: Consider using ESLint for linting"
        )
    
    # Structure recommendations
    avg_lines_per_file = stats['total_lines'] / stats['total_files']
    if avg_lines_per_file > 500:
        stats['recommendations'].append(
            f"Files are quite large (avg {avg_lines_per_file:.0f} lines). "
            "Consider breaking them into smaller modules"
        )
    
    # Issue-based recommendations
    if len(stats['issues']) > 10:
        stats['recommendations'].append(
            f"Found {len(stats['issues'])} code quality issues. "
            "Review and address them to improve maintainability"
        )
    
    if not stats['issues']:
        stats['recommendations'].append(
            "No major issues detected! Code structure looks good."
        )
