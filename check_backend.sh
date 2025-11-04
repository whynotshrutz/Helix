#!/bin/bash
# Quick script to check EC2 backend status

echo "🔍 Checking Helix Backend Status on EC2"
echo "========================================"
echo ""

BACKEND_URL="http://3.93.17.130:8001"

echo "1️⃣ Testing /health endpoint..."
curl -s "$BACKEND_URL/health" || echo "❌ Backend not responding"
echo ""
echo ""

echo "2️⃣ Testing simple query..."
curl -s -X POST "$BACKEND_URL/run" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "stream": false}' || echo "❌ Backend not responding"
echo ""
echo ""

echo "✅ If you see responses above, backend is running"
echo "❌ If you see errors, backend needs to be started on EC2"
echo ""
echo "To start backend on EC2:"
echo "  ssh ubuntu@3.93.17.130"
echo "  cd ~/Helix/backend"
echo "  python3 run_server.py"
