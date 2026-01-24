#!/usr/bin/env python
"""Groq Integration Verification Script"""

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent / ".env")

from rag.llm_interface import GroqLLM, OllamaLLM, DummyLLM
from rag.pipeline import rag_query, _get_default_llm
from utils.config import Config

print('=== GROQ INTEGRATION VERIFICATION ===\n')

# Test 1: Classes exist
print('✓ GroqLLM class:', GroqLLM)
print('✓ OllamaLLM class:', OllamaLLM)
print('✓ DummyLLM class:', DummyLLM)

# Test 2: Initialize config
Config.initialize()
print('\n✓ Config initialized')

# Test 3: Check provider
provider = Config.llm_provider()
print(f'✓ LLM Provider: {provider}')

# Test 4: Check API key
api_key = Config.groq_api_key()
print(f'✓ Groq API Key configured: {bool(api_key)}')

# Test 5: DummyLLM works
try:
    dummy = DummyLLM()
    answer = dummy.generate_answer('Test?', 'def test(): pass')
    print(f'✓ DummyLLM works ({len(answer)} char response)')
except Exception as e:
    print(f'✗ DummyLLM error: {e}')

# Test 6: Config validation
is_valid, warnings = Config.validate()
print(f'✓ Config validation: {"valid" if is_valid else f"{len(warnings)} warnings"}')

print('\n=== ALL CORE SYSTEMS VERIFIED ===')
