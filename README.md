# Legacy Code Modernization Platform

An AI-assisted, domain-aware Python code intelligence and modernization platform. Specializes in analyzing ERPNext Accounts modules with semantic understanding of accounting workflows, enabling intelligent legacy code assessment and Python-to-Go migration planning.

**Current Status**: Phase 1 ✅ (Core Architecture) | Phase 2 ✅ (Semantic Analysis) | Phase 3+ 🚀 (AI Analysis & FastAPI)

---

## 🎯 Project Overview

### Purpose
This project helps teams **understand, document, and modernize legacy Python codebases**. Instead of manually reading through thousands of lines of code, you can:
- Extract comprehensive code structure (functions, classes, imports, methods)
- Identify function call relationships and architectural dependencies
- Build semantic search indices for intelligent querying
- Query codebases using natural language questions
- Generate AI-powered refactoring and modernization suggestions

### Problem Solved
When working with unfamiliar or large legacy Python codebases, development teams face:
- **Architectural Blindness**: Not understanding the overall system design
- **Hidden Dependencies**: Circular imports, tight coupling, monolithic structures
- **Refactoring Risk**: Can't safely extract services without breaking everything
- **Knowledge Loss**: Code understanding locked in team members' heads
- **Modernization Barriers**: Can't migrate to microservices without understanding architecture

This tool automates architectural analysis using **AST-based code extraction** and **Retrieval-Augmented Generation (RAG)**.

---

## 🧠 Semantic Analysis & Domain Intelligence

### ERPNext Accounts Module Focus
This platform specializes in analyzing **ERPNext Accounts modules**, providing domain-aware intelligence for accounting systems. Unlike generic code analyzers, it understands:

- **Accounting Concepts**: Ledger, journal entries, payments, taxes, reconciliation
- **Business Workflows**: Journal Entry → Ledger Posting → Trial Balance patterns
- **Legacy Modernization**: Python-to-Go migration planning with business context

### Key Differentiators
- **Domain Tagging**: Automatically classifies code into accounting concepts (ledger, payment, tax, etc.)
- **Workflow Detection**: Identifies business process patterns and dependencies
- **Quality Scoring**: Prioritizes modernization efforts based on code quality and business impact
- **Semantic Querying**: Natural language search with accounting domain awareness

### Why This Matters for Legacy Modernization
Traditional code analysis shows "what" the code does. This platform explains "why" - connecting technical implementation to business processes, enabling:
- **Informed Migration Decisions**: Prioritize which modules to migrate first
- **Service Boundary Identification**: Use business workflows to define microservice boundaries
- **Risk Assessment**: Understand business impact of refactoring decisions
- **Knowledge Preservation**: Document business logic alongside technical architecture

---

## ✨ Features

### Current (Phase 1 ✅)
- **Code Analysis**: Extracts functions, classes, methods, imports with metadata
- **AST-Based Parsing**: Accurate syntax tree analysis (no regex hacks)
- **Relationship Detection**: Identifies function calls, inheritance, imports
- **Structured Logging**: Context-aware logging throughout the stack
- **Configuration Management**: Environment-based configuration with .env support
- **Clean Architecture**: Layered, testable, extensible codebase
- **RAG Pipeline**: Query codebase using natural language
- **FAISS Indexing**: Fast semantic search for code discovery
- **JSON Reports**: Structured analysis results for programmatic access
- **Web UI**: Streamlit dashboard for interactive querying

### Current (Phase 2 ✅ - Semantic Analysis)
- **Domain Tagging**: Rule-based classification of accounting concepts (ledger, journal_entry, payment, tax)
- **Workflow Detection**: Identifies business process patterns (Journal Entry → Ledger Posting)
- **Context Scoring**: Quality assessment for modernization prioritization (HIGH/MEDIUM/LOW)
- **Semantic Indexing**: Unified index combining domain knowledge, workflows, and quality scores
- **Semantic Querying**: Domain-aware search with natural language queries

