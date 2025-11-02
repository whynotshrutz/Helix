# Helix Memory & Git Integration Features

## 🧠 Persistent Memory System

Helix now maintains conversation history and project context across sessions using a persistent memory manager.

### Memory Storage Location
- **File**: `.helix/memory.json`
- **Permissions**: 0o600 (owner read/write only)
- **Auto-created**: First time you interact with Helix

### Features

#### 1. Conversation History
- Automatically stores all user messages and agent responses
- **Rotation**: Keeps most recent 1000 messages
- **TTL**: 30-day time-to-live for old entries
- **Access**: via Orchestrator agent memory tools

#### 2. Project Context
Store and retrieve project information:
- **Languages**: Programming languages used
- **Frameworks**: Frameworks and libraries
- **Key Files**: Important files in the project
- **Description**: Project description

#### 3. Facts Storage
Store arbitrary facts with categories:
- **user_preference**: User preferences (language, style, etc.)
- **project**: Project-specific information
- **code_pattern**: Code patterns and decisions
- **decision**: Design decisions made

### Using Memory Tools

All memory tools are available through the Orchestrator agent:

```
# Store a fact
"Remember that I prefer TypeScript for new files"
→ Stores: user_preference/language = TypeScript

# Store project info
"This is a React project with FastAPI backend"
→ Updates project context: frameworks = ['React', 'FastAPI']

# Recall information
"What language do I prefer?"
→ Recalls: user_preference/language

# Search memory
"Show me all user preferences"
→ Searches: category=user_preference

# Get project context
"What's this project about?"
→ Returns full project context

# Memory statistics
"Show memory stats"
→ Returns: message count, facts count, file size
```

### API Endpoints

**GET /api/memory/stats**
- Returns memory statistics

**GET /api/memory/conversation?limit=50**
- Returns recent conversation messages

**GET /api/memory/context**
- Returns project context

**POST /api/memory/fact**
```json
{
  "category": "user_preference",
  "key": "coding_style",
  "value": "functional",
  "ttl_days": 30
}
```

**DELETE /api/memory/conversation**
- Clears conversation history (keeps facts and context)

---

## 🔐 Git Authentication System

Helix supports three authentication methods for Git operations, with automatic account selection.

### Authentication Methods

#### 1. Credential Helper (Easiest)
Uses your system's Git credentials automatically.

**Setup**: Already configured if you can push via `git` command

**How it works**:
- Reads from `git config --list`
- Uses system credential helper
- No additional setup needed

#### 2. Personal Access Token (PAT)
Store GitHub/GitLab tokens securely.

**Setup**:
1. Generate token from GitHub:
   - Go to Settings → Developer Settings → Personal Access Tokens
   - Generate new token (classic)
   - Select scopes: `repo`, `workflow`, `write:packages`

2. Store in Helix:
   ```
   POST /api/git/store-pat
   {
     "name": "GitHub Main",
     "username": "your-username",
     "token": "ghp_...",
     "email": "your@email.com"
   }
   ```

**Storage**: `.helix/git_auth.json` (permissions: 0o600)

#### 3. OAuth (Future)
Full OAuth flow with refresh tokens.

**Status**: Infrastructure ready, OAuth flow to be implemented

### Git Operations

#### Available Commands

**Git Status**:
```
"what's the git status?"
→ Shows: modified, added, deleted, untracked files
```

**Auto-Commit**:
```
"commit these changes"
→ Auto-generates message by analyzing changes
→ Returns 3 suggestions: standard, chore:, feat:
```

**Push with Account Selection**:
```
"push to GitHub"
→ Lists available accounts
→ User selects account (via UI prompt)
→ Pushes using selected credentials
→ Shows: account used, remote, branch
```

**Branch Management**:
```
"create branch feature-x"
"switch to main"
"list all branches"
```

**Conflict Resolution**:
```
"list conflicts"
→ Shows conflicted files

"resolve conflict file.py with ours"
→ Resolves using 'ours' or 'theirs' strategy
```

**GitHub Operations** (requires GitHub CLI):
```
"create repo my-project"
→ Creates GitHub repository
→ Returns: repo URL

"create pull request"
→ Creates PR from current branch
→ Returns: PR URL
```

### Git Workflows

#### Recommended Flow for Pushing

1. **Check Status**:
   ```
   "show git status"
   ```

2. **Commit Changes**:
   ```
   "commit these changes"
   # Or with custom message:
   "commit with message: Add new feature"
   ```

3. **Push to Remote**:
   ```
   "push to GitHub"
   # Helix will:
   # - List available accounts
   # - Prompt for selection (UI)
   # - Push using selected account
   # - Confirm: "Pushed to origin/main using GitHub Main account"
   ```

#### Conflict Resolution Flow

1. **Detect Conflicts**:
   ```
   "pull from main"
   # If conflicts: "⚠️ Merge conflicts detected in 2 file(s)"
   ```

