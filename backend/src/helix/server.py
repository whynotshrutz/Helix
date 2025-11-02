"""FastAPI-based server for Helix AI Assistant.

This HTTP server accepts chat and completion requests from the VS Code extension
and routes them to the appropriate AI agent (multi-agent system with NVIDIA NIM).
"""
import os
import asyncio
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, AsyncIterator

load_dotenv()

# Handle both relative and absolute imports
try:
    from .agno_agent import create_agent
    from .multi_agent_system import create_multi_agent_system
except ImportError:
    from agno_agent import create_agent
    from multi_agent_system import create_multi_agent_system

app = FastAPI(title="Helix AI Server")

# Add CORS middleware to allow VS Code extension to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    prompt: str
    mode: Optional[str] = "chat"  # chat | inline
    stream: Optional[bool] = False
    inline_completion: Optional[bool] = False  # Flag to prevent file creation


@app.on_event("startup")
async def startup_event():
    # Check if we should use multi-agent system or single agent
    use_multi_agent = os.getenv("HELIX_MULTI_AGENT", "true").lower() == "true"
    
    loop = asyncio.get_event_loop()
    try:
        if use_multi_agent:
            print("🚀 Starting Helix with Multi-Agent System...")
            app.state.multi_agent_system = create_multi_agent_system()
            app.state.agent = None  # Not using single agent
            app.state.mode = "multi-agent"
        else:
            print("🚀 Starting Helix with Single Agent...")
            app.state.agent = create_agent()
            app.state.multi_agent_system = None
            app.state.mode = "single-agent"
    except Exception as e:
        # Agent creation failed (missing dependencies) — keep server up for testing
        app.state.agent = None
        app.state.multi_agent_system = None
        app.state.agent_error = str(e)
        app.state.mode = "error"


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
    mode = getattr(app.state, "mode", "unknown")
    
    if mode == "error":
        error = getattr(app.state, 'agent_error', 'unknown')
        return {"status": "unhealthy", "error": error, "mode": mode}
    
    if mode == "multi-agent":
        multi_system = getattr(app.state, "multi_agent_system", None)
        if multi_system is None:
            return {"status": "unhealthy", "error": "Multi-agent system not initialized", "mode": mode}
        return {
            "status": "healthy", 
            "mode": "multi-agent",
            "agents": multi_system.list_agents(),
            "agent_count": len(multi_system.list_agents())
        }
    else:
        agent = getattr(app.state, "agent", None)
        if agent is None:
            return {"status": "unhealthy", "error": "Agent not initialized", "mode": mode}
        return {"status": "healthy", "mode": "single-agent", "agent": "ready"}