### Coming Soon (Phase 3+)
- **Coupling Analysis**: Detect tightly-coupled modules
- **Refactoring Suggestions**: AI-powered modernization recommendations
- **Service Extraction**: Monolith → microservices recommendations
- **Architecture Explanations**: Human-friendly system architecture explanations
- **FastAPI Backend**: REST API for integration with external tools
- **Dependency Graphs**: Visualize code dependencies and architecture
- **Multi-file Analysis**: Cross-file relationships and impact analysis

---

## 🏗️ Architecture (Phase 1)

The codebase follows **clean architecture** principles with clear separation of concerns:

```
CLI Layer (analyzer.py)
    ↓ delegates to
Core Analysis (core/*.py)
    ├─ ast_parser.py: AST-based code extraction
    ├─ models.py: Type-safe data models
    ↓ uses
Utilities (utils/*.py)
    ├─ logger.py: Structured logging
    ├─ config.py: Configuration management
    ↓ integrates with
RAG Pipeline (rag/*.py)
    └─ embeddings, faiss, retrieval
```

### Core Modules

#### **core/ast_parser.py** (AST Analysis)
Extracts code structure using Python's AST module:
- `SafeParser`: Safe entry point with error handling
- `EntityExtractor`: Finds functions, classes, methods, imports
- `RelationshipExtractor`: Detects calls, inheritance, imports
- Produces type-safe `FileAnalysis` objects

#### **core/models.py** (Data Models)
Immutable dataclasses representing code entities:
- `Entity`: Base class for all code components
- `Function`: Function/method with metadata
- `Class`: Class with methods and inheritance
- `Import`: Import statement tracking
- `Location`: File location (file, line, column)
- `Relationship`: Entity-to-entity relationships
- `FileAnalysis`: Results from single file analysis
- `ProjectAnalysis`: Project-wide analysis results

#### **utils/logger.py** (Structured Logging)
Context-aware logging throughout the stack:
- `Logger`: Singleton logger with context injection
- `StructuredFormatter`: Log formatter with context metadata
- `get_logger(name)`: Module-level logger convenience function
- Temporary context management via context manager

#### **utils/config.py** (Configuration Management)
Environment-based configuration without hardcoding:
- `Config`: Static configuration class
- Supports environment variables, .env file, and defaults
- Grouped settings: Logging, RAG, Analysis, LLM, API
- Validation and diagnostic methods

#### **analyzer.py** (CLI Entry Point - Refactored)
Command-line interface delegating to core modules:
- `analyze_file()`: Uses SafeParser for analysis
- `index_file()`: Builds FAISS index for RAG
- `query_codebase()`: Queries indexed codebase
- `_convert_to_legacy_format()`: Backward compatibility layer

#### **rag/*** (Unchanged - RAG Subsystem)
Retrieval-Augmented Generation pipeline:
- `chunker.py`: Converts analysis to queryable chunks
- `embeddings.py`: Generates semantic embeddings
- `faiss_index.py`: FAISS index management
- `retriever.py`: Semantic similarity search
- `llm_interface.py`: Answer generation
- `pipeline.py`: RAG orchestration

### Supporting Modules

#### **extractor.py** (Backward Compatibility)
Legacy module - now wraps core/ast_parser

#### **relationships.py** (Backward Compatibility)
Legacy module - now wrapped by core/ast_parser

#### **output.py** (Backward Compatibility)
JSON saving and console display - unchanged

---

## 📂 Project Structure

