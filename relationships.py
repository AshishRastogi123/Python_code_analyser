import ast
from collections import defaultdict


class RelationshipAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.current_function = None
        self.function_calls = defaultdict(list)

    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = None

    def visit_Call(self, node):
        if self.current_function:
            # direct function calls: foo()
            if isinstance(node.func, ast.Name):
                self.function_calls[self.current_function].append(node.func.id)

            # method calls: obj.foo()
            elif isinstance(node.func, ast.Attribute):
                self.function_calls[self.current_function].append(node.func.attr)

        self.generic_visit(node)


def extract_relationships(tree):
    """
    Takes AST tree and returns function call relationships
    """
    analyzer = RelationshipAnalyzer()
    analyzer.visit(tree)
    return dict(analyzer.function_calls)
