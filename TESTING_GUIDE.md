# Helix - Testing Guide for New Features

## 🚀 Server Restart & Feature Testing

### Step 1: Restart the Server

The server needs to be restarted to load the new modules (memory_manager, git_auth_manager, git_operations, repo_analyzer).

```bash
# Navigate to backend directory
cd backend

# Stop any running server (Ctrl+C if running, or kill process)

# Start server
python run_server.py
```

**Expected Output**:
```
🚀 Starting Helix with Multi-Agent System...
🔄 Initializing NVIDIA model for multi-agent system: nvidia/llama-3_1-nemotron-nano-8b-v1
✅ NVIDIA model initialized
✅ Shared knowledge base initialized
🔄 Creating specialized agents...
  ✅ Orchestrator Agent created with memory tools
  ✅ Code Analyst Agent created
  ✅ File Operations Agent created
  ✅ Web Research Agent created
  ✅ Git Operations Agent created
```

**Verify New Modules Loaded**:
- Look for "Orchestrator Agent created **with memory tools**"
- No import errors for memory_manager, git_auth_manager, git_operations

---

## 🧠 Memory System Tests

### Test 1: Store and Recall User Preference

**Chat**: "Remember that I prefer TypeScript for new files"

**Expected**: `✅ Stored: user_preference/language = TypeScript (expires in 30 days)`

**Verify**: "What language do I prefer?"

**Expected**: `📌 user_preference/language = TypeScript`

### Test 2: Update Project Context

**Chat**: "This is a TypeScript React project with FastAPI backend"

**Expected**: `✅ Project context updated: languages, frameworks`

**Verify**: "What's this project about?"

**Expected**: Returns project context with languages and frameworks

### Test 3: Memory Statistics

**Chat**: "Show memory stats"

**Expected**: Shows message count, facts count, file size, timestamps

### Test 4: Persistence Across Restarts

1. Send messages
2. Stop server
3. Restart server
4. Check "Show memory stats"
5. **Expected**: Message count includes pre-restart messages

---

## 📊 Repository Analysis Tests

### Test 1: Full Repository Analysis

**Chat**: "Analyze entire repository for outdated patterns"

**Expected**: 
- Files analyzed count
- Severity breakdown (high/medium/low)
- Top 10 recommendations
- 8-step migration plan
- Web-researched best practices with URLs

### Test 2: Focused Analysis

**Chat**: "Analyze repository focusing on backend/src/"

**Expected**: Only analyzes files in backend/src/

### Test 3: Limited File Count

**Chat**: "Analyze repository with max 10 files"

**Expected**: Analyzes only 10 files

---

## 🔐 Git Operations Tests

### Test 1: Git Status

**Chat**: "Show git status"

**Expected**: Lists modified, added, deleted, untracked files

### Test 2: List Git Accounts

**Chat**: "List my Git accounts"

**Expected**: Shows accounts from credential helper, PAT, OAuth

### Test 3: Auto-Commit Message

**Prerequisite**: Make a change and stage it
```bash
echo "# Test" >> test.txt
git add test.txt
```

**Chat**: "Generate commit message"

**Expected**: Auto-generated message with 3 suggestions

### Test 4: Commit Changes

**Chat**: "Commit these changes"

**Expected**: Creates commit with generated message

### Test 5: Branch Operations

**Chat**: "Create branch feature/test"

**Expected**: Creates and checks out branch

**Verify**: "List branches"

**Expected**: Shows all branches with current marked (➤)

---

## 🌐 API Endpoint Tests

### Memory API

```bash
# Get stats
curl http://localhost:8001/api/memory/stats

# Get conversation
curl http://localhost:8001/api/memory/conversation?limit=5

# Get project context
curl http://localhost:8001/api/memory/context

# Store fact
curl -X POST http://localhost:8001/api/memory/fact \
  -H "Content-Type: application/json" \
  -d '{"category": "test", "key": "example", "value": "test value", "ttl_days": 30}'
```

### Git API

```bash
# List accounts
curl http://localhost:8001/api/git/accounts

# Store PAT (optional)
curl -X POST http://localhost:8001/api/git/store-pat \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GitHub Test",
    "username": "username",
    "token": "ghp_token",
    "email": "email@example.com"
  }'
```

---

## ✅ Success Checklist

### Memory System
- [ ] Memory file created at `.helix/memory.json`
- [ ] File permissions are 0o600
- [ ] Facts stored and retrieved
- [ ] Project context persists
- [ ] Conversation history saved
- [ ] Persists across restarts
- [ ] Memory stats show correct counts

### Git Authentication
- [ ] Lists system Git credentials
- [ ] Can store PAT via API
- [ ] PAT file permissions are 0o600
- [ ] Account listing works

### Git Operations
- [ ] Status shows files correctly
- [ ] Auto-commit message generation works
- [ ] Commit creates actual commit
- [ ] Branch creation works
- [ ] Branch listing shows current

### Repository Analysis
- [ ] Discovers files
- [ ] Skips excluded directories
- [ ] Returns recommendations
- [ ] Migration plan has 8 steps
- [ ] Web research includes URLs

### API Endpoints
- [ ] All endpoints return 200 OK
- [ ] Memory endpoints work
- [ ] Git endpoints work

---

## 🐛 Common Issues

### Memory file not created

**Check**: `cat .env | grep HELIX_MULTI_AGENT`

**Fix**: Add `HELIX_MULTI_AGENT=true` to .env and restart

### Import errors

**Symptom**: `ImportError: cannot import name 'MemoryManager'`

**Fix**: Verify files exist in `backend/src/helix/`

### Git operations fail

**Check**: `git --version`

**Fix**: Install Git if missing

### GitHub CLI not found

**Check**: `gh --version`

**Fix**: Install GitHub CLI (winget install GitHub.cli)

---

## 📊 Expected File Structure

```
Helix/
├── .helix/                   # Auto-created
│   ├── memory.json          # 0o600
│   └── git_auth.json        # 0o600 (if PAT stored)
├── backend/src/helix/
│   ├── memory_manager.py         ✅ NEW
│   ├── git_auth_manager.py       ✅ NEW
│   ├── git_operations.py         ✅ NEW
│   ├── repo_analyzer.py          ✅ NEW
│   ├── multi_agent_system.py    ✅ UPDATED
│   └── server.py                 ✅ UPDATED
├── MEMORY_AND_GIT.md             ✅ NEW
└── IMPLEMENTATION_SUMMARY.md     ✅ NEW
```

---

**For detailed documentation, see MEMORY_AND_GIT.md**
