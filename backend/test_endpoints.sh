#!/bin/bash
# Test production backend endpoints

BACKEND_URL="http://3.93.17.130:8001"

echo "🔍 Testing Helix Backend Endpoints"
echo "======================================"
echo ""

echo "1️⃣ Testing /health endpoint..."
echo "GET $BACKEND_URL/health"
curl -s "$BACKEND_URL/health" | python3 -m json.tool
echo ""
echo ""

echo "2️⃣ Testing /docs endpoint..."
echo "GET $BACKEND_URL/docs"
curl -s -o /dev/null -w "Status: %{http_code}\n" "$BACKEND_URL/docs"
echo ""
echo ""

echo "3️⃣ Testing /run endpoint (simple query)..."
echo "POST $BACKEND_URL/run"
curl -s -X POST "$BACKEND_URL/run" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, what can you do?",
    "stream": false,
    "user_id": "test-user",
    "session_id": "test-session"
  }' | python3 -m json.tool | head -20
echo ""
echo "... (truncated)"
echo ""

echo "======================================"
echo "✅ Endpoint tests complete!"
