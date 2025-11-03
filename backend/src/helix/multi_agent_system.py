"""Multi-Agent System for Helix - Parallel specialized agents working together.

This module implements a coordinator pattern where specialized agents handle specific tasks:
- Code Analyst Agent: Code analysis, semantic checks, vulnerabilities
- File Operations Agent: File read/write, search operations
- Web Research Agent: Web searches, documentation lookup
- Git Operations Agent: Version control, commits, PRs
"""
from typing import Optional, Dict, Any, List
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

try:
    from agno.agent import Agent
    from agno.models.nvidia import Nvidia
    from agno.tools import tool
    from agno.db.sqlite import SqliteDb
    from agno.knowledge.knowledge import Knowledge
    from agno.vectordb.chroma import ChromaDb
    from .nvidia_model_wrapper import NvidiaModelWrapper
except Exception as e:
    Agent = None
    Nvidia = None
    tool = None
    SqliteDb = None
    Knowledge = None
    ChromaDb = None
    NvidiaModelWrapper = None

from .tools import (
    file_reader_tool, 
    code_executor_tool, 
    search_tool, 
    doc_helper_tool,
    code_analyzer_tool,
    file_writer_tool
)
from .semantic_analyzer import analyze_codebase_semantics
from .web_search import get_search_manager
from .github_orchestrator import get_github_orchestrator
from .safety_manager import get_safety_manager, SafetyMode
from .memory_manager import MemoryManager


