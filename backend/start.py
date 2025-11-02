#!/usr/bin/env python3
"""
Helix Startup Script
Quick validation and startup for the Helix backend.
"""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Ensure Python 3.11+"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        sys.exit(1)
    print("✅ Python version OK")


def check_dependencies():
    """Check if dependencies are installed"""
    try:
        import agno
        print("✅ Agno SDK installed")
    except ImportError:
        print("❌ Agno SDK not found. Run: pip install -r requirements.txt")
        return False
    
    try:
        import fastapi
        import uvicorn
        import httpx
        print("✅ Web dependencies installed")
    except ImportError:
        print("❌ FastAPI dependencies missing. Run: pip install -r requirements.txt")
        return False
    
    try:
        import chromadb
        print("✅ ChromaDB installed")
    except ImportError:
        print("⚠️  ChromaDB not installed (optional for RAG)")
    
    return True


def check_env_file():
    """Check if .env file exists"""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("⚠️  .env file not found. Copy from .env.example")
        return False
    
    # Check for NVIDIA_API_KEY
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("NVIDIA_API_KEY"):
        print("⚠️  NVIDIA_API_KEY not set in .env")
        return False
    
    print("✅ Environment configured")
    return True


def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Docker available: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  Docker not found (code executor will use local fallback)")
    return False


def start_backend(mode="local"):
    """Start the backend server"""
    print(f"\n🚀 Starting Helix backend in {mode} mode...\n")
    
    if mode == "docker":
        cmd = ["docker-compose", "up", "-d"]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)
        print("\n✅ Backend started with Docker")
        print("   - Backend: http://localhost:8000")
        print("   - Executor: http://localhost:8888")
        print("\nView logs: docker-compose logs -f")
    else:
        # Add src directory to Python path
        src_dir = Path(__file__).parent / "src"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(src_dir) + os.pathsep + env.get("PYTHONPATH", "")
        
        cmd = [
            "python", "-m", "uvicorn",
            "helix.server:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ]
        print(f"Running: {' '.join(cmd)}")
        print("\n✅ Backend starting...")
        print("   - Backend: http://localhost:8000")
        print("   - Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop\n")
        subprocess.run(cmd, env=env)


def main():
    print("=" * 60)
    print("Helix Backend Startup")
    print("=" * 60)
    print()
    
    # Run checks
    check_python_version()
    deps_ok = check_dependencies()
    env_ok = check_env_file()
    docker_available = check_docker()
    
    print()
    
    if not deps_ok:
        print("\n❌ Dependencies missing. Please run:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    if not env_ok:
        print("\n⚠️  Environment not fully configured.")
        print("   Backend will start but agent may not work.")
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Choose mode
    if docker_available:
        print("\nStart with Docker or locally?")
        print("  1. Docker (recommended)")
        print("  2. Local development")
        choice = input("\nChoice (1/2): ").strip()
        
        if choice == "1":
            start_backend("docker")
        else:
            start_backend("local")
    else:
        start_backend("local")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
