"""
Python Function Extractor using AST.

Extracts function metadata from Python source files for migration purposes.
"""

import ast
import inspect
from typing import Dict, Any, Optional


class FunctionExtractor:
    """Extracts function information from Python source code using AST."""

    def extract_function(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """
        Extract function information from a Python file.

        Args:
            file_path: Path to the Python file
            function_name: Name of the function to extract

        Returns:
            Dictionary containing function metadata
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return self._extract_function_info(node, source_code)

        raise ValueError(f"Function '{function_name}' not found in {file_path}")

    def _extract_function_info(self, node: ast.FunctionDef, source_code: str) -> Dict[str, Any]:
        """Extract detailed information from an AST FunctionDef node."""
        # Extract function name
        function_name = node.name

        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'type': None,  # Type hints not extracted for simplicity
                'default': None
            }
            parameters.append(param_info)

        # Handle *args and **kwargs
        if node.args.vararg:
            parameters.append({'name': f"*{node.args.vararg.arg}", 'type': None, 'default': None})
        if node.args.kwark:
            parameters.append({'name': f"**{node.args.kwark.arg}", 'type': None, 'default': None})

        # Extract docstring
        docstring = ast.get_docstring(node) or ""

        # Extract raw function body (simplified)
        # Get the source lines for the function
        start_line = node.lineno - 1  # AST lineno is 1-based
        end_line = node.end_lineno
        lines = source_code.splitlines()
        raw_body = '\n'.join(lines[start_line:end_line])

        return {
            'name': function_name,
            'parameters': parameters,
            'docstring': docstring,
            'raw_body': raw_body,
            'line_start': node.lineno,
            'line_end': node.end_lineno
        }