```
d:\Python_code_analyser/
├── core/                    ← NEW: Core analysis engine
│   ├── __init__.py
│   ├── ast_parser.py        (SafeParser, EntityExtractor, RelationshipExtractor)
│   ├── models.py            (Entity, Function, Class, Import, FileAnalysis)
│   └── __pycache__/
│
├── utils/                   ← NEW: Cross-cutting utilities
│   ├── __init__.py
│   ├── logger.py            (Logger, get_logger, context management)
│   ├── config.py            (Config class, env var + .env support)
│   └── __pycache__/
│
├── interfaces/              ← NEW: Placeholder for Phase 2
│   ├── __init__.py
│   └── __pycache__/
│
├── services/                ← NEW: Placeholder for Phase 2
│   ├── __init__.py
│   └── __pycache__/
│
├── rag/                     ← EXISTING: RAG subsystem (unchanged)
│   ├── chunker.py
│   ├── embeddings.py
│   ├── faiss_index.py
│   ├── llm_interface.py
│   ├── pipeline.py
│   ├── retriever.py
│   ├── index.faiss          (FAISS index - preserved)
│   ├── chunks.pkl           (Code chunks - preserved)
│   └── qa_test.md
│
├── ui/                      ← EXISTING: Streamlit web UI (unchanged)
│   └── app.py
│
├── analyzer.py              ← REFACTORED: CLI wrapper (delegates to core/)
├── extractor.py             ← LEGACY: Backward compatibility wrapper
├── relationships.py         ← LEGACY: Backward compatibility wrapper
├── output.py                ← EXISTING: JSON output (unchanged)
├── sample.py                ← Test file
├── result.json              ← Analysis output (generated)
│
├── .env                     ← Custom configuration (optional)
├── .env.example             ← NEW: Configuration template
├── requirements.txt         ← Python dependencies
├── README.md                ← This file
├── PHASE_1_COMPLETION.md    ← NEW: Phase 1 detailed summary
├── QUICK_REFERENCE.md       ← NEW: Quick reference guide
└── LICENSE
```

---

## 🔄 Data Flow

```
Python File
    ↓
[analyzer.py delegates to core/ast_parser.py]
    ↓
SafeParser.parse_file()
    ├─ Pass 1: EntityExtractor → Functions, Classes, Imports
    ├─ Pass 2: RelationshipExtractor → Calls, Inheritance
    ↓
FileAnalysis (typed, immutable)
    ├─ entities, relationships, errors
    ↓
[For Analysis Mode]
    ├─ Convert to legacy format
    └─ Save JSON → result.json
    
[For Indexing Mode]
    ├─ Create chunks (rag/chunker.py)
    ├─ Generate embeddings (rag/embeddings.py)
    ├─ Build FAISS index (rag/faiss_index.py)
    └─ Save → index.faiss + chunks.pkl
    
[For Query Mode]
    ├─ Load FAISS index
    ├─ Search for similar chunks
    ├─ Generate answer (rag/llm_interface.py)
    └─ Return results
```

## 📋 Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- pip or conda

### Installation

1. **Clone or download the repository**
   ```bash
   cd d:\Python_code_analyser
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Optional: Create .env file for custom configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### Dependencies
See `requirements.txt` for the complete list. Key packages:
- `sentence-transformers`: Semantic embeddings
- `faiss-cpu`: Vector similarity search
- `streamlit`: Web UI
- `networkx`: Graph analysis (Phase 2+)

## 🚀 Quick Start

### 1. Analyze a Python File (Default)

Extract code structure from any Python file:

```bash
python analyzer.py sample.py
```

**Output:**
- Console: Detailed analysis summary (functions, classes, imports, relationships)
- File: `result.json` with structured analysis data

**Configuration:**
Uses structured logging and configuration from `utils/config.py`. Override with environment variables or `.env` file.

### 2. Index for RAG (Semantic Search)

Build a FAISS index for intelligent code querying:

```bash
python analyzer.py sample.py --command index
```

**Steps:**
1. Analyzes the file (AST extraction)
2. Creates semantic chunks from code structure
3. Generates embeddings using Sentence Transformers
4. Builds and saves FAISS index
5. Saves chunks metadata

**Output:**
- `rag/index.faiss`: FAISS vector index
- `rag/chunks.pkl`: Code chunks metadata

### 3. Query via CLI

Search the indexed codebase using natural language:

```bash
python analyzer.py --command query --query "What functions handle data loading?"
```

**Process:**
1. Converts your question to embeddings
2. Searches FAISS index for similar code chunks
3. Retrieves matching functions/classes/imports
4. Generates comprehensive answer

### 4. Query via Web UI (Streamlit)

Launch interactive web interface:

```bash
streamlit run ui/app.py
```

**Features:**
- Browser-based interface
- Real-time query input
- Automatic index detection
- Setup guidance

### 5. Semantic Analysis (Phase 2)

Perform domain-aware analysis and querying for accounting systems:

**Build Semantic Index:**
```bash
python analyzer.py /path/to/erpnext --command analyze_semantic
```

**Query Semantic Index:**
```bash
python analyzer.py --command query_semantic --query "ledger posting functions" --index project_semantic.json
```

**Example Queries:**
- "journal entry validation"
- "trial balance calculation"
- "payment reconciliation"
- "tax processing functions"

**Features:**
- Domain tagging of accounting concepts (ledger, journal_entry, payment, tax)
- Workflow detection (Journal Entry → Ledger Posting patterns)
- Quality scoring for modernization prioritization (HIGH/MEDIUM/LOW)
- Semantic search with relevance ranking and explanations

### Example Semantic Query Output
```bash
$ python analyzer.py --command query_semantic --query "ledger posting functions" --index project_semantic.json

