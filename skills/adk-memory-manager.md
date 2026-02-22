---
name: adk-memory-manager
description: Build multi-agent memory systems for ADK. Types include working (short-term context with attention scoring/TTL), semantic (knowledge graphs for reasoning), shared (cross-agent state with conflict strategies), and persistent (long-term with Pinecone/in-memory). Configure max-size, TTL, conflict-strategy, namespace. Supports multimodal memory (text/image/audio).
version: 1.0.0
---

# adk-memory-manager

**Multi-Agent Memory System for Google ADK**

Build sophisticated memory systems for multi-agent coordination. Includes working memory with attention scoring, semantic memory for knowledge graphs, shared memory for cross-agent state, and persistent memory with Pinecone vector storage.

## When to Use

Use this skill when:
- Agents need short-term context (working memory)
- Multiple agents need to share state
- Building knowledge graphs for agent reasoning
- Long-term memory persistence is required
- Cross-session memory recall is needed
- Multimodal memory (text, image, audio) is needed

## Quick Start

```bash
# Working memory for single agent
/adk-memory-manager --type "working" \
  --max-size "20" \
  --ttl "5m"

# Shared memory for multi-agent
/adk-memory-manager --type "shared" \
  --conflict-strategy "last-write-wins"

# Persistent memory with Pinecone
/adk-memory-manager --type "persistent" \
  --backend "pinecone" \
  --namespace "agent-memory"
```

## Parameters

```bash
--type "working|semantic|shared|persistent"  # Required
--max-size "20"                              # Working memory capacity
--ttl "5m"                                   # Time-to-live for entries
--conflict-strategy "last-write-wins|first-write-wins|merge|reject"
--backend "pinecone|in-memory"               # For persistent
--namespace "default"                        # Memory namespace
```

## Memory Types

### 1. Working Memory

Short-term context with attention-based eviction.

```bash
/adk-memory-manager --type "working" \
  --max-size "20" \
  --recency-weight "0.4" \
  --importance-weight "0.4"
```

**Generated Code:**
```python
from adk_bidi import WorkingMemory

# Create working memory
memory = WorkingMemory(
    max_size=20,
    recency_weight=0.4,
    importance_weight=0.4,
    access_weight=0.2,
)

# Add entries with importance
memory.add(
    key="user_name",
    value="Alice",
    importance=0.8,  # High importance
    source_agent="assistant",
)

memory.add(
    key="last_topic",
    value="AI research",
    importance=0.5,  # Medium importance
)

# Retrieve value
user_name = memory.get("user_name")  # "Alice"

# Get context for agent (top-k by attention score)
context = memory.get_context(top_k=5)
# Returns: [{"key": "user_name", "value": "Alice"}, ...]

# Get formatted context string
context_str = memory.get_context_string(top_k=5)
# Returns: "Current context:\n- user_name: Alice\n- last_topic: AI research"

# Clear all entries
memory.clear()
```

**Attention Scoring:**
```
attention = (recency * 0.4) + (importance * 0.4) + (access_count * 0.2)

- recency: 1 / (1 + seconds_since_access / 60)
- importance: 0.0 to 1.0 (user-defined)
- access_count: normalized count of retrievals
```

### 2. Semantic Memory

Knowledge graph for concept relationships.

```bash
/adk-memory-manager --type "semantic" \
  --enable-inference "true"
```

**Generated Code:**
```python
from adk_bidi.memory.semantic_memory import SemanticMemory, RelationType

# Create semantic memory
memory = SemanticMemory()

# Add concepts
memory.add_concept(
    name="Python",
    category="programming_language",
    attributes={"type": "interpreted", "paradigm": "multi-paradigm"},
)

memory.add_concept(
    name="Flask",
    category="framework",
    attributes={"type": "web", "language": "Python"},
)

# Add relationships
memory.add_relationship(
    source="Flask",
    target="Python",
    relation_type=RelationType.USES,
    strength=1.0,
)

memory.add_relationship(
    source="Flask",
    target="Web Framework",
    relation_type=RelationType.IS_A,
)

# Query related concepts
related = memory.get_related("Python", depth=2)
# Returns concepts connected within 2 hops

# Find path between concepts
path = memory.find_path("Flask", "Python")
# Returns: ["Flask", "Python"]

# Query by attributes
results = memory.query(category="framework", language="Python")

# Infer transitive relationships
inferred = memory.infer_transitive(RelationType.IS_A)

# Get statistics
stats = memory.get_stats()
```

