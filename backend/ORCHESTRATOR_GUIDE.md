# Helix AI Code Orchestrator - Complete Feature Guide

## 🚀 Overview

Helix is now a fully autonomous AI Code Orchestrator powered by Agno and NVIDIA NIM, with capabilities spanning:

1. **Interactive Confirmation Layer** - Safe operations with user consent
2. **Enhanced Semantic Analysis** - Deep code understanding (dependencies, vulnerabilities, complexity)
3. **Web Search Integration** - Real-time documentation retrieval (Tavily/Exa)
4. **GitHub Automation** - Full workflow automation (commit, push, branch, PR)

---

## 1️⃣ Interactive Confirmation Layer

### Overview
Safety-first approach that asks users before destructive operations, with smart session management.

### Features
- **Safety Modes**:
  - `STRICT`: Ask for every operation
  - `NORMAL`: Ask only for destructive ops (delete, overwrite) ✅ **DEFAULT**
  - `PERMISSIVE`: Ask only once per session
  - `UNSAFE`: Never ask (dangerous!)

- **Tracked Operations**:
  - File creation (first time)
  - File overwrite
  - File deletion
  - Git push
  - Branch deletion
  - PR creation

### Usage

```python
from helix.safety_manager import get_safety_manager, SafetyMode

# Get safety manager
safety = get_safety_manager(mode=SafetyMode.NORMAL)

# Check if confirmation needed
needs_confirm, prompt = safety.needs_confirmation(
    operation=OperationType.UPDATE,
    target="important_file.py",
    details="Overwriting existing file"
)

if needs_confirm:
    if ask_user_confirmation(prompt):
        safety.confirm_operation(OperationType.UPDATE, "important_file.py")
        # Perform operation
```

### Agent Integration
The agent automatically uses the safety manager for file operations:

```
User: "Create a new server.py file"
Agent: 📝 Create new file: server.py
       Proceed? (yes/no): 

User: "yes"
Agent: ✅ File created successfully (only asked once per session)
```

---

## 2️⃣ Enhanced Semantic Analysis

### Overview
Deep code analysis using AST parsing, dependency graphs, and vulnerability scanning.

### Features

#### 📊 Dependency Analysis
- Build complete dependency graph
- Detect circular dependencies
- Find unused imports
- Identify missing dependencies

#### 🔒 Security Scanning
- Pattern-based vulnerability detection
- Detects:
  - `eval()` / `exec()` usage (Critical)
  - Pickle deserialization (High)
  - Shell injection (`shell=True`)
  - Hardcoded credentials
  - SQL injection patterns
  - XSS vulnerabilities
  
#### 📈 Complexity Metrics
- Cyclomatic complexity per function
- Lines of code per function
- Parameter count
- Docstring coverage

### Usage

#### Via Agent Tool
```
User: "Analyze my codebase for security issues"

Agent: [Uses analyze_semantics() tool]

🔍 SEMANTIC CODE ANALYSIS
============================================================

📊 Summary:
  Files analyzed: 15
  Total imports: 48
  Total functions: 23
  🔴 Vulnerabilities: 3
  🔄 Circular dependencies: 1
  🧹 Unused imports: 7
  📊 Complex functions: 2

🚨 SECURITY VULNERABILITIES (3 found):
  [CRITICAL] Hardcoded API key
    File: src/config.py:12
    Fix: Use environment variables or secure credential storage

  [HIGH] Command injection risk
    File: src/utils.py:45
    Fix: Use shell=False and pass arguments as a list
```

#### Direct Python Usage
```python
from helix.semantic_analyzer import analyze_codebase_semantics

# Analyze Python files
result = analyze_codebase_semantics(
    base_dir="./src",
    file_patterns=["**/*.py"]
)

# Access results
print(f"Vulnerabilities: {result['summary']['vulnerabilities_found']}")
print(f"Circular deps: {result['circular_dependencies']}")
print(f"Complex functions: {result['complex_functions']}")
```

### Detected Patterns

