"""
Test script to interact with AgentOS API directly.
Run this while the server is running (helix --serve)
"""

import requests
import json

BASE_URL = "http://localhost:7777"

def test_connection():
    """Test if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Server is running!")
        print(f"Response: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Server not running: {e}")
        return False

def list_agents():
    """List all available agents."""
    try:
        response = requests.get(f"{BASE_URL}/agents")
        agents = response.json()
        print(f"\n📋 Available Agents:")
        for agent in agents:
            # Handle different possible response structures
            agent_id = agent.get('agent_id', agent.get('id', agent.get('name', 'Unknown')))
            name = agent.get('name', agent_id)
            description = agent.get('description', 'No description')
            model_info = agent.get('model', {})
            
            # If model_info is a dict, extract the model name
            if isinstance(model_info, dict):
                model_name = model_info.get('model', model_info.get('name', 'Unknown'))
            else:
                model_name = str(model_info)
            
            print(f"   - {name} (ID: {agent_id})")
            print(f"     Description: {description}")
            print(f"     Model: {model_name}")
        return agents
    except Exception as e:
        print(f"❌ Error listing agents: {e}")
        import traceback
        traceback.print_exc()
        return []

def chat_with_agent(agent_id: str, message: str, session_id: str = "test_session"):
    """Send a message to an agent."""
    print(f"\n💬 Chatting with {agent_id}...")
    print(f"📝 Message: {message}")
    
    try:
        # Try with form data (multipart/form-data)
        response = requests.post(
            f"{BASE_URL}/agents/{agent_id}/runs",
            data={
                "message": message,
                "stream": "false",
                "session_id": session_id
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Response from {agent_id}:")
            content = result.get('content', result.get('response', result))
            if isinstance(content, dict):
                content = json.dumps(content, indent=2)
            print(f"{content}")
            return result
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"{response.text}")
            
            # Try alternative format if first attempt failed
            if response.status_code == 422:
                print(f"\n🔄 Trying alternative request format...")
                response2 = requests.post(
                    f"{BASE_URL}/agents/{agent_id}/runs",
                    json={
                        "message": message,
                        "stream": False,
                        "session_id": session_id
                    }
                )
                if response2.status_code == 200:
                    result = response2.json()
                    print(f"\n✅ Response from {agent_id}:")
                    content = result.get('content', result.get('response', result))
                    if isinstance(content, dict):
                        content = json.dumps(content, indent=2)
                    print(f"{content}")
                    return result
                else:
                    print(f"❌ Still failed: {response2.status_code}")
                    print(f"{response2.text}")
            
            return None
            
    except Exception as e:
        print(f"❌ Error chatting with agent: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main test function."""
    print("="*60)
    print("🧪 Testing Helix AgentOS API")
    print("="*60)
    
    # Test connection
    if not test_connection():
        print("\n❌ Please start the server first:")
        print("   helix --serve")
        return
    
    # List agents
    agents = list_agents()
    
    if not agents:
        print("\n⚠️  No agents found")
        return
    
    # Get agent IDs
    planner_id = None
    coder_id = None
    
    for agent in agents:
        agent_id = agent.get('agent_id', agent.get('id', agent.get('name')))
        name = agent.get('name', '').lower()
        
        if 'planner' in name.lower():
            planner_id = agent_id
        elif 'coder' in name.lower():
            coder_id = agent_id
    
    # Test chat with Planner
    if planner_id:
        chat_with_agent(
            agent_id=planner_id,
            message="Create a plan for building a simple calculator app"
        )
    else:
        print("\n⚠️  Planner agent not found")
    
    # Test chat with Coder
    if coder_id:
        chat_with_agent(
            agent_id=coder_id,
            message="Write a Python function to add two numbers"
        )
    else:
        print("\n⚠️  Coder agent not found")
    
    print("\n" + "="*60)
    print("✅ API tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()
