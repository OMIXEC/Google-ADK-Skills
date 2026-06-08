# Memory & State Management for ADK Workflows

ADK agents operate on sessions. State flows through `session.state` within a session. Persistent memory across sessions uses external stores. This reference covers all layers.

## Memory Hierarchy

```
┌──────────────────────────────────────────────┐
│ L1: Working Memory (session.state)           │
│    - Lives within one session                │
│    - Dict-like access: state["key"] = value  │
│    - Survives agent transfers                │
│    - Lost when session ends                  │
├──────────────────────────────────────────────┤
│ L2: Session Memory (SessionService)          │
│    - Full conversation history               │
│    - Persisted across turns                  │
│    - Backend: InMemory, Firestore, Spanner   │
├──────────────────────────────────────────────┤
│ L3: Persistent Memory (external store)       │
│    - User profiles, preferences, facts       │
│    - Survives sessions and deployments       │
│    - Backend: DB, vector store, cache        │
├──────────────────────────────────────────────┤
│ L4: Episodic Memory (conversation archive)   │
│    - Past conversations, decisions, outcomes │
│    - Used for learning, personalization      │
│    - Backend: object store, DB, vector DB    │
└──────────────────────────────────────────────┘
```

## SessionService Configuration

### InMemory (development only)

```python
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()
session = await session_service.create_session(
    app_name="my_app",
    user_id="user_123",
    state={"user_preference": "concise"},  # Initial state
)
```

### Firestore (production — serverless)

```python
from google.adk.sessions import FirestoreSessionService

session_service = FirestoreSessionService(
    project_id=os.getenv("GCP_PROJECT_ID"),
    database="(default)",  # or named database
)
```

### Spanner (production — global, high-throughput)

```python
from google.adk.sessions import SpannerSessionService

session_service = SpannerSessionService(
    instance_id="my-instance",
    database_id="sessions-db",
)
```

### Redis (custom SessionService)

```python
"""Custom Redis-backed SessionService for high-throughput caching layer."""
import json
import redis.asyncio as redis
from google.adk.sessions import SessionService, Session

class RedisSessionService(SessionService):
    def __init__(self, redis_url: str, ttl: int = 3600):
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl

    async def create_session(self, app_name: str, user_id: str, state: dict = {}) -> Session:
        session = Session(
            id=f"{app_name}:{user_id}:{uuid4().hex[:12]}",
            app_name=app_name,
            user_id=user_id,
            state=state,
        )
        await self._save(session)
        return session

    async def get_session(self, session_id: str) -> Session | None:
        data = await self.redis.get(f"session:{session_id}")
        return Session(**json.loads(data)) if data else None

    async def _save(self, session: Session):
        await self.redis.setex(
            f"session:{session.id}", self.ttl, json.dumps(session.model_dump())
        )
```

## Working Memory — `session.state`

### Within agents

```python
# Writing to state
async def set_context(callback_context):
    callback_context.state["user_name"] = "Alice"
    callback_context.state["current_step"] = "gathering_requirements"

# Reading from state
async def use_context(callback_context):
    name = callback_context.state.get("user_name", "Guest")

# Deleting from state
async def clear_step(callback_context):
    callback_context.state.pop("current_step", None)
```

### Across agents via `output_key`

```python
# Agent A writes output to state
agent_a = LlmAgent(
    name="fetcher",
    output_key="fetched_data",  # → state["fetched_data"]
)

# Agent B reads from state
agent_b = LlmAgent(
    name="processor",
    instruction="Process the data in session.state['fetched_data'].",
)

pipeline = SequentialAgent(sub_agents=[agent_a, agent_b])
```

### State keys convention

```python
# Use namespaced keys to avoid collisions
STATE_PREFIX = "my_app"

# Good
state[f"{STATE_PREFIX}.user_query"] = query
state[f"{STATE_PREFIX}.search_results"] = results

# Avoid generic keys that might collide
# state["query"]  ← could be overwritten by any agent
# state["results"] ← ambiguous
```

## Persistent Memory Across Sessions

### User profiles

```python
"""Persistent user memory via Firestore — survives session end."""
from google.cloud import firestore

class UserMemory:
    def __init__(self):
        self.db = firestore.Client()

    async def get_profile(self, user_id: str) -> dict:
        doc = self.db.collection("user_profiles").document(user_id).get()
        return doc.to_dict() if doc.exists else {}

    async def update_profile(self, user_id: str, updates: dict):
        self.db.collection("user_profiles").document(user_id).set(
            updates, merge=True
        )

    async def get_preferences(self, user_id: str) -> dict:
        profile = await self.get_profile(user_id)
        return profile.get("preferences", {})

# Inject into session at start
session = await session_service.create_session(
    app_name="my_app",
    user_id="user_123",
    state={
        "user_profile": await UserMemory().get_profile("user_123"),
    },
)
```

