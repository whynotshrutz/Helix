# Helix AI Agent System - Quick Reference Guide

## 🚀 Getting Started

### 1. Environment Setup

```bash
# Required
export NVIDIA_API_KEY="your-nvidia-api-key"

# Optional (for GitHub operations)
export GITHUB_TOKEN="your-github-token"

# Optional (customize models)
export NVIDIA_MODEL_ID="nvidia/llama-3_1-nemotron-nano-8b-v1"
export NVIDIA_BASE_URL="https://integrate.api.nvidia.com/v1"
```

### 2. Run Test Suite

```bash
python test_agents.py
```

### 3. Start the Server

```bash
cd backend
python run_server.py
```

---

## 🤖 Agent Capabilities

### **Code Analyst Agent**
**What it does**: Generates code, analyzes quality, finds bugs, executes code

**Example queries**:
- "create a function to parse JSON"
- "write a FastAPI endpoint for user login"
- "analyze my codebase for issues"
- "check for security vulnerabilities"
- "modernize this Python 2 code"
- "execute this code and show output"

### **File Operations Agent**
**What it does**: Scans workspace, reads/writes files, searches content

**Example queries**:
- "what files are in this project?"
- "show me the project structure"
- "list all Python files"
- "read config.py"
- "create a new file called utils.js"
- "find where function X is defined"

### **Web Research Agent**
**What it does**: Searches internet, fetches URLs, finds documentation

**Example queries**:
- "find documentation for React hooks"
- "read this article: https://example.com/guide"
- "how to deploy Next.js to Vercel"
- "compare MongoDB vs PostgreSQL"
- "find best practices for API design"

### **Git Operations Agent**
**What it does**: Manages Git/GitHub, commits, branches, PRs, auto-resolves errors

**Example queries**:
- "show git status"
- "commit my changes with message 'fix bug'"
- "push to main"
- "create a new branch called feature-x"
- "list all branches"
- "create a pull request"
- "resolve merge conflicts"

---

## 💡 Usage Patterns

### Pattern 1: Code Generation
```
You: "create a Python function that validates email addresses"

Agent: [Generates complete function with:
- Type hints
- Docstring
- Error handling
- Regex pattern
- Test examples
- Comments explaining logic]
```

### Pattern 2: Workspace Exploration
```
You: "what's in this project?"

Agent: [Scans workspace and shows:
- Total files and directories
- Language breakdown
- File type statistics
- Project structure overview]

You: "show me the src folder"

Agent: [Lists immediate contents of src/:
- Subdirectories
- Files with languages
- File sizes]
```

### Pattern 3: Problem Solving
```
You: "my code has a bug in the login function"

Agent: [Asks for code or finds it automatically]

You: [Provides code]

Agent: [Analyzes, identifies issue, provides fixed version]

You: "test if it works"

Agent: [Executes code and shows results]
```

### Pattern 4: Learning and Research
```
You: "how do I use async/await in JavaScript?"

Agent: [Searches web for official docs and tutorials]
       [Provides comprehensive explanation]
       [Shows code examples]
       [Links to resources]

You: "read this article for more details: [URL]"

Agent: [Fetches URL content]
       [Summarizes key points]
       [Answers follow-up questions]
```

### Pattern 5: Git Workflow
```
You: "what changes do I have?"

Agent: [Shows git status with files]

You: "commit everything with message 'add feature X'"

Agent: [Stages all files]
       [Creates commit]
       [Shows commit hash]

You: "push to origin"

Agent: [Attempts push]
       [Auto-resolves any errors]
       [Confirms success]
```

---

## 🔧 Advanced Features

### Dynamic Workspace Scanning

```python
# The agent automatically scans and understands your workspace
# No need to tell it about your project structure!

# It discovers:
- All files and folders
- Programming languages used
- File types and sizes
- Project organization

# Usage is natural:
"show me all TypeScript files" → Finds them dynamically
"what's in the components folder?" → Lists contents
"find where UserModel is defined" → Searches everywhere
```

### Auto Error Resolution

```python
# Git operations with automatic error fixing:

User: "push to main"

# If error occurs (e.g., remote has new commits):
1. Agent detects error type
2. Finds appropriate solution
3. Applies fix (e.g., pulls first)
4. Retries operation
5. Reports success

# Common errors auto-resolved:
- Push rejected (pulls first)
- Merge conflicts (guides resolution)
- Authentication issues (checks config)
- Branch conflicts (suggests resolution)
```

### Multi-Agent Coordination

```python
# Complex queries use multiple agents in parallel:

User: "analyze my code and find best practices online"

# Orchestrator routes to:
1. Code Analyst: Analyzes codebase
2. Web Research: Searches best practices

# Results are combined and presented together
```

### Memory and Context

```python
# Agents remember context across conversation:

User: "I'm working on a React project"
Agent: [Stores: project.framework = React]

User: "create a component"
Agent: [Knows it's React, generates React component]

User: "what framework am I using?"
Agent: [Recalls: "You're working on a React project"]
```

---

## 🎯 Best Practices

### For Code Generation:
1. **Be specific about requirements**
   - ✅ "create a REST API endpoint that accepts JSON and validates email"
   - ❌ "make an API"

2. **Mention language if ambiguous**
   - ✅ "write a sorting function in Python"
   - ✅ "create a React component for login form"

3. **Provide context when fixing bugs**
   - ✅ "fix this function: [code]"
   - ✅ "this code throws TypeError, fix it: [code]"

### For Workspace Operations:
1. **Start with overview**
   - First: "what files are here?"
   - Then: "show me the src folder"
   - Finally: "read src/main.py"

2. **Use natural language**
   - ✅ "find all Python files"
   - ✅ "list files in the components directory"

### For Research:
1. **Be specific about what you need**
   - ✅ "find React hooks documentation"
   - ✅ "how to implement JWT authentication"

2. **Provide URLs when you have them**
   - ✅ "read this guide: https://..."
   - ✅ "summarize this article: https://..."

### For Git Operations:
1. **Check status first**
   - "show git status"
   - "what changes do I have?"

2. **Use descriptive commit messages**
   - ✅ "commit with message 'add user authentication'"
   - ❌ "commit with message 'update'"

3. **Let auto-resolution work**
   - Don't worry about common errors
   - Agent will handle and retry automatically

---

## 🐛 Troubleshooting

### "Agent not responding correctly"
- Check NVIDIA_API_KEY is set
- Verify internet connection
- Try rephrasing your query

### "Can't find files in workspace"
- Make sure you're in the correct directory
- Try "scan workspace" to refresh
- Check file permissions

### "Git operations failing"
- Verify you're in a Git repository
- Check Git authentication is configured
- Set GITHUB_TOKEN for GitHub API operations

### "Code execution failing"
- Check if Docker executor is running (optional)
- Verify code syntax is correct
- Check for missing dependencies

---

## 📚 API Integration

### REST API Endpoint

```python
POST /api/v1/query
{
    "query": "create a function to sort arrays",
    "context": {}  # optional
}

Response:
{
    "ok": true,
    "result": "[Generated code]",
    "agent": "code_analyst",
    "mode": "single"
}
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const response = JSON.parse(event.data);
    console.log(response.result);
};

ws.send(JSON.stringify({
    query: "what files are in this project?"
}));
```

---

## 🎊 Tips for Best Results

1. **Be Conversational**: Talk naturally, don't use commands
   - ✅ "can you create a login function?"
   - ✅ "show me what's in the project"

2. **Provide Context**: The agent learns as you talk
   - Mention your tech stack
   - Describe what you're building
   - Explain your goals

3. **Iterate**: Refine results through conversation
   - "make it more secure"
   - "add error handling"
   - "simplify this"

4. **Trust the Tools**: Let agents use their tools
   - They know when to scan workspace
   - They'll fetch URLs when needed
   - They'll execute code to verify

5. **Explore**: Try different queries to discover capabilities
   - "what can you help me with?"
   - "analyze this codebase"
   - "research best practices for X"

---

## 🚀 Ready to Use!

The Helix AI system is now fully operational and ready to assist with:
- ✅ Code generation (any language)
- ✅ Workspace exploration
- ✅ Web research and documentation
- ✅ Git/GitHub operations
- ✅ Error detection and resolution
- ✅ Code analysis and improvement

**Start chatting and let the agents help you build!** 🎉
