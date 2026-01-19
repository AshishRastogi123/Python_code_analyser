import json
import os


def save_json(data, filename="output/result.json"):
    """
    Saves analysis result to a JSON file
    """
    # Create directory if needed, but only if filename has a directory component
    dir_path = os.path.dirname(filename)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Output saved to {filename}")


def print_summary(data):
    """
    Prints a readable summary to terminal
    """
    print("\n📊 CODE ANALYSIS SUMMARY\n")

    print("Functions:")
    for func in data.get("functions", []):
        print(f"  - {func['name']} (line {func['line']})")

    print("\nClasses:")
    for cls in data.get("classes", []):
        print(f"  - {cls['name']} (line {cls['line']})")

    print("\nFunction Calls:")
    calls = data.get("relationships", {})
    if not calls:
        print("  No function calls detected.")
    else:
        for caller, callees in calls.items():
            print(f"  {caller} → {', '.join(callees)}")
