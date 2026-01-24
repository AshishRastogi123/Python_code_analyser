# Groq LLM Integration - Testing Guide

Quick reference for testing the Groq integration with different configurations.

---

## 🧪 Testing Scenarios

### Test 1: Verify Imports (No Setup Required)

```bash
cd d:\Python_code_analyser

# Test GroqLLM import
python -c "from rag.llm_interface import GroqLLM; print('✓ GroqLLM imported')"

# Test OllamaLLM import
python -c "from rag.llm_interface import OllamaLLM; print('✓ OllamaLLM imported')"

# Test DummyLLM import
python -c "from rag.llm_interface import DummyLLM; print('✓ DummyLLM imported')"

# Test pipeline import
python -c "from rag.pipeline import rag_query; print('✓ Pipeline imported')"
```

**Expected Result:** All imports succeed

---

### Test 2: Test with DummyLLM (Fallback Testing)

```bash
# Set provider to dummy
set LLM_PROVIDER=dummy
# or on macOS/Linux: export LLM_PROVIDER=dummy

# Run analyzer with dummy LLM
python analyzer.py sample.py --command index
python analyzer.py --command query --query "What functions are in this file?"
```

**Expected Result:**
```
[DUMMY LLM RESPONSE - For testing only]

Question: What functions are in this file?

Context summary: ...

Note: This is a placeholder response...
```

---

### Test 3: Test GroqLLM with Valid API Key

```bash
# 1. Get your API key from https://console.groq.com

# 2. Set environment variables
set GROQ_API_KEY=gsk_your_actual_key_here
set LLM_PROVIDER=groq

# 3. Verify configuration
python -c "from utils.config import Config; Config.initialize(); print('✓ API Key set:', bool(Config.groq_api_key())); print('✓ Provider:', Config.llm_provider())"

# 4. Test LLM initialization
python -c "from rag.llm_interface import GroqLLM; llm = GroqLLM(); print('✓ GroqLLM initialized successfully')"

# 5. Test with actual query
python analyzer.py sample.py --command index
python analyzer.py --command query --query "What functions are in this file?"
```

**Expected Result:**
```
Based on the provided context:

## Functions Found

### analyze_file(filename: str)
Purpose: Main entry point for analyzing Python files
Parameters: filename (str) - Path to Python file
Returns: dict containing analysis results

### extract_entities(tree, filename)
Purpose: Extracts classes and functions from AST
...
```

---

### Test 4: Test Error Handling - Missing API Key

```bash
# Clear API key
set GROQ_API_KEY=
set LLM_PROVIDER=groq

# Try to initialize GroqLLM
python -c "from rag.llm_interface import GroqLLM; llm = GroqLLM()"
```

**Expected Result:**
```
RuntimeError: Groq API key not found. Please set GROQ_API_KEY environment variable.
Get your API key from: https://console.groq.com
Then set: export GROQ_API_KEY=your_key_here
```

---

### Test 5: Test Error Handling - Invalid API Key

```bash
# Set invalid API key
set GROQ_API_KEY=invalid_key_123
set LLM_PROVIDER=groq

# Try to query
python analyzer.py --command query --query "What is in this code?"
```

**Expected Result:**
```
RuntimeError: Groq API authentication failed. Check your GROQ_API_KEY.
Get a valid key from: https://console.groq.com
```

---

### Test 6: Test Graceful Fallback

```bash
# Set Groq as provider but use invalid key
set LLM_PROVIDER=groq
set GROQ_API_KEY=invalid_key

# Run query
python analyzer.py --command query --query "Explain this code"
```

**Expected Behavior:**
1. Pipeline tries to initialize GroqLLM
2. Gets authentication error
3. Falls back to DummyLLM
4. Returns dummy response with fallback message

---

### Test 7: Test Configuration Validation

```bash
# Set Groq provider without API key
set LLM_PROVIDER=groq
set GROQ_API_KEY=

# Run validation
python -c "from utils.config import Config; Config.initialize(); is_valid, warnings = Config.validate(); [print('⚠️', w) for w in warnings]"
```

**Expected Result:**
```
⚠️ LLM provider set to 'groq' but GROQ_API_KEY not set
   Get key from: https://console.groq.com
   Set: export GROQ_API_KEY=your_key_here
```

---

### Test 8: Test Multiple Provider Switching

```bash
# Test with Dummy
set LLM_PROVIDER=dummy
python analyzer.py --command query --query "Test 1"
echo "✓ Test 1: Dummy LLM works"

# Test with Groq (if API key available)
set LLM_PROVIDER=groq
set GROQ_API_KEY=gsk_your_key_here
python analyzer.py --command query --query "Test 2"
echo "✓ Test 2: Groq LLM works"

# Test with Ollama (if running)
set LLM_PROVIDER=ollama
python analyzer.py --command query --query "Test 3"
echo "✓ Test 3: Ollama LLM works"
```

**Expected Result:** All three providers can be switched seamlessly

---

### Test 9: Test Streamlit UI with Groq

