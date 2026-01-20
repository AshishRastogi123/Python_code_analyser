# Python Code Analyser with RAG

A powerful utility that parses Python source files to extract functions, classes, imports, and function-call relationships using the AST module. It also provides Retrieval-Augmented Generation (RAG) capabilities with FAISS indexing and semantic search for intelligent code querying.

---

## � Project Overview

### Purpose
This project solves the problem of **understanding and querying large Python codebases**. Instead of manually reading through code files, you can:
- Automatically extract code structure (functions, classes, imports)
- Identify function call relationships and dependencies
- Build a semantic search index for natural language queries
- Query the codebase using plain English questions

### Problem Solved
When working with unfamiliar or large Python codebases, developers face challenges:
- Understanding the overall structure and architecture
- Tracking which functions call which other functions
- Finding specific code components quickly
- Documenting relationships between code entities

This tool automates these tasks using **AST analysis** and **RAG (Retrieval-Augmented Generation)**.

---

## 🔧 Features

- **Code Analysis**: Extracts function and class definitions with line numbers and docstrings
- **Relationship Detection**: Identifies which functions call which other functions
- **Import Tracking**: Collects all imports used in the file
- **Semantic Embeddings**: Generates embeddings for code chunks using Sentence Transformers
- **FAISS Indexing**: Creates a fast similarity search index for code retrieval
- **RAG Pipeline**: Query your codebase using natural language and get relevant code snippets
- **Detailed Progress Tracking**: Console messages showing which steps work properly
- **JSON Reports**: Saves structured analysis results to JSON files
- **Web UI**: Interactive Streamlit interface for querying your indexed codebase

---

## 🏗️ Project Architecture

### Core Modules

#### **analyzer.py** (Entry Point)
Main module that orchestrates the entire workflow:
- `analyze_file()`: Parses a Python file using AST, extracts entities and relationships
- `index_file()`: Builds a complete semantic search index for a file
- `query_codebase()`: Queries the indexed codebase using RAG
- CLI interface with commands: `analyze`, `index`, `query`

#### **extractor.py** (Code Extraction)
`CodeExtractor` class (AST visitor) that extracts:
- **Functions**: Name, line number, docstring
- **Classes**: Name, line number, docstring
- **Imports**: Both `import x` and `from x import y` statements

#### **relationships.py** (Dependency Analysis)
`RelationshipAnalyzer` class that maps function call relationships:
- Tracks which function is currently being analyzed
- Records direct function calls: `foo()`
- Records method calls: `obj.foo()`
- Returns a dictionary: `{function_name: [callees]}`

#### **output.py** (Reporting)
Handles results presentation:
- `save_json()`: Saves analysis to JSON file
- `print_summary()`: Displays human-readable analysis summary with function calls and class definitions

### RAG Subsystem (rag/ directory)

#### **chunker.py** (Text Chunking)
Converts analysis results into queryable text chunks:
- Creates chunks for imports
- Creates chunks for each function (including its callees)
- Creates chunks for each class

#### **embeddings.py** (Semantic Embeddings)
Generates vector embeddings for code chunks:
- Uses Sentence Transformers (`sentence-transformers` library)
- Converts text chunks into dense vector representations
- Enables semantic similarity search

#### **faiss_index.py** (Vector Index)
Manages FAISS (Facebook AI Similarity Search) index:
- `build_and_save_index()`: Creates normalized FAISS index and persists to disk
- `load_index()`: Loads pre-built index from disk
- Stores both embeddings (index.faiss) and chunks metadata (chunks.pkl)

#### **retriever.py** (Similarity Search)
Retrieves relevant code chunks based on query:
- Loads FAISS index and chunks
- Converts query to embeddings
- Returns top-k most similar chunks using cosine similarity

#### **llm_interface.py** (Answer Generation)
Generates final answer from retrieved context:
- `DummyLLM`: Default LLM interface (can be extended for real LLMs)
- Takes query and retrieved context as input
- Generates comprehensive answers

#### **pipeline.py** (RAG Orchestration)
Combines retrieval and generation:
- `rag_query()`: Main RAG function combining retrieval + generation
- `run_query()`: Convenient alias for `rag_query()`

### UI Subsystem (ui/ directory)

#### **app.py** (Streamlit Web Interface)
Interactive web application for code analysis:
- Checks if FAISS index exists
- Provides guided setup instructions
- Accepts natural language questions
- Displays results with search confirmation

---

## 📋 Requirements

