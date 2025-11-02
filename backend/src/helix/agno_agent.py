"""Agno Agent wrapper for Helix code assistant.

This module creates an Agent configured with NVIDIA model, Chroma knowledge and tools.
"""
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from agno.agent import Agent
    from agno.models.nvidia import Nvidia
    from agno.tools import tool
    from agno.db.sqlite import SqliteDb
    from agno.knowledge.knowledge import Knowledge
    from agno.vectordb.chroma import ChromaDb
    
    # Import our custom wrapper
    from .nvidia_model_wrapper import NvidiaModelWrapper
except Exception as e:  # pragma: no cover - agno optional for scaffolding
    Agent = None
    Nvidia = None
    tool = None
    SqliteDb = None
    Knowledge = None
    ChromaDb = None
    NvidiaModelWrapper = None

from .tools import (
    file_reader_tool, 
    code_executor_tool, 
    search_tool, 
    doc_helper_tool,
    code_analyzer_tool,
    file_writer_tool
)
from .semantic_analyzer import analyze_codebase_semantics
from .web_search import get_search_manager
from .github_orchestrator import get_github_orchestrator
from .safety_manager import get_safety_manager, SafetyMode


def create_agent(
    name: str = "Helix Code Assistant",
    chroma_collection: str = "helix_vectors",
    db_file: str = "./tmp/helix.db",
    workspace_dir: str = "."
):
    """Create and return an Agno Agent instance wired with tools and knowledge.

    If Agno is not installed the function raises a helpful error.
    """
    if Agent is None:
        raise RuntimeError("Agno SDK not installed. `pip install agno` to enable agent functionality.")

    # Register tools as Agno tools with proper decorators
    # All tools return strings to avoid empty message issues with NVIDIA API
    
    @tool(name="read_file")
    def read_file(path: str) -> str:
        """Read a file from the workspace.
        
        Args:
            path: Relative path to the file
            
        Returns:
            File content or error message
        """
        result = file_reader_tool(path, base_dir=workspace_dir)
        if isinstance(result, dict):
            if result.get("ok"):
                if result.get("type") == "file":
                    return f"File: {result['path']}\n\n{result['content']}"
                elif result.get("type") == "dir":
                    return f"Directory contains: {', '.join(result['files'])}"
            return f"Error: {result.get('error', 'Unknown error')}"
        return str(result)

    @tool(name="search_files")
    def search_files(query: str, use_regex: bool = False, max_results: int = 20) -> str:
        """Search files in the workspace.
        
        Args:
            query: Search query (text or regex)
            use_regex: Whether to use regex matching
            max_results: Maximum results to return
            
        Returns:
            Search results as formatted string
        """
        results = search_tool(query, base_dir=workspace_dir, use_regex=use_regex, max_results=max_results)
        if not results:
            return f"No files found matching '{query}'"
        output = [f"Found {len(results)} matches:"]
        for r in results[:10]:  # Limit output
            output.append(f"\n- {r['path']}: ...{r['snippet']}...")
        return "\n".join(output)

    @tool(name="execute_code")
    def execute_code(code: str, language: str = "python") -> str:
        """Execute code in a sandboxed environment.
        
        Args:
            code: Code to execute
            language: Programming language (python, bash, etc.)
            
        Returns:
            Execution result as formatted string
        """
        result = code_executor_tool(code, language=language)
        if isinstance(result, dict):
            output = [f"Executed {language} code:"]
            if result.get("stdout"):
                output.append(f"Output: {result['stdout']}")
            if result.get("stderr"):
                output.append(f"Errors: {result['stderr']}")
            output.append(f"Exit code: {result.get('returncode', 'unknown')}")
            return "\n".join(output)
        return str(result)

    @tool(name="explain_code")
    def explain_code(code: str, request: str = "explain") -> str:
        """Get documentation help for code.
        
        Args:
            code: Code to analyze
            request: Type of help (explain, docstring)
            
        Returns:
            Documentation or explanation as string
        """
        result = doc_helper_tool(code, request=request)
        if isinstance(result, dict):
            return result.get("explanation", str(result))
        return str(result)

    @tool(name="analyze_codebase")
    def analyze_codebase(directory: str = ".") -> str:
        """Analyze entire codebase and provide comprehensive recommendations.
        
        Args:
            directory: Directory to analyze (default: current workspace)
            
        Returns:
            Detailed analysis report with recommendations
        """
        result = code_analyzer_tool(base_dir=workspace_dir if directory == "." else directory)
        if not result.get('ok'):
            return f"Error analyzing codebase: {result.get('error', 'Unknown error')}"
        
        output = ["📊 CODEBASE ANALYSIS REPORT", "=" * 50, ""]
        
        summary = result['summary']
        output.append(f"📁 Total Files: {summary['total_files']}")
        output.append(f"📝 Total Lines: {summary['total_lines']:,}")
        output.append("")
        
        output.append("🗂️ Languages:")
        for lang, count in summary['languages'].items():
            output.append(f"  • {lang}: {count} files")
        output.append("")
        
        if result['issues']:
            output.append(f"⚠️ Issues Found ({len(result['issues'])}):")
            for issue in result['issues'][:10]:  # Show first 10
                output.append(f"  • {issue}")
            if len(result['issues']) > 10:
                output.append(f"  ... and {len(result['issues']) - 10} more")
            output.append("")
        
        if result['recommendations']:
            output.append("💡 Recommendations:")
            for rec in result['recommendations']:
                output.append(f"  ✓ {rec}")
        
        return "\n".join(output)

    @tool(name="write_file")
    def write_file(path: str, content: str) -> str:
        """Create or overwrite a file with content.
        
        Args:
            path: Relative path to the file to create
            content: Content to write to the file
            
        Returns:
            Success message or error description
        """
        import os
        from pathlib import Path
        
        try:
            if not content or not content.strip():
                return "Error: File content cannot be empty"
            if not path or not path.strip():
                return "Error: File path cannot be empty"
            
            # Create full path
            full_path = Path(workspace_dir) / path
            
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            full_path.write_text(content, encoding='utf-8')
            
            return f"✅ File created successfully: {path} ({len(content)} bytes at {str(full_path)})"
        except Exception as e:
            return f"❌ Failed to create file {path}: {str(e)}"
    
    @tool(name="analyze_semantics")
    def analyze_semantics(directory: str = ".") -> str:
        """Analyze codebase semantics: dependencies, complexity, vulnerabilities.
        
        Args:
            directory: Directory to analyze (default: workspace root)
            
        Returns:
            Detailed semantic analysis report
        """
        target_dir = workspace_dir if directory == "." else directory
        
        try:
            result = analyze_codebase_semantics(base_dir=target_dir)
            
            if not result:
                return "❌ Semantic analysis failed"
            
            output = ["🔍 SEMANTIC CODE ANALYSIS", "=" * 60, ""]
            
            # Summary
            summary = result.get('summary', {})
            output.append("📊 Summary:")
            output.append(f"  Files analyzed: {summary.get('total_files', 0)}")
            output.append(f"  Total imports: {summary.get('total_imports', 0)}")
            output.append(f"  Total functions: {summary.get('total_functions', 0)}")
            output.append(f"  🔴 Vulnerabilities: {summary.get('vulnerabilities_found', 0)}")
            output.append(f"  🔄 Circular dependencies: {summary.get('circular_dependencies', 0)}")
            output.append(f"  🧹 Unused imports: {summary.get('unused_imports', 0)}")
            output.append(f"  📊 Complex functions: {summary.get('complex_functions', 0)}")
            output.append("")
            
            # Vulnerabilities (Critical!)
            vulns = result.get('vulnerabilities', [])
            if vulns:
                output.append(f"🚨 SECURITY VULNERABILITIES ({len(vulns)} found):")
                for v in vulns[:5]:  # Top 5
                    output.append(f"  [{v['severity'].upper()}] {v['title']}")
                    output.append(f"    File: {v['file']}:{v['line']}")
                    output.append(f"    Fix: {v['recommendation']}")
                    output.append("")
            
            # Circular dependencies
            circular = result.get('circular_dependencies', [])
            if circular:
                output.append(f"🔄 Circular Dependencies ({len(circular)} found):")
                for cycle in circular[:3]:  # Show first 3
                    output.append(f"  • {' → '.join(cycle)}")
                output.append("")
            
            # Complex functions
            complex_funcs = result.get('complex_functions', [])
            if complex_funcs:
                output.append(f"📊 Complex Functions ({len(complex_funcs)} found):")
                for func in complex_funcs[:5]:  # Top 5
                    output.append(f"  • {func['name']} (complexity: {func['complexity']}, {func['lines']} lines)")
                    output.append(f"    {func['file']}:{func['line']}")
                output.append("")
            
            # Recommendations
            recs = result.get('recommendations', [])
            if recs:
                output.append("💡 Recommendations:")
                for rec in recs:
                    output.append(f"  ✓ {rec}")
            
            return "\n".join(output)
        
        except Exception as e:
            return f"❌ Semantic analysis error: {str(e)}"
    
    @tool(name="search_web")
    def search_web(query: str, search_type: str = "docs") -> str:
        """Search the web for documentation, solutions, and best practices.
        
        Args:
            query: Search query
            search_type: Type of search (docs, code, general, error)
            
        Returns:
            Search results with URLs and content
        """
        try:
            search_mgr = get_search_manager()
            result = search_mgr.search(query=query, search_type=search_type, max_results=3)
            
            if not result.get('ok'):
                return f"❌ Search failed: {result.get('error', 'unknown error')}"
            
            results = result.get('results', [])
            if not results:
                return f"🔍 No results found for: {query}"
            
            output = [f"🔍 WEB SEARCH RESULTS: {query}", "=" * 60, ""]
            
            for i, item in enumerate(results, 1):
                output.append(f"{i}. {item.get('title', 'Untitled')}")
                output.append(f"   URL: {item.get('url', '')}")
                content = item.get('content', '')
                if content:
                    # Truncate to first 200 chars
                    preview = content[:200] + "..." if len(content) > 200 else content
                    output.append(f"   {preview}")
                output.append("")
            
            return "\n".join(output)
        
        except Exception as e:
            return f"❌ Web search error: {str(e)}"
    
    @tool(name="git_commit")
    def git_commit(message: str, add_all: bool = True) -> str:
        """Create a git commit with changes.
        
        Args:
            message: Commit message
            add_all: Whether to stage all changes (default: True)
            
        Returns:
            Commit result with hash
        """
        try:
            gh = get_github_orchestrator()
            
            # Check status first
            status = gh.git_status(repo_path=workspace_dir)
            if not status.get('ok'):
                return f"❌ Git status check failed: {status.get('error')}"
            
            if status.get('clean'):
                return "ℹ️ No changes to commit (working tree clean)"
            
            # Create commit
            result = gh.git_commit(
                message=message,
                repo_path=workspace_dir,
                add_all=add_all
            )
            
            if result.get('ok'):
                return f"✅ Commit created: {result.get('commit_hash')[:8]}\n   Message: {message}"
            else:
                return f"❌ Commit failed: {result.get('error')}"
        
        except Exception as e:
            return f"❌ Git commit error: {str(e)}"
    
    @tool(name="git_push")
    def git_push(remote: str = "origin", branch: str = None) -> str:
        """Push commits to remote repository.
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
            
        Returns:
            Push result
        """
        try:
            gh = get_github_orchestrator()
            
            result = gh.git_push(
                remote=remote,
                branch=branch,
                repo_path=workspace_dir
            )
            
            if result.get('ok'):
                return f"✅ Successfully pushed to {result.get('remote')}/{result.get('branch')}"
            else:
                return f"❌ Push failed: {result.get('message', result.get('error'))}"
        
        except Exception as e:
            return f"❌ Git push error: {str(e)}"
    
    @tool(name="create_pull_request")
    def create_pull_request(
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str = "main",
        description: str = ""
    ) -> str:
        """Create a pull request on GitHub.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Source branch with changes
            base: Target branch (default: main)
            description: PR description
            
        Returns:
            PR creation result with URL
        """
        try:
            gh = get_github_orchestrator()
            
            result = gh.create_pull_request(
                owner=owner,
                repo=repo,
                title=title,
                head=head,
                base=base,
                body=description
            )
            
            if result.get('ok'):
                return f"✅ Pull request created!\n   #{result.get('pr_number')}: {title}\n   URL: {result.get('pr_url')}"
            else:
                return f"❌ PR creation failed: {result.get('message', result.get('error'))}"
        
        except Exception as e:
            return f"❌ GitHub PR error: {str(e)}"
    
    @tool(name="create_branch")
    def create_branch(branch_name: str, checkout: bool = True) -> str:
        """Create a new git branch.
        
        Args:
            branch_name: Name for the new branch
            checkout: Whether to switch to the new branch (default: True)
            
        Returns:
            Branch creation result
        """
        try:
            gh = get_github_orchestrator()
            
            result = gh.create_branch(
                branch_name=branch_name,
                checkout=checkout,
                repo_path=workspace_dir
            )
            
            if result.get('ok'):
                msg = f"✅ Branch '{branch_name}' created"
                if checkout:
                    msg += " and checked out"
                return msg
            else:
                return f"❌ Branch creation failed: {result.get('error')}"
        
        except Exception as e:
            return f"❌ Git branch error: {str(e)}"

    tools = [
        read_file, 
        write_file, 
        search_files, 
        execute_code, 
        explain_code, 
        analyze_codebase,
        analyze_semantics,
        search_web,
        git_commit,
        git_push,
        create_pull_request,
        create_branch
    ]

    # Setup storage database
    db = None
    try:
        db = SqliteDb(db_file=db_file) if SqliteDb is not None else None
    except Exception:
        db = None

    # Setup Knowledge base with ChromaDB and NVIDIA Embeddings
    knowledge = None
    try:
        if Knowledge is not None and ChromaDb is not None:
            # Import custom NVIDIA embedder
            try:
                from .nvidia_embedder import NvidiaEmbedder
                
                chroma_path = os.getenv("CHROMA_PERSIST_DIR", "./tmp/chroma")
                embed_model = os.getenv("NVIDIA_EMBED_MODEL", "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1")
                
                print(f"🔄 Initializing Knowledge base with NVIDIA embeddings...")
                print(f"   Embed model: {embed_model}")
                print(f"   ChromaDB path: {chroma_path}")
                
                # Create NVIDIA embedder with extra_body support for input_type
                embedder = NvidiaEmbedder(id=embed_model, enable_batch=True)
                
                # Create vector database with NVIDIA embeddings
                vector_db = ChromaDb(
                    collection=chroma_collection,
                    path=chroma_path,
                    persistent_client=True,
                    embedder=embedder,
                )
                
                # Create knowledge base
                knowledge = Knowledge(
                    name="Helix Code Knowledge",
                    description="Code context and documentation for Helix assistant",
                    vector_db=vector_db,
                )
                
                print(f"✅ Knowledge base initialized with NVIDIA embeddings")
                
            except ImportError as e:
                print(f"⚠️ Could not import NvidiaEmbedder: {e}")
                knowledge = None
    except Exception as e:
        print(f"⚠️ Could not initialize knowledge base: {e}")
        import traceback
        print(traceback.format_exc())
        knowledge = None

    # Get NVIDIA API key
    nvidia_api_key = os.getenv("NVIDIA_API_KEY")
    
    # Create NVIDIA model (required - no fallback)
    if Nvidia is None:
        raise RuntimeError("NVIDIA model class not available. Please install: pip install agno[nvidia]")
    
    if not nvidia_api_key:
        raise RuntimeError("NVIDIA_API_KEY is required but not set in .env file")
    
    model_id = os.getenv("NVIDIA_MODEL_ID", "nvidia/llama-3_1-nemotron-nano-8b-v1")
    base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    print(f"🔄 Initializing NVIDIA model: {model_id}")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {nvidia_api_key[:20]}...")
    
    try:
        # Use our custom wrapper to filter empty messages
        model = NvidiaModelWrapper(
            id=model_id,
            api_key=nvidia_api_key,
            base_url=base_url
        )
        print(f"✅ Successfully initialized NVIDIA model with empty message filter: {model_id}")
    except Exception as e:
        import traceback
        print(f"❌ Failed to initialize NVIDIA model: {e}")
        print(f"   Full error traceback:")
        print(traceback.format_exc())
        raise RuntimeError(f"NVIDIA model initialization failed: {e}")

    # Initialize safety manager
    safety_mgr = get_safety_manager(mode=SafetyMode.NORMAL)
    
    # Create agent with RAG-enabled knowledge base
    print("✅ Creating Agno-powered Helix AI Code Orchestrator with full autonomy...")
    
    agent = Agent(
        name=name,
        model=model,
        knowledge=knowledge,  # Enable RAG with NVIDIA embeddings
        search_knowledge=False,  # Disable auto-search to avoid empty message bug
        tools=tools,  # 12 powerful tools for autonomous operations
        markdown=False,
        debug_mode=True,  # Enable debug logging to see message content
        instructions=[
            "You are Helix, an AI coding assistant powered by NVIDIA NIM.",
            "ALWAYS respond in clear, professional English only.",
            "",
            "YOUR CAPABILITIES:",
            "- Analyze code with analyze_codebase() or analyze_semantics()",
            "- Read/write files with read_file() and write_file()",
            "- Search the web with search_web()",
            "- Git operations: git_commit(), git_push(), create_branch()",
            "- Execute code with execute_code()",
            "",
            "🛠️ AVAILABLE TOOLS (use proactively):",
            "",
            "📊 CODE ANALYSIS:",
            "- analyze_codebase(): Quick scan of all files, detect issues, recommend fixes",
            "- analyze_semantics(): Deep analysis - dependencies, circular imports, vulnerabilities, complexity",
            "- read_file(path): Read specific files",
            "- search_files(query): Search for patterns across files",
            "",
            "📝 FILE OPERATIONS:",
            "- write_file(path, content): Create or update files (asks confirmation first time)",
            "- execute_code(code): Test code snippets safely",
            "",
            "🌐 WEB INTELLIGENCE:",
            "- search_web(query, search_type): Search for docs, solutions, best practices",
            "  search_type: 'docs' (technical), 'code', 'error' (solutions), 'general'",
            "  Example: search_web('FastAPI async database', 'docs')",
            "",
            "🔧 GITHUB AUTOMATION:",
            "- git_commit(message, add_all): Commit changes with message",
            "- git_push(remote, branch): Push to remote repository",
            "- create_branch(name, checkout): Create and switch to new branch",
            "- create_pull_request(owner, repo, title, head, base, description): Automated PR creation",
            "",
            "💡 INTELLIGENT WORKFLOWS:",
            "",
            "WHEN ASKED TO 'ANALYZE' or 'REVIEW CODE':",
            "1. Run analyze_codebase() for quick overview",
            "2. If security/complexity concerns: Run analyze_semantics()",
            "3. Summarize findings with priorities (Critical → High → Medium → Low)",
            "4. Provide actionable recommendations with code examples",
            "",
            "WHEN ASKED TO 'IMPLEMENT' or 'BUILD FEATURE':",
            "1. Analyze existing codebase structure (analyze_codebase)",
            "2. Search for best practices if unsure: search_web('technology best practices', 'docs')",
            "3. Generate code following project patterns",
            "4. Write files using write_file()",
            "5. Offer to commit changes: git_commit('feat: description')",
            "",
            "",
            "HOW TO RESPOND:",
            "- Be concise and helpful",
            "- Respond in English only - no other languages",
            "- Use tools when needed",
            "- Ask for confirmation before destructive operations",
            "- Provide clear explanations",
        ],
        description="Agno-powered Helix AI Code Orchestrator - Autonomous coding assistant with NVIDIA NIM"
    )

    return agent
