"""Command-line interface for Helix."""

import sys
import argparse
from pathlib import Path
from typing import Optional
import os

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment from {env_path}")
except ImportError:
    pass  # python-dotenv not installed

from helix.config import Config
from helix.agno_agents import AgnoHelixOrchestrator
from helix.ai_detector import AIKeywordDetector
from helix.providers import ProviderRegistry


def prompt_for_model_selection(config: Config) -> None:
    """Prompt user to select LLM and embedder."""
    providers = ProviderRegistry.list_providers()
    
    print("\n🤖 Model Selection")
    print("=" * 60)
    
    # LLM selection
    print("\nAvailable LLM Providers:")
    for i, provider in enumerate(providers["llm"], 1):
        print(f"  {i}. {provider}")
    
    llm_choice = input("\nSelect LLM provider (press Enter for default 'nvidia_nim'): ").strip()
    
    if llm_choice and llm_choice.isdigit():
        idx = int(llm_choice) - 1
        if 0 <= idx < len(providers["llm"]):
            config.selected_provider = providers["llm"][idx]
    
    if config.selected_provider:
        llm_model = input(f"Enter model name for {config.selected_provider} (or press Enter for default): ").strip()
        if llm_model:
            config.selected_model = llm_model
    
    # Embedder selection
    print("\nAvailable Embedder Providers:")
    for i, provider in enumerate(providers["embedder"], 1):
        print(f"  {i}. {provider}")
    
    embedder_choice = input("\nSelect embedder provider (press Enter for default 'nvidia_nim'): ").strip()
    
    if embedder_choice and embedder_choice.isdigit():
        idx = int(embedder_choice) - 1
        if 0 <= idx < len(providers["embedder"]):
            config.selected_embedder_provider = providers["embedder"][idx]
    
    if config.selected_embedder_provider:
        embedder_model = input(f"Enter embedder model for {config.selected_embedder_provider} (or press Enter for default): ").strip()
        if embedder_model:
            config.selected_embedder_model = embedder_model
    
    # Save preferences
    config.save_user_preferences()
    
    print("\n✅ Model preferences saved")
    print(f"   LLM: {config.get_provider()} / {config.get_model()}")
    print(f"   Embedder: {config.get_embedder_provider()} / {config.get_embedder_model()}")


def run_helix(
    prompt: str,
    config: Optional[Config] = None,
    auto_push: Optional[bool] = None,
    require_confirmation: Optional[bool] = None
) -> None:
    """Run Helix with given prompt."""
    if config is None:
        config = Config.from_env()
    
    # Override config if specified
    if auto_push is not None:
        config.auto_push = auto_push
    if require_confirmation is not None:
        config.require_human_confirmation = require_confirmation
    
    # Load saved preferences
    config.load_user_preferences()
    
    # Check if AI-related and prompt for model selection if needed
    has_preference = config.selected_provider is not None
    should_prompt = AIKeywordDetector.should_prompt_model_selection(prompt, has_preference)
    
    if should_prompt:
        is_ai, keywords = AIKeywordDetector.is_ai_related(prompt)
        print(AIKeywordDetector.get_model_selection_prompt(keywords))
        
        response = input("\nWould you like to specify models? (y/n): ").strip().lower()
        if response in ('y', 'yes'):
            prompt_for_model_selection(config)
    
    # Execute orchestrator
    orchestrator = AgnoHelixOrchestrator(config)
    results = orchestrator.execute(prompt)
    
    if results["success"]:
        print("\n✅ Helix execution completed successfully!")
    else:
        print("\n❌ Helix execution encountered errors")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Helix - Multi-agent coding assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with a prompt (auto-push enabled by default)
  helix --prompt "Create a REST API for user management"
  
  # Run without auto-push
  helix --prompt "Add logging" --no-push
  
  # Require human confirmation before push
  helix --prompt "Refactor authentication" --confirm
  
  # Set model preferences
  helix --set-model provider=nvidia_nim model=meta/llama-3.1-70b-instruct
  
  # Start interactive mode
  helix --start
  
  # Start AgentOS server (access at http://localhost:7777)
  helix --serve
  
  # Start server with custom host and port
  helix --serve --host 0.0.0.0 --port 8000 --reload
  
  # Create standalone AgentOS application file
  helix --create-agentos
        """
    )
    
    parser.add_argument(
        "--prompt",
        type=str,
        help="Natural language prompt describing desired changes"
    )
    
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Disable automatic push to GitHub"
    )
    
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Require human confirmation before push"
    )
    
    parser.add_argument(
        "--create-pr",
        action="store_true",
        help="Create a pull request after push"
    )
    
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace directory (default: current directory)"
    )
    
    parser.add_argument(
        "--set-model",
        type=str,
        help="Set model preferences (format: provider=X model=Y)"
    )
    
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start interactive mode"
    )
    
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start AgentOS server mode"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Server host (default: localhost, use 0.0.0.0 for external access)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=7777,
        help="Server port (default: 7777)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--create-agentos",
        action="store_true",
        help="Create standalone AgentOS application file"
    )
    
    args = parser.parse_args()
    
    # Load config
    config = Config.from_env()
    config.workspace_dir = args.workspace
    
    if args.create_pr:
        config.create_pr = True
    
    # Handle --create-agentos
    if args.create_agentos:
        orchestrator = AgnoHelixOrchestrator(config)
        app_file = orchestrator.create_agentos_file()
        print(f"\n✅ AgentOS application created!")
        print(f"📍 Location: {app_file}")
        print(f"\n🚀 To run the server:")
        print(f"   python {app_file.name}")
        print(f"\n📚 Then access:")
        print(f"   - API: http://localhost:7777")
        print(f"   - Docs: http://localhost:7777/docs")
        print(f"   - Config: http://localhost:7777/config")
        return
    
    # Handle --serve (AgentOS server mode)
    if args.serve:
        print("🚀 Starting Helix AgentOS Server...")
        orchestrator = AgnoHelixOrchestrator(config)
        orchestrator.serve(
            host=args.host,
            port=args.port,
            reload=args.reload
        )
        return
    
    # Handle --set-model
    if args.set_model:
        parts = args.set_model.split()
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                if key == "provider":
                    config.selected_provider = value
                elif key == "model":
                    config.selected_model = value
                elif key == "embedder_provider":
                    config.selected_embedder_provider = value
                elif key == "embedder_model":
                    config.selected_embedder_model = value
        
        config.save_user_preferences()
        print("✅ Model preferences updated")
        return
    
    # Handle --start (interactive mode)
    if args.start:
        print("🚀 Helix Interactive Mode")
        print("=" * 60)
        print("Enter your prompts (or 'quit' to exit)\n")
        
        while True:
            try:
                prompt = input("helix> ").strip()
                if not prompt:
                    continue
                if prompt.lower() in ('quit', 'exit', 'q'):
                    print("Goodbye!")
                    break
                
                run_helix(
                    prompt=prompt,
                    config=config,
                    auto_push=not args.no_push,
                    require_confirmation=args.confirm
                )
                print()
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
        
        return
    
    # Require prompt if not in interactive mode
    if not args.prompt:
        parser.print_help()
        sys.exit(1)
    
    # Run with prompt
    run_helix(
        prompt=args.prompt,
        config=config,
        auto_push=not args.no_push,
        require_confirmation=args.confirm
    )


if __name__ == "__main__":
    main()