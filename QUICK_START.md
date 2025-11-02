# Helix Quick Start Guide

## ✅ Current Status

- ✅ Backend running on http://127.0.0.1:8000
- ✅ VS Code extension built successfully
- ✅ All dependencies installed

## 🚀 Test the Extension Now

### Step 1: Open Extension in VS Code

In the current terminal:

```powershell
# Make sure you're in the extension directory
cd C:\Users\sriha\Hackathon\Helix\vscode-extension

# Open in VS Code
code .
```

### Step 2: Launch Extension Development Host

1. Press `F5` in VS Code
2. A new VS Code window will open with the extension loaded
3. You'll see "[Extension Development Host]" in the title

### Step 3: Test the Chat Command

In the Extension Development Host window:

1. Press `Ctrl+Shift+P` to open command palette
2. Type "Helix: Chat"
3. Enter a prompt, for example:
   - "What tools do you have available?"
   - "Explain what an async function is"
   - "Help me understand Python decorators"
4. Check the "Helix Output" panel for the response

### Step 4: Test Inline Suggestions

In the Extension Development Host window:

1. Create a new file or open an existing code file
2. Type a partial line of code
3. Press `Ctrl+Shift+P` and select "Helix: Inline Suggest"
4. View the suggestion in a quick pick menu

## 🔧 Troubleshooting

### Backend Not Responding

Check if backend is still running:

```powershell
# Test the API
curl http://localhost:8000/docs

# If not running, restart it
cd C:\Users\sriha\Hackathon\Helix\backend
$env:PYTHONPATH="$pwd\src"
python -m uvicorn helix.server:app --host 127.0.0.1 --port 8000 --reload
```

### Extension Not Loading

1. Check the "Debug Console" in VS Code for errors
2. Verify `out/extension.js` exists in the extension folder
3. Try rebuilding: `npm run build`

### "Cannot find module" Error

Make sure you ran `npm install` in the extension directory.

## 📝 Test Examples

### Basic Chat Tests

```
Prompt: "Hello, can you introduce yourself?"
Expected: Agent responds with its capabilities

Prompt: "What tools do you have?"
Expected: Lists 4 tools (read_file, search_files, execute_code, explain_code)

Prompt: "Read the README.md file"
Expected: Agent uses read_file tool to fetch content
```

### Code Execution Tests

```
Prompt: "Execute this Python code: print('Hello from Helix!')"
Expected: Agent uses execute_code tool (may warn about Docker fallback)
```

### Documentation Tests

```
Prompt: "Explain what a Python decorator is"
Expected: Agent provides explanation using doc_helper tool
```

## 🎯 Next Steps After Testing

1. **Add More Tools**: Edit `backend/src/helix/tools.py`
2. **Customize Agent**: Edit `backend/src/helix/agno_agent.py`
3. **Enable RAG**: Ingest your codebase:
   ```powershell
   cd backend
   python -m helix.rag_ingestion "C:\path\to\your\project"
   ```
4. **Deploy**: See README.md for Docker and cloud deployment options

## 📊 Monitoring

### View Backend Logs

The backend terminal shows:
- Incoming requests
- Tool executions
- Agent reasoning steps
- Errors and warnings

### View Extension Logs

In the Extension Development Host:
- Open "View" → "Output"
- Select "Helix Output" from the dropdown
- See real-time streaming responses

## 🔐 Security Notes

- Backend is currently running in local development mode
- Code executor uses local fallback (not sandboxed)
- For production, use Docker: `docker-compose up -d`

## ✨ Success Indicators

You'll know it's working when:

1. ✅ Backend shows "Application startup complete"
2. ✅ Extension loads without errors in Debug Console
3. ✅ Chat command streams responses to Output panel
4. ✅ Agent can use tools (read files, execute code, etc.)

---

**Need help?** Check the detailed documentation:
- Main docs: `README.md`
- Setup guide: `SETUP.md`
- Backend API: http://localhost:8000/docs
