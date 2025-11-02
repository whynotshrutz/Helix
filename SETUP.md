# Helix Setup Guide

Complete step-by-step guide to set up and run Helix.

## Prerequisites Checklist

- [ ] Python 3.11 or higher installed
- [ ] pip package manager
- [ ] Node.js 18+ and npm (for VS Code extension)
- [ ] Docker Desktop (optional but recommended)
- [ ] NVIDIA API Key from https://build.nvidia.com/
- [ ] Git (for version control)

## Installation Steps

### 1. Backend Setup (5 minutes)

#### Step 1.1: Navigate to backend directory

```bash
cd Helix/backend
```

#### Step 1.2: Install Python dependencies

```bash
pip install -r requirements.txt
```

Expected packages:
- agno (>=0.8.0)
- fastapi
- uvicorn
- httpx
- chromadb
- pydantic
- python-dotenv

#### Step 1.3: Configure environment

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env` file and add:

```ini
# Required
NVIDIA_API_KEY=nvapi-YOUR_KEY_HERE

# Optional (use defaults if running locally)
NVIDIA_MODEL_ID=meta/llama-3.1-nemotron-nano-8b-v1
NIM_BASE_URL=http://localhost:8001
NIM_EMBEDDING_URL=http://localhost:8002
CHROMA_PERSIST_DIR=./tmp/chroma
CODE_EXECUTOR_URL=http://localhost:8888
FASTMCP_BIND_HOST=127.0.0.1
FASTMCP_BIND_PORT=8000
```

#### Step 1.4: Verify installation

```bash
python start.py
```

This will:
- Check Python version
- Verify dependencies
- Validate environment configuration
- Offer to start the backend

### 2. Docker Setup (Optional, 3 minutes)

#### Step 2.1: Build Docker images

```bash
docker-compose build
```

#### Step 2.2: Start services

```bash
docker-compose up -d
```

This starts:
- **backend** on port 8000
- **code-executor** on port 8888

#### Step 2.3: Verify services

```bash
# Check containers are running
docker-compose ps

# Test backend health
curl http://localhost:8000/docs

# Test executor health
curl http://localhost:8888/health
```

### 3. VS Code Extension Setup (5 minutes)

#### Step 3.1: Navigate to extension directory

```bash
cd ../vscode-extension
```

#### Step 3.2: Install Node.js dependencies

```bash
npm install
```

#### Step 3.3: Build extension

```bash
npm run build
```

#### Step 3.4: Open in VS Code

```bash
code .
```

#### Step 3.5: Run extension

1. Press `F5` to open Extension Development Host
2. A new VS Code window opens with Helix extension loaded

#### Step 3.6: Test extension

In the new window:
1. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type "Helix: Chat"
3. Enter a test prompt: "Hello, can you help me?"
4. Check Output panel for response

### 4. RAG Setup (Optional, 10 minutes)

To enable code context awareness:

#### Step 4.1: Ingest your workspace

```bash
cd backend
python -m helix.rag_ingestion /path/to/your/project
```

Example:
```bash
python -m helix.rag_ingestion C:\Users\YourName\MyProjects\webapp
```

This will:
- Scan for code files (.py, .js, .ts, etc.)
- Chunk content into manageable pieces
- Generate embeddings via NVIDIA NIM
- Store vectors in ChromaDB

Progress will be displayed:
```
Processing files: 45/100
Chunks created: 234
Embeddings generated: 234
✅ Ingestion complete
```

## Verification Checklist

### Backend Verification

```bash
# 1. Check backend is running
curl http://localhost:8000/docs

# Expected: OpenAPI documentation page

# 2. Test non-streaming endpoint
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"Say hello\", \"stream\": false}"

# Expected: {"content": "...", "run_id": "..."}

# 3. Test streaming endpoint
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"Count to 3\", \"stream\": true}" \
  --no-buffer

# Expected: SSE events stream
```

### Docker Verification

```bash
# Check all services are healthy
docker-compose ps

# Expected:
# NAME              STATUS
# helix-backend     Up
# helix-executor    Up

