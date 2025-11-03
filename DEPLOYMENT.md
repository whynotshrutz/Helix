# Helix Deployment Guide for AWS EKS

This guide covers deploying Helix to AWS Elastic Kubernetes Service (EKS).

## Prerequisites

- AWS CLI configured with appropriate credentials
- kubectl installed
- Docker installed
- eksctl installed (optional, for cluster creation)
- An AWS account with EKS permissions

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   AWS EKS Cluster                    │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│
│  │   Backend    │  │   Sandbox    │  │    Code    ││
│  │   (3 pods)   │  │   Worker     │  │  Executor  ││
│  │   Port 8001  │  │   (2 pods)   │  │  (2 pods)  ││
│  └──────┬───────┘  └──────────────┘  └────────────┘│
│         │                                            │
│  ┌──────▼───────────────────────────────────────┐  │
│  │         LoadBalancer Service                  │  │
│  └──────────────────┬────────────────────────────┘  │
│                     │                                │
└─────────────────────┼────────────────────────────────┘
                      │
              ┌───────▼────────┐
              │  Internet/DNS  │
              └────────────────┘
                      │
              ┌───────▼────────┐
              │  VS Code       │
              │  Extension     │
              └────────────────┘
```

## Step 1: Create EKS Cluster

If you don't have an EKS cluster yet:

```bash
# Using eksctl (recommended)
eksctl create cluster \
  --name helix-cluster \
  --region us-east-1 \
  --nodegroup-name helix-nodes \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed

# Or using AWS Console:
# 1. Go to EKS service
# 2. Click "Create cluster"
# 3. Follow the wizard with default VPC settings
```

Configure kubectl:

```bash
aws eks update-kubeconfig --name helix-cluster --region us-east-1
```

## Step 2: Setup AWS Load Balancer Controller

Required for Ingress to work:

```bash
# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=helix-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

## Step 3: Build and Push Docker Images

Update the script configuration:

```bash
# Edit scripts/build-and-push.sh
# Set your AWS region and account ID
AWS_REGION="us-east-1"
```

Run the build script:

```bash
chmod +x scripts/build-and-push.sh
./scripts/build-and-push.sh latest
```

This will:
1. Create ECR repositories
2. Build all Docker images
3. Push them to ECR

## Step 4: Configure Secrets

**IMPORTANT**: Update `k8s/secrets.yaml` with your actual credentials:

```bash
# DO NOT commit this file to git!
# Add k8s/secrets.yaml to .gitignore

# Edit k8s/secrets.yaml
nano k8s/secrets.yaml
```

Replace:
- `YOUR_NVIDIA_API_KEY_HERE` with your NVIDIA API key
- `YOUR_GITHUB_TOKEN_HERE` with your GitHub token

Or use kubectl directly:

```bash
kubectl create secret generic helix-secrets \
  --from-literal=nvidia-api-key='YOUR_NVIDIA_API_KEY' \
  --from-literal=github-token='YOUR_GITHUB_TOKEN'
```

## Step 5: Update Deployment Files

Edit `k8s/deployment.yaml` and replace `<YOUR_ECR_REGISTRY>` with your ECR registry URL:

```yaml
image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/helix-backend:latest
```

## Step 6: Deploy to EKS

Run the deployment script:

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh helix-cluster us-east-1
```

This will:
1. Create secrets and config maps
2. Deploy all applications
3. Create services and ingress
4. Wait for deployments to be ready

## Step 7: Get Backend URL

After deployment, get the LoadBalancer URL:

```bash
# Get the LoadBalancer hostname
kubectl get service helix-backend-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Or with full details
kubectl get services
kubectl get ingress
```

The URL will look like:
```
a1234567890abcdef-1234567890.us-east-1.elb.amazonaws.com
```

## Step 8: Configure VS Code Extension

The VS Code extension uses environment variable `HELIX_BACKEND_URL`.

### For Users Installing the Extension:

1. **Option 1**: Set environment variable before starting VS Code:
   ```bash
   # Linux/Mac
   export HELIX_BACKEND_URL=http://your-loadbalancer-url.amazonaws.com
   code .

   # Windows (PowerShell)
   $env:HELIX_BACKEND_URL="http://your-loadbalancer-url.amazonaws.com"
   code .
   ```

2. **Option 2**: Add to VS Code settings:
   Create a workspace settings file `.vscode/settings.json`:
   ```json
   {
     "terminal.integrated.env.windows": {
       "HELIX_BACKEND_URL": "http://your-loadbalancer-url.amazonaws.com"
     },
     "terminal.integrated.env.linux": {
       "HELIX_BACKEND_URL": "http://your-loadbalancer-url.amazonaws.com"
     },
     "terminal.integrated.env.osx": {
       "HELIX_BACKEND_URL": "http://your-loadbalancer-url.amazonaws.com"
     }
   }
   ```

### Building and Publishing the Extension:

```bash
cd vscode-extension

