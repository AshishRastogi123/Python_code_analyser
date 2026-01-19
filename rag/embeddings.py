"""
Embeddings module for generating vector embeddings using HuggingFace sentence-transformers.
"""

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

def load_model():
    """Load the sentence transformer model."""
    return SentenceTransformer(MODEL_NAME)

def generate_embeddings(chunks, model=None):
    """
    Generate embeddings for a list of text chunks.

    Args:
        chunks (list): List of text strings.
        model: Pre-loaded model, or None to load here.

    Returns:
        list: List of numpy arrays (embeddings).
    """
    if model is None:
        model = load_model()
    embeddings = model.encode(chunks, convert_to_numpy=True)
    return embeddings
