# Python Code Analyser with RAG

A powerful utility that parses Python source files to extract functions, classes, imports, and function-call relationships using the AST module. It also provides Retrieval-Augmented Generation (RAG) capabilities with FAISS indexing and semantic search for intelligent code querying.

---

## 🔧 Features

- **Code Analysis**: Extracts function and class definitions with line numbers
- **Relationship Detection**: Identifies which functions call which other functions
- **Import Tracking**: Collects all imports used in the file
- **Semantic Embeddings**: Generates embeddings for code chunks using Sentence Transformers
- **FAISS Indexing**: Creates a fast similarity search index for code retrieval
- **RAG Pipeline**: Query your codebase using natural language and get relevant code snippets
- **Detailed Progress Tracking**: Console messages showing which steps work properly
- **JSON Reports**: Saves structured analysis results to JSON files

---

## 📋 Requirements

- Python 3.10+ (tested on Python 3.14)
- Dependencies: `sentence-transformers`, `huggingface-hub`, `faiss-cpu`, `numpy`

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

### 1. Analyze a Python File (Default)

Simply pass a Python file to analyze it:

```bash
python analyzer.py sample.py
```

This will:
- Display detailed progress messages for each analysis step
- Extract functions, classes, imports, and relationships
- Save the JSON report to `result.json`
- Print a human-friendly summary to the console

### 2. Index a File for RAG

Build a semantic search index for intelligent querying:

```bash
python analyzer.py --command index --file sample.py
```

This will:
- Analyze the file
- Convert code into chunks
- Generate embeddings for each chunk
- Build and save a FAISS index

### 3. Query the Indexed Codebase

Search your indexed code using natural language:

```bash
python analyzer.py --command query --query "what functions handle data processing"
```

---

## 📊 Output Format

The JSON output (`result.json`) follows this structure:

```json
{
  "functions": [
    { "name": "load_data", "line": 1 },
    { "name": "process_data", "line": 4 }
  ],
  "classes": [
    { "name": "Analyzer", "line": 7 }
  ],
  "imports": [
    "os", "sys"
  ],
  "relationships": {
    "process_data": ["load_data"],
    "run": ["process_data"]
  }
}
```

---

## 📁 Project Structure

```
Python_code_analyser/
├── analyzer.py           # Main entry point
├── extractor.py          # AST-based entity extraction
├── relationships.py      # Function call relationship detection
├── output.py             # JSON output and terminal display
├── rag/
│   ├── chunker.py        # Code chunking for embeddings
│   ├── embeddings.py     # Embedding generation
│   ├── faiss_index.py    # FAISS index creation and management
│   ├── llm_interface.py  # LLM integration
│   ├── pipeline.py       # RAG pipeline orchestration
│   └── retriever.py      # Semantic retrieval from FAISS
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

---

## 🤝 Contributing

Contributions are welcome! Typical improvements:
- Add unit tests for all modules
- Add CLI flags for custom output paths
- Add support for batch file/directory scanning
- Enhance RAG with more sophisticated chunking strategies
- Add support for multi-file analysis with cross-file relationships

Please open an issue or submit a pull request.

---

## 💡 Next Steps

- Add linters and tests to CI/CD pipeline
- Expand analysis to include class methods and attributes
- Support for tracking import usage
- Add visualization of code relationships
- Implement caching for FAISS indexes

---

Made with ❤️ by the code analyser project.