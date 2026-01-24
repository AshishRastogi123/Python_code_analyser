# Ollama Integration Guide

This document explains how to use Ollama (local LLM) with the Legacy Code Modernization Platform.

---

## 📋 Quick Start

### 1. Install Ollama

Download and install Ollama from https://ollama.ai

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:** Download installer from https://ollama.ai

**Verify installation:**
```bash
ollama --version
```

### 2. Pull a Model

The default model is `llama3`. You can also use `mistral`, `neural-chat`, or others.

```bash
# Pull llama3 (recommended, ~4 GB)
ollama pull llama3

# Or pull a smaller model
ollama pull mistral

# Or pull a larger model
ollama pull neural-chat
```

List available models: https://ollama.ai/library

### 3. Start Ollama

In a separate terminal, start the Ollama service:

```bash
ollama serve
```

This will run Ollama on `localhost:11434` (default).

### 4. Configure the Platform

Edit your `.env` file (or create one):

```bash
cp .env.example .env
```

Set the LLM provider:

```env
LLM_PROVIDER=ollama
```

### 5. Use It!

**Analyze and index a file:**
```bash
python analyzer.py sample.py --command index
```

**Query via CLI:**
```bash
python analyzer.py --command query --query "What does the process_data function do?"
```

**Query via Web UI:**
```bash
streamlit run ui/app.py
```

Then type your questions in the web interface!

---

## 🏗️ Architecture

### Data Flow

```
User Query
    ↓
RAG Pipeline (rag/pipeline.py)
    ├─ Retrieve: Find similar code chunks from FAISS index
    ├─ Generate: Send to Ollama via subprocess
    └─ Return: Answer from LLM
    ↓
Display in CLI or Streamlit UI
```

### OllamaLLM Class

Located in `rag/llm_interface.py`:

```python
from rag.llm_interface import OllamaLLM

# Initialize
llm = OllamaLLM(model="llama3")

# Generate answer
answer = llm.generate_answer(
    query="What does this function do?",
    context="def process_data(data): ..."
)
```

### Using Programmatically

```python
from rag.pipeline import rag_query

# Query with Ollama (if configured)
answer = rag_query("Explain the codebase architecture")
print(answer)
```

---

## 🔧 Configuration

### Environment Variables

**LLM Provider:**
```env
LLM_PROVIDER=ollama      # Use Ollama (default if configured)
LLM_PROVIDER=dummy       # Use dummy (testing without LLM)
```

**Logging:**
```env
LOG_LEVEL=DEBUG          # Verbose logging to see LLM interactions
LOG_FILE=./logs/app.log  # Log to file
```

### Python Configuration

```python
from utils.config import Config

Config.initialize()
print(Config.llm_provider())  # "ollama"
```

---

## 🎯 Common Use Cases

### 1. Code Architecture Explanation

```bash
python analyzer.py myapp.py --command index

python analyzer.py --command query \
  --query "Describe the overall architecture of this codebase"
```

**Ollama Response:**
```
Based on the analyzed code, here's the architecture:

[Classes]
- DataProcessor: Main processing class with methods for data validation and transformation
- Logger: Handles logging across the application

[Key Functions]
- process_data(): Main entry point that orchestrates data flow
- validate_input(): Input validation before processing
- save_results(): Persists processed data

[Dependencies]
- process_data() calls validate_input() and save_results()
- Logger is used throughout for debugging
```

### 2. Function Relationship Analysis

```bash
python analyzer.py --command query \
  --query "Which functions call process_data and what do they do?"
```

### 3. Class Hierarchy Understanding

```bash
python analyzer.py --command query \
  --query "Explain the DataProcessor class and its methods"
```

### 4. Error Path Analysis

```bash
python analyzer.py --command query \
  --query "How are errors handled in the load_data function?"
```

---

## 🚀 Performance Tips

### Model Selection

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| mistral | 4 GB | Very Fast | Good | Quick summaries |
| llama3 | 4 GB | Fast | Excellent | Recommended |
| neural-chat | 6 GB | Medium | Very Good | Detailed analysis |
| dolphin-mixtral | 26 GB | Slow | Superior | Complex analysis |

**Recommendation:** Start with `llama3` (4 GB, good balance)

### Optimize Responses

**Faster responses:**
```bash
# Set reasonable timeout
export OLLAMA_TIMEOUT=60  # seconds
```

