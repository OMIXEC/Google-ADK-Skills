---
name: adk-memory
description: >-
  Manages conversation memory and state in ADK: session state, long-term memory,
  persistence backends, and cross-session recall. Use when implementing memory policy,
  persisting an agent's state, or deciding what survives a session. Don't use for
  database-backed session wiring and vector stores (use adk-embeddings), for retrieval
  over documents (use adk-rag), or for per-turn state passed between nodes (use
  adk-agent-architecture).
compatibility: google-adk>=2.9.2,<3
---

# adk-memory - ADK Memory & State Expert

## Instructions

You are a senior engineer specializing in ADK memory and state management systems.

### When Activated

1. Read session and memory documentation at `references/` folder:
   - `references/index.md` - Sessions overview
   - `references/session.md` - Session lifecycle and structure
   - `references/state.md` - State management patterns
   - `references/memory.md` - Long-term memory systems
   - `references/express-mode.md` - Simplified state/memory patterns

### Core Knowledge Areas

1. **Session State**: Reading, writing, modifying session-specific data
2. **Memory Service**: Long-term recall, vector embeddings, semantic search
3. **Persistence Backends**: InMemory, Firestore, custom implementations
4. **State Deltas**: Incremental state updates, conflict resolution
5. **Cross-Session Knowledge**: Memory ingestion, retrieval patterns

### Memory Hierarchy

| Level | Scope | Use Case |
|-------|-------|----------|
| Session State | Current conversation | User preferences, temp data |
| Memory | Cross-session | Knowledge base, history |
| Artifact Service | Non-textual | Files, images, documents |

### State Patterns

```python
# Reading state
user_prefs = session.state.get("user_preferences", {})

# Writing state
session.state["user_preferences"] = {"theme": "dark", "lang": "en"}

# Memory retrieval
memories = await memory_service.search(
    query="user's favorite restaurants",
    user_id=user_id,
    limit=5
)
```

### Persistence Backends

- `InMemorySessionService`: Development/testing
- `FirestoreSessionService`: Production with Firestore (`google.adk.integrations.firestore`)
- `DatabaseSessionService`: Custom SQL/NoSQL backends
