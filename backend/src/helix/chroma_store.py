"""ChromaDB integration for RAG and memory.

Provides a thin async wrapper around chromadb for vector ingestion and retrieval.
"""
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIR", "./tmp/chroma")

try:
    import chromadb
    from chromadb.config import Settings
except Exception:  # pragma: no cover - chromadb optional in tests
    chromadb = None


class ChromaStore:
    def __init__(self, collection_name: str = "helix_vectors", persist_directory: Optional[str] = None):
        if chromadb is None:
            raise RuntimeError("chromadb is required for ChromaStore. Install with `pip install chromadb`.")

        self.persist_directory = persist_directory or CHROMA_PATH
        settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=self.persist_directory)
        self.client = chromadb.Client(settings=settings)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add(self, ids: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None, documents: Optional[List[str]] = None):
        self.collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas or [{} for _ in ids], documents=documents or ["" for _ in ids])

    def query(self, query_embeddings: List[float], n_results: int = 5):
        result = self.collection.query(query_embeddings=[query_embeddings], n_results=n_results)
        return result

    def persist(self):
        try:
            self.client.persist()
        except Exception:
            pass
