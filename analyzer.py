"""
Python Code Analyzer with RAG - CLI Entry Point

This module serves as the command-line interface and orchestrator for the
legacy code modernization platform. It delegates to core modules for analysis
and RAG services.

Architecture:
- core.ast_parser: AST-based code analysis
- rag.*: Semantic search and retrieval
- output: Legacy compatibility wrapper
"""

import json
import sys
import argparse
from pathlib import Path

# Configure logging and config (one-time at startup)
from utils.logger import Logger, get_logger
from utils.config import Config

# Import core analysis modules
from core.ast_parser import SafeParser
from core.models import EntityType

# Import RAG modules
from rag.chunker import create_chunks
from rag.embeddings import generate_embeddings, load_model
from rag.faiss_index import build_and_save_index
from rag.pipeline import rag_query

# Import legacy output modules (for backward compatibility)
from output import save_json, print_summary

# Initialize logging
Logger.initialize(log_level=Config.log_level(), log_file=Config.log_file())
logger = get_logger(__name__)

# Initialize configuration
Config.initialize()


def analyze_file(file_path: str) -> dict:
    """
    Parse a Python file and extract code structure.

    This function now delegates to core.ast_parser.SafeParser for analysis
    and converts results to the legacy format for backward compatibility.

    Args:
        file_path: Path to the Python file to analyze

    Returns:
        Dictionary with keys: functions, classes, imports, relationships
        (maintains legacy format for compatibility with output.py)
    """
    logger.info(f"Starting analysis of file: {file_path}")
    
    # Use the new SafeParser from core.ast_parser
    file_analysis = SafeParser.parse_file(file_path)
    
    if file_analysis.errors:
        logger.warning(f"Errors during analysis: {file_analysis.errors}")
        print(f"✗ Analysis errors: {file_analysis.errors}")
        sys.exit(1)
    
    # Convert new format to legacy format for backward compatibility
    logger.debug(f"Converting to legacy format")
    legacy_result = _convert_to_legacy_format(file_analysis)
    
    return legacy_result


def index_file(file_path: str) -> None:
    """
    Index a Python file for RAG: analyze, chunk, embed, and save to FAISS.

    Steps:
    1. Analyze file using core.ast_parser
    2. Create semantic chunks from the analysis
    3. Generate embeddings for each chunk
    4. Build and save FAISS index

    Args:
        file_path: Path to the Python file to index
    """
    logger.info(f"Starting indexing of file: {file_path}")
    print(f"\n✓ Starting indexing of file: {file_path}")
    
    try:
        print(f"  → Step 1: Analyzing file...")
        result = analyze_file(file_path)
        logger.debug(f"Analysis produced {len(result.get('functions', []))} functions")
        print(f"  ✓ Analysis complete")
        
        print(f"  → Step 2: Creating chunks...")
        chunks = create_chunks(result)
        logger.info(f"Created {len(chunks)} semantic chunks")
        print(f"  ✓ Created {len(chunks)} chunks")
        
        print(f"  → Step 3: Loading embedding model...")
        model = load_model()
        logger.info(f"Embedding model loaded: {Config.embedding_model()}")
        print(f"  ✓ Model loaded successfully")
        
        print(f"  → Step 4: Generating embeddings...")
        embeddings = generate_embeddings(chunks, model)
        logger.debug(f"Generated {len(embeddings)} embeddings")
        print(f"  ✓ Generated embeddings for {len(embeddings)} chunks")
        
        print(f"  → Step 5: Building FAISS index...")
        build_and_save_index(chunks, embeddings)
        logger.info(f"FAISS index saved to {Config.faiss_index_path()}")
        print(f"  ✓ FAISS index built and saved")
        
        print(f"\n✓ Indexing complete! Indexed {len(chunks)} chunks for {file_path}")
        logger.info(f"Indexing complete for {file_path}")
    
    except Exception as e:
        logger.error(f"Indexing failed: {e}", exc_info=True)
        print(f"✗ Indexing failed: {e}")
        sys.exit(1)

