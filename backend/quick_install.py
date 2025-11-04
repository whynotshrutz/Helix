#!/usr/bin/env python3
"""
Quick fix script - Run this on EC2 to install the correct package
"""

import subprocess
import sys

def run_command(cmd):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

print("🔧 Installing Helix dependencies...\n")

# List of packages to try in order
packages_to_try = [
    ("phidata", "Official phidata package"),
    ("phi", "Alternative phi package"),
    ("agno", "Legacy agno package"),
]

success = False

for package, description in packages_to_try:
    print(f"📦 Trying to install {package} ({description})...")
    success, stdout, stderr = run_command(f"pip3 install {package}")
    
    if success:
        print(f"   ✅ {package} installed successfully")
        
        # Verify import
        try:
            __import__(package)
            print(f"   ✅ {package} imports successfully")
            success = True
            break
        except ImportError:
            print(f"   ⚠️  {package} installed but cannot import")
            continue
    else:
        print(f"   ❌ Failed to install {package}")
        if "not found" not in stderr.lower():
            print(f"   Error: {stderr[:200]}")

if not success:
    print("\n❌ Could not install any agent framework package")
    print("\n📌 Manual installation options:")
    print("   1. pip3 install phidata")
    print("   2. pip3 install git+https://github.com/phidatahq/phidata.git")
    print("   3. Check PyPI directly: https://pypi.org/search/?q=phidata")
    sys.exit(1)

# Install other required packages
print("\n📦 Installing other required packages...")
required = [
    "fastapi",
    "uvicorn",
    "httpx",
    "python-dotenv",
    "pydantic",
    "chromadb",
    "rich",
    "requests",
    "beautifulsoup4",
]

for package in required:
    print(f"   Installing {package}...", end=" ")
    success, _, _ = run_command(f"pip3 install {package}")
    print("✅" if success else "❌")

print("\n✅ Installation complete!")
print("\n📌 Next steps:")
print("   1. export NVIDIA_API_KEY='your-key'")
print("   2. cd ~/Helix/backend")
print("   3. python3 run_server.py")
