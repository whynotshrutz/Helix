#!/bin/bash
# Build and Push Docker Images to AWS ECR

set -e

# Configuration
AWS_REGION="us-east-1"  # Change to your region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_TAG="${1:-latest}"

echo "🔐 Logging in to AWS ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

# Create ECR repositories if they don't exist
echo "📦 Creating ECR repositories..."
for repo in helix-backend helix-sandbox-worker helix-code-executor; do
    aws ecr describe-repositories --repository-names ${repo} --region ${AWS_REGION} 2>/dev/null || \
    aws ecr create-repository --repository-name ${repo} --region ${AWS_REGION}
done

# Build and push backend
echo "🏗️  Building helix-backend..."
cd backend
docker build -t helix-backend:${IMAGE_TAG} .
docker tag helix-backend:${IMAGE_TAG} ${ECR_REGISTRY}/helix-backend:${IMAGE_TAG}
echo "⬆️  Pushing helix-backend..."
docker push ${ECR_REGISTRY}/helix-backend:${IMAGE_TAG}
cd ..

# Build and push code executor
echo "🏗️  Building helix-code-executor..."
cd backend/docker/code-executor
docker build -t helix-code-executor:${IMAGE_TAG} .
docker tag helix-code-executor:${IMAGE_TAG} ${ECR_REGISTRY}/helix-code-executor:${IMAGE_TAG}
echo "⬆️  Pushing helix-code-executor..."
docker push ${ECR_REGISTRY}/helix-code-executor:${IMAGE_TAG}
cd ../../..

# Build and push sandbox worker
echo "🏗️  Building helix-sandbox-worker..."
cd backend/sandbox_worker
docker build -t helix-sandbox-worker:${IMAGE_TAG} .
docker tag helix-sandbox-worker:${IMAGE_TAG} ${ECR_REGISTRY}/helix-sandbox-worker:${IMAGE_TAG}
echo "⬆️  Pushing helix-sandbox-worker..."
docker push ${ECR_REGISTRY}/helix-sandbox-worker:${IMAGE_TAG}
cd ../..

echo "✅ All images built and pushed successfully!"
echo "📝 Update k8s/deployment.yaml with:"
echo "   ${ECR_REGISTRY}/helix-backend:${IMAGE_TAG}"
echo "   ${ECR_REGISTRY}/helix-sandbox-worker:${IMAGE_TAG}"
echo "   ${ECR_REGISTRY}/helix-code-executor:${IMAGE_TAG}"