def query_codebase(query: str) -> None:
    """
    Query the indexed codebase using RAG.

    Retrieves semantically relevant code chunks and generates an answer
    using the configured LLM provider.

    Args:
        query: Natural language query about the codebase
    """
    logger.info(f"Processing query: {query}")
    print(f"\n✓ Starting query: '{query}'")
    
    try:
        print(f"  → Retrieving relevant context...")
        answer = rag_query(query)
        logger.debug(f"RAG query returned answer of length {len(answer)}")
        print(f"  ✓ Query processed")
        
        print(f"\nQuery: {query}")
        print(f"Answer: {answer}")
    
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        print(f"✗ Query failed: {e}")
        sys.exit(1)

def _convert_to_legacy_format(file_analysis) -> dict:
    """
    Convert FileAnalysis (new format) to legacy dict format.

    This maintains backward compatibility with output.py and existing code.
    
    Legacy format:
    {
        "functions": [{"name": "func_name", "line": 42}, ...],
        "classes": [{"name": "class_name", "line": 10}, ...],
        "imports": ["module_name", ...],
        "relationships": {"func_a": ["func_b", "func_c"], ...}
    }

    Args:
        file_analysis: FileAnalysis object from core.ast_parser

    Returns:
        Dictionary in legacy format
    """
    # Extract functions
    functions = [
        {"name": f.name, "line": f.location.line_start}
        for f in file_analysis.functions
    ]
    
    # Extract classes
    classes = [
        {"name": c.name, "line": c.location.line_start}
        for c in file_analysis.classes
    ]
    
    # Extract imports
    imports = [
        imp.module for imp in file_analysis.imports
        if imp.module  # Filter out empty module names
    ]
    
    # Convert relationships to legacy format: {source: [targets]}
    relationships = {}
    for rel in file_analysis.relationships:
        if rel.source not in relationships:
            relationships[rel.source] = []
        relationships[rel.source].append(rel.target)
    
    return {
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "relationships": relationships,
    }


def main():
    """
    Command-line interface for the Python Code Analyzer.

    Supports three commands:
    - analyze: Extract code structure from a Python file
    - index: Build FAISS index for RAG queries
    - query: Query the indexed codebase using natural language
    """
    parser = argparse.ArgumentParser(
        description="Legacy Code Modernization Platform - Code Analysis CLI"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to Python file to analyze"
    )
    parser.add_argument(
        "--command",
        choices=["analyze", "index", "query"],
        help="Command to run (default: analyze if file provided)"
    )
    parser.add_argument(
        "--query",
        help="Query string for 'query' command"
    )

    args = parser.parse_args()

    # Default behavior: if only a file is provided, analyze it
    if args.file and not args.command:
        args.command = "analyze"
    elif not args.file and not args.command:
        parser.print_help()
        return

    try:
        if args.command == "analyze":
            logger.info(f"Running 'analyze' command on {args.file}")
            print("=" * 60)
            print("PYTHON CODE ANALYSIS REPORT")
            print("=" * 60)
            result = analyze_file(args.file)
            save_json(result, filename="result.json")
            print("\n✓ Analysis complete!")
            print("\n" + "=" * 60)
            print("DETAILED ANALYSIS OUTPUT")
            print("=" * 60)
            print(json.dumps(result, indent=2))
            print("\n" + "=" * 60)
            print("ANALYSIS SUMMARY")
            print("=" * 60)
            print_summary(result)
            print("=" * 60)
        
        elif args.command == "index":
            logger.info(f"Running 'index' command on {args.file}")
            index_file(args.file)
        
        elif args.command == "query":
            logger.info(f"Running 'query' command: {args.query}")
            if not args.query:
                print("✗ --query argument is required for 'query' command")
                sys.exit(1)
            query_codebase(args.query)
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
        print("\n✗ Program interrupted")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