Query Results:
1. make_ledger_entry (ledger_entry.py:45)
   Relevance: 0.92 | Quality: HIGH | Domain: ledger
   Reason: Matches query terms: ledger, posting | Identified as accounting-related code

2. update_ledger_balance (ledger.py:123)
   Relevance: 0.88 | Quality: HIGH | Domain: ledger
   Reason: Matches query terms: ledger | High-quality, well-documented code

3. post_journal_to_ledger (journal.py:78)
   Relevance: 0.85 | Quality: MEDIUM | Domain: journal_entry, ledger
   Reason: Matches query terms: posting, ledger | Workflow: Journal Entry → Ledger Posting
```

---

## 📚 Documentation

- **[PHASE_1_COMPLETION.md](./PHASE_1_COMPLETION.md)**: Detailed Phase 1 architecture & changes
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)**: Quick reference for common tasks
- **[.env.example](./.env.example)**: Configuration options with explanations

---

## 🛠️ Configuration

### Environment Variables

All configuration can be set via environment variables or `.env` file. See `.env.example` for all options.

**Common settings:**
```bash
# Logging
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=./logs/app.log         # Optional file logging

# Embedding & RAG
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
FAISS_INDEX_PATH=./rag/index.faiss

# LLM Provider
LLM_PROVIDER=dummy              # dummy (default), openai, local
# OPENAI_API_KEY=sk-...         # If using OpenAI
# OPENAI_MODEL=gpt-3.5-turbo
```

### Programmatic Configuration

```python
from utils.config import Config

Config.initialize()
log_level = Config.log_level()
faiss_path = Config.faiss_index_path()

# Validate configuration
is_valid, warnings = Config.validate()
for warning in warnings:
    print(f"⚠️ {warning}")
```

---

## 📊 Example Output

### Analysis Output (JSON)
```json
{
  "functions": [
    {"name": "load_data", "line": 1},
    {"name": "process_data", "line": 11}
  ],
  "classes": [
    {"name": "Analyzer", "line": 14}
  ],
  "imports": [],
  "relationships": {
    "process_data": ["load_data"],
    "Analyzer.run": ["process_data"]
  }
}
```

### Console Output (Analysis)
```
============================================================
ANALYSIS SUMMARY
============================================================

📊 CODE ANALYSIS SUMMARY

Functions:
  - load_data (line 1)
  - process_data (line 11)

Classes:
  - Analyzer (line 14)

Function Calls:
  process_data → load_data
  Analyzer.run → process_data
