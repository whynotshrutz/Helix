# Helix — Autonomous AI Code Orchestrator ✨

A **fully autonomous** AI coding assistant powered by Agno AI, NVIDIA NIM, and ChromaDB. Features real-time web search, GitHub automation, deep semantic analysis, and intelligent safety confirmations. Integrates seamlessly into VS Code.

## 🚀 What Makes Helix Unique?

### Fully Autonomous Operations
- **Proactive**: Suggests improvements without being asked
- **Chained Workflows**: Analyze → Fix → Commit → Push → Create PR
- **Context-Aware**: Learns from your codebase patterns
- **Safety-First**: Asks before destructive operations (first time only)

### 4 Core Autonomous Features

#### 1. 🔒 Interactive Confirmation Layer
- Smart session management with 4 safety modes
- Asks once per session for file operations
- Tracks confirmed operations across sessions
- Prevents accidental destructive changes

#### 2. 🔍 Enhanced Semantic Analysis  
- AST-based dependency graph construction
- Detects circular dependencies & unused imports
- Scans for 8 types of security vulnerabilities
- Calculates code complexity metrics
- Generates actionable architecture recommendations

#### 3. 🌐 Real-Time Web Intelligence
- Dual provider support: Tavily (general) + Exa (technical docs)
- Smart caching with 24-hour TTL
- Specialized searches: docs, errors, best practices
- Integrates latest API documentation automatically

#### 4. 🔧 Full GitHub Automation
- Complete git workflow (commit, push, branch, PR)
- GitHub REST API integration (issues, PRs, repos)
- Automated pull request creation with descriptions
- Branch management and status tracking

## 🎯 Core Capabilities

- 🤖 **Agno AI Agent** — 12 powerful tools with autonomous orchestration
- ⚡ **NVIDIA NIM** — High-performance LLM inference with `llama-3.1-nemotron-nano-8b-v1`
- 🔍 **RAG with ChromaDB** — Retrieval-augmented generation for code context
- 🐳 **Docker Sandbox** — Secure code execution with resource limits
- 💬 **Streaming Support** — Real-time SSE streaming to VS Code
- 📝 **Session Memory** — Persistent conversation history and context
- 🛠️ **Rich Toolset** — 12 tools including analysis, search, git, and more

## Architecture

```
┌─────────────────────────────────────────┐
│         VS Code Extension (MCP)         │
│  ┌────────────────────────────────────┐ │
│  │   Chat Interface + Inline Suggest  │ │
│  │        (SSE Streaming Client)      │ │
│  └────────────────────────────────────┘ │
└──────────────────┬──────────────────────┘
                   │ HTTP/SSE
┌──────────────────▼──────────────────────┐
│    FastAPI Backend (FastMCP Bridge)     │
│  ┌────────────────────────────────────┐ │
│  │      Agno Agent Orchestrator       │ │
│  │  • NVIDIA NIM Model                │ │
│  │  • Session Management              │ │
│  │  • Tool Execution                  │ │
│  │  • RAG Knowledge Search            │ │
│  └────────────────────────────────────┘ │
└─────────────────┬────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
┌─────▼─────┐        ┌────────▼────────┐
│  ChromaDB │        │ Docker Executor │
│  (Vectors)│        │   (Sandbox)     │
└───────────┘        └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for VS Code extension)
- Docker & Docker Compose
- NVIDIA API Key ([Get one here](https://build.nvidia.com/))

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Helix
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY

# Start with Docker (recommended)
docker-compose up -d

# OR start locally
python -m uvicorn helix.server:app --host 127.0.0.1 --port 8000
```

Backend will be available at `http://localhost:8000`

### 3. Ingest Workspace (Optional)

For better code suggestions, ingest your workspace:

```bash
python -m helix.rag_ingestion /path/to/your/project
```

### 4. VS Code Extension Setup

```bash
cd ../vscode-extension

# Install dependencies
npm install

# Build
npm run build

# Install extension in VS Code
# Open vscode-extension folder in VS Code
# Press F5 to run Extension Development Host
```

### 5. Test the Assistant

In VS Code Extension Development Host:

1. Press `Ctrl+Shift+P`
2. Type "Helix: Chat"
3. Enter your question

## Usage

### Chat Mode

Ask questions about your code:

```
> Explain the main function in server.py
> How do I add a new tool?
> Debug this error: [paste error]
```

### Inline Suggestions

Get code completions:

```python
# Type a comment or partial code
# Press Ctrl+Shift+P → "Helix: Inline Suggest"
```

### API Usage

```bash
# Non-streaming
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello Helix", "mode": "chat"}'

# Streaming
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain async/await", "stream": true}' \
  --no-buffer
```

## Configuration

### Backend Configuration

Edit `backend/.env`:

```bash
# Required
NVIDIA_API_KEY=nvapi-xxx

# Optional - Core Settings
NVIDIA_MODEL_ID=meta/llama-3.1-nemotron-nano-8b-v1
NIM_BASE_URL=http://localhost:8001
CHROMA_PERSIST_DIR=./tmp/chroma
CODE_EXECUTOR_URL=http://localhost:8888

# Optional - Autonomous Features
# Web Search (pick one or both)
TAVILY_API_KEY=tvly-xxx          # Get at https://tavily.com
EXA_API_KEY=exa-xxx              # Get at https://exa.ai

# GitHub Automation
GITHUB_TOKEN=ghp-xxx             # Personal access token from GitHub

# Safety Mode (default: normal)
HELIX_SAFETY_MODE=normal         # strict|normal|permissive|unsafe
```

### Autonomous Features

Helix now includes 14 tools for fully autonomous operation:

