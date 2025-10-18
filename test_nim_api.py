"""Test NVIDIA NIM API connectivity."""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment
load_dotenv(Path(".env"))

nim_api_key = os.getenv("NIM_API_KEY")
nim_base_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")

print(f"Testing NVIDIA NIM API")
print(f"Base URL: {nim_base_url}")
print(f"API Key: {nim_api_key[:20]}..." if nim_api_key else "NO KEY")
print()

# Test chat completion
print("Testing chat completion with nvidia/llama-3.1-nemotron-70b-instruct...")
try:
    response = requests.post(
        f"{nim_base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {nim_api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "meta/llama-3.1-70b-instruct",
            "messages": [
                {"role": "user", "content": "Say hello in Python"}
            ],
            "max_tokens": 100
        }
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse:")
        print(result['choices'][0]['message']['content'])
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")
