# Memory Services Reference

Complete reference for ADK memory services - long-term knowledge storage across sessions.

## Memory vs Session

| Aspect | Session | Memory |
|--------|---------|--------|
| **Purpose** | Conversation history | Long-term facts |
| **Scope** | Single conversation | Cross-conversation |
| **Lifespan** | Until session deleted | Persistent |
| **Content** | User messages, agent responses | Facts, preferences, knowledge |
| **Storage** | Session service | Memory service |
| **Query** | Linear (conversation order) | Semantic (by relevance) |

## Memory Service Types

### InMemoryMemoryService

**Use Case:** Development and testing

```python
from google.adk.memory import InMemoryMemoryService

class InMemoryMemoryService:
    """In-memory knowledge storage."""

    def __init__(self):
        """Initialize in-memory storage."""
        pass

    def store_memory(
        self,
        user_id: str,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Store a memory.

        Args:
            user_id: User identifier
            content: Memory content
            tags: Optional tags for categorization
            metadata: Optional metadata

        Returns:
            Memory ID
        """
        pass

    def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        tags: Optional[List[str]] = None,
    ) -> List[Memory]:
        """Search memories.

        Args:
            user_id: User identifier
            query: Search query
            limit: Max results
            tags: Filter by tags

        Returns:
            List of relevant memories
        """
        pass

    def get_memory(
        self,
        memory_id: str,
    ) -> Memory:
        """Retrieve specific memory.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory object
        """
        pass

    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Update a memory."""
        pass

    def delete_memory(
        self,
        memory_id: str,
    ) -> None:
        """Delete a memory."""
        pass

    def delete_user_memories(
        self,
        user_id: str,
    ) -> None:
        """Delete all memories for a user."""
        pass
```

### VertexAiMemoryBankService

**Use Case:** Production with semantic search

```python
from google.adk.memory import VertexAiMemoryBankService

class VertexAiMemoryBankService:
    """Vertex AI managed memory storage with semantic search."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        memory_bank_id: str = "default",
        embedding_model: str = "textembedding-gecko@003",
    ):
        """Initialize Vertex AI memory service.

        Args:
            project_id: GCP project ID
            location: GCP region
            memory_bank_id: Memory bank identifier
            embedding_model: Embedding model for semantic search
        """
        pass
```

## Memory Data Model

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Memory:
    """Memory object."""

    memory_id: str                    # Unique ID
    user_id: str                      # User this memory belongs to
    content: str                      # Memory content
    created_at: datetime              # When created
    updated_at: datetime              # Last update
    tags: List[str]                   # Tags for categorization
    metadata: dict                    # Custom metadata
    score: Optional[float] = None     # Relevance score (from search)
    embedding: Optional[List[float]] = None  # Vector embedding

# Example memory
memory = Memory(
    memory_id="mem_123",
    user_id="user_456",
    content="User prefers dark mode and compact layouts",
    created_at=datetime(2024, 1, 15, 10, 30),
    updated_at=datetime(2024, 1, 15, 10, 30),
    tags=["preference", "ui"],
    metadata={"source": "settings", "confidence": 0.9},
)
```

## Memory Operations

### Storing Memories

```python
# Basic storage
memory_id = memory_service.store_memory(
    user_id="user_123",
    content="User works at Google as a Software Engineer",
    tags=["employment", "personal"],
)

# With metadata
memory_id = memory_service.store_memory(
    user_id="user_123",
    content="User's favorite programming language is Python",
    tags=["preference", "technical"],
    metadata={
        "source": "conversation",
        "confidence": 0.95,
        "extracted_at": "2024-01-15T10:30:00Z",
    },
)
```

### Searching Memories

```python
# Simple search
memories = memory_service.search_memories(
    user_id="user_123",
    query="What does the user do for work?",
    limit=5,
)

for memory in memories:
    print(f"Score: {memory.score}")
    print(f"Content: {memory.content}")
    print(f"Tags: {memory.tags}")
    print()

# Search with tag filter
tech_memories = memory_service.search_memories(
    user_id="user_123",
    query="programming preferences",
    tags=["technical"],
    limit=3,
)
```

### Updating Memories

```python
# Update content
memory_service.update_memory(
    memory_id="mem_123",
    content="User works at Google as a Senior Software Engineer",  # Updated
)

# Add tags
memory = memory_service.get_memory("mem_123")
memory_service.update_memory(
    memory_id="mem_123",
    tags=memory.tags + ["verified"],
)

# Update metadata
memory_service.update_memory(
    memory_id="mem_123",
    metadata={
        **memory.metadata,
        "last_verified": "2024-01-20T15:00:00Z",
    },
)
```

### Deleting Memories

```python
# Delete specific memory
memory_service.delete_memory("mem_123")

# Delete by tag
memories = memory_service.search_memories(
    user_id="user_123",
    query="*",  # All memories
    tags=["temporary"],
)
for memory in memories:
    memory_service.delete_memory(memory.memory_id)

