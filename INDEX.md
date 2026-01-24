# Project Documentation Index

## 📚 Where to Start?

### For Quick Overview
Start here for a 5-minute understanding of what was done:
- **[README.md](./README.md)** — Main documentation with all features and usage examples
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** — Quick reference guide for common tasks

### For Detailed Architecture
Want to understand the architectural decisions and design patterns?
- **[PHASE_1_COMPLETION.md](./PHASE_1_COMPLETION.md)** — Complete Phase 1 breakdown with all implementation details

### For Configuration
How to customize the tool for your environment?
- **[.env.example](./.env.example)** — All configuration options with explanations

---

## 🗂️ Project Structure

```
d:\Python_code_analyser/
├── core/                    # NEW: Core analysis engine
│   ├── ast_parser.py       # AST parsing, 2-pass analysis
│   ├── models.py           # Type-safe data models
│   └── __init__.py
│
├── utils/                  # NEW: Utilities
│   ├── logger.py          # Structured logging
│   ├── config.py          # Configuration management
│   └── __init__.py
│
├── interfaces/            # NEW: Placeholder for Phase 2
├── services/              # NEW: Placeholder for Phase 2
├── rag/                   # EXISTING: RAG pipeline (unchanged)
├── ui/                    # EXISTING: Streamlit UI (unchanged)
│
├── analyzer.py            # REFACTORED: CLI wrapper
├── extractor.py           # LEGACY: Backward compat
├── relationships.py       # LEGACY: Backward compat
├── output.py              # EXISTING: Unchanged
│
├── README.md              # Main documentation
├── PHASE_1_COMPLETION.md  # Detailed Phase 1 report
├── QUICK_REFERENCE.md     # Quick reference
├── .env.example           # Configuration template
└── requirements.txt       # Dependencies
```

---

## 🚀 Quick Commands

### Analyze a file
```bash
python analyzer.py sample.py
```

### Index for RAG
```bash
python analyzer.py sample.py --command index
```

### Query the codebase
```bash
python analyzer.py --command query --query "What functions handle data loading?"
```

### Launch web UI
```bash
streamlit run ui/app.py
```

---

## ✨ What's New in Phase 1?

### Code Structure
- ✅ Clean layered architecture (CLI → Core → Utils)
- ✅ Separation of concerns (Analysis, Logging, Configuration)
- ✅ Type-safe data models (immutable dataclasses)
- ✅ Testable, reusable components

### Code Quality
- ✅ Structured logging with context injection
- ✅ Environment-based configuration (12-factor app)
- ✅ Comprehensive docstrings and comments
- ✅ Type hints throughout codebase

### Backward Compatibility
- ✅ All existing code still works
- ✅ FAISS index preserved
- ✅ CLI interface unchanged
- ✅ Output format compatible

---

## 📖 Module Guide

### core/ast_parser.py
Two-pass AST analysis extracting code structure:
- Pass 1: EntityExtractor → Functions, Classes, Imports
- Pass 2: RelationshipExtractor → Calls, Inheritance
- Entry point: `SafeParser.parse_file(path) → FileAnalysis`

### core/models.py
Type-safe immutable data models for all code entities:
- Entity hierarchy: Entity → Function/Class/Import
- Analysis results: FileAnalysis → ProjectAnalysis
- Serializable: to_dict() for JSON output

### utils/logger.py
Structured logging with context management:
- Singleton Logger with context injection
- Temporary context via context manager
- Console + file logging support

### utils/config.py
Configuration from environment variables and .env file:
- Grouped settings (Logging, RAG, Analysis, LLM, API)
- Validation and diagnostic methods
- Sensible defaults for all options

---

## 🔧 Configuration Options

See `.env.example` for complete list. Common ones:

```bash
LOG_LEVEL=INFO                              # DEBUG, INFO, WARNING, ERROR
LOG_FILE=./logs/app.log                     # Optional
EMBEDDING_MODEL=sentence-transformers/...  # Model name
LLM_PROVIDER=dummy                          # dummy, openai, local
FAISS_INDEX_PATH=./rag/index.faiss         # Index path
```

---

## 🎓 Architecture Decision Records

### Why Two-Pass AST Analysis?
Separates concerns: pass 1 extracts entities, pass 2 finds relationships. Enables independent testing and future enhancements.

### Why Immutable Dataclasses?
Ensures data integrity, enables caching, supports serialization, and prevents accidental mutations.

### Why Structured Logging?
Adds context to every log line (file, stage, operation) making debugging and monitoring easier. Integrates with external logging services.

### Why Configuration Class?
Centralizes all settings, supports environment variables + .env files, enables testing without file I/O, and follows 12-factor app methodology.

---

## 🚀 Next Steps

### For Users
1. Read [README.md](./README.md) for overview
2. Try analyzing a file: `python analyzer.py sample.py`
3. Index and query: `python analyzer.py sample.py --command index`
4. Launch UI: `streamlit run ui/app.py`

### For Developers
1. Review [PHASE_1_COMPLETION.md](./PHASE_1_COMPLETION.md) for architecture
2. Check [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) for development patterns
3. See core/models.py for data structures
4. See core/ast_parser.py for analysis implementation
5. See utils/logger.py and utils/config.py for utilities

### For Phase 2
Phase 2 will add AI-powered analysis modules:
- Coupling detection (tight coupling between modules)
- Refactoring suggestions (extract services, reduce dependencies)
- Architecture explanations (describe system design)

Ready to proceed when you are!

---

## ❓ FAQ

**Q: Will this break my existing code?**  
A: No, all existing functionality is preserved. The refactoring is internal.

**Q: Can I use this on large codebases?**  
A: Yes, with configuration: `MAX_FILE_SIZE_MB` controls file size limit.

**Q: How do I customize behavior?**  
A: Use environment variables or create `.env` file (copy `.env.example`).

**Q: Can I integrate this into my CI/CD pipeline?**  
A: Yes, use the `analyze` command which outputs JSON. Phase 4 will add FastAPI for REST API integration.

**Q: What if I find a bug?**  
A: Check the console output for detailed error messages. Enable `LOG_LEVEL=DEBUG` for more details.

---

Made with ❤️ for developers who work with legacy code.

*"Understanding code is the first step to improving it."*
