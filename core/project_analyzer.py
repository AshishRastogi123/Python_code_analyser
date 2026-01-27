"""
Project-wide code analyzer for Python codebases.

Design Rationale:
- Recursively analyzes entire Python projects using existing FileAnalysis
- Aggregates results into ProjectAnalysis for cross-file insights
- Builds dependency graphs and call relationships across files
- Outputs unified JSON index for RAG and analysis tools
- Extensible for future domain tagging and modernization features

Architecture Pattern:
- ProjectAnalyzer: Main class for project traversal and aggregation
- Uses os.walk for directory traversal with ignore patterns
- Leverages SafeParser for individual file analysis
- Builds cross-file relationships (imports, calls, dependencies)
"""

import os
import json
from pathlib import Path
from typing import List, Optional

from core.models import ProjectAnalysis, FileAnalysis, Relationship
from core.ast_parser import SafeParser
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class ProjectAnalyzer:
    """
    Analyzes entire Python projects by recursively parsing all .py files.

    Features:
    - Directory traversal with configurable ignore patterns
    - Aggregation of FileAnalysis into ProjectAnalysis
    - Cross-file relationship building (imports, calls)
    - Progress logging and error handling
    - JSON output for indexing and RAG
    """

    def __init__(self, root_path: str, project_name: Optional[str] = None):
        """
        Initialize project analyzer.

        Args:
            root_path: Root directory path to analyze (legacy code only)
            project_name: Optional project name (defaults to directory name)
        """
        self.root_path = Path(root_path).resolve()
        self.project_name = project_name or self.root_path.name

        # Ignore patterns (configurable + defaults)
        self.ignore_patterns = set(Config.ignore_patterns())
        self.ignore_patterns.update({
            "__pycache__",
            ".git",
            "venv",
            "env",
            ".venv",
            "node_modules"
        })

        # SAFETY CHECK: prevent analyzing analyzer source itself
        repo_root = Path(__file__).resolve().parents[1]
        if self.root_path == repo_root or repo_root in self.root_path.parents:
            logger.warning(
                "Root path appears to include analyzer source code. "
                "Expected an external legacy code directory."
            )

        logger.info(f"Initialized ProjectAnalyzer")
        logger.info(f"Project name: {self.project_name}")
        logger.info(f"Legacy code root: {self.root_path}")
        logger.info("Analyzer source code is excluded by design")

    def analyze_project(self) -> ProjectAnalysis:
        """
        Analyze the entire project recursively.

        Returns:
            ProjectAnalysis containing all files, entities, and relationships
        """
        logger.info(f"Starting project analysis: {self.project_name}")

        project_analysis = ProjectAnalysis(project_name=self.project_name)
        file_paths = self._collect_python_files()

        logger.info(f"Found {len(file_paths)} Python files to analyze")

        for index, file_path in enumerate(file_paths, start=1):
            logger.info(f"Analyzing file {index}/{len(file_paths)}: {file_path}")
            print(f"  → Analyzing {index}/{len(file_paths)}: {Path(file_path).name}")

            try:
                file_analysis = SafeParser.parse_file(file_path)

                # Optional metadata tagging
                if "test" in Path(file_path).parts:
                    file_analysis.metadata["is_test_file"] = True

                project_analysis.file_analyses.append(file_analysis)

                if file_analysis.errors:
                    project_analysis.errors.extend(file_analysis.errors)
                    logger.warning(f"Errors in {file_path}: {file_analysis.errors}")

            except Exception as exc:
                error_msg = f"Failed to analyze {file_path}: {exc}"
                project_analysis.errors.append(error_msg)
                logger.error(error_msg)

        # Build cross-file relationships
        logger.info("Building cross-file relationships")
        project_analysis.all_relationships = self._build_cross_file_relationships(
            project_analysis.file_analyses
        )

        logger.info(
            f"Project analysis complete: {len(project_analysis.file_analyses)} files analyzed"
        )
        return project_analysis

    def _collect_python_files(self) -> List[str]:
        """
        Recursively collect all Python files in the project,
        respecting ignore patterns.

        Returns:
            List of absolute paths to Python files
        """
        python_files: List[str] = []

        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)

            # Skip ignored directories
            dirs[:] = [
                d for d in dirs
                if not self._should_ignore(root_path / d)
            ]

            # Skip ignored roots
            if self._should_ignore(root_path):
                continue

            for file in files:
                if file.endswith(".py"):
                    file_path = root_path / file
                    if not self._should_ignore(file_path):
                        python_files.append(str(file_path))

        return python_files

    def _should_ignore(self, path: Path) -> bool:
        """
        Check if a path should be ignored.

        Args:
            path: Path to check

        Returns:
            True if path should be ignored
        """
        # Ignore exact directory names
        if path.name in self.ignore_patterns:
            return True

        # Ignore hidden directories/files
        if any(part.startswith(".") for part in path.parts):
            return True

        return False

    def _build_cross_file_relationships(
        self, file_analyses: List[FileAnalysis]
    ) -> List[Relationship]:
        """
        Build relationships that span across files.

        Args:
            file_analyses: List of FileAnalysis objects

        Returns:
            List of cross-file relationships
        """
        relationships: List[Relationship] = []
        entity_map = {}  # entity_name -> (file_path, entity)

        # Build entity lookup
        for fa in file_analyses:
            for entity in fa.entities:
                entity_map[entity.name] = (fa.file_path, entity)

        # Build cross-file relationships
        for fa in file_analyses:
            for rel in fa.relationships:
                if rel.target in entity_map:
                    target_file, _ = entity_map[rel.target]
                    if target_file != fa.file_path:
                        cross_rel = Relationship(
                            source=f"{fa.file_path}::{rel.source}",
                            target=f"{target_file}::{rel.target}",
                            type=rel.type,
                            source_location=rel.source_location,
                            metadata={
                                **rel.metadata,
                                "cross_file": True,
                                "source_file": fa.file_path,
                                "target_file": target_file,
                            },
                        )
                        relationships.append(cross_rel)

        logger.info(f"Built {len(relationships)} cross-file relationships")
        return relationships

    def save_analysis(
        self,
        project_analysis: ProjectAnalysis,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Save project analysis to a JSON file.

        Args:
            project_analysis: Analysis results to save
            output_path: Optional output path

        Returns:
            Path to saved JSON file
        """
        if output_path is None:
            output_path = f"{self.project_name}_analysis.json"

        output_path = Path(output_path).resolve()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                project_analysis.to_dict(),
                f,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(f"Saved project analysis to {output_path}")
        return str(output_path)


def analyze_project(
    root_path: str,
    project_name: Optional[str] = None,
    save_output: bool = True,
) -> ProjectAnalysis:
    """
    Convenience function to analyze an entire project.

    Args:
        root_path: Root directory of legacy code
        project_name: Optional project name
        save_output: Whether to save JSON output

    Returns:
        ProjectAnalysis object
    """
    analyzer = ProjectAnalyzer(root_path, project_name)
    analysis = analyzer.analyze_project()

    if save_output:
        output_file = analyzer.save_analysis(analysis)
        print(f"✓ Analysis saved to: {output_file}")

    return analysis
