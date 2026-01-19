"""
RAG Pipeline: Combines retrieval and generation for answering queries.
"""

from .retriever import retrieve
from .llm_interface import DummyLLM

def rag_query(query, top_k=5, llm=None):
    """
    Perform a RAG query: retrieve relevant chunks and generate an answer.

    Args:
        query (str): User query.
        top_k (int): Number of chunks to retrieve.
        llm: LLM interface instance, or None for default DummyLLM.

    Returns:
        str: Generated answer.
    """
    if llm is None:
        llm = DummyLLM()

    # Retrieve relevant chunks
    retrieved_chunks = retrieve(query, top_k=top_k)
    context = "\n".join(retrieved_chunks)

    # Generate answer
    answer = llm.generate_answer(query, context)
    return answer
