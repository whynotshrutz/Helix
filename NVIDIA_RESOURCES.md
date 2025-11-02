# NVIDIA NIM & AI Development Resources

## Official NVIDIA NIM Resources

### Platform & Models
- **NVIDIA NIM Platform**: https://build.nvidia.com/
- **Llama-3.1-nemotron-nano-8B-v1 Documentation**: https://build.nvidia.com/nvidia/llama-3_1-nemotron-nano-8b-v1
- **NVIDIA Retrieval Embedding NIM**: https://build.nvidia.com/explore/retrieval
- **NIM API Reference**: https://docs.nvidia.com/nim/
- **Model Cards and Performance Specs**: Available on NVIDIA build platform

### NVIDIA AI Playground
- **Explore Models**: https://build.nvidia.com/explore/

## Prompt Engineering for Agentic AI

- **Prompt Engineering Guide**: https://www.promptingguide.ai/
- **LangChain Prompt Templates**: https://python.langchain.com/docs/modules/model_io/prompts/
- **Best Practices for Instruction Following**: https://platform.openai.com/docs/guides/prompt-engineering

## Retrieval-Augmented Generation (RAG)

- **NVIDIA RAG Best Practices**: https://developer.nvidia.com/blog/rag/
- **Building RAG Applications**: https://python.langchain.com/docs/use_cases/question_answering/
- **Vector Database Comparisons**: https://www.pinecone.io/learn/vector-database/
- **Embedding Model Selection Guide**: https://huggingface.co/blog/mteb

## Current Helix Setup

- **Model**: nvidia/llama-3.1-nemotron-nano-8b-v1
- **API Base**: https://integrate.api.nvidia.com/v1
- **Mode**: Streaming chat with inline completions
- **Features**: 
  - Real-time inline code completions
  - Automatic file creation via chat commands
  - NVIDIA NIM integration

## Future Enhancements

1. **Enable RAG with NVIDIA Embeddings**
   - Integrate NVIDIA Retrieval Embedding NIM
   - Configure ChromaDB with NVIDIA embeddings
   - Add code context from workspace

2. **Improve Prompt Engineering**
   - Use LangChain prompt templates
   - Add few-shot examples for better code generation
   - Context-aware completions

3. **Add More Tools**
   - Git operations
   - Terminal command execution
   - Code refactoring suggestions
   - Test generation

## Useful Commands

```bash
# Backend
cd backend
python -m uvicorn helix.server:app --host 127.0.0.1 --port 8000 --reload

# Extension
cd vscode-extension
npm run build
# Press F5 to launch Extension Development Host
```

## Configuration Files

- **Backend**: `backend/.env`
- **Extension**: `vscode-extension/src/extension.ts`
- **Agent**: `backend/src/helix/agno_agent.py`
