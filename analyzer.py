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
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        tree = ast.parse(code)

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)

    except SyntaxError as e:
        print(" Syntax error in file:", e)
        sys.exit(1)

    entities = extract_entities(tree)
    rels = extract_relationships(tree)

    result = {
        "functions": entities.get("functions", []),
        "classes": entities.get("classes", []),
        "imports": entities.get("imports", []),
        "relationships": rels,
    }

    return result


def index_file(file_path):
    """Index a file for RAG: analyze, chunk, embed, and save to FAISS."""
    result = analyze_file(file_path)
    chunks = create_chunks(result)
    model = load_model()
    embeddings = generate_embeddings(chunks, model)
    build_and_save_index(chunks, embeddings)
    print(f"Indexed {len(chunks)} chunks for {file_path}")

def query_codebase(query):
    """Query the indexed codebase using RAG."""
    answer = rag_query(query)
    print(f"Query: {query}\nAnswer: {answer}")

def main():
    parser = argparse.ArgumentParser(description="Python Code Analyzer with RAG")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze subcommand
    subparsers.add_parser("analyze", help="Analyze a Python file").add_argument("file", help="Path to Python file")

    # Index subcommand
    subparsers.add_parser("index", help="Index a Python file for RAG").add_argument("file", help="Path to Python file")

    # Query subcommand
    subparsers.add_parser("query", help="Query the indexed codebase").add_argument("query", help="Query string")

    args = parser.parse_args()

    if args.command == "analyze":
        result = analyze_file(args.file)
        save_json(result, filename="result.json")
        print("\nAnalysis complete!\n")
        print(json.dumps(result, indent=2))
        print_summary(result)
    elif args.command == "index":
        index_file(args.file)
    elif args.command == "query":
        query_codebase(args.query)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
