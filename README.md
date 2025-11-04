# Helix - AI-Powered Development Assistant

> **Intelligent multi-agent AI system that performs tasks like GitHub Copilot, Cursor, and Windsurf**

Helix is an advanced AI development assistant powered by NVIDIA NIMs that provides intelligent code generation, analysis, file operations, Git management, and web research capabilities through a seamless VS Code extension.

## ✨ Key Features

- 🤖 **Multi-Agent System**: Specialized agents that **perform tasks** (not just respond)
  - **Code Analyst**: Generates complete code, analyzes quality, finds bugs, executes code
  - **File Operations**: Dynamic workspace scanning, file creation/editing, intelligent search
  - **Git Operations**: Smart Git management with automatic error resolution and retry logic
  - **Web Research**: Real-time web search and URL content fetching
  
- 🎯 **Task Performance**: Agents generate code, execute commands, and resolve errors automatically
- 🔍 **Dynamic Discovery**: Zero hardcoded paths - all workspace scanning is dynamic
- 🔧 **Auto Error Resolution**: Automatically detects, categorizes, and fixes errors (up to 3 retries)
- 🛠️ **Complete Git Integration**: Execute Git operations with intelligent error handling
- 🌐 **Web Intelligence**: Search multiple sources (DuckDuckGo, Tavily, Exa) and fetch URL content
- 💬 **VS Code Extension**: Intuitive chat panel UI for seamless interaction
- 🔒 **Secure Execution**: Sandboxed environment for running code safely
- 📊 **RAG-Powered**: Semantic code search with ChromaDB vector database

## Architecture

```
┌─────────────────────────────────────────────────┐
│              VS Code Extension                   │
│         (TypeScript Chat Panel UI)               │
└────────────────┬────────────────────────────────┘
                 │ HTTP/SSE
┌────────────────▼────────────────────────────────┐
│          FastAPI Backend (Port 8001)             │
│  ┌────────────────────────────────────────────┐ │
│  │      Multi-Agent Orchestrator              │ │
│  ├────────────────────────────────────────────┤ │
│  │  • Code Analyst    • File Operations       │ │
│  │  • Git Operations  • Web Research          │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
         │              │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │ NVIDIA  │   │ ChromaDB │   │ GitHub  │
    │  NIMs   │   │   RAG    │   │   API   │
    └─────────┘   └──────────┘   └─────────┘
```

## 🤖 How Helix Works (vs Traditional Chatbots)

| Traditional Chatbot | ✅ Helix AI Agents |
|---------------------|-------------------|
| "Here's how to write a function..." | **Writes complete working code** |
| "You should run git push..." | **Executes git push command** |
| "Files are typically in folders..." | **Scans and lists actual 77 files** |
| "To fix errors, try..." | **Auto-resolves errors with retry** |
| "You can create a file..." | **Creates actual file in workspace** |

### Example Interactions

**Code Generation:**
```
You: "create a bubble sort function"
Helix: [Generates complete Python function with type hints, docstring, error handling, and optimization]
```

**Workspace Exploration:**
```
You: "what files are in this project?"
Helix: [Scans workspace dynamically]
       "Found 77 files in 12 directories across 7 languages:
        - Python: 38 files
        - Markdown: 14 files
        - YAML: 6 files..."
```

**Git Operations:**
```
You: "push to GitHub"
Helix: [Executes] git add . → git commit → git push
       [If error] Auto-resolves merge conflicts and retries
       "✅ Successfully pushed to main"
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Required
export NVIDIA_API_KEY="your-nvidia-api-key"

# Optional (for GitHub operations)
export GITHUB_TOKEN="your-github-token"
```

### Local Development

**Backend:**

```bash
cd backend
pip install -r requirements.txt
python run_server.py
```

**VS Code Extension:**

```bash
cd vscode-extension
npm install
npm run build
# Install the extension: code --install-extension helix-mcp-client-1.0.0.vsix
```

### Docker Compose

```bash
cd backend
docker-compose up
```

---

## 🎯 Agent Capabilities

### 1. Code Analyst Agent
**Generates code like GitHub Copilot**

- ✅ Write complete, working code in any language
- ✅ Create functions, classes, modules, entire files
- ✅ Implement algorithms and data structures
- ✅ Fix bugs and improve existing code
- ✅ Add features to existing codebases
- ✅ Analyze code for vulnerabilities
- ✅ Modernize outdated patterns
- ✅ Execute code in sandbox environment