@app.post("/run")
async def run(req: RunRequest):
    mode = getattr(app.state, "mode", "unknown")
    
    if mode == "error":
        raise HTTPException(status_code=503, detail=f"Agent not available: {getattr(app.state, 'agent_error', 'unknown')}")
    
    # Multi-agent mode
    if mode == "multi-agent":
        multi_system = getattr(app.state, "multi_agent_system", None)
        if multi_system is None:
            raise HTTPException(status_code=503, detail="Multi-agent system not initialized")
        
        # Non-streaming mode (multi-agent doesn't support streaming yet)
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: multi_system.process_query(req.prompt))
            
            if not result.get('ok', False):
                raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
            
            # Get content from result
            if result.get('mode') == 'parallel':
                content = result.get('combined', '')
            else:
                content = result.get('response', '')
            
            # Log the response for debugging
            print(f"\n{'='*60}")
            print(f"📤 RESPONSE TO CLIENT:")
            print(f"{'='*60}")
            print(f"Mode: {result.get('mode')}")
            print(f"Agent: {result.get('agent', 'multiple')}")
            print(f"Content Length: {len(content)} chars")
            print(f"Content Preview: {content[:200]}..." if len(content) > 200 else f"Content: {content}")
            print(f"{'='*60}\n")
            
            return {
                "content": content,
                "mode": result.get('mode'),
                "agent": result.get('agent', 'multiple'),
                "run_id": None  # Multi-agent doesn't have run_id yet
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Single-agent mode (legacy)
    agent = getattr(app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not available")

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
    return {"content": content, "run_id": getattr(result, "run_id", None), "mode": "single-agent"}


@app.get("/api/memory/stats")
async def get_memory_stats():
    """Get memory statistics."""
    multi_agent = getattr(app.state, "multi_agent_system", None)
    if not multi_agent or not hasattr(multi_agent, 'memory_manager'):
        raise HTTPException(status_code=503, detail="Memory manager not available")
    
    try:
        stats = multi_agent.memory_manager.get_memory_stats()
        return {"ok": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/conversation")
async def get_conversation_history(limit: int = 50):
    """Get conversation history."""
    multi_agent = getattr(app.state, "multi_agent_system", None)
    if not multi_agent or not hasattr(multi_agent, 'memory_manager'):
        raise HTTPException(status_code=503, detail="Memory manager not available")
    
    try:
        messages = multi_agent.memory_manager.get_conversation_history(limit=limit)
        return {"ok": True, "messages": messages, "count": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/context")
async def get_project_context():
    """Get project context."""
    multi_agent = getattr(app.state, "multi_agent_system", None)
    if not multi_agent or not hasattr(multi_agent, 'memory_manager'):
        raise HTTPException(status_code=503, detail="Memory manager not available")
    
    try:
        context = multi_agent.memory_manager.get_project_context()
        return {"ok": True, "context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MemoryFactRequest(BaseModel):
    category: str
    key: str
    value: str
    ttl_days: Optional[int] = 30


@app.post("/api/memory/fact")
async def store_memory_fact(req: MemoryFactRequest):
    """Store a fact in memory."""
    multi_agent = getattr(app.state, "multi_agent_system", None)
    if not multi_agent or not hasattr(multi_agent, 'memory_manager'):
        raise HTTPException(status_code=503, detail="Memory manager not available")
    
    try:
        success = multi_agent.memory_manager.add_fact(req.category, req.key, req.value, req.ttl_days)
        return {"ok": success, "message": f"Fact stored: {req.category}/{req.key}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/memory/conversation")
async def clear_conversation():
    """Clear conversation history."""
    multi_agent = getattr(app.state, "multi_agent_system", None)
    if not multi_agent or not hasattr(multi_agent, 'memory_manager'):
        raise HTTPException(status_code=503, detail="Memory manager not available")
    
    try:
        success = multi_agent.memory_manager.clear_conversation()
        return {"ok": success, "message": "Conversation cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/git/accounts")
async def get_git_accounts():
    """Get available Git accounts from all authentication methods."""
    try:
        # Import here to avoid startup errors if git_auth_manager not available
        from .git_auth_manager import GitAuthManager
        
        workspace_dir = os.getenv("WORKSPACE_DIR", ".")
        auth_manager = GitAuthManager(workspace_dir)
        accounts = auth_manager.get_available_accounts()
        
        return {"ok": True, **accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class GitAccountSelection(BaseModel):
    account_id: str
    auth_method: str


@app.post("/api/git/select-account")
async def select_git_account(req: GitAccountSelection):
    """Store selected Git account for next operation."""
    # This endpoint can be used by the UI to confirm account selection
    # The actual push operation will use the account_id and auth_method directly
    return {
        "ok": True,
        "message": f"Account selected: {req.account_id} ({req.auth_method})",
        "account_id": req.account_id,
        "auth_method": req.auth_method
    }


class GitPATRequest(BaseModel):
    name: str
    username: str
    token: str
    email: Optional[str] = None


@app.post("/api/git/store-pat")
async def store_git_pat(req: GitPATRequest):
    """Store a Personal Access Token for Git operations."""
    try:
        from .git_auth_manager import GitAuthManager
        
        workspace_dir = os.getenv("WORKSPACE_DIR", ".")
        auth_manager = GitAuthManager(workspace_dir)
        
        result = auth_manager.store_pat(req.name, req.username, req.token, req.email)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("helix.server:app", host=os.getenv("HELIX_BIND_HOST", "127.0.0.1"), port=int(os.getenv("HELIX_BIND_PORT", 8001)), reload=False)