- Python 3.10+ (tested on Python 3.14)
- Dependencies: `sentence-transformers`, `huggingface-hub`, `faiss-cpu`, `numpy`, `streamlit`

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
python analyzer.py sample.py --command index
```

This will:
- Analyze the file
- Convert code into chunks
- Generate embeddings for each chunk using Sentence Transformers
- Build and save a FAISS index (index.faiss) and chunks metadata (chunks.pkl)

### 3. Query the Indexed Codebase (CLI)

Search your indexed code using natural language:

```bash
python analyzer.py --command query --query "what functions handle data processing"
```

**Workflow:**
1. Converts your query into embeddings
2. Searches FAISS index for top-k similar code chunks
3. Retrieves matching functions/classes/imports
4. Generates a comprehensive answer

### 4. Use the Web Interface (Streamlit)

Launch an interactive web UI for querying:

```bash
streamlit run ui/app.py
```

**Features:**
- ✓ User-friendly interface for natural language queries
- ✓ Automatic FAISS index detection
- ✓ Step-by-step setup guidance
- ✓ Real-time query results

---

## 🔄 Workflow Example

```bash
# Step 1: Index your Python file
python analyzer.py sample.py --command index
# Output: Created embeddings and FAISS index

# Step 2a: Query via CLI
python analyzer.py --command query --query "What does the main function do?"

# Step 2b: Or use the Web UI
streamlit run ui/app.py
# Open browser and ask questions interactively
```

---

## 📊 Output Format

### JSON Report (result.json)
The analysis output follows this structure:

```json
{
  "functions": [
    { "name": "load_data", "line": 1, "docstring": "Loads data..." },
    { "name": "process_data", "line": 10, "docstring": "Processes..." }
  ],
  "classes": [
    { "name": "DataAnalyzer", "line": 20, "docstring": "Main analyzer..." }
  ],
  "imports": [
    "os", "sys", "pandas.DataFrame"
  ],
  "relationships": {
    "process_data": ["load_data", "validate"],
    "main": ["process_data", "output_results"]
  }
}
```

### RAG Query Output
When you query the indexed codebase, you receive:
- **Retrieved Chunks**: The most similar code snippets from the FAISS index
- **Generated Answer**: A comprehensive answer synthesizing the retrieved context

---

## 📁 Project Structure

```
Python_code_analyser/
├── analyzer.py              # Main CLI entry point
├── extractor.py             # AST-based entity extraction
├── relationships.py         # Function call relationship detection
├── output.py                # JSON saving and terminal display
├── sample.py                # Example Python file for testing
├── result.json              # Analysis output (generated)
├── requirements.txt         # Python dependencies
├── rag/                      # RAG (Retrieval-Augmented Generation) subsystem
│   ├── chunker.py           # Converts analysis to text chunks
│   ├── embeddings.py        # Generates vector embeddings
│   ├── faiss_index.py       # FAISS index creation/loading
│   ├── retriever.py         # Semantic search from FAISS
│   ├── llm_interface.py     # LLM answer generation
│   ├── pipeline.py          # RAG orchestration (retrieve + generate)
│   ├── index.faiss          # Persisted FAISS index (generated)
│   ├── chunks.pkl           # Persisted code chunks (generated)
│   └── qa_test.md           # Test documentation
├── ui/                       # Web interface
│   └── app.py               # Streamlit web application
└── README.md                # This file
```

---

## 🔄 Data Flow

```
Python File
    ↓
AST Parsing (analyzer.py)
    ↓
Extract Entities (extractor.py)
    ├─ Functions, Classes, Imports
    ↓
Extract Relationships (relationships.py)
    ├─ Function call mappings
    ↓
[For Analysis Mode]
    ↓
Save JSON (output.py)
    ↓
result.json
    
[For Indexing Mode]
    ↓
Create Chunks (chunker.py)
    ↓
Generate Embeddings (embeddings.py)
    ├─ Uses Sentence Transformers
    ↓
Build FAISS Index (faiss_index.py)
    ├─ Saves index.faiss + chunks.pkl
    ↓
[For Query Mode]
    ↓
Query → Embedding (embeddings.py)
    ↓
FAISS Search (retriever.py)
    ├─ Top-k similar chunks
    ↓
Generate Answer (llm_interface.py)
    ↓
Result
```

---

## 🤝 Contributing

Contributions are welcome! Typical improvements:
- Add unit tests for all modules
- Add CLI flags for custom output paths (--output, --chunk-size)
- Add support for batch file/directory scanning
- Enhance RAG with more sophisticated chunking strategies
- Add support for multi-file analysis with cross-file relationships
- Integrate with real LLMs (OpenAI, HuggingFace, etc.)
- Add metrics for embedding quality
- Export results to different formats (HTML, Markdown)

Please open an issue or submit a pull request.

---

## 💡 Future Enhancements

- [ ] Batch processing for multiple files
- [ ] Visualization of code dependency graphs
- [ ] Cross-file function tracking
- [ ] Integration with real LLMs (GPT, Claude, etc.)
- [ ] Support for other languages (Java, C++, Go)
- [ ] Performance benchmarks and optimization
- [ ] Advanced chunking strategies (by function, by logical blocks)
- [ ] Caching layer for FAISS indexes
- [ ] REST API for programmatic access
- [ ] Docker containerization for easy deployment

---

## 📄 License

This project is open source and available under the MIT License.

---

Made with ❤️ by the Python Code Analyzer project.