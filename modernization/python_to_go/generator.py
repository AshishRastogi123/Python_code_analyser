"""
Go Code Generator for Python to Go Migration.

Generates Go function skeletons from extracted Python function information.
"""

from typing import Dict, Any
from .extractor import FunctionExtractor
from .go_templates import GoTemplates


class GoGenerator:
    """Generates Go code skeletons from Python functions."""

    def __init__(self):
        self.extractor = FunctionExtractor()
        self.templates = GoTemplates()

    def generate_go_skeleton(self, python_file: str, function_name: str) -> str:
        """
        Generate a Go function skeleton from a Python function.

        Args:
            python_file: Path to the Python source file
            function_name: Name of the Python function to migrate

        Returns:
            Go function skeleton as a string
        """
        # Extract function information
        func_info = self.extractor.extract_function(python_file, function_name)

        # Generate Go code
        go_code = self.templates.generate_complete_function(func_info, python_file)

        return go_code

    def generate_multiple_skeletons(self, functions: list) -> str:
        """
        Generate multiple Go function skeletons.

        Args:
            functions: List of tuples (python_file, function_name)

        Returns:
            Combined Go code with multiple functions
        """
        skeletons = []
        for python_file, function_name in functions:
            try:
                skeleton = self.generate_go_skeleton(python_file, function_name)
                skeletons.append(skeleton)
            except Exception as e:
                skeletons.append(f"// Error generating skeleton for {function_name}: {str(e)}")

        return '\n\n'.join(skeletons)