| Pattern | Severity | Description |
|---------|----------|-------------|
| `eval()` | Critical | Arbitrary code execution |
| `exec()` | Critical | Arbitrary code execution |
| `pickle.loads()` | High | Unsafe deserialization |
| `shell=True` | High | Command injection risk |
| `password = "..."` | Critical | Hardcoded credentials |
| `api_key = "..."` | Critical | Hardcoded API key |
| `.innerHTML =` | Medium | XSS vulnerability (JS) |
| SQL string concat | High | SQL injection risk |

---

## 3️⃣ Web Search Integration (Tavily & Exa)

### Overview
Real-time web search for documentation, solutions, and best practices using Tavily and Exa APIs.

### Features
- **Tavily**: Best for general search, error solutions, Stack Overflow
- **Exa**: Optimized for technical docs, semantic search
- **Smart routing**: Auto-selects best provider based on search type
- **Caching**: 24-hour TTL to avoid duplicate API calls
- **ChromaDB integration**: Cache results in vector database

### Setup

#### Install Dependencies
```bash
pip install agno[tavily] agno[exa]
```

#### Configure API Keys
```bash
# .env file
TAVILY_API_KEY=your_tavily_key_here
EXA_API_KEY=your_exa_key_here
```

Get API keys:
- Tavily: https://tavily.com/
- Exa: https://exa.ai/

### Usage

#### Via Agent Tool
```
User: "Search for FastAPI async database best practices"

Agent: [Uses search_web() tool]

🔍 WEB SEARCH RESULTS: FastAPI async database best practices
============================================================

1. FastAPI with Async SQLAlchemy - Official Docs
   URL: https://fastapi.tiangolo.com/advanced/async-sql-databases/
   Learn how to use async SQLAlchemy with FastAPI for
   high-performance database operations. Includes session
   management and dependency injection patterns...

2. Async Database Best Practices 2024
   URL: https://realpython.com/fastapi-async-database/
   Complete guide to async database patterns in FastAPI.
   Covers connection pooling, transaction management, and
   performance optimization techniques...
```

#### Direct Python Usage
```python
from helix.web_search import get_search_manager

# Initialize manager
search = get_search_manager()

# Search for documentation
result = search.search_documentation(
    technology="FastAPI",
    topic="async database",
    max_results=3
)

# Search for error solution
result = search.search_error_solution(
    error_message="ModuleNotFoundError: No module named 'fastapi'",
    context="Python FastAPI",
    max_results=3
)

# Search for best practices
result = search.search_best_practices(
    technology="React",
    area="security",
    max_results=3
)
```

### Search Types

| Type | Use Case | Recommended Provider |
|------|----------|---------------------|
| `docs` | Technical documentation | Exa (semantic) |
| `code` | Code examples | Exa |
| `error` | Error solutions | Tavily (Stack Overflow) |
| `general` | General search | Tavily |

### Caching
- Results cached in `./tmp/search_cache/`
- Cache TTL: 24 hours (configurable)
- Clear cache: `search.clear_cache()`

---

## 4️⃣ GitHub Automation

### Overview
Full GitHub workflow automation using Git commands and GitHub REST API.

### Features

#### 🌿 Branch Management
- Create branches
- Switch branches
- Delete branches
- List branches

#### 💾 Commit Operations
- Stage files
- Create commits
- Amend commits
- View commit history

#### 🚀 Remote Operations
- Push to remote
- Pull from remote
- Fetch updates
- Force push (with safety)

#### 🔀 Pull Requests
- Create PRs via GitHub API
- List PRs
- Get PR details
- Draft PR support

#### 📋 Issue Management
- Create issues
- Add labels
- Get issue details

### Setup

#### Configure GitHub Token
```bash
# .env file
GITHUB_TOKEN=ghp_your_personal_access_token_here
```

Get token: https://github.com/settings/tokens
- Permissions needed: `repo`, `workflow`

### Usage

#### Via Agent Tools

**Commit Changes**
```
User: "Commit my changes with message 'feat: add user authentication'"

Agent: [Uses git_commit() tool]
✅ Commit created: a3f5b2c1
   Message: feat: add user authentication
```

**Push to Remote**
```
User: "Push my changes to GitHub"

Agent: [Uses git_push() tool]
✅ Successfully pushed to origin/main
```