# Install dependencies
npm install

# Package extension
npm install -g vsce
vsce package

# This creates helix-mcp-X.X.X.vsix
# Users can install with: code --install-extension helix-mcp-X.X.X.vsix
```

To publish to VS Code Marketplace:
```bash
# Create a publisher account at https://marketplace.visualstudio.com/
vsce publish
```

## Step 9: Verify Deployment

Check pod status:

```bash
kubectl get pods
kubectl logs -f deployment/helix-backend
```

Test the health endpoint:

```bash
BACKEND_URL=$(kubectl get service helix-backend-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl http://${BACKEND_URL}/health
```

Expected response:
```json
{"status":"healthy"}
```

## Monitoring and Maintenance

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/helix-backend

# Sandbox worker logs
kubectl logs -f deployment/helix-sandbox-worker

# Code executor logs
kubectl logs -f deployment/helix-code-executor

# All pods
kubectl logs -f -l app=helix-backend
```

### Scale Applications

```bash
# Scale backend to 5 replicas
kubectl scale deployment helix-backend --replicas=5

# Or edit deployment.yaml and reapply
kubectl apply -f k8s/deployment.yaml
```

### Update Deployment

```bash
# Build new images with version tag
./scripts/build-and-push.sh v1.1.0

# Update deployment.yaml with new image tag
# Then apply
kubectl apply -f k8s/deployment.yaml

# Or use kubectl set image
kubectl set image deployment/helix-backend helix-backend=<ECR_URL>/helix-backend:v1.1.0
```

### Rollback

```bash
# Quick rollback
./scripts/rollback.sh

# Or manual rollback
kubectl rollout undo deployment/helix-backend
kubectl rollout status deployment/helix-backend
```

## Cost Optimization

### Development Environment

For development, use smaller instances:

```bash
eksctl create cluster \
  --name helix-dev \
  --region us-east-1 \
  --node-type t3.small \
  --nodes 2 \
  --spot
```

And reduce replicas in `k8s/deployment.yaml`:
```yaml
spec:
  replicas: 1  # Instead of 3
```

### Production Environment

For production:
- Use t3.medium or larger
- Enable cluster autoscaling
- Use AWS Fargate for serverless pods
- Enable CloudWatch Container Insights for monitoring

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

Common issues:
- Image pull errors: Check ECR permissions
- Secrets not found: Verify secrets.yaml was applied
- Health check failures: Check application logs

### LoadBalancer not getting external IP

```bash
kubectl describe service helix-backend-service
```

Check:
- AWS Load Balancer Controller is installed
- Security groups allow traffic on port 80
- Subnets are properly tagged

### Extension not connecting

1. Verify backend URL:
   ```bash
   curl http://<backend-url>/health
   ```

2. Check HELIX_BACKEND_URL environment variable in VS Code:
   - Open terminal in VS Code
   - Run: `echo $HELIX_BACKEND_URL` (Linux/Mac) or `echo %HELIX_BACKEND_URL%` (Windows)

3. Check browser console in VS Code webview for errors

## Security Best Practices

1. **Use HTTPS in Production**:
   - Setup AWS Certificate Manager certificate
   - Update ingress.yaml with TLS configuration
   - Use Route53 for custom domain

2. **Rotate Secrets Regularly**:
   ```bash
   kubectl delete secret helix-secrets
   kubectl create secret generic helix-secrets \
     --from-literal=nvidia-api-key='NEW_KEY' \
     --from-literal=github-token='NEW_TOKEN'
   kubectl rollout restart deployment/helix-backend
   ```

3. **Enable Pod Security Policies**:
   - Use non-root users (already configured in Dockerfiles)
   - Set resource limits (already configured in deployment.yaml)
   - Enable network policies

4. **Monitor and Alert**:
   - Setup CloudWatch alarms for pod failures
   - Monitor CPU/memory usage
   - Track API error rates

## Cleanup

To delete everything:

```bash
# Delete Kubernetes resources
kubectl delete -f k8s/

# Delete ECR images (optional)
aws ecr delete-repository --repository-name helix-backend --force --region us-east-1
aws ecr delete-repository --repository-name helix-sandbox-worker --force --region us-east-1
aws ecr delete-repository --repository-name helix-code-executor --force --region us-east-1

# Delete EKS cluster
eksctl delete cluster --name helix-cluster --region us-east-1
```

## Next Steps

- Setup CI/CD with GitHub Actions
- Configure custom domain with Route53
- Enable HTTPS with AWS Certificate Manager
- Setup monitoring with CloudWatch or Prometheus
- Configure autoscaling policies
- Implement backup strategies for persistent data

## Support

For issues or questions:
- Check logs: `kubectl logs -f deployment/helix-backend`
- Review pod events: `kubectl describe pod <pod-name>`
- Verify health: `curl http://<backend-url>/health`
