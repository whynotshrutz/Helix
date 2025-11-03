# Helix AWS EKS Deployment - Quick Reference

## 🚀 One-Line Deploy Commands

```bash
# 1. Build & Push Images
./scripts/build-and-push.sh latest

# 2. Create Secrets
kubectl create secret generic helix-secrets \
  --from-literal=nvidia-api-key='YOUR_KEY' \
  --from-literal=github-token='YOUR_TOKEN'

# 3. Deploy
./scripts/deploy.sh helix-cluster us-west-2

# 4. Get Backend URL
kubectl get svc helix-backend-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

## 📋 Pre-Deployment Checklist

- [ ] AWS CLI configured
- [ ] kubectl installed
- [ ] EKS cluster created
- [ ] Update ECR URLs in `k8s/deployment.yaml`
- [ ] Set your NVIDIA API key
- [ ] Set your GitHub token

## 🔧 Essential Commands

### Check Status
```bash
kubectl get pods                    # Pod status
kubectl get services               # Service status
kubectl get ingress                # Ingress status
```

### View Logs
```bash
kubectl logs -f deployment/helix-backend
kubectl logs -f deployment/helix-sandbox-worker
kubectl logs -f deployment/helix-code-executor
```

### Scale Services
```bash
kubectl scale deployment helix-backend --replicas=5
```

### Update Deployment
```bash
kubectl set image deployment/helix-backend helix-backend=<ECR_URL>:new-tag
kubectl rollout status deployment/helix-backend
```

### Rollback
```bash
./scripts/rollback.sh
# OR
kubectl rollout undo deployment/helix-backend
```

## 🔍 Health Checks

```bash
# Get backend URL
BACKEND_URL=$(kubectl get svc helix-backend-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test health
curl http://${BACKEND_URL}/health

# Expected response: {"status":"healthy"}
```

## 🆘 Troubleshooting

### Pods Crashing
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Can't Connect to Backend
```bash
# Check service
kubectl describe svc helix-backend-service

# Check security groups
# Ensure port 80 is open in AWS console
```

### Extension Not Working
```bash
# Check environment variable
echo $HELIX_BACKEND_URL

# Set it:
export HELIX_BACKEND_URL=http://<your-lb-url>
```

## 📦 VS Code Extension

### Build Extension
```bash
cd vscode-extension
npm install
npm run build
npm install -g vsce
vsce package
```

### Install Extension
```bash
# Users run:
code --install-extension helix-mcp-X.X.X.vsix

# Set backend URL:
export HELIX_BACKEND_URL=http://your-backend-url.com
```

## 🔐 Security Notes

- ✅ Never commit `k8s/secrets.yaml` with real credentials
- ✅ Use AWS Secrets Manager for production
- ✅ Enable HTTPS with AWS Certificate Manager
- ✅ Rotate secrets regularly

## 💰 Cost Estimates

**Dev:** ~$50-70/month (t3.small, 2 nodes)
**Prod:** ~$200-300/month (t3.medium, 3+ nodes)

## 📚 Full Documentation

- `DEPLOYMENT.md` - Complete deployment guide
- `PRODUCTION_READY.md` - Production readiness summary
- `README.md` - Project overview

---

**Need Help?**
- Check logs: `kubectl logs -f deployment/helix-backend`
- Review DEPLOYMENT.md for detailed steps
- Test health: `curl http://<backend-url>/health`