**Create Branch**
```
User: "Create a new branch called feature/api-refactor"

Agent: [Uses create_branch() tool]
✅ Branch 'feature/api-refactor' created and checked out
```

**Create Pull Request**
```
User: "Create a PR to merge feature/api-refactor into main"

Agent: [Uses create_pull_request() tool]
✅ Pull request created!
   #42: Refactor API endpoints for better performance
   URL: https://github.com/user/repo/pull/42
```

#### Direct Python Usage

```python
from helix.github_orchestrator import get_github_orchestrator

# Initialize orchestrator
gh = get_github_orchestrator()

# Check status
status = gh.git_status()
print(f"Current branch: {status['current_branch']}")
print(f"Modified files: {status['modified']}")

# Commit changes
result = gh.git_commit(
    message="feat: add new feature",
    add_all=True
)

# Push to remote
result = gh.git_push(remote="origin", branch="main")

# Create branch
result = gh.create_branch(
    branch_name="feature/new-feature",
    checkout=True
)

# Create PR
result = gh.create_pull_request(
    owner="username",
    repo="repository",
    title="Add new feature",
    head="feature/new-feature",
    base="main",
    body="This PR adds...",
    draft=False
)

# List PRs
result = gh.list_pull_requests(
    owner="username",
    repo="repository",
    state="open",
    limit=10
)

# Create issue
result = gh.create_issue(
    owner="username",
    repo="repository",
    title="Bug: Something broken",
    body="Description of the bug...",
    labels=["bug", "high-priority"]
)
```

### Git Operations Reference

#### Status & Info
```python
gh.git_status()  # Get working tree status
gh.get_repository_info(owner, repo)  # GitHub repo info
```

#### Branching
```python
gh.create_branch(name, checkout=True)
gh.switch_branch(name)
gh.delete_branch(name, force=False)
```

#### Committing
```python
gh.git_add(["file1.py", "file2.py"])
gh.git_add(["-A"])  # Add all
gh.git_commit(message, add_all=False)
```

#### Remote Operations
```python
gh.git_push(remote="origin", branch="main", force=False)
gh.git_pull(remote="origin", branch="main")
```

#### GitHub API
```python
gh.create_pull_request(owner, repo, title, head, base, body, draft)
gh.list_pull_requests(owner, repo, state="open", limit=10)
gh.create_issue(owner, repo, title, body, labels)
```

---

## 🎯 Complete Workflows

### Workflow 1: Analyze & Fix Security Issues

```
User: "Analyze my code for security vulnerabilities"

Agent:
1. [Uses analyze_semantics()]
   🚨 Found 2 CRITICAL vulnerabilities
   
2. [Explains issues]
   - Hardcoded API key in config.py:15
   - eval() usage in parser.py:42

3. [Suggests fixes with code examples]
   "Replace hardcoded keys with environment variables..."

4. [Offers to fix]
   "Would you like me to fix these issues and commit the changes?"

User: "Yes, fix and commit"

Agent:
5. [Fixes files using write_file()]
6. [Uses git_commit("fix: remove hardcoded credentials")]
   ✅ Commit created: f8d3a1b2
   
7. [Suggests next step]
   "Would you like me to push these changes to GitHub?"
```

### Workflow 2: Implement Feature with Best Practices

```
User: "Add async database support to my FastAPI app"

Agent:
1. [Uses analyze_codebase()]
   📊 Detected: FastAPI project, SQLAlchemy already used
   
2. [Uses search_web("FastAPI async SQLAlchemy", "docs")]
   🔍 Found official docs and best practices
   
3. [Generates code following patterns]
   CREATE_FILE: database.py
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
   # ... (complete implementation)
   ```

4. [Uses write_file() to create files]
   ✅ Created database.py
   ✅ Updated main.py
   
5. [Offers to commit and create PR]
   "Code is ready. Would you like me to:
    1. Commit changes
    2. Create feature branch
    3. Push to GitHub
    4. Create pull request?"

User: "Yes, do all of that"

