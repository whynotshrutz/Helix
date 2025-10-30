"""Integration tests for Helix backend."""
import pytest
import httpx
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.mark.asyncio
async def test_backend_health():
    """Test that backend starts and responds to health checks."""
    # Note: This requires the backend to be running
    # Skip if not available
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/docs")
            assert resp.status_code == 200
    except httpx.ConnectError:
        pytest.skip("Backend not running")


@pytest.mark.asyncio
async def test_run_endpoint():
    """Test the /run endpoint with a simple prompt."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://localhost:8000/run",
                json={"prompt": "Hello", "mode": "chat", "stream": False},
                timeout=30.0
            )
            if resp.status_code == 503:
                pytest.skip("Agent not available (dependencies missing)")
            
            assert resp.status_code == 200
            data = resp.json()
            assert "content" in data or "error" in data
    except httpx.ConnectError:
        pytest.skip("Backend not running")


@pytest.mark.asyncio
async def test_streaming_endpoint():
    """Test the /run endpoint with streaming enabled."""
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "http://localhost:8000/run",
                json={"prompt": "Count to 3", "mode": "chat", "stream": True},
                timeout=30.0
            ) as resp:
                if resp.status_code == 503:
                    pytest.skip("Agent not available")
                
                assert resp.status_code == 200
                
                events = []
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            import json
                            try:
                                events.append(json.loads(data))
                            except json.JSONDecodeError:
                                pass
                
                # Should have received some events
                assert len(events) > 0
    except httpx.ConnectError:
        pytest.skip("Backend not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
