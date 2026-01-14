import ast


class CodeExtractor(ast.NodeVisitor):
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []

    def visit_FunctionDef(self, node):
        self.functions.append({
            "name": node.name,
            "line": node.lineno
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.classes.append({
            "name": node.name,
            "line": node.lineno
        })
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module if node.module else ""
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)


def extract_entities(tree):
    """
    Takes an AST tree and extracts:
    - functions
    - classes
    - imports
    """
    extractor = CodeExtractor()
    extractor.visit(tree)

    return {
        "functions": extractor.functions,
        "classes": extractor.classes,
        "imports": extractor.imports
    }
