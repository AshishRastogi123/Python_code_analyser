import ast
import json
import sys
import argparse

from extractor import extract_entities
from relationships import extract_relationships
from output import save_json, print_summary
from rag.chunker import create_chunks
from rag.embeddings import generate_embeddings, load_model
from rag.faiss_index import build_and_save_index
from rag.pipeline import rag_query


def analyze_file(file_path):
    """Parse the file and return a unified analysis dict.

    The returned structure matches what `output.print_summary` expects:
      - functions: list of {name, line}
      - classes: list of {name, line}
      - imports: list of import strings
      - relationships: dict mapping function name -> [callees]
    """
    print(f"\n✓ Starting analysis of file: {file_path}")
    try:
        print(f"  → Reading file...")
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        print(f"  ✓ File read successfully")

        print(f"  → Parsing AST...")
        tree = ast.parse(code)
        print(f"  ✓ AST parsing successful")

    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        sys.exit(1)

    except SyntaxError as e:
        print(f"✗ Syntax error in file: {e}")
        sys.exit(1)

    print(f"  → Extracting entities...")
    entities = extract_entities(tree)
    print(f"  ✓ Entities extracted: {len(entities.get('functions', []))} functions, {len(entities.get('classes', []))} classes")

    print(f"  → Extracting relationships...")
    rels = extract_relationships(tree)
    print(f"  ✓ Relationships extracted: {len(rels)} relationships found")

    result = {
        "functions": entities.get("functions", []),
        "classes": entities.get("classes", []),
        "imports": entities.get("imports", []),
        "relationships": rels,
    }

    return result


def index_file(file_path):
    """Index a file for RAG: analyze, chunk, embed, and save to FAISS."""
    print(f"\n✓ Starting indexing of file: {file_path}")
    
    print(f"  → Step 1: Analyzing file...")
    result = analyze_file(file_path)
    print(f"  ✓ Analysis complete")
    
    print(f"  → Step 2: Creating chunks...")
    chunks = create_chunks(result)
    print(f"  ✓ Created {len(chunks)} chunks")
    
    print(f"  → Step 3: Loading embedding model...")
    model = load_model()
    print(f"  ✓ Model loaded successfully")
    
    print(f"  → Step 4: Generating embeddings...")
    embeddings = generate_embeddings(chunks, model)
    print(f"  ✓ Generated embeddings for {len(embeddings)} chunks")
    
    print(f"  → Step 5: Building FAISS index...")
    build_and_save_index(chunks, embeddings)
    print(f"  ✓ FAISS index built and saved")
    
    print(f"\n✓ Indexing complete! Indexed {len(chunks)} chunks for {file_path}")

def query_codebase(query):
    """Query the indexed codebase using RAG."""
    print(f"\n✓ Starting query: '{query}'")
    print(f"  → Retrieving relevant context...")
    answer = rag_query(query)
    print(f"  ✓ Query processed")
    print(f"\nQuery: {query}\nAnswer: {answer}")

def main():
    parser = argparse.ArgumentParser(description="Python Code Analyzer with RAG")
    parser.add_argument("file", nargs="?", help="Path to Python file (default: analyze mode)")
    parser.add_argument("--command", choices=["analyze", "index", "query"], help="Command to run")
    parser.add_argument("--query", help="Query string for query command")

    args = parser.parse_args()

    # Default behavior: if only a file is provided, analyze it
    if args.file and not args.command:
        args.command = "analyze"
    elif not args.file and not args.command:
        parser.print_help()
        return

    if args.command == "analyze":
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
        index_file(args.file)
    elif args.command == "query":
        query_codebase(args.query)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
