"""
Python Code Analyzer with RAG and Semantic Analysis - CLI Entry Point

This module serves as the command-line interface and orchestrator for the
legacy code modernization platform with domain-aware semantic analysis.

Architecture:
- core.ast_parser: AST-based code analysis
- core.project_analyzer: Project-wide analysis with semantic indexing
- core.semantic_query: Domain-aware querying
- rag.*: Semantic search and retrieval
"""

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent / ".env")

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
from core.project_analyzer import analyze_project, analyze_project_with_semantic
from core.semantic_index import SemanticIndexer
from core.semantic_query import query_semantic_index

# Import RAG modules (lazy loading to avoid dependency issues)
def _import_rag_modules():
    """Lazy import RAG modules to avoid dependency issues when not needed."""
    global create_chunks, generate_embeddings, load_model, build_and_save_index, rag_query
    if 'create_chunks' not in globals():
        from rag.chunker import create_chunks
        from rag.embeddings import generate_embeddings
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
    # Lazy import RAG modules
    _import_rag_modules()

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


def analyze_project_semantic(root_path: str) -> None:
    """
    Analyze entire project with semantic indexing for domain-aware insights.

    Steps:
    1. Analyze project structure and relationships
    2. Build semantic index with domain tagging
    3. Detect accounting workflows
    4. Score code quality and relevance
    5. Save semantic index

    Args:
        root_path: Root directory of the project to analyze
    """
    logger.info(f"Starting semantic project analysis: {root_path}")
    print(f"\n✓ Starting semantic analysis of project: {root_path}")

    try:
        print(f"  → Step 1: Analyzing project structure...")
        analysis, semantic_index = analyze_project_with_semantic(root_path)
        logger.info(f"Analyzed {len(analysis.file_analyses)} files")
        print(f"  ✓ Project structure analyzed")

        print(f"  → Step 2: Building semantic index...")
        logger.info(f"Built semantic index with {len(semantic_index.entities)} entities")
        print(f"  ✓ Semantic index built")

        print(f"  → Step 3: Domain tagging complete...")
        accounting_files = sum(1 for sf in semantic_index.files.values() if sf.domain_context.is_accounting_related)
        logger.info(f"Identified {accounting_files} accounting-related files")
        print(f"  ✓ Tagged {accounting_files} accounting files")

        print(f"  → Step 4: Workflow detection...")
        logger.info(f"Detected {len(semantic_index.workflows)} workflows")
        print(f"  ✓ Detected {len(semantic_index.workflows)} workflows")

        print(f"  → Step 5: Quality scoring...")
        high_quality = sum(1 for se in semantic_index.entities.values() if se.context_score.overall_score.value == "HIGH")
        logger.info(f"Scored {high_quality} high-quality entities")
        print(f"  ✓ Scored {high_quality} high-quality entities")

        print(f"\n✓ Semantic analysis complete!")
        print(f"  - Files analyzed: {len(semantic_index.files)}")
        print(f"  - Entities indexed: {len(semantic_index.entities)}")
        print(f"  - Workflows detected: {len(semantic_index.workflows)}")
        print(f"  - Accounting files: {accounting_files}")
        print(f"  - High-quality entities: {high_quality}")

        logger.info("Semantic project analysis complete")

    except Exception as e:
        logger.error(f"Semantic analysis failed: {e}", exc_info=True)
        print(f"✗ Semantic analysis failed: {e}")
        sys.exit(1)


