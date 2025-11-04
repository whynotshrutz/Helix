import requests
import json

print("🔍 Testing Helix Backend Connection\n")

BACKEND_URL = "http://3.93.17.130:8001"

# Test 1: Health check
print("1️⃣ Testing /health endpoint...")
try:
    response = requests.get(f"{BACKEND_URL}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Test 2: Simple query
print("2️⃣ Testing /run endpoint...")
try:
    response = requests.post(
        f"{BACKEND_URL}/run",
        json={"prompt": "Hello", "stream": False},
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Response preview: {str(data.get('content', ''))[:200]}...")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("If you see errors above, the backend is NOT running on EC2")
print("Start it with: ssh ubuntu@3.93.17.130 'cd ~/Helix/backend && python3 run_server.py'")
