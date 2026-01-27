"""
Context quality scoring for code analysis.

This module provides rule-based quality assessment of files and entities
to help prioritize modernization efforts.

Design:
- Lightweight, explainable scoring rules
- Focus on domain relevance, connectivity, and documentation
- Separate from AST extraction layer
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum
from pathlib import Path

from core.models import FileAnalysis, Entity, EntityType, Relationship, RelationType, ProjectAnalysis
from utils.logger import get_logger

logger = get_logger(__name__)


class QualityScore(str, Enum):
    """Quality score levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class ContextScore:
    """
    Quality score for a file or entity.

    Attributes:
        overall_score: Overall quality assessment
        domain_relevance: How relevant to accounting domain (0.0-1.0)
        relationship_density: How connected the code is (0.0-1.0)
        docstring_quality: Quality of documentation (0.0-1.0)
        test_coverage: Presence of test files/functions (0.0-1.0)
        reasoning: List of reasons for the score
    """
    overall_score: QualityScore
    domain_relevance: float = 0.0
    relationship_density: float = 0.0
    docstring_quality: float = 0.0
    test_coverage: float = 0.0
    reasoning: List[str] = field(default_factory=list)


class ContextScorer:
    """
    Scores code quality based on multiple dimensions.

    Uses rule-based heuristics to assess:
    - Domain relevance (accounting concepts)
    - Relationship density (code connectivity)
    - Documentation quality
    - Test coverage presence
    """

    def __init__(self):
        """Initialize scorer."""
        pass

    def score_file(self, file_analysis: FileAnalysis, project_analysis: 'ProjectAnalysis') -> ContextScore:
        """
        Score a file's overall quality.

        Args:
            file_analysis: Analysis of the file
            project_analysis: Full project context

        Returns:
            ContextScore for the file
        """
        reasoning = []

        # Domain relevance: based on file path and content
        domain_relevance = self._calculate_domain_relevance_file(file_analysis)
        if domain_relevance > 0.7:
            reasoning.append("High domain relevance - appears to be core accounting logic")
        elif domain_relevance > 0.3:
            reasoning.append("Medium domain relevance - contains some accounting concepts")
        else:
            reasoning.append("Low domain relevance - utility or generic code")

        # Relationship density: how connected this file is
        relationship_density = self._calculate_relationship_density_file(file_analysis, project_analysis)
        if relationship_density > 0.7:
            reasoning.append("High connectivity - central to the codebase")
        elif relationship_density > 0.3:
            reasoning.append("Medium connectivity - moderately connected")
        else:
            reasoning.append("Low connectivity - peripheral code")

        # Docstring quality: average docstring presence and length
        docstring_quality = self._calculate_docstring_quality_file(file_analysis)
        if docstring_quality > 0.7:
            reasoning.append("Well documented - good docstring coverage")
        elif docstring_quality > 0.3:
            reasoning.append("Partially documented - some docstrings present")
        else:
            reasoning.append("Poorly documented - missing docstrings")

        # Test coverage: heuristic based on file naming
        test_coverage = self._calculate_test_coverage_file(file_analysis)
        if test_coverage > 0.5:
            reasoning.append("Likely well tested - test file or test-related")
        else:
            reasoning.append("Test coverage unclear - not identified as test code")

        # Overall score calculation
        overall_score = self._calculate_overall_score_file(
            domain_relevance, relationship_density, docstring_quality, test_coverage
        )

        return ContextScore(
            overall_score=overall_score,
            domain_relevance=domain_relevance,
            relationship_density=relationship_density,
            docstring_quality=docstring_quality,
            test_coverage=test_coverage,
            reasoning=reasoning
        )

    def score_entity(self, entity: Entity, file_analysis: FileAnalysis, project_analysis: 'ProjectAnalysis') -> ContextScore:
        """
        Score an entity's quality.

        Args:
            entity: The entity to score
            file_analysis: Analysis of the containing file
            project_analysis: Full project context

        Returns:
            ContextScore for the entity
        """
        reasoning = []

        # Domain relevance: based on entity name and docstring
        domain_relevance = self._calculate_domain_relevance_entity(entity)
        if domain_relevance > 0.7:
            reasoning.append("High domain relevance - core accounting function/class")
        elif domain_relevance > 0.3:
            reasoning.append("Medium domain relevance - accounting-related")
        else:
            reasoning.append("Low domain relevance - utility function")

        # Relationship density: how many relationships this entity has
        relationship_density = self._calculate_relationship_density_entity(entity, file_analysis, project_analysis)
        if relationship_density > 0.7:
            reasoning.append("Highly connected - called by many other functions")
        elif relationship_density > 0.3:
            reasoning.append("Moderately connected - has some dependencies")
        else:
            reasoning.append("Low connectivity - rarely used")

        # Docstring quality: presence and quality of docstring
        docstring_quality = self._calculate_docstring_quality_entity(entity)
        if docstring_quality > 0.8:
            reasoning.append("Well documented - comprehensive docstring")
        elif docstring_quality > 0.4:
            reasoning.append("Partially documented - basic docstring")
        else:
            reasoning.append("Undocumented - missing or poor docstring")

        # Test coverage: heuristic (harder to determine for individual entities)
        test_coverage = 0.0  # Default low for entities
        reasoning.append("Test coverage assessment requires test file analysis")

        # Overall score
        overall_score = self._calculate_overall_score_entity(
            domain_relevance, relationship_density, docstring_quality, test_coverage
        )

        return ContextScore(
            overall_score=overall_score,
            domain_relevance=domain_relevance,
            relationship_density=relationship_density,
            docstring_quality=docstring_quality,
            test_coverage=test_coverage,
            reasoning=reasoning
        )

    def _calculate_domain_relevance_file(self, file_analysis: FileAnalysis) -> float:
        """Calculate domain relevance for a file."""
        file_path = Path(file_analysis.file_path).name.lower()

        # Check file name for accounting keywords
        accounting_keywords = [
            'account', 'ledger', 'journal', 'invoice', 'payment', 'tax',
            'balance', 'posting', 'transaction', 'finance', 'erp'
        ]

        keyword_matches = sum(1 for kw in accounting_keywords if kw in file_path)
        base_score = min(keyword_matches * 0.2, 0.6)  # Max 0.6 from filename

        # Boost if file has many entities (likely core business logic)
        entity_boost = min(len(file_analysis.entities) * 0.02, 0.3)

        # Boost if file has relationships (connected to business logic)
        relationship_boost = min(len(file_analysis.relationships) * 0.01, 0.1)

        return min(base_score + entity_boost + relationship_boost, 1.0)

    def _calculate_domain_relevance_entity(self, entity: Entity) -> float:
        """Calculate domain relevance for an entity."""
        name_lower = entity.name.lower()
        docstring_lower = (entity.docstring or "").lower()

        # Accounting keywords in name or docstring
        accounting_keywords = [
            'account', 'ledger', 'journal', 'invoice', 'payment', 'tax',
            'balance', 'posting', 'transaction', 'debit', 'credit', 'gl'
        ]

        name_matches = sum(1 for kw in accounting_keywords if kw in name_lower)
        doc_matches = sum(1 for kw in accounting_keywords if kw in docstring_lower)

        # Score based on matches
        score = min((name_matches * 0.3) + (doc_matches * 0.2), 1.0)

        # Boost for functions with business-sounding names
        if any(term in name_lower for term in ['create', 'post', 'validate', 'calculate', 'process']):
            score = min(score + 0.2, 1.0)

        return score

    def _calculate_relationship_density_file(self, file_analysis: FileAnalysis, project_analysis: 'ProjectAnalysis') -> float:
        """Calculate relationship density for a file."""
        # Count relationships involving entities in this file
        file_entity_names = {e.name for e in file_analysis.entities}
        related_relationships = 0

        for rel in project_analysis.all_relationships:
            if rel.source in file_entity_names or rel.target in file_entity_names:
                related_relationships += 1

        # Also count internal relationships
        internal_relationships = len(file_analysis.relationships)

        total_relationships = related_relationships + internal_relationships

        # Normalize by number of entities (more entities = potentially more relationships)
        if len(file_analysis.entities) == 0:
            return 0.0

        density = total_relationships / len(file_analysis.entities)
        return min(density * 0.1, 1.0)  # Scale down and cap

    def _calculate_relationship_density_entity(self, entity: Entity, file_analysis: FileAnalysis, project_analysis: 'ProjectAnalysis') -> float:
        """Calculate relationship density for an entity."""
        # Count relationships where this entity is source or target
        relationship_count = 0

        for rel in file_analysis.relationships:
            if rel.source == entity.name or rel.target == entity.name:
                relationship_count += 1

        # Also check cross-file relationships
        for rel in project_analysis.all_relationships:
            if rel.source == entity.name or rel.target == entity.name:
                relationship_count += 1

        # Normalize (higher count = higher density)
        density = min(relationship_count * 0.2, 1.0)
        return density

    def _calculate_docstring_quality_file(self, file_analysis: FileAnalysis) -> float:
        """Calculate docstring quality for a file."""
        if not file_analysis.entities:
            return 0.0

        entities_with_docstrings = sum(1 for e in file_analysis.entities if e.docstring)
        coverage = entities_with_docstrings / len(file_analysis.entities)

        # Average docstring length (rough quality proxy)
        total_length = sum(len(e.docstring or "") for e in file_analysis.entities)
        avg_length = total_length / len(file_analysis.entities)

        length_score = min(avg_length * 0.001, 0.5)  # Cap at 0.5

        return min(coverage * 0.5 + length_score, 1.0)

    def _calculate_docstring_quality_entity(self, entity: Entity) -> float:
        """Calculate docstring quality for an entity."""
        if not entity.docstring:
            return 0.0

        docstring = entity.docstring.strip()

        # Length score
        length_score = min(len(docstring) * 0.002, 0.6)  # Cap at 0.6

        # Content quality heuristics
        content_score = 0.0
        if len(docstring.split()) > 5:  # More than 5 words
            content_score += 0.2
        if 'Args:' in docstring or 'Returns:' in docstring:  # Structured
            content_score += 0.2
        if any(term in docstring.lower() for term in ['function', 'class', 'method', 'calculate', 'create', 'validate']):
            content_score += 0.2

        return min(length_score + content_score, 1.0)

    def _calculate_test_coverage_file(self, file_analysis: FileAnalysis) -> float:
        """Calculate test coverage heuristic for a file."""
        file_path = Path(file_analysis.file_path)

        # Check file path for test indicators
        path_parts = file_path.parts
        if any('test' in part.lower() for part in path_parts):
            return 0.8

        # Check function names for test patterns
        test_functions = sum(1 for e in file_analysis.entities
                           if isinstance(e, Entity) and e.type == EntityType.FUNCTION
                           and e.name.lower().startswith(('test_', 'test')))

        if test_functions > 0:
            return 0.6

        return 0.0  # Unknown/unclear

    def _calculate_overall_score_file(self, domain_rel: float, rel_density: float,
                                    doc_quality: float, test_cov: float) -> QualityScore:
        """Calculate overall quality score for a file."""
        # Weighted average
        score = (domain_rel * 0.4 + rel_density * 0.3 +
                doc_quality * 0.2 + test_cov * 0.1)

        if score >= 0.7:
            return QualityScore.HIGH
        elif score >= 0.4:
            return QualityScore.MEDIUM
        else:
            return QualityScore.LOW

    def _calculate_overall_score_entity(self, domain_rel: float, rel_density: float,
                                      doc_quality: float, test_cov: float) -> QualityScore:
        """Calculate overall quality score for an entity."""
        # Similar weights but emphasize documentation for entities
        score = (domain_rel * 0.3 + rel_density * 0.3 +
                doc_quality * 0.3 + test_cov * 0.1)

        if score >= 0.7:
            return QualityScore.HIGH
        elif score >= 0.4:
            return QualityScore.MEDIUM
        else:
            return QualityScore.LOW
