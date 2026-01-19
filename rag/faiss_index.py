"""
FAISS index module for storing and loading embeddings.
"""

import pickle
import numpy as np
import faiss

INDEX_FILE = "rag/index.faiss"
CHUNKS_FILE = "rag/chunks.pkl"

def build_and_save_index(chunks, embeddings):
    """
    Build FAISS index from embeddings and save to disk.

    Args:
        chunks (list): List of text chunks.
        embeddings (np.array): Embeddings array.
    """
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)

    # Create index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for cosine
    index.add(embeddings)

    # Save index and chunks
    faiss.write_index(index, INDEX_FILE)
    with open(CHUNKS_FILE, "wb") as f:
        pickle.dump(chunks, f)

    print(f"Index saved to {INDEX_FILE}, chunks to {CHUNKS_FILE}")

def load_index():
    """
    Load FAISS index and chunks from disk.

    Returns:
        tuple: (index, chunks)
    """
    index = faiss.read_index(INDEX_FILE)
    with open(CHUNKS_FILE, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks
