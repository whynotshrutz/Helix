#!/bin/bash
# Comprehensive installation script for EC2

echo "🔧 Helix Backend - Dependency Installation"
echo "================================================"

# Check Python version
echo -e "\n1️⃣ Checking Python version..."
python3 --version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "   Python version: $PYTHON_VERSION"

if (( $(echo "$PYTHON_VERSION < 3.9" | bc -l) )); then
    echo "   ⚠️  Python 3.9+ required, found $PYTHON_VERSION"
fi

# Upgrade pip
echo -e "\n2️⃣ Upgrading pip..."
pip3 install --upgrade pip setuptools wheel

# Check if phidata exists on PyPI
echo -e "\n3️⃣ Searching for phidata package on PyPI..."
pip3 search phidata 2>/dev/null || echo "   (pip search disabled, proceeding with installation)"

# Try installing phidata
echo -e "\n4️⃣ Attempting to install phidata..."
pip3 install phidata

if [ $? -eq 0 ]; then
    echo "   ✅ phidata installed"
    python3 -c "import phi; print(f'   Version: {phi.__version__}')"
else
    echo "   ❌ phidata installation failed"
    echo ""
    echo "   Trying alternative package names..."
    
    # Try agno
    echo -e "\n   Trying 'agno'..."
    pip3 install agno
    
    if [ $? -eq 0 ]; then
        echo "   ✅ agno installed"
        python3 -c "import agno; print(f'   Version: {agno.__version__}')"
    else
        echo "   ❌ agno installation failed"
        
        # Try phi
        echo -e "\n   Trying 'phi'..."
        pip3 install phi
        
        if [ $? -eq 0 ]; then
            echo "   ✅ phi installed"
        else
            echo "   ❌ phi installation failed"
            
            # Try phidata from GitHub
            echo -e "\n   Trying installation from GitHub..."
            pip3 install git+https://github.com/phidatahq/phidata.git
        fi
    fi
fi

# Install all other requirements
echo -e "\n5️⃣ Installing other requirements..."
pip3 install fastapi uvicorn httpx python-dotenv pydantic chromadb rich async-timeout requests beautifulsoup4 pytest pytest-asyncio

# Verify key imports
echo -e "\n6️⃣ Verifying imports..."
python3 << 'EOF'
import sys

packages = [
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
    ("httpx", "HTTPX"),
    ("chromadb", "ChromaDB"),
]

print("\nCore packages:")
for pkg, name in packages:
    try:
        __import__(pkg)
        print(f"   ✅ {name}")
    except ImportError:
        print(f"   ❌ {name}")

# Check for phi/phidata/agno
print("\nAgent framework:")
found = False

try:
    import phi
    print(f"   ✅ phi (version: {getattr(phi, '__version__', 'unknown')})")
    found = True
except ImportError:
    pass

try:
    import phidata
    print(f"   ✅ phidata (version: {getattr(phidata, '__version__', 'unknown')})")
    found = True
except ImportError:
    pass

try:
    import agno
    print(f"   ✅ agno (version: {getattr(agno, '__version__', 'unknown')})")
    found = True
except ImportError:
    pass

if not found:
    print("   ❌ No agent framework found (phi/phidata/agno)")
    print("\n   📌 Manual installation required:")
    print("   pip3 install phidata")
    print("   OR")
    print("   pip3 install git+https://github.com/phidatahq/phidata.git")

# Test specific imports
if found:
    print("\nAgent components:")
    try:
        from phi.agent import Agent
        print("   ✅ phi.agent.Agent")
    except ImportError:
        try:
            from agno.agent import Agent
            print("   ✅ agno.agent.Agent")
        except ImportError:
            print("   ❌ Agent class not found")
    
    try:
        from phi.models.nvidia import Nvidia
        print("   ✅ phi.models.nvidia.Nvidia")
    except ImportError:
        try:
            from agno.models.nvidia import Nvidia
            print("   ✅ agno.models.nvidia.Nvidia")
        except ImportError:
            print("   ❌ Nvidia model not found")
EOF

echo -e "\n================================================"
echo "📊 Installation Summary"
echo "================================================"

echo -e "\nInstalled packages:"
pip3 list | grep -E "(phi|agno|fastapi|uvicorn|chromadb)"

echo -e "\n================================================"
echo "✅ Setup complete!"
echo ""
echo "📌 Next steps:"
echo "   1. Set environment variable: export NVIDIA_API_KEY='your-key'"
echo "   2. cd ~/Helix/backend"
echo "   3. python3 run_server.py"
echo ""
