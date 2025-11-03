# Helix AI Assistant - VS Code Extension

AI-powered code assistant with multi-agent system, Git operations, and web research capabilities using NVIDIA NIMs.

## Features

🤖 **Multi-Agent AI System**
- Code analysis and generation
- File operations and workspace management
- Git operations with smart commit messages
- Real-time web research

💬 **Chat Interface**
- Interactive chat panel in VS Code sidebar
- File attachment support (drag & drop)
- Syntax-highlighted code responses
- Streaming responses for real-time feedback

⚡ **Inline Completions**
- AI-powered code suggestions as you type
- Context-aware completions
- Fast, non-intrusive suggestions

## Installation & Configuration

### Backend URL Setup

Configure the backend server URL (choose one method):

**Method 1: VS Code Settings (Recommended)**
1. Open Settings (Ctrl+,)
2. Search for "Helix"
3. Set "Helix: Backend Url" to your server

Or add to `settings.json`:
```json
{
  "helix.backendUrl": "http://your-backend-server.com"
}
```

**Method 2: Environment Variable**
```bash
# Linux/Mac
export HELIX_BACKEND_URL=http://your-backend-server.com

# Windows
set HELIX_BACKEND_URL=http://your-backend-server.com
```

**Default:** `http://127.0.0.1:8001` (local development)

## Usage

1. Click Helix AI icon in Activity Bar (left sidebar)
2. Type your question in the chat
3. Attach files with 📎 button or drag & drop
4. Get AI-powered responses!

## Requirements

- VS Code 1.70.0+
- Helix backend server running

## Backend Setup

**Local Development:**
```bash
cd backend
pip install -r requirements.txt
python run_server.py
```

**Production:** See [DEPLOYMENT.md](https://github.com/whynotshrutz/Helix/blob/main/DEPLOYMENT.md)

## Development

```bash
npm install
npm run build
# Package: vsce package
```

## License

MIT
