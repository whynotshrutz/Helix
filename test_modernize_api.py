"""
Test the code modernization API endpoint
"""
import requests
import json

BACKEND_URL = "http://127.0.0.1:8001"

old_python_code = '''
# Old Python 2 style code
print "Hello World"

name = "John"
age = 30
message = "My name is %s and I'm %d years old" % (name, age)

try:
    result = 10 / 0
except Exception, e:
    print "Error:", str(e)

import imp
import optparse

def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
'''

def test_modernize_code():
    print("=" * 80)
    print("TESTING CODE MODERNIZATION API")
    print("=" * 80)
    
    # Test with /run endpoint
    payload = {
        "prompt": f"Please analyze this old Python code and provide modernization recommendations:\n\n```python\n{old_python_code}\n```",
        "workspace_dir": "C:/Users/sriha/Hackathon/Helix"
    }
    
    print("\n📤 Sending request to /run endpoint...")
    print(f"Prompt: {payload['prompt'][:100]}...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/run",
            json=payload,
            timeout=60
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success!")
            print(f"Mode: {result.get('mode', 'N/A')}")
            print(f"Agent: {result.get('agent', 'N/A')}")
            print(f"\n📄 Response Content:")
            print("=" * 80)
            print(result.get('content', 'No content'))
            print("=" * 80)
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend server!")
        print("Make sure the server is running on http://127.0.0.1:8001")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_modernize_code()
