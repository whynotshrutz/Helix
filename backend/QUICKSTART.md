# Helix Quick Start - Autonomous AI Code Orchestrator

## ⚡ 30-Second Setup

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your keys:
#   NVIDIA_API_KEY=nvapi-xxx
#   TAVILY_API_KEY=tvly-xxx (optional)
#   EXA_API_KEY=exa-xxx (optional)
#   GITHUB_TOKEN=ghp-xxx (optional)

# 3. Start server
python run_server.py
```

Server runs on: `http://127.0.0.1:8000`

---

## 🎯 What Can Helix Do?

### 1. Code Analysis (No Setup Required)

```
User: "Analyze my codebase"

Agent: 
📊 CODEBASE ANALYSIS REPORT
==================================================

📁 Total Files: 15
📝 Total Lines: 2,450
🎯 Languages: Python (12), JavaScript (3)

⚠️ Issues Found (5):
  • TODO: Implement error handling (server.py:45)
  • Function too long: process_request (utils.py:120)
  • Missing docstring: calculate_metrics (analysis.py:78)

💡 Recommendations:
  ✓ Run pylint to enforce code quality
  ✓ Break down complex functions (>50 lines)
  ✓ Add docstrings for public APIs
```

### 2. Deep Security & Semantic Analysis

```
User: "Check for security vulnerabilities"

Agent:
🔍 SEMANTIC CODE ANALYSIS
============================================================

🚨 SECURITY VULNERABILITIES (2 found):
  [CRITICAL] Hardcoded API key
    File: config.py:15
    Fix: Use environment variables

  [HIGH] Command injection risk
    File: utils.py:42
    Fix: Use shell=False in subprocess.run()

🔄 Circular Dependencies (1 found):
  • module_a.py → module_b.py → module_a.py

📊 Complex Functions (3 found):
  • process_data() (complexity: 15, 85 lines)
```

### 3. Web Search for Documentation (Requires TAVILY_API_KEY or EXA_API_KEY)

```
User: "Search for FastAPI async database best practices"

Agent:
🔍 WEB SEARCH RESULTS
============================================================

1. FastAPI Async SQLAlchemy - Official Docs
   URL: https://fastapi.tiangolo.com/advanced/async-sql...
   Complete guide to async database operations with
   FastAPI. Includes session management, connection
   pooling, and dependency injection patterns...

2. Real-world FastAPI Async Patterns (2024)
   URL: https://testdriven.io/blog/fastapi-async-db/
   Production-ready patterns for async databases...
```

### 4. GitHub Automation (Requires GITHUB_TOKEN)

```
User: "Commit my changes and create a PR"

Agent:
1. Checking git status...
2. Creating commit...
   ✅ Commit created: a3f5b2c1
   Message: feat: add async database support

3. Creating feature branch...
   ✅ Branch 'feature/async-db' created

4. Pushing to GitHub...
   ✅ Successfully pushed to origin/feature/async-db

5. Creating pull request...
   ✅ PR #42 created!
   URL: https://github.com/user/repo/pull/42
```

---

## 🔑 API Keys (Optional but Recommended)

### NVIDIA NIM (Required)
```bash
# Get free key: https://build.nvidia.com/
NVIDIA_API_KEY=nvapi-xxx
```

### Tavily Search (Optional - for web search)
```bash
# Get key: https://tavily.com/
TAVILY_API_KEY=tvly-xxx
```

### Exa Search (Optional - alternative to Tavily)
```bash
# Get key: https://exa.ai/
EXA_API_KEY=exa-xxx
```

### GitHub (Optional - for automation)
```bash
# Generate: https://github.com/settings/tokens
# Permissions: repo, workflow
GITHUB_TOKEN=ghp_xxx
```

---

## 🚀 Example Workflows

### Workflow 1: Code Review & Fix