2. **List Conflicts**:
   ```
   "list conflicts"
   # Shows: src/main.py, README.md
   ```

3. **Resolve**:
   ```
   "resolve conflict src/main.py with ours"
   # Or: "with theirs"
   ```

4. **Commit Resolution**:
   ```
   "commit"
   # Auto-generates merge commit message
   ```

### API Endpoints

**GET /api/git/accounts**
- Returns all available Git accounts across all auth methods
- Response:
  ```json
  {
    "ok": true,
    "accounts": {
      "credential_helper": [...],
      "pat": [...],
      "oauth": [...]
    },
    "total_count": 3
  }
  ```

**POST /api/git/select-account**
```json
{
  "account_id": "GitHub Main",
  "auth_method": "pat"
}
```

**POST /api/git/store-pat**
```json
{
  "name": "GitHub Main",
  "username": "octocat",
  "token": "ghp_...",
  "email": "octocat@github.com"
}
```

---

## 🔄 Repository-Wide Code Analysis

Analyze entire repositories for modernization opportunities.

### Usage

```
"analyze entire repository"
# Or:
"modernize whole project"
"check all files for outdated patterns"
```

### What It Does

1. **Discovers Files**: Walks entire directory tree
   - Skips: `node_modules`, `__pycache__`, `.git`, `dist`, `build`
   - Scans: `.py`, `.js`, `.ts`, `.java`, `.go`, `.rs`, `.cpp`, `.c` files

2. **Analyzes Each File**: Uses CodeModernizer to detect:
   - Python 2 syntax
   - Old JavaScript (var, function callbacks)
   - Deprecated dependencies
   - Security vulnerabilities
   - Performance anti-patterns

3. **Web Research**: For top 5 most common patterns:
   - Searches web for best practices
   - Collects migration guides
   - Returns web resources with URLs

4. **Generates Migration Plan**: 8-step plan with:
   - Estimated time
   - Difficulty level
   - Priority-sorted steps
   - Backup and testing recommendations

### Output Format

```
📊 REPOSITORY-WIDE CODE ANALYSIS
Workspace: /path/to/project
Files analyzed: 45
Files with issues: 12
Total patterns found: 34

⚠️ SEVERITY BREAKDOWN:
  🔴 High priority: 8
  🟡 Medium priority: 18
  🟢 Low priority: 8

💡 TOP RECOMMENDATIONS (10):
  1. [HIGH] Replace Python 2 print statements
     File: src/main.py
     Current: print "hello"
     Alternative: print("hello")
     Example: ...

📋 MIGRATION PLAN:
  Total items: 34
  Estimated time: 12 hours
  Difficulty: medium
  
  Steps:
    1. Create backup branch
    2. Fix critical issues (8 items)
    3. Update dependencies
    4. Implement improvements (18 items)
    5. Run tests
    6. Polish and optimize (8 items)
    7. Review and commit
    8. Create pull request

🌐 RESEARCHED BEST PRACTICES:
  Pattern: Python 2 print statements
  Found in 5 files
    📎 Python 3 Migration Guide
       https://docs.python.org/3/howto/pyporting.html
  
  Pattern: var declarations in JavaScript
  Found in 8 files
    📎 ES6 Migration Guide
       https://developer.mozilla.org/en-US/docs/Web/JavaScript
```

### Focus on Specific Paths

```
"analyze repository focusing on src/ and tests/"
→ Only analyzes files in src/ and tests/ directories
```

---

## 🚀 Quick Start

### 1. Store Your Git Credentials

**Option A**: Use system Git (automatic)
- No setup needed if `git push` already works

**Option B**: Store PAT
```bash
curl -X POST http://localhost:8001/api/git/store-pat \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GitHub Main",
    "username": "your-username",
    "token": "ghp_...",
    "email": "your@email.com"
  }'
```

### 2. Update Project Context

Tell Helix about your project:
```
"This is a TypeScript React project with Node.js backend"
```

Helix will automatically:
- Store: languages = ['TypeScript', 'JavaScript']
- Store: frameworks = ['React', 'Node.js']
- Remember for future sessions

### 3. Analyze Your Code

```
"analyze entire repository for outdated patterns"
```

Helix will:
- Scan all files
- Detect patterns
- Research best practices
- Generate migration plan

### 4. Commit and Push

```
"commit these changes"
→ Auto-generates message

"push to GitHub"
→ Shows accounts
→ You select
→ Pushes automatically
```

---

## 🛠️ Configuration

### Environment Variables

```bash
# Enable multi-agent system (required for memory/git features)
HELIX_MULTI_AGENT=true

# Workspace directory (default: current directory)
WORKSPACE_DIR=./path/to/project

# Server settings
HELIX_BIND_HOST=127.0.0.1
HELIX_BIND_PORT=8001

# NVIDIA API
NVIDIA_API_KEY=nvapi-...
NVIDIA_MODEL_ID=nvidia/llama-3_1-nemotron-nano-8b-v1
```

### File Locations

```
workspace/
├── .helix/
│   ├── memory.json          # Conversation history, facts, context
│   ├── git_auth.json        # PAT and OAuth credentials (0o600)
│   └── chroma/              # Vector database for knowledge
├── .vscode/
│   └── helix.json           # Extension settings
└── your-files...
```

### Permissions

All `.helix/` files are created with restrictive permissions:
- `memory.json`: 0o600 (owner read/write only)
- `git_auth.json`: 0o600 (owner read/write only)

Never commit `.helix/` to version control!

Add to `.gitignore`:
```
.helix/
```

---

## 📊 Memory Statistics

Check memory usage:
```
"show memory stats"
```

Output:
```
📊 MEMORY STATS:
  Conversation messages: 245
  Facts stored: 12 valid, 3 expired
  Memory file: /path/to/.helix/memory.json
  File size: 45.23 KB
  Created: 2024-01-15T10:30:00
  Last updated: 2024-01-20T14:22:15
```

---

## 🧹 Maintenance

### Clear Conversation History

```
"clear conversation history"
```

**API**:
```bash
curl -X DELETE http://localhost:8001/api/memory/conversation
```

**Note**: Facts and project context are preserved

### Export Memory

```python
from helix.memory_manager import MemoryManager

memory = MemoryManager(workspace_dir=".")
data = memory.export_memory(export_path="memory_backup.json")
```

### Remove Git Account

Currently via API:
```python
from helix.git_auth_manager import GitAuthManager

auth = GitAuthManager(workspace_dir=".")
auth.remove_account("GitHub Main", "pat")
```

---

## 🔒 Security Notes

1. **Never commit `.helix/` directory**
   - Contains tokens and credentials
   - Add to `.gitignore`

2. **PAT Permissions**
   - Only grant necessary scopes
   - Rotate tokens regularly
   - Use fine-grained PATs when possible

3. **File Permissions**
   - All credential files: 0o600
   - Automatic on creation
   - Check periodically: `ls -la .helix/`

4. **Memory Privacy**
   - Conversation history stored locally
   - Not sent to external services
   - Clear when sharing workspace

---

## 🐛 Troubleshooting

### Memory Not Persisting

**Check**:
1. Is multi-agent mode enabled? `HELIX_MULTI_AGENT=true`
2. Does `.helix/` directory exist? Created automatically
3. Check file permissions: `ls -la .helix/memory.json`
4. Check logs: Memory operations logged to console

### Git Authentication Fails

**Check**:
1. List accounts: `GET /api/git/accounts`
2. Verify PAT has correct scopes
3. Test system Git: `git push` from terminal
4. Check GitHub CLI: `gh auth status`

### Repository Analysis Too Slow

**Limit files**:
```
"analyze repository with max 20 files"
```

**Focus on specific paths**:
```
"analyze repository focusing on src/"
```

### Account Selection Not Working

**Temporary workaround** (until UI complete):
- Agent will attempt credential helper first
- Or prompt in chat for account name
- Full UI prompt coming soon

---

## 📝 Examples

### Complete Workflow Example

```
User: "This is a Python FastAPI project"
Helix: ✅ Project context updated: frameworks, languages

User: "I prefer using type hints"
Helix: ✅ Stored: user_preference/type_hints = true

User: "analyze entire repository"
Helix: [Shows repo-wide analysis]

User: "commit these changes"
Helix: Auto-generated message: "feat: Add type hints to main.py"

User: "push to GitHub"
Helix: [Lists accounts]
       GitHub Main (pat) - your-username
       GitLab Work (credential_helper) - work-email
User: "use GitHub Main"
Helix: ✅ Pushed to origin/main using GitHub Main account

User: "What did I say about type hints?"
Helix: 📌 user_preference/type_hints = true

User: "show memory stats"
Helix: [Shows statistics]
```

---

## 🚧 Roadmap

### Completed ✅
- Persistent memory manager
- Three-way Git authentication
- Repository-wide analysis
- Automatic commit message generation
- Conflict resolution
- GitHub repo and PR creation
- API endpoints for memory and Git

### In Progress 🔄
- VS Code account selection dialog
- OAuth flow implementation

### Planned 📋
- Dry-run mode for code changes
- Preview/apply flow for recommendations
- Interactive conflict resolution UI
- GitHub Actions integration
- Automated testing workflows
- Memory search UI
- Export/import memory backups

---

## 📚 Related Documentation

- [Multi-Agent System](./AGENTS.md)
- [Code Modernization](./MODERNIZATION.md)
- [Web Research Integration](./WEB_RESEARCH.md)
- [Safety Features](./SAFETY.md)

---

**Version**: 1.0  
**Last Updated**: 2024-01-20  
**Status**: Production Ready (Memory & Git Backend), UI in Progress
