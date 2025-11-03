#!/bin/bash
# Rollback Helix deployment to previous version

set -e

echo "🔄 Rolling back deployments..."

kubectl rollout undo deployment/helix-backend
kubectl rollout undo deployment/helix-sandbox-worker
kubectl rollout undo deployment/helix-code-executor

echo "⏳ Waiting for rollback to complete..."
kubectl rollout status deployment/helix-backend
kubectl rollout status deployment/helix-sandbox-worker
kubectl rollout status deployment/helix-code-executor

echo "✅ Rollback complete!"
kubectl get pods
