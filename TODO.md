# TODO: Enhance Python Code Analyzer with RAG System

## Steps to Complete

- [ ] Enhance extractor.py to extract docstrings for functions and classes
- [ ] Create rag/ folder structure
- [ ] Create rag/chunker.py: Convert JSON data into human-readable text chunks
- [ ] Create rag/embeddings.py: Generate embeddings using sentence-transformers (all-MiniLM-L6-v2)
- [ ] Create rag/faiss_index.py: Build and save FAISS index for embeddings
- [ ] Create rag/retriever.py: Retrieve top-k relevant chunks for a query
- [ ] Create rag/llm_interface.py: Abstract LLM interface (pluggable)
- [ ] Create rag/pipeline.py: RAG query pipeline (retrieve + generate answer)
- [ ] Create requirements.txt with new dependencies (sentence-transformers, faiss-cpu)
- [ ] Update analyzer.py to support subcommands via argparse ('analyze', 'index', 'query')
- [ ] Install new dependencies in virtual environment
- [ ] Test indexing and querying functionality
- [ ] Ensure clean separation between analyzer and RAG components