Agent:
6. [Uses git_commit("feat: add async database support")]
7. [Uses create_branch("feature/async-db")]
8. [Uses git_push()]
9. [Uses create_pull_request()]
   ✅ PR #15 created: https://github.com/user/repo/pull/15
```

### Workflow 3: Debug & Fix Error

```
User: "I'm getting 'Connection refused' error when starting the server"

Agent:
1. [Uses read_file("server.py")]
   📄 Read server configuration
   
2. [Uses search_web("FastAPI connection refused error", "error")]
   🔍 Found common solutions:
   - Check if port is already in use
   - Verify host binding (0.0.0.0 vs 127.0.0.1)
   
3. [Identifies issue in code]
   "I see the issue: server is binding to 127.0.0.1, which doesn't
    allow external connections. Should use 0.0.0.0"
   
4. [Fixes the code]
   [Uses write_file() to update server.py]
   ✅ Updated server.py - Changed host to 0.0.0.0
   
5. [Uses git_commit("fix: bind server to 0.0.0.0 for external access")]
   ✅ Committed fix
   
6. "Try running the server now. The error should be resolved."
```

---

## 📚 API Reference

### Safety Manager

```python
from helix.safety_manager import (
    get_safety_manager,
    SafetyMode,
    OperationType,
    ask_user_confirmation
)

# Initialize
safety = get_safety_manager(
    mode=SafetyMode.NORMAL,
    session_file="./tmp/helix_safety_session.json"
)

# Check if confirmation needed
needs_confirm, prompt = safety.needs_confirmation(
    operation=OperationType.UPDATE,
    target="/path/to/file.py",
    details="Overwriting 500 bytes"
)

# Confirm operation
if needs_confirm and ask_user_confirmation(prompt):
    safety.confirm_operation(OperationType.UPDATE, "/path/to/file.py")

# Change mode
safety.set_mode(SafetyMode.STRICT)

# Reset session
safety.reset_session()
```

### Semantic Analyzer

```python
from helix.semantic_analyzer import analyze_codebase_semantics

result = analyze_codebase_semantics(
    base_dir="./src",
    file_patterns=["**/*.py", "**/*.js"]
)

# Access results
summary = result['summary']
vulnerabilities = result['vulnerabilities']
circular_deps = result['circular_dependencies']
unused_imports = result['unused_imports']
complex_functions = result['complex_functions']
recommendations = result['recommendations']
```

### Web Search

```python
from helix.web_search import get_search_manager

search = get_search_manager(
    tavily_api_key="...",  # Optional, reads from env
    exa_api_key="...",
    cache_dir="./tmp/search_cache",
    cache_ttl=86400  # 24 hours
)

# General search
result = search.search(
    query="FastAPI best practices",
    provider="auto",  # "tavily", "exa", or "auto"
    max_results=5,
    search_type="docs",  # "docs", "code", "error", "general"
    use_cache=True
)

# Specialized searches
result = search.search_documentation("FastAPI", "async endpoints")
result = search.search_error_solution("ModuleNotFoundError", context="Python")
result = search.search_best_practices("React", "security")

# Clear cache
search.clear_cache()
```

### GitHub Orchestrator

```python
from helix.github_orchestrator import get_github_orchestrator

gh = get_github_orchestrator(
    github_token="...",  # Optional, reads from env
    default_remote="origin",
    default_branch="main"
)

# Git operations
status = gh.git_status(repo_path=".")
gh.git_add(["file1.py", "file2.py"])
gh.git_commit(message="feat: new feature", add_all=True)
gh.git_push(remote="origin", branch="main")
gh.git_pull()

# Branch operations
gh.create_branch("feature/new", checkout=True)
gh.switch_branch("main")
gh.delete_branch("feature/old", force=False)

# GitHub API operations
gh.create_pull_request(
    owner="username",
    repo="repository",
    title="Add feature",
    head="feature/new",
    base="main",
    body="Description",
    draft=False
)

gh.list_pull_requests(owner, repo, state="open", limit=10)
gh.create_issue(owner, repo, title, body, labels)
gh.get_repository_info(owner, repo)
```

---

## 🔧 Configuration

### Environment Variables

```bash
# .env file

