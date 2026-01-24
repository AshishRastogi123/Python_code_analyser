"""
AST-based Python code parser for extracting code entities and relationships.

Design Rationale:
- Pure AST analysis using Python's built-in ast module
- Produces FileAnalysis objects (models.FileAnalysis)
- Two-pass approach: first extract entities, then extract relationships
- Handles async functions, decorators, inheritance, and method extraction
- Provides detailed error reporting and logging

Architecture Pattern:
- ASTVisitor classes (NodeVisitor subclasses) for traversal
- EntityExtractor: Pass 1 - extract all entities
- RelationshipExtractor: Pass 2 - find dependencies and calls
- SafeParser: Main entry point with error handling
"""

import ast
import sys
from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass

from core.models import (
    Entity, Function, Class, Import, Relationship,
    Location, EntityType, RelationType, FileAnalysis
)
from utils.logger import get_logger
from utils.config import Config


logger = get_logger(__name__)


class EntityExtractor(ast.NodeVisitor):
    """
    First pass: Extract all functions, classes, and imports from AST.
    
    Builds:
    - List of Function entities
    - List of Class entities with their methods
    - List of Import entities
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.entities: List[Entity] = []
        self.current_class: Optional[Class] = None
        self.current_class_methods: List[Function] = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Extract a regular function definition."""
        self._extract_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Extract an async function definition."""
        self._extract_function(node, is_async=True)
    
    def _extract_function(self, node: ast.AST, is_async: bool) -> None:
        """
        Extract a function and determine if it's a method or standalone function.
        
        If we're inside a class, add to current_class_methods.
        Otherwise, add to entities as a standalone function.
        """
        docstring = ast.get_docstring(node) or ""
        
        # Get source code snippet (first 100 chars of docstring as preview)
        source_preview = docstring[:100] if docstring else ""
        
        # Get decorator names
        decorators = [d.id if isinstance(d, ast.Name) else "" for d in node.decorator_list]
        decorators = [d for d in decorators if d]  # Filter empty strings
        
        entity_type = EntityType.ASYNC_FUNCTION if is_async else EntityType.FUNCTION
        
        location = Location(
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=getattr(node, 'end_lineno', node.lineno),
        )
        
        func = Function(
            name=node.name,
            type=entity_type,
            location=location,
            docstring=docstring,
            source_code=source_preview,
            metadata={
                "is_async": is_async,
                "decorators": decorators,
                "args": [arg.arg for arg in node.args.args],
                "line_count": (getattr(node, 'end_lineno', node.lineno) - node.lineno + 1),
            }
        )
        
        if self.current_class:
            # Method: add to current class
            self.current_class_methods.append(func)
        else:
            # Standalone function: add to entities
            self.entities.append(func)
        
        # Don't visit inside function body (we don't care about nested functions for now)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract a class definition and all its methods."""
        docstring = ast.get_docstring(node) or ""
        
        # Get base class names
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                # For qualified names like parent.BaseClass
                base_classes.append(self._get_name_from_node(base))
        
        location = Location(
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=getattr(node, 'end_lineno', node.lineno),
        )
        
        # Temporarily store current class context
        prev_class = self.current_class
        prev_methods = self.current_class_methods
        
        self.current_class = Class(
            name=node.name,
            type=EntityType.CLASS,
            location=location,
            docstring=docstring,
            base_classes=base_classes,
        )
        self.current_class_methods = []
        
        # Visit class body (will populate current_class_methods)
        self.generic_visit(node)
        
        # Finalize class with extracted methods
        # We need to reconstruct since dataclass is frozen
        finalized_class = Class(
            name=self.current_class.name,
            type=self.current_class.type,
            location=self.current_class.location,
            docstring=self.current_class.docstring,
            source_code=self.current_class.source_code,
            metadata=self.current_class.metadata,
            methods=self.current_class_methods,
            base_classes=self.current_class.base_classes,
        )
        self.entities.append(finalized_class)
        
        # Restore previous class context
        self.current_class = prev_class
        self.current_class_methods = prev_methods
    
    def visit_Import(self, node: ast.Import) -> None:
        """Extract an import statement."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            location = Location(
                file_path=self.file_path,
                line_start=node.lineno,
            )
            
            imp = Import(
                name=name,
                type=EntityType.IMPORT,
                location=location,
                module=alias.name,
                alias=alias.asname,
                is_from=False,
            )
            self.entities.append(imp)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Extract a from...import statement."""
        module = node.module if node.module else ""
        
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            location = Location(
                file_path=self.file_path,
                line_start=node.lineno,
            )
            
            # Store full qualified name for tracking
            full_name = f"{module}.{name}" if module else name
            
            imp = Import(
                name=name,
                type=EntityType.IMPORT,
                location=location,
                module=module,
                alias=alias.asname,
                is_from=True,
            )
            self.entities.append(imp)
    
    @staticmethod
    def _get_name_from_node(node: ast.AST) -> str:
        """Extract name string from various AST node types."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{EntityExtractor._get_name_from_node(node.value)}.{node.attr}"
        else:
            return ""


class RelationshipExtractor(ast.NodeVisitor):
    """
    Second pass: Extract relationships between entities (function calls, inheritance, imports).
    
    Finds:
    - Which functions call which other functions
    - Which classes inherit from which
    - Usage of imported modules
    """
    
    def __init__(self, file_path: str, entities: List[Entity]):
        self.file_path = file_path
        self.entities = entities
        self.relationships: List[Relationship] = []
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function and look for calls inside."""
        self._visit_function_body(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function and look for calls inside."""
        self._visit_function_body(node)
    
    def _visit_function_body(self, node: ast.AST) -> None:
        """Extract calls from within a function body."""
        prev_func = self.current_function
        func_name = node.name
        
        if self.current_class:
            self.current_function = f"{self.current_class}.{func_name}"
        else:
            self.current_function = func_name
        
        # Look for function calls
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                self._extract_call(child)
        
        self.current_function = prev_func
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class and extract inheritance relationships."""
        prev_class = self.current_class
        self.current_class = node.name
        
        # Extract inheritance relationships
        for base in node.bases:
            base_name = self._get_name_from_node(base)
            if base_name:
                rel = Relationship(
                    source=self.current_class,
                    target=base_name,
                    type=RelationType.INHERITS,
                    source_location=Location(file_path=self.file_path, line_start=node.lineno),
                )
                self.relationships.append(rel)
        
        # Visit methods inside class
        self.generic_visit(node)
        
        self.current_class = prev_class
    
    def _extract_call(self, node: ast.Call) -> None:
        """
        Extract a function call relationship.
        
        Handles:
        - Simple calls: func()
        - Method calls: obj.method()
        - Chained calls: obj.method().other()
        """
        called_name = self._get_name_from_node(node.func)
        
        if not called_name or not self.current_function:
            return
        
        location = Location(
            file_path=self.file_path,
            line_start=node.lineno,
        )
        
        rel = Relationship(
            source=self.current_function,
            target=called_name,
            type=RelationType.CALLS,
            source_location=location,
        )
        self.relationships.append(rel)
    
    @staticmethod
    def _get_name_from_node(node: ast.AST) -> str:
        """Extract callable name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = RelationshipExtractor._get_name_from_node(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        else:
            return ""


class SafeParser:
    """
    Safe entry point for parsing Python files.
    
    Handles errors gracefully and returns FileAnalysis with error information.
    """
    
    @staticmethod
    def parse_file(file_path: str) -> FileAnalysis:
        """
        Parse a Python file and extract entities and relationships.
        
        Args:
            file_path: Path to the Python file
        
        Returns:
            FileAnalysis with extracted entities, relationships, and any errors
        """
        file_path = str(Path(file_path).resolve())
        analysis = FileAnalysis(file_path=file_path)
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Check file size (avoid analyzing huge files)
            max_size = Config.max_file_size_mb() * 1024 * 1024
            if len(source_code) > max_size:
                analysis.errors.append(
                    f"File exceeds maximum size ({Config.max_file_size_mb()} MB)"
                )
                logger.warning(f"Skipping {file_path}: file too large")
                return analysis
            
            # Parse AST
            tree = ast.parse(source_code, filename=file_path)
            
            # Extract entities (first pass)
            entity_extractor = EntityExtractor(file_path)
            entity_extractor.visit(tree)
            analysis.entities = entity_extractor.entities
            
            # Extract relationships (second pass)
            relationship_extractor = RelationshipExtractor(file_path, analysis.entities)
            relationship_extractor.visit(tree)
            analysis.relationships = relationship_extractor.relationships
            
            logger.info(
                f"Parsed {file_path}: "
                f"{len(analysis.functions)} functions, "
                f"{len(analysis.classes)} classes, "
                f"{len(analysis.imports)} imports"
            )
        
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            analysis.errors.append(error_msg)
            logger.error(f"Syntax error in {file_path}: {error_msg}")
        
        except UnicodeDecodeError as e:
            error_msg = f"Encoding error: {e}"
            analysis.errors.append(error_msg)
            logger.error(f"Encoding error in {file_path}: {error_msg}")
        
        except Exception as e:
            error_msg = f"Unexpected error: {type(e).__name__}: {e}"
            analysis.errors.append(error_msg)
            logger.error(f"Error parsing {file_path}: {error_msg}")
        
        return analysis