# Check logs
docker-compose logs backend
docker-compose logs code-executor
```

### VS Code Extension Verification

1. **Chat Command**
   - Press `Ctrl+Shift+P`
   - Type "Helix: Chat"
   - Enter prompt
   - Check Output panel shows streaming response

2. **Inline Suggest Command**
   - Open a code file
   - Press `Ctrl+Shift+P`
   - Type "Helix: Inline Suggest"
   - Verify suggestion appears

## Troubleshooting

### Issue: "Agent not available (503)"

**Cause:** Agno SDK not installed or NVIDIA_API_KEY missing

**Solution:**
```bash
pip install agno
# Edit .env and add NVIDIA_API_KEY
```

### Issue: "Cannot connect to backend"

**Cause:** Backend not running or wrong URL

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/docs

# Check extension uses correct URL
# Edit vscode-extension/src/extension.ts
# Verify: const BACKEND_URL = 'http://127.0.0.1:8000';
```

### Issue: "Code executor timeout"

**Cause:** Docker executor not running

**Solution:**
```bash
# Check Docker is running
docker ps | grep executor

# Restart executor
docker-compose restart code-executor

# Or run executor locally
cd backend/docker/code-executor
python executor.py
```

### Issue: "ChromaDB errors"

**Cause:** Permissions or corrupted database

**Solution:**
```bash
# Check directory exists and is writable
ls -la backend/tmp/chroma

# Reset database
rm -rf backend/tmp/chroma
mkdir -p backend/tmp/chroma
```

### Issue: "Module not found" errors

**Cause:** Python path not set or dependencies missing

**Solution:**
```bash
# Install all dependencies
pip install -r backend/requirements.txt

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/Helix/backend/src"

# Or on Windows
set PYTHONPATH=%PYTHONPATH%;C:\Users\YourName\Helix\backend\src
```

## Testing Your Setup

### 1. Basic Test

```bash
cd backend
python -c "from helix.tools import file_reader_tool; print(file_reader_tool('README.md', '.'))"
```

Expected: File content displayed

### 2. Agent Test (requires Agno + API key)

```bash
cd backend
python -c "
from helix.agno_agent import create_agent
agent = create_agent()
print('Agent created successfully')
print(f'Model: {agent.model}')
print(f'Tools: {len(agent.tools)}')
"
```

Expected:
```
Agent created successfully
Model: <Nvidia model object>
Tools: 4
```

### 3. Integration Test

```bash
cd backend
pytest tests/test_tools.py -v
```

Expected: All tests pass

### 4. End-to-End Test

Start backend, then:

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"What tools do you have available?\", \"stream\": false}"
```

Expected: Response listing 4 tools (read_file, search_files, execute_code, explain_code)

## Next Steps

Once setup is complete:

1. **Customize Agent**
   - Edit `backend/src/helix/agno_agent.py`
   - Adjust instructions, tools, model parameters

2. **Add Custom Tools**
   - Add functions in `backend/src/helix/tools.py`
   - Register in `agno_agent.py`

3. **Ingest More Content**
   - Run RAG ingestion on your projects
   - Add documentation, API specs

4. **Deploy to Production**
   - Review security settings
   - Set up monitoring
   - Configure scaling

5. **Extend VS Code Extension**
   - Add more commands
   - Implement inline completions
   - Add UI panels

## Support Resources

- **Documentation:** See README.md files in each directory
- **Tests:** Run `pytest tests/` for examples
- **Logs:** Check `docker-compose logs` or terminal output
- **API Docs:** http://localhost:8000/docs (when running)

## Quick Reference

### Common Commands

```bash
# Start backend (local)
cd backend && python start.py

# Start backend (Docker)
cd backend && docker-compose up -d

# Stop backend (Docker)
docker-compose down

# View logs
docker-compose logs -f

# Run tests
pytest tests/ -v

# Ingest workspace
python -m helix.rag_ingestion /path/to/project

# Build extension
cd vscode-extension && npm run build
```

### Default Ports

| Service | Port | URL |
|---------|------|-----|
| Backend API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| Code Executor | 8888 | http://localhost:8888 |

### File Locations

| Item | Path |
|------|------|
| Backend source | `backend/src/helix/` |
| Configuration | `backend/.env` |
| ChromaDB data | `backend/tmp/chroma/` |
| Session DB | `backend/tmp/helix.db` |
| Extension source | `vscode-extension/src/` |
| Tests | `backend/tests/` |

## Success Criteria

Your setup is complete when:

- ✅ Backend starts without errors
- ✅ `/run` endpoint returns responses
- ✅ VS Code extension commands work
- ✅ Agent can use tools (read_file, search, etc.)
- ✅ Streaming works (SSE events appear)
- ✅ Code executor runs (or gracefully falls back)
- ✅ Tests pass

Congratulations! You now have a fully functional AI code assistant. 🎉