### Learned facts (long-term memory)

```python
"""Store facts the agent learns across sessions."""
class FactStore:
    def __init__(self, db):
        self.db = db  # PG, Spanner, Firestore — any DB from database-integration.md

    async def remember(self, user_id: str, fact: str, source: str):
        await self.db.execute(
            "INSERT INTO facts (user_id, fact, source, created_at) VALUES ($1, $2, $3, NOW())",
            (user_id, fact, source),
        )

    async def recall(self, user_id: str, query: str, limit: int = 5) -> list[str]:
        rows = await self.db.query(
            "SELECT fact FROM facts WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
            (user_id, limit),
        )
        return [r["fact"] for r in rows]
```

## Context Window Management

### Token budgeting strategies

```python
"""Monitor and manage token usage per session."""
from google.genai import types

class TokenBudget:
    def __init__(self, max_input_tokens: int = 100_000, warning_threshold: float = 0.8):
        self.max = max_input_tokens
        self.warning = warning_threshold

    def estimate_tokens(self, events: list) -> int:
        """Rough estimate: ~4 chars per token."""
        total = 0
        for event in events:
            if event.content:
                for part in event.content.parts:
                    if part.text:
                        total += len(part.text) // 4
        return total

    def should_summarize(self, events: list) -> bool:
        used = self.estimate_tokens(events)
        if used > self.max * self.warning:
            return True
        return False

# In before_model_callback, check and summarize if needed
async def manage_context(callback_context):
    budget = TokenBudget()
    if budget.should_summarize(callback_context.session.events):
        # Insert a summarization instruction
        callback_context.state["needs_summary"] = True
```

### Sliding window

```python
"""Keep only the last N events to manage context window."""
def sliding_window(events: list, max_events: int = 20) -> list:
    # Always keep the first event (system instruction context)
    if len(events) <= max_events:
        return events
    return [events[0]] + events[-(max_events - 1):]
```

### Summarization trigger

```python
"""Automatically summarize when context exceeds budget."""
async def auto_summarize(callback_context):
    events = callback_context.session.events
    budget = TokenBudget(max_input_tokens=50_000)

    if budget.should_summarize(events):
        # Store summary in state, clear old events
        summary_prompt = "Summarize the conversation so far, preserving key facts and decisions."
        # The agent will receive this as a system instruction addition
        callback_context.state["conversation_summary"] = summary_prompt
        callback_context.state["context_summarized"] = True
```

## State Serialization & Hydration

```python
"""Serialize session state for warm start / checkpoint / restore."""

import json
from pydantic import BaseModel

class SessionCheckpoint(BaseModel):
    session_id: str
    user_id: str
    state: dict
    event_count: int
    created_at: str  # ISO 8601

async def save_checkpoint(session, store) -> str:
    """Save session state for later recovery."""
    checkpoint = SessionCheckpoint(
        session_id=session.id,
        user_id=session.user_id,
        state=session.state,
        event_count=len(session.events),
        created_at=datetime.utcnow().isoformat(),
    )
    await store.save(f"checkpoint:{session.id}", checkpoint.model_dump_json())
    return session.id

async def restore_checkpoint(session_id: str, store) -> SessionCheckpoint | None:
    """Restore session from checkpoint."""
    data = await store.get(f"checkpoint:{session_id}")
    return SessionCheckpoint(**json.loads(data)) if data else None
```

## Memory Service Integration (ADK Built-in)

ADK provides `MemoryService` for storing and retrieving agent memories:

```python
from google.adk.memory import InMemoryMemoryService, FirestoreMemoryService

# Development
memory_service = InMemoryMemoryService()

# Production — Firestore
memory_service = FirestoreMemoryService(project_id=os.getenv("GCP_PROJECT_ID"))

# Attach to Runner
runner = Runner(
    app_name="my_app",
    agent=root_agent,
    session_service=session_service,
    memory_service=memory_service,
)
```

### Using memory in agents

```python
# Agent can access memory via InvocationContext
async def use_memory(ctx: InvocationContext):
    # Search memory
    memories = await ctx.memory.search("user preferences", user_id=ctx.user_id)

    # Save to memory
    await ctx.memory.save(
        content="User prefers blue theme and concise answers.",
        user_id=ctx.user_id,
        metadata={"category": "preferences"},
    )
```