**📊 Code Analysis** (no config needed):
- `analyze_codebase()` - Quick scan
- `deep_analyze()` - Semantic analysis with AST, dependencies, vulnerabilities

**🌐 Web Intelligence** (requires API key):
- `search_web()` - Real-time documentation search via Tavily or Exa

**🔧 GitHub Automation** (git works without token, API features need token):
- `git_commit()`, `git_push()` - Git operations
- `create_branch()`, `list_branches()` - Branch management
- `create_pull_request()` - PR automation

**🔒 Safety**:
- `check_safety()` - Interactive confirmations for first-time/destructive operations

For detailed usage, see:
- `backend/QUICKSTART.md` - Quick examples
- `backend/ORCHESTRATOR_GUIDE.md` - Complete feature guide

### Agent Customization

Edit `backend/src/helix/agno_agent.py` to:
- Change model parameters
- Add/remove tools
- Adjust context window
- Configure memory settings

### VS Code Extension

Set environment variable before launching:

```bash
export HELIX_BACKEND_URL=http://localhost:8000
```

Or edit in `vscode-extension/src/extension.ts`

## Development

### Project Structure

```
Helix/
├── backend/
│   ├── src/helix/              # Python backend
│   │   ├── server.py           # FastAPI + SSE
│   │   ├── agno_agent.py       # Agent config
│   │   ├── tools.py            # Tool implementations
│   │   ├── nim_client.py       # NVIDIA NIM client
│   │   ├── chroma_store.py     # Vector store
│   │   └── rag_ingestion.py    # Content pipeline
│   ├── docker/                 # Docker configs
│   ├── tests/                  # Test suite
│   └── docker-compose.yml      # Orchestration
├── vscode-extension/
│   ├── src/extension.ts        # VS Code client
│   └── package.json            # Extension manifest
└── README.md                   # This file
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=helix --cov-report=html
```

### Debugging

**Backend:**
```bash
export LOG_LEVEL=DEBUG
python -m uvicorn helix.server:app --reload --log-level debug
```

**VS Code Extension:**
- Open `vscode-extension` in VS Code
- Press F5 (opens Extension Development Host)
- View → Output → Select "Helix"

## Advanced Topics

### Custom Tools

Add new tools in `backend/src/helix/tools.py`:

```python
from agno.tools import tool

@tool(name="my_custom_tool")
def my_tool(param: str) -> dict:
    """Tool description for LLM."""
    # Your implementation
    return {"result": "..."}
```

Register in `agno_agent.py`:
```python
tools = [read_file, search_files, execute_code, my_tool]
```

### RAG Optimization

```python
# Ingest specific file types
from helix.rag_ingestion import ContentIngester

ingester = ContentIngester()
await ingester.ingest_directory(
    "/path/to/project",
    extensions=[".py", ".js", ".md"]
)
```

### Session Management

Sessions are automatically tracked per `user_id` and `session_id`:

```bash
curl -X POST http://localhost:8000/run \
  -d '{"prompt": "...", "user_id": "alice", "session_id": "proj-1"}'
```

History is preserved across runs for the same session.

### Security Hardening

1. **Enable authentication:**
   - Add API key validation in `server.py`
   - Use JWT tokens for session management

2. **Harden code executor:**
   - Use gVisor runtime: `docker run --runtime=runsc`
   - Add network isolation
   - Implement rate limiting

3. **Data privacy:**
   - Encrypt ChromaDB storage
   - Use secure WebSocket (wss://)
   - Sanitize user inputs

## Deployment

### Docker Production

```bash
# Build images
docker-compose build

# Deploy with production config
docker-compose -f docker-compose.prod.yml up -d

# Scale executor workers
docker-compose up -d --scale code-executor=3
```

### Cloud Deployment

**AWS:**
- Use ECS/Fargate for containers
- Store vectors in S3 + DynamoDB
- Use Lambda for executor

**Azure:**
- Deploy to AKS
- Use CosmosDB for sessions
- Azure Container Instances for executor

**GCP:**
- Deploy to Cloud Run
- Use Firestore for sessions
- Use Cloud Functions for executor

## Troubleshooting

### Agent Not Available (503)

```bash
# Check Agno installation
pip show agno

# Verify API key
echo $NVIDIA_API_KEY

# Check logs
docker-compose logs backend
```

### Code Executor Timeout

```bash
# Check executor is running
docker ps | grep executor

# Test executor directly
curl http://localhost:8888/health

# Check logs
docker-compose logs code-executor
```

### ChromaDB Issues

```bash
# Verify permissions
ls -la backend/tmp/chroma

# Reset database
rm -rf backend/tmp/chroma
python -m helix.rag_ingestion .
```

## Performance Tuning

| Component | Setting | Impact |
|-----------|---------|--------|
| Agent | `num_history_runs=10` | More context, slower |
| ChromaDB | SSD storage | Faster retrieval |
| Executor | `cpus: '2.0'` | Parallel execution |
| Backend | `workers=4` | Handle more requests |

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## Roadmap

- [ ] Multi-file editing support
- [ ] Git integration (commits, diffs)
- [ ] Collaborative sessions
- [ ] Plugin marketplace
- [ ] Mobile/web interface
- [ ] Fine-tuned models

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [Agno AI](https://agno.com/) — Agent framework
- [NVIDIA NIM](https://build.nvidia.com/) — LLM inference
- [ChromaDB](https://www.trychroma.com/) — Vector database
- [FastAPI](https://fastapi.tiangolo.com/) — Backend framework

## Support

- 📖 [Documentation](backend/README.md)
- 🐛 [Report Issues](../../issues)
- 💬 [Discussions](../../discussions)
- 📧 Email: support@example.com
