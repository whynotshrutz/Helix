"""
Direct test of modernize_code_tool function
"""
import sys
sys.path.insert(0, 'C:/Users/sriha/Hackathon/Helix/backend/src')

from helix.tools import modernize_code_tool

old_python_code = '''
print "Hello World"

name = "John"
message = "My name is %s" % name

def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
'''

print("=" * 80)
print("DIRECT TEST: modernize_code_tool")
print("=" * 80)

try:
    print("\n📝 Testing with old Python code...")
    result = modernize_code_tool(
        code=old_python_code,
        file_path="test.py",
        language="python",
        base_dir="C:/Users/sriha/Hackathon/Helix"
    )
    
    print(f"\n✅ Result OK: {result.get('ok', False)}")
    print(f"Language: {result.get('language', 'N/A')}")
    
    if result.get('outdated_patterns'):
        print(f"\n⚠️ Outdated Patterns Found: {len(result['outdated_patterns'])}")
        for p in result['outdated_patterns'][:3]:
            print(f"  - [{p['severity'].upper()}] {p['pattern']}")
    
    if result.get('recommendations'):
        print(f"\n💡 Recommendations: {len(result['recommendations'])}")
        for r in result['recommendations'][:3]:
            print(f"  - [{r['priority'].upper()}] {r['title']}")
    
    if result.get('migration_guide'):
        guide = result['migration_guide']
        print(f"\n📋 Migration Guide:")
        print(f"  Steps: {len(guide.get('steps', []))}")
        print(f"  Estimated Time: {guide.get('estimated_time', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("✅ Direct tool test completed successfully!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
