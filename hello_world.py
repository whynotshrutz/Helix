#!/usr/bin/env python3
"""
Hello World Script

A simple Python script that demonstrates basic output.
"""

def main():
    """Print a friendly greeting to the console."""
    print("Hello, World!")
    print("Welcome to Helix - Your Multi-Agent Coding Assistant! 🚀")
    
    # Show some fun facts
    facts = [
        "Helix uses 5 specialized AI agents",
        "Powered by NVIDIA NIM and Llama 3.1",
        "Now integrated with VS Code!",
        "Try: @helix-coder in VS Code chat"
    ]
    
    print("\n📚 Fun Facts:")
    for i, fact in enumerate(facts, 1):
        print(f"  {i}. {fact}")


if __name__ == "__main__":
    main()
