"""
Semantic index for domain-aware code analysis.

This module provides a unified index that combines:
- Domain tagging
- Workflow detection
- Context quality scoring

Design:
- Separate from AST extraction layer
- Queryable for domain-aware searches
- JSON serializable for persistence
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

from core.models import ProjectAnalysis, FileAnalysis
from core.domain_tagger import DomainTagger, DomainContext, DomainTag
from core.workflow_detector import WorkflowDetector, WorkflowHint
from core.context_scorer import ContextScorer, ContextScore, QualityScore
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SemanticEntity:
    """
    Semantic information for a code entity.

    Attributes:
        name: Entity name
        file_path: File containing the entity
        domain_context: Domain tagging results
        context_score: Quality scoring
        entity_type: Type of entity (function, class, etc.)
    """
    name: str
    file_path: str
    domain_context: DomainContext
    context_score: ContextScore
    entity_type: str


@dataclass
class SemanticFile:
    """
    Semantic information for a file.

    Attributes:
        file_path: Path to the file
        domain_context: Domain tagging results
        context_score: Quality scoring
        entities: List of entities in the file
    """
    file_path: str
    domain_context: DomainContext
    context_score: ContextScore
    entities: List[SemanticEntity] = field(default_factory=list)


@dataclass
class SemanticIndex:
    """
    Unified semantic index for domain-aware analysis.

    Attributes:
        project_name: Name of the analyzed project
        files: Semantic information for all files
        entities: Semantic information for all entities
        workflows: Detected workflow hints
        metadata: Additional metadata
    """
    project_name: str
    files: Dict[str, SemanticFile] = field(default_factory=dict)
    entities: Dict[str, SemanticEntity] = field(default_factory=dict)
    workflows: List[WorkflowHint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_name": self.project_name,
            "files": {
                path: {
                    "file_path": sf.file_path,
                    "domain_context": {
                        "tags": [{"tag": t.tag, "confidence": t.confidence, "reasoning": t.reasoning} for t in sf.domain_context.tags],
                        "primary_tag": sf.domain_context.primary_tag,
                        "is_accounting_related": sf.domain_context.is_accounting_related
                    },
                    "context_score": {
                        "overall_score": sf.context_score.overall_score.value,
                        "domain_relevance": sf.context_score.domain_relevance,
                        "relationship_density": sf.context_score.relationship_density,
                        "docstring_quality": sf.context_score.docstring_quality,
                        "test_coverage": sf.context_score.test_coverage,
                        "reasoning": sf.context_score.reasoning
                    },
                    "entities": [e.name for e in sf.entities]
                }
                for path, sf in self.files.items()
            },
            "entities": {
                key: {
                    "name": se.name,
                    "file_path": se.file_path,
                    "domain_context": {
                        "tags": [{"tag": t.tag, "confidence": t.confidence, "reasoning": t.reasoning} for t in se.domain_context.tags],
                        "primary_tag": se.domain_context.primary_tag,
                        "is_accounting_related": se.domain_context.is_accounting_related
                    },
                    "context_score": {
                        "overall_score": se.context_score.overall_score.value,
                        "domain_relevance": se.context_score.domain_relevance,
                        "relationship_density": se.context_score.relationship_density,
                        "docstring_quality": se.context_score.docstring_quality,
                        "test_coverage": se.context_score.test_coverage,
                        "reasoning": se.context_score.reasoning
                    },
                    "entity_type": se.entity_type
                }
                for key, se in self.entities.items()
            },
            "workflows": [
                {
                    "name": w.name,
                    "steps": [
                        {
                            "entity_name": s.entity_name,
                            "file_path": s.file_path,
                            "domain_tags": s.domain_tags,
                            "role": s.role
                        }
                        for s in w.steps
                    ],
                    "confidence": w.confidence,
                    "reasoning": w.reasoning,
                    "business_process": w.business_process
                }
                for w in self.workflows
            ],
            "metadata": self.metadata
        }


class SemanticIndexer:
    """
    Builds semantic index from project analysis.

    Combines domain tagging, workflow detection, and quality scoring
    into a unified, queryable index.
    """

    def __init__(self):
        """Initialize semantic indexer."""
        self.tagger = DomainTagger()
        self.workflow_detector = WorkflowDetector()
        self.scorer = ContextScorer()

    def build_index(self, project_analysis: ProjectAnalysis) -> SemanticIndex:
        """
        Build complete semantic index from project analysis.

        Args:
            project_analysis: Complete project analysis

        Returns:
            SemanticIndex with all semantic information
        """
        logger.info("Building semantic index")

        index = SemanticIndex(project_name=project_analysis.project_name)

        # Build file and entity semantic info
        for file_analysis in project_analysis.file_analyses:
            semantic_file = self._build_semantic_file(file_analysis, project_analysis)
            index.files[file_analysis.file_path] = semantic_file

            # Add entities
            for semantic_entity in semantic_file.entities:
                key = f"{semantic_entity.file_path}::{semantic_entity.name}"
                index.entities[key] = semantic_entity

        # Detect workflows
        index.workflows = self.workflow_detector.detect_workflows(project_analysis)

        # Add metadata
        index.metadata = {
            "total_files": len(index.files),
            "total_entities": len(index.entities),
            "total_workflows": len(index.workflows),
            "accounting_files": sum(1 for sf in index.files.values() if sf.domain_context.is_accounting_related),
            "high_quality_entities": sum(1 for se in index.entities.values() if se.context_score.overall_score == QualityScore.HIGH)
        }

        logger.info(f"Built semantic index: {index.metadata}")
        return index

    def _build_semantic_file(self, file_analysis: FileAnalysis, project_analysis: ProjectAnalysis) -> SemanticFile:
        """
        Build semantic information for a file.

        Args:
            file_analysis: Analysis of the file
            project_analysis: Full project context

        Returns:
            SemanticFile with domain and quality info
        """
        # Domain context
        domain_context = self.tagger.tag_file(file_analysis)

        # Quality score
        context_score = self.scorer.score_file(file_analysis, project_analysis)

        # Build semantic entities
        entities = []
        for entity in file_analysis.entities:
            entity_score = self.scorer.score_entity(entity, file_analysis, project_analysis)
            entity_domain = self.tagger.tag_entity(entity)

            semantic_entity = SemanticEntity(
                name=entity.name,
                file_path=file_analysis.file_path,
                domain_context=entity_domain,
                context_score=entity_score,
                entity_type=entity.type.value
            )
            entities.append(semantic_entity)

        return SemanticFile(
            file_path=file_analysis.file_path,
            domain_context=domain_context,
            context_score=context_score,
            entities=entities
        )

    def save_index(self, index: SemanticIndex, output_path: str) -> None:
        """
        Save semantic index to JSON file.

        Args:
            index: Semantic index to save
            output_path: Output file path
        """
        output_path = Path(output_path).resolve()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(index.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved semantic index to {output_path}")

    def load_index(self, input_path: str) -> SemanticIndex:
        """
        Load semantic index from JSON file.

        Args:
            input_path: Input file path

        Returns:
            Loaded SemanticIndex
        """
        input_path = Path(input_path).resolve()

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Reconstruct SemanticIndex from dict
        index = SemanticIndex(project_name=data["project_name"])

        # Reconstruct files
        for path, file_data in data["files"].items():
            domain_context = DomainContext(
                tags=[DomainTag(tag=t["tag"], confidence=t["confidence"], reasoning=t["reasoning"])
                      for t in file_data["domain_context"]["tags"]],
                primary_tag=file_data["domain_context"]["primary_tag"],
                is_accounting_related=file_data["domain_context"]["is_accounting_related"]
            )

            context_score = ContextScore(
                overall_score=QualityScore(file_data["context_score"]["overall_score"]),
                domain_relevance=file_data["context_score"]["domain_relevance"],
                relationship_density=file_data["context_score"]["relationship_density"],
                docstring_quality=file_data["context_score"]["docstring_quality"],
                test_coverage=file_data["context_score"]["test_coverage"],
                reasoning=file_data["context_score"]["reasoning"]
            )

            semantic_file = SemanticFile(
                file_path=file_data["file_path"],
                domain_context=domain_context,
                context_score=context_score
            )
            index.files[path] = semantic_file

        # Reconstruct entities
        for key, entity_data in data["entities"].items():
            domain_context = DomainContext(
                tags=[DomainTag(tag=t["tag"], confidence=t["confidence"], reasoning=t["reasoning"])
                      for t in entity_data["domain_context"]["tags"]],
                primary_tag=entity_data["domain_context"]["primary_tag"],
                is_accounting_related=entity_data["domain_context"]["is_accounting_related"]
            )

            context_score = ContextScore(
                overall_score=QualityScore(entity_data["context_score"]["overall_score"]),
                domain_relevance=entity_data["context_score"]["domain_relevance"],
                relationship_density=entity_data["context_score"]["relationship_density"],
                docstring_quality=entity_data["context_score"]["docstring_quality"],
                test_coverage=entity_data["context_score"]["test_coverage"],
                reasoning=entity_data["context_score"]["reasoning"]
            )

            semantic_entity = SemanticEntity(
                name=entity_data["name"],
                file_path=entity_data["file_path"],
                domain_context=domain_context,
                context_score=context_score,
                entity_type=entity_data["entity_type"]
            )
            index.entities[key] = semantic_entity

        # Reconstruct workflows
        for workflow_data in data["workflows"]:
            from core.workflow_detector import WorkflowStep, WorkflowHint
            steps = [
                WorkflowStep(
                    entity_name=s["entity_name"],
                    file_path=s["file_path"],
                    domain_tags=s["domain_tags"],
                    role=s["role"]
                )
                for s in workflow_data["steps"]
            ]

            workflow = WorkflowHint(
                name=workflow_data["name"],
                steps=steps,
                confidence=workflow_data["confidence"],
                reasoning=workflow_data["reasoning"],
                business_process=workflow_data["business_process"]
            )
            index.workflows.append(workflow)

        index.metadata = data["metadata"]

        logger.info(f"Loaded semantic index from {input_path}")
        return index
