# Python Code Analyser 

A small utility that parses Python source files to extract functions, classes, imports, and function-call relationships using the AST module. The analyzer saves a structured JSON report to `output/result.json` and prints a friendly terminal summary.

---

## 🔧 Features

- Extracts function and class definitions with line numbers
- Collects imports used in the file
- Detects relationships (which functions call which other functions)
- Saves results to `result.json` and prints a readable summary


##  Requirements

- Python 3.10+ (tested on Python 3.14)

No third-party packages are required — the project relies on the Python standard library.


##  Usage

Run the analyzer against a Python file:

```bash
python analyzer.py sample.py
```

This will:
- Save the JSON report to `result.json`
- Print a human-friendly summary to the console


##  Output format

The JSON output (`result.json`) follows this shape:

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


## 🤝 Contributing

Contributions are welcome! Typical improvements:
- Add unit tests for `extractor`, `relationships`, and `output`
- Add CLI flags (output path, multiple input files)
- Add support for package/dir scanning

Please open an issue or submit a pull request.


## 💡 Next steps

- Add linters and tests to CI
- Expand analysis to include class/attribute relationships and imports usage


---

Made with ❤️ by the code analyser project.