"""
Retriever module for fetching relevant chunks based on query.
"""

import numpy as np
from .embeddings import generate_embeddings, load_model
from .faiss_index import load_index

def retrieve(query, top_k=5):
    """
    Retrieve top-k relevant chunks for a query.

    Args:
        query (str): User query.
        top_k (int): Number of top results to retrieve.

    Returns:
        list: List of retrieved text chunks.
    """
    # Load model and generate query embedding
    model = load_model()
    query_embedding = generate_embeddings([query], model)[0]
    query_embedding = np.expand_dims(query_embedding, axis=0)
    faiss.normalize_L2(query_embedding)

    # Load index and search
    index, chunks = load_index()
    distances, indices = index.search(query_embedding, top_k)

    # Retrieve chunks
    retrieved = [chunks[i] for i in indices[0] if i < len(chunks)]
    return retrieved
