# Groq LLM Integration Guide

This document explains how to use **Groq** (cloud-based LLM) with the Legacy Code Modernization Platform.

---

## 📋 Quick Start

### 1. Get Groq API Key

Go to **https://console.groq.com** and:
1. Sign up for a free account
2. Navigate to **API Keys** section
3. Create a new API key
4. Copy the key (starts with `gsk_` or similar)

### 2. Configure Environment

Edit your `.env` file (or create one):

```bash
cp .env.example .env
```

Set your Groq configuration:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_actual_key_here
```

### 3. Install Dependencies

Ensure `requests` library is installed:

```bash
pip install requests
```

Or from requirements:

```bash
pip install -r requirements.txt
```

### 4. Analyze and Index Code

```bash
python analyzer.py sample.py --command index
```

### 5. Query Your Code!

**Via CLI:**
```bash
python analyzer.py --command query --query "What does the process_data function do?"
```

**Via Web UI:**
```bash
streamlit run ui/app.py
```

Then ask questions about your code!

---

## 🏗️ How Groq Integration Works

### Architecture

```
User Query
    ↓
RAG Pipeline (rag/pipeline.py)
    ├─ Retrieve: Find similar code chunks from FAISS index
    ├─ Generate: Send to Groq API via HTTPS
    └─ Return: Answer from Groq LLM
    ↓
Display in CLI or Streamlit UI
```

### GroqLLM Class

Located in `rag/llm_interface.py`:

**Key Features:**
- Uses OpenAI-compatible Groq API endpoint
- Model: `llama3-70b-8192` (fast, high-quality)
- System prompt: Instructs model as "senior Python engineer"
- Error handling: API auth, rate limits, network issues
- Graceful fallback to DummyLLM if Groq fails

**Usage:**
```python
from rag.llm_interface import GroqLLM

# Initialize with API key
llm = GroqLLM(api_key="gsk_your_key_here")

# Or use environment variable (automatic)
llm = GroqLLM()

# Generate answer
answer = llm.generate_answer(
    query="What does this function do?",
    context="def process_data(data): ..."
)
print(answer)
```

### RAG Pipeline Integration

Located in `rag/pipeline.py`:

**Automatic Provider Selection:**
```python
from rag.pipeline import rag_query

# Uses provider from Config.llm_provider()
answer = rag_query("Explain the codebase architecture")
```

**With Error Handling:**
- If Groq API fails → Falls back to DummyLLM with helpful message
- If network error → Returns clear error message
- If rate-limited → Helpful message to try again later

---

## 🔧 Configuration

### Environment Variables

**Required:**
```env
LLM_PROVIDER=groq          # Enable Groq provider
GROQ_API_KEY=gsk_...       # Your API key
```

**Optional:**
```env
LOG_LEVEL=DEBUG            # Verbose logging to see API interactions
LOG_FILE=./logs/app.log    # Log file for debugging
```

### Python Configuration

```python
from utils.config import Config

Config.initialize()
print(Config.llm_provider())   # "groq"
print(Config.groq_api_key())   # "gsk_..." (masked if in logs)
```

---

## 📊 Model Options

Groq API supports multiple models with different trade-offs:

| Model | Speed | Quality | Context | Use Case |
|-------|-------|---------|---------|----------|
| mixtral-8x7b-32768 | Very Fast | Good | 32K | Quick summaries |
| llama3-70b-8192 | Fast | Excellent | 8K | Recommended |
| llama2-70b-4096 | Medium | Very Good | 4K | Detailed analysis |

**Recommendation:** Stick with `llama3-70b-8192` (default, good balance)

To use a different model, modify `rag/pipeline.py`:

```python
def _get_default_llm():
    if provider == "groq":
        return GroqLLM(model="mixtral-8x7b-32768")  # Change model
```

---

## 🎯 Common Use Cases

### 1. Explain a Function

```bash
python analyzer.py --command query \
  --query "What does the authenticate_user function do?"
```

**Groq Response:**
```
Based on the provided code context:

## Function: authenticate_user

**Purpose:** Validates user credentials against the database

**Parameters:**
- username (str): User's login name
- password (str): User's password

**Returns:**
- tuple: (success: bool, user_id: int or None)

**Implementation:**
1. Query database for user record
2. Hash provided password
3. Compare with stored hash
4. Return success status and user ID
```

### 2. Understand Class Structure

```bash
python analyzer.py --command query \
  --query "Explain the DataProcessor class and all its methods"
```

### 3. Find Relationships

```bash
python analyzer.py --command query \
  --query "Which functions call calculate_total and what are their dependencies?"
```

### 4. Code Quality Analysis

```bash
python analyzer.py --command query \
  --query "Are there any error handling issues in the load_config function?"