**Relationship Types:**
```python
class RelationType(Enum):
    IS_A = "is_a"           # Inheritance (Flask IS_A Framework)
    HAS = "has"             # Composition (Project HAS Files)
    PART_OF = "part_of"     # Component relationship
    RELATED_TO = "related"  # General association
    CAUSES = "causes"       # Causal relationship
    USES = "uses"           # Dependency (Flask USES Python)
    PRECEDES = "precedes"   # Temporal ordering
```

### 3. Shared Memory

Cross-agent state with conflict resolution.

```bash
/adk-memory-manager --type "shared" \
  --conflict-strategy "last-write-wins"
```

**Generated Code:**
```python
from adk_bidi import SharedMemory
from adk_bidi.memory.shared_memory import ConflictStrategy

# Create shared memory
memory = SharedMemory(
    conflict_strategy=ConflictStrategy.LAST_WRITE_WINS,
)

# Write from agent
await memory.write(
    key="current_task",
    value="research AI trends",
    agent_id="researcher",
)

# Read from another agent
value = await memory.read(key="current_task", agent_id="analyst")
# Returns: "research AI trends"

# Subscribe to changes
async def on_task_change(key: str, value: any):
    print(f"Task changed: {value}")

memory.subscribe("current_task", on_task_change)

# Atomic compare-and-swap
success = await memory.compare_and_swap(
    key="status",
    expected="pending",
    new_value="in_progress",
    agent_id="worker",
)

# Delete key
await memory.delete("current_task", "supervisor")

# Get all keys
all_keys = memory.get_all_keys()
```

**Conflict Strategies:**
```python
class ConflictStrategy(Enum):
    LAST_WRITE_WINS = "lww"     # Latest write always wins
    FIRST_WRITE_WINS = "fww"   # First write preserved
    MERGE = "merge"             # Attempt to merge values
    REJECT = "reject"           # Reject conflicting writes
```

### 4. Persistent Memory (Pinecone)

Long-term vector storage with semantic search.

```bash
/adk-memory-manager --type "persistent" \
  --backend "pinecone" \
  --namespace "agent-memory"
```

**Generated Code:**
```python
from adk_bidi import PersistentMemoryStore

# Create persistent store
store = PersistentMemoryStore(
    index_name="agent-memory",
    namespace="default",
    # Uses PINECONE_API_KEY and PINECONE_INDEX_HOST env vars
)

# Store text memory
store.store_memory(
    memory_id="fact_001",
    content="Python is a programming language created by Guido van Rossum",
    metadata={"topic": "programming", "source": "wikipedia"},
    importance=0.8,
    agent_id="knowledge_agent",
    modality="text",
)

# Store image memory
store.store_memory(
    memory_id="image_001",
    content=image_base64,
    metadata={"description": "Product screenshot"},
    importance=0.6,
    agent_id="vision_agent",
    modality="image",
)

# Recall by semantic similarity
memories = store.recall(
    query="What programming language did Guido create?",
    top_k=5,
    agent_id="researcher",  # Optional: filter by agent
    min_score=0.5,
)
# Returns: [{"content": "Python is...", "score": 0.92, ...}]

# Multimodal recall (cross-modal search)
memories = store.recall_multimodal(
    text_query="programming documentation",
    top_k=5,
)

# Delete memory
store.delete_memory("fact_001")

# Get statistics
stats = store.get_stats()
# Returns: {"total_vectors": 1000, "namespaces": {...}}
```

**Environment Variables:**
```bash
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_HOST=your_index_host
```

## Multi-Agent Memory Integration

### Agent with All Memory Types

```python
from adk_bidi import (
    BidiAgent,
    WorkingMemory,
    SharedMemory,
    PersistentMemoryStore,
)
from adk_bidi.memory.semantic_memory import SemanticMemory

# Create memory systems
working = WorkingMemory(max_size=20)
shared = SharedMemory()
persistent = PersistentMemoryStore()
semantic = SemanticMemory()

# Create agent with memories
agent = BidiAgent(
    name="memory_agent",
    instruction="You have access to multiple memory systems.",
    working_memory=working,
    shared_memory=shared,
    memory_context_size=10,  # Include top 10 in context
)

# Agent has built-in memory tools
# - remember(key, value, importance) -> stores in working memory
# - recall_context(count) -> retrieves from working memory
# - share_information(key, value) -> shares via shared memory
# - get_shared_information(key) -> reads from shared memory
```

### Multi-Agent Coordination with Shared Memory

