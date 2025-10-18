#!/usr/bin/env python3
"""
Test Helix agents creating files through the API.
This tests the VS Code integration tools!
"""

import requests
import json
import time


def chat_with_agent(agent_name: str, message: str):
    """Chat with an agent and get the response."""
    url = f"http://localhost:7777/agents/{agent_name}/runs"
    
    form_data = {
        "message": message,
        "session_id": f"file-creation-test",
        "stream": "false"
    }
    
    print(f"\n{'='*70}")
    print(f"🤖 {agent_name.upper()} Agent")
    print(f"{'='*70}")
    print(f"📝 Request: {message}")
    print(f"{'-'*70}")
    
    try:
        response = requests.post(url, data=form_data, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract content
        if isinstance(result, dict):
            content = (result.get('content') or 
                      result.get('response', '') or 
                      result.get('messages', [{}])[-1].get('content', ''))
        else:
            content = str(result)
        
        print(f"💬 Response:\n{content}\n")
        
        # Check if there are any tool calls or file operations mentioned
        if 'create_file' in content.lower() or 'createfile' in content.lower():
            print("✨ Agent wants to create a file!")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None


def main():
    """Test file creation capabilities."""
    print("\n" + "="*70)
    print("🚀 Helix VS Code Integration - File Creation Test")
    print("="*70)
    
    # Check server health
    try:
        health = requests.get("http://localhost:7777/health", timeout=5)
        print(f"\n✅ Server is running: {health.json()}")
    except:
        print("\n❌ Server is not running!")
        print("Start it with: python -m helix --serve")
        return
    
    # Test 1: Ask Coder to create a simple Python file
    print("\n" + "🧪 TEST 1: Create a simple Python calculator file")
    chat_with_agent(
        "coder",
        "Create a file called 'calculator.py' with functions for add, subtract, multiply, and divide. Include proper docstrings and type hints."
    )
    
    # Test 2: Ask Planner to create a plan
    print("\n" + "🧪 TEST 2: Create a project plan")
    chat_with_agent(
        "planner",
        "Create a plan for building a web scraper. Save the plan to 'web_scraper_plan.md'"
    )
    
    # Test 3: Ask Explainer to document something
    print("\n" + "🧪 TEST 3: Create documentation")
    chat_with_agent(
        "explainer",
        "Explain how to use the Helix multi-agent system and save the explanation to 'HELIX_USAGE.md'"
    )
    
    print("\n" + "="*70)
    print("✅ All tests complete!")
    print("="*70)
    print("\n📋 Next Steps:")
    print("1. Check if agents mentioned creating files in their responses")
    print("2. Look for file paths and content in the output")
    print("3. Agents have access to create_file, edit_file, and other VS Code tools")
    print("4. To actually create files in VS Code, we need the extension working")
    print("\n💡 Alternative: Use the Web UI at http://localhost:7777")
    print()


if __name__ == "__main__":
    main()
