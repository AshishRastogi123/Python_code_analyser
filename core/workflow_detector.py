"""
Workflow inference for accounting processes.

This module detects high-level workflows and responsibilities
by analyzing relationships between tagged entities.

Design:
- Rule-based workflow patterns
- Focus on accounting process flows
- Explainable inferences
- Separate from AST extraction
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

from core.models import ProjectAnalysis, Relationship, RelationType
from core.domain_tagger import DomainContext, DomainTagger
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowStep:
    """
    A step in an accounting workflow.

    Attributes:
        entity_name: Name of the entity (function/class)
        file_path: File containing the entity
        domain_tags: Accounting concepts this step relates to
        role: Role in workflow (e.g., 'creator', 'validator', 'processor')
    """
    entity_name: str
    file_path: str
    domain_tags: List[str] = field(default_factory=list)
    role: Optional[str] = None


@dataclass
class WorkflowHint:
    """
    Inferred workflow between entities.

    Attributes:
        name: Descriptive name of the workflow
        steps: Sequence of workflow steps
        confidence: Confidence in this workflow inference
        reasoning: Explanation of how this was inferred
        business_process: High-level business process (e.g., 'ledger_posting')
    """
    name: str
    steps: List[WorkflowStep] = field(default_factory=list)
    confidence: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    business_process: Optional[str] = None


class WorkflowDetector:
    """
    Detects accounting workflows from code relationships.

    Analyzes call relationships and domain tags to infer
    business processes like journal entry -> ledger posting.
    """

    # Known workflow patterns
    WORKFLOW_PATTERNS = {
        "journal_to_ledger": {
            "start_concepts": ["journal_entry"],
            "end_concepts": ["ledger", "general_ledger"],
            "intermediate_concepts": ["posting", "entry"],
            "business_process": "ledger_posting"
        },
        "invoice_to_payment": {
            "start_concepts": ["invoice"],
            "end_concepts": ["payment"],
            "intermediate_concepts": ["reconciliation"],
            "business_process": "payment_processing"
        },
        "ledger_to_reports": {
            "start_concepts": ["ledger", "general_ledger"],
            "end_concepts": ["reports", "trial_balance", "profit_and_loss"],
            "intermediate_concepts": ["calculation", "aggregation"],
            "business_process": "financial_reporting"
        },
        "tax_calculation": {
            "start_concepts": ["invoice", "payment"],
            "end_concepts": ["tax"],
            "intermediate_concepts": ["calculation"],
            "business_process": "tax_processing"
        }
    }

    def __init__(self):
        """Initialize workflow detector."""
        self.tagger = DomainTagger()

    def detect_workflows(self, project_analysis: ProjectAnalysis) -> List[WorkflowHint]:
        """
        Detect workflows across the entire project.

        Args:
            project_analysis: Complete project analysis

        Returns:
            List of inferred workflow hints
        """
        logger.info("Starting workflow detection")

        # Build entity context map
        entity_contexts = self._build_entity_contexts(project_analysis)

        # Build call graph
        call_graph = self._build_call_graph(project_analysis.all_relationships)

        # Detect workflows using patterns
        workflows = []
        for pattern_name, pattern in self.WORKFLOW_PATTERNS.items():
            pattern_workflows = self._detect_pattern_workflows(
                pattern_name, pattern, entity_contexts, call_graph
            )
            workflows.extend(pattern_workflows)

        logger.info(f"Detected {len(workflows)} workflow hints")
        return workflows

    def _build_entity_contexts(self, project_analysis: ProjectAnalysis) -> Dict[str, Tuple[str, DomainContext]]:
        """
        Build mapping of entity names to their file paths and domain contexts.

        Args:
            project_analysis: Project analysis

        Returns:
            Dict[entity_name, (file_path, domain_context)]
        """
        contexts = {}

        for file_analysis in project_analysis.file_analyses:
            file_context = self.tagger.tag_file(file_analysis)

            for entity in file_analysis.entities:
                entity_context = self.tagger.tag_entity(entity)
                contexts[entity.name] = (file_analysis.file_path, entity_context)

        return contexts

    def _build_call_graph(self, relationships: List[Relationship]) -> Dict[str, Set[str]]:
        """
        Build call graph from relationships.

        Args:
            relationships: All relationships

        Returns:
            Dict[caller, set(callees)]
        """
        graph = defaultdict(set)

        for rel in relationships:
            if rel.type == RelationType.CALLS:
                graph[rel.source].add(rel.target)

        return graph

    def _detect_pattern_workflows(
        self,
        pattern_name: str,
        pattern: Dict,
        entity_contexts: Dict[str, Tuple[str, DomainContext]],
        call_graph: Dict[str, Set[str]]
    ) -> List[WorkflowHint]:
        """
        Detect workflows matching a specific pattern.

        Args:
            pattern_name: Name of the pattern
            pattern: Pattern definition
            entity_contexts: Entity contexts
            call_graph: Call relationships

        Returns:
            List of matching workflow hints
        """
        workflows = []

        # Find potential start entities
        start_entities = self._find_entities_by_concepts(
            pattern["start_concepts"], entity_contexts
        )

        # Find potential end entities
        end_entities = self._find_entities_by_concepts(
            pattern["end_concepts"], entity_contexts
        )

        # For each start-end pair, try to find a path
        for start_entity in start_entities:
            for end_entity in end_entities:
                if start_entity == end_entity:
                    continue

                path = self._find_workflow_path(
                    start_entity, end_entity, call_graph,
                    pattern.get("intermediate_concepts", [])
                )

                if path:
                    workflow = self._build_workflow_hint(
                        pattern_name, pattern, path, entity_contexts
                    )
                    if workflow:
                        workflows.append(workflow)

        return workflows

    def _find_entities_by_concepts(
        self,
        concepts: List[str],
        entity_contexts: Dict[str, Tuple[str, DomainContext]]
    ) -> List[str]:
        """
        Find entities that match given concepts.

        Args:
            concepts: List of concept names
            entity_contexts: Entity contexts

        Returns:
            List of matching entity names
        """
        matches = []
        for entity_name, (file_path, context) in entity_contexts.items():
            if context.primary_tag in concepts:
                matches.append(entity_name)
        return matches

    def _find_workflow_path(
        self,
        start: str,
        end: str,
        call_graph: Dict[str, Set[str]],
        intermediate_concepts: List[str]
    ) -> Optional[List[str]]:
        """
        Find a path from start to end entity in call graph.

        Args:
            start: Starting entity
            end: Ending entity
            call_graph: Call relationships
            intermediate_concepts: Concepts that can be intermediate steps

        Returns:
            Path as list of entity names, or None if no path found
        """
        # Simple BFS to find path (could be optimized)
        visited = set()
        queue = [(start, [start])]

        while queue:
            current, path = queue.pop(0)

            if current == end:
                return path

            if current in visited:
                continue
            visited.add(current)

            for neighbor in call_graph.get(current, set()):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        return None

    def _build_workflow_hint(
        self,
        pattern_name: str,
        pattern: Dict,
        path: List[str],
        entity_contexts: Dict[str, Tuple[str, DomainContext]]
    ) -> Optional[WorkflowHint]:
        """
        Build a workflow hint from a found path.

        Args:
            pattern_name: Name of the pattern
            pattern: Pattern definition
            path: Entity path
            entity_contexts: Entity contexts

        Returns:
            WorkflowHint or None if invalid
        """
        if len(path) < 2:
            return None

        steps = []
        total_confidence = 0.0
        reasoning = []

        for entity_name in path:
            if entity_name not in entity_contexts:
                continue

            file_path, context = entity_contexts[entity_name]

            # Determine role based on position
            role = None
            if entity_name == path[0]:
                role = "initiator"
            elif entity_name == path[-1]:
                role = "finalizer"
            else:
                role = "processor"

            step = WorkflowStep(
                entity_name=entity_name,
                file_path=file_path,
                domain_tags=[tag.tag for tag in context.tags],
                role=role
            )
            steps.append(step)

            # Accumulate confidence
            if context.tags:
                total_confidence += context.tags[0].confidence

        if not steps:
            return None

        # Average confidence
        avg_confidence = total_confidence / len(steps)

        # Build reasoning
        reasoning.append(f"Found call path: {' -> '.join(path)}")
        reasoning.append(f"Matches {pattern_name} pattern")
        reasoning.append(f"Business process: {pattern.get('business_process', 'unknown')}")

        workflow = WorkflowHint(
            name=f"{pattern_name}: {' -> '.join([s.entity_name for s in steps])}",
            steps=steps,
            confidence=min(avg_confidence, 1.0),
            reasoning=reasoning,
            business_process=pattern.get("business_process")
        )

        return workflow
