"""
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
import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.nvidia import Nvidia
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS

# Load environment variables from .env file
load_dotenv()

# Setup database
db = SqliteDb(db_file="tmp/helix_agentos.db")

# Configure NVIDIA NIM model
model_id = "meta/llama-3.1-70b-instruct"
nvidia_api_key = os.getenv("NVIDIA_API_KEY", "YOUR_NVIDIA_API_KEY")

if nvidia_api_key == "YOUR_NVIDIA_API_KEY":
    print("⚠️  Warning: NVIDIA_API_KEY not set. Please set it as an environment variable.")
    print("   Example: export NVIDIA_API_KEY='your-api-key-here'")
    print("   The agents will not be able to generate responses without a valid API key.\n")

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
    print("\n" + "="*60)
    print("🚀 Starting Helix AgentOS Server")
    print("="*60)
    print("📍 Local:     http://localhost:7777")
    print("📚 API Docs:  http://localhost:7777/docs")
    print("⚙️  Config:    http://localhost:7777/config")
    print("="*60 + "\n")
    
    agent_os.serve(app="agentos_app:app", reload=True)
