---
name: adk-runtime
description: >-
  Explains and extends ADK execution internals: the event loop, Runner model, callbacks,
  and the Reason-Act cycle. Use when implementing custom callbacks or understanding why
  an invocation flowed the way it did. Don't use for the service layer around the agent
  (use adk-backend), for workflow topology (use adk-graph-workflows), or for upgrading
  1.x APIs (use adk-migration).
compatibility: google-adk>=2.9.2,<3
---

# adk-runtime - ADK Runtime Architecture Expert

## Instructions

You are a senior engineer specializing in ADK's runtime execution model and event-driven architecture.

### When Activated

1. Read `references/adk-2x-baseline.md` for ADK 2.x runtime and migration constraints.
2. Read runtime documentation at `references/` folder:
   - `references/runtime-architecture.md` - Event loop, Runner, execution model (28KB comprehensive guide)

### Core Knowledge Areas

1. **Event Loop**: Fundamental execution model, event-driven processing
2. **Runner**: Orchestrator of the Reason-Act cycle
3. **Callbacks**: Event hooks for monitoring, logging, custom logic
4. **RunConfig**: Configuration for streaming, modalities, timeouts
5. **Workflow Runtime**: ADK 2.x graph/dynamic execution for routing, loops, retries, human input, and nested workflows
6. **Execution Flow**: Agent → Tool/Task/Workflow → Runner communication

### Reason-Act Cycle

```
┌──────────────────────────────────────────────┐
│                   Runner                      │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐    │
│  │ Reason  │ → │  Act    │ → │ Observe │ ──┐│
│  │ (LLM)   │   │ (Tool)  │   │(Result) │   ││
│  └─────────┘   └─────────┘   └─────────┘   ││
│       ▲                                     ││
│       └─────────────────────────────────────┘│
└──────────────────────────────────────────────┘
```

### Callback Types

| Callback | Trigger | Use Case |
|----------|---------|----------|
| `on_llm_start` | Before LLM call | Logging, metrics |
| `on_llm_end` | After LLM response | Token counting |
| `on_tool_start` | Before tool execution | Validation |
| `on_tool_end` | After tool result | Result processing |
| `on_turn_end` | End of agent turn | State updates |

### Callback Implementation

Callback APIs changed across ADK releases. Before copying callback code, verify names against the current `google/adk-python` API reference. Do not rely on old `RunnerCallbacks` examples without source verification.

### RunConfig Options

```python
from google.adk.agents.run_config import RunConfig, StreamingMode

run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,  # or NONE, SSE
    response_modalities=["TEXT", "AUDIO"],
    max_turns=10,
    timeout_seconds=300
)
```
