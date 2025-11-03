# Complete Helix Deployment Guide

## 🎯 What You Have Now

### ✅ VS Code Extension
- **Updated**: `vscode-extension/package.json` with proper metadata, version 1.0.0
- **Updated**: `extension.ts` to use VS Code settings for backend URL
- **Feature**: Users can configure backend via Settings UI or environment variable
- **Ready**: For building, packaging, and distribution

### ✅ Backend Services
- **3 Dockerfiles**: Backend, Code Executor, Sandbox Worker (all production-ready)
- **Security**: Non-root users, health checks, resource limits
- **Kubernetes**: Full manifests for AWS EKS deployment
- **Scripts**: Automated build, deploy, and rollback scripts
- **CI/CD**: GitHub Actions workflow for continuous deployment

### ✅ Documentation
- `DEPLOYMENT.md` - Complete AWS EKS deployment guide
- `EXTENSION_PUBLISHING.md` - Extension publishing and distribution guide
- `PRODUCTION_READY.md` - Production readiness checklist
- `QUICK_DEPLOY.md` - Quick reference card
- `README.md` - Updated project overview

---

## 🚀 Quick Start: Deploy Everything

### Step 1: Build & Package Extension

**Windows:**
```cmd
cd C:\Users\sriha\Hackathon\Helix
scripts\build-extension.bat
```

**Linux/Mac:**
```bash
cd /path/to/Helix
chmod +x scripts/build-extension.sh
./scripts/build-extension.sh
```

**Output:** `vscode-extension/helix-mcp-client-1.0.0.vsix`

### Step 2: Deploy Backend to AWS

**Prerequisites:**
- AWS CLI configured
- kubectl installed
- Docker installed
- EKS cluster created (or use eksctl to create one)

**Deploy:**
```bash
# 1. Build and push images to ECR
chmod +x scripts/build-and-push.sh
./scripts/build-and-push.sh latest

# 2. Create secrets
kubectl create secret generic helix-secrets \
  --from-literal=nvidia-api-key='YOUR_NVIDIA_API_KEY' \
  --from-literal=github-token='YOUR_GITHUB_TOKEN'

# 3. Deploy to EKS
chmod +x scripts/deploy.sh
./scripts/deploy.sh helix-cluster us-west-2

# 4. Get backend URL
kubectl get service helix-backend-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

**Example output:** `a1234567890abcd.us-west-2.elb.amazonaws.com`

### Step 3: Distribute Extension

**Option A: Internal Distribution (Recommended)**

1. Share the `.vsix` file with users
2. Provide setup instructions:

```markdown
# Helix Setup

1. Install extension:
   code --install-extension helix-mcp-client-1.0.0.vsix

2. Configure backend URL:
   - Open VS Code Settings (Ctrl+,)
   - Search for "Helix"
   - Set "Helix: Backend Url" to:
     http://a1234567890abcd.us-west-2.elb.amazonaws.com

3. Start using Helix:
   - Click Helix icon in left sidebar
   - Start chatting!
```

**Option B: VS Code Marketplace (Public)**

```bash
cd vscode-extension

# Login (one-time)
vsce login your-publisher-name

# Publish
vsce publish
```

Users can then install from VS Code Extensions marketplace.

---

## 📋 Deployment Checklist

### Before You Start

- [ ] AWS account with EKS permissions
- [ ] NVIDIA API key (get from build.nvidia.com)
- [ ] GitHub personal access token
- [ ] Node.js 16+ installed (for extension)
- [ ] Docker installed
- [ ] kubectl installed
- [ ] AWS CLI configured

### Extension Build

- [ ] Run `scripts/build-extension.bat` (Windows) or `scripts/build-extension.sh` (Linux/Mac)
- [ ] Verify `.vsix` file created in `vscode-extension/`
- [ ] Test locally: `code --install-extension helix-mcp-client-1.0.0.vsix`

### Backend Deployment

- [ ] Update `scripts/build-and-push.sh` with your AWS region/account
- [ ] Update `k8s/deployment.yaml` with your ECR registry URLs
- [ ] Create/access EKS cluster
- [ ] Run `scripts/build-and-push.sh latest`
- [ ] Create secrets with real credentials
- [ ] Run `scripts/deploy.sh`
- [ ] Verify pods running: `kubectl get pods`
- [ ] Get LoadBalancer URL: `kubectl get svc`

### Integration

- [ ] Test backend health: `curl http://YOUR-LB-URL/health`
- [ ] Install extension in VS Code
- [ ] Configure backend URL in VS Code settings
- [ ] Test chat functionality
- [ ] Test file attachments
- [ ] Test inline completions

### Distribution

- [ ] Create user setup guide with your backend URL
- [ ] Test on clean machine
- [ ] Distribute `.vsix` file + setup guide
- [ ] Monitor backend logs for errors

---

## 🔧 Configuration Guide for Users

### Method 1: VS Code Settings UI (Easiest)

1. Install extension: `code --install-extension helix-mcp-client-1.0.0.vsix`
2. Open Settings: `Ctrl+,` (or `Cmd+,` on Mac)
3. Search: "Helix"
4. Set "Helix: Backend Url" to your server URL
5. Restart VS Code (optional)
6. Click Helix icon in sidebar

### Method 2: Settings JSON

Open settings.json and add:
```json
{
  "helix.backendUrl": "http://your-backend-url.com"
}
```

