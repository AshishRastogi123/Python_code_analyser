"""
Domain-aware tagging for accounting concepts.

This module provides rule-based classification of files and functions
into accounting domain concepts like ledger, journal_entry, etc.

Design:
- Lightweight, explainable rules based on file paths, names, docstrings
- No ML or complex heuristics
- Configurable tag definitions
- Separate from AST extraction layer
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from pathlib import Path
import re

from core.models import FileAnalysis, Entity, EntityType
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DomainTag:
    """
    Represents a domain tag with confidence and reasoning.

    Attributes:
        tag: The accounting concept (e.g., 'ledger', 'journal_entry')
        confidence: Confidence score 0.0-1.0
        reasoning: List of reasons why this tag was applied
    """
    tag: str
    confidence: float
    reasoning: List[str] = field(default_factory=list)


@dataclass
class DomainContext:
    """
    Semantic context for a file or entity.

    Attributes:
        tags: List of domain tags
        primary_tag: Most relevant tag
        is_accounting_related: Whether this appears accounting-related
    """
    tags: List[DomainTag] = field(default_factory=list)
    primary_tag: Optional[str] = None
    is_accounting_related: bool = False


class DomainTagger:
    """
    Tags files and entities with accounting domain concepts.

    Uses rule-based matching on:
    - File paths and names
    - Function/class names
    - Docstrings
    - Import usage
    """

    # Accounting domain concepts to detect
    ACCOUNTING_CONCEPTS = {
        "ledger": [
            "ledger", "posting", "entry", "debit", "credit", "balance",
            "general_ledger", "gl_entry", "ledger_entry"
        ],
        "journal_entry": [
            "journal", "jv", "journal_entry", "journal_voucher",
            "accounting_entry", "entry"
        ],
        "trial_balance": [
            "trial_balance", "trial", "balance_sheet", "balances"
        ],
        "profit_and_loss": [
            "profit_loss", "pnl", "income_statement", "profit", "loss"
        ],
        "reconciliation": [
            "reconcile", "reconciliation", "matching", "clearance"
        ],
        "tax": [
            "tax", "gst", "vat", "taxation", "tax_entry"
        ],
        "invoice": [
            "invoice", "billing", "bill", "sales_invoice", "purchase_invoice"
        ],
        "payment": [
            "payment", "pay", "settlement", "payment_entry"
        ],
        "deferred_revenue": [
            "deferred", "revenue", "accrual", "deferred_revenue"
        ],
        "reports": [
            "report", "reporting", "financial_report", "statement"
        ]
    }

    # File path patterns that indicate accounting modules
    ACCOUNTING_PATH_PATTERNS = [
        re.compile(r".*accounts.*", re.IGNORECASE),
        re.compile(r".*accounting.*", re.IGNORECASE),
        re.compile(r".*finance.*", re.IGNORECASE),
        re.compile(r".*ledger.*", re.IGNORECASE),
        re.compile(r".*journal.*", re.IGNORECASE),
        re.compile(r".*erpnext.*accounts.*", re.IGNORECASE),
    ]

    def __init__(self):
        """Initialize tagger with compiled patterns."""
        self.concept_patterns = self._compile_concept_patterns()

    def _compile_concept_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for each accounting concept."""
        patterns = {}
        for concept, keywords in self.ACCOUNTING_CONCEPTS.items():
            patterns[concept] = [
                re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
                for kw in keywords
            ]
        return patterns

    def tag_file(self, file_analysis: FileAnalysis) -> DomainContext:
        """
        Tag a file with accounting domain concepts.

        Args:
            file_analysis: Analysis of the file

        Returns:
            DomainContext with tags and metadata
        """
        context = DomainContext()
        file_path = Path(file_analysis.file_path)
        file_name = file_path.name.lower()

        # Check file path patterns
        path_reasons = []
        for pattern in self.ACCOUNTING_PATH_PATTERNS:
            if pattern.match(str(file_path)):
                path_reasons.append(f"File path matches accounting pattern: {pattern.pattern}")

        if path_reasons:
            context.is_accounting_related = True

        # Check file name for concepts
        name_tags = self._tag_text(file_name, "file name")

        # Check docstrings and names of entities
        entity_tags = []
        for entity in file_analysis.entities:
            if entity.docstring:
                doc_tags = self._tag_text(entity.docstring, f"docstring of {entity.name}")
                entity_tags.extend(doc_tags)

            # Tag entity names
            name_tags.extend(self._tag_text(entity.name, f"name of {entity.name}"))

        # Combine all tags
        all_tags = name_tags + entity_tags

        # Aggregate tags by concept
        tag_scores = {}
        tag_reasons = {}

        for tag in all_tags:
            if tag.tag not in tag_scores:
                tag_scores[tag.tag] = 0
                tag_reasons[tag.tag] = []
            tag_scores[tag.tag] += tag.confidence
            tag_reasons[tag.tag].extend(tag.reasoning)

        # Add path-based confidence boost
        if path_reasons:
            for concept in tag_scores:
                tag_scores[concept] += 0.3  # Boost for path match
                tag_reasons[concept].extend(path_reasons)

        # Create final tags with aggregated confidence
        for concept, score in tag_scores.items():
            confidence = min(score, 1.0)  # Cap at 1.0
            if confidence >= 0.1:  # Minimum threshold
                context.tags.append(DomainTag(
                    tag=concept,
                    confidence=confidence,
                    reasoning=tag_reasons[concept]
                ))

        # Sort by confidence
        context.tags.sort(key=lambda t: t.confidence, reverse=True)

        # Set primary tag
        if context.tags:
            context.primary_tag = context.tags[0].tag
            context.is_accounting_related = True

        logger.debug(f"Tagged {file_path.name}: {len(context.tags)} tags, primary: {context.primary_tag}")
        return context

    def _tag_text(self, text: str, source: str) -> List[DomainTag]:
        """
        Tag text using concept patterns.

        Args:
            text: Text to analyze
            source: Description of text source for reasoning

        Returns:
            List of domain tags found
        """
        tags = []
        text_lower = text.lower()

        for concept, patterns in self.concept_patterns.items():
            matches = []
            for pattern in patterns:
                if pattern.search(text_lower):
                    matches.append(pattern.pattern)

            if matches:
                # Calculate confidence based on number of matches
                confidence = min(len(matches) * 0.2, 0.8)  # Max 0.8 for text matches
                reasoning = [f"Found {len(matches)} keyword matches in {source}: {', '.join(matches[:3])}"]
                if len(matches) > 3:
                    reasoning[0] += f" (and {len(matches)-3} more)"

                tags.append(DomainTag(
                    tag=concept,
                    confidence=confidence,
                    reasoning=reasoning
                ))

        return tags

    def tag_entity(self, entity: Entity) -> DomainContext:
        """
        Tag an individual entity (function/class).

        Args:
            entity: The entity to tag

        Returns:
            DomainContext for the entity
        """
        context = DomainContext()

        # Tag based on name
        name_tags = self._tag_text(entity.name, "entity name")

        # Tag based on docstring
        doc_tags = []
        if entity.docstring:
            doc_tags = self._tag_text(entity.docstring, "docstring")

        # Combine
        all_tags = name_tags + doc_tags

        # Aggregate as above
        tag_scores = {}
        tag_reasons = {}

        for tag in all_tags:
            if tag.tag not in tag_scores:
                tag_scores[tag.tag] = 0
                tag_reasons[tag.tag] = []
            tag_scores[tag.tag] += tag.confidence
            tag_reasons[tag.tag].extend(tag.reasoning)

        for concept, score in tag_scores.items():
            confidence = min(score, 1.0)
            if confidence >= 0.1:
                context.tags.append(DomainTag(
                    tag=concept,
                    confidence=confidence,
                    reasoning=tag_reasons[concept]
                ))

        context.tags.sort(key=lambda t: t.confidence, reverse=True)
        if context.tags:
            context.primary_tag = context.tags[0].tag
            context.is_accounting_related = True

        return context
