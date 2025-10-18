"""Agno-based multi-agent system for Helix with AgentOS integration."""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from agno.agent import Agent
    from agno.os import AgentOS
    from agno.db.sqlite import SqliteDb
    from agno.tools.mcp import MCPTools
    from agno.tools import tool
    from agno.models.anthropic import Claude
    from agno.models.openai import OpenAIChat
    from agno.models.nvidia import Nvidia  # Use dedicated NVIDIA model class
    
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Agent = None
    AgentOS = None

from helix.config import Config
from helix.providers import ProviderRegistry


# VS Code Integration Tools
@tool
def create_file(path: str, content: str) -> Dict[str, Any]:
    """
    Create a new file in the VS Code workspace.
    
    Args:
        path: Relative path from workspace root (e.g., 'src/calculator.py')
        content: Complete file content to write
    
    Returns:
        Action instruction for VS Code extension
    """
    return {
        "action": "createFile",
        "path": path,
        "content": content,
        "status": "pending"
    }


@tool
def edit_file(path: str, old_content: str, new_content: str) -> Dict[str, Any]:
    """
    Edit an existing file by replacing old content with new content.
    
    Args:
        path: Relative path from workspace root
        old_content: Content to be replaced (must match exactly)
        new_content: New content to insert
    
    Returns:
        Action instruction for VS Code extension
    """
    return {
        "action": "editFile",
        "path": path,
        "old_content": old_content,
        "new_content": new_content,
        "status": "pending"
    }


@tool
def read_workspace_file(path: str) -> Dict[str, Any]:
    """
    Read the contents of a file in the workspace.
    
    Args:
        path: Relative path from workspace root
    
    Returns:
        Action instruction for VS Code extension to read file
    """
    return {
        "action": "readFile",
        "path": path,
        "status": "pending"
    }


@tool
def list_workspace_files(pattern: str = "**/*") -> Dict[str, Any]:
    """
    List files in the workspace matching a glob pattern.
    
    Args:
        pattern: Glob pattern (e.g., '**/*.py', 'src/**', '*.json')
    
    Returns:
        Action instruction for VS Code extension
    """
    return {
        "action": "listFiles",
        "pattern": pattern,
        "status": "pending"
    }


