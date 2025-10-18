#!/usr/bin/env python
"""
Example script demonstrating Helix's new capabilities:
- NVIDIA NIM integration with Nemotron and NeMo Retriever
- Agno-based multi-agent orchestration
- Intelligent workflow routing
- AgentOS runtime

Usage:
    python examples/demo_agno_nim.py
"""

import asyncio
from pathlib import Path
import os

# Set up environment
os.environ.setdefault("NIM_API_KEY", "your-nim-api-key")
os.environ.setdefault("GH_TOKEN", "your-github-token")
os.environ.setdefault("AGNO_USE_MCP", "false")


def demo_basic_usage():
    """Demo 1: Basic Helix usage with NVIDIA NIM."""
    print("=" * 80)
    print("DEMO 1: Basic Usage with NVIDIA NIM")
    print("=" * 80)
    
    from helix.config import Config
    from helix.agno_agents import AgnoHelixOrchestrator
    
    # Create config
    config = Config.from_env()
    print(f"\n✓ Using provider: {config.get_provider()}")
    print(f"✓ Using model: {config.get_model()}")
    print(f"✓ Using embedder: {config.get_embedder_model()}")
    
    # Create orchestrator
    orchestrator = AgnoHelixOrchestrator(config)
    print(f"\n✓ Created orchestrator with {len(orchestrator.agents)} agents:")
    for agent_name in orchestrator.list_agents():
        print(f"  - {agent_name}")
    
    # Execute simple task
    print("\n🚀 Executing: 'Add a hello world function'")
    result = orchestrator.execute(
        user_prompt="Add a hello world function to utils.py",
        workspace=Path.cwd()
    )
    
    print(f"\n✓ Success: {result['success']}")
    if result['success']:
        print("\n📝 Explanation:")
        print(result.get('explanation', 'No explanation generated'))


def demo_intelligent_workflow():
    """Demo 2: Intelligent workflow with complexity detection."""
    print("\n" + "=" * 80)
    print("DEMO 2: Intelligent Workflow Orchestration")
    print("=" * 80)
    
    from helix.config import Config
    from helix.agno_agents import AgnoHelixOrchestrator
    from helix.workflow import WorkflowOrchestrator
    
    config = Config.from_env()
    agno_orchestrator = AgnoHelixOrchestrator(config)
    
    # Create workflow orchestrator
    workflow = WorkflowOrchestrator(config, agno_orchestrator.agents)
    
    # Analyze and execute
    async def run_workflow():
        print("\n🔍 Analyzing repository...")
        analysis = workflow.router.analyze_repository(Path.cwd())
        print(f"  - Test framework: {analysis.get('test_framework', 'None')}")
        print(f"  - File count: {analysis.get('file_count', 0)}")
        print(f"  - Complexity score: {analysis.get('complexity_score', 0)}")
        
        print("\n🚀 Executing workflow with intelligent routing...")
        state = await workflow.execute(
            prompt="Refactor the agent system",
            workspace=Path.cwd()
        )
        
        print(f"\n✓ Workflow completed")
        print(f"  - Complexity: {state.complexity.value}")
        print(f"  - Success: {state.success}")
        print(f"  - Retry count: {state.retry_count}")
        if state.errors:
            print(f"  - Errors: {len(state.errors)}")
    
    asyncio.run(run_workflow())


