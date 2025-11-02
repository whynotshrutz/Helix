"""
Startup script for Helix backend server.
This handles the Python path setup correctly.
"""
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Now import and run the server
from src.helix.server import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Helix Backend Server...")
    print(f"📂 Backend directory: {backend_dir}")
    print(f"🌐 Server will be available at: http://127.0.0.1:8001")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )
