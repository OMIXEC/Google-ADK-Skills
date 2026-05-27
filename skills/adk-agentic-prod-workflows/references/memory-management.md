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