```
User: "Review my code for issues"

Agent: [Runs analysis]
Found 3 critical issues:
1. Hardcoded API key in config.py
2. Unused imports in utils.py
3. SQL injection risk in database.py

User: "Fix these issues"

Agent:
1. ✅ Fixed config.py (using env vars)
2. ✅ Cleaned up utils.py (removed unused)
3. ✅ Fixed database.py (using parameterized queries)

User: "Commit and push"

Agent:
✅ Committed: fix: resolve security vulnerabilities
✅ Pushed to origin/main
```

### Workflow 2: Feature Implementation

```
User: "Add authentication to my FastAPI app"

Agent:
1. [Analyzes existing code]
2. [Searches for best practices]
   🔍 Found: FastAPI JWT auth patterns

3. [Generates code]
   CREATE_FILE: auth.py
   CREATE_FILE: models/user.py
   UPDATE_FILE: main.py

4. [Writes files]
   ✅ Created auth.py (250 lines)
   ✅ Created models/user.py (80 lines)
   ✅ Updated main.py

User: "Create a PR for this"

Agent:
✅ Committed: feat: add JWT authentication
✅ Branch created: feature/auth
✅ PR #15 created
```

---

## 🛠️ Available Tools

The agent has 12 powerful tools:

### 📊 Analysis
- `analyze_codebase()` - Quick file scan, detect issues
- `analyze_semantics()` - Deep analysis (deps, security, complexity)

### 📝 File Operations
- `read_file()` - Read any file
- `write_file()` - Create/update files (with confirmation)
- `search_files()` - Search for patterns

### 🌐 Web Intelligence
- `search_web()` - Real-time docs, solutions, best practices

### 🔧 GitHub Operations
- `git_commit()` - Commit changes
- `git_push()` - Push to remote
- `create_branch()` - Create new branch
- `create_pull_request()` - Automated PR creation

### 💻 Code Testing
- `execute_code()` - Test snippets safely
- `explain_code()` - Generate documentation

---

## 🔒 Safety Features

### Confirmation Layer
The agent asks before:
- ✅ First file creation/overwrite (per session)
- ✅ File deletion
- ✅ Git push operations
- ✅ Branch deletion
- ✅ Creating pull requests

Example:
```
Agent: 📝 Create new file: server.py (350 bytes)
       Proceed? (yes/no): 

User: yes

Agent: ✅ File created (won't ask again this session)
```

### Safety Modes
- `NORMAL` (default): Ask for destructive ops
- `STRICT`: Ask for everything
- `PERMISSIVE`: Ask once per session
- `UNSAFE`: Never ask (not recommended)

---

## 📖 Full Documentation

- **Complete Guide**: `ORCHESTRATOR_GUIDE.md`
- **Dynamic Analysis**: `DYNAMIC_ANALYSIS.md`
- **API Reference**: See ORCHESTRATOR_GUIDE.md § API Reference

---

## 🎓 Pro Tips

1. **Be Conversational**: "Analyze code, fix issues, commit, and create PR"
2. **Trust the Agent**: It follows best practices from latest docs
3. **Review PRs**: Agent creates them, you review and merge
4. **Use Web Search**: Agent finds latest patterns automatically
5. **Chain Commands**: Agent executes multi-step workflows

---

## 🐛 Troubleshooting

### "Provider not available" error
```bash
pip install agno[tavily] agno[exa]
# Add API keys to .env
```

### "github_token_required" error
```bash
# Generate token: https://github.com/settings/tokens
# Add to .env: GITHUB_TOKEN=ghp_xxx
```

### Server won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process or change port in run_server.py
```

---

## 🚀 Next Steps

1. **Start Server**: `python run_server.py`
2. **Open VS Code**: Load your project
3. **Try Analysis**: Ask "Analyze my codebase"
4. **Enable Web Search**: Add TAVILY_API_KEY
5. **Enable GitHub**: Add GITHUB_TOKEN
6. **Go Autonomous**: "Analyze, fix, commit, push, create PR"

---

**Your AI Code Orchestrator is ready! 🎉**

Try: "Analyze my code for security issues and suggest fixes"
