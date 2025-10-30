"""Script to populate the knowledge base with workspace code files."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from helix.agno_agent import create_agent


def add_workspace_files_to_knowledge(workspace_dir: str = "."):
    """Add all code files from workspace to the knowledge base.
    
    Args:
        workspace_dir: Path to workspace directory
    """
    print(f"📂 Scanning workspace: {workspace_dir}")
    
    # Create agent (which initializes knowledge base)
    agent = create_agent(workspace_dir=workspace_dir)
    
    if agent.knowledge is None:
        print("❌ Knowledge base not initialized. Check embedder configuration.")
        return
    
    # File extensions to index
    code_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
        '.html', '.css', '.scss', '.json', '.yaml', '.yml', '.md', '.txt'
    }
    
    workspace_path = Path(workspace_dir)
    files_added = 0
    
    # Scan for code files
    for file_path in workspace_path.rglob('*'):
        # Skip directories, hidden files, and non-code files
        if file_path.is_dir() or file_path.name.startswith('.'):
            continue
        
        # Skip node_modules, venv, etc.
        if any(part.startswith('.') or part in ['node_modules', 'venv', '__pycache__', 'dist', 'build'] 
               for part in file_path.parts):
            continue
        
        # Check if it's a code file
        if file_path.suffix.lower() in code_extensions:
            try:
                # Read file content
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Skip empty files
                if not content.strip():
                    continue
                
                # Add to knowledge base with metadata
                relative_path = file_path.relative_to(workspace_path)
                print(f"  📄 Adding: {relative_path}")
                
                agent.knowledge.add_content(
                    text_content=content,
                    metadata={
                        'file_path': str(relative_path),
                        'file_name': file_path.name,
                        'file_type': file_path.suffix,
                        'language': _get_language(file_path.suffix)
                    }
                )
                
                files_added += 1
                
            except Exception as e:
                print(f"  ⚠️ Error adding {file_path}: {e}")
    
    print(f"\n✅ Added {files_added} files to knowledge base")
    print(f"📊 Knowledge base ready for RAG queries")


def _get_language(extension: str) -> str:
    """Map file extension to language name."""
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'react',
        '.tsx': 'react-typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c-header',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
    }
    return lang_map.get(extension.lower(), 'text')


if __name__ == "__main__":
    # Get workspace directory from environment or use default
    workspace_dir = os.getenv("WORKSPACE_DIR", "../workspace")
    
    print("🚀 Helix Knowledge Base Indexer")
    print("=" * 50)
    
    add_workspace_files_to_knowledge(workspace_dir)
    
    print("\n💡 Knowledge base is now ready!")
    print("   Start the server and the agent will use this context for better suggestions.")
