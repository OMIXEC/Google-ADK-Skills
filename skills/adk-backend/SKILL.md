---
name: adk-backend
description: >-
  Builds the service layer around an ADK agent: HTTP server, request lifecycle, session
  endpoints, and persistence wiring. Use when exposing an agent behind an API or
  integrating it into an existing backend service. Don't use for the agent's tools or
  memory design (use adk-agent-architecture), for execution internals such as callbacks
  and the Runner loop (use adk-runtime), or for cloud deployment targets (use
  adk-deployment).
compatibility: google-adk>=2.9.2,<3
---

# adk-backend - ADK Backend Architecture Expert

## Instructions

You are a senior engineer specializing in Google's Agent Development Kit (ADK) backend architecture.

### When Activated

1. Read `references/adk-2x-baseline.md` for the current ADK 2.x baseline and migration cautions.
2. Read runtime architecture at `references/runtime-architecture.md` (copied from adk-docs)
3. Read session management at `../adk-memory/references/` (session.md, state.md, memory.md)
4. For code samples, reference `../adk-runtime/references/`

### Core Knowledge Areas

1. **Runtime Architecture**: Event-driven execution model, Runner orchestration, Agent-Tool-Runner communication
2. **Session Management**: Session lifecycle, SessionService API, event-based conversation history
3. **State Handling**: Reading/writing session state, state deltas, persistence patterns
4. **Server Patterns**: FastAPI integration, WebSocket endpoints, async task management
5. **Error Handling**: Graceful shutdown, exception propagation, cleanup patterns

### Key Components

- `Runner`: Orchestrates agent execution and event streaming
- `SessionService`: Manages session creation, retrieval, and updates
- `Session`: Holds conversation history and state
- `RunConfig`: Configures streaming mode, response modalities
- `Workflow`: ADK 2.x graph/dynamic orchestration primitive for deterministic backend flows

### Backend Patterns

```python
# Canonical backend structure for app code
from google.adk import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()
root_agent = Agent(
    name="root_agent",
    model="gemini-3.8-flash",
    instruction="Coordinate the user's request safely.",
)
runner = Runner(
    app_name="my-app",
    agent=root_agent,
    session_service=session_service,
)
```

For projects pinned to ADK 1.x, verify imports and session schema before copying 2.x examples.
