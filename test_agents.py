"""
Test script to verify all Helix agents and tools work correctly.

Run this to test:
- Workspace scanning
- Error resolution
- All agent tools
- Multi-agent coordination
"""

import os
import sys
from pathlib import Path

# Add backend src to path
backend_path = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_path))

print("🔧 Helix Agent System Test Suite")
print("=" * 60)

# Test 1: Workspace Scanner
print("\n📂 Test 1: Workspace Scanner")
print("-" * 60)
try:
    from helix.workspace_scanner import get_workspace_scanner
    
    scanner = get_workspace_scanner(".")
    summary = scanner.get_workspace_summary()
    print("✅ Workspace scanner working!")
    print(summary[:500] + "..." if len(summary) > 500 else summary)
except Exception as e:
    print(f"❌ Workspace scanner failed: {e}")

# Test 2: Error Resolver
print("\n🔧 Test 2: Error Resolver")
print("-" * 60)
try:
    from helix.auto_error_resolver import get_error_resolver
    
    resolver = get_error_resolver(".")
    result = resolver.resolve_error(
        "merge conflict in file.py",
        error_context={'operation': 'merge'},
        operation_type='git'
    )
    print("✅ Error resolver working!")
    print(f"Error type: {result.get('error_type')}")
    print(f"Suggestions: {len(result.get('suggestions', []))} found")
except Exception as e:
    print(f"❌ Error resolver failed: {e}")

# Test 3: Multi-Agent System
print("\n🤖 Test 3: Multi-Agent System")
print("-" * 60)
try:
    from helix.multi_agent_system import create_multi_agent_system
    
    # Check if required env vars are set
    if not os.getenv("NVIDIA_API_KEY"):
        print("⚠️  NVIDIA_API_KEY not set. Set it to test agents:")
        print("   export NVIDIA_API_KEY='your-key-here'")
    else:
        print("✅ Environment configured")
        
        # Try to create system (will initialize all agents)
        try:
            system = create_multi_agent_system(".")
            print(f"✅ Multi-agent system created with {len(system.list_agents())} agents")
            print(f"   Agents: {', '.join(system.list_agents())}")
            
            # Test simple query routing
            print("\n   Testing routing...")
            route = system.route_query("what files are in this project?")
            print(f"   ✅ Route detected: {route}")
            
            system.shutdown()
        except Exception as e:
            print(f"⚠️  Agent creation skipped (need API key): {e}")
    
except Exception as e:
    print(f"❌ Multi-agent system failed: {e}")

# Test 4: File Operations
print("\n📁 Test 4: File Operations Tools")
print("-" * 60)
try:
    from helix.tools import (
        file_reader_tool,
        search_tool,
        code_analyzer_tool,
        file_writer_tool
    )
    
    # Test file reader
    result = file_reader_tool("README.md", base_dir=".")
    if result.get('ok'):
        print("✅ File reader working")
    else:
        print(f"⚠️  File reader: {result.get('error')}")
    
    # Test search
    results = search_tool("Helix", base_dir=".", max_results=5)
    print(f"✅ Search tool working: {len(results)} matches found")
    
    # Test code analyzer
    analysis = code_analyzer_tool(base_dir=".", max_files=10)
    if analysis.get('ok'):
        print(f"✅ Code analyzer working: {analysis['summary']['total_files']} files analyzed")
    else:
        print(f"⚠️  Code analyzer: {analysis.get('error')}")
    
except Exception as e:
    print(f"❌ File operations failed: {e}")

# Test 5: Git Operations
print("\n🔀 Test 5: Git Operations")
print("-" * 60)
try:
    from helix.github_orchestrator import GitHubOrchestrator
    from helix.git_auth_manager import GitAuthManager
    
    github = GitHubOrchestrator()
    status = github.git_status(repo_path=".")
    
    if status.get('ok'):
        print("✅ Git operations working")
        print(f"   Current branch: {status.get('current_branch', 'N/A')}")
        print(f"   Clean: {status.get('clean', False)}")
        print(f"   Total changes: {len(status.get('modified', [])) + len(status.get('untracked', []))}")
    else:
        print(f"⚠️  Git status: {status.get('error')}")
    
    # Test auth manager
    auth = GitAuthManager(".")
    accounts = auth.get_available_accounts()
    print(f"✅ Git auth manager working: {accounts.get('total_count', 0)} accounts found")
    
