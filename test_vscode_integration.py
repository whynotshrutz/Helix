#!/usr/bin/env python3
"""
Quick test of Helix agents using the API directly.
This works without VS Code extension!
"""

import requests
import json

def test_agent(agent_name: str, message: str):
    """Test an agent via the API."""
    url = f"http://localhost:7777/agents/{agent_name}/runs"
    
    # AgentOS API requires multipart/form-data, not JSON
    form_data = {
        "message": message,
        "session_id": f"test-{agent_name}",
        "stream": "false"  # String, not boolean for form data
    }
    
    print(f"\n{'='*60}")
    print(f"🤖 Testing {agent_name.upper()} Agent")
    print(f"{'='*60}")
    print(f"📝 Prompt: {message}")
    print(f"{'-'*60}")
    
    try:
        # Use data= for form data, not json=
        response = requests.post(url, data=form_data, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract content from the response
        if isinstance(result, dict):
            content = result.get('content') or result.get('response', '') or result.get('messages', [{}])[-1].get('content', '')
        else:
            content = str(result)
        
        print(f"✅ Response:\n{content}\n")
        
        return result
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None


def main():
    """Run tests on all agents."""
    print("\n" + "="*60)
    print("🚀 Helix Multi-Agent System - Direct API Test")
    print("="*60)
    
    # Check if server is running
    try:
        health = requests.get("http://localhost:7777/health", timeout=5)
        print(f"\n✅ Server is running!")
        print(f"📊 Health: {health.json()}")
    except:
        print("\n❌ Server is not running!")
        print("Start it with: python -m helix --serve")
        return
    
    # Test cases
    tests = [
        ("planner", "Create a plan for a simple calculator application"),
        ("coder", "Write a Python function to add two numbers"),
        ("explainer", "Explain what Helix is and how it works"),
    ]
    
    for agent_name, message in tests:
        test_agent(agent_name, message)
    
    print("="*60)
    print("✅ All tests complete!")
    print("="*60)
    print("\n💡 Tips:")
    print("- Web UI: http://localhost:7777")
    print("- API Docs: http://localhost:7777/docs")
    print("- Control Plane: https://os.agno.com")
    print()


if __name__ == "__main__":
    main()