## Continuous Learning: Auto-Save + Preload Pattern

Agents that learn across sessions need automatic memory capture. This pattern saves context on exit and preloads it on entry — no manual intervention required.

```
┌──────────────────────────────────────────────────────────┐
│ Session Start                                            │
│   │                                                      │
│   ▼                                                      │
│ PreloadMemoryTool ─── Fetch user facts, preferences,     │
│                        past decisions from MemoryService │
│   │                                                      │
│   ▼                                                      │
│ [Agent conversation] ─── Uses preloaded context           │
│   │                        Accumulates new facts          │
│   ▼                                                      │
│ Session End                                              │
│   │                                                      │
│   ▼                                                      │
│ after_agent_callback ─── Auto-save new facts,             │
│                           updated preferences,            │
│                           decisions to MemoryService      │
└──────────────────────────────────────────────────────────┘
```

### PreloadMemoryTool — Load on Entry

```python
"""preload_memory_tool.py — Load user memory at session start."""
from google.adk.tools import ToolContext


def preload_memory(tool_context: ToolContext) -> dict:
    """Tool that loads user memory into session state on first turn.

    Register this as a tool on the entry agent. The model calls it
    automatically when it needs user context.
    """
    user_id = tool_context.user_id
    memory_service = tool_context.memory_service

    # Search recent memories
    facts = memory_service.search(f"user {user_id} preferences facts decisions", user_id=user_id)

    # Load into session state for easy access
    tool_context.state["user_facts"] = [
        {"content": m.content, "category": m.metadata.get("category", "general")}
        for m in facts
    ]
    tool_context.state["memory_loaded"] = True

    return {
        "status": "ok",
        "facts_loaded": len(facts),
        "summary": "\n".join(f["content"] for f in tool_context.state["user_facts"][:5]),
    }
```

### Auto-Save Callback — Save on Exit

```python
"""auto_save_callback.py — Persist learned facts on session exit."""
from google.adk.memory import FirestoreMemoryService


async def after_agent_auto_save(callback_context):
    """After each agent turn, extract and save any new facts learned.

    The agent instruction should mark facts with:
    [REMEMBER: <fact>]
    or use a structured output tool to record facts.
    """
    response = callback_context.state.get("agent_response", "")
    user_id = callback_context.user_id
    memory_service = callback_context.memory_service

    # Extract marked facts
    import re
    facts = re.findall(r"\[REMEMBER:\s*(.+?)\]", response)
    for fact in facts:
        await memory_service.save(
            content=fact.strip(),
            user_id=user_id,
            metadata={
                "category": "learned_fact",
                "session_id": callback_context.session_id,
                "timestamp": callback_context.state.get("timestamp", ""),
            },
        )

    # Track what was learned this session
    if facts:
        callback_context.state.setdefault("new_facts_this_session", []).extend(facts)
        logger.info(f"Auto-saved {len(facts)} facts for user {user_id}")
```

### Wiring

```python
entry_agent = LlmAgent(
    name="learning_agent",
    model="gemini-2.5-flash",
    instruction="""You are a personal assistant that learns about the user over time.
    When you learn a new fact about the user, mark it with [REMEMBER: <fact>].
    Use preload_memory() at the start of each session to recall past facts.""",
    tools=[preload_memory],
    after_agent_callback=after_agent_auto_save,
)
```

## adk-redis: Redis Memory Service Patterns

Three integration patterns for using Redis as a memory backend with ADK. Redis provides sub-millisecond retrieval for session and memory caching.

### Pattern 1: Framework-Managed (Simplest)

```python
"""Redis as drop-in MemoryService via ADK Redis plugin."""
import os
from google.adk.memory import RedisMemoryService

memory_service = RedisMemoryService(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
)

runner = Runner(
    app_name="my_app",
    agent=root_agent,
    session_service=session_service,
    memory_service=memory_service,
)
# ADK handles all read/write. No custom code needed.
```

Best for: Standard use cases, minimal customization, fastest setup.

### Pattern 2: LLM-Controlled REST Tools

