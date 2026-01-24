"""
Data models for code analysis results.

Design Rationale:
- Use standard library dataclasses (no external dependencies)
- Represent all code entities extracted from AST
- Immutable/frozen dataclasses for integrity
- Easy conversion to dict/JSON (for API responses later)
- Type hints throughout for IDE support and validation

These models form the core vocabulary of the entire platform:
- They are produced by core.ast_parser and core.dependency_graph
- They are consumed by RAG indexing, AI analysis, and API responses
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum


class EntityType(str, Enum):
    """Types of code entities that can be extracted."""
    FUNCTION = "function"
    CLASS = "class"
    IMPORT = "import"
    VARIABLE = "variable"
    DECORATOR = "decorator"
    ASYNC_FUNCTION = "async_function"


class RelationType(str, Enum):
    """Types of relationships between entities."""
    CALLS = "calls"
    DEFINES = "defines"
    INHERITS = "inherits"
    IMPORTS = "imports"
    USES = "uses"
    DEPENDS_ON = "depends_on"


@dataclass(frozen=True)
class Location:
    """
    Location of an entity in source code.
    
    Attributes:
        file_path: Absolute path to the source file
        line_start: Starting line number (1-indexed)
        line_end: Ending line number (1-indexed)
        column_start: Starting column (0-indexed)
    """
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    column_start: int = 0
    
    def __str__(self) -> str:
        """Format location as 'file:line' string."""
        return f"{self.file_path}:{self.line_start}"


@dataclass(frozen=True)
class Entity:
    """
    Base class for all code entities (functions, classes, etc.).
    
    Attributes:
        name: Entity name (function/class/import name)
        type: Type of entity (function, class, import, etc.)
        location: Where in the code this entity is defined
        docstring: Documentation string (if present)
        source_code: First N lines of the entity (for preview)
        metadata: Additional metadata (modifiers, decorators, etc.)
    """
    name: str
    type: EntityType
    location: Location
    docstring: Optional[str] = None
    source_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary (for JSON serialization)."""
        return {
            "name": self.name,
            "type": self.type.value,
            "location": {
                "file_path": self.location.file_path,
                "line_start": self.location.line_start,
                "line_end": self.location.line_end,
                "column_start": self.location.column_start,
            },
            "docstring": self.docstring,
            "source_code": self.source_code,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class Function(Entity):
    """Represents a function or method."""
    
    def __post_init__(self):
        """Validate that entity type is a function variant."""
        if self.type not in (EntityType.FUNCTION, EntityType.ASYNC_FUNCTION):
            raise ValueError(f"Function entity must have function type, got {self.type}")


@dataclass(frozen=True)
class Class(Entity):
    """
    Represents a class definition.
    
    Attributes:
        methods: List of methods in this class
        base_classes: Names of parent classes
    """
    methods: List[Function] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate that entity type is CLASS."""
        if self.type != EntityType.CLASS:
            raise ValueError(f"Class entity must have CLASS type, got {self.type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert class to dictionary including methods."""
        d = super().to_dict()
        d["methods"] = [m.to_dict() for m in self.methods]
        d["base_classes"] = self.base_classes
        return d


@dataclass(frozen=True)
class Import(Entity):
    """
    Represents an import statement.
    
    Attributes:
        module: Module name being imported
        alias: Optional alias for the import
        is_from: Whether this is a 'from X import Y' style
    """
    module: str = ""
    alias: Optional[str] = None
    is_from: bool = False
    
    def __post_init__(self):
        """Validate that entity type is IMPORT."""
        if self.type != EntityType.IMPORT:
            raise ValueError(f"Import entity must have IMPORT type, got {self.type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert import to dictionary."""
        d = super().to_dict()
        d["module"] = self.module
        d["alias"] = self.alias
        d["is_from"] = self.is_from
        return d


@dataclass(frozen=True)
class Relationship:
    """
    Represents a relationship between two code entities.
    
    Attributes:
        source: Name of the source entity
        target: Name of the target entity
        type: Type of relationship (calls, imports, inherits, etc.)
        source_location: Location where the relationship is defined
        metadata: Additional metadata about the relationship
    """
    source: str
    target: str
    type: RelationType
    source_location: Optional[Location] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type.value,
            "source_location": {
                "file_path": self.source_location.file_path,
                "line_start": self.source_location.line_start,
            } if self.source_location else None,
            "metadata": self.metadata,
        }


@dataclass
class FileAnalysis:
    """
    Results of analyzing a single Python file.
    
    Attributes:
        file_path: Path to the analyzed file
        entities: All entities found in the file
        relationships: Relationships between entities
        imports: All imports (convenience list)
        functions: All functions (convenience list)
        classes: All classes (convenience list)
        errors: Any errors encountered during analysis
    """
    file_path: str
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def imports(self) -> List[Import]:
        """Get all imports from entities."""
        return [e for e in self.entities if isinstance(e, Import)]
    
    @property
    def functions(self) -> List[Function]:
        """Get all functions from entities."""
        return [e for e in self.entities if isinstance(e, Function)]
    
    @property
    def classes(self) -> List[Class]:
        """Get all classes from entities."""
        return [e for e in self.entities if isinstance(e, Class)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary."""
        return {
            "file_path": self.file_path,
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "errors": self.errors,
            "summary": {
                "total_entities": len(self.entities),
                "functions": len(self.functions),
                "classes": len(self.classes),
                "imports": len(self.imports),
                "relationships": len(self.relationships),
            }
        }


@dataclass
class ProjectAnalysis:
    """
    Results of analyzing an entire project/codebase.
    
    Attributes:
        project_name: Name of the project
        file_analyses: Analysis results for each file
        all_relationships: All relationships across all files
        errors: Project-level errors
    """
    project_name: str
    file_analyses: List[FileAnalysis] = field(default_factory=list)
    all_relationships: List[Relationship] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def all_entities(self) -> List[Entity]:
        """Get all entities from all files."""
        entities = []
        for fa in self.file_analyses:
            entities.extend(fa.entities)
        return entities
    
    @property
    def all_functions(self) -> List[Function]:
        """Get all functions from all files."""
        return [e for e in self.all_entities if isinstance(e, Function)]
    
    @property
    def all_classes(self) -> List[Class]:
        """Get all classes from all files."""
        return [e for e in self.all_entities if isinstance(e, Class)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project analysis to dictionary."""
        return {
            "project_name": self.project_name,
            "file_analyses": [fa.to_dict() for fa in self.file_analyses],
            "all_relationships": [r.to_dict() for r in self.all_relationships],
            "errors": self.errors,
            "summary": {
                "total_files": len(self.file_analyses),
                "total_entities": len(self.all_entities),
                "total_functions": len(self.all_functions),
                "total_classes": len(self.all_classes),
                "total_relationships": len(self.all_relationships),
            }
        }