### Method 3: Environment Variable

**Windows (PowerShell):**
```powershell
$env:HELIX_BACKEND_URL="http://your-backend-url.com"
code .
```

**Windows (CMD):**
```cmd
set HELIX_BACKEND_URL=http://your-backend-url.com
code .
```

**Linux/Mac:**
```bash
export HELIX_BACKEND_URL=http://your-backend-url.com
code .
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           End Users (Developers)             │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │  VS Code with Helix Extension       │    │
│  │  - Chat Panel UI                    │    │
│  │  - Inline Completions               │    │
│  │  - File Attachments                 │    │
│  └──────────────┬──────────────────────┘    │
└─────────────────┼──────────────────────────┘
                  │ HTTP/HTTPS
                  │ (Configure in settings)
┌─────────────────▼──────────────────────────┐
│         AWS Application Load Balancer       │
│         (Public URL from EKS)               │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────▼──────────────────────────┐
│          AWS EKS Cluster                    │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  Helix Backend (3 replicas)          │  │
│  │  - Multi-agent orchestration         │  │
│  │  - FastAPI server (port 8001)        │  │
│  │  - Health checks enabled             │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  Sandbox Worker (2 replicas)         │  │
│  │  - Safe code execution               │  │
│  │  - Port 5000                          │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │  Code Executor (2 replicas)          │  │
│  │  - Python execution sandbox          │  │
│  │  - Port 8888                          │  │
│  └──────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
         │              │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │ NVIDIA  │   │ ChromaDB│   │ GitHub  │
    │  NIMs   │   │   RAG   │   │   API   │
    └─────────┘   └─────────┘   └─────────┘
```

---

## 📊 Monitoring & Maintenance

### Check Backend Health

```bash
# Get backend URL
BACKEND_URL=$(kubectl get svc helix-backend-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test health
curl http://${BACKEND_URL}/health
# Expected: {"status":"healthy"}
```

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/helix-backend

# All pods
kubectl get pods
kubectl logs -f <pod-name>
```

### Scale Services

```bash
# Scale backend to 5 replicas
kubectl scale deployment helix-backend --replicas=5

# Check status
kubectl get deployments
```

### Update Backend

```bash
# Build new version
./scripts/build-and-push.sh v1.1.0

# Update deployment
kubectl set image deployment/helix-backend helix-backend=<ECR_URL>:v1.1.0

# Or rollback
./scripts/rollback.sh
```

### Update Extension

```bash
# Update version in package.json
cd vscode-extension
npm version patch  # 1.0.0 → 1.0.1

# Rebuild
npm run build
vsce package

# Distribute new .vsix to users
```

---

## 🆘 Troubleshooting

### Extension Can't Connect

**Check backend URL:**
1. VS Code Settings → "Helix: Backend Url"
2. Verify URL is correct (no trailing slash)

**Test backend:**
```bash
curl http://your-backend-url/health
```

**Check firewall:**
- Ensure security groups allow HTTP/HTTPS
- Check corporate firewall/proxy

### Pods Not Starting

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

Common issues:
- Image pull errors → Check ECR permissions
- Secrets not found → Re-create secrets
- Out of memory → Increase resource limits

### High Latency

- Scale backend: `kubectl scale deployment helix-backend --replicas=5`
- Use larger instance types (t3.large instead of t3.medium)
- Enable autoscaling
- Check NVIDIA API rate limits

---

## 💰 Cost Estimates

### Development/Testing
- **EKS Cluster**: $0.10/hour (~$73/month)
- **t3.small nodes (2)**: ~$30/month
- **Load Balancer**: ~$20/month
- **ECR Storage**: ~$5/month
- **Total**: ~$130/month

### Production
- **EKS Cluster**: $0.10/hour (~$73/month)
- **t3.medium nodes (3)**: ~$90/month
- **Load Balancer**: ~$20/month
- **ECR Storage**: ~$10/month
- **Data Transfer**: ~$50/month
- **Total**: ~$250/month

### Cost Optimization
- Use Spot instances for dev (50-70% savings)
- Enable cluster autoscaling
- Use Fargate for serverless pods
- Schedule non-prod environments (shut down at night)

---

## 🎉 You're Ready!

### What You Can Do Now

1. **Build Extension**: `scripts/build-extension.bat` → Get `.vsix` file
2. **Deploy Backend**: Follow AWS EKS steps → Get LoadBalancer URL
3. **Distribute**: Share `.vsix` + setup guide with users
4. **Monitor**: Use kubectl commands to monitor health
5. **Scale**: Adjust replicas as usage grows

### Next Steps

- [ ] Setup custom domain with Route53
- [ ] Enable HTTPS with AWS Certificate Manager
- [ ] Configure autoscaling policies
- [ ] Setup CloudWatch alarms
- [ ] Create backup procedures
- [ ] Implement CI/CD with GitHub Actions
- [ ] Add monitoring dashboard
- [ ] Setup user analytics (optional)

### Support Resources

- **Full deployment**: `DEPLOYMENT.md`
- **Extension publishing**: `EXTENSION_PUBLISHING.md`
- **Quick reference**: `QUICK_DEPLOY.md`
- **Production checklist**: `PRODUCTION_READY.md`

---

**🚀 Your Helix system is production-ready! Good luck with deployment!**
