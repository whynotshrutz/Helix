# 🚀 Helix VS Code Extension - Deployment Guide

## 📦 Quick Deploy (You Already Have the .vsix!)

You already have `helix-mcp-client-0.1.0.vsix` - here's how to install it:

### **Method 1: Install from VSIX File (Recommended)**

```bash
# 1. Open VS Code
# 2. Press Ctrl+Shift+P (Cmd+Shift+P on Mac)
# 3. Type: "Extensions: Install from VSIX"
# 4. Select: helix-mcp-client-0.1.0.vsix
```

OR via command line:
```bash
code --install-extension vscode-extension/helix-mcp-client-0.1.0.vsix
```

### **Method 2: Install in VS Code Marketplace (Public Release)**

Follow these steps to publish to VS Code Marketplace:

---

## 🔧 Step 1: Update Configuration for Production

Before publishing, update the backend URL in `package.json`:

```json
{
  "helix.backendUrl": {
    "default": "http://your-ec2-public-ip:8001"
  }
}
```

Or users can configure it in VS Code settings after installation.

---

## 📝 Step 2: Create Publisher Account

1. **Go to Azure DevOps**: https://dev.azure.com
2. **Sign in** with Microsoft account
3. **Create Personal Access Token**:
   - Click user icon (top right) → **Personal Access Tokens**
   - Click **+ New Token**
   - Name: `vsce-publisher`
   - Organization: **All accessible organizations**
   - Scopes: **Custom defined** → Check **Marketplace (Manage)**
   - Click **Create** and **COPY THE TOKEN** (save it securely!)

4. **Create Publisher** (one-time):
   - Go to https://marketplace.visualstudio.com/manage
   - Click **Create Publisher**
   - Publisher ID: `helix-ai` (or your choice - this will be in the extension URL)
   - Display name: `Helix AI Team`
   - Click **Create**

---

## 🛠️ Step 3: Build and Package Extension

```bash
# 1. Go to extension directory
cd vscode-extension

# 2. Install dependencies
npm install

# 3. Install vsce (VS Code Extension Manager)
npm install -g @vscode/vsce

# 4. Build the extension
npm run build

# 5. Update version (if needed)
# Edit package.json and change "version": "1.0.1"

# 6. Package the extension
vsce package
# This creates: helix-mcp-client-1.0.0.vsix
```

---

## 📤 Step 4: Publish to Marketplace

### **Option A: Publish via Command Line**

```bash
# 1. Login with your publisher
vsce login helix-ai
# Enter the Personal Access Token when prompted

# 2. Publish the extension
vsce publish
# Or publish with version bump:
vsce publish patch  # 1.0.0 → 1.0.1
vsce publish minor  # 1.0.0 → 1.1.0
vsce publish major  # 1.0.0 → 2.0.0
```

### **Option B: Publish via Web UI**

```bash
# 1. Package the extension
vsce package

# 2. Go to marketplace manager
# https://marketplace.visualstudio.com/manage/publishers/helix-ai

# 3. Click "+ New Extension" → "Visual Studio Code"

# 4. Upload the .vsix file

# 5. Fill in details and publish
```

---

## 🎯 Step 5: Update Extension Settings

After users install the extension, they need to configure the backend URL:

1. **Open VS Code Settings** (Ctrl+,)
2. Search for: `helix.backendUrl`
3. Set to: `http://your-ec2-ip:8001`

Or create a `.vscode/settings.json` in workspace:
```json
{
  "helix.backendUrl": "http://your-ec2-ip:8001"
}
```

---

## 🔒 Step 6: Configure EC2 Security

Make sure your EC2 instance allows connections:

```bash
# 1. Open port 8001 in EC2 Security Group
# AWS Console → EC2 → Security Groups → Add Inbound Rule:
# Type: Custom TCP
# Port: 8001
# Source: 0.0.0.0/0 (or specific IPs)

# 2. Make sure backend is running on 0.0.0.0 (not 127.0.0.1)
# In .env file:
HELIX_BIND_HOST=0.0.0.0
HELIX_BIND_PORT=8001
```

---

## 📊 Quick Installation Commands

### **For Local Testing:**
```bash
# Build extension
cd vscode-extension
npm install
npm run build
vsce package

# Install locally
code --install-extension helix-mcp-client-1.0.0.vsix
```

### **For Production Release:**
```bash
# Login to marketplace
vsce login your-publisher-id

# Publish
vsce publish

# Or publish with automatic version bump
vsce publish patch
```

---

## 🌐 After Publishing

Your extension will be available at:
```
https://marketplace.visualstudio.com/items?itemName=helix-ai.helix-mcp-client
```

Users can install it:
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Helix AI Assistant"
4. Click Install

---

## 🎨 Optional: Add Extension Icon

1. Create a 128x128 PNG icon named `icon.png`
2. Place it in `vscode-extension/` directory
3. Rebuild and republish

---

## 🔄 Update Extension

When you make changes:

```bash
# 1. Update code
# 2. Bump version in package.json
# 3. Build and publish
npm run build
vsce publish patch
```

Users will get automatic updates in VS Code!

---

## 📝 Important Files Checklist

Before publishing, make sure you have:

- ✅ `package.json` - Extension metadata
- ✅ `README.md` - Extension documentation
- ✅ `LICENSE` - License file (MIT)
- ✅ `icon.png` - Extension icon (128x128)
- ✅ `CHANGELOG.md` - Version history (optional but recommended)
- ✅ `.vscodeignore` - Files to exclude from package

---

## 🐛 Troubleshooting

### **Extension doesn't load:**
- Check VS Code version compatibility in `package.json` engines
- Check console: Help → Toggle Developer Tools

### **Can't connect to backend:**
- Verify backend URL in settings
- Check EC2 security group allows port 8001
- Test: `curl http://your-ec2-ip:8001/health`

### **Publishing fails:**
- Verify Personal Access Token is valid
- Check publisher ID matches
- Ensure all required fields in package.json are filled

---

## 🎯 Summary

**Quick Install (Already Built):**
```bash
code --install-extension vscode-extension/helix-mcp-client-0.1.0.vsix
```

**Rebuild and Install:**
```bash
cd vscode-extension
npm install
npm run build
vsce package
code --install-extension helix-mcp-client-1.0.0.vsix
```

**Publish to Marketplace:**
```bash
npm install -g @vscode/vsce
vsce login your-publisher-id
vsce publish
```

Done! 🚀