```python
"""Redis as tools the LLM controls explicitly."""
import redis.asyncio as redis

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))


async def search_memory(query: str, user_id: str, top_k: int = 5) -> dict:
    """Vector search over user memories stored in Redis with RedisVL."""
    # RedisVL vector search
    results = await r.ft("memories_idx").search(
        query=f"(@user_id:{user_id}) => [KNN {top_k} @embedding $vec AS score]",
        query_params={"vec": embed_query(query)},
    )
    return {
        "matches": [
            {"content": doc.content, "score": float(doc.score)}
            for doc in results.docs
        ]
    }


async def save_memory(user_id: str, content: str, metadata: dict = {}) -> dict:
    """Save a memory with vector embedding for semantic search."""
    embedding = embed_text(content)
    await r.hset(
        f"memory:{user_id}:{uuid4().hex[:12]}",
        mapping={
            "content": content,
            "embedding": embedding.tobytes(),
            "metadata": json.dumps(metadata),
            "user_id": user_id,
        },
    )
    return {"status": "ok"}


agent = LlmAgent(
    name="redis_agent",
    tools=[search_memory, save_memory],  # LLM controls memory ops
)
```

Best for: Fine-grained LLM control, custom schema, multi-index search.

### Pattern 3: MCP Tools

```python
"""Redis exposed via MCP server — language-agnostic, process-isolated."""
# mcp_servers/redis_memory_server.py
from mcp.server import Server, stdio
from mcp.types import Tool, TextContent

server = Server("redis-memory")


@server.tool()
async def search_user_memory(query: str, user_id: str) -> list[dict]:
    """Semantic search over user memories."""
    results = await redis_client.ft("memories_idx").search(
        f"@user_id:{user_id} => [KNN 5 @embedding $vec AS score]",
        {"vec": embed(query)},
    )
    return [{"content": d.content, "score": d.score} for d in results.docs]


@server.tool()
async def save_user_memory(user_id: str, content: str) -> dict:
    """Persist a fact about the user."""
    key = f"memory:{user_id}:{uuid4().hex[:12]}"
    await redis_client.hset(key, mapping={
        "content": content, "user_id": user_id, "embedding": embed(content),
    })
    return {"status": "ok", "key": key}


# Client side — MCPToolset
agent = LlmAgent(
    name="mcp_redis_agent",
    tools=[MCPToolset(
        connection_params=StdioServerParameters(
            command="python3", args=["mcp_servers/redis_memory_server.py"],
        ),
        tool_filter=["search_user_memory", "save_user_memory"],
    )],
)
```

Best for: Cross-language workflows (Python agent, Go memory server), process isolation, reusable memory infrastructure.

### RedisVL Semantic Caching

```python
"""Cache model responses with semantic similarity matching."""
import hashlib

async def semantic_cache(query: str, threshold: float = 0.85) -> dict | None:
    """Check if semantically similar query has a cached response."""
    results = await r.ft("cache_idx").search(
        f"=> [KNN 1 @embedding $vec AS score]",
        {"vec": embed_query(query)},
    )
    if results.docs and float(results.docs[0].score) >= threshold:
        return json.loads(results.docs[0].response)
    return None

async def cache_response(query: str, response: str, ttl: int = 3600):
    """Cache response with semantic embedding for future hits."""
    key = f"cache:{hashlib.sha256(query.encode()).hexdigest()[:16]}"
    await r.hset(key, mapping={
        "query": query, "response": response,
        "embedding": embed_query(query).tobytes(),
    })
    await r.expire(key, ttl)
```

### Redis Hybrid Search

```python
"""Combine full-text + vector search for precise memory retrieval."""
async def hybrid_search(user_id: str, query: str, filters: dict = {}) -> list[dict]:
    """FT.SEARCH with both text and vector components."""
    filter_parts = [f"@user_id:{user_id}"]
    for k, v in filters.items():
        filter_parts.append(f"@{k}:{v}")

    results = await r.ft("memories_idx").search(
        f"({' '.join(filter_parts)}) => [KNN 10 @embedding $vec AS vector_score]",
        {"vec": embed_query(query)},
        sort_by="vector_score",
        return_fields=["content", "category", "timestamp"],
    )
    return [{"content": d.content, "score": d.vector_score, **d.__dict__}
            for d in results.docs]
```

## Custom Memory Backend Implementations

### Milvus (Billion-Scale Vector DB)