```

---

## 🚀 Performance & Costs

### Response Times

- **First request:** ~1-2 seconds (API latency)
- **Subsequent requests:** ~0.5-1 second (with caching)
- **Max timeout:** 30 seconds (configurable)

### API Rate Limits (Free Tier)

- Groq free tier is quite generous
- ~25-30 requests per minute
- See console.groq.com for current limits
- Paid plans for higher usage

### Cost Optimization

1. **Use smaller context:** Fewer retrieved chunks = faster response
   ```bash
   # Query with top_k=3 instead of default 5
   # (Modify pipeline.py or rag_query call)
   ```

2. **Reuse results:** Cache answers for similar questions

3. **Monitor usage:** Check Groq console for costs

---

## 🔌 Switching LLM Providers

### Switch to Ollama (Local)

```env
LLM_PROVIDER=ollama
```

Then install Ollama and run:
```bash
ollama pull llama3
ollama serve
```

### Switch to Dummy (Testing)

```env
LLM_PROVIDER=dummy
```

No external calls, useful for testing.

### Add New Provider (Future)

1. Create class in `rag/llm_interface.py`:
   ```python
   class MyLLM(LLMInterface):
       def generate_answer(self, query: str, context: str) -> str:
           # Implementation
           return answer
   ```

2. Update pipeline in `rag/pipeline.py`:
   ```python
   elif provider == "my_provider":
       return MyLLM(api_key=Config.my_api_key())
   ```

3. Add config method in `utils/config.py`:
   ```python
   @classmethod
   def my_api_key(cls) -> Optional[str]:
       return os.getenv("MY_API_KEY", None)
   ```

---

## 🔍 Troubleshooting

### Error: "GROQ_API_KEY not found"

**Solution:** Set environment variable

```bash
# macOS/Linux
export GROQ_API_KEY=gsk_your_key_here

# Windows PowerShell
$env:GROQ_API_KEY="gsk_your_key_here"

# Or add to .env file
GROQ_API_KEY=gsk_your_key_here
```

**Verify:**
```bash
python -c "from utils.config import Config; Config.initialize(); print(Config.groq_api_key())"
```

### Error: "Groq API authentication failed"

**Causes:**
- Invalid API key
- Key has expired
- API key has insufficient permissions

**Solutions:**
1. Verify key from https://console.groq.com
2. Create a new key if old one expired
3. Check key doesn't have typos

### Error: "requests library not installed"

**Solution:**
```bash
pip install requests
```

### Error: "Groq API rate limited"

**Cause:** Exceeded rate limit (free tier has limits)

**Solutions:**
1. Wait a minute and retry
2. Check usage at console.groq.com
3. Upgrade to paid plan for higher limits
4. Switch to Ollama for unlimited local requests

### Error: "Connection refused" or "Failed to connect"

**Cause:** Network issues or API endpoint down

**Solutions:**
1. Check internet connection
2. Verify API endpoint: https://api.groq.com
3. Try again in a few moments
4. Check Groq status page

### Slow Responses

**Causes:**
- Network latency
- Large context size
- API overload

**Solutions:**
1. Reduce context size (retrieve fewer chunks)
2. Use faster model (mixtral-8x7b-32768)
3. Simplify query
4. Wait during peak hours

---

## 📊 Monitoring & Debugging

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
python analyzer.py --command query --query "..."
```

**Output shows:**
```
[2026-01-24 14:32:15] [DEBUG   ] Sending query to Groq (llama3-70b-8192): What does...
[2026-01-24 14:32:18] [INFO    ] Groq response received (2456 chars)
```

### Check Groq Account Status

Visit **https://console.groq.com** to:
- View API key status
- Check usage statistics
- Monitor rate limits
- Review billing (if paid tier)

### View API Request Details

Add to code for debugging:
```python
from rag.llm_interface import GroqLLM

llm = GroqLLM()
# Will log detailed debug info
answer = llm.generate_answer(query, context)
```

---

## 📚 Resources

- **Groq Console:** https://console.groq.com
- **API Docs:** https://console.groq.com/docs
- **Models Available:** https://console.groq.com/docs/models
- **Status Page:** https://status.groq.com

---

## 🎓 API Response Format

Groq uses OpenAI-compatible format:

**Request:**
```json
{
  "model": "llama3-70b-8192",
  "messages": [
    {
      "role": "system",
      "content": "You are a senior Python software engineer..."
    },
    {
      "role": "user",
      "content": "Context: ...\n\nUser Question: ..."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Response:**
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Based on the provided context..."
      }
    }
  ]
}
```

---

## ❓ FAQ

**Q: Is Groq free?**  
A: Yes, Groq offers a free tier with generous rate limits. Paid plans available for higher usage.

**Q: Can I use Groq offline?**  
A: No, Groq is cloud-based. Use Ollama for offline/local LLM.

**Q: Which is faster, Groq or Ollama?**  
A: Groq cloud LLM is generally faster (0.5-1s) than local Ollama (varies by hardware). But Groq requires internet.

**Q: Can I switch between providers?**  
A: Yes, just change `LLM_PROVIDER` in `.env` and optionally set API keys.

**Q: What if my code is proprietary?**  
A: Code is sent to Groq's API. Use Ollama (local) if you need to keep code private.

**Q: Do you store my API key?**  
A: No, API key only stored in `.env` file locally. Never committed to version control.

**Q: Can I use multiple API keys for load balancing?**  
A: Not built-in, but can modify code to support it.

**Q: What's the context limit?**  
A: llama3-70b-8192 has 8K token context (roughly 6-8 pages of code).

---

Made with ❤️ for intelligent code analysis.
