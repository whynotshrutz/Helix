# Helix Backend

Production-ready backend for the Helix AI Code Assistant using FastMCP, Agno AI, NVIDIA NIM, and ChromaDB.

## Architecture

### Key Components

- **`server.py`** — FastAPI server with SSE streaming support for MCP-compatible communication
- **`agno_agent.py`** — Agno Agent with NVIDIA NIM model, session management, RAG, and tool orchestration
- **`tools.py`** — Code assistant tools (file reading, search, code execution, documentation)
- **`nim_client.py`** — Async NVIDIA NIM client for LLM inference and embeddings
- **`chroma_store.py`** — ChromaDB vector store for RAG
- **`rag_ingestion.py`** — Content ingestion pipeline for code and documentation

### Docker Services

- **`code-executor`** — Sandboxed code execution environment with resource limits
- **`backend`** — Main API server

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY and other settings
```

### 3. Run with Docker (Recommended)

```bash
docker-compose up -d
```

This starts:
- Backend API on `http://localhost:8000`
- Code executor on `http://localhost:8888`

### 4. Run Locally (Development)

```bash
# Start code executor (optional, will fallback to local if not available)
python docker/code-executor/executor.py &

# Start backend
python -m uvicorn helix.server:app --host 127.0.0.1 --port 8000 --reload
```

## Usage

### Ingest Workspace for RAG

```bash
python -m helix.rag_ingestion /path/to/your/workspace
```

### API Endpoints

#### POST /run

Run the agent with a prompt.

**Request:**
```json
{
  "prompt": "Explain this code",
  "user_id": "user123",
  "session_id": "session456",
  "mode": "chat",
  "stream": true
}
```

**Response (streaming):**
```
data: {"event": "run_content", "content": "Let me explain...", "run_id": "..."}
data: {"event": "tool_call_started", "content": "read_file", ...}
data: [DONE]
```

**Response (non-streaming):**
```json
{
  "content": "Response text",
  "run_id": "run_abc123"
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NVIDIA_API_KEY` | NVIDIA NIM API key | (required) |
| `NVIDIA_MODEL_ID` | Model ID | `meta/llama-3.1-nemotron-nano-8b-v1` |
| `NIM_BASE_URL` | NIM inference endpoint | `http://localhost:8001` |
| `NIM_EMBEDDING_URL` | NIM embedding endpoint | `http://localhost:8002` |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | `./tmp/chroma` |
| `CODE_EXECUTOR_URL` | Code executor service URL | `http://localhost:8888` |
| `FASTMCP_BIND_HOST` | Server bind address | `127.0.0.1` |
| `FASTMCP_BIND_PORT` | Server port | `8000` |

### Agent Configuration

Edit `agno_agent.py` to customize:
- Tool selection and configuration
- Session management settings
- Knowledge base parameters
- Memory and context settings

## Testing

```bash
# Run unit tests
pytest tests/test_tools.py -v

# Run integration tests (requires backend running)
pytest tests/test_integration.py -v

# Run all tests
pytest tests/ -v
```

## Security

### Code Execution Sandbox

The code executor runs in a Docker container with:
- Non-root user
- Resource limits (CPU, memory)
- Isolated filesystem
- Network restrictions (configurable)

For production, consider additional hardening:
- Use gVisor or Kata Containers for stronger isolation
- Implement rate limiting
- Add authentication and authorization
- Monitor resource usage

## Development

### Project Structure

```
backend/
├── src/helix/          # Source code
│   ├── server.py       # FastAPI server
│   ├── agno_agent.py   # Agent configuration
│   ├── tools.py        # Tool implementations
│   ├── nim_client.py   # NVIDIA NIM client
│   ├── chroma_store.py # Vector store
│   └── rag_ingestion.py # Content ingestion
├── docker/             # Docker configurations
│   └── code-executor/  # Sandbox executor
├── tests/              # Test suite
├── docker-compose.yml  # Docker orchestration
└── requirements.txt    # Python dependencies
```

### Adding New Tools

1. Implement tool function in `tools.py`
2. Register in `agno_agent.py` with `@tool` decorator
3. Add tests in `tests/test_tools.py`

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m uvicorn helix.server:app --log-level debug
```

## Troubleshooting

**Agent not available (503 error)**
- Check that `agno` is installed: `pip install agno`
- Verify `NVIDIA_API_KEY` is set

**Code executor timeout**
- Check Docker service is running: `docker ps`
- Verify `CODE_EXECUTOR_URL` is correct
- Falls back to local execution with warning

**ChromaDB errors**
- Ensure `CHROMA_PERSIST_DIR` is writable
- Check disk space

## Performance

### Recommended Resources

- **Development:** 4GB RAM, 2 CPU cores
- **Production:** 8GB+ RAM, 4+ CPU cores
- **Storage:** 10GB+ for ChromaDB vectors

### Optimization Tips

1. Use SSD storage for ChromaDB
2. Increase `num_history_runs` for better context
3. Batch RAG ingestion during off-peak hours
4. Enable caching for frequently accessed files
5. Use connection pooling for database

## License

See main project LICENSE file.
