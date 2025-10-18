```bash
#!/bin/bash
# Run Helix locally with environment setup

set -e

echo "🚀 Starting Helix Locally"
echo "========================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded .env file"
else
    echo "⚠️  No .env file found. Using system environment variables."
fi

# Check for required variables
if [ -z "$GH_TOKEN" ] && [ -z "$GH_OAUTH_TOKEN" ]; then
    echo "❌ Error: GH_TOKEN or GH_OAUTH_TOKEN must be set"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Activated virtual environment"
fi

# Run Helix
echo ""
echo "Starting Helix interactive mode..."
echo ""
python -m helix.cli --start