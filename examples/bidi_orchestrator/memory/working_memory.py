"""
WorkingMemory - Short-term memory with attention scoring.

Provides a sliding-window memory system that automatically evicts
low-attention entries based on recency, importance, and access frequency.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
import heapq


@dataclass
class MemoryEntry:
    """A single memory entry with metadata for attention scoring."""
    key: str
    value: Any
    importance: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl: Optional[timedelta] = field(default_factory=lambda: timedelta(minutes=5))
    tags: List[str] = field(default_factory=list)
    source_agent: str = ""

    def is_expired(self) -> bool:
        """Check if entry has exceeded its TTL."""
        if self.ttl is None:
            return False
        return datetime.now() > self.created_at + self.ttl

    def to_dict(self) -> dict:
        """Convert entry to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
            "tags": self.tags,
            "source_agent": self.source_agent,
        }


class WorkingMemory:
    """
    Short-term memory with attention-based eviction.

    Maintains a fixed-size memory pool where entries are scored
    based on recency, importance, and access frequency. Low-scoring
    entries are automatically evicted when capacity is reached.

    Example:
        memory = WorkingMemory(max_size=20)
        memory.add("user_name", "Alice", importance=0.8)
        name = memory.get("user_name")  # Returns "Alice"
        context = memory.get_context(top_k=5)  # Top 5 entries by attention
    """

    def __init__(
        self,
        max_size: int = 20,
        recency_weight: float = 0.4,
        importance_weight: float = 0.4,
        access_weight: float = 0.2,
        auto_expire: bool = True,
    ):
        """
        Initialize working memory.

        Args:
            max_size: Maximum number of entries to store
            recency_weight: Weight for recency in attention calculation
            importance_weight: Weight for importance in attention calculation
            access_weight: Weight for access count in attention calculation
            auto_expire: Automatically remove expired entries
        """
        self.max_size = max_size
        self.recency_weight = recency_weight
        self.importance_weight = importance_weight
        self.access_weight = access_weight
        self.auto_expire = auto_expire
        self.entries: Dict[str, MemoryEntry] = {}

    def add(
        self,
        key: str,
        value: Any,
        importance: float = 0.5,
        ttl: Optional[timedelta] = None,
        tags: Optional[List[str]] = None,
        source_agent: str = "",
    ) -> bool:
        """
        Add or update an entry in working memory.

        Args:
            key: Unique identifier for the entry
            value: The value to store
            importance: Importance score (0.0 to 1.0)
            ttl: Optional time-to-live override
            tags: Optional tags for categorization
            source_agent: Agent that created this entry

        Returns:
            True if entry was added successfully
        """
        # Clean expired entries if enabled
        if self.auto_expire:
            self._remove_expired()

        # Evict lowest attention entry if at capacity
        if key not in self.entries and len(self.entries) >= self.max_size:
            self._evict_lowest_attention()

        # Create or update entry
        if key in self.entries:
            # Update existing entry
            entry = self.entries[key]
            entry.value = value
            entry.importance = importance
            entry.accessed_at = datetime.now()
            if tags:
                entry.tags = tags
        else:
            # Create new entry
            self.entries[key] = MemoryEntry(
                key=key,
                value=value,
                importance=importance,
                ttl=ttl if ttl is not None else timedelta(minutes=5),
                tags=tags or [],
                source_agent=source_agent,
            )

        return True

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve an entry from working memory.

        Updates access metadata for attention scoring.

        Args:
            key: The entry key to retrieve
            default: Default value if key not found

        Returns:
            The stored value or default
        """
        if key not in self.entries:
            return default

        entry = self.entries[key]

        # Check expiration
        if self.auto_expire and entry.is_expired():
            del self.entries[key]
            return default

        # Update access metadata
        entry.accessed_at = datetime.now()
        entry.access_count += 1

        return entry.value

    def remove(self, key: str) -> bool:
        """Remove an entry from working memory."""
        if key in self.entries:
            del self.entries[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all entries from working memory."""
        self.entries.clear()

    def _calculate_attention(self, entry: MemoryEntry) -> float:
        """
        Calculate attention score for an entry.

        Combines recency, importance, and access frequency.

        Args:
            entry: The memory entry to score

        Returns:
            Attention score (higher = more important to keep)
        """
        # Recency: decays over time (1.0 = just accessed, approaches 0)
        seconds_since_access = (datetime.now() - entry.accessed_at).total_seconds()
        recency = 1.0 / (1 + seconds_since_access / 60)

        # Importance: direct from entry (0.0 to 1.0)
        importance = entry.importance

        # Access frequency: normalized (caps at 10 accesses)
        access_freq = min(entry.access_count / 10, 1.0)

        # Weighted combination
        return (
            self.recency_weight * recency +
            self.importance_weight * importance +
            self.access_weight * access_freq
        )

    def _evict_lowest_attention(self) -> None:
        """Remove the entry with lowest attention score."""
        if not self.entries:
            return

        # Find entry with lowest attention
        lowest = min(self.entries.values(), key=self._calculate_attention)
        del self.entries[lowest.key]

    def _remove_expired(self) -> None:
        """Remove all expired entries."""
        expired_keys = [
            key for key, entry in self.entries.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self.entries[key]

    def get_context(self, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Get top-k entries by attention score for agent context.

        Args:
            top_k: Number of entries to return

        Returns:
            List of entries sorted by attention (highest first)
        """
        if self.auto_expire:
            self._remove_expired()

        # Score and sort all entries
        scored = [
            (self._calculate_attention(entry), entry)
            for entry in self.entries.values()
        ]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return top-k as dicts
        return [
            {"key": entry.key, "value": entry.value, "attention": score}
            for score, entry in scored[:top_k]
        ]

    def get_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get all entries with a specific tag."""
        return [
            entry.to_dict()
            for entry in self.entries.values()
            if tag in entry.tags
        ]

    def get_by_agent(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get all entries created by a specific agent."""
        return [
            entry.to_dict()
            for entry in self.entries.values()
            if entry.source_agent == agent_name
        ]

    def get_context_string(self, top_k: int = 5) -> str:
        """
        Get top-k entries as a formatted string for agent prompts.

        Args:
            top_k: Number of entries to include

        Returns:
            Formatted string with memory context
        """
        context = self.get_context(top_k)
        if not context:
            return ""

        lines = ["Current context:"]
        for entry in context:
            lines.append(f"- {entry['key']}: {entry['value']}")
        return "\n".join(lines)

    def __len__(self) -> int:
        """Return number of entries in memory."""
        return len(self.entries)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in memory."""
        return key in self.entries

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "size": len(self.entries),
            "max_size": self.max_size,
            "utilization": len(self.entries) / self.max_size if self.max_size > 0 else 0,
            "avg_importance": (
                sum(e.importance for e in self.entries.values()) / len(self.entries)
                if self.entries else 0
            ),
            "avg_access_count": (
                sum(e.access_count for e in self.entries.values()) / len(self.entries)
                if self.entries else 0
            ),
        }