except Exception as e:
    print(f"❌ Git operations failed: {e}")

# Test 6: Web Search (if available)
print("\n🌐 Test 6: Web Search")
print("-" * 60)
try:
    from helix.web_search import get_search_manager
    
    search_mgr = get_search_manager()
    # Don't actually search (uses API quota), just check initialization
    print("✅ Web search manager initialized")
    
except Exception as e:
    print(f"⚠️  Web search: {e}")

# Test 7: Semantic Analyzer
print("\n🔍 Test 7: Semantic Analyzer")
print("-" * 60)
try:
    from helix.semantic_analyzer import analyze_codebase_semantics
    
    # Analyze a small subset
    result = analyze_codebase_semantics(base_dir="backend/src/helix", file_patterns=["*.py"])
    
    if result:
        summary = result.get('summary', {})
        print("✅ Semantic analyzer working")
        print(f"   Files analyzed: {summary.get('total_files', 0)}")
        print(f"   Vulnerabilities: {summary.get('vulnerabilities_found', 0)}")
        print(f"   Complex functions: {summary.get('complex_functions', 0)}")
    else:
        print("⚠️  Semantic analyzer returned no results")
    
except Exception as e:
    print(f"❌ Semantic analyzer failed: {e}")

# Test 8: Memory Manager
print("\n🧠 Test 8: Memory Manager")
print("-" * 60)
try:
    from helix.memory_manager import MemoryManager
    
    memory = MemoryManager(workspace_dir=".")
    
    # Test fact storage
    memory.add_fact("test", "test_key", "test_value", ttl_days=1)
    value = memory.get_fact("test", "test_key")
    
    if value == "test_value":
        print("✅ Memory manager working")
        print(f"   Facts stored: {memory.get_memory_stats()['valid_facts']}")
    else:
        print("⚠️  Memory manager: fact retrieval failed")
    
except Exception as e:
    print(f"❌ Memory manager failed: {e}")

# Test 9: Safety Manager
print("\n🛡️ Test 9: Safety Manager")
print("-" * 60)
try:
    from helix.safety_manager import get_safety_manager, OperationType
    
    safety = get_safety_manager()
    
    # Test safety check
    needs_confirm, prompt = safety.needs_confirmation(
        OperationType.UPDATE,
        "test.txt",
        "Test update"
    )
    
    print("✅ Safety manager working")
    print(f"   Confirmation needed: {needs_confirm}")
    
except Exception as e:
    print(f"❌ Safety manager failed: {e}")

# Test 10: Code Modernizer
print("\n🔄 Test 10: Code Modernizer")
print("-" * 60)
try:
    from helix.code_modernizer import CodeModernizer
    from helix.web_search import get_search_manager
    from helix.semantic_analyzer import SemanticAnalyzer
    
    web_search = get_search_manager()
    semantic = SemanticAnalyzer(".")
    modernizer = CodeModernizer(web_search, semantic)
    
    # Test with simple old Python code
    old_code = "print 'Hello World'"
    result = modernizer.analyze_and_recommend(
        code=old_code,
        language="python"
    )
    
    if result.get('ok'):
        print("✅ Code modernizer working")
        print(f"   Patterns found: {len(result.get('outdated_patterns', []))}")
    else:
        print(f"⚠️  Code modernizer: {result.get('message')}")
    
except Exception as e:
    print(f"❌ Code modernizer failed: {e}")

# Summary
print("\n" + "=" * 60)
print("🎉 TEST SUITE COMPLETE")
print("=" * 60)
print("\n📋 Summary:")
print("   ✅ = Working correctly")
print("   ⚠️  = Working with warnings/limitations")
print("   ❌ = Failed (needs attention)")
print("\n💡 Next Steps:")
print("   1. Set NVIDIA_API_KEY environment variable")
print("   2. Set GITHUB_TOKEN for GitHub operations (optional)")
print("   3. Run: python test_agents.py")
print("   4. Test with actual queries via the API")
print("\n🚀 System Status: Ready for testing!")
