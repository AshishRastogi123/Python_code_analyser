import ast
import json
import sys

from extractor import extract_entities
from relationships import extract_relationships
from output import save_json, print_summary


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


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <python_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    result = analyze_file(file_path)

    # Save to the project's output folder for consistency
    save_json(result, filename="result.json")

    print("\n Analysis complete!\n")
    print(json.dumps(result, indent=2))

    # Also print a friendly summary
    print_summary(result)


if __name__ == "__main__":
    main()
