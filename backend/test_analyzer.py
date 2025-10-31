"""Test the code analyzer tool."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from helix.tools import code_analyzer_tool

if __name__ == "__main__":
    workspace = Path(__file__).parent.parent / "workspace"
    
    print("🔍 Testing Code Analyzer Tool")
    print("=" * 60)
    print(f"Analyzing workspace: {workspace}")
    print()
    
    result = code_analyzer_tool(base_dir=str(workspace))
    
    if result['ok']:
        print("✅ Analysis completed successfully!")
        print()
        print(f"📊 Summary:")
        print(f"   Files: {result['summary']['total_files']}")
        print(f"   Lines: {result['summary']['total_lines']:,}")
        print(f"   Languages: {', '.join(result['summary']['languages'].keys())}")
        print()
        
        if result['issues']:
            print(f"⚠️ Issues ({len(result['issues'])}):")
            for issue in result['issues'][:5]:
                print(f"   • {issue}")
            if len(result['issues']) > 5:
                print(f"   ... and {len(result['issues']) - 5} more")
            print()
        
        if result['recommendations']:
            print("💡 Recommendations:")
            for rec in result['recommendations']:
                print(f"   ✓ {rec}")
    else:
        print(f"❌ Analysis failed: {result.get('error')}")
