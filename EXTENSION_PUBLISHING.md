# Helix Extension Publishing & Deployment Guide

This guide covers how to build, package, and distribute the Helix VS Code extension, plus how to deploy the complete system.

## Part 1: Building the VS Code Extension

### Prerequisites

- Node.js 16+ installed
- npm installed
- VS Code Extension Manager (vsce)

### Step 1: Install Dependencies

```bash
cd vscode-extension
npm install
```

### Step 2: Build the Extension

```bash
npm run build
```

This compiles TypeScript to JavaScript in the `out/` directory.

### Step 3: Test Locally

Press **F5** in VS Code to launch Extension Development Host and test the extension.

## Part 2: Packaging the Extension

### Install VSCE

```bash
npm install -g vsce
```

### Create Icon (Optional)

Create a 128x128 PNG icon named `icon.png` in the `vscode-extension/` directory.

### Package Extension

```bash
cd vscode-extension
vsce package
```

This creates: `helix-mcp-client-1.0.0.vsix`

## Part 3: Publishing Options

### Option A: Private Distribution (Recommended for Internal Use)

**1. Share VSIX File**

Distribute the `.vsix` file to users via:
- Email
- Internal file server
- GitHub Releases
- Company intranet

**2. Users Install:**

```bash
# Command line
code --install-extension helix-mcp-client-1.0.0.vsix

# Or in VS Code:
# 1. Ctrl+Shift+P → "Extensions: Install from VSIX..."
# 2. Select the .vsix file
```

### Option B: Publish to VS Code Marketplace (Public)

**1. Create Publisher Account**

Visit: https://marketplace.visualstudio.com/manage

- Sign in with Microsoft account
- Create a publisher ID (replace "helix-dev" in package.json)

**2. Get Personal Access Token**

1. Go to: https://dev.azure.com/
2. User Settings → Personal Access Tokens
3. Create token with:
   - Organization: All accessible organizations
   - Scopes: Marketplace (Manage)
   - Expiration: Custom (1 year recommended)

**3. Login to VSCE**

```bash
vsce login your-publisher-name
# Enter your Personal Access Token
```

**4. Publish**

```bash
cd vscode-extension
vsce publish
```

The extension will be available at:
`https://marketplace.visualstudio.com/items?itemName=your-publisher-name.helix-mcp-client`

### Option C: Publish to Open VSX (VS Codium, etc.)

```bash
npx ovsx publish helix-mcp-client-1.0.0.vsix -p YOUR_ACCESS_TOKEN
```

## Part 4: Complete System Deployment

### Architecture Overview

```
┌──────────────────┐
│  VS Code Users   │
│   (Extension)    │
└────────┬─────────┘
         │
         │ HTTP
         ▼
┌──────────────────┐
│  Load Balancer   │ ← Users configure this URL
│   (AWS ALB)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Helix Backend   │
│  (EKS Cluster)   │
│  - Backend       │
│  - Workers       │
│  - Executors     │
└──────────────────┘
```

### Deployment Steps

#### Step 1: Deploy Backend to AWS EKS

See full guide in `DEPLOYMENT.md`. Quick version:

```bash
# 1. Create EKS cluster (one-time)
eksctl create cluster \
  --name helix-cluster \
  --region us-east-1 \
  --nodegroup-name helix-nodes \
  --node-type t3.medium \
  --nodes 3

# 2. Build and push Docker images
cd Helix
chmod +x scripts/build-and-push.sh
./scripts/build-and-push.sh latest

# 3. Configure secrets
kubectl create secret generic helix-secrets \
  --from-literal=nvidia-api-key='YOUR_NVIDIA_API_KEY' \
  --from-literal=github-token='YOUR_GITHUB_TOKEN'

# 4. Deploy
chmod +x scripts/deploy.sh
./scripts/deploy.sh helix-cluster us-east-1

# 5. Get backend URL
kubectl get service helix-backend-service \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

Example output: `a1234567890.us-east-1.elb.amazonaws.com`

#### Step 2: Update Extension Configuration

**For Users:**

Create a guide for users to configure the extension:

**Quick Setup Guide for Users:**
```markdown
# Helix Setup

1. Install extension:
   - Download helix-mcp-client-1.0.0.vsix
   - In VS Code: Ctrl+Shift+P → "Extensions: Install from VSIX..."

2. Configure backend:
   - Open Settings (Ctrl+,)
   - Search: "Helix"
   - Set "Helix: Backend Url" to: http://YOUR-BACKEND-URL

3. Start using:
   - Click Helix icon in sidebar
   - Start chatting!
```

**Or via Environment Variable:**

```bash
# Add to ~/.bashrc or ~/.zshrc (Linux/Mac)
export HELIX_BACKEND_URL=http://a1234567890.us-east-1.elb.amazonaws.com

