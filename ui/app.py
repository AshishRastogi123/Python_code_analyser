import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from rag.pipeline import run_query
from analyzer import index_file

st.title("Python Code Analyzer (RAG)")

# Check if FAISS index exists
index_path = "rag/index.faiss"
chunks_path = "rag/chunks.pkl"
index_exists = os.path.exists(index_path) and os.path.exists(chunks_path)

if not index_exists:
    st.warning("⚠️ FAISS index not found. Please index a Python file first.")
    st.info("**Steps to get started:**")
    st.markdown("""
    1. Open a terminal in the project directory
    2. Run the indexing command:
       ```bash
       python analyzer.py <path_to_python_file> --command index
       ```
    3. For example:
       ```bash
       python analyzer.py sample.py --command index
       ```
    4. Refresh this page after indexing is complete
    """)
    st.stop()

st.success("✓ FAISS index loaded successfully!")

question = st.text_input("Ask about the codebase")

if st.button("Analyze"):
    if not question.strip():
        st.warning("Please enter a question")
    else:
        try:
            with st.spinner("Searching codebase..."):
                answer = run_query(question)
            st.success("Answer found!")
            st.write(answer)
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
