#!/bin/bash
# Script to set up .env file on EC2 instance

echo "🔧 Setting up Helix .env file..."
echo "================================================"

# Create .env file
cat > /home/ubuntu/Helix/backend/.env << 'EOF'
# Helix Backend Environment Variables

# NVIDIA API Configuration (REQUIRED)
NVIDIA_API_KEY=your-nvidia-api-key-here
NVIDIA_MODEL_ID=nvidia/llama-3.1-nemotron-70b-instruct
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

# Workspace Configuration
WORKSPACE_DIR=/home/ubuntu/Helix/workspace

# GitHub Configuration (Optional - for Git operations)
GITHUB_TOKEN=your-github-token-here

# Server Configuration
HOST=0.0.0.0
PORT=8001

# Database Configuration
CHROMA_DB_PATH=./tmp/chroma

# Logging
LOG_LEVEL=INFO
EOF

echo "✅ .env file created at: /home/ubuntu/Helix/backend/.env"
echo ""
echo "⚠️  IMPORTANT: Update the following values:"
echo "   1. NVIDIA_API_KEY - Get from: https://build.nvidia.com/explore/discover"
echo "   2. GITHUB_TOKEN - Get from: https://github.com/settings/tokens"
echo ""
echo "📝 Edit the file:"
echo "   nano /home/ubuntu/Helix/backend/.env"
echo ""
echo "🔒 Set secure permissions:"
chmod 600 /home/ubuntu/Helix/backend/.env
echo "   ✅ Permissions set to 600 (owner read/write only)"
echo ""
echo "================================================"
