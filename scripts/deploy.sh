#!/bin/bash
# Deploy Helix to AWS EKS

set -e

CLUSTER_NAME="${1:-helix-cluster}"
AWS_REGION="${2:-us-west-2}"

echo "🔧 Configuring kubectl for EKS cluster..."
aws eks update-kubeconfig --name ${CLUSTER_NAME} --region ${AWS_REGION}

echo "🔐 Creating secrets..."
kubectl apply -f k8s/secrets.yaml

echo "⚙️  Creating config map..."
kubectl apply -f k8s/configmap.yaml

echo "🚀 Deploying applications..."
kubectl apply -f k8s/deployment.yaml

echo "🌐 Creating services..."
kubectl apply -f k8s/service.yaml

echo "🔗 Creating ingress..."
kubectl apply -f k8s/ingress.yaml

echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/helix-backend \
  deployment/helix-sandbox-worker \
  deployment/helix-code-executor

echo "✅ Deployment complete!"
echo ""
echo "📊 Checking status..."
kubectl get pods
echo ""
kubectl get services
echo ""
echo "🌍 Getting LoadBalancer URL..."
kubectl get ingress helix-ingress
echo ""
echo "💡 To get the backend URL, run:"
echo "   kubectl get service helix-backend-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'"
