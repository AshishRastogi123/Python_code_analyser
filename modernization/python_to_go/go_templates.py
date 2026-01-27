"""
Go Code Templates for Python to Go Migration.

Provides templates for generating Go function skeletons.
"""

from typing import Dict, Any, List


class GoTemplates:
    """Templates for generating Go code from Python functions."""

    @staticmethod
    def to_camel_case(snake_str: str) -> str:
        """Convert snake_case to CamelCase."""
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)

    @staticmethod
    def map_python_type_to_go(param_name: str, python_type: Any = None) -> str:
        """
        Map Python parameter to Go type.
        Uses generic types since we don't have full type information.
        """
        # Basic heuristics based on parameter name
        name_lower = param_name.lower()

        if 'map' in name_lower or 'dict' in name_lower:
            return 'map[string]interface{}'
        elif 'list' in name_lower or 'array' in name_lower:
            return '[]interface{}'
        elif 'bool' in name_lower or param_name in ['cancel', 'adv_adj', 'merge_entries', 'from_repost']:
            return 'bool'
        elif 'date' in name_lower or 'time' in name_lower:
            return 'string'  # Simplified
        elif 'amount' in name_lower or 'debit' in name_lower or 'credit' in name_lower:
            return 'float64'
        elif 'count' in name_lower or 'number' in name_lower or 'no' in name_lower:
            return 'int'
        else:
            return 'interface{}'  # Generic fallback

    @staticmethod
    def generate_function_signature(func_info: Dict[str, Any]) -> str:
        """Generate Go function signature."""
        func_name = GoTemplates.to_camel_case(func_info['name'])

        params = []
        for param in func_info['parameters']:
            param_name = param['name']
            # Handle *args and **kwargs
            if param_name.startswith('*'):
                if param_name.startswith('**'):
                    # **kwargs -> variadic interface{}
                    param_name = param_name[2:]
                    go_type = '...interface{}'
                else:
                    # *args -> variadic interface{}
                    param_name = param_name[1:]
                    go_type = '...interface{}'
            else:
                go_type = GoTemplates.map_python_type_to_go(param_name)

            params.append(f"{param_name} {go_type}")

        param_str = ', '.join(params) if params else ''

        return f"func {func_name}({param_str}) error"

    @staticmethod
    def generate_function_body(func_info: Dict[str, Any]) -> str:
        """Generate Go function body with TODO comments."""
        body_lines = []

        # Add basic structure
        body_lines.append("\t// TODO: transcribed logic")
        body_lines.append("\treturn nil")

        return '\n'.join(body_lines)

    @staticmethod
    def generate_complete_function(func_info: Dict[str, Any], source_file: str) -> str:
        """Generate complete Go function."""
        lines = []

        # Header comments
        lines.append(f"// Migrated from ERPNext Accounts: {source_file}")
        lines.append(f"// Original function: {func_info['name']}")

        # Function signature
        signature = GoTemplates.generate_function_signature(func_info)
        lines.append(signature + " {")

        # Function body
        body = GoTemplates.generate_function_body(func_info)
        lines.append(body)

        lines.append("}")

        return '\n'.join(lines)
