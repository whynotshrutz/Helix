"""
Dynamic Live Testing - No Hardcoded Checks
Tests actual agent behavior dynamically
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_server():
    """Check server health"""
    print("="*70)
    print("🏥 SERVER HEALTH CHECK")
    print("="*70)
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Server healthy")
            print(f"   Mode: {data.get('mode')}")
            print(f"   Agents: {data.get('agent_count')}")
            return True
        else:
            print(f"❌ Server returned {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect: {e}")
        return False

def send_request(prompt: str, test_name: str):
    """Send a request and show the response"""
    print(f"\n{'='*70}")
    print(f"📝 {test_name}")
    print(f"{'='*70}")
    print(f"Prompt: {prompt}")
    print("-"*70)
    
    payload = {
        "prompt": prompt,
        "workspace_dir": None,  # Let agent use VS Code workspace
        "session_id": f"test_{int(time.time())}"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/run", json=payload, timeout=90)
        
        if resp.status_code == 200:
            result = resp.json()
            content = result.get("content", result.get("response", ""))
            agent = result.get("agent", "unknown")
            
            print(f"Agent: {agent}")
            print(f"Response length: {len(content)} chars")
            print(f"\n📄 FULL RESPONSE:")
            print("-"*70)
            print(content)
            print("-"*70)
            
            # Check for CREATE_FILE format
            if "CREATE_FILE:" in content:
                print("\n✅ Contains CREATE_FILE format")
            else:
                print("\n⚠️  No CREATE_FILE format found")
            
            return True
        else:
            print(f"❌ Request failed: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🧪 HELIX DYNAMIC TESTING - NO HARDCODED CHECKS")
    print("="*70 + "\n")
    
    if not test_server():
        print("\n❌ Server not available. Please start the server first.")
        return
    
    time.sleep(1)
    
    # Test 1: File creation with explicit name
    send_request(
        "create a file called test_math.py with functions for add, subtract, multiply and divide",
        "TEST 1: Create File (Explicit Name)"
    )
    
    time.sleep(3)
    
    # Test 2: File creation without name
    send_request(
        "create a python file that generates fibonacci numbers",
        "TEST 2: Create File (No Name Given)"
    )
    
    time.sleep(3)
    
    # Test 3: List files dynamically
    send_request(
        "what files are in the workspace directory?",
        "TEST 3: List Workspace Files Dynamically"
    )
    
    time.sleep(3)
    
    # Test 4: Git status
    send_request(
        "show git status",
        "TEST 4: Git Operations"
    )
    
    time.sleep(3)
    
    # Test 5: Analyze repository
    send_request(
        "analyze all files in the repository",
        "TEST 5: Repository Analysis"
    )
    
    print("\n" + "="*70)
    print("✅ TESTING COMPLETE")
    print("="*70)
    print("\nReview the responses above to verify:")
    print("1. CREATE_FILE format is used (not manual instructions)")
    print("2. Agent actually lists files using tools (not hardcoded paths)")
    print("3. Git operations work")
    print("4. Analysis explores files dynamically")

if __name__ == "__main__":
    main()
