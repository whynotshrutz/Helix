"""Secure code executor service running in Docker container.

This service accepts code execution requests via HTTP and runs them
in a resource-limited, sandboxed environment.
"""
import asyncio
import tempfile
import subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Helix Code Executor")


class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = 5


class ExecuteResponse(BaseModel):
    ok: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    error: str = ""


@app.post("/execute", response_model=ExecuteResponse)
async def execute_code(req: ExecuteRequest):
    """Execute code in a sandboxed environment with resource limits."""
    
    with tempfile.TemporaryDirectory() as td:
        try:
            if req.language == "python":
                file_path = Path(td) / "snippet.py"
                file_path.write_text(req.code, encoding="utf-8")
                cmd = ["python", "-u", str(file_path)]
            elif req.language in ["bash", "sh"]:
                file_path = Path(td) / "snippet.sh"
                file_path.write_text(req.code, encoding="utf-8")
                cmd = ["bash", str(file_path)]
            elif req.language == "javascript":
                file_path = Path(td) / "snippet.js"
                file_path.write_text(req.code, encoding="utf-8")
                cmd = ["node", str(file_path)]
            else:
                return ExecuteResponse(
                    ok=False,
                    error=f"Unsupported language: {req.language}"
                )
            
            # Run with resource limits
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=td,
                limit=1024 * 1024  # 1MB buffer limit
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=req.timeout
                )
                
                return ExecuteResponse(
                    ok=True,
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    returncode=proc.returncode or 0
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return ExecuteResponse(
                    ok=False,
                    error="Execution timed out"
                )
                
        except Exception as e:
            return ExecuteResponse(
                ok=False,
                error=str(e)
            )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