**Better quality (slower):**
```bash
# Use larger model
ollama pull neural-chat
# Then configure: modify rag/pipeline.py to use it
```

### Hardware Requirements

- **CPU Only**: ≥8 GB RAM, modern processor
- **GPU (faster)**: NVIDIA (CUDA), AMD (ROCm), or Apple Silicon (Metal)
  - NVIDIA: Requires CUDA toolkit
  - AMD: Requires ROCm
  - Apple: Automatic GPU acceleration

---

## 🔍 Troubleshooting

### Error: "Ollama not found"

**Solution:** Install Ollama from https://ollama.ai

```bash
# Verify installation
ollama --version
```

### Error: "Connection refused"

**Cause:** Ollama is not running

**Solution:**
```bash
# In a separate terminal
ollama serve
```

### Error: "Model 'llama3' not found"

**Cause:** Model not downloaded locally

**Solution:**
```bash
# Pull the model
ollama pull llama3

# Check available models
ollama list
```

### Error: "Timeout after 120 seconds"

**Cause:** Query took too long

**Solutions:**
1. Use faster model: `ollama pull mistral`
2. Increase timeout in code:
   ```python
   llm = OllamaLLM(model="llama3", timeout=300)
   ```
3. Simplify your query or reduce context size

### Slow Responses

**Solutions:**
1. Use GPU acceleration if available
2. Use smaller/faster model (mistral)
3. Reduce number of retrieved chunks:
   ```bash
   # In code: rag_query(query, top_k=3)
   ```

---

## 🔌 Switching LLM Providers

### Currently Supported

- **OllamaLLM**: Local LLM via Ollama (implemented ✅)
- **DummyLLM**: Testing without LLM (implemented ✅)

### Future Support

- OpenAI (GPT-3.5, GPT-4)
- Claude (Anthropic)
- Local alternatives (Hugging Face Transformers)

### Adding a New Provider

1. Create a new class inheriting from `LLMInterface`:
   ```python
   # In rag/llm_interface.py
   class MyLLM(LLMInterface):
       def generate_answer(self, query: str, context: str) -> str:
           # Your implementation
           return answer
   ```

2. Update pipeline to support it:
   ```python
   # In rag/pipeline.py
   if provider == "my_llm":
       return MyLLM()
   ```

3. Update config:
   ```python
   # In utils/config.py
   # Add my_llm_api_key() method if needed
   ```

---

## 📊 Monitoring & Logging

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
python analyzer.py --command query --query "..."
```

**Output:**
```
[2026-01-24 14:32:15] [DEBUG   ] Sending query to Ollama (llama3): What does...
[2026-01-24 14:32:18] [INFO    ] Ollama response received (2456 chars)
```

### Check Ollama Status

```bash
# In another terminal
curl http://localhost:11434/api/tags

# Response: lists running models
{
  "models": [
    {
      "name": "llama3:latest",
      "modified_at": "2024-01-24T10:00:00.000000000Z",
      "size": 4000000000
    }
  ]
}
```

---

## 🎓 Example Prompts

### "Explain this function"
```
What does the authenticate_user function do? 
What parameters does it take? 
What does it return?
```

### "Find dependencies"
```
Which functions call calculate_total? 
What functions does calculate_total call?
```

### "Architecture review"
```
Describe the overall architecture and how components interact.
What are the main classes and their responsibilities?
```

### "Code quality"
```
Are there any potential issues in the error handling?
Which functions might benefit from refactoring?
```

---

## 📚 Resources

- **Ollama**: https://ollama.ai
- **Models**: https://ollama.ai/library
- **Documentation**: https://github.com/ollama/ollama/tree/main/docs

---

## ❓ FAQ

**Q: Can I run Ollama on a different machine?**  
A: Yes, update the connection (not implemented yet, use localhost for now)

**Q: Can I use multiple models?**  
A: Yes, modify the config and pipeline to support model selection

**Q: What if I want to use OpenAI instead?**  
A: Coming in Phase 2! Currently implemented are Ollama and Dummy LLM

**Q: Does Ollama require internet?**  
A: No, everything runs locally once model is downloaded

**Q: How do I uninstall Ollama?**  
A: Use your OS package manager or uninstall from Applications

---

Made with ❤️ for local-first LLM workflows.