```python
"""MilvusMemoryService — user-isolated vector search at scale."""
from pymilvus import MilvusClient, DataType


class MilvusMemoryService:
    """Billion-scale memory backend with per-user collection partitioning."""

    def __init__(self, uri: str = "http://localhost:19530"):
        self.client = MilvusClient(uri=uri)

    async def search(self, query: str, user_id: str, top_k: int = 10) -> list[dict]:
        embedding = embed_query(query)
        results = self.client.search(
            collection_name="agent_memories",
            data=[embedding],
            anns_field="embedding",
            limit=top_k,
            # User isolation via partition key — critical for multi-tenant
            expr=f'user_id == "{user_id}"',
            output_fields=["content", "category", "timestamp"],
        )
        return [
            {"content": h.entity.get("content"), "score": h.distance}
            for h in results[0]
        ]

    async def save(self, user_id: str, content: str, metadata: dict = {}):
        embedding = embed_query(content)
        self.client.insert(
            collection_name="agent_memories",
            data=[{
                "user_id": user_id,  # Partition key
                "content": content,
                "embedding": embedding,
                "category": metadata.get("category", "general"),
                "timestamp": metadata.get("timestamp", ""),
            }],
        )


# Create collection with user_id as partition key
client.create_collection(
    collection_name="agent_memories",
    dimension=768,
    partition_key_field="user_id",  # Enforced user isolation
    metric_type="COSINE",
)
```

### Firestore (GCP NoSQL)

```python
"""FirestoreMemoryService — serverless document memory."""
from google.cloud import firestore_async


class FirestoreMemoryService:
    """Memory backend for serverless GCP deployments."""

    def __init__(self, project_id: str):
        self.db = firestore_async.Client(project=project_id)

    async def search(self, query: str, user_id: str, limit: int = 10) -> list[dict]:
        """Simple keyword search — for semantic search use with Vertex AI embeddings."""
        docs = self.db.collection("memories")
        results = (
            await docs.where("user_id", "==", user_id)
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [doc.to_dict() for doc in results]

    async def save(self, user_id: str, content: str, metadata: dict = {}):
        await self.db.collection("memories").add({
            "user_id": user_id,
            "content": content,
            "metadata": metadata,
            "timestamp": firestore_async.SERVER_TIMESTAMP,
        })

    async def delete_user_memories(self, user_id: str):
        """GDPR: delete all memories for a user."""
        docs = await self.db.collection("memories").where("user_id", "==", user_id).get()
        for doc in docs:
            await doc.reference.delete()
```

### cognee (Knowledge Graph Memory)

```python
"""CogneeMemoryService — graph-based memory with entity relationships."""
import cognee


class CogneeMemoryService:
    """Knowledge graph memory for entity-aware reasoning.

    Use when: relationships between facts matter (e.g., "Alice works at Acme",
    "Acme competitor is BetaCorp", agent should infer competitive context).
    """

    async def save(self, user_id: str, content: str):
        """Add fact to knowledge graph. cognee extracts entities and relationships."""
        await cognee.add(
            f"user:{user_id}",
            content,
            dataset_name=f"user_{user_id}",
        )

    async def search(self, user_id: str, query: str, top_k: int = 10) -> list[dict]:
        """Search with graph-aware retrieval — returns related entities too."""
        results = await cognee.search(
            query,
            dataset_name=f"user_{user_id}",
            k=top_k,
            include_related=True,  # Follow entity edges
        )
        return [
            {"content": r.content, "entities": r.entities, "score": r.score}
            for r in results
        ]

    async def get_entity_graph(self, user_id: str, entity: str) -> dict:
        """Get all relationships for an entity across all user facts."""
        graph = await cognee.get_graph(
            dataset_name=f"user_{user_id}",
            center_entity=entity,
            depth=2,  # 2-hop neighborhood
        )
        return graph
```

**Backend selection guide:**

| Backend | Scale | Latency | Best For |
|---------|-------|---------|----------|
| Vertex AI Memory Bank | <1M docs | <50ms | GCP-native, simplest setup |
| adk-redis | <10M docs | <1ms | Ultra-low latency caching, session memory |
| Milvus | >1B docs | <100ms | Enterprise-scale vector search with user isolation |
| Firestore | <100K docs | <200ms | Serverless GCP deployments, no ops |
| cognee | <1M entities | <500ms | Relationship-aware reasoning, entity graphs |

## Production Checklist

- [ ] SessionService backend matches scale: InMemory for dev, Firestore for serverless, Spanner for global
- [ ] State keys use namespaced prefixes to avoid collisions
- [ ] `output_key` naming follows convention: `agent_name_result`
- [ ] Token budget monitoring enabled in production
- [ ] Summarization triggers configured for context window management
- [ ] Persistent user memory has TTL or cleanup policy (GDPR compliance)
- [ ] Session checkpoints for long-running workflows (>5 min)
- [ ] Memory service credentials use secret manager
- [ ] Session data encrypted at rest (all managed backends do this)