**Example Queries:**
- "create a FastAPI endpoint for user authentication"
- "analyze my codebase for security issues"
- "modernize this Python 2 code to Python 3"
- "implement binary search algorithm"

### 2. File Operations Agent
**Dynamic workspace exploration (NO hardcoding)**

- ✅ Scan entire workspace dynamically
- ✅ List directories non-recursively
- ✅ Find files by pattern (*.py, test_*, etc.)
- ✅ Read file contents
- ✅ Create and update files
- ✅ Search for text across all files

**Example Queries:**
- "what's the project structure?"
- "find all test files"
- "create a config.json file"
- "search for TODO comments"

### 3. Git Operations Agent
**Executes Git commands with auto error resolution**

- ✅ Check repository status
- ✅ Commit changes
- ✅ Push to remote (with auto-retry)
- ✅ Create and switch branches
- ✅ Resolve merge conflicts automatically
- ✅ Handle authentication errors
- ✅ Retry failed operations (up to 3 times)

**Example Queries:**
- "commit my changes with message 'fix bug'"
- "push to GitHub" (auto-resolves errors)
- "create a new branch called feature-x"
- "resolve merge conflicts"

### 4. Web Research Agent
**Searches web and fetches URLs**

- ✅ Search multiple sources (DuckDuckGo, Tavily, Exa)
- ✅ Fetch content from URLs
- ✅ Find documentation and best practices
- ✅ Research technical topics
- ✅ Compare technologies

**Example Queries:**
- "find React best practices"
- "fetch content from https://example.com/guide"
- "compare MongoDB vs PostgreSQL"
- "what's new in Python 3.12?"

---

## 🚢 Production Deployment (AWS EKS)

### Quick Deploy Steps

**1. Build and Push Images:**

```bash
chmod +x scripts/build-and-push.sh
./scripts/build-and-push.sh latest
```

**2. Create Kubernetes Secrets:**

```bash
kubectl create secret generic helix-secrets \
  --from-literal=nvidia-api-key='YOUR_NVIDIA_API_KEY' \
  --from-literal=github-token='YOUR_GITHUB_TOKEN'
```

**3. Deploy to EKS:**

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh helix-cluster us-east-1
```

**4. Get Backend URL:**

```bash
kubectl get service helix-backend-service \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

**5. Configure VS Code Extension:**

Set backend URL in VS Code Settings or via environment:

```bash
export HELIX_BACKEND_URL="http://your-load-balancer-url.com"
code --install-extension vscode-extension/helix-mcp-client-1.0.0.vsix
```

### Architecture (AWS EKS)

```text
┌─────────────────────────────────────────────────────┐
│                   AWS EKS Cluster                    │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│
│  │   Backend    │  │   Sandbox    │  │    Code    ││
│  │   (3 pods)   │  │   Worker     │  │  Executor  ││
│  │   Port 8001  │  │   (2 pods)   │  │  (2 pods)  ││
│  └──────┬───────┘  └──────────────┘  └────────────┘│
│         │                                            │
│  ┌──────▼─────────────────────────────────────────┐│
│  │         AWS Load Balancer Service              ││
│  └────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
              │
      ┌───────▼────────┐
      │  VS Code Users │
      └────────────────┘
```

## Configuration

### Environment Variables

**Backend:**
- `NVIDIA_API_KEY` - NVIDIA API key for model access
- `GITHUB_TOKEN` - GitHub personal access token
- `CHROMA_HOST` - ChromaDB host (default: localhost)

