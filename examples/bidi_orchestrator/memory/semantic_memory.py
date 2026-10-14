"""
SemanticMemory - Knowledge graph with concepts and relationships.

Provides a semantic memory system for storing and querying
knowledge as concepts and their relationships.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Set, Tuple
from datetime import datetime
from enum import Enum


class RelationType(Enum):
    """Standard relationship types for semantic memory."""
    IS_A = "is_a"              # Category/inheritance
    HAS = "has"                # Possession/attribute
    PART_OF = "part_of"        # Composition
    RELATED_TO = "related_to"  # General association
    CAUSES = "causes"          # Causation
    PRECEDES = "precedes"      # Temporal ordering
    LOCATED_IN = "located_in"  # Spatial relationship
    CREATED_BY = "created_by"  # Creation/origin
    SIMILAR_TO = "similar_to"  # Similarity
    OPPOSITE_OF = "opposite_of"# Opposition


@dataclass
class Concept:
    """A concept node in the semantic memory graph."""
    id: str
    name: str
    description: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    importance: float = 0.5
    source_agent: str = ""

    def to_dict(self) -> dict:
        """Convert concept to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat(),
            "importance": self.importance,
            "source_agent": self.source_agent,
        }


@dataclass
class Relationship:
    """A relationship edge between concepts."""
    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    source_agent: str = ""

    def to_dict(self) -> dict:
        """Convert relationship to dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "source_agent": self.source_agent,
        }


class SemanticMemory:
    """
    Knowledge graph with concepts and relationships.

    Stores knowledge as a graph of concepts connected by typed
    relationships. Supports queries, path finding, and inference.

    Example:
        memory = SemanticMemory()
        memory.add_concept("python", "Python", "Programming language")
        memory.add_concept("ml", "Machine Learning", "AI discipline")
        memory.add_relationship("python", "ml", "used_for")
        related = memory.get_related("python")
    """

    def __init__(self):
        """Initialize semantic memory."""
        self.concepts: Dict[str, Concept] = {}
        self.relationships: List[Relationship] = []
        self._outgoing: Dict[str, List[Relationship]] = {}  # source_id -> relationships
        self._incoming: Dict[str, List[Relationship]] = {}  # target_id -> relationships

    def add_concept(
        self,
        concept_id: str,
        name: str,
        description: str = "",
        attributes: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
        source_agent: str = "",
    ) -> Concept:
        """
        Add a concept to semantic memory.

        Args:
            concept_id: Unique identifier
            name: Human-readable name
            description: Description of the concept
            attributes: Additional attributes
            importance: Importance score (0.0 to 1.0)
            source_agent: Agent that created this concept

        Returns:
            The created Concept
        """
        if concept_id in self.concepts:
            # Update existing concept
            concept = self.concepts[concept_id]
            concept.name = name
            concept.description = description
            if attributes:
                concept.attributes.update(attributes)
            concept.importance = importance
            concept.updated_at = datetime.now()
        else:
            # Create new concept
            concept = Concept(
                id=concept_id,
                name=name,
                description=description,
                attributes=attributes or {},
                importance=importance,
                source_agent=source_agent,
            )
            self.concepts[concept_id] = concept
            self._outgoing[concept_id] = []
            self._incoming[concept_id] = []

        return concept

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get a concept by ID."""
        return self.concepts.get(concept_id)

    def remove_concept(self, concept_id: str) -> bool:
        """Remove a concept and all its relationships."""
        if concept_id not in self.concepts:
            return False

        # Remove relationships
        self.relationships = [
            r for r in self.relationships
            if r.source_id != concept_id and r.target_id != concept_id
        ]

        # Update indices
        if concept_id in self._outgoing:
            del self._outgoing[concept_id]
        if concept_id in self._incoming:
            del self._incoming[concept_id]

        # Remove from other indices
        for cid in self._outgoing:
            self._outgoing[cid] = [
                r for r in self._outgoing[cid]
                if r.target_id != concept_id
            ]
        for cid in self._incoming:
            self._incoming[cid] = [
                r for r in self._incoming[cid]
                if r.source_id != concept_id
            ]

        # Remove concept
        del self.concepts[concept_id]
        return True

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
        source_agent: str = "",
    ) -> Optional[Relationship]:
        """
        Add a relationship between concepts.

        Args:
            source_id: Source concept ID
            target_id: Target concept ID
            relation_type: Type of relationship
            weight: Relationship strength (0.0 to 1.0)
            properties: Additional properties
            source_agent: Agent that created this relationship

        Returns:
            The created Relationship or None if concepts don't exist
        """
        # Verify concepts exist
        if source_id not in self.concepts or target_id not in self.concepts:
            return None

        # Check for existing relationship
        for rel in self._outgoing.get(source_id, []):
            if rel.target_id == target_id and rel.relation_type == relation_type:
                # Update existing
                rel.weight = weight
                if properties:
                    rel.properties.update(properties)
                return rel

        # Create new relationship
        relationship = Relationship(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            properties=properties or {},
            source_agent=source_agent,
        )

        self.relationships.append(relationship)
        self._outgoing[source_id].append(relationship)
        self._incoming[target_id].append(relationship)

        return relationship

    def get_related(
        self,
        concept_id: str,
        relation_type: Optional[str] = None,
        direction: str = "both",
    ) -> List[Tuple[Concept, Relationship]]:
        """
        Get concepts related to a given concept.

        Args:
            concept_id: The concept to find relations for
            relation_type: Filter by relationship type
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of (Concept, Relationship) tuples
        """
        results = []

        if direction in ("outgoing", "both"):
            for rel in self._outgoing.get(concept_id, []):
                if relation_type is None or rel.relation_type == relation_type:
                    target = self.concepts.get(rel.target_id)
                    if target:
                        results.append((target, rel))

        if direction in ("incoming", "both"):
            for rel in self._incoming.get(concept_id, []):
                if relation_type is None or rel.relation_type == relation_type:
                    source = self.concepts.get(rel.source_id)
                    if source:
                        results.append((source, rel))

        return results

    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
    ) -> Optional[List[Tuple[Concept, Optional[Relationship]]]]:
        """
        Find a path between two concepts using BFS.

        Args:
            start_id: Starting concept ID
            end_id: Target concept ID
            max_depth: Maximum path length

        Returns:
            List of (Concept, Relationship) tuples or None if no path
        """
        if start_id not in self.concepts or end_id not in self.concepts:
            return None

        if start_id == end_id:
            return [(self.concepts[start_id], None)]

        # BFS
        visited = {start_id}
        queue = [(start_id, [(self.concepts[start_id], None)])]

        while queue:
            current_id, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            for rel in self._outgoing.get(current_id, []):
                next_id = rel.target_id
                if next_id in visited:
                    continue

                visited.add(next_id)
                new_path = path + [(self.concepts[next_id], rel)]

                if next_id == end_id:
                    return new_path

                queue.append((next_id, new_path))

        return None

    def query(
        self,
        name_contains: Optional[str] = None,
        has_attribute: Optional[str] = None,
        min_importance: float = 0.0,
        source_agent: Optional[str] = None,
    ) -> List[Concept]:
        """
        Query concepts by various criteria.

        Args:
            name_contains: Filter by name substring
            has_attribute: Filter by attribute key
            min_importance: Minimum importance score
            source_agent: Filter by creating agent

        Returns:
            List of matching concepts
        """
        results = []

        for concept in self.concepts.values():
            # Apply filters
            if name_contains and name_contains.lower() not in concept.name.lower():
                continue
            if has_attribute and has_attribute not in concept.attributes:
                continue
            if concept.importance < min_importance:
                continue
            if source_agent and concept.source_agent != source_agent:
                continue

            results.append(concept)

        return results

    def infer_transitive(
        self,
        concept_id: str,
        relation_type: str,
        max_depth: int = 3,
    ) -> List[Concept]:
        """
        Infer transitive relationships (e.g., A is_a B, B is_a C -> A is_a C).

        Args:
            concept_id: Starting concept
            relation_type: Relationship type to follow
            max_depth: Maximum inference depth

        Returns:
            List of transitively related concepts
        """
        if concept_id not in self.concepts:
            return []

        results = []
        visited = {concept_id}
        current_level = [concept_id]

        for _ in range(max_depth):
            next_level = []
            for cid in current_level:
                for rel in self._outgoing.get(cid, []):
                    if rel.relation_type == relation_type and rel.target_id not in visited:
                        visited.add(rel.target_id)
                        next_level.append(rel.target_id)
                        results.append(self.concepts[rel.target_id])

            if not next_level:
                break
            current_level = next_level

        return results

    def get_context_string(self, concept_ids: List[str]) -> str:
        """
        Get a formatted string of concepts and their relationships.

        Args:
            concept_ids: List of concept IDs to include

        Returns:
            Formatted knowledge context string
        """
        lines = ["Knowledge context:"]

        for cid in concept_ids:
            concept = self.concepts.get(cid)
            if not concept:
                continue

            lines.append(f"\n{concept.name}: {concept.description}")

            # Add relationships
            for target, rel in self.get_related(cid, direction="outgoing"):
                lines.append(f"  - {rel.relation_type} -> {target.name}")

        return "\n".join(lines)

    def __len__(self) -> int:
        """Return number of concepts."""
        return len(self.concepts)

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "concept_count": len(self.concepts),
            "relationship_count": len(self.relationships),
            "avg_connections": (
                len(self.relationships) * 2 / len(self.concepts)
                if self.concepts else 0
            ),
            "relationship_types": list(set(r.relation_type for r in self.relationships)),
        }