# Delete all user memories
memory_service.delete_user_memories("user_123")
```

## Semantic Search

Vertex AI Memory Bank uses semantic search to find relevant memories.

### How Semantic Search Works

```
1. User query: "What are my food preferences?"
   ↓
2. Generate query embedding
   ↓
3. Search memory embeddings for similarity
   ↓
4. Return top matches by cosine similarity
   ↓
5. Results:
   - "User loves Italian food" (score: 0.92)
   - "User is vegetarian" (score: 0.88)
   - "User allergic to peanuts" (score: 0.85)
```

### Semantic vs Keyword Search

```python
# Keyword search (InMemoryMemoryService)
# Query: "programming languages"
# Matches: Exact text containing "programming" or "languages"

# Semantic search (VertexAiMemoryBankService)
# Query: "What tech does the user know?"
# Matches:
#   - "User expert in Python" (high similarity)
#   - "Knows JavaScript and TypeScript" (high similarity)
#   - "Prefers VS Code editor" (medium similarity)
```

## Integration with Agents

### Automatic Memory Extraction

```python
from google.adk.agents import LlmAgent
from google.adk.memory import VertexAiMemoryBankService
from google.adk.runners import Runner

# Configure memory service
memory_service = VertexAiMemoryBankService(
    project_id="my-project",
    location="us-central1",
    memory_bank_id="user_knowledge",
)

# Create agent with memory
agent = LlmAgent(
    name="assistant",
    model="gemini-2.0-flash-exp",
    system_instruction="""You are a helpful assistant with memory.
    When users share information about themselves, extract and remember it.
    Use stored memories to provide personalized responses.""",
)

# Create runner
runner = Runner(
    agent=agent,
    app_name="my_app",
    memory_service=memory_service,
)

# Agent automatically extracts and stores facts
response = runner.run(
    user_input="I'm a vegetarian and I love Italian food",
    session_id="session_1",
    user_id="user_123",  # Important: provide user_id
)

# Later conversation
response = runner.run(
    user_input="What kind of restaurant should I go to?",
    session_id="session_2",  # Different session
    user_id="user_123",  # Same user
)
# Agent retrieves memories: "vegetarian", "loves Italian"
# Responds: "I'd recommend a vegetarian Italian restaurant!"
```

### Manual Memory Management

```python
# Store memory explicitly
def store_user_preference(user_id: str, preference: str):
    """Store user preference in memory."""
    memory_service.store_memory(
        user_id=user_id,
        content=preference,
        tags=["preference"],
        metadata={
            "source": "manual",
            "stored_at": datetime.now().isoformat(),
        },
    )

# Use in application
store_user_preference("user_123", "Prefers email over SMS for notifications")

# Retrieve for decision making
def get_notification_preference(user_id: str) -> str:
    """Get user's notification preference."""
    memories = memory_service.search_memories(
        user_id=user_id,
        query="notification preferences",
        limit=1,
    )

    if memories and "email" in memories[0].content.lower():
        return "email"
    else:
        return "sms"
```

## Memory Tagging Strategies

### Category Tags

```python
# Organize by category
TAGS = {
    "personal": ["name", "age", "location", "family"],
    "preference": ["food", "music", "color", "style"],
    "professional": ["job", "skills", "education", "company"],
    "technical": ["tools", "languages", "frameworks"],
    "health": ["allergies", "conditions", "medications"],
}

memory_service.store_memory(
    user_id="user_123",
    content="User allergic to peanuts",
    tags=["health", "allergies"],
)
```

### Temporal Tags

```python
# Track when information is relevant
from datetime import datetime, timedelta

def store_temporary_memory(user_id: str, content: str, expires_days: int):
    """Store memory with expiration."""
    expires_at = datetime.now() + timedelta(days=expires_days)

    memory_service.store_memory(
        user_id=user_id,
        content=content,
        tags=["temporary"],
        metadata={
            "expires_at": expires_at.isoformat(),
        },
    )

# Cleanup expired memories
def cleanup_expired_memories():
    """Delete expired memories."""
    # Implementation would query and delete expired memories
    pass
```

### Source Tags

```python
# Track where memory came from
memory_service.store_memory(
    user_id="user_123",
    content="User mentioned loving Python",
    tags=["technical", "preference", "conversation_derived"],
    metadata={"source": "conversation", "session_id": "session_456"},
)

memory_service.store_memory(
    user_id="user_123",
    content="User set dark mode preference",
    tags=["ui", "preference", "settings_derived"],
    metadata={"source": "settings_page"},
)
```

## Memory Confidence Scoring

Track confidence in memories:

```python
def store_memory_with_confidence(
    user_id: str,
    content: str,
    confidence: float,
):
    """Store memory with confidence score."""
    assert 0.0 <= confidence <= 1.0

    memory_service.store_memory(
        user_id=user_id,
        content=content,
        metadata={"confidence": confidence},
    )

# High confidence (explicit statement)
store_memory_with_confidence(
    "user_123",
    "User is vegetarian",
    confidence=0.95,
)