def demo_provider_comparison():
    """Demo 3: Compare different providers."""
    print("\n" + "=" * 80)
    print("DEMO 3: Provider Comparison")
    print("=" * 80)
    
    from helix.providers import ProviderRegistry
    
    # List available providers
    providers = ProviderRegistry.list_providers()
    print("\n✓ Available providers:")
    for provider_type, provider_list in providers.items():
        print(f"  {provider_type}: {', '.join(provider_list)}")
    
    # Test NVIDIA NIM LLM
    print("\n🧪 Testing NVIDIA NIM LLM...")
    try:
        nim_llm = ProviderRegistry.get_llm(
            provider="nvidia_nim",
            model="meta/llama-3.1-nemotron-nano-8b-v1",
            options={
                "api_key": os.getenv("NIM_API_KEY"),
                "base_url": "https://integrate.api.nvidia.com/v1"
            }
        )
        
        response = nim_llm.chat(
            messages=[{"role": "user", "content": "Say hello in Python"}],
            max_tokens=100
        )
        print(f"✓ Response: {response.text[:100]}...")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test NVIDIA NIM Embeddings
    print("\n🧪 Testing NVIDIA NIM Embeddings...")
    try:
        nim_embedder = ProviderRegistry.get_embedder(
            provider="nvidia_nim",
            model="nvidia/llama-3_2-nemoretriever-300m-embed-v1",
            options={
                "api_key": os.getenv("NIM_API_KEY"),
                "base_url": "https://integrate.api.nvidia.com/v1"
            }
        )
        
        embedding_response = nim_embedder.embed(
            texts=["Hello world", "Testing embeddings"],
            input_type="query"
        )
        print(f"✓ Generated {len(embedding_response.embeddings)} embeddings")
        print(f"  Dimension: {len(embedding_response.embeddings[0])}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test NVIDIA NIM Reranking
    print("\n🧪 Testing NVIDIA NIM Reranking...")
    try:
        nim_reranker = ProviderRegistry.get_reranker(
            provider="nvidia_nim",
            model="nvidia/llama-3.2-nv-rerankqa-1b-v2",
            options={
                "api_key": os.getenv("NIM_API_KEY"),
                "base_url": "https://integrate.api.nvidia.com/v1"
            }
        )
        
        rerank_response = nim_reranker.rerank(
            query="Python code generation",
            documents=[
                "Python is a programming language",
                "Code generation with LLMs",
                "Weather forecast for today"
            ],
            top_n=2
        )
        print(f"✓ Reranked {len(rerank_response.scores)} documents")
        print(f"  Top indices: {rerank_response.ranked_indices[:2]}")
    except Exception as e:
        print(f"✗ Failed: {e}")


def demo_agentos_server():
    """Demo 4: Run AgentOS server."""
    print("\n" + "=" * 80)
    print("DEMO 4: AgentOS Server")
    print("=" * 80)
    
    from helix.config import Config
    from helix.agno_agents import AgnoHelixOrchestrator
    
    config = Config.from_env()
    orchestrator = AgnoHelixOrchestrator(config)
    
    # Create AgentOS
    agent_os = orchestrator.create_agent_os()
    print("\n✓ AgentOS created with agents:")
    for agent_name in orchestrator.list_agents():
        print(f"  - {agent_name}")
    
    print("\n🚀 To start the AgentOS server, run:")
    print("    orchestrator.serve(host='0.0.0.0', port=8000)")
    print("\n📱 Then visit https://os.agno.com to connect to your runtime")
    print("   and interact with agents through the UI")
    
    # Get FastAPI app (don't serve in demo)
    app = orchestrator.get_fastapi_app()
    print(f"\n✓ FastAPI app ready: {type(app).__name__}")


def demo_state_persistence():
    """Demo 5: State persistence and checkpoint recovery."""
    print("\n" + "=" * 80)
    print("DEMO 5: State Persistence & Recovery")
    print("=" * 80)
    
    from helix.workflow import WorkflowState, TaskComplexity, WorkflowPhase
    from datetime import datetime
    
    # Create a state
    state = WorkflowState(
        session_id="demo_session_001",
        prompt="Add authentication system",
        workspace=Path.cwd(),
        complexity=TaskComplexity.COMPLEX
    )
    
    # Simulate some progress
    state.current_phase = WorkflowPhase.CODING
    state.plan_result = {"tasks": ["task1", "task2"]}
    state.code_result = {"files_created": ["auth.py"]}
    
    # Save checkpoint
    checkpoint_dir = Path.cwd() / ".helix" / "checkpoints"
    state.save_checkpoint(checkpoint_dir)
    print(f"\n✓ Checkpoint saved: {state.session_id}")
    print(f"  - Phase: {state.current_phase.value}")
    print(f"  - Complexity: {state.complexity.value}")
    
    # Load checkpoint
    loaded_state = WorkflowState.load_checkpoint(
        session_id="demo_session_001",
        checkpoint_dir=checkpoint_dir
    )
    
    if loaded_state:
        print(f"\n✓ Checkpoint loaded successfully")
        print(f"  - Prompt: {loaded_state.prompt}")
        print(f"  - Phase: {loaded_state.current_phase.value}")
        print(f"  - Plan result: {loaded_state.plan_result}")
    else:
        print("\n✗ Failed to load checkpoint")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("HELIX DEMO - NVIDIA NIM + Agno Integration")
    print("=" * 80)
    
    try:
        # Check prerequisites
        if not os.getenv("NIM_API_KEY") or os.getenv("NIM_API_KEY") == "your-nim-api-key":
            print("\n⚠️  Warning: NIM_API_KEY not set. Some demos will fail.")
            print("   Get your API key from: https://build.nvidia.com")
        
        # Run demos
        demos = [
            ("Basic Usage", demo_basic_usage),
            ("Intelligent Workflow", demo_intelligent_workflow),
            ("Provider Comparison", demo_provider_comparison),
            ("AgentOS Server", demo_agentos_server),
            ("State Persistence", demo_state_persistence),
        ]
        
        for name, demo_func in demos:
            try:
                demo_func()
            except Exception as e:
                print(f"\n❌ Demo '{name}' failed: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("✅ All demos completed!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demos interrupted by user")


if __name__ == "__main__":
    main()