```python
from adk_bidi import MultiAgentSupervisor, SharedMemory, BidiAgent

# Create shared memory for team
shared_memory = SharedMemory()

# Create agents with shared memory
researcher = BidiAgent(
    name="researcher",
    instruction="Research topics and share findings.",
    shared_memory=shared_memory,
)

writer = BidiAgent(
    name="writer",
    instruction="Write based on shared research.",
    shared_memory=shared_memory,
)

# Create supervisor
supervisor = MultiAgentSupervisor(
    agents=[researcher, writer],
    shared_memory=shared_memory,
)

# Agents can now share state
# Researcher: await shared_memory.write("findings", data, "researcher")
# Writer: findings = await shared_memory.read("findings", "writer")
```

### Persistent Memory for Long-Term Knowledge

```python
from adk_bidi.memory.persistent_store import PersistentMemoryStore, InMemoryPersistentStore

# Production: Use Pinecone
store = PersistentMemoryStore(namespace="knowledge_base")

# Development: Use in-memory
store = InMemoryPersistentStore(namespace="test")

# Store knowledge
store.store_memory(
    memory_id="kb_001",
    content="The Eiffel Tower is 330 meters tall",
    metadata={"category": "landmarks", "verified": True},
    importance=0.7,
)

# Recall with semantic search
results = store.recall("How tall is the Eiffel Tower?")
```

## Memory Context Injection

BidiAgent automatically injects working memory into prompts:

```python
agent = BidiAgent(
    name="assistant",
    instruction="You are helpful.",
    working_memory=WorkingMemory(),
    memory_context_size=5,           # Include top 5 entries
    include_memory_in_prompt=True,   # Enable injection
)

# Memory context is added to instruction:
# "You are helpful.
#
# Current context:
# - user_name: Alice
# - last_topic: AI research
# - preference: detailed explanations"
```

## Full Example: Knowledge Management Agent

```python
"""Agent with comprehensive memory management."""
import asyncio
from datetime import datetime
from adk_bidi import BidiAgent, WorkingMemory, SharedMemory
from adk_bidi.memory.semantic_memory import SemanticMemory, RelationType
from adk_bidi.memory.persistent_store import PersistentMemoryStore

class KnowledgeAgent:
    def __init__(self, name: str):
        # Initialize memory systems
        self.working = WorkingMemory(max_size=30)
        self.semantic = SemanticMemory()
        self.persistent = PersistentMemoryStore(namespace=name)
        self.shared = SharedMemory()

        # Create agent
        self.agent = BidiAgent(
            name=name,
            instruction=self._build_instruction(),
            working_memory=self.working,
            shared_memory=self.shared,
            memory_context_size=10,
        )

    def _build_instruction(self) -> str:
        return """You are a knowledge management agent.

You have access to:
- Working memory: Short-term context
- Semantic memory: Knowledge graph
- Persistent memory: Long-term storage
- Shared memory: Cross-agent coordination

Use these systems to:
1. Remember important information
2. Build knowledge relationships
3. Recall relevant context
4. Share findings with other agents"""

    def learn_concept(self, name: str, category: str, **attributes):
        """Add concept to semantic memory."""
        self.semantic.add_concept(name, category, attributes)

        # Also store in persistent memory
        self.persistent.store_memory(
            memory_id=f"concept_{name}",
            content=f"{name} is a {category}",
            metadata={"type": "concept", **attributes},
        )

    def connect_concepts(self, source: str, target: str, relation: RelationType):
        """Create relationship between concepts."""
        self.semantic.add_relationship(source, target, relation)

    def remember(self, key: str, value: str, importance: float = 0.5):
        """Add to working memory."""
        self.working.add(key, value, importance, self.agent.name)

    async def share(self, key: str, value: str):
        """Share with other agents."""
        await self.shared.write(key, value, self.agent.name)

    def recall(self, query: str, top_k: int = 5) -> list:
        """Recall from persistent memory."""
        return self.persistent.recall(query, top_k)

    def get_context(self) -> str:
        """Get current context from working memory."""
        return self.working.get_context_string()

# Usage
agent = KnowledgeAgent("knowledge_bot")

# Learn concepts
agent.learn_concept("Python", "language", type="programming")
agent.learn_concept("Flask", "framework", type="web")
agent.connect_concepts("Flask", "Python", RelationType.USES)

# Remember context
agent.remember("user_interest", "web development", importance=0.8)

# Share findings
await agent.share("research_topic", "Python web frameworks")

# Recall knowledge
results = agent.recall("What frameworks use Python?")
```

## Environment Variables

```bash
# Pinecone (for persistent memory)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_HOST=your_index_host

# Google AI (for agents)
GOOGLE_API_KEY=your_gemini_api_key
```

## Related Skills

- **adk-bidi-multi-agent**: Real-time multi-agent streaming
- **adk-autonomous-agent**: Self-reasoning agents with memory
- **adk-pinecone-rag**: Pinecone RAG integration
