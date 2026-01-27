"""
Semantic query interface for domain-aware code search.

This module provides natural language querying over semantic indexes,
focusing on accounting workflows and business logic discovery.

Design:
- Query accounting concepts like "ledger posting functions"
- Rank results by relevance and quality scores
- Explain why results match the query
- Support for workflow-aware searches
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
import re
from pathlib import Path

from core.semantic_index import SemanticIndex, SemanticEntity, SemanticFile
from core.domain_tagger import DomainTag
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QueryResult:
    """
    Result of a semantic query.

    Attributes:
        entity_name: Name of the matching entity
        file_path: File containing the entity
        relevance_score: How well this matches the query (0.0-1.0)
        domain_tags: Accounting concepts this entity relates to
        context_score: Quality score (HIGH/MEDIUM/LOW)
        short_context: Brief context about the entity
        reasoning: Why this result was included
    """
    entity_name: str
    file_path: str
    relevance_score: float
    domain_tags: List[str] = field(default_factory=list)
    context_score: str = "UNKNOWN"
    short_context: Optional[str] = None
    reasoning: List[str] = field(default_factory=list)


class SemanticQueryEngine:
    """
    Engine for querying semantic indexes with domain awareness.

    Supports queries like:
    - "ledger posting functions"
    - "journal entry validation"
    - "trial balance calculation"
    - "payment reconciliation"
    """

    def __init__(self, semantic_index: SemanticIndex):
        """
        Initialize query engine with a semantic index.

        Args:
            semantic_index: Pre-built semantic index to query
        """
        self.index = semantic_index
        self._build_search_structures()

    def _build_search_structures(self):
        """Build internal data structures for fast querying."""
        self.entity_search_terms: Dict[str, Set[str]] = {}
        self.file_search_terms: Dict[str, Set[str]] = {}

        # Build entity search terms
        for entity_key, entity in self.index.entities.items():
            terms = self._extract_search_terms_entity(entity)
            self.entity_search_terms[entity_key] = terms

        # Build file search terms
        for file_path, file_info in self.index.files.items():
            terms = self._extract_search_terms_file(file_path, file_info)
            self.file_search_terms[file_path] = terms

    def _extract_search_terms_entity(self, entity: SemanticEntity) -> Set[str]:
        """Extract searchable terms from an entity."""
        terms = set()

        # Add name tokens
        terms.update(self._tokenize_name(entity.name))

        # Add domain tags
        terms.update(tag.tag.lower() for tag in entity.domain_context.tags)

        # Add docstring tokens (if present)
        if entity.domain_context.primary_tag:
            terms.add(entity.domain_context.primary_tag.lower())

        return terms

    def _extract_search_terms_file(self, file_path: str, file_info: SemanticFile) -> Set[str]:
        """Extract searchable terms from a file."""
        terms = set()

        # Add file path tokens
        path_obj = Path(file_path)
        terms.update(self._tokenize_name(path_obj.name))

        # Add domain tags
        terms.update(tag.tag.lower() for tag in file_info.domain_context.tags)

        # Add primary tag
        if file_info.domain_context.primary_tag:
            terms.add(file_info.domain_context.primary_tag.lower())

        return terms

    def _tokenize_name(self, name: str) -> Set[str]:
        """Tokenize a name into searchable terms."""
        # Remove file extension
        name = Path(name).stem

        # Split on underscores and camelCase
        tokens = re.split(r'[_]+|[A-Z][a-z]*', name)

        # Filter and clean tokens
        clean_tokens = set()
        for token in tokens:
            token = token.lower().strip()
            if len(token) > 2:  # Skip very short tokens
                clean_tokens.add(token)

        return clean_tokens

    def query(self, query_string: str, max_results: int = 10) -> List[QueryResult]:
        """
        Execute a semantic query.

        Args:
            query_string: Natural language query
            max_results: Maximum number of results to return

        Returns:
            List of QueryResult objects, ranked by relevance
        """
        logger.info(f"Executing semantic query: '{query_string}'")

        # Tokenize query
        query_terms = self._tokenize_query(query_string)
        logger.debug(f"Query terms: {query_terms}")

        # Score all entities
        scored_results = []

        for entity_key, entity in self.index.entities.items():
            relevance = self._calculate_entity_relevance(entity, query_terms)
            if relevance > 0.0:
                result = self._build_query_result(entity_key, entity, relevance, query_terms)
                scored_results.append(result)

        # Sort by relevance score (descending)
        scored_results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Limit results
        results = scored_results[:max_results]

        logger.info(f"Query returned {len(results)} results")
        return results

    def _tokenize_query(self, query: str) -> Set[str]:
        """Tokenize query string into search terms."""
        # Simple tokenization: split on spaces and clean
        tokens = query.lower().split()
        clean_tokens = set()

        for token in tokens:
            # Remove punctuation
            token = re.sub(r'[^\w]', '', token)
            if len(token) > 2:
                clean_tokens.add(token)

        return clean_tokens

    def _calculate_entity_relevance(self, entity: SemanticEntity, query_terms: Set[str]) -> float:
        """Calculate how relevant an entity is to the query."""
        entity_terms = self.entity_search_terms.get(f"{entity.file_path}::{entity.name}", set())

        # Calculate term overlap
        matching_terms = entity_terms.intersection(query_terms)
        if not matching_terms:
            return 0.0

        # Base relevance from term matches
        term_relevance = len(matching_terms) / len(query_terms)

        # Boost for exact matches in name
        name_lower = entity.name.lower()
        if any(term in name_lower for term in query_terms):
            term_relevance += 0.3

        # Boost for domain relevance
        domain_boost = 0.0
        if entity.domain_context.is_accounting_related:
            domain_boost += 0.2
        if entity.domain_context.primary_tag and any(term in entity.domain_context.primary_tag.lower() for term in query_terms):
            domain_boost += 0.3

        # Boost for quality
        quality_boost = 0.0
        if entity.context_score.overall_score.value == "HIGH":
            quality_boost += 0.1
        elif entity.context_score.overall_score.value == "MEDIUM":
            quality_boost += 0.05

        total_relevance = min(term_relevance + domain_boost + quality_boost, 1.0)
        return total_relevance

    def _build_query_result(self, entity_key: str, entity: SemanticEntity,
                           relevance: float, query_terms: Set[str]) -> QueryResult:
        """Build a QueryResult from an entity and relevance score."""
        # Get domain tags
        domain_tags = [tag.tag for tag in entity.domain_context.tags]

        # Get context score
        context_score = entity.context_score.overall_score.value

        # Build short context
        short_context = None
        if entity.domain_context.primary_tag:
            short_context = f"Primary domain: {entity.domain_context.primary_tag}"

        # Build reasoning
        reasoning = []
        entity_terms = self.entity_search_terms.get(entity_key, set())
        matching_terms = entity_terms.intersection(query_terms)
        if matching_terms:
            reasoning.append(f"Matches query terms: {', '.join(matching_terms)}")

        if entity.domain_context.is_accounting_related:
            reasoning.append("Identified as accounting-related code")

        if entity.context_score.overall_score.value == "HIGH":
            reasoning.append("High-quality, well-documented code")

        return QueryResult(
            entity_name=entity.name,
            file_path=entity.file_path,
            relevance_score=relevance,
            domain_tags=domain_tags,
            context_score=context_score,
            short_context=short_context,
            reasoning=reasoning
        )


def query_semantic_index(query: str, semantic_index: SemanticIndex, max_results: int = 10) -> List[QueryResult]:
    """
    Convenience function to query a semantic index.

    Args:
        query: Natural language query
        semantic_index: SemanticIndex to query
        max_results: Maximum results to return

    Returns:
        List of QueryResult objects
    """
    engine = SemanticQueryEngine(semantic_index)
    return engine.query(query, max_results)