class MultiAgentSystem:
    """Orchestrates multiple specialized agents working in parallel."""
    
    def __init__(self, workspace_dir: str = "."):
        """Initialize the multi-agent system.
        
        Args:
            workspace_dir: Workspace directory for file operations
        """
        self.workspace_dir = workspace_dir
        self.agents: Dict[str, Agent] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize shared resources
        self.model = self._create_model()
        self.knowledge = self._create_knowledge()
        self.db = self._create_db()
        self.memory_manager = MemoryManager(workspace_dir=workspace_dir)
        
        # Create specialized agents
        self._create_specialized_agents()
    
    def _create_model(self):
        """Create NVIDIA model wrapper."""
        if NvidiaModelWrapper is None:
            raise RuntimeError("NVIDIA model wrapper not available")
        
        nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        if not nvidia_api_key:
            raise RuntimeError("NVIDIA_API_KEY required")
        
        model_id = os.getenv("NVIDIA_MODEL_ID", "nvidia/llama-3_1-nemotron-nano-8b-v1")
        base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        
        print(f"🔄 Initializing NVIDIA model for multi-agent system: {model_id}")
        
        try:
            model = NvidiaModelWrapper(
                id=model_id,
                api_key=nvidia_api_key,
                base_url=base_url
            )
            print(f"✅ NVIDIA model initialized")
            return model
        except Exception as e:
            raise RuntimeError(f"Model initialization failed: {e}")
    
    def _create_knowledge(self):
        """Create shared knowledge base."""
        try:
            if Knowledge is None or ChromaDb is None:
                return None
            
            from .nvidia_embedder import NvidiaEmbedder
            
            chroma_path = os.getenv("CHROMA_PERSIST_DIR", "./tmp/chroma")
            embed_model = os.getenv("NVIDIA_EMBED_MODEL", "nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1")
            
            embedder = NvidiaEmbedder(id=embed_model, enable_batch=True)
            
            vector_db = ChromaDb(
                collection="helix_multi_agent",
                path=chroma_path,
                persistent_client=True,
                embedder=embedder,
            )
            
            knowledge = Knowledge(
                name="Helix Multi-Agent Knowledge",
                description="Shared knowledge base for specialized agents",
                vector_db=vector_db,
            )
            
            print(f"✅ Shared knowledge base initialized")
            return knowledge
        except Exception as e:
            print(f"⚠️ Knowledge base not available: {e}")
            return None
    
    def _create_db(self):
        """Create shared database."""
        try:
            if SqliteDb is None:
                return None
            return SqliteDb(db_file="./tmp/helix_multi_agent.db")
        except Exception:
            return None
    
    def _create_specialized_agents(self):
        """Create all specialized agents."""
        print("🔄 Creating specialized agents...")
        
        # 0. Orchestrator Agent (for routing)
        self.orchestrator = self._create_orchestrator_agent()
        
        # 1. Code Analyst Agent
        self.agents['code_analyst'] = self._create_code_analyst_agent()
        
        # 2. File Operations Agent
        self.agents['file_ops'] = self._create_file_ops_agent()
        
        # 3. Web Research Agent
        self.agents['web_research'] = self._create_web_research_agent()
        
        # 4. Git Operations Agent
        self.agents['git_ops'] = self._create_git_ops_agent()
        
        print(f"✅ Created {len(self.agents)} specialized agents + orchestrator")
    
    def _create_orchestrator_agent(self):
        """Create Orchestrator Agent - routes queries and manages memory."""
        
        @tool(name="store_fact")
        def store_fact(category: str, key: str, value: str, ttl_days: int = 30) -> str:
            """Store a fact in persistent memory (e.g., user preferences, project info).
            
            Args:
                category: Fact category (project, user_preference, code_pattern, decision)
                key: Fact key (e.g., 'preferred_language', 'main_framework')
                value: Fact value
                ttl_days: Time-to-live in days (default 30)
            """
            success = self.memory_manager.add_fact(category, key, value, ttl_days)
            if success:
                return f"✅ Stored: {category}/{key} = {value} (expires in {ttl_days} days)"
            return "❌ Failed to store fact"
        
        @tool(name="recall_fact")
        def recall_fact(category: str, key: str) -> str:
            """Recall a specific fact from memory.
            
            Args:
                category: Fact category
                key: Fact key
            """
            value = self.memory_manager.get_fact(category, key)
            if value is not None:
                return f"📌 {category}/{key} = {value}"
            return f"❌ No fact found for {category}/{key}"
        
        @tool(name="search_memory")
        def search_memory(category: str = None, query: str = None) -> str:
            """Search stored facts by category or query string.
            
            Args:
                category: Filter by category (optional)
                query: Search in keys/values (optional)
            """
            facts = self.memory_manager.search_facts(category, query)
            if not facts:
                return "No facts found"
            
            output = [f"🔍 Found {len(facts)} fact(s):", ""]
            for fact in facts[:10]:  # Limit to 10
                output.append(f"  [{fact['category']}] {fact['key']} = {fact['value']}")
            
            if len(facts) > 10:
                output.append(f"\n  ... and {len(facts) - 10} more")
            
            return "\n".join(output)
        
        @tool(name="update_project_context")
        def update_project_context(languages: str = None, frameworks: str = None, 
                                   key_files: str = None, description: str = None) -> str:
            """Update project context (tech stack, key files, description).
            
            Args:
                languages: Comma-separated languages (e.g., 'Python,JavaScript')
                frameworks: Comma-separated frameworks (e.g., 'React,FastAPI')
                key_files: Comma-separated key files (e.g., 'main.py,App.tsx')
                description: Project description
            """
            updates = {}
            if languages:
                updates['languages'] = [l.strip() for l in languages.split(',')]
            if frameworks:
                updates['frameworks'] = [f.strip() for f in frameworks.split(',')]
            if key_files:
                updates['key_files'] = [k.strip() for k in key_files.split(',')]
            if description:
                updates['description'] = description
            
            success = self.memory_manager.update_project_context(**updates)
            if success:
                return f"✅ Project context updated: {', '.join(updates.keys())}"
            return "❌ Failed to update project context"
        
        @tool(name="get_project_context")
        def get_project_context() -> str:
            """Get current project context."""
            context = self.memory_manager.get_project_context()
            
            output = ["📋 PROJECT CONTEXT:", ""]
            if context.get('description'):
                output.append(f"Description: {context['description']}")
            if context.get('languages'):
                output.append(f"Languages: {', '.join(context['languages'])}")
            if context.get('frameworks'):
                output.append(f"Frameworks: {', '.join(context['frameworks'])}")
            if context.get('key_files'):
                output.append(f"Key Files: {', '.join(context['key_files'])}")
            
            return "\n".join(output) if len(output) > 2 else "No project context stored"
        
        @tool(name="memory_stats")
        def memory_stats() -> str:
            """Get memory statistics."""
            stats = self.memory_manager.get_memory_stats()
            
            return f"""📊 MEMORY STATS:
  Conversation messages: {stats['conversation_messages']}
  Facts stored: {stats['valid_facts']} valid, {stats['expired_facts']} expired
  Memory file: {stats['memory_file']}
  File size: {stats['file_size_kb']} KB
  Created: {stats['created_at']}
  Last updated: {stats['last_updated']}"""
        
        agent = Agent(
            name="Orchestrator",
            model=self.model,
            knowledge=None,  # Orchestrator doesn't need knowledge base
            search_knowledge=False,
            tools=[store_fact, recall_fact, search_memory, update_project_context, 
                   get_project_context, memory_stats],
            markdown=False,
            instructions=[
                "You are an intelligent coordinator for a multi-agent system with memory.",
                "",
                "PRIMARY FUNCTIONS:",
                "1. Route queries to specialized agents based on semantic understanding",
                "2. Manage persistent memory (facts, project context, conversation history)",
                "3. ONLY route to agents when user has a SPECIFIC request or task",
                "",
                "IMPORTANT - GREETINGS AND SIMPLE QUERIES:",
                "- If user just says 'hi', 'hello', 'hey' → Respond directly, DON'T route to any agent",
                "- If user asks general questions without specific task → Respond directly",
                "- ONLY route to agents when there's a clear action or analysis needed",
                "",
                "AVAILABLE SPECIALIZED AGENTS:",
                "",
                "🔬 code_analyst - Code understanding and analysis",
                "   Handles: code review, bug detection, optimization suggestions, complexity analysis,",
                "   security vulnerabilities, code execution, modernization recommendations,",
                "   repository-wide analysis, semantic understanding, technical explanations",
                "",
                "📁 file_ops - File system operations",
                "   Handles: reading files, writing files, searching file content,",
                "   listing directories, finding files by name/pattern",
                "",
                "🌐 web_research - Internet research and documentation",
                "   Handles: searching for information, finding documentation,",
                "   fetching web content, researching best practices, tutorials,",
                "   looking up API references, technology comparisons",
                "",
                "🔧 git_ops - Version control and GitHub operations",
                "   Handles: git status, commits, branches, push/pull, conflict resolution,",
                "   repository creation, pull requests, GitHub management",
                "",
                "ROUTING DECISION PROCESS:",
                "1. Is this just a greeting or casual conversation? → Handle yourself, don't route",
                "2. Understand the INTENT and GOAL of the user's query",
                "3. Does user want a specific ACTION or ANALYSIS? → Route to appropriate agent",
                "4. Respond with ONLY the agent name (code_analyst, file_ops, web_research, git_ops)",
                "5. Use 'parallel' if query needs multiple agents working together",
                "6. For memory operations (storing/recalling info), handle directly with your tools",
                "",
                "ROUTING EXAMPLES (understand semantics, not keywords):",
                "- 'What does this function do?' → code_analyst (needs code understanding)",
                "- 'Is this approach secure?' → code_analyst (security analysis)",
                "- 'Show me that configuration file' → file_ops (file reading)",
                "- 'How does React hooks work?' → web_research (needs external knowledge)",
                "- 'What's the best way to handle async?' → web_research (best practices)",
                "- 'Save these changes' → git_ops (version control)",
                "- 'Compare my code to best practices online' → parallel (code_analyst + web_research)",
                "",
                "MEMORY TOOLS:",
                "- store_fact: Store user preferences, decisions, patterns",
                "- recall_fact: Retrieve stored facts by category and key",
                "- search_memory: Search facts by category or query string",
                "- update_project_context: Store tech stack, frameworks, key files",
                "- get_project_context: Retrieve project information",
                "- memory_stats: Show memory usage statistics",
                "",
                "AUTO-STORE IMPORTANT INFORMATION:",
                "When user mentions preferences, tech stack, or project details:",
                "- Automatically use store_fact or update_project_context",
                "- Categories: project, user_preference, code_pattern, decision",
                "- Use descriptive keys",
                "- TTL: 30 days default, 90 for critical info",
                "",
                "REMEMBER: Understand the user's INTENT, not just keywords.",
                "Think about what they're trying to accomplish."
            ],
            description="Orchestrator agent for routing and memory management"
        )
        
        print("  ✅ Orchestrator Agent created with memory tools")
        return agent
    
    def _create_code_analyst_agent(self) -> Agent:
        """Create Code Analyst Agent - specialized in code analysis."""
        
        @tool(name="analyze_codebase")
        def analyze_codebase(directory: str = ".") -> str:
            """Analyze entire codebase and provide recommendations."""
            result = code_analyzer_tool(base_dir=self.workspace_dir if directory == "." else directory)
            if not result.get('ok'):
                return f"Error: {result.get('error', 'Unknown error')}"
            
            output = ["📊 CODEBASE ANALYSIS", "=" * 50, ""]
            summary = result['summary']
            output.append(f"Files: {summary['total_files']}, Lines: {summary['total_lines']:,}")
            
            if result['issues']:
                output.append(f"\n⚠️ Issues ({len(result['issues'])}):")
                for issue in result['issues'][:5]:
                    output.append(f"  • {issue}")
            
            if result['recommendations']:
                output.append("\n💡 Recommendations:")
                for rec in result['recommendations']:
                    output.append(f"  ✓ {rec}")
            
            return "\n".join(output)
        
        @tool(name="analyze_semantics")
        def analyze_semantics(directory: str = ".") -> str:
            """Deep semantic analysis: dependencies, vulnerabilities, complexity."""
            target_dir = self.workspace_dir if directory == "." else directory
            
            try:
                result = analyze_codebase_semantics(base_dir=target_dir)
                
                if not result:
                    return "❌ Analysis failed"
                
                output = ["🔍 SEMANTIC ANALYSIS", "=" * 50, ""]
                
                summary = result.get('summary', {})
                output.append(f"Files: {summary.get('total_files', 0)}, Vulnerabilities: {summary.get('vulnerabilities_found', 0)}")
                
                vulns = result.get('vulnerabilities', [])
                if vulns:
                    output.append(f"\n🚨 VULNERABILITIES ({len(vulns)}):")
                    for v in vulns[:3]:
                        output.append(f"  [{v['severity'].upper()}] {v['title']}")
                        output.append(f"    {v['file']}:{v['line']}")
                
                return "\n".join(output)
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        @tool(name="execute_code")
        def execute_code(code: str, language: str = "python") -> str:
            """Execute code safely."""
            result = code_executor_tool(code, language=language)
            if isinstance(result, dict):
                output = [f"Executed {language}:"]
                if result.get("stdout"):
                    output.append(f"Output: {result['stdout']}")
                if result.get("stderr"):
                    output.append(f"Errors: {result['stderr']}")
                return "\n".join(output)
            return str(result)
        
        @tool(name="modernize_code")
        def modernize_code(code: str, file_path: str = None, language: str = None) -> str:
            """Analyze old/legacy code and provide modernization recommendations based on latest best practices from web research.
            
            Args:
                code: The source code to analyze
                file_path: Optional file path (helps detect language)
                language: Optional language override (python, javascript, typescript, java, go, rust, cpp, c)
            
            Returns:
                Detailed analysis with outdated patterns, modern alternatives, migration guide, and web-researched best practices.
            """
            from .tools import modernize_code_tool
            
            result = modernize_code_tool(
                code=code,
                file_path=file_path,
                language=language,
                base_dir=self.workspace_dir
            )
            
            if not result.get('ok'):
                return f"❌ Modernization analysis failed: {result.get('message', 'Unknown error')}"
            
            output = ["🔄 CODE MODERNIZATION ANALYSIS", "=" * 60, ""]
            output.append(f"Language: {result['language']}")
            if result.get('file_path'):
                output.append(f"File: {result['file_path']}")
            output.append("")
            
            # Outdated patterns
            patterns = result.get('outdated_patterns', [])
            if patterns:
                output.append(f"⚠️ OUTDATED PATTERNS DETECTED ({len(patterns)}):")
                for p in patterns:
                    output.append(f"  [{p['severity'].upper()}] {p['pattern']}")
                    output.append(f"  └─ {p['description']}")
                output.append("")
            
            # Recommendations
            recs = result.get('recommendations', [])
            if recs:
                output.append("💡 MODERNIZATION RECOMMENDATIONS:")
                for r in recs:
                    priority = r.get('priority', 'medium').upper()
                    output.append(f"  [{priority}] {r['title']}")
                    if r.get('alternative'):
                        output.append(f"  └─ Modern alternative: {r['alternative']}")
                    if r.get('example'):
                        output.append(f"  └─ Example:\n{r['example']}")
                output.append("")
            
            # Migration guide
            guide = result.get('migration_guide', {})
            if guide.get('steps'):
                output.append("📋 MIGRATION GUIDE:")
                output.append(f"  Estimated time: {guide.get('estimated_time', 'N/A')}")
                output.append(f"  Difficulty: {guide.get('difficulty', 'N/A')}")
                output.append("")
                for step in guide['steps'][:3]:  # Show first 3 steps
                    output.append(f"  Step {step['step']}: {step['title']}")
                    output.append(f"  └─ {step['description']}")
            
            return "\n".join(output)
        
        @tool(name="analyze_repository")
        def analyze_repository(max_files: int = 50, focus_paths: str = None, request_confirmation: bool = True) -> str:
            """Analyze entire repository for outdated patterns and generate comprehensive modernization recommendations.
            
            Args:
                max_files: Maximum number of files to analyze (default: 50)
                focus_paths: Optional comma-separated list of specific paths to focus on
                request_confirmation: Whether to request user confirmation before applying changes (default: True)
            
            Returns:
                Repository-wide analysis with aggregated recommendations, migration plan, and best practices research.
                If request_confirmation=True, asks user for approval before suggesting to apply changes.
            """
            from .repo_analyzer import analyze_repo_and_recommend_tool
            from .recommendation_confirmation import get_confirmation_manager
            
            focus_list = None
            if focus_paths:
                focus_list = [p.strip() for p in focus_paths.split(',')]
            
            result = analyze_repo_and_recommend_tool(
                workspace_dir=self.workspace_dir,
                max_files=max_files,
                focus_paths=focus_list
            )
            
            if not result.get('ok'):
                return f"❌ Repository analysis failed: {result.get('error', 'Unknown error')}"
            
            output = ["� REPOSITORY-WIDE CODE ANALYSIS", "=" * 70, ""]
            output.append(f"Workspace: {result['workspace']}")
            output.append(f"Files analyzed: {result['files_analyzed']}")
            output.append(f"Files with issues: {result['files_with_issues']}")
            output.append(f"Total patterns found: {result['total_patterns']}")
            output.append("")
            
            # Severity breakdown
            severity_counts = result.get('severity_counts', {})
            if severity_counts:
                output.append("⚠️ SEVERITY BREAKDOWN:")
                output.append(f"  🔴 High priority: {severity_counts.get('high', 0)}")
                output.append(f"  🟡 Medium priority: {severity_counts.get('medium', 0)}")
                output.append(f"  🟢 Low priority: {severity_counts.get('low', 0)}")
                output.append("")
            
            # Top recommendations
            recs = result.get('recommendations', [])
            if recs:
                output.append(f"💡 TOP RECOMMENDATIONS ({len(recs)}):")
                for i, r in enumerate(recs[:10], 1):  # Show top 10
                    priority = r.get('priority', 'medium').upper()
                    output.append(f"  {i}. [{priority}] {r['title']}")
                    output.append(f"     File: {r['file']}")
                    if r.get('alternative'):
                        output.append(f"     Alternative: {r['alternative']}")
                output.append("")
            
            # Migration plan
            plan = result.get('migration_plan', {})
            if plan:
                output.append("📋 MIGRATION PLAN:")
                output.append(f"  Total items: {plan.get('total_recommendations', 0)}")
                output.append(f"  Estimated time: {plan.get('estimated_time', 'Unknown')}")
                output.append(f"  Difficulty: {plan.get('difficulty', 'Unknown')}")
                output.append("")
                output.append("  Steps:")
                for step in plan.get('steps', [])[:5]:  # Show first 5 steps
                    output.append(f"    {step['step']}. {step['title']}")
                    output.append(f"       {step['description']}")
                output.append("")
            
            # Best practices links
            best_practices = result.get('best_practices', {})
            if best_practices:
                output.append("🌐 RESEARCHED BEST PRACTICES:")
                for pattern, info in list(best_practices.items())[:3]:  # Show top 3
                    output.append(f"  Pattern: {pattern}")
                    output.append(f"  Found in {info['count']} files")
                    if info.get('resources'):
                        for res in info['resources'][:2]:  # Show 2 resources per pattern
                            output.append(f"    📎 {res.get('title', 'Resource')}")
                            output.append(f"       {res.get('url', '')}")
                output.append("")
            
            # Request user confirmation if enabled
            if request_confirmation and recs:
                confirmation_mgr = get_confirmation_manager()
                
                # Create changes list from recommendations
                changes = []
                for rec in recs[:5]:  # Top 5 for confirmation
                    changes.append({
                        'file': rec.get('file', 'Unknown'),
                        'type': 'modernization',
                        'description': rec.get('title', 'No description'),
                        'alternative': rec.get('alternative', '')
                    })
                
                # Create confirmation request
                conf_request = confirmation_mgr.create_confirmation_request(
                    title="Repository Modernization Recommendations",
                    description=f"Found {len(recs)} recommendations across {result['files_with_issues']} files. Would you like to proceed with applying these changes?",
                    changes=changes,
                    priority="high" if severity_counts.get('high', 0) > 0 else "medium"
                )
                
                # Add confirmation prompt to output
                output.append("\n" + "=" * 70)
                output.append("🔔 USER CONFIRMATION REQUIRED")
                output.append("=" * 70)
                output.append(confirmation_mgr.format_for_user(conf_request))
            
            return "\n".join(output)
        
        @tool(name="confirm_recommendation")
        def confirm_recommendation(confirmation_id: str, action: str = "yes") -> str:
            """Confirm or reject a recommendation.
            
            Args:
                confirmation_id: ID of the confirmation request (e.g., 'confirm_1')
                action: 'yes' to confirm, 'no' to reject
            
            Returns:
                Confirmation result
            """
            from .recommendation_confirmation import get_confirmation_manager
            
            confirmation_mgr = get_confirmation_manager()
            
            if action.lower() in ['yes', 'confirm', 'accept']:
                if confirmation_mgr.confirm(confirmation_id):
                    request = confirmation_mgr.get_request(confirmation_id)
                    return f"✅ Recommendation confirmed: {request['title']}\n\n   You can now proceed to apply the changes. Use the modernization tools to implement the recommendations."
                else:
                    return f"❌ Confirmation ID not found: {confirmation_id}"
            
            elif action.lower() in ['no', 'reject', 'cancel', 'decline']:
                if confirmation_mgr.reject(confirmation_id):
                    return f"❌ Recommendation rejected: {confirmation_id}\n\n   Changes will not be applied."
                else:
                    return f"❌ Confirmation ID not found: {confirmation_id}"
            
            else:
                return f"❌ Invalid action: {action}. Use 'yes' or 'no'"
        
        agent = Agent(
            name="Code Analyst",
            model=self.model,
            knowledge=self.knowledge,
            search_knowledge=False,
            tools=[analyze_codebase, analyze_semantics, execute_code, modernize_code, analyze_repository, confirm_recommendation],
            markdown=True,
            instructions=[
                "You are an expert Code Analyst and helpful programming assistant.",
                "",
                "YOUR CAPABILITIES:",
                "- Generate code with detailed explanations",
                "- Code analysis and quality checks",
                "- Security vulnerability detection",
                "- Code modernization and legacy code updates",
                "- Repository-wide analysis and recommendations",
                "",
                "COMMUNICATION STYLE:",
                "- Be conversational and helpful",
                "- Explain your code with comments",
                "- Provide context and reasoning",
                "- Suggest best practices",
                "- Ask clarifying questions when needed",
                "",
                "🚨 CRITICAL - ONLY USE TOOLS WHEN EXPLICITLY REQUESTED:",
                "- DO NOT automatically analyze repository unless user asks for it",
                "- DO NOT execute code unless user wants to run/test it",
                "- DO NOT use modernize_code unless user mentions outdated code or modernization",
                "- If user asks a question, ANSWER it without running tools",
                "- ONLY run tools when user clearly wants that specific action",
                "",
                "UNDERSTANDING USER INTENT:",
                "Listen to what the user is trying to accomplish, not just specific words.",
                "",
                " CODE ANALYSIS - When user wants to understand or improve code:",
                "   Use: analyze_codebase() for general overview",
                "   Use: analyze_semantics() for deep dependency/vulnerability analysis",
                "   Consider: What specific insights would help them?",
                "",
                " CODE MODERNIZATION - When user has outdated code:",
                "   Recognize patterns like:",
                "   - Python 2 style (print statements, old string formatting, no type hints)",
                "   - Old JavaScript (var declarations, callbacks, jQuery, CommonJS)",
                "   - Deprecated libraries or patterns",
                "   - Missing modern features",
                "   ",
                "   For SINGLE FILE or CODE SNIPPET:",
                "   1. Call modernize_code(code=<code>, file_path=<filename>, language=<language>)",
                "   2. Returns: patterns found, web-researched alternatives, migration guide",
                "   3. Share complete output with user",
                "",
                "   ",
                "   For ENTIRE REPOSITORY or PROJECT-WIDE:",
                "   1. Understand scope: Does user want to analyze the whole codebase?",
                "   2. Call analyze_repository(max_files=50, focus_paths=None)",
                "   3. Returns: aggregated patterns, severity breakdown, migration plan, best practices",
                "   4. Use focus_paths='src/,tests/' to target specific directories",
                "   ",
                "   Recognize intent like:",
                "   - Wanting to modernize/update entire codebase",
                "   - Looking for patterns across all files",
                "   - Planning a migration or upgrade",
                "   - Understanding technical debt across project",
                "",
                " CODE EXECUTION - When user wants to run/test code:",
                "   Use: execute_code(code, language)",
                "   Understand: Do they want to see output? Test functionality? Debug?",
                "",
                "SUPPORTED LANGUAGES:",
                "Python, JavaScript, TypeScript, Java, Go, Rust, C++, C",
                "",
                "REMEMBER: Focus on user's GOAL, not specific words they use.",
                "Think: What would actually help them accomplish their task?"
            ],
            description="Specialized agent for code generation, analysis and quality checks"
        )
        
        print("  ✅ Code Analyst Agent created")
        return agent
    
    def _create_file_ops_agent(self) -> Agent:
        """Create File Operations Agent - specialized in file management."""
        
        @tool(name="list_workspace_files")
        def list_workspace_files(pattern: str = "*", include_dirs: bool = False) -> str:
            """List all files in workspace matching pattern. Use this to explore what exists!
            
            Args:
                pattern: Glob pattern like '*.py', '**/*.js', '*' (all files)
                include_dirs: Include directories in results
            
            Returns:
                List of files found in workspace
            """
            from pathlib import Path
            
            try:
                workspace = Path(self.workspace_dir)
                if not workspace.exists():
                    return f"❌ Workspace not found: {self.workspace_dir}"
                
                files = []
                if '**' in pattern:
                    matches = workspace.glob(pattern)
                else:
                    matches = workspace.rglob(pattern) if '*' in pattern else [workspace / pattern]
                
                for p in matches:
                    if p.is_file() or (include_dirs and p.is_dir()):
                        rel_path = p.relative_to(workspace)
                        files.append(str(rel_path))
                
                if not files:
                    return f"No files matching '{pattern}' in workspace: {self.workspace_dir}"
                
                output = [f"📂 Workspace: {self.workspace_dir}"]
                output.append(f"Found {len(files)} files matching '{pattern}':")
                for f in sorted(files)[:50]:  # Show max 50
                    output.append(f"  📄 {f}")
                if len(files) > 50:
                    output.append(f"  ... and {len(files) - 50} more")
                
                return "\n".join(output)
            except Exception as e:
                return f"❌ Error listing files: {e}"
        
        @tool(name="read_file")
        def read_file(path: str) -> str:
            """Read a file from workspace to see its content."""
            result = file_reader_tool(path, base_dir=self.workspace_dir)
            if isinstance(result, dict):
                if result.get("ok"):
                    if result.get("type") == "file":
                        content = result['content']
                        lines = content.split('\n')
                        return f"File: {path}\nLines: {len(lines)}\n\n{content}"
                    elif result.get("type") == "dir":
                        files = result['files'][:20]  # First 20
                        return f"Directory: {path}\nContains {len(files)} files:\n" + "\n".join(f"  - {f}" for f in files)
                return f"Error: {result.get('error', 'file not found')}"
            return str(result)
        
        @tool(name="search_files")
        def search_files(query: str, use_regex: bool = False, max_results: int = 20) -> str:
            """Search for text inside files in workspace."""
            results = search_tool(query, base_dir=self.workspace_dir, use_regex=use_regex, max_results=max_results)
            if not results:
                return f"No matches for '{query}' in workspace files"
            
            output = [f"Found '{query}' in {len(results)} files:"]
            for r in results[:10]:
                output.append(f"  • {r['path']}: ...{r['snippet']}...")
            return "\n".join(output)
        
        agent = Agent(
            name="File Operations",
            model=self.model,
            knowledge=self.knowledge,
            search_knowledge=False,
            tools=[list_workspace_files, read_file, search_files],
            markdown=True,
            instructions=[
                f"You are a helpful File Operations assistant for workspace: {self.workspace_dir}",
                "",
                "YOUR ROLE:",
                "- Help users understand what files exist in the workspace",
                "- Show file contents when requested",
                "- Search for specific files or content",
                "- Provide clear, conversational responses",
                "",
                "AVAILABLE TOOLS:",
                "- list_workspace_files(pattern): List files matching a pattern (e.g., '*.py', 'src/**')",
                "- read_file(path): Read and show file contents",
                "- search_files(query): Search for text inside files",
                "",
                "WHEN USER ASKS:",
                "- 'what files are here?' → Use list_workspace_files('*')",
                "- 'show me X file' → Use read_file(path)",
                "- 'find code that does X' → Use search_files(query)",
                "- 'list python files' → Use list_workspace_files('*.py')",
                "",
                "IMPORTANT:",
                "- ALWAYS use tools to get current file information",
                "- DO NOT make up or assume file lists",
                "- Call list_workspace_files to see actual files",
                "- Be conversational and helpful in your explanations",
                "",
                "COMMUNICATION STYLE:",
                "- Explain what you're doing",
                "- Provide context about the files",
                "- Suggest next steps if helpful",
                "- Be friendly and informative"
            ],
            description="Specialized agent for file operations"
        )
        
        print("  ✅ File Operations Agent created")
        return agent
    
    def _create_web_research_agent(self) -> Agent:
        """Create Web Research Agent - specialized in web searches and URL fetching."""
        
        @tool(name="search_web")
        def search_web(query: str, search_type: str = "docs") -> str:
            """Search web for documentation and solutions."""
            try:
                search_mgr = get_search_manager()
                result = search_mgr.search(query=query, search_type=search_type, max_results=3)
                
                if not result.get('ok'):
                    return f"❌ Search failed: {result.get('error')}"
                
                results = result.get('results', [])
                if not results:
                    return f"No results for: {query}"
                
                output = [f"🔍 SEARCH RESULTS: {query}", ""]
                
                for i, item in enumerate(results, 1):
                    output.append(f"{i}. {item.get('title', 'Untitled')}")
                    output.append(f"   {item.get('url', '')}")
                    content = item.get('content', '')
                    if content:
                        preview = content[:150] + "..." if len(content) > 150 else content
                        output.append(f"   {preview}")
                    output.append("")
                
                return "\n".join(output)
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        @tool(name="fetch_url")
        def fetch_url(url: str) -> str:
            """Fetch and extract content from a web URL.
            
            Args:
                url: The URL to fetch content from
                
            Returns:
                Extracted text content from the webpage
            """
            try:
                import requests
                from bs4 import BeautifulSoup
                
                # Fetch the URL
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Extract text
                text = soup.get_text()
                
                # Clean up text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                # Limit length
                max_length = 5000
                if len(text) > max_length:
                    text = text[:max_length] + "\n\n[Content truncated for length]"
                
                output = [f"📄 FETCHED CONTENT FROM: {url}", "=" * 60, "", text]
                return "\n".join(output)
                
            except requests.RequestException as e:
                return f"❌ Failed to fetch URL: {str(e)}"
            except Exception as e:
                return f"❌ Error processing URL: {str(e)}"
        
        agent = Agent(
            name="Web Research",
            model=self.model,
            knowledge=self.knowledge,
            search_knowledge=False,
            tools=[search_web, fetch_url],
            markdown=False,
            instructions=[
                "You are a Web Research specialist who finds information online.",
                "",
                "UNDERSTAND WHAT USER NEEDS:",
                "- Are they looking for how-to guides or tutorials?",
                "- Do they need API documentation or reference?",
                "- Are they comparing technologies or approaches?",
                "- Do they want best practices or design patterns?",
                "- Do they have a specific URL to fetch content from?",
                "",
                "TOOLS:",
                "- search_web(query, search_type): Search internet for information",
                "  search_type: 'docs' (technical documentation), 'general' (broader search)",
                "- fetch_url(url): Extract and read content from a specific web page",
                "",
                "WHEN TO USE EACH TOOL:",
                "- User provides URL (http://, https://) → Use fetch_url to get actual content",
                "- User asks questions needing web knowledge → Use search_web",
                "- User wants to compare/research → Use search_web",
                "",
                "SEARCH STRATEGY:",
                "Think about the best search query to find what they need:",
                "- Include technical terms when relevant",
                "- Be specific enough to get quality results",
                "- Use search_type='docs' for technical/API documentation",
                "- Use search_type='general' for broader topics",
                "",
                "PRESENTING RESULTS:",
                "- Summarize key findings clearly",
                "- Include relevant URLs for further reading",
                "- Focus on reliable, technical sources (official docs, Stack Overflow, etc.)",
                "- If URL content was fetched, explain what you found in it",
                "",
                "REMEMBER: You're helping them find and understand online information.",
                "Think about what would actually answer their question."
            ],
            description="Specialized agent for web research and URL content extraction"
        )
        
        print("  ✅ Web Research Agent created")
        return agent
    
    def _create_git_ops_agent(self) -> Agent:
        """Create Git Operations Agent - comprehensive version control and GitHub operations."""
        
        from .github_orchestrator import GitHubOrchestrator
        from .git_auth_manager import GitAuthManager
        import os
        
        # Initialize GitHub orchestrator (uses API, not CLI)
        github = GitHubOrchestrator(
            github_token=os.getenv("GITHUB_TOKEN"),
            default_remote="origin",
            default_branch="main"
        )
        git_auth = GitAuthManager(self.workspace_dir)
        
        @tool(name="git_status")
        def git_status() -> str:
            """Get comprehensive git repository status with detailed file tracking."""
            result = github.git_status(repo_path=self.workspace_dir)
            
            if not result['ok']:
                return f"❌ {result.get('error')}"
            
            if result['clean']:
                return f"✅ Working directory clean (no changes)\n   📍 Branch: {result['current_branch']}"
            
            output = ["📊 GIT STATUS:", ""]
            output.append(f"  📍 Current Branch: {result['current_branch']}")
            output.append("")
            
            # Staged changes
            if result['staged']:
                output.append(f"  ✅ Staged for commit: {len(result['staged'])} files")
                for f in result['staged'][:10]:
                    output.append(f"    + {f}")
                if len(result['staged']) > 10:
                    output.append(f"    ... and {len(result['staged']) - 10} more")
                output.append("")
            
            # Modified but not staged
            if result['modified']:
                output.append(f"  📝 Modified (unstaged): {len(result['modified'])} files")
                for f in result['modified'][:10]:
                    output.append(f"    M {f}")
                if len(result['modified']) > 10:
                    output.append(f"    ... and {len(result['modified']) - 10} more")
                output.append("")
            
            # Untracked files
            if result['untracked']:
                output.append(f"  ❓ Untracked: {len(result['untracked'])} files")
                for f in result['untracked'][:10]:
                    output.append(f"    ? {f}")
                if len(result['untracked']) > 10:
                    output.append(f"    ... and {len(result['untracked']) - 10} more")
                output.append("")
            
            total = len(result['staged']) + len(result['modified']) + len(result['untracked'])
            output.append(f"  💡 Total changes: {total} files")
            
            return "\n".join(output)
        
        @tool(name="git_add")
        def git_add(files: str = ".") -> str:
            """Stage files for commit. Use '.' for all files or comma-separated paths."""
            file_list = [f.strip() for f in files.split(',')] if files != "." else ["."]
            
            result = github.git_add(files=file_list, repo_path=self.workspace_dir)
            
            if not result['ok']:
                return f"❌ {result.get('error')}"
            
            return f"✅ Staged: {files}"
        
        @tool(name="git_commit")
        def git_commit(message: str, add_all: bool = False) -> str:
            """Create a git commit with a message. Use add_all=True to stage all changes first."""
            result = github.git_commit(
                message=message,
                repo_path=self.workspace_dir,
                add_all=add_all
            )
            
            if not result['ok']:
                return f"❌ Commit failed: {result.get('error')}"
            
            return f"✅ Committed: {result.get('commit_hash', 'unknown')[:7]}\n   📝 {message}"
        
        @tool(name="git_push")
        def git_push(remote: str = "origin", branch: str = None, force: bool = False) -> str:
            """Push commits to remote repository. Automatically selects best available account."""
            # Get available accounts
            accounts_result = git_auth.get_available_accounts()
            
            if not accounts_result['ok'] or accounts_result['total_count'] == 0:
                return "⚠️ No Git accounts found. Using system Git credentials.\n   💡 Configure accounts with 'list_git_accounts'"
            
            # Auto-select best account (credential helper > PAT > OAuth)
            accounts = accounts_result['accounts']
            account = None
            account_name = "System Git"
            
            if accounts['credential_helper']:
                account = accounts['credential_helper'][0]
                account_name = f"{account['name']} (Git Helper)"
            elif accounts['pat']:
                account = accounts['pat'][0]
                account_name = f"{account['username']} (PAT)"
            elif accounts['oauth']:
                account = accounts['oauth'][0]
                account_name = f"{account['username']} (OAuth)"
            
            # Push using GitHub orchestrator
            result = github.git_push(
                remote=remote,
                branch=branch,
                force=force,
                repo_path=self.workspace_dir
            )
            
            if not result['ok']:
                error = result.get('error', 'Unknown error')
                if 'rejected' in error.lower() or 'non-fast-forward' in error.lower():
                    return f"❌ Push rejected. Remote has new changes.\n   💡 Run 'git_pull' first, then try again."
                return f"❌ Push failed: {error}"
            
            return f"✅ Pushed to {remote}" + (f"/{branch}" if branch else "") + f"\n   🔐 Using: {account_name}"
        
        @tool(name="git_pull")
        def git_pull(remote: str = "origin", branch: str = None) -> str:
            """Pull changes from remote repository and check for conflicts."""
            result = github.git_pull(
                remote=remote,
                branch=branch,
                repo_path=self.workspace_dir
            )
            
            if not result['ok']:
                error = result.get('error', 'Unknown error')
                if 'CONFLICT' in error or 'conflict' in error.lower():
                    return f"⚠️ Pull resulted in merge conflicts!\n   💡 Use 'list_conflicts' to see affected files.\n   💡 Use 'resolve_conflict' to fix them."
                return f"❌ Pull failed: {error}"
            
            output_msg = result.get('output', '')
            return f"✅ Pulled from {remote}" + (f"/{branch}" if branch else "") + (f"\n   {output_msg}" if output_msg and 'Already up to date' not in output_msg else "")
        
        @tool(name="create_branch")
        def create_branch(branch_name: str, checkout: bool = True) -> str:
            """Create a new Git branch and optionally switch to it."""
            result = github.create_branch(
                branch_name=branch_name,
                checkout=checkout,
                repo_path=self.workspace_dir
            )
            
            if not result['ok']:
                return f"❌ {result.get('error')}"
            
            msg = result.get('message', f"Branch '{branch_name}' created")
            return f"✅ {msg}"
        
        @tool(name="switch_branch")
        def switch_branch(branch_name: str) -> str:
            """Switch to a different branch."""
            result = github.switch_branch(
                branch_name=branch_name,
                repo_path=self.workspace_dir
            )
            
            if not result['ok']:
                return f"❌ {result.get('error')}"
            
            return f"✅ Switched to branch: {branch_name}"
        
        @tool(name="list_branches")
        def list_branches() -> str:
            """List all Git branches (local and remote)."""
            # Get local branches
            local_result = github._run_git_command(['branch'], cwd=self.workspace_dir)
            # Get remote branches
            remote_result = github._run_git_command(['branch', '-r'], cwd=self.workspace_dir)
            
            if not local_result['ok']:
                return f"❌ {local_result.get('error')}"
            
            output = ["📋 GIT BRANCHES:", ""]
            
            # Parse local branches
            current_branch = None
            local_branches = []
            for line in local_result['output'].split('\n'):
                if not line.strip():
                    continue
                is_current = line.startswith('*')
                branch = line.replace('*', '').strip()
                if is_current:
                    current_branch = branch
                local_branches.append(branch)
            
            output.append(f"  📍 Current: {current_branch}")
            output.append(f"  📦 Local branches: {len(local_branches)}")
            for branch in local_branches[:15]:
                marker = "➤" if branch == current_branch else " "
                output.append(f"    {marker} {branch}")
            
            # Parse remote branches
            if remote_result['ok'] and remote_result['output'].strip():
                remote_branches = [line.strip() for line in remote_result['output'].split('\n') if line.strip()]
                output.append("")
                output.append(f"  🌐 Remote branches: {len(remote_branches)}")
                for branch in remote_branches[:10]:
                    output.append(f"     {branch}")
            
            return "\n".join(output)
        
        @tool(name="delete_branch")
        def delete_branch(branch_name: str, force: bool = False) -> str:
            """Delete a Git branch. Use force=True for unmerged branches."""
            result = github.delete_branch(
                branch_name=branch_name,
                force=force,
                repo_path=self.workspace_dir
            )
            
            if not result['ok']:
                return f"❌ {result.get('error')}"
            
            return f"✅ Deleted branch: {branch_name}"
        
        @tool(name="list_conflicts")
        def list_conflicts() -> str:
            """List all files with merge conflicts."""
            # Use git diff to find conflicted files
            result = github._run_git_command(
                ['diff', '--name-only', '--diff-filter=U'],
                cwd=self.workspace_dir
            )
            
            if not result['ok']:
                return f"❌ {result.get('error')}"
            
            conflicted_files = [f for f in result['output'].split('\n') if f.strip()]
            
            if not conflicted_files:
                return "✅ No merge conflicts detected"
            
            output = ["⚠️ MERGE CONFLICTS DETECTED:", ""]
            output.append(f"  🔴 {len(conflicted_files)} file(s) with conflicts:")
            output.append("")
            for file in conflicted_files:
                output.append(f"    ⚡ {file}")
            output.append("")
            output.append("  💡 To resolve:")
            output.append("     - Use 'resolve_conflict(file, strategy)' with strategy='ours' or 'theirs'")
            output.append("     - Or manually edit files and use 'git_add' to mark as resolved")
            
            return "\n".join(output)
        
        @tool(name="resolve_conflict")
        def resolve_conflict(file_path: str, strategy: str = "ours") -> str:
            """Resolve merge conflict automatically. strategy='ours' (keep local) or 'theirs' (keep remote)."""
            if strategy not in ['ours', 'theirs']:
                return "❌ Invalid strategy. Use 'ours' (keep local changes) or 'theirs' (keep remote changes)"
            
            # Resolve using git checkout
            checkout_result = github._run_git_command(
                ['checkout', f'--{strategy}', file_path],
                cwd=self.workspace_dir
            )
            
            if not checkout_result['ok']:
                return f"❌ Failed to resolve: {checkout_result.get('error')}"
            
            # Stage the resolved file
            add_result = github._run_git_command(
                ['add', file_path],
                cwd=self.workspace_dir
            )
            
            if not add_result['ok']:
                return f"⚠️ Resolved but failed to stage: {add_result.get('error')}"
            
            return f"✅ Resolved '{file_path}' using '{strategy}' strategy and staged for commit"
        
        @tool(name="create_pull_request")
        def create_pull_request(owner: str, repo: str, title: str, head: str, base: str = "main", body: str = "") -> str:
            """Create a GitHub pull request via API (no GitHub CLI needed)."""
            if not os.getenv("GITHUB_TOKEN"):
                return "❌ GITHUB_TOKEN environment variable required for PR creation"
            
            result = github.create_pull_request(
                owner=owner,
                repo=repo,
                title=title,
                head=head,
                base=base,
                body=body
            )
            
            if not result['ok']:
                error = result.get('error', 'Unknown error')
                if error == 'github_token_required':
                    return "❌ GitHub token required. Set GITHUB_TOKEN environment variable."
                return f"❌ Failed to create PR: {error}"
            
            pr_data = result.get('pr', {})
            return f"✅ Pull Request Created!\n   📝 Title: {title}\n   🔗 URL: {pr_data.get('html_url', 'N/A')}\n   #️⃣ Number: #{pr_data.get('number', 'N/A')}"
        
        @tool(name="list_pull_requests")
        def list_pull_requests(owner: str, repo: str, state: str = "open", limit: int = 10) -> str:
            """List pull requests from GitHub repository. state: 'open', 'closed', or 'all'."""
            if not os.getenv("GITHUB_TOKEN"):
                return "⚠️ GITHUB_TOKEN not set. Cannot list PRs."
            
            result = github.list_pull_requests(
                owner=owner,
                repo=repo,
                state=state,
                limit=limit
            )
            
            if not result['ok']:
                return f"❌ {result.get('error')}"
            
            prs = result.get('pulls', [])
            
            if not prs:
                return f"ℹ️ No {state} pull requests found in {owner}/{repo}"
            
            output = [f"📋 PULL REQUESTS ({state}) in {owner}/{repo}:", ""]
            output.append(f"  Found {len(prs)} PR(s):")
            output.append("")
            
            for pr in prs:
                status_icon = "🟢" if pr['state'] == 'open' else "🔴"
                output.append(f"  {status_icon} #{pr['number']}: {pr['title']}")
                output.append(f"     👤 By: {pr['author']} | 🌿 {pr['head']} → {pr['base']}")
                output.append(f"     🔗 {pr['url']}")
                output.append("")
            
            return "\n".join(output)
        
        @tool(name="create_issue")
        def create_issue(owner: str, repo: str, title: str, body: str = "", labels: str = "") -> str:
            """Create a GitHub issue. labels: comma-separated string like 'bug,enhancement'."""
            if not os.getenv("GITHUB_TOKEN"):
                return "❌ GITHUB_TOKEN required for issue creation"
            
            label_list = [l.strip() for l in labels.split(',') if l.strip()] if labels else None
            
            result = github.create_issue(
                owner=owner,
                repo=repo,
                title=title,
                body=body,
                labels=label_list
            )
            
            if not result['ok']:
                return f"❌ {result.get('error')}"
            
            issue_data = result.get('issue', {})
            return f"✅ Issue Created!\n   📝 {title}\n   🔗 {issue_data.get('html_url', 'N/A')}\n   #️⃣ #{issue_data.get('number', 'N/A')}"
        
        @tool(name="get_repo_info")
        def get_repo_info(owner: str, repo: str) -> str:
            """Get detailed information about a GitHub repository."""
            if not os.getenv("GITHUB_TOKEN"):
                return "⚠️ GITHUB_TOKEN not set. Limited info available."
            
            result = github.get_repository_info(owner=owner, repo=repo)
            
            if not result['ok']:
                return f"❌ {result.get('error')}"
            
            repo_data = result.get('repository', {})
            
            output = [f"📦 REPOSITORY: {owner}/{repo}", ""]
            output.append(f"  📝 Description: {repo_data.get('description', 'N/A')}")
            output.append(f"  🌐 URL: {repo_data.get('html_url', 'N/A')}")
            output.append(f"  ⭐ Stars: {repo_data.get('stars', 0)}")
            output.append(f"  🍴 Forks: {repo_data.get('forks', 0)}")
            output.append(f"  👀 Watchers: {repo_data.get('watchers', 0)}")
            output.append(f"  🔓 Visibility: {'Private' if repo_data.get('private') else 'Public'}")
            output.append(f"  📅 Created: {repo_data.get('created_at', 'N/A')}")
            output.append(f"  📊 Size: {repo_data.get('size', 0)} KB")
            
            if repo_data.get('language'):
                output.append(f"  💻 Language: {repo_data['language']}")
            
            return "\n".join(output)
        
        @tool(name="list_git_accounts")
        def list_git_accounts() -> str:
            """List all available Git authentication accounts."""
            result = git_auth.get_available_accounts()
            
            if not result['ok']:
                return f"❌ {result.get('error')}"
            
            output = ["🔐 GIT AUTHENTICATION ACCOUNTS:", ""]
            
            accounts = result['accounts']
            
            if accounts['credential_helper']:
                output.append("  Method A: Credential Helper (System Git)")
                for acc in accounts['credential_helper']:
                    output.append(f"    • {acc['name']} <{acc['email']}>")
                output.append("")
            
            if accounts['pat']:
                output.append("  Method B: Personal Access Tokens")
                for acc in accounts['pat']:
                    output.append(f"    • {acc['username']} ({acc['token_preview']})")
                output.append("")
            
            if accounts['oauth']:
                output.append("  Method C: OAuth")
                for acc in accounts['oauth']:
                    output.append(f"    • {acc['username']} <{acc.get('email', 'N/A')}>")
                output.append("")
            
            if result['total_count'] == 0:
                output.append("  ⚠️ No accounts configured")
                output.append("  Configure authentication to enable push operations")
            
            return "\n".join(output)
        
        agent = Agent(
            name="Git Operations",
            model=self.model,
            knowledge=self.knowledge,
            search_knowledge=False,
            tools=[
                git_status, git_add, git_commit, git_push, git_pull,
                create_branch, switch_branch, list_branches, delete_branch,
                list_conflicts, resolve_conflict,
                create_pull_request, list_pull_requests, create_issue, get_repo_info,
                list_git_accounts
            ],
            markdown=True,
            instructions=[
                "You are a helpful Git Operations assistant.",
                "",
                "🎯 YOUR MISSION:",
                "When users ask about git status, branches, or repository state - ACTUALLY CALL THE TOOLS!",
                "Don't just format text - execute the actual git commands using your tools.",
                "",
                "CRITICAL - ALWAYS USE TOOLS:",
                "❌ WRONG: 'Here is the git status formatted nicely...'",
                "✅ RIGHT: Call git_status() tool and show the actual result",
                "",
                "❌ WRONG: 'The branches are: main, origin/main'",
                "✅ RIGHT: Call list_branches() tool and show actual branches",
                "",
                "AVAILABLE TOOLS:",
                "",
                "📊 Status & Inspection:",
                "   • git_status() - Get current repository state (staged, modified, untracked files)",
                "   • list_branches() - Show all local and remote branches",
                "   • list_conflicts() - Show files with merge conflicts",
                "   • list_git_accounts() - Show available authentication methods",
                "",
                "💾 Staging & Committing:",
                "   • git_add(files) - Stage specific files (use '.' for all)",
                "   • git_commit(message, add_all) - Commit changes with message",
                "",
                "🚀 Synchronization:",
                "   • git_push(remote, branch, force) - Push to remote",
                "   • git_pull(remote, branch) - Pull from remote",
                "",
                "🌿 Branch Management:",
                "   • create_branch(name, checkout) - Create new branch",
                "   • switch_branch(name) - Switch to existing branch",
                "   • delete_branch(name, force) - Remove branch",
                "",
                "🌐 GitHub Operations:",
                "   • create_pull_request(...) - Create PR via API",
                "   • list_pull_requests(...) - List PRs",
                "   • create_issue(...) - Create issue",
                "   • get_repo_info(owner, repo) - Get repo details",
                "",
                "COMMUNICATION STYLE:",
                "- Always call the appropriate tool first",
                "- Then explain the results in a friendly way",
                "- Suggest next steps if helpful",
                "- Be conversational but accurate",
                "",
                "EXAMPLES:",
                "User: 'show git status'",
                "You: [Call git_status() tool] 'Here's your repository status: ...'",
                "",
                "User: 'what branches do we have?'",
                "You: [Call list_branches() tool] 'You have these branches: ...'",
                "",
                "User: 'commit my changes'",
                "You: [Call git_status() first to see what changed, then git_commit() with a good message]"
            ],
            description="Git & GitHub operations assistant"
        )
        
        print("  ✅ Git Operations Agent created")
        return agent
    
    def route_query(self, query: str) -> str:
        """Route query to appropriate agent(s) using orchestrator agent.
        
        Args:
            query: User query
            
        Returns:
            Agent type to use: 'code_analyst', 'file_ops', 'web_research', 'git_ops', 'parallel', or 'none'
        """
        # Check for simple greetings/casual queries that don't need agent routing
        query_lower = query.lower().strip()
        simple_greetings = ['hi', 'hello', 'hey', 'sup', 'yo', 'howdy']
        if query_lower in simple_greetings or len(query.split()) <= 2:
            print(f"💬 Simple greeting detected, no agent routing needed")
            return 'none'
        
        # Create routing prompt for orchestrator
        routing_prompt = f"""Available Agents:
- code_analyst: Write/generate code, create functions/classes, analyze code, find bugs, execute code
- file_ops: Read files, write to files, search in files, list directories
- web_research: Search documentation, find tutorials, lookup best practices
- git_ops: Git commits, pushes, branches, pull requests
- none: Just a greeting or casual conversation, no agent needed

User Query: "{query}"

Which agent should handle this? Respond with ONE WORD ONLY: code_analyst, file_ops, web_research, git_ops, parallel, or none"""

        try:
            # Use orchestrator agent to route
            response = self.orchestrator.run(routing_prompt)
            
            # Extract the agent name from response
            if hasattr(response, 'content'):
                route = response.content.strip().lower()
            else:
                route = str(response).strip().lower()
            
            # Clean up the response (remove punctuation, extra text)
            route = route.replace('.', '').replace(':', '').replace('!', '').strip()
            
            # Validate the route
            valid_routes = ['code_analyst', 'file_ops', 'web_research', 'git_ops', 'parallel', 'none']
            
            # Find the first valid route in the response
            for valid_route in valid_routes:
                if valid_route in route:
                    print(f"🎯 Orchestrator selected: {valid_route}")
                    return valid_route
            
            # If orchestrator response is unclear, use fallback
            print(f"⚠️  Orchestrator response unclear: '{route[:50]}...', using fallback")
            return self._fallback_routing(query)
                
        except Exception as e:
            print(f"⚠️  Orchestrator error: {e}, using fallback")
            return self._fallback_routing(query)
    
    def _fallback_routing(self, query: str) -> str:
        """LLM-based fallback routing when orchestrator response is unclear.
        
        Uses a simple LLM prompt to understand intent and route appropriately.
        
        Args:
            query: User query
            
        Returns:
            Agent type
        """
        try:
            # Create a simple routing prompt for the LLM
            routing_prompt = f"""Analyze this user query and determine which agent should handle it.

User Query: "{query}"

Available Agents:
- code_analyst: Code analysis, bugs, optimization, execution, modernization, technical explanations
- file_ops: Reading files, writing files, file searches, directory operations
- web_research: Internet searches, documentation, best practices, tutorials, research
- git_ops: Version control, commits, branches, GitHub operations

Respond with ONLY ONE of these: code_analyst, file_ops, web_research, git_ops, or parallel

Think about the user's INTENT:
- What are they trying to accomplish?
- What capabilities do they need?
- Which agent can best help them?

Agent:"""

            # Use the model directly for quick routing decision
            response = self.model.generate(routing_prompt)
            
            if hasattr(response, 'content'):
                route = response.content.strip().lower()
            else:
                route = str(response).strip().lower()
            
            # Validate the response
            valid_routes = ['code_analyst', 'file_ops', 'web_research', 'git_ops', 'parallel']
            if route in valid_routes:
                print(f"✅ LLM fallback routing: {route}")
                return route
            
            # If response is unclear, try to extract agent name
            for valid_route in valid_routes:
                if valid_route in route:
                    print(f"✅ LLM fallback routing (extracted): {valid_route}")
                    return valid_route
            
            # Last resort: analyze query semantics
            print(f"⚠️  LLM fallback unclear, using semantic analysis")
            return self._semantic_fallback(query)
            
        except Exception as e:
            print(f"⚠️  LLM fallback error: {e}, using semantic analysis")
            return self._semantic_fallback(query)
    
    def _semantic_fallback(self, query: str) -> str:
        """Ultra-simple semantic fallback based on query characteristics.
        
        Args:
            query: User query
            
        Returns:
            Agent type
        """
        query_lower = query.lower()
        
        # Simple heuristics based on common patterns (not keyword matching)
        # These are broad semantic categories, not specific keywords
        
        # Questions about how things work → research
        if query_lower.startswith(('how', 'what', 'why', 'when', 'where', 'explain')):
            # Check if it's about code → code_analyst
            if any(term in query_lower for term in ['code', 'function', 'class', 'variable', 'method', 'this']):
                return 'code_analyst'
            # Otherwise → web_research
            return 'web_research'
        
        # Imperatives (commands) → likely code or file operations
        if query_lower.startswith(('show', 'tell', 'give', 'get', 'find', 'read')):
            # File-related → file_ops
            if 'file' in query_lower or 'directory' in query_lower:
                return 'file_ops'
            return 'code_analyst'
        
        # Default to code_analyst as it's the most versatile
        return 'code_analyst'
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process query using appropriate agent(s).
        
        Args:
            query: User query
            
        Returns:
            Response dict with results
        """
        # Store user message in memory
        self.memory_manager.add_message('user', query, metadata={'source': 'chat'})
        
        route = self.route_query(query)
        
        print(f"📍 Routing query to: {route}")
        
        # Handle greetings and simple queries directly
        if route == 'none':
            greeting_responses = [
                "Hello! I'm Helix, your AI coding assistant. How can I help you today?\n\nI can:\n• Analyze and write code\n• Read and modify files\n• Search for documentation and best practices\n• Help with Git operations (commits, branches, PRs)",
                "Hi there! I'm ready to assist you with coding tasks. What would you like to work on?",
                "Hey! How can I help you today? Just let me know what you need - code analysis, file operations, research, or Git help."
            ]
            import random
            response_text = random.choice(greeting_responses)
            
            response = {
                'ok': True,
                'result': response_text,
                'response': response_text,
                'mode': 'direct',
                'agent': 'orchestrator'
            }
            
            self.memory_manager.add_message(
                'assistant', 
                response_text, 
                metadata={'agent': 'orchestrator', 'route': 'none'}
            )
            
            return response
        
        if route == 'parallel':
            response = self._process_parallel(query)
        else:
            response = self._process_single(query, route)
        
        # Store assistant response in memory
        if response.get('ok') and response.get('result'):
            agent_name = route if route != 'parallel' else 'multi_agent'
            self.memory_manager.add_message(
                'assistant', 
                response['result'], 
                metadata={'agent': agent_name, 'route': route}
            )
        
        return response
    
    def _clean_response(self, content: str, query: str) -> str:
        """Clean response - just return as-is for natural conversation.
        
        Args:
            content: Raw agent response
            query: Original user query
            
        Returns:
            Content unchanged
        """
        # Return content as-is for natural conversation
        return content
    
    def _process_single(self, query: str, agent_type: str) -> Dict[str, Any]:
        """Process query with single agent.
        
        Args:
            query: User query
            agent_type: Type of agent to use
            
        Returns:
            Response dict
        """
        agent = self.agents.get(agent_type)
        if not agent:
            return {
                'ok': False,
                'error': f'Agent {agent_type} not found'
            }
        
        try:
            # Use Agno agent's run method
            response = agent.run(query)
            
            # Extract content from response
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, dict):
                content = response.get('content', str(response))
            else:
                content = str(response)
            
            # Clean response to extract essential format
            content = self._clean_response(content, query)
            
            return {
                'ok': True,
                'agent': agent_type,
                'response': content,
                'mode': 'single'
            }
        except Exception as e:
            return {
                'ok': False,
                'agent': agent_type,
                'error': str(e)
            }
    
    def _process_parallel(self, query: str) -> Dict[str, Any]:
        """Process query with multiple agents in parallel.
        
        Args:
            query: User query
            
        Returns:
            Combined response dict
        """
        futures = {}
        responses = {}
        
        # Submit to all agents
        for agent_type, agent in self.agents.items():
            future = self.executor.submit(self._run_agent, agent, query)
            futures[future] = agent_type
        
        # Collect results
        for future in as_completed(futures):
            agent_type = futures[future]
            try:
                result = future.result()
                responses[agent_type] = result
            except Exception as e:
                responses[agent_type] = f"Error: {str(e)}"
        
        # Combine responses
        combined = [f"🤖 Multi-Agent Response (Parallel Processing):", ""]
        
        for agent_type, response in responses.items():
            combined.append(f"📌 {agent_type.replace('_', ' ').title()}:")
            combined.append(str(response))
            combined.append("")
        
        return {
            'ok': True,
            'mode': 'parallel',
            'responses': responses,
            'combined': '\n'.join(combined)
        }
    
    def _run_agent(self, agent: Agent, query: str) -> str:
        """Run agent with query (for thread pool).
        
        Args:
            agent: Agent instance
            query: User query
            
        Returns:
            Response string
        """
        try:
            response = agent.run(query)
            
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, dict):
                return response.get('content', str(response))
            else:
                return str(response)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_agent(self, agent_type: str) -> Optional[Agent]:
        """Get specific agent by type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Agent instance or None
        """
        return self.agents.get(agent_type)
    
    def list_agents(self) -> List[str]:
        """List all available agents.
        
        Returns:
            List of agent types
        """
        return list(self.agents.keys())
    
    def shutdown(self):
        """Shutdown the multi-agent system."""
        print("🔄 Shutting down multi-agent system...")
        self.executor.shutdown(wait=True)
        print("✅ Multi-agent system shutdown complete")


def create_multi_agent_system(workspace_dir: str = ".") -> MultiAgentSystem:
    """Create and return a MultiAgentSystem instance.
    
    Args:
        workspace_dir: Workspace directory
        
    Returns:
        Initialized MultiAgentSystem
    """
    if Agent is None:
        raise RuntimeError("Agno SDK not installed. Install with: pip install agno")
    
    print("🚀 Initializing Multi-Agent System...")
    system = MultiAgentSystem(workspace_dir=workspace_dir)
    print(f"✅ Multi-Agent System ready with {len(system.list_agents())} agents")
    
    return system
