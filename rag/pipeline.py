"""
RAG Pipeline: Combines retrieval and generation for answering queries.

This module orchestrates the Retrieval-Augmented Generation process:
1. Retrieval: Find similar code chunks from FAISS index
2. Generation: Use LLM to generate answer based on context

Supports multiple LLM backends:
- GroqLLM: Cloud-based LLM via Groq API (llama3-70b-8192, etc.)
- OllamaLLM: Local LLM via Ollama (llama3, mistral, etc.)
- DummyLLM: Placeholder for testing without LLM
- Custom implementations of LLMInterface
"""

from .retriever import retrieve
from .llm_interface import GroqLLM, OllamaLLM, DummyLLM
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


def rag_query(query, top_k=5, llm=None):
    """
    Perform a RAG query: retrieve relevant chunks and generate an answer.

    Args:
        query (str): User query about the codebase
        top_k (int): Number of code chunks to retrieve (default: 5)
        llm: LLM interface instance. If None, uses configured provider:
            - "ollama": OllamaLLM (local LLM via Ollama)
            - "dummy": DummyLLM (testing without real LLM)

    Returns:
        str: Generated answer explaining the code

    Raises:
        RuntimeError: If configured LLM is not available
    """
    # Initialize LLM if not provided
    if llm is None:
        llm = _get_default_llm()
    
    logger.info(f"RAG Query: {query[:50]}...")
    
    # Retrieve relevant chunks from FAISS index
    logger.debug(f"Retrieving top {top_k} code chunks")
    retrieved_chunks = retrieve(query, top_k=top_k)
    
    if not retrieved_chunks:
        logger.warning("No code chunks retrieved from FAISS index")
        return (
            "No relevant code found in the indexed codebase. "
            "Make sure to index your code first: python analyzer.py <file> --command index"
        )
    
    context = "\n".join(retrieved_chunks)
    logger.debug(f"Context size: {len(context)} characters")
    
    # Generate answer using LLM
    logger.info("Generating answer from LLM")
    answer = llm.generate_answer(query, context)
    
    logger.info("RAG query complete")
    return answer


def _get_default_llm():
    """
    Get the default LLM based on configuration.
    
    Returns:
        LLMInterface: Configured LLM instance
    
    Raises:
        RuntimeError: If configured LLM is not available
    """
    provider = Config.llm_provider()
    logger.info(f"Using LLM provider: {provider}")
    
    try:
        if provider == "groq":
            logger.debug("Initializing GroqLLM")
            return GroqLLM()
        elif provider == "ollama":
            model = Config.embedding_model()  # Can extend for separate LLM_MODEL later
            logger.debug(f"Initializing OllamaLLM with model: llama3")
            return OllamaLLM(model="llama3")
        elif provider == "dummy":
            logger.debug("Initializing DummyLLM (testing mode)")
            return DummyLLM()
        else:
            logger.warning(f"Unknown provider '{provider}', falling back to DummyLLM")
            return DummyLLM()
    except RuntimeError as e:
        # If Groq/Ollama fails, provide helpful message and fallback
        logger.error(f"Failed to initialize LLM: {e}")
        if provider in ("groq", "ollama"):
            logger.info(f"Falling back to DummyLLM. Error details: {e}")
            return DummyLLM()
        raise


# Alias for convenience
def run_query(query, top_k=5, llm=None):
    """
    Alias for rag_query() for backward compatibility.
    
    Args:
        query (str): User query
        top_k (int): Number of chunks to retrieve
        llm: LLM instance (optional)
    
    Returns:
        str: Generated answer
    """
    return rag_query(query, top_k=top_k, llm=llm)
