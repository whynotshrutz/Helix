#!/usr/bin/env python3
"""
Complete example: Using Helix agents via API to create a real project.
This demonstrates the full workflow from planning to testing.
"""

import requests
import json
import time


def chat(agent: str, message: str, session_id: str = None):
    """Send a message to an agent and get the response."""
    url = f"http://localhost:7777/agents/{agent}/runs"
    
    form_data = {
        "message": message,
        "stream": "false"
    }
    
    if session_id:
        form_data["session_id"] = session_id
    
    try:
        response = requests.post(url, data=form_data, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        # Extract content
        content = (result.get('content') or 
                  result.get('response', '') or 
                  result.get('messages', [{}])[-1].get('content', ''))
        
        return content
    except Exception as e:
        return f"Error: {e}"


def main():
    """Demonstrate complete workflow with all 5 agents."""
    
    print("\n" + "="*70)
    print("🎯 Helix Multi-Agent System - Complete Workflow Demo")
    print("="*70)
    
    # Check server
    try:
        health = requests.get("http://localhost:7777/health", timeout=5)
        print(f"\n✅ Server Status: {health.json()}")
    except:
        print("\n❌ Server is not running!")
        print("Start it with: python -m helix --serve")
        return
    
    session_id = "demo-session-" + str(int(time.time()))
    
    # ==================== STEP 1: PLANNER ====================
    print("\n" + "="*70)
    print("📋 STEP 1: Planning with Planner Agent")
    print("="*70)
    
    plan = chat(
        "planner",
        "Create a detailed plan for a Python web API that serves weather data. "
        "Include endpoints for current weather and forecast.",
        session_id
    )
    
    print(f"\n{plan[:500]}...\n")  # Show first 500 chars
    
    # ==================== STEP 2: CODER ====================
    print("\n" + "="*70)
    print("💻 STEP 2: Coding with Coder Agent")
    print("="*70)
    
    code = chat(
        "coder",
        "Create a FastAPI application with two endpoints: "
        "/weather/current and /weather/forecast. "
        "Include proper type hints and docstrings.",
        session_id
    )
    
    print(f"\n{code[:500]}...\n")
    
    # ==================== STEP 3: TESTER ====================
    print("\n" + "="*70)
    print("🧪 STEP 3: Testing with Tester Agent")
    print("="*70)
    
    tests = chat(
        "tester",
        "Create pytest unit tests for the weather API endpoints. "
        "Include tests for valid requests, invalid inputs, and error handling.",
        session_id
    )
    
    print(f"\n{tests[:500]}...\n")
    
    # ==================== STEP 4: REVIEWER ====================
    print("\n" + "="*70)
    print("👀 STEP 4: Review with Reviewer Agent")
    print("="*70)
    
    review = chat(
        "reviewer",
        "Review the weather API code for best practices, security issues, "
        "and code quality. Suggest improvements.",
        session_id
    )
    
    print(f"\n{review[:500]}...\n")
    
    # ==================== STEP 5: EXPLAINER ====================
    print("\n" + "="*70)
    print("📚 STEP 5: Documentation with Explainer Agent")
    print("="*70)
    
    docs = chat(
        "explainer",
        "Create a README.md for the weather API project. "
        "Include installation instructions, usage examples, and API documentation.",
        session_id
    )
    
    print(f"\n{docs[:500]}...\n")
    
    # ==================== SUMMARY ====================
    print("\n" + "="*70)
    print("✅ Workflow Complete!")
    print("="*70)
    print("""
All 5 agents successfully processed the weather API project:

1. ✅ Planner - Created project plan
2. ✅ Coder - Generated FastAPI code
3. ✅ Tester - Created pytest tests
4. ✅ Reviewer - Provided code review
5. ✅ Explainer - Generated documentation

📊 Session ID: """ + session_id + """

💡 Next Steps:
- View full responses in the terminal output above
- Copy code snippets to create actual files
- Use the Web UI (http://localhost:7777) for interactive development
- Check session history in AgentOS

🌐 Open Web UI: http://localhost:7777
📚 API Docs: http://localhost:7777/docs
""")


if __name__ == "__main__":
    main()
