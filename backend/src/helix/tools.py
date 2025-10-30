"""Tool implementations exposed to the Agno Agent.

Tools:
- FileReaderTool: read files from workspace
- SearchTool: search files by keyword/regex
- CodeExecutorTool: run snippets in a constrained subprocess (NOT fully secure)
- DocHelperTool: generate/explain documentation (calls model via agent)

These are simple, clear implementations and should be hardened before production.
"""
from typing import Optional, Dict, Any, List
import os
import re
import tempfile
import subprocess
import shlex
from pathlib import Path


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
