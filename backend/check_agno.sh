#!/bin/bash
# Quick diagnostic script for EC2

echo "🔍 Checking Agno SDK Installation..."
echo "================================================"

echo -e "\n1️⃣ Python version:"
python3 --version

echo -e "\n2️⃣ Pip version:"
pip3 --version

echo -e "\n3️⃣ Searching for 'agno' package:"
pip3 list | grep -i agno

echo -e "\n4️⃣ Searching for 'phi' package (alternative name):"
pip3 list | grep -i phi

echo -e "\n5️⃣ All installed packages:"
pip3 list

echo -e "\n6️⃣ Trying to import agno:"
python3 -c "import agno; print(f'✅ Agno version: {agno.__version__}')" 2>&1

echo -e "\n7️⃣ Trying alternative import (phidata):"
python3 -c "import phi; print(f'✅ Phi version: {phi.__version__}')" 2>&1

echo -e "\n8️⃣ Checking if it's phidata instead of agno:"
python3 -c "from phi.agent import Agent; print('✅ phi.agent.Agent found')" 2>&1

echo -e "\n================================================"
echo "💡 If 'agno' not found but 'phi' is found, the package might be 'phidata'"
