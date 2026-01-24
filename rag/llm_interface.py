"""
LLM interface with support for multiple backends.

Supports:
- GroqLLM: Cloud-based LLM via Groq API (llama3-70b-8192, mixtral, etc.)
- OllamaLLM: Local LLM via Ollama (llama3, mistral, etc.)
- DummyLLM: Placeholder for testing without LLM
- Extensible for OpenAI, Claude, HuggingFace, etc.

Design Pattern:
- Abstract LLMInterface defines contract
- Concrete implementations handle different backends
- Graceful error handling (API errors, network issues, etc.)
"""

import subprocess
import json
import sys
import os
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMInterface:
    """Abstract base class for LLM interactions."""

    def generate_answer(self, query: str, context: str) -> str:
        """
        Generate an answer based on query and context.

        Args:
            query (str): User question about the code
            context (str): Retrieved code context from RAG

        Returns:
            str: Generated answer from the LLM
        
        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError("Subclasses must implement generate_answer")


class GroqLLM(LLMInterface):
    """
    Cloud-based LLM interface using Groq API.
    
    Requires:
    - Groq API key (get from https://console.groq.com)
    - GROQ_API_KEY environment variable set
    - requests library (pip install requests)
    
    Model: mixtral-8x7b-32768 (fast, high-quality open-source model)
    """
    
    # Prompt template for code analysis
    SYSTEM_PROMPT = """You are a senior Python software engineer and code reviewer.

You are analyzing a Python codebase using extracted AST context and code retrieval.

Your task:
1. Explain what the code component does
2. Mention relevant classes, functions, and their responsibilities
3. Keep explanations concise and accurate
4. Use ONLY the provided context (no hallucinations or external knowledge)
5. If information is not in the context, say so explicitly

Format your response clearly with headers and bullet points when appropriate."""

    def __init__(self, model: str = "mixtral-8x7b-32768", api_key: Optional[str] = None):
        """
        Initialize Groq LLM interface.
        
        Args:
            model (str): Groq model name (e.g., 'llama3-70b-8192', 'mixtral-8x7b-32768')
            api_key (str): Groq API key. If None, reads from GROQ_API_KEY env var
        
        Raises:
            RuntimeError: If API key is not provided or invalid
        """
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            logger.error("GROQ_API_KEY not set in environment")
            raise RuntimeError(
                "Groq API key not found. Please set GROQ_API_KEY environment variable.\n"
                "Get your API key from: https://console.groq.com\n"
                "Then set: export GROQ_API_KEY=your_key_here"
            )
        
        self._check_groq_availability()
    
    def _check_groq_availability(self) -> None:
        """
        Validate that requests library is available and API key is valid.
        
        Raises:
            RuntimeError: If requests not installed or API key invalid
        """
        try:
            import requests
            logger.info("requests library available for Groq API")
        except ImportError:
            logger.error("requests library not installed")
            raise RuntimeError(
                "requests library is required for Groq API.\n"
                "Install with: pip install requests"
            )
        
        # Validate API key format (basic check)
        if not self.api_key or len(self.api_key) < 10:
            raise RuntimeError("GROQ_API_KEY appears to be invalid (too short)")
        
        logger.info(f"Using Groq model: {self.model}")
    
    def generate_answer(self, query: str, context: str) -> str:
        """
        Generate an answer using Groq cloud LLM.
        
        Args:
            query (str): User question about the code
            context (str): Retrieved code context from RAG
        
        Returns:
            str: Generated explanation from the LLM
        
        Raises:
            RuntimeError: If Groq API call fails
        """
        import requests
        
        # Build the complete prompt
        prompt = self._build_prompt(query, context)
        
        logger.debug(f"Sending query to Groq ({self.model}): {query[:50]}...")
        
        try:
            # Call Groq API
            url = "https://api.groq.com/openai/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 0.9
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 401:
                logger.error("Groq API authentication failed")
                raise RuntimeError(
                    "Groq API authentication failed. Check your GROQ_API_KEY.\n"
                    "Get a valid key from: https://console.groq.com"
                )
            elif response.status_code == 429:
                logger.error("Groq API rate limited")
                raise RuntimeError(
                    "Groq API rate limit exceeded. Please try again later."
                )
            elif response.status_code != 200:
                logger.error(f"Groq API error: {response.status_code}")
                raise RuntimeError(
                    f"Groq API error: {response.status_code}\n{response.text}"
                )
            
            result = response.json()
            
            # Extract answer from response
            if "choices" not in result or not result["choices"]:
                raise RuntimeError("Invalid response format from Groq API")
            
            answer = result["choices"][0]["message"]["content"].strip()
            logger.info(f"Groq response received ({len(answer)} chars)")
            return answer
        
        except requests.exceptions.Timeout:
            logger.error("Groq API request timed out")
            raise RuntimeError("Groq API request timed out. Try again or simplify your query.")
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Groq API")
            raise RuntimeError(
                "Failed to connect to Groq API. Check your internet connection.\n"
                "API: https://api.groq.com"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response: {e}")
            raise RuntimeError(f"Invalid response from Groq API: {e}")
        except Exception as e:
            logger.error(f"Unexpected Groq error: {e}")
            raise RuntimeError(f"Failed to get response from Groq: {e}")
    
    def _build_prompt(self, query: str, context: str) -> str:
        """
        Build the complete prompt for Groq.
        
        Args:
            query (str): User question
            context (str): Code context from RAG retrieval
        
        Returns:
            str: Complete prompt with context and question
        """
        prompt = f"""Context extracted from a Python codebase (AST + FAISS):
{context}

User Question:
{query}

Answer clearly and accurately.
Mention functions, classes, and their responsibilities.
Do not assume anything beyond the given context."""
        
        return prompt


class OllamaLLM(LLMInterface):
    """
    Local LLM interface using Ollama.
    
    Requires:
    - Ollama installed (https://ollama.ai)
    - Model available locally (e.g., ollama pull llama3)
    - Ollama running (ollama serve or ollama run llama3)
    
    Uses subprocess to call Ollama CLI directly (no external Python libs).
    """
    
    # Prompt template for code analysis
    SYSTEM_PROMPT = """You are a senior Python software engineer and code reviewer.

You are analyzing a Python codebase using extracted AST context.

Your task:
1. Explain what the code component does
2. Mention relevant classes, functions, and their responsibilities
3. Keep explanations concise and accurate
4. Use ONLY the provided context (no hallucinations or external knowledge)
5. If information is not in the context, say so explicitly

Format your response clearly with headers and bullet points."""

    def __init__(self, model: str = "llama3", timeout: int = 120):
        """
        Initialize Ollama LLM interface.
        
        Args:
            model (str): Model name (e.g., 'llama3', 'mistral', 'neural-chat')
            timeout (int): Timeout for Ollama subprocess in seconds
        """
        self.model = model
        self.timeout = timeout
        self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> None:
        """
        Check if Ollama is installed and the model is available.
        
        Raises:
            RuntimeError: If Ollama is not installed or model not found
        """
        # Check if ollama command is available
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Ollama command failed")
            logger.info(f"Ollama found: {result.stdout.strip()}")
        except FileNotFoundError:
            logger.error("Ollama not installed. Install from https://ollama.ai")
            raise RuntimeError(
                "Ollama not found. Please install Ollama from https://ollama.ai\n"
                "Then pull a model: ollama pull llama3\n"
                "And start Ollama: ollama serve"
            )
        except subprocess.TimeoutExpired:
            logger.error("Ollama command timed out")
            raise RuntimeError("Ollama check timed out")
        
        # Check if model is available
        logger.info(f"Using Ollama model: {self.model}")
    
    def generate_answer(self, query: str, context: str) -> str:
        """
        Generate an answer using Ollama local LLM.
        
        Args:
            query (str): User question about the code
            context (str): Retrieved code context from RAG
        
        Returns:
            str: Generated explanation from the LLM
        
        Raises:
            RuntimeError: If Ollama is not running or fails
        """
        # Build the complete prompt
        prompt = self._build_prompt(query, context)
        
        logger.debug(f"Sending query to Ollama ({self.model}): {query[:50]}...")
        
        try:
            # Call Ollama via subprocess
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else result.stdout
                logger.error(f"Ollama error: {error_msg}")
                
                # Provide helpful error messages
                if "connection refused" in error_msg.lower() or "could not connect" in error_msg.lower():
                    raise RuntimeError(
                        f"Ollama is not running. Please start it with: ollama serve\n"
                        f"Error: {error_msg}"
                    )
                elif "model" in error_msg.lower() and "not found" in error_msg.lower():
                    raise RuntimeError(
                        f"Model '{self.model}' not found. Pull it with: ollama pull {self.model}\n"
                        f"Error: {error_msg}"
                    )
                else:
                    raise RuntimeError(f"Ollama error: {error_msg}")
            
            answer = result.stdout.strip()
            logger.info(f"Ollama response received ({len(answer)} chars)")
            return answer
        
        except subprocess.TimeoutExpired:
            logger.error(f"Ollama timeout after {self.timeout}s")
            raise RuntimeError(
                f"Ollama timed out after {self.timeout} seconds. "
                f"Try increasing timeout or simplifying your query."
            )
        except Exception as e:
            logger.error(f"Unexpected Ollama error: {e}")
            raise RuntimeError(f"Failed to get response from Ollama: {e}")
    
    def _build_prompt(self, query: str, context: str) -> str:
        """
        Build the complete prompt for Ollama.
        
        Args:
            query (str): User question
            context (str): Code context
        
        Returns:
            str: Complete prompt with system message and context
        """
        prompt = f"""{self.SYSTEM_PROMPT}

Context (from analyzed codebase):
{context}

User Question:
{query}

Please provide a clear, accurate explanation based ONLY on the provided context."""
        
        return prompt


class DummyLLM(LLMInterface):
    """
    Dummy LLM for testing without a real LLM backend.
    
    Returns a simple formatted response without making external calls.
    Useful for testing the RAG pipeline structure.
    """

    def generate_answer(self, query: str, context: str) -> str:
        """
        Return a dummy response for testing.
        
        Args:
            query (str): User question
            context (str): Retrieved context
        
        Returns:
            str: Simple test response
        """
        context_preview = context[:200].replace('\n', ' ')
        return (
            f"[DUMMY LLM RESPONSE - For testing only]\n\n"
            f"Question: {query}\n\n"
            f"Context summary: {context_preview}...\n\n"
            f"Note: This is a placeholder response. "
            f"To use a real LLM, configure one of:\n"
            f"1. Groq (cloud): Set LLM_PROVIDER=groq and GROQ_API_KEY\n"
            f"   Get key: https://console.groq.com\n"
            f"2. Ollama (local): Set LLM_PROVIDER=ollama\n"
            f"   Install: https://ollama.ai\n"
            f"   Then: ollama pull llama3 && ollama serve"
        )


# For future extensibility
class MockLLM(LLMInterface):
    """
    Mock LLM that returns predefined responses.
    
    Useful for testing without external dependencies.
    """
    
    def __init__(self, response: str = "Mock response"):
        """Initialize with a predefined response."""
        self.response = response
    
    def generate_answer(self, query: str, context: str) -> str:
        """Return the predefined response."""
        return self.response
