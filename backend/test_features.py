"""Test script to verify all Helix Orchestrator features.

Run this to check if all components are properly installed and configured.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("=" * 70)
print("HELIX AI CODE ORCHESTRATOR - FEATURE TEST")
print("=" * 70)
print()

# Test 1: Safety Manager
print("1️⃣ Testing Safety Manager...")
try:
    from src.helix.safety_manager import get_safety_manager, SafetyMode, OperationType
    
    safety = get_safety_manager(mode=SafetyMode.NORMAL)
    needs_confirm, prompt = safety.needs_confirmation(
        OperationType.CREATE,
        "test.py",
        "Creating test file"
    )
    
    print(f"   ✅ Safety Manager loaded")
    print(f"   → Confirmation needed: {needs_confirm}")
    print(f"   → Prompt: {prompt[:50]}...")
    print()
except Exception as e:
    print(f"   ❌ Failed: {e}")
    print()

# Test 2: Semantic Analyzer
print("2️⃣ Testing Semantic Analyzer...")
try:
    from src.helix.semantic_analyzer import analyze_codebase_semantics
    
    # Analyze current directory (limited)
    result = analyze_codebase_semantics(
        base_dir="./src",
        file_patterns=["**/*.py"]
    )
    
    summary = result.get('summary', {})
    print(f"   ✅ Semantic Analyzer loaded")
    print(f"   → Files analyzed: {summary.get('total_files', 0)}")
    print(f"   → Vulnerabilities: {summary.get('vulnerabilities_found', 0)}")
    print(f"   → Circular deps: {summary.get('circular_dependencies', 0)}")
    print()
except Exception as e:
    print(f"   ❌ Failed: {e}")
    print()

# Test 3: Web Search Manager
print("3️⃣ Testing Web Search Manager...")
try:
    from src.helix.web_search import get_search_manager
    import os
    
    search = get_search_manager()
    
    # Check if API keys are configured
    tavily_ok = bool(os.getenv("TAVILY_API_KEY"))
    exa_ok = bool(os.getenv("EXA_API_KEY"))
    
    print(f"   ✅ Web Search Manager loaded")
    print(f"   → Tavily API: {'✓ Configured' if tavily_ok else '✗ Not configured'}")
    print(f"   → Exa API: {'✓ Configured' if exa_ok else '✗ Not configured'}")
    
    if not tavily_ok and not exa_ok:
        print(f"   ⚠️  Add TAVILY_API_KEY or EXA_API_KEY to .env for web search")
    print()
except Exception as e:
    print(f"   ❌ Failed: {e}")
    print()

# Test 4: GitHub Orchestrator
print("4️⃣ Testing GitHub Orchestrator...")
try:
    from src.helix.github_orchestrator import get_github_orchestrator
    import os
    
    gh = get_github_orchestrator()
    
    # Check if token is configured
    token_ok = bool(os.getenv("GITHUB_TOKEN"))
    
    # Try to get git status (doesn't require GitHub token)
    try:
        status = gh.git_status()
        git_ok = status.get('ok', False)
        current_branch = status.get('current_branch', 'unknown')
    except:
        git_ok = False
        current_branch = 'error'
    
    print(f"   ✅ GitHub Orchestrator loaded")
    print(f"   → Git available: {'✓ Yes' if git_ok else '✗ No (git not installed?)'}")
    print(f"   → Current branch: {current_branch}")
    print(f"   → GitHub token: {'✓ Configured' if token_ok else '✗ Not configured'}")
    
    if not token_ok:
        print(f"   ⚠️  Add GITHUB_TOKEN to .env for GitHub API features")
    print()
except Exception as e:
    print(f"   ❌ Failed: {e}")
    print()

# Test 5: Agent Creation
print("5️⃣ Testing Agent Creation...")
try:
    from src.helix.agno_agent import create_agent
    import os
    
    # Check if NVIDIA API key is set
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    
    if not nvidia_key:
        print(f"   ⚠️  NVIDIA_API_KEY not set - skipping agent creation")
        print(f"   → Add NVIDIA_API_KEY to .env to test agent")
        print()
    else:
        print(f"   🔄 Creating agent (this may take a moment)...")
        agent = create_agent(
            name="Helix Test",
            workspace_dir="./test_workspace"
        )
        
        print(f"   ✅ Agent created successfully")
        print(f"   → Model: {agent.model.id if hasattr(agent, 'model') else 'unknown'}")
        print(f"   → Tools: {len(agent.tools) if hasattr(agent, 'tools') else 0}")
        print()
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    print(f"   Error details: {traceback.format_exc()[:200]}...")
    print()

# Test 6: File Operations
print("6️⃣ Testing File Operations...")
try:
    from src.helix.tools import file_reader_tool, file_writer_tool, code_analyzer_tool
    
    print(f"   ✅ File tools loaded")
    
    # Test code analyzer
    result = code_analyzer_tool(base_dir="./src", max_files=50)
    if result.get('ok'):
        summary = result.get('summary', {})
        print(f"   → Analyzer: Scanned {summary.get('total_files', 0)} files")
    
    print()
except Exception as e:
    print(f"   ❌ Failed: {e}")
    print()

# Summary
print("=" * 70)
print("FEATURE SUMMARY")
print("=" * 70)
print()
print("✅ Core Features (Always Available):")
print("   • Safety Manager")
print("   • Semantic Analyzer")
print("   • Code Analyzer")
print("   • File Operations")
print()
print("⚙️  Optional Features (Require API Keys):")
print("   • Web Search (TAVILY_API_KEY or EXA_API_KEY)")
print("   • GitHub API (GITHUB_TOKEN)")
print("   • NVIDIA Agent (NVIDIA_API_KEY)")
print()
print("📚 Documentation:")
print("   • Quick Start: QUICKSTART.md")
print("   • Complete Guide: ORCHESTRATOR_GUIDE.md")
print("   • Implementation: IMPLEMENTATION_SUMMARY.md")
print()
print("🚀 To start server:")
print("   python run_server.py")
print()
print("=" * 70)
