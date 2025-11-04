#!/usr/bin/env python3
"""Diagnostic script to check Helix dependencies on EC2 instance."""

import sys
import os
from pathlib import Path

print("=" * 70)
print("🔍 HELIX DEPENDENCY DIAGNOSTIC")
print("=" * 70)

print(f"\n📍 Python Version: {sys.version}")
print(f"📍 Python Executable: {sys.executable}")
print(f"📍 Current Directory: {os.getcwd()}")

print("\n" + "=" * 70)
print("1️⃣ CHECKING CORE DEPENDENCIES")
print("=" * 70)

dependencies = [
    ("agno", "Agno SDK - Core AI framework"),
    ("fastapi", "FastAPI - Web framework"),
    ("uvicorn", "Uvicorn - ASGI server"),
    ("httpx", "HTTPX - HTTP client"),
    ("python-dotenv", "python-dotenv - Environment variables", "dotenv"),
    ("pydantic", "Pydantic - Data validation"),
    ("chromadb", "ChromaDB - Vector database"),
    ("rich", "Rich - Terminal formatting"),
    ("requests", "Requests - HTTP library"),
    ("beautifulsoup4", "BeautifulSoup4 - HTML parsing", "bs4"),
]

missing = []
installed = []

for dep in dependencies:
    if len(dep) == 2:
        package_name, description = dep
        import_name = package_name
    else:
        package_name, description, import_name = dep
    
    try:
        __import__(import_name)
        print(f"✅ {package_name}: {description}")
        installed.append(package_name)
    except ImportError:
        print(f"❌ {package_name}: {description} - NOT INSTALLED")
        missing.append(package_name)

print("\n" + "=" * 70)
print("2️⃣ CHECKING AGNO SDK COMPONENTS")
print("=" * 70)

try:
    import agno
    print(f"✅ agno package found")
    print(f"   Location: {agno.__file__}")
    print(f"   Version: {getattr(agno, '__version__', 'unknown')}")
    
    # Check submodules
    agno_components = [
        ("agno.agent", "Agent"),
        ("agno.models.nvidia", "Nvidia"),
        ("agno.tools", "tool"),
        ("agno.db.sqlite", "SqliteDb"),
        ("agno.knowledge.knowledge", "Knowledge"),
        ("agno.vectordb.chroma", "ChromaDb"),
    ]
    
    for module_name, class_name in agno_components:
        try:
            module = __import__(module_name, fromlist=[class_name])
            obj = getattr(module, class_name)
            print(f"   ✅ {module_name}.{class_name}")
        except (ImportError, AttributeError) as e:
            print(f"   ❌ {module_name}.{class_name} - {e}")
    
except ImportError as e:
    print(f"❌ agno package NOT FOUND: {e}")
    print("\n💡 To install Agno SDK:")
    print("   pip install agno>=0.8.0")

print("\n" + "=" * 70)
print("3️⃣ CHECKING ENVIRONMENT VARIABLES")
print("=" * 70)

env_vars = [
    ("NVIDIA_API_KEY", True),
    ("GITHUB_TOKEN", False),
    ("NVIDIA_MODEL_ID", False),
    ("NVIDIA_BASE_URL", False),
    ("WORKSPACE_DIR", False),
]

for var_name, required in env_vars:
    value = os.getenv(var_name)
    if value:
        masked_value = value[:10] + "..." if len(value) > 10 else value
        print(f"✅ {var_name}: {masked_value}")
    else:
        if required:
            print(f"❌ {var_name}: NOT SET (REQUIRED)")
        else:
            print(f"⚠️  {var_name}: NOT SET (optional)")

print("\n" + "=" * 70)
print("4️⃣ CHECKING FILE PATHS")
print("=" * 70)

paths_to_check = [
    "backend/src/helix/multi_agent_system.py",
    "backend/src/helix/server.py",
    "backend/src/helix/tools.py",
    "backend/requirements.txt",
]

for path in paths_to_check:
    if Path(path).exists():
        print(f"✅ {path}")
    else:
        print(f"❌ {path} - NOT FOUND")

print("\n" + "=" * 70)
print("5️⃣ TESTING IMPORTS")
print("=" * 70)

print("\n📦 Testing Helix imports...")

try:
    sys.path.insert(0, os.path.join(os.getcwd(), 'backend', 'src'))
    from helix.multi_agent_system import create_multi_agent_system, AGNO_AVAILABLE, AGNO_ERROR
    
    if AGNO_AVAILABLE:
        print("✅ helix.multi_agent_system imports successfully")
        print("✅ Agno SDK is available")
    else:
        print("❌ helix.multi_agent_system imports but Agno SDK is NOT available")
        print(f"   Error: {AGNO_ERROR}")
except Exception as e:
    print(f"❌ Failed to import helix.multi_agent_system: {e}")

try:
    from helix.server import app
    print("✅ helix.server imports successfully")
except Exception as e:
    print(f"❌ Failed to import helix.server: {e}")

print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)

print(f"\n✅ Installed: {len(installed)}/{len(dependencies)} dependencies")
print(f"❌ Missing: {len(missing)}/{len(dependencies)} dependencies")

if missing:
    print(f"\n💡 To install missing dependencies:")
    print(f"   pip install {' '.join(missing)}")

print("\n" + "=" * 70)
print("🔧 RECOMMENDED ACTIONS")
print("=" * 70)

if "agno" in missing:
    print("\n1️⃣ Install Agno SDK:")
    print("   pip install agno>=0.8.0")
    print("\n   OR if that fails, try:")
    print("   pip install --upgrade pip")
    print("   pip install agno>=0.8.0 --no-cache-dir")

if not os.getenv("NVIDIA_API_KEY"):
    print("\n2️⃣ Set NVIDIA_API_KEY:")
    print("   export NVIDIA_API_KEY='your-api-key'")
    print("   # Get your key from: https://build.nvidia.com")

if missing:
    print("\n3️⃣ Install all requirements:")
    print("   cd backend")
    print("   pip install -r requirements.txt")

print("\n4️⃣ Test the server:")
print("   cd backend")
print("   python run_server.py")
print("   # Or: python -m helix.server")

print("\n5️⃣ Check health endpoint:")
print("   curl http://localhost:8001/health")

print("\n" + "=" * 70)
print("✅ DIAGNOSTIC COMPLETE")
print("=" * 70)
