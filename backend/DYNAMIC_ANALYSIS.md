# Dynamic Code Analysis with Helix

Helix now includes powerful dynamic code analysis capabilities that scan entire codebases and provide actionable recommendations.

## Features

### 1. **Automatic Codebase Scanning**
   - Scans all code files in directory
   - Supports 15+ programming languages
   - Detects project structure and patterns

### 2. **Code Quality Analysis**
   - Detects TODO/FIXME comments
   - Identifies long functions (50+ lines)
   - Finds missing documentation
   - Checks for hardcoded credentials

### 3. **Best Practice Recommendations**
   - Language-specific linting suggestions
   - Code structure improvements
   - Security recommendations
   - Maintainability tips

## Usage

### Via VS Code Extension

Simply ask Helix to analyze your code:

```
"Analyze this codebase and recommend improvements"
"Check my code for issues"
"What can I improve in this project?"
```

Helix will automatically:
1. Scan all files in your workspace
2. Detect issues and patterns
3. Provide specific recommendations
4. Suggest best practices

### Programmatically

```python
from helix.tools import code_analyzer_tool

# Analyze current directory
result = code_analyzer_tool(base_dir=".")

print(f"Files: {result['summary']['total_files']}")
print(f"Issues: {len(result['issues'])}")
print(f"Recommendations: {result['recommendations']}")
```

### Via Agent Tools

The agent has access to `analyze_codebase()` tool:

```python
agent = create_agent(workspace_dir="/path/to/project")
response = agent.run("Analyze my codebase and provide recommendations")
```

## Example Output

```
📊 CODEBASE ANALYSIS REPORT
==================================================

📁 Total Files: 15
📝 Total Lines: 2,450

🗂️ Languages:
  • python: 8 files
  • javascript: 5 files
  • typescript: 2 files

⚠️ Issues Found (5):
  • server.py: 3 TODO/FIXME comments found
  • utils.py: Function 'process_data' is too long (65 lines)
  • config.py:12: Possible hardcoded credential detected
  • app.py: Missing module docstring
  • handlers.py: Function 'handle_request' is too long (58 lines)

💡 Recommendations:
  ✓ Python detected: Consider using pylint/flake8 for code quality checks
  ✓ JavaScript/TypeScript detected: Consider using ESLint for linting
  ✓ Found 5 code quality issues. Review and address them to improve maintainability
  ✓ Files are quite large (avg 163 lines). Consider breaking them into smaller modules
```

## Supported Languages

- Python (.py)
- JavaScript (.js)
- TypeScript (.ts, .tsx)
- React (.jsx)
- Java (.java)
- C/C++ (.c, .cpp, .h)
- C# (.cs)
- Go (.go)
- Rust (.rs)
- Ruby (.rb)
- PHP (.php)
- And more...

## Configuration

Set max files to scan (default: 100):

```python
result = code_analyzer_tool(base_dir=".", max_files=200)
```

## Integration with RAG

The code analyzer works seamlessly with RAG:

1. **Index workspace**: `python index_workspace.py`
2. **Ask for analysis**: Agent uses both tools + knowledge base
3. **Get comprehensive insights**: Combines static analysis + semantic understanding

## Best Practices

1. **Run regularly**: Analyze code after major changes
2. **Address issues incrementally**: Don't try to fix everything at once
3. **Use with version control**: Track improvements over time
4. **Combine with linters**: Use alongside pylint, ESLint, etc.
5. **Review recommendations**: Not all suggestions apply to every project

## Troubleshooting

**"No files found"**
- Check workspace_dir is set correctly
- Ensure files have recognized extensions
- Check .gitignore isn't excluding code files

**"Analysis too slow"**
- Reduce max_files parameter
- Exclude large directories (node_modules, etc.)
- Use more specific base_dir

**"Too many false positives"**
- Analysis is intentionally conservative
- Review and filter recommendations based on your project needs
- Customize detection patterns in tools.py

## Next Steps

1. Test the analyzer: `python test_analyzer.py`
2. Index your workspace: `python index_workspace.py`
3. Start the server: `python run_server.py`
4. Try in VS Code: Ask "Analyze my code"

## API Reference

### `code_analyzer_tool(base_dir, max_files)`

**Parameters:**
- `base_dir` (str): Directory to analyze (default: ".")
- `max_files` (int): Maximum files to scan (default: 100)

**Returns:**
```python
{
    'ok': True,
    'summary': {
        'total_files': int,
        'total_lines': int,
        'languages': dict
    },
    'files_by_language': dict,
    'issues': list,
    'recommendations': list
}
```

## Examples

### Example 1: Quick Health Check
```python
result = code_analyzer_tool(".")
if len(result['issues']) == 0:
    print("✅ No issues found!")
```

### Example 2: Language-Specific Analysis
```python
result = code_analyzer_tool(".")
python_files = result['files_by_language'].get('python', [])
for file in python_files:
    if file['lines'] > 300:
        print(f"Large file: {file['path']}")
```

### Example 3: CI/CD Integration
```bash
# Add to your CI pipeline
python test_analyzer.py
if [ $? -ne 0 ]; then
    echo "Code quality issues detected!"
    exit 1
fi
```

---

**Happy Coding with Helix! 🚀**
