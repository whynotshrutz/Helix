"""
Test modernization with explicit tool request
"""
import requests
import json

BACKEND_URL = "http://127.0.0.1:8001"

old_python_code = '''
print "Hello World"

name = "John"
age = 30
message = "My name is %s and I'm %d years old" % (name, age)

try:
    result = 10 / 0
except Exception, e:
    print "Error:", str(e)

def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
'''

def test_with_explicit_tool_request():
    print("=" * 80)
    print("TESTING MODERNIZATION WITH EXPLICIT TOOL REQUEST")
    print("=" * 80)
    
    # Be very explicit about using the tool
    prompt = f"""Please use the modernize_code tool to analyze this old Python 2 code:

{old_python_code}

Use modernize_code tool with:
- code: the code above
- language: python
- file_path: old_script.py"""
    
    payload = {
        "prompt": prompt,
        "mode": "chat",
        "stream": False
    }
    
    print("\n📤 Sending explicit tool request...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/run",
            json=payload,
            timeout=120  # Longer timeout
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
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out (120 seconds)")
        print("The agent might be processing... check server logs")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_with_explicit_tool_request()