# Or to system environment variables (Windows)
setx HELIX_BACKEND_URL "http://a1234567890.us-east-1.elb.amazonaws.com"
```

#### Step 3: Test End-to-End

1. **Install Extension**
   ```bash
   code --install-extension helix-mcp-client-1.0.0.vsix
   ```

2. **Configure Backend URL**
   - Open VS Code Settings
   - Set `helix.backendUrl` to your AWS URL

3. **Test Connection**
   - Open Helix chat panel
   - Send test message: "Hello, are you working?"
   - Should receive AI response

4. **Test Features**
   - File attachment
   - Code generation
   - Git operations
   - Web research

## Part 5: Distribution Strategies

### Strategy 1: Internal Company Distribution

**Setup:**
1. Deploy backend to company AWS/cloud
2. Package extension as .vsix
3. Host .vsix on internal server
4. Distribute setup guide with backend URL

**Pros:**
- Full control over backend
- Private data stays internal
- Can customize for company needs

**Cons:**
- Manual updates required
- Users must configure backend URL

### Strategy 2: SaaS Model (Hosted Backend)

**Setup:**
1. Deploy backend to production AWS
2. Publish extension to VS Code Marketplace
3. Users install from marketplace
4. Extension auto-configured to your backend

**Update package.json:**
```json
{
  "contributes": {
    "configuration": {
      "properties": {
        "helix.backendUrl": {
          "default": "https://api.helix.yourcompany.com"
        }
      }
    }
  }
}
```

**Pros:**
- Easy for users (just install)
- Auto-updates via marketplace
- No user configuration needed

**Cons:**
- You host for all users
- Infrastructure costs
- Need to scale for all users

### Strategy 3: Hybrid (Local + Cloud)

**Setup:**
1. Extension defaults to localhost
2. Users can run backend locally
3. Or configure cloud backend URL

**Best for:**
- Open source projects
- Developer tools
- Privacy-conscious users

## Part 6: Continuous Deployment

### GitHub Actions Workflow for Extension

Create `.github/workflows/publish-extension.yml`:

```yaml
name: Publish Extension

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd vscode-extension
          npm install
      
      - name: Build
        run: |
          cd vscode-extension
          npm run build
      
      - name: Package
        run: |
          cd vscode-extension
          npm install -g vsce
          vsce package
      
      - name: Upload VSIX
        uses: actions/upload-artifact@v3
        with:
          name: helix-extension
          path: vscode-extension/*.vsix
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: vscode-extension/*.vsix
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Usage

```bash
# Create version tag
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will automatically:
# 1. Build extension
# 2. Package as .vsix
# 3. Create GitHub release
# 4. Attach .vsix file
```

## Part 7: Version Management

### Updating Version

```bash
cd vscode-extension

# Update version in package.json
npm version patch  # 1.0.0 → 1.0.1
npm version minor  # 1.0.0 → 1.1.0
npm version major  # 1.0.0 → 2.0.0

# Rebuild and republish
npm run build
vsce package
vsce publish
```

### Changelog

Update `vscode-extension/CHANGELOG.md`:

```markdown
## [1.0.1] - 2025-11-03
### Fixed
- Connection timeout increased to 30s
- Better error messages

### Added
- Support for Python 3.12
```

## Part 8: Monitoring & Support

### User Feedback Collection

Add telemetry (optional, with user consent):

```typescript
// In extension.ts
import * as vscode from 'vscode';

function sendTelemetry(event: string, data: any) {
  const config = vscode.workspace.getConfiguration('helix');
  if (config.get('enableTelemetry') === true) {
    // Send to your analytics endpoint
  }
}
```

### Error Tracking

Implement error reporting:

```typescript
try {
  // ... extension code ...
} catch (error) {
  console.error('Helix error:', error);
  vscode.window.showErrorMessage(
    `Helix error: ${error.message}. Please check backend connection.`
  );
}
```

### Support Channels

Setup:
1. GitHub Issues for bug reports
2. Discussion forum for questions
3. Documentation site for guides
4. Status page for backend health

## Summary

✅ **Extension Ready:**
- Updated package.json with metadata
- Added VS Code settings support
- Built and packaged as .vsix

✅ **Backend Deployed:**
- AWS EKS with 3 services
- Load balancer with public URL
- Kubernetes manifests
- CI/CD pipeline

✅ **Distribution:**
- Private: Share .vsix file
- Public: VS Code Marketplace
- Auto-updates: GitHub releases

**Next Steps:**
1. Build extension: `cd vscode-extension && npm run build && vsce package`
2. Deploy backend: `./scripts/deploy.sh helix-cluster us-east-1`
3. Get backend URL: `kubectl get svc helix-backend-service`
4. Distribute extension + setup guide to users
5. Monitor usage and collect feedback

**Your complete Helix system is now ready for deployment! 🚀**