@tool
def run_command(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a terminal command in the workspace.
    
    Args:
        command: Shell command to execute
        cwd: Working directory (relative to workspace root, optional)
    
    Returns:
        Action instruction for VS Code extension
    """
    return {
        "action": "runCommand",
        "command": command,
        "cwd": cwd,
        "status": "pending"
    }


@tool
def git_commit(message: str, files: List[str]) -> Dict[str, Any]:
    """
    Create a git commit with specified files.
    
    Args:
        message: Commit message
        files: List of file paths to include in commit
    
    Returns:
        Action instruction for VS Code extension
    """
    return {
        "action": "gitCommit",
        "message": message,
        "files": files,
        "status": "pending"
    }


@tool
def show_preview(url: Optional[str] = None, html: Optional[str] = None) -> Dict[str, Any]:
    """
    Show a preview in VS Code (like Lovable).
    
    Args:
        url: URL to preview (e.g., 'http://localhost:3000')
        html: Direct HTML content to preview
    
    Returns:
        Action instruction for VS Code extension
    """
    return {
        "action": "showPreview",
        "url": url,
        "html": html,
        "status": "pending"
    }


@tool
def search_workspace(query: str, file_pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for text across workspace files.
    
    Args:
        query: Text or regex to search for
        file_pattern: Optional glob pattern to limit search
    
    Returns:
        Action instruction for VS Code extension
    """
    return {
        "action": "searchWorkspace",
        "query": query,
        "file_pattern": file_pattern,
        "status": "pending"
    }


@dataclass
class AgnoAgentConfig:
    """Configuration for Agno agents."""
    name: str
    model_provider: str
    model_id: str
    system_prompt: str
    tools: List[Any] = None
    add_history: bool = True
    markdown: bool = True


class AgnoHelixOrchestrator:
    """
    Helix orchestrator using Agno's multi-agent framework.
    
    Features:
    - AgentOS for runtime and UI integration
    - SqliteDb for conversation state management
    - MCP (Model Context Protocol) support
    - Multi-agent teams with coordinated execution
    """
    
    def __init__(self, config: Config):
        if not AGNO_AVAILABLE:
            raise RuntimeError(
                "Agno is not installed. Install with: pip install agno\n"
                "See: https://docs.agno.com"
            )
        
        self.config = config
        self.db = SqliteDb(db_file=config.agno_db_path)
        self.agents = {}
        self.agent_os = None
        
        # Set up environment for Agno
        self._setup_environment()
        
        # Initialize agents
        self._create_agents()
    
    def _setup_environment(self):
        """Set up environment variables for Agno to work properly."""
        import os
        
        # For NVIDIA NIM, set the NVIDIA_API_KEY that Agno expects
        if self.config.get_provider() == "nvidia_nim" and self.config.nim_api_key:
            os.environ["NVIDIA_API_KEY"] = self.config.nim_api_key
            print(f"✓ Using NVIDIA NIM with API key from config")
        
        # Set other API keys if available
        if self.config.agno_api_key:
            os.environ["AGNO_API_KEY"] = self.config.agno_api_key
    
    def _get_agno_model(self, provider: str, model_id: str):
        """Get Agno model instance based on provider."""
        if provider == "anthropic" or "claude" in model_id.lower():
            api_key = self.config.options.get("anthropic_api_key")
            return Claude(id=model_id, api_key=api_key) if api_key else Claude(id=model_id)
        elif provider == "openai" or "gpt" in model_id.lower():
            api_key = self.config.options.get("openai_api_key")
            return OpenAIChat(id=model_id, api_key=api_key) if api_key else OpenAIChat(id=model_id)
        elif provider == "nvidia_nim":
            # Use Agno's dedicated Nvidia model class
            if not self.config.nim_api_key:
                raise ValueError(
                    "NIM_API_KEY is not set. Please set it in your .env file or environment.\n"
                    "Get your API key from: https://build.nvidia.com"
                )
            # Agno's Nvidia class handles role compatibility automatically
            return Nvidia(
                id=model_id,
                api_key=self.config.nim_api_key,
                base_url=self.config.nim_base_url
            )
        else:
            # Default to OpenAI-compatible
            return OpenAIChat(id=model_id)
    
    def _create_agents(self):
        """Create specialized Agno agents for Helix workflow."""
        
        # Get model configuration
        provider = self.config.get_provider()
        model_id = self.config.get_model()
        
        # Planner Agent (with VS Code tools)
        planner_model = self._get_agno_model(provider, model_id)
        self.agents["planner"] = Agent(
            name="Planner",
            model=planner_model,
            db=self.db,
            add_history_to_context=True,
            markdown=True,
            description="Analyzes prompts and creates execution plans",
            instructions=[
                "Parse natural language prompts into structured tasks",
                "Analyze repository state and context",
                "Create prioritized task lists with clear requirements",
                "Define test coverage and quality requirements",
                "Generate appropriate branch names",
                "Use list_workspace_files() to understand project structure",
                "Use search_workspace() to find relevant code",
                "Use read_workspace_file() to analyze existing files"
            ],
            tools=[list_workspace_files, search_workspace, read_workspace_file]
        )
        
        # Coder Agent (with VS Code tools)
        coder_model = self._get_agno_model(provider, model_id)
        self.agents["coder"] = Agent(
            name="Coder",
            model=coder_model,
            db=self.db,
            add_history_to_context=True,
            markdown=True,
            description="Generates and modifies code",
            instructions=[
                "Generate clean, production-ready code",
                "Follow best practices and style guidelines",
                "Add comprehensive docstrings and type hints",
                "Implement proper error handling",
                "Create or update tests as needed",
                "Use create_file() to create new files in the workspace",
                "Use edit_file() to modify existing files",
                "Use read_workspace_file() to read file contents before editing",
                "Use show_preview() to display web previews of generated code"
            ],
            tools=[create_file, edit_file, read_workspace_file, list_workspace_files, run_command, show_preview]
        )
        
        # Tester Agent (with VS Code tools)
        tester_model = self._get_agno_model(provider, model_id)
        self.agents["tester"] = Agent(
            name="Tester",
            model=tester_model,
            db=self.db,
            add_history_to_context=True,
            markdown=True,
            description="Runs tests and performs quality checks",
            instructions=[
                "Execute unit tests and integration tests",
                "Run static analysis (mypy, flake8, bandit)",
                "Calculate test coverage",
                "Identify and report issues",
                "Suggest improvements",
                "Use create_file() to create test files",
                "Use run_command() to execute tests",
                "Use search_workspace() to find existing tests"
            ],
            tools=[create_file, read_workspace_file, run_command, search_workspace, list_workspace_files]
        )
        
        # Reviewer Agent (new - inspired by Orion's validation, with VS Code tools)
        reviewer_model = self._get_agno_model(provider, model_id)
        self.agents["reviewer"] = Agent(
            name="Reviewer",
            model=reviewer_model,
            db=self.db,
            add_history_to_context=True,
            markdown=True,
            description="Reviews code changes and ensures quality",
            instructions=[
                "Review code diffs for correctness",
                "Check for security vulnerabilities",
                "Verify adherence to coding standards",
                "Ensure tests cover changes",
                "Provide constructive feedback",
                "Use read_workspace_file() to read files for review",
                "Use search_workspace() to check for similar patterns",
                "Use list_workspace_files() to understand project structure"
            ],
            tools=[read_workspace_file, search_workspace, list_workspace_files, run_command]
        )
        
        # Explainer Agent (with VS Code tools)
        explainer_model = self._get_agno_model(provider, model_id)
        self.agents["explainer"] = Agent(
            name="Explainer",
            model=explainer_model,
            db=self.db,
            add_history_to_context=True,
            markdown=True,
            description="Generates human-readable explanations",
            instructions=[
                "Create clear, concise explanations of changes",
                "Document what was changed and why",
                "Provide run commands and usage examples",
                "Suggest next steps",
                "Generate comprehensive documentation",
                "Use read_workspace_file() to understand code changes",
                "Use create_file() to generate documentation files"
            ],
            tools=[read_workspace_file, create_file, list_workspace_files]
        )
        
        # Add MCP tools if enabled
        if self.config.agno_use_mcp:
            try:
                mcp_tools = MCPTools(
                    transport="streamable-http",
                    url="https://docs.agno.com/mcp"
                )
                for agent in self.agents.values():
                    if agent.tools is None:
                        agent.tools = []
                    agent.tools.append(mcp_tools)
            except Exception as e:
                print(f"⚠️  MCP tools not available: {e}")
    
    def create_agent_os(self, custom_app: Optional[Any] = None) -> AgentOS:
        """
        Create AgentOS for runtime and UI integration.
        
        AgentOS provides:
        - RESTful API endpoints for agent runs
        - Session management and tracking
        - Chat interface compatibility
        - Knowledge and memory management
        - Metrics and monitoring
        
        Args:
            custom_app: Optional custom FastAPI app to integrate with
        
        Returns:
            AgentOS instance with all agents configured
        """
        agent_list = list(self.agents.values())
        
        # Create AgentOS with comprehensive configuration
        # Note: Telemetry should be True for Control Plane connectivity
        self.agent_os = AgentOS(
            id="helix-agentos",
            name="Helix AgentOS",
            description="Multi-agent development assistant with NVIDIA NIM and intelligent workflow orchestration",
            version="2.0.0",
            agents=agent_list,
            base_app=custom_app,  # Support custom FastAPI integration
            enable_mcp_server=self.config.agno_use_mcp,  # Enable MCP if configured
            telemetry=True,  # Enable telemetry for Control Plane connectivity
        )
        
        print("✓ AgentOS created with agents:", [agent.name for agent in agent_list])
        
        # Add VS Code integration routes
        self._add_vscode_routes()
        
        return self.agent_os
    
    def _add_vscode_routes(self):
        """Add VS Code integration API routes to AgentOS."""
        if self.agent_os is None:
            return
        
        from fastapi import APIRouter, Body
        from pydantic import BaseModel
        
        # Create VS Code router
        vscode_router = APIRouter(prefix="/vscode", tags=["VS Code Integration"])
        
        class ToolExecutionRequest(BaseModel):
            """Request to execute a tool action."""
            tool: str
            parameters: Dict[str, Any]
            agent_id: Optional[str] = None
        
        class WorkspaceContextRequest(BaseModel):
            """Workspace context from VS Code."""
            workspace_folder: str
            open_files: List[str] = []
            active_file: Optional[str] = None
            file_contents: Dict[str, str] = {}
        
        @vscode_router.post("/execute-tool")
        async def execute_tool(request: ToolExecutionRequest):
            """
            Execute a tool action from VS Code extension.
            
            This endpoint receives tool calls from agents and returns
            actions for VS Code to perform.
            """
            return {
                "action": request.tool,
                "params": request.parameters,
                "agent_id": request.agent_id,
                "status": "pending",
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
        
        @vscode_router.post("/workspace-context")
        async def update_workspace_context(request: WorkspaceContextRequest):
            """
            Receive workspace context from VS Code.
            
            This allows agents to have context about the current workspace,
            open files, and active editor state.
            """
            # Store context for agents to use
            # This could be stored in agent_os memory or database
            return {
                "success": True,
                "message": "Workspace context updated",
                "workspace": request.workspace_folder,
                "files_count": len(request.open_files)
            }
        
        @vscode_router.get("/health")
        async def vscode_health():
            """Health check for VS Code extension."""
            return {
                "status": "ok",
                "agents": list(self.agents.keys()),
                "version": "2.0.0"
            }
        
        # Add router to AgentOS app
        app = self.agent_os.get_app()
        app.include_router(vscode_router)
        print("✓ VS Code integration routes added")
    
    def get_fastapi_app(self):
        """
        Get FastAPI application for AgentOS.
        
        This returns a complete FastAPI app with:
        - Agent run endpoints: POST /agents/{agent_id}/runs
        - Session management: GET/POST/DELETE /sessions
        - Memory management: GET/POST/DELETE /memories
        - Knowledge base: GET/POST/DELETE /knowledge
        - API docs: GET /docs
        - Configuration: GET /config
        
        Returns:
            FastAPI app instance ready to serve
        """
        if self.agent_os is None:
            self.create_agent_os()
        return self.agent_os.get_app()
    
    def serve(self, host: str = "localhost", port: int = 7777, reload: bool = False, workers: Optional[int] = None):
        """
        Serve AgentOS with FastAPI server.
        
        This starts a production-ready FastAPI server with:
        - HTTP API at http://{host}:{port}
        - Interactive docs at http://{host}:{port}/docs
        - AgentOS config at http://{host}:{port}/config
        
        The server can be connected to the AgentOS Control Plane at https://agno.com
        for a web-based management interface.
        
        Args:
            host: Host address (default: localhost, use 0.0.0.0 for external access)
            port: Port number (default: 7777 - AgentOS standard port)
            reload: Enable auto-reload for development (default: False)
            workers: Number of worker processes for production (default: None)
        
        Example:
            >>> orchestrator = AgnoHelixOrchestrator(config)
            >>> orchestrator.serve(host="0.0.0.0", port=7777, reload=True)
        """
        if self.agent_os is None:
            self.create_agent_os()
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting Helix AgentOS Server")
        print(f"{'='*60}")
        print(f"📍 Local:     http://{host}:{port}")
        print(f"📚 API Docs:  http://{host}:{port}/docs")
        print(f"⚙️  Config:    http://{host}:{port}/config")
        print(f"{'='*60}\n")
        
        # Serve using AgentOS's built-in server with uvicorn
        # According to Agno docs, we need to run uvicorn directly with the app
        import uvicorn
        from fastapi.middleware.cors import CORSMiddleware
        
        # Get the FastAPI app
        app = self.agent_os.get_app()
        
        # Add CORS middleware to allow Control Plane access
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://os.agno.com", "https://agno.com"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Configure uvicorn
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        
        try:
            server.run()
        except KeyboardInterrupt:
            print("\n👋 Shutting down Helix AgentOS Server...")
        except Exception as e:
            print(f"\n❌ Error starting server: {e}")
            raise
    
    def execute(self, user_prompt: str, workspace: Optional[Path] = None) -> Dict[str, Any]:
        """
        Execute multi-agent workflow for a user prompt.
        
        Args:
            user_prompt: Natural language description of task
            workspace: Workspace directory (defaults to config workspace)
            
        Returns:
            Results dictionary with outputs from all agents
        """
        if workspace is None:
            workspace = self.config.workspace_dir
        
        results = {
            "success": False,
            "prompt": user_prompt,
            "workspace": str(workspace),
            "agents": {},
            "outputs": {}
        }
        
        try:
            # Step 1: Planning
            print("🔍 Planning phase...")
            plan_response = self.agents["planner"].run(
                f"Create an execution plan for: {user_prompt}\n"
                f"Workspace: {workspace}"
            )
            results["agents"]["planner"] = {
                "response": plan_response.content,
                "success": True
            }
            
            # Step 2: Coding
            print("💻 Coding phase...")
            code_response = self.agents["coder"].run(
                f"Implement the following plan:\n{plan_response.content}\n"
                f"Workspace: {workspace}"
            )
            results["agents"]["coder"] = {
                "response": code_response.content,
                "success": True
            }
            
            # Step 3: Review
            print("🔎 Review phase...")
            review_response = self.agents["reviewer"].run(
                f"Review the following changes:\n{code_response.content}"
            )
            results["agents"]["reviewer"] = {
                "response": review_response.content,
                "success": True
            }
            
            # Step 4: Testing (if review passes)
            if "approved" in review_response.content.lower() or "looks good" in review_response.content.lower():
                print("✅ Testing phase...")
                test_response = self.agents["tester"].run(
                    f"Run tests for the changes in: {workspace}"
                )
                results["agents"]["tester"] = {
                    "response": test_response.content,
                    "success": True
                }
            
            # Step 5: Explanation
            print("📝 Generating explanation...")
            explain_response = self.agents["explainer"].run(
                f"Explain the following changes:\n"
                f"Plan: {plan_response.content}\n"
                f"Code: {code_response.content}\n"
                f"Review: {review_response.content}"
            )
            results["agents"]["explainer"] = {
                "response": explain_response.content,
                "success": True
            }
            
            results["success"] = True
            results["explanation"] = explain_response.content
            
        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Execution failed: {e}")
        
        return results
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get agent by name."""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all available agents."""
        return list(self.agents.keys())
    
    def create_agentos_file(self, output_path: Optional[Path] = None) -> Path:
        """
        Create a standalone AgentOS Python file that can be served.
        
        This generates a complete AgentOS application file that can be run
        independently with: python agentos_app.py
        
        Args:
            output_path: Where to save the file (default: workspace/agentos_app.py)
        
        Returns:
            Path to the created file
        
        Example:
            >>> orchestrator = AgnoHelixOrchestrator(config)
            >>> app_file = orchestrator.create_agentos_file()
            >>> # Run with: python agentos_app.py
        """
        if output_path is None:
            output_path = self.config.workspace_dir / "agentos_app.py"
        
        # Generate the AgentOS application code
        app_code = '''"""
Helix AgentOS Application

This is a standalone AgentOS server for the Helix multi-agent system.
Run with: python agentos_app.py

Access:
- API: http://localhost:7777
- Docs: http://localhost:7777/docs
- Config: http://localhost:7777/config

Connect to AgentOS Control Plane at https://agno.com
"""

from pathlib import Path
from agno.agent import Agent
from agno.models.nvidia import Nvidia
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS

# Setup database
db = SqliteDb(db_file="tmp/helix_agentos.db")

# Configure NVIDIA NIM model
model_id = "meta/llama-3.1-70b-instruct"
nvidia_api_key = "YOUR_NVIDIA_API_KEY"  # Set your key or use env var

# Create agents
planner = Agent(
    name="Planner",
    model=Nvidia(id=model_id, api_key=nvidia_api_key),
    db=db,
    add_history_to_context=True,
    markdown=True,
    description="Analyzes prompts and creates execution plans",
    instructions=[
        "Parse natural language prompts into structured tasks",
        "Analyze repository state and context",
        "Create prioritized task lists with clear requirements",
        "Define test coverage and quality requirements",
        "Generate appropriate branch names"
    ]
)

coder = Agent(
    name="Coder",
    model=Nvidia(id=model_id, api_key=nvidia_api_key),
    db=db,
    add_history_to_context=True,
    markdown=True,
    description="Generates and modifies code",
    instructions=[
        "Generate clean, production-ready code",
        "Follow best practices and style guidelines",
        "Add comprehensive docstrings and type hints",
        "Implement proper error handling",
        "Create or update tests as needed"
    ]
)

tester = Agent(
    name="Tester",
    model=Nvidia(id=model_id, api_key=nvidia_api_key),
    db=db,
    add_history_to_context=True,
    markdown=True,
    description="Runs tests and performs quality checks",
    instructions=[
        "Execute unit tests and integration tests",
        "Run static analysis (mypy, flake8, bandit)",
        "Calculate test coverage",
        "Identify and report issues",
        "Suggest improvements"
    ]
)

reviewer = Agent(
    name="Reviewer",
    model=Nvidia(id=model_id, api_key=nvidia_api_key),
    db=db,
    add_history_to_context=True,
    markdown=True,
    description="Reviews code changes and ensures quality",
    instructions=[
        "Review code diffs for correctness",
        "Check for security vulnerabilities",
        "Verify adherence to coding standards",
        "Ensure tests cover changes",
        "Provide constructive feedback"
    ]
)

explainer = Agent(
    name="Explainer",
    model=Nvidia(id=model_id, api_key=nvidia_api_key),
    db=db,
    add_history_to_context=True,
    markdown=True,
    description="Generates human-readable explanations",
    instructions=[
        "Create clear, concise explanations of changes",
        "Document what was changed and why",
        "Provide run commands and usage examples",
        "Suggest next steps",
        "Generate comprehensive documentation"
    ]
)

# Create AgentOS
agent_os = AgentOS(
    id="helix-agentos",
    name="Helix AgentOS",
    description="Multi-agent development assistant with NVIDIA NIM",
    version="2.0.0",
    agents=[planner, coder, tester, reviewer, explainer],
    telemetry=False,
)

# Get FastAPI app
app = agent_os.get_app()

if __name__ == "__main__":
    """Run Helix AgentOS server."""
    print("\\n" + "="*60)
    print("🚀 Starting Helix AgentOS Server")
    print("="*60)
    print("📍 Local:     http://localhost:7777")
    print("📚 API Docs:  http://localhost:7777/docs")
    print("⚙️  Config:    http://localhost:7777/config")
    print("="*60 + "\\n")
    
    agent_os.serve(app="agentos_app:app", reload=True)
'''
        
        # Write to file with UTF-8 encoding
        output_path.write_text(app_code, encoding='utf-8')
        print(f"✓ Created AgentOS app at: {output_path}")
        print(f"  Run with: python {output_path.name}")
        
        return output_path