def query_semantic(query: str, index_path: str) -> None:
    """
    Query the semantic index for domain-aware code search.

    Args:
        query: Natural language query (e.g., "ledger posting functions")
        index_path: Path to the semantic index JSON file
    """
    logger.info(f"Processing semantic query: '{query}' using index: {index_path}")
    print(f"\n✓ Starting semantic query: '{query}'")

    try:
        print(f"  → Loading semantic index...")
        indexer = SemanticIndexer()
        semantic_index = indexer.load_index(index_path)
        logger.info(f"Loaded index with {len(semantic_index.entities)} entities")
        print(f"  ✓ Index loaded")

        print(f"  → Executing query...")
        results = query_semantic_index(query, semantic_index, max_results=10)
        logger.info(f"Query returned {len(results)} results")
        print(f"  ✓ Query executed")

        print(f"\n📋 Query Results for: '{query}'")
        print("=" * 80)

        if not results:
            print("No matching results found.")
            return

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.entity_name}")
            print(f"   📁 File: {result.file_path}")
            print(f"   🎯 Relevance: {result.relevance_score:.2f}")
            print(f"   🏷️  Domain Tags: {', '.join(result.domain_tags) if result.domain_tags else 'None'}")
            print(f"   ⭐ Quality: {result.context_score}")
            if result.short_context:
                print(f"   📝 Context: {result.short_context}")
            if result.reasoning:
                print(f"   💡 Why: {result.reasoning[0]}")

        print(f"\n" + "=" * 80)
        print(f"Found {len(results)} relevant results")

    except Exception as e:
        logger.error(f"Semantic query failed: {e}", exc_info=True)
        print(f"✗ Semantic query failed: {e}")
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
    Command-line interface for the Python Code Analyzer with Semantic Analysis.

    Supports commands:
    - analyze: Extract code structure from a Python file
    - analyze_project: Analyze entire Python project
    - analyze_semantic: Analyze project with domain-aware semantic indexing
    - index: Build FAISS index for RAG queries
    - query: Query the indexed codebase using natural language (RAG)
    - query_semantic: Query semantic index for domain-aware search
    """
    parser = argparse.ArgumentParser(
        description="Legacy Code Modernization Platform - Code Analysis CLI with Semantic Analysis"
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to Python file or directory to analyze"
    )
    parser.add_argument(
        "--command",
        choices=["analyze", "analyze_project", "analyze_semantic", "index", "query", "query_semantic"],
        help="Command to run (default: analyze if file provided)"
    )
    parser.add_argument(
        "--query",
        help="Query string for 'query' or 'query_semantic' commands"
    )
    parser.add_argument(
        "--index",
        help="Path to semantic index JSON file for 'query_semantic' command"
    )

    args = parser.parse_args()

    # Default behavior: if only a path is provided, analyze it
    if args.path and not args.command:
        args.command = "analyze"
    elif not args.path and not args.command:
        parser.print_help()
        return

    try:
        if args.command == "analyze":
            logger.info(f"Running 'analyze' command on {args.path}")
            print("=" * 60)
            print("PYTHON CODE ANALYSIS REPORT")
            print("=" * 60)
            result = analyze_file(args.path)
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

        elif args.command == "analyze_project":
            logger.info(f"Running 'analyze_project' command on {args.path}")
            print("=" * 60)
            print("PROJECT ANALYSIS SUMMARY")
            print("=" * 60)
            print(f"Path: {args.path}")
            project_analysis = analyze_project(args.path)
            print(f"Python files analyzed: {len(project_analysis.file_analyses)}")
            print(f"Functions found: {len(project_analysis.all_functions)}")
            print(f"Classes found: {len(project_analysis.all_classes)}")
            print("=" * 60)

        elif args.command == "analyze_semantic":
            logger.info(f"Running 'analyze_semantic' command on {args.path}")
            analyze_project_semantic(args.path)

        elif args.command == "index":
            logger.info(f"Running 'index' command on {args.path}")
            index_file(args.path)

        elif args.command == "query":
            logger.info(f"Running 'query' command: {args.query}")
            if not args.query:
                print("✗ --query argument is required for 'query' command")
                sys.exit(1)
            query_codebase(args.query)

        elif args.command == "query_semantic":
            logger.info(f"Running 'query_semantic' command: {args.query}")
            if not args.query:
                print("✗ --query argument is required for 'query_semantic' command")
                sys.exit(1)
            if not args.index:
                print("✗ --index argument is required for 'query_semantic' command")
                sys.exit(1)
            query_semantic(args.query, args.index)

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
