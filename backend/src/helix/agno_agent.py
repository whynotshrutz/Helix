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
except Exception as e:  # pragma: no cover - agno optional for scaffolding
    Agent = None
    Nvidia = None
    tool = None
    SqliteDb = None
    Knowledge = None
    ChromaDb = None

from .tools import file_reader_tool, code_executor_tool, search_tool, doc_helper_tool


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

    tools = [read_file, write_file, search_files, execute_code, explain_code]

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
        model = Nvidia(
            id=model_id,
            api_key=nvidia_api_key,
            base_url=base_url
        )
        print(f"✅ Successfully initialized NVIDIA model: {model_id}")
    except Exception as e:
        import traceback
        print(f"❌ Failed to initialize NVIDIA model: {e}")
        print(f"   Full error traceback:")
        print(traceback.format_exc())
        raise RuntimeError(f"NVIDIA model initialization failed: {e}")

    # Create agent with RAG-enabled knowledge base
    print("✅ Creating agent with NVIDIA model and RAG knowledge base...")
    
    agent = Agent(
        name=name,
        model=model,
        knowledge=knowledge,  # Enable RAG with NVIDIA embeddings
        search_knowledge=True,  # Automatically search knowledge base for context
        # tools=tools,  # Tools disabled to avoid empty message bug
        markdown=False,
        instructions=[
            "You are Helix, an AI coding assistant with RAG capabilities.",
            "You have access to a knowledge base with code context from the workspace.",
            "Use the knowledge base to provide better, context-aware suggestions.",
            "INLINE MODE: If the prompt says 'Complete the following' or 'Complete this line':",
            "- Return ONLY the code completion, no explanations, no markdown",
            "- Continue naturally from where the code left off",
            "- Use workspace context from knowledge base when relevant",
            "CHAT MODE: When asked to write, create, or generate complete files:",
            "- Search knowledge base for relevant code patterns and context",
            "- Output in this exact format:",
            "  CREATE_FILE: filename.ext",
            "  ```language",
            "  code here",
            "  ```",
            "Always generate idiomatic, clean code with comments.",
        ],
        description="AI coding assistant with RAG"
    )

    return agent
