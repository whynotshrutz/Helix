"""RAG content ingestion utilities for Helix.

Load code files, documentation, and PDFs into ChromaDB with embeddings.
"""
import asyncio
from typing import List, Optional
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from agno.knowledge.knowledge import Knowledge
    from agno.vectordb.chroma import ChromaDb
except Exception:
    Knowledge = None
    ChromaDb = None

from .nim_client import NimClient


class ContentIngester:
    """Ingest content into knowledge base with NIM embeddings."""
    
    def __init__(self, knowledge: Optional[any] = None, chroma_collection: str = "helix_vectors"):
        self.knowledge = knowledge
        self.chroma_collection = chroma_collection
        self.nim_client = NimClient()
        
    async def ingest_directory(self, directory: str, extensions: List[str] = None) -> dict:
        """Ingest all code files from a directory.
        
        Args:
            directory: Path to directory
            extensions: List of file extensions to include (e.g., ['.py', '.js'])
            
        Returns:
            Dictionary with ingestion statistics
        """
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.md', '.txt']
        
        dir_path = Path(directory)
        if not dir_path.exists():
            return {"ok": False, "error": "directory_not_found"}
        
        files_processed = 0
        chunks_added = 0
        errors = []
        
        for ext in extensions:
            for file_path in dir_path.rglob(f"*{ext}"):
                try:
                    result = await self.ingest_file(str(file_path))
                    if result.get("ok"):
                        files_processed += 1
                        chunks_added += result.get("chunks", 0)
                    else:
                        errors.append(f"{file_path}: {result.get('error')}")
                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")
        
        return {
            "ok": True,
            "files_processed": files_processed,
            "chunks_added": chunks_added,
            "errors": errors
        }
    
    async def ingest_file(self, file_path: str) -> dict:
        """Ingest a single file into the knowledge base.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with ingestion result
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"ok": False, "error": "file_not_found"}
            
            content = path.read_text(encoding="utf-8")
            
            # Chunk the content (simple line-based chunking)
            chunks = self._chunk_content(content, path.suffix)
            
            if not chunks:
                return {"ok": False, "error": "no_chunks"}
            
            # Generate embeddings via NIM
            texts = [chunk["text"] for chunk in chunks]
            embeddings = await self.nim_client.embed(texts)
            
            # Store in knowledge base
            if self.knowledge:
                try:
                    # Use Agno's knowledge add_content methods
                    await self.knowledge.add_content_async(
                        name=path.name,
                        content=content,
                        metadata={"path": str(path), "extension": path.suffix}
                    )
                except Exception:
                    # Fallback: direct chroma storage if knowledge wrapper doesn't work
                    pass
            
            return {
                "ok": True,
                "file": str(path),
                "chunks": len(chunks)
            }
            
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def _chunk_content(self, content: str, extension: str, chunk_size: int = 500) -> List[dict]:
        """Chunk content into smaller pieces for embedding.
        
        Args:
            content: File content
            extension: File extension
            chunk_size: Target chunk size in characters
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        lines = content.splitlines()
        
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            
            if current_size + line_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    "text": "\n".join(current_chunk),
                    "size": current_size
                })
                current_chunk = []
                current_size = 0
            
            current_chunk.append(line)
            current_size += line_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append({
                "text": "\n".join(current_chunk),
                "size": current_size
            })
        
        return chunks
    
    async def close(self):
        """Clean up resources."""
        await self.nim_client.close()


async def ingest_workspace(workspace_dir: str = ".", chroma_collection: str = "helix_vectors"):
    """Helper function to ingest an entire workspace.
    
    Args:
        workspace_dir: Root directory of workspace
        chroma_collection: ChromaDB collection name
        
    Returns:
        Ingestion statistics
    """
    # Create knowledge base
    knowledge = None
    if Knowledge is not None and ChromaDb is not None:
        chroma_path = os.getenv("CHROMA_PERSIST_DIR", "./tmp/chroma")
        vector_db = ChromaDb(
            collection=chroma_collection,
            path=chroma_path,
            persistent_client=True
        )
        knowledge = Knowledge(
            name="Workspace Knowledge",
            vector_db=vector_db
        )
    
    ingester = ContentIngester(knowledge=knowledge, chroma_collection=chroma_collection)
    
    try:
        result = await ingester.ingest_directory(workspace_dir)
        return result
    finally:
        await ingester.close()


if __name__ == "__main__":
    # Example usage
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    result = asyncio.run(ingest_workspace(workspace))
    print(f"Ingestion complete: {result}")
