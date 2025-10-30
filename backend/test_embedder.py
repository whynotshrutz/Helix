#!/usr/bin/env python3
"""Test the NVIDIA embedder directly."""
import asyncio
import os
from dotenv import load_dotenv
from src.helix.nvidia_embedder import NvidiaEmbedder

load_dotenv()

async def test_embedder():
    embedder = NvidiaEmbedder()
    
    # Test embed() method
    print("\n=== Testing embed() ===")
    texts = ["hello world", "test text"]
    result = await embedder.embed(texts)
    print(f"Result type: {type(result)}")
    print(f"Result length: {len(result)}")
    if result:
        print(f"First embedding type: {type(result[0])}")
        print(f"First embedding dim: {len(result[0])}")
        print(f"First few values: {result[0][:5]}")
    
    # Test async_get_embedding_and_usage
    print("\n=== Testing async_get_embedding_and_usage() ===")
    result2 = await embedder.async_get_embedding_and_usage("test")
    print(f"Result type: {type(result2)}")
    print(f"Result: {result2 if not isinstance(result2, tuple) or len(str(result2)) < 200 else f'(embedding_vec[{len(result2[0])}], usage)'}")
    
    if isinstance(result2, tuple):
        emb, usage = result2
        print(f"Embedding type: {type(emb)}, len: {len(emb)}")
        print(f"Usage: {usage}")

if __name__ == "__main__":
    asyncio.run(test_embedder())
