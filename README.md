# Helix - AI-Powered Development Assistant

Helix is a multi-agent AI system powered by NVIDIA NIMs that provides intelligent code analysis, file operations, Git management, and web research capabilities through a VS Code extension.

## Features

- 🤖 **Multi-Agent System**: Specialized agents for code analysis, file operations, Git operations, and web research
- 🔍 **Semantic Code Search**: RAG-powered code understanding with ChromaDB
- 🛠️ **Git Integration**: Smart Git operations with authentication management
- 🌐 **Web Search**: Real-time web research capabilities
- 💬 **VS Code Extension**: Chat panel UI for seamless interaction
- 🔒 **Secure Code Execution**: Sandboxed environment for running code safely

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

## Quick Start

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
# Install the extension in VS Code
```

### Docker Compose

```bash
cd backend
docker-compose up
```

## Production Deployment

For production deployment to AWS EKS, see [DEPLOYMENT.md](DEPLOYMENT.md)

### Quick Deploy to AWS EKS:

1. Build and push images:
   ```bash
   ./scripts/build-and-push.sh latest
   ```

2. Configure secrets:
   ```bash
   kubectl create secret generic helix-secrets \
     --from-literal=nvidia-api-key='YOUR_KEY' \
     --from-literal=github-token='YOUR_TOKEN'
   ```

3. Deploy:
   ```bash
   ./scripts/deploy.sh helix-cluster us-west-2
   ```

## Configuration

### Environment Variables

**Backend:**
- `NVIDIA_API_KEY` - NVIDIA API key for model access
- `GITHUB_TOKEN` - GitHub personal access token
- `CHROMA_HOST` - ChromaDB host (default: localhost)

**VS Code Extension:**
- `HELIX_BACKEND_URL` - Backend URL (default: http://127.0.0.1:8001)

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

## Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete AWS EKS deployment guide
- [SETUP.md](SETUP.md) - Detailed setup instructions
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [NVIDIA_RESOURCES.md](NVIDIA_RESOURCES.md) - NVIDIA NIM resources

## Development

### Running Tests

```bash
cd backend
python test_dynamic.py
```

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

## Security

- ✅ Non-root users in all containers
- ✅ Health checks enabled
- ✅ Resource limits configured
- ✅ Sandboxed code execution
- ✅ Secrets management with Kubernetes secrets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Your License Here]

## Support

For issues, questions, or deployment help:
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- Review pod logs: `kubectl logs -f deployment/helix-backend`
- Test health: `curl http://your-backend/health`
