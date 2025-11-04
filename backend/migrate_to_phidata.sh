#!/bin/bash
# Migration script to update from agno to phidata
# Run this on your EC2 instance

echo "🔄 Migrating from Agno SDK to Phidata..."
echo "================================================"

# Step 1: Uninstall old package
echo -e "\n1️⃣ Uninstalling old agno package (if exists)..."
pip3 uninstall -y agno 2>/dev/null || echo "   agno not installed (OK)"

# Step 2: Install phidata
echo -e "\n2️⃣ Installing phidata>=2.0.0..."
pip3 install "phidata>=2.0.0"

if [ $? -eq 0 ]; then
    echo "   ✅ phidata installed successfully"
else
    echo "   ❌ Failed to install phidata"
    exit 1
fi

# Step 3: Verify installation
echo -e "\n3️⃣ Verifying installation..."
python3 -c "import phi; print(f'✅ Phidata version: {phi.__version__}')"

if [ $? -eq 0 ]; then
    echo "   ✅ Import successful"
else
    echo "   ❌ Import failed"
    exit 1
fi

# Step 4: Test key imports
echo -e "\n4️⃣ Testing key imports..."
python3 << EOF
try:
    from phi.agent import Agent
    print("   ✅ phi.agent.Agent")
except ImportError as e:
    print(f"   ❌ phi.agent.Agent: {e}")

try:
    from phi.models.nvidia import Nvidia
    print("   ✅ phi.models.nvidia.Nvidia")
except ImportError as e:
    print(f"   ❌ phi.models.nvidia.Nvidia: {e}")

try:
    from phi.tools import tool
    print("   ✅ phi.tools.tool")
except ImportError as e:
    print(f"   ❌ phi.tools.tool: {e}")

try:
    from phi.storage.agent.sqlite import SqlAgentStorage
    print("   ✅ phi.storage.agent.sqlite.SqlAgentStorage")
except ImportError as e:
    print(f"   ❌ phi.storage.agent.sqlite.SqlAgentStorage: {e}")

try:
    from phi.vectordb.chroma import ChromaDb
    print("   ✅ phi.vectordb.chroma.ChromaDb")
except ImportError as e:
    print(f"   ❌ phi.vectordb.chroma.ChromaDb: {e}")
EOF

# Step 5: Pull latest code
echo -e "\n5️⃣ Pulling latest code from GitHub..."
cd ~/Helix
git pull origin main

if [ $? -eq 0 ]; then
    echo "   ✅ Code updated"
else
    echo "   ⚠️  Git pull failed (may need to resolve conflicts)"
fi

# Step 6: Restart server
echo -e "\n6️⃣ Restarting server..."
echo "   Run: cd ~/Helix/backend && python3 run_server.py"

echo -e "\n================================================"
echo "✅ Migration complete!"
echo ""
echo "📌 Next steps:"
echo "   1. cd ~/Helix/backend"
echo "   2. python3 run_server.py"
echo "   3. Check health: curl http://localhost:8001/health"
echo ""