**VS Code Extension:**
- `HELIX_BACKEND_URL` - Backend URL (default: http://0.0.0.0:8001)

### VS Code Extension Setup

Set the backend URL:
```bash
# Linux/Mac
export HELIX_BACKEND_URL=http://your-backend-url.com
code .

# Windows
$env:HELIX_BACKEND_URL="http://your-backend-url.com"
code .
```

## Project Structure

```
Helix/
├── backend/
│   ├── src/helix/          # Main application code
│   │   ├── multi_agent_system.py
│   │   ├── server.py
│   │   ├── tools.py
│   │   └── ...
│   ├── docker/
│   │   └── code-executor/  # Sandboxed code execution
│   ├── sandbox_worker/     # Sandbox worker service
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── vscode-extension/
│   ├── src/
│   │   ├── extension.ts
│   │   └── chatPanel.ts
│   └── package.json
├── k8s/                    # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── secrets.yaml
│   └── ingress.yaml
├── scripts/                # Deployment scripts
│   ├── build-and-push.sh
│   ├── deploy.sh
│   └── rollback.sh
└── DEPLOYMENT.md           # Detailed deployment guide
```

---

## 🔧 Development

### Building Docker Images

```bash
# Backend
cd backend
docker build -t helix-backend .

# Code Executor
cd backend/docker/code-executor
docker build -t helix-code-executor .

# Sandbox Worker
cd backend/sandbox_worker
docker build -t helix-sandbox-worker .
```

### Building VS Code Extension

```bash
cd vscode-extension
npm install
npm run build
vsce package
```

Output: `helix-mcp-client-1.0.0.vsix`

---

## 🔒 Security Features

- ✅ Non-root users in all containers
- ✅ Health checks enabled
- ✅ Resource limits configured
- ✅ Sandboxed code execution environment
- ✅ Secrets management with Kubernetes secrets
- ✅ Automatic error detection and resolution
- ✅ Secure Git credential management

---

## 📝 Configuration Reference

### Environment Variables

**Required:**
- `NVIDIA_API_KEY` - Your NVIDIA API key ([Get it here](https://build.nvidia.com))

**Optional:**
- `GITHUB_TOKEN` - GitHub personal access token (for private repos)
- `NVIDIA_MODEL_ID` - Model ID (default: nvidia/llama-3_1-nemotron-nano-8b-v1)
- `NVIDIA_BASE_URL` - NVIDIA API URL (default: https://integrate.api.nvidia.com/v1)
- `CHROMA_HOST` - ChromaDB host (default: localhost)
- `WORKSPACE_DIR` - Workspace directory (default: current directory)

### VS Code Extension Settings

Open Settings (Ctrl+,) and search for "Helix":

- **Helix: Backend Url** - Backend server URL
- Or set via environment: `export HELIX_BACKEND_URL="http://your-url.com"`

---

## 🚀 What Makes Helix Different

### Traditional AI Assistants
- Provide suggestions and explanations
- User must execute commands manually
- Static responses without context
- No error handling or retry logic
- Hardcoded assumptions about project structure

### ✅ Helix AI Agents
- **Perform actual tasks** (generate code, execute commands, create files)
- **Auto-execute** Git operations with error resolution
- **Dynamic discovery** of workspace structure
- **Automatic error resolution** with retry logic (up to 3 attempts)
- **Context-aware** actions based on your actual project
- **Multi-agent orchestration** for complex workflows

---

## 📊 System Requirements

**Backend:**
- Python 3.9+
- 4GB RAM minimum
- NVIDIA API key
- (Optional) GitHub token

**VS Code Extension:**
- VS Code 1.80.0+
- Node.js 16+ (for development)

**Production (AWS EKS):**
- EKS cluster with 2+ nodes
- g5.xlarge or g6e.xlarge instances recommended
- AWS Load Balancer Controller
- kubectl configured

---

## 🐛 Troubleshooting

### Backend Not Starting
```bash
# Check Python version
python --version  # Should be 3.9+

# Install dependencies
cd backend
pip install -r requirements.txt

# Check API key
echo $NVIDIA_API_KEY
```

### Extension Can't Connect
```bash
# Verify backend is running
curl http://localhost:8001/health

# Check VS Code settings
# Settings > Helix: Backend Url should match your backend URL
```

### Git Operations Failing
```bash
# Set GitHub token
export GITHUB_TOKEN="your-github-token"

# Verify Git credentials
git config --global user.name
git config --global user.email
```

### Deployment Issues
```bash
# Check pod status
kubectl get pods

# View logs
kubectl logs -f deployment/helix-backend

# Check service
kubectl get service helix-backend-service

# Verify secrets
kubectl get secrets helix-secrets
```

---

## 📚 Learn More

- **Agent System**: See `backend/src/helix/multi_agent_system.py`
- **Workspace Scanner**: See `backend/src/helix/workspace_scanner.py`
- **Error Resolver**: See `backend/src/helix/auto_error_resolver.py`
- **Tools**: See `backend/src/helix/tools.py`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 💡 Support

**Issues or Questions?**
- 📖 Check this README first
- 🐛 Open an issue on GitHub
- 📧 Contact the development team

**Quick Health Checks:**
```bash
# Backend health
curl http://your-backend-url/health

# Pod logs (production)
kubectl logs -f deployment/helix-backend

# Extension logs
# Open VS Code Developer Tools: Help > Toggle Developer Tools
```

---

**Built with ❤️ using NVIDIA NIMs, FastAPI, and VS Code Extension API**
