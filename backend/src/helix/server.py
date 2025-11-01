"""FastAPI-based FastMCP-compatible bridge exposing endpoints for VS Code MCP client.

This is a small HTTP server that accepts chat and completion requests and proxies
them to the Agno agent. It aims to be compatible with a FastMCP backend pattern.
"""
import os
import asyncio
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, AsyncIterator, List
from .github_integration import GitHubIntegrationAgent, PullRequestInfo, RepositoryInfo

load_dotenv()

# Handle both relative and absolute imports
try:
    from .agno_agent import create_agent
except ImportError:
    from agno_agent import create_agent

app = FastAPI(title="Helix FastMCP Bridge")


class RunRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    prompt: str
    mode: Optional[str] = "chat"  # chat | inline
    stream: Optional[bool] = False
    inline_completion: Optional[bool] = False  # Flag to prevent file creation


@app.on_event("startup")
async def startup_event():
    # Create the agent once on startup; Agno supports multiple users via session_id
    loop = asyncio.get_event_loop()
    try:
        app.state.agent = create_agent()
        app.state.github_agent = GitHubIntegrationAgent()
    except Exception as e:
        # Agent creation failed (missing dependencies) — keep server up for testing
        app.state.agent = None
        app.state.agent_error = str(e)
        app.state.github_agent = None


def _parse_and_create_files(content: str, workspace_dir: str = ".") -> str:
    """Parse agent response for CREATE_FILE markers and create the files."""
    import re
    from pathlib import Path
    
    # Pattern: CREATE_FILE: filename.ext followed by code block
    pattern = r'CREATE_FILE:\s*([^\n]+)\s*```(\w+)?\s*\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for filename, language, code in matches:
        filename = filename.strip()
        code = code.strip()
        
        try:
            file_path = Path(workspace_dir) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(code, encoding='utf-8')
            print(f"✅ Auto-created file: {filename} ({len(code)} bytes)")
            
            # Add confirmation to the response
            content += f"\n\n✅ File created: `{filename}` ({len(code)} bytes)"
        except Exception as e:
            print(f"❌ Failed to create {filename}: {e}")
            content += f"\n\n❌ Failed to create `{filename}`: {str(e)}"
    
    return content


async def _stream_agent_events(agent, prompt: str, user_id: Optional[str], session_id: Optional[str], inline_completion: bool = False) -> AsyncIterator[str]:
    """Stream agent events as Server-Sent Events (SSE)."""
    try:
        # Run agent synchronously in thread pool and stream response
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: agent.run(prompt))
        
        # Get the content
        content = getattr(result, "content", str(result))
        run_id = getattr(result, "run_id", None)
        
        # File creation is now handled by VS Code extension, not server
        # Just return the content as-is
        
        # Send the complete response
        event_data = {
            "event": "response",
            "content": content,
            "run_id": run_id,
        }
        yield f"data: {json.dumps(event_data)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        error_data = {"error": str(e)}
        yield f"data: {json.dumps(error_data)}\n\n"


@app.get("/health")
async def health():
    """Health check endpoint showing agent status."""
    agent = getattr(app.state, "agent", None)
    if agent is None:
        error = getattr(app.state, 'agent_error', 'unknown')
        return {"status": "unhealthy", "error": error}
    return {"status": "healthy", "agent": "ready"}


@app.post("/run")
async def run(req: RunRequest):
    agent = getattr(app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail=f"Agent not available: {getattr(app.state, 'agent_error', 'unknown')}")

    # Streaming mode
    if req.stream:
        return StreamingResponse(
            _stream_agent_events(agent, req.prompt, req.user_id, req.session_id, req.inline_completion),
            media_type="text/event-stream"
        )

    # Non-streaming mode
    try:
        # Use run() for non-streaming, arun() returns generator
        if hasattr(agent, "run"):
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: agent.run(req.prompt))
        else:
            raise HTTPException(status_code=500, detail="Agent doesn't support synchronous execution")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Get content - file creation is now handled by VS Code extension
    content = getattr(result, "content", str(result))
    
    # Return content with file creation results
    return {"content": content, "run_id": getattr(result, "run_id", None)}


# GitHub Integration Endpoints
@app.get("/github/auth/status")
async def github_auth_status():
    """Get GitHub authentication status."""
    if not app.state.github_agent:
        raise HTTPException(status_code=503, detail="GitHub integration not available")
    return JSONResponse(app.state.github_agent.get_authentication_status())

@app.get("/github/repositories")
async def list_repositories(
    filter_private: bool = False,
    sort_by: str = "updated",
    limit: int = 30
) -> List[RepositoryInfo]:
    """List GitHub repositories."""
    if not app.state.github_agent:
        raise HTTPException(status_code=503, detail="GitHub integration not available")
    try:
        return await app.state.github_agent.list_repositories(filter_private, sort_by, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class FileUpdateRequest(BaseModel):
    content: str
    message: str
    branch: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "content": "File content here",
                "message": "Commit message",
                "branch": "main"
            }
        }

@app.post("/github/{owner}/{repo}/pr")
async def create_pull_request(
    owner: str,
    repo: str,
    pr_info: PullRequestInfo
):
    """Create a pull request."""
    if not app.state.github_agent:
        raise HTTPException(status_code=503, detail="GitHub integration not available")
    try:
        # Validate that base and head branches exist
        if not pr_info.base or not pr_info.head:
            raise ValueError("Both base and head branches must be specified")
        return await app.state.github_agent.create_pull_request(owner, repo, pr_info)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/github/{owner}/{repo}/content/{path:path}")
async def update_file(
    owner: str,
    repo: str,
    path: str,
    file_update: FileUpdateRequest
):
    """Update or create a file in the repository."""
    if not app.state.github_agent:
        raise HTTPException(status_code=503, detail="GitHub integration not available")
    try:
        return await app.state.github_agent.update_file(
            owner=owner,
            repo=repo,
            path=path,
            content=file_update.content,
            message=file_update.message,
            branch=file_update.branch
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("helix.server:app", host=os.getenv("FASTMCP_BIND_HOST", "127.0.0.1"), port=int(os.getenv("FASTMCP_BIND_PORT", 8000)), reload=False)