```

---

## 🎓 Use Cases

### 1. **Legacy Code Assessment**
Quickly understand the structure of inherited codebases:
```bash
python analyzer.py large_legacy_app.py > architecture_report.txt
```

### 2. **Refactoring Planning**
Identify tightly-coupled modules before extracting services:
```bash
python analyzer.py monolith.py --command index
python analyzer.py --command query --query "Which functions are called most frequently?"
```

### 3. **Knowledge Transfer**
Document code architecture for new team members:
```bash
python analyzer.py app.py > team_docs/architecture.json
streamlit run ui/app.py  # Interactive exploration
```

### 4. **Microservices Migration** (Phase 2+)
Get AI-powered recommendations for service extraction:
```bash
python analyzer.py monolith.py --command refactor
# Returns: Suggested microservices, domain boundaries, API contracts
```

---

## 🔮 Roadmap

### Phase 1: ✅ Core Architecture (COMPLETE)
- [x] Clean layered architecture
- [x] AST-based code analysis
- [x] Structured logging & configuration
- [x] Backward compatibility maintained
- [x] Type-safe data models

### Phase 2: ✅ Semantic Analysis (COMPLETE)
- [x] Domain tagging of accounting concepts
- [x] Workflow detection (business process patterns)
- [x] Context scoring for modernization prioritization
- [x] Semantic indexing and querying
- [x] Domain-aware search with relevance ranking

### Phase 3: 🚀 AI Analysis (In Progress)
- [ ] High-coupling module detection
- [ ] Refactoring opportunity suggestions
- [ ] Service extraction recommendations
- [ ] Circular dependency detection
- [ ] Architecture explanation generation

### Phase 4: 🚀 FastAPI Backend
- [ ] REST API endpoints
- [ ] Authentication & authorization
- [ ] Integration with CI/CD pipelines
- [ ] Analysis result caching
- [ ] Batch processing

### Phase 5: 🚀 Advanced UI
- [ ] Dependency graph visualization
- [ ] Interactive architecture diagram
- [ ] Refactoring impact analysis
- [ ] Team collaboration features

### Phase 6: 🚀 Enterprise Features
- [ ] Multi-language support (Java, C#, Go, etc.)
- [ ] Custom analysis rules
- [ ] Integration with code review tools
- [ ] Automated modernization reports
- [ ] Docker containerization

---

## 🤝 Contributing

We welcome contributions! Areas of interest:

### Code Quality
- [ ] Unit tests for all modules
- [ ] Integration tests
- [ ] Performance benchmarks

### Features
- [ ] Additional chunking strategies
- [ ] Support for more LLM providers
- [ ] Enhanced visualization options
- [ ] Language-specific analysis rules

### Documentation
- [ ] API documentation
- [ ] Video tutorials
- [ ] Architecture decision records (ADRs)

See [PHASE_1_COMPLETION.md](./PHASE_1_COMPLETION.md) for detailed architecture and [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) for development guide.

---

## 💡 Tips & Tricks

### Analyzing Large Files
```bash
# Skip large files to avoid memory issues
export MAX_FILE_SIZE_MB=50
python analyzer.py huge_file.py
```

### Custom Logging
```bash
export LOG_LEVEL=DEBUG
export LOG_FILE=analysis.log
python analyzer.py sample.py
# Logs to console AND analysis.log
```

### Using Different Embedding Models
```bash
# Faster, smaller model
export EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# More accurate, larger model
export EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
```

---

## 📞 Support & Feedback

- 📖 **Documentation**: See [PHASE_1_COMPLETION.md](./PHASE_1_COMPLETION.md) and [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
- 💬 **Questions**: Check existing issues or create a new one
- 🐛 **Bug Reports**: Please include Python version, error message, and reproduction steps
- 📚 **Feature Requests**: Describe the use case and expected behavior

---

## 📄 License

This project is open source and available under the MIT License. See [LICENSE](./LICENSE) for details.

---

## 🎯 Vision

The **Legacy Code Modernization Platform** aims to become the industry standard for:
- Understanding complex legacy codebases
- Planning safe refactoring and modernization
- Automating knowledge transfer between teams
- Guiding monolith-to-microservices migrations
- Supporting enterprise code quality improvements

**Current Status**: Phase 1 ✅ Complete  
**Next Goals**: Phase 2 (AI Analysis) → Phase 3 (FastAPI) → Phase 4 (Advanced UI)

---

Made with ❤️ for developers who inherit legacy code.  
*"Understanding code is the first step to improving it."*