# Medium confidence (inferred)
store_memory_with_confidence(
    "user_123",
    "User might like hiking",
    confidence=0.6,
)

# Retrieve only high-confidence memories
def get_confident_memories(user_id: str, min_confidence: float = 0.8):
    """Get high-confidence memories."""
    all_memories = memory_service.search_memories(
        user_id=user_id,
        query="*",
        limit=100,
    )

    return [
        m for m in all_memories
        if m.metadata.get("confidence", 0) >= min_confidence
    ]
```

## Memory Versioning

Track changes to memories over time:

```python
class VersionedMemoryService:
    """Memory service with version tracking."""

    def __init__(self, base_service):
        self.base_service = base_service

    def update_memory_with_history(
        self,
        memory_id: str,
        new_content: str,
    ):
        """Update memory and store previous version."""
        # Get current memory
        current = self.base_service.get_memory(memory_id)

        # Store old version as separate memory
        self.base_service.store_memory(
            user_id=current.user_id,
            content=current.content,
            tags=current.tags + ["archived", "version"],
            metadata={
                **current.metadata,
                "original_memory_id": memory_id,
                "archived_at": datetime.now().isoformat(),
                "version": current.metadata.get("version", 1),
            },
        )

        # Update current memory
        self.base_service.update_memory(
            memory_id=memory_id,
            content=new_content,
            metadata={
                **current.metadata,
                "version": current.metadata.get("version", 1) + 1,
                "updated_at": datetime.now().isoformat(),
            },
        )
```

## Performance Considerations

### Embedding Model Selection

| Model | Dimensions | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| `textembedding-gecko@003` | 768 | Fast | Good | General purpose |
| `textembedding-gecko@latest` | 768 | Fast | Better | Recommended |
| `text-embedding-004` | 768 | Medium | Best | High-quality search |

```python
# Choose model based on needs
memory_service = VertexAiMemoryBankService(
    project_id="my-project",
    embedding_model="textembedding-gecko@latest",
)
```

### Batch Operations

```python
# Store multiple memories efficiently
memories_to_store = [
    {"content": "User likes coffee", "tags": ["preference"]},
    {"content": "User works remotely", "tags": ["professional"]},
    {"content": "User in timezone PST", "tags": ["personal"]},
]

for memory_data in memories_to_store:
    memory_service.store_memory(
        user_id="user_123",
        **memory_data,
    )

# Better: Use batch API if available
# memory_service.store_memories_batch(user_id="user_123", memories=memories_to_store)
```

### Caching Search Results

```python
from functools import lru_cache
import hashlib

class CachedMemoryService:
    """Memory service with search result caching."""

    def __init__(self, base_service):
        self.base_service = base_service

    @lru_cache(maxsize=1000)
    def search_memories_cached(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ):
        """Search with caching."""
        return self.base_service.search_memories(
            user_id=user_id,
            query=query,
            limit=limit,
        )

    def store_memory(self, **kwargs):
        """Store and invalidate cache."""
        self.search_memories_cached.cache_clear()
        return self.base_service.store_memory(**kwargs)
```

## Testing Memory Services

```python
import pytest

def test_memory_storage():
    """Test storing and retrieving memories."""
    service = InMemoryMemoryService()

    # Store memory
    memory_id = service.store_memory(
        user_id="test_user",
        content="Test memory content",
        tags=["test"],
    )

    # Retrieve
    memory = service.get_memory(memory_id)
    assert memory.content == "Test memory content"
    assert "test" in memory.tags

def test_memory_search():
    """Test memory search."""
    service = InMemoryMemoryService()

    # Store multiple memories
    service.store_memory("user1", "Loves Python", tags=["tech"])
    service.store_memory("user1", "Works at Google", tags=["job"])
    service.store_memory("user1", "Vegetarian", tags=["food"])

    # Search
    results = service.search_memories(
        user_id="user1",
        query="programming",
        limit=5,
    )

    assert len(results) > 0

def test_memory_isolation():
    """Test user memory isolation."""
    service = InMemoryMemoryService()

    service.store_memory("user1", "User1's secret", tags=["private"])
    service.store_memory("user2", "User2's secret", tags=["private"])

    # User1's search shouldn't return User2's memories
    results = service.search_memories("user1", "secret")
    assert all(m.user_id == "user1" for m in results)
```

## Best Practices

1. **Use descriptive content** - Store complete, clear information
2. **Tag consistently** - Use standardized tag vocabulary
3. **Track confidence** - Know which memories are reliable
4. **Clean up old data** - Delete expired or irrelevant memories
5. **Respect privacy** - Delete user memories on account deletion
6. **Cache searches** - Reduce API calls with caching
7. **Batch operations** - Store multiple memories efficiently
8. **Monitor costs** - Track embedding API usage

## Related Resources

- Vertex AI Embeddings: https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings/get-text-embeddings
- Vector Search: https://cloud.google.com/vertex-ai/docs/vector-search
- Memory Bank API: https://cloud.google.com/vertex-ai/docs/agents/memory
