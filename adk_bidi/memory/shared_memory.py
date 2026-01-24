"""
SharedMemory - Cross-agent shared state with conflict resolution.

Provides a thread-safe shared memory system for multi-agent
coordination with locking, versioning, and subscription support.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List, Callable, Awaitable
from datetime import datetime
from enum import Enum


class ConflictStrategy(Enum):
    """Strategies for resolving write conflicts."""
    LAST_WRITE_WINS = "last_write_wins"    # Most recent write takes precedence
    FIRST_WRITE_WINS = "first_write_wins"  # First write is preserved
    MERGE = "merge"                         # Attempt to merge (for dicts/lists)
    REJECT = "reject"                       # Reject conflicting writes


@dataclass
class SharedValue:
    """A value in shared memory with metadata."""
    value: Any
    version: int = 0
    owner_agent: str = ""
    readers: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    write_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "value": self.value,
            "version": self.version,
            "owner_agent": self.owner_agent,
            "readers": self.readers,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "write_count": self.write_count,
        }


# Type alias for subscription callbacks
SubscriptionCallback = Callable[[str, Any, str], Awaitable[None]]


class SharedMemory:
    """
    Cross-agent shared state with conflict resolution.

    Provides a thread-safe memory space that multiple agents can
    read and write to, with configurable conflict resolution,
    locking, and change notification support.

    Example:
        memory = SharedMemory(conflict_strategy=ConflictStrategy.LAST_WRITE_WINS)

        await memory.write("task_status", "in_progress", agent_id="agent1")
        status = await memory.read("task_status", agent_id="agent2")

        # Subscribe to changes
        async def on_change(key, value, agent_id):
            print(f"Key {key} changed to {value} by {agent_id}")
        memory.subscribe("task_status", on_change)
    """

    def __init__(
        self,
        conflict_strategy: ConflictStrategy = ConflictStrategy.LAST_WRITE_WINS,
        lock_timeout: float = 30.0,
    ):
        """
        Initialize shared memory.

        Args:
            conflict_strategy: Strategy for handling write conflicts
            lock_timeout: Timeout for acquiring locks (seconds)
        """
        self.conflict_strategy = conflict_strategy
        self.lock_timeout = lock_timeout
        self.store: Dict[str, SharedValue] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
        self.subscribers: Dict[str, List[SubscriptionCallback]] = {}
        self._global_lock = asyncio.Lock()

    async def write(
        self,
        key: str,
        value: Any,
        agent_id: str,
        expected_version: Optional[int] = None,
    ) -> bool:
        """
        Write a value to shared memory.

        Args:
            key: The key to write to
            value: The value to store
            agent_id: ID of the writing agent
            expected_version: Optional version for optimistic locking

        Returns:
            True if write succeeded, False if conflict
        """
        # Ensure lock exists
        async with self._global_lock:
            if key not in self.locks:
                self.locks[key] = asyncio.Lock()

        # Acquire key lock
        try:
            async with asyncio.timeout(self.lock_timeout):
                async with self.locks[key]:
                    return await self._do_write(key, value, agent_id, expected_version)
        except asyncio.TimeoutError:
            return False

    async def _do_write(
        self,
        key: str,
        value: Any,
        agent_id: str,
        expected_version: Optional[int],
    ) -> bool:
        """Internal write implementation."""
        if key in self.store:
            existing = self.store[key]

            # Check version if optimistic locking
            if expected_version is not None and existing.version != expected_version:
                return False

            # Apply conflict strategy
            if self.conflict_strategy == ConflictStrategy.FIRST_WRITE_WINS:
                if existing.owner_agent != agent_id:
                    return False

            elif self.conflict_strategy == ConflictStrategy.REJECT:
                if existing.owner_agent != agent_id:
                    return False

            elif self.conflict_strategy == ConflictStrategy.MERGE:
                value = self._merge_values(existing.value, value)

            # Update existing
            existing.value = value
            existing.version += 1
            existing.updated_at = datetime.now()
            existing.write_count += 1
            if agent_id != existing.owner_agent:
                existing.owner_agent = agent_id

        else:
            # Create new
            self.store[key] = SharedValue(
                value=value,
                version=1,
                owner_agent=agent_id,
                write_count=1,
            )

        # Notify subscribers
        await self._notify_subscribers(key, value, agent_id)

        return True

    def _merge_values(self, old_value: Any, new_value: Any) -> Any:
        """Attempt to merge values for MERGE strategy."""
        if isinstance(old_value, dict) and isinstance(new_value, dict):
            merged = old_value.copy()
            merged.update(new_value)
            return merged
        elif isinstance(old_value, list) and isinstance(new_value, list):
            return old_value + [v for v in new_value if v not in old_value]
        else:
            # Default to new value if merge not possible
            return new_value

    async def read(
        self,
        key: str,
        agent_id: str,
        default: Any = None,
    ) -> Any:
        """
        Read a value from shared memory.

        Args:
            key: The key to read
            agent_id: ID of the reading agent
            default: Default value if key not found

        Returns:
            The stored value or default
        """
        if key not in self.store:
            return default

        shared = self.store[key]

        # Track reader
        if agent_id not in shared.readers:
            shared.readers.append(agent_id)

        return shared.value

    async def delete(self, key: str, agent_id: str) -> bool:
        """
        Delete a key from shared memory.

        Args:
            key: The key to delete
            agent_id: ID of the deleting agent

        Returns:
            True if key was deleted
        """
        if key not in self.store:
            return False

        # Check ownership for some strategies
        if self.conflict_strategy in (ConflictStrategy.FIRST_WRITE_WINS, ConflictStrategy.REJECT):
            if self.store[key].owner_agent != agent_id:
                return False

        del self.store[key]

        # Notify subscribers
        await self._notify_subscribers(key, None, agent_id)

        return True

    def subscribe(self, key: str, callback: SubscriptionCallback) -> None:
        """
        Subscribe to changes on a key.

        Args:
            key: The key to watch
            callback: Async function called on changes: (key, value, agent_id) -> None
        """
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(callback)

    def unsubscribe(self, key: str, callback: SubscriptionCallback) -> bool:
        """
        Unsubscribe from changes on a key.

        Args:
            key: The key to stop watching
            callback: The callback to remove

        Returns:
            True if callback was found and removed
        """
        if key not in self.subscribers:
            return False
        try:
            self.subscribers[key].remove(callback)
            return True
        except ValueError:
            return False

    async def _notify_subscribers(self, key: str, value: Any, agent_id: str) -> None:
        """Notify all subscribers of a key change."""
        for callback in self.subscribers.get(key, []):
            try:
                await callback(key, value, agent_id)
            except Exception as e:
                print(f"Subscriber callback error for {key}: {e}")

        # Also notify wildcard subscribers
        for callback in self.subscribers.get("*", []):
            try:
                await callback(key, value, agent_id)
            except Exception as e:
                print(f"Wildcard subscriber callback error: {e}")

    async def get_or_create(
        self,
        key: str,
        default_value: Any,
        agent_id: str,
    ) -> Any:
        """
        Get a value or create it with default if not exists.

        Args:
            key: The key to get or create
            default_value: Default value to set if key doesn't exist
            agent_id: ID of the requesting agent

        Returns:
            The existing or newly created value
        """
        if key in self.store:
            return await self.read(key, agent_id)

        await self.write(key, default_value, agent_id)
        return default_value

    async def compare_and_swap(
        self,
        key: str,
        expected_value: Any,
        new_value: Any,
        agent_id: str,
    ) -> bool:
        """
        Atomic compare-and-swap operation.

        Args:
            key: The key to update
            expected_value: Expected current value
            new_value: New value to set
            agent_id: ID of the requesting agent

        Returns:
            True if swap succeeded (value matched expected)
        """
        async with self._global_lock:
            if key not in self.locks:
                self.locks[key] = asyncio.Lock()

        async with self.locks[key]:
            current = self.store.get(key)

            if current is None:
                if expected_value is None:
                    self.store[key] = SharedValue(
                        value=new_value,
                        version=1,
                        owner_agent=agent_id,
                    )
                    await self._notify_subscribers(key, new_value, agent_id)
                    return True
                return False

            if current.value == expected_value:
                current.value = new_value
                current.version += 1
                current.updated_at = datetime.now()
                current.write_count += 1
                await self._notify_subscribers(key, new_value, agent_id)
                return True

            return False

    def get_all_keys(self) -> List[str]:
        """Get all keys in shared memory."""
        return list(self.store.keys())

    def get_keys_by_agent(self, agent_id: str) -> List[str]:
        """Get all keys owned by a specific agent."""
        return [
            key for key, value in self.store.items()
            if value.owner_agent == agent_id
        ]

    def get_metadata(self, key: str) -> Optional[dict]:
        """Get metadata for a key without the value."""
        if key not in self.store:
            return None
        shared = self.store[key]
        return {
            "version": shared.version,
            "owner_agent": shared.owner_agent,
            "readers": shared.readers,
            "created_at": shared.created_at.isoformat(),
            "updated_at": shared.updated_at.isoformat(),
            "write_count": shared.write_count,
        }

    def __len__(self) -> int:
        """Return number of keys in shared memory."""
        return len(self.store)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in shared memory."""
        return key in self.store

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self.store:
            return {
                "key_count": 0,
                "total_writes": 0,
                "unique_agents": 0,
                "avg_readers_per_key": 0,
            }

        agents = set()
        total_writes = 0
        total_readers = 0

        for shared in self.store.values():
            agents.add(shared.owner_agent)
            agents.update(shared.readers)
            total_writes += shared.write_count
            total_readers += len(shared.readers)

        return {
            "key_count": len(self.store),
            "total_writes": total_writes,
            "unique_agents": len(agents),
            "avg_readers_per_key": total_readers / len(self.store),
        }