# NVIDIA API
NVIDIA_API_KEY=nvapi-xxx
NVIDIA_MODEL_ID=nvidia/llama-3.1-nemotron-nano-8b-v1
NVIDIA_EMBED_MODEL=nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1

# Web Search
TAVILY_API_KEY=tvly-xxx
EXA_API_KEY=exa-xxx

# GitHub
GITHUB_TOKEN=ghp_xxx

# Workspace
WORKSPACE_DIR=./workspace
CHROMA_PERSIST_DIR=./tmp/chroma

# Safety
HELIX_SAFETY_MODE=normal  # strict, normal, permissive, unsafe
```

### Safety Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `STRICT` | Ask for every operation | Maximum safety |
| `NORMAL` | Ask for destructive ops | **Recommended** |
| `PERMISSIVE` | Ask once per session | Trusted environment |
| `UNSAFE` | Never ask | Automated scripts |

---

## 🐛 Troubleshooting

### Web Search Not Working

**Issue**: "Provider not available" error

**Solution**:
1. Install dependencies: `pip install agno[tavily] agno[exa]`
2. Set API keys in `.env`:
   ```
   TAVILY_API_KEY=your_key
   EXA_API_KEY=your_key
   ```
3. Restart server: `python run_server.py`

### GitHub Operations Failing

**Issue**: "github_token_required" error

**Solution**:
1. Generate token: https://github.com/settings/tokens
2. Add to `.env`: `GITHUB_TOKEN=ghp_xxx`
3. Ensure permissions: `repo`, `workflow`

### Semantic Analysis Slow

**Issue**: Analysis takes too long

**Solution**:
1. Limit file patterns:
   ```python
   analyze_codebase_semantics(
       base_dir="./src",
       file_patterns=["src/**/*.py"]  # Only src directory
   )
   ```
2. Increase system resources
3. Exclude large directories in patterns

### Confirmation Dialogs Not Showing

**Issue**: Operations proceed without asking

**Solution**:
1. Check safety mode: `safety.mode == SafetyMode.NORMAL`
2. Verify session file exists: `./tmp/helix_safety_session.json`
3. Reset session: `safety.reset_session()`

---

## 📊 Performance Tips

1. **Web Search Caching**: Results cached for 24h - reuse queries
2. **Semantic Analysis**: Run once, store results, update incrementally
3. **GitHub API**: Use GraphQL for complex queries (not yet implemented)
4. **ChromaDB**: Index only relevant files, not node_modules/venv

---

## 🎓 Best Practices

### For Users

1. **Trust the Agent**: It will ask before destructive operations
2. **Be Specific**: "Analyze security" vs "Look at my code"
3. **Review PRs**: Agent creates PRs, you review and merge
4. **Use Web Search**: Agent finds latest docs, you don't need to
5. **Chain Commands**: "Analyze, fix, commit, and create PR"

### For Developers

1. **Never Hardcode Secrets**: Use env vars, agent scans for leaks
2. **Trust Semantic Analysis**: It catches issues you miss
3. **Follow Agent Suggestions**: Based on latest best practices
4. **Review Auto-Commits**: Agent writes good messages, but verify
5. **Keep Agent Updated**: New features added regularly

---

## 🚀 Next Steps

Now that you have all features enabled:

1. **Test Safety Layer**:
   ```
   User: "Create a new config.py file"
   Agent: [Asks confirmation first time]
   ```

2. **Try Semantic Analysis**:
   ```
   User: "Analyze my codebase for security issues"
   Agent: [Runs deep analysis, finds vulnerabilities]
   ```

3. **Use Web Search**:
   ```
   User: "Search for FastAPI async patterns"
   Agent: [Finds and summarizes latest docs]
   ```

4. **Automate GitHub**:
   ```
   User: "Create a PR for my changes"
   Agent: [Commits, pushes, creates PR automatically]
   ```

5. **Chain Everything**:
   ```
   User: "Analyze code, fix issues, commit, and create PR"
   Agent: [Executes full workflow autonomously]
   ```

---

## 📞 Support

- **Documentation**: This file + `DYNAMIC_ANALYSIS.md`
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**You now have a fully autonomous AI Code Orchestrator! 🎉**