```bash
# Set Groq provider
set GROQ_API_KEY=gsk_your_key_here
set LLM_PROVIDER=groq

# Index a file
python analyzer.py sample.py --command index

# Start Streamlit UI
streamlit run ui/app.py
```

**Expected UI Behavior:**
1. Upload or select indexed file
2. Enter query in text box
3. Click "Ask Question"
4. See Groq response appear in UI

---

## 📊 Test Matrix

| Test | Setup | Command | Expected Result |
|------|-------|---------|-----------------|
| Import GroqLLM | None | `from rag.llm_interface import GroqLLM` | Success |
| Import OllamaLLM | None | `from rag.llm_interface import OllamaLLM` | Success |
| Import DummyLLM | None | `from rag.llm_interface import DummyLLM` | Success |
| Init DummyLLM | None | `DummyLLM()` | Success |
| Config with dummy | `LLM_PROVIDER=dummy` | `Config.llm_provider()` | "dummy" |
| Config check API key | None | `Config.groq_api_key()` | None (if not set) |
| Init GroqLLM (no key) | `GROQ_API_KEY=` | `GroqLLM()` | RuntimeError |
| Init GroqLLM (valid key) | `GROQ_API_KEY=gsk_...` | `GroqLLM()` | Success |
| Query with Groq | Groq key set | `rag_query("...")` | Real response |
| Query with Dummy | `LLM_PROVIDER=dummy` | `rag_query("...")` | Dummy response |
| Fallback on error | Invalid Groq key | `rag_query("...")` | Falls back to Dummy |

---

## 🔍 Debugging Tips

### Enable Debug Logging

```bash
set LOG_LEVEL=DEBUG
python analyzer.py --command query --query "..."
```

**Shows:**
- LLM provider being used
- API requests being sent
- Response received
- Any errors encountered

### Check Configuration

```bash
python -c "from utils.config import Config; Config.initialize(); print(Config.to_dict())"
```

**Shows:**
- All configuration values
- API keys (masked for security)
- Paths and settings

### Validate Installation

```bash
# Check requests library
python -c "import requests; print('✓ requests installed:', requests.__version__)"

# Check RAG modules
python -c "from rag import embeddings, faiss_index, retriever, pipeline; print('✓ All RAG modules available')"

# Check AST parser
python -c "from core.ast_parser import SafeParser; print('✓ AST parser available')"
```

### Test API Connectivity

```bash
python -c "import requests; r = requests.get('https://api.groq.com', timeout=5); print('✓ API reachable')" 2>/dev/null || echo "✗ API unreachable"
```

---

## 🚨 Common Issues & Solutions

### Issue: "requests library not installed"

**Solution:**
```bash
pip install requests
```

### Issue: "GROQ_API_KEY not found"

**Solution:**
```bash
# Set environment variable
set GROQ_API_KEY=gsk_your_key_here

# Or add to .env
echo "GROQ_API_KEY=gsk_your_key_here" >> .env
```

### Issue: "Groq API authentication failed"

**Causes:**
- Invalid API key
- Key expired
- Key from wrong account

**Solution:**
1. Visit https://console.groq.com
2. Check/create new API key
3. Update GROQ_API_KEY

### Issue: "Connection refused"

**Causes:**
- Network issue
- API endpoint down
- Firewall blocking

**Solution:**
```bash
# Test connectivity
python -c "import requests; requests.get('https://api.groq.com')"

# Or use Ollama (local alternative)
set LLM_PROVIDER=ollama
```

### Issue: "Timeout after 30 seconds"

**Causes:**
- Slow network
- Groq API overloaded
- Large context

**Solution:**
1. Try simpler query
2. Reduce context (top_k parameter)
3. Try again later

---

## ✅ Success Criteria

✅ All tests pass when:

1. **Imports work:** All LLM classes import successfully
2. **Configuration works:** GROQ_API_KEY can be read from env
3. **Dummy fallback works:** Returns placeholder responses
4. **Groq works:** Returns real responses with valid key
5. **Error handling works:** Proper error messages for issues
6. **Fallback works:** Gracefully switches to DummyLLM on error
7. **CLI works:** Queries return answers via CLI
8. **UI works:** Streamlit shows responses

---

## 📝 Test Log Template

Use this to document your testing:

```
Testing Date: ___________
Groq API Key: [MASKED]
Environment: Windows/macOS/Linux

Test 1: Imports - PASS/FAIL
Test 2: DummyLLM - PASS/FAIL
Test 3: GroqLLM Valid Key - PASS/FAIL
Test 4: GroqLLM Missing Key - PASS/FAIL
Test 5: GroqLLM Invalid Key - PASS/FAIL
Test 6: Fallback Behavior - PASS/FAIL
Test 7: Config Validation - PASS/FAIL
Test 8: Provider Switching - PASS/FAIL
Test 9: Streamlit UI - PASS/FAIL

Notes:
- ___________
- ___________

Result: ALL TESTS PASSED ✅
```

---

Made with ❤️ for thorough testing.
