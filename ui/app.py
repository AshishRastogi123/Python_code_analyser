import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.semantic_query import query_semantic_index
from core.semantic_index import SemanticIndexer
from analyzer import index_file

st.title("Python Code Analyzer (Semantic)")

# Check if semantic index exists
semantic_index_path = "Python_code_analyser_semantic.json"
semantic_index_exists = os.path.exists(semantic_index_path)

if not semantic_index_exists:
    st.warning("⚠️ Semantic index not found. Please analyze the project first.")
    st.info("**Steps to get started:**")
    st.markdown("""
    1. Open a terminal in the project directory
    2. Run the semantic analysis command:
       ```bash
       python analyzer.py <path_to_project> --command analyze_semantic
       ```
    3. For example:
       ```bash
       python analyzer.py . --command analyze_semantic
       ```
    4. Refresh this page after analysis is complete
    """)
    st.stop()

# Load semantic index
try:
    indexer = SemanticIndexer()
    semantic_index = indexer.load_index(semantic_index_path)
    st.success("✓ Semantic index loaded successfully!")
except Exception as e:
    st.error(f"Error loading semantic index: {str(e)}")
    st.stop()

question = st.text_input("Ask about the codebase")

if st.button("Analyze"):
    if not question.strip():
        st.warning("Please enter a question")
    else:
        try:
            with st.spinner("Searching codebase..."):
                results = query_semantic_index(question, semantic_index, max_results=10)
            st.success(f"Found {len(results)} relevant results!")

            if not results:
                st.info("No matching results found for your query.")
            else:
                for i, result in enumerate(results, 1):
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.subheader(f"{i}. {result.entity_name}")
                            st.write(f"📁 **File:** {result.file_path}")
                        with col2:
                            st.metric("Relevance", f"{result.relevance_score:.2f}")
                            st.metric("Quality", result.context_score)

                        if result.domain_tags:
                            st.write(f"🏷️ **Domain Tags:** {', '.join(result.domain_tags)}")

                        if result.short_context:
                            st.write(f"📝 **Context:** {result.short_context}")

                        if result.reasoning:
                            with st.expander("💡 Why this result?"):
                                for reason in result.reasoning:
                                    st.write(f"• {reason}")

                        st.divider()

        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
