#!/bin/bash
# Quick build and package script for Helix VS Code Extension

set -e

echo "🏗️  Building Helix VS Code Extension..."
echo ""

cd vscode-extension

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build TypeScript
echo "🔨 Building TypeScript..."
npm run build

# Install vsce if not present
if ! command -v vsce &> /dev/null; then
    echo "📥 Installing vsce..."
    npm install -g vsce
fi

# Package extension
echo "📦 Packaging extension..."
vsce package

echo ""
echo "✅ Extension packaged successfully!"
echo ""
ls -lh *.vsix
echo ""
echo "📝 To install:"
echo "   code --install-extension helix-mcp-client-*.vsix"
echo ""
echo "📝 To distribute:"
echo "   Share the .vsix file with users"
echo ""
echo "📝 To publish to marketplace:"
echo "   vsce publish"
