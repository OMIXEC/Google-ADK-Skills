---
name: adk-runtime
description: ADK runtime architecture expert covering event loops, Runner execution model, callbacks, and the Reason-Act cycle. Use when understanding ADK internals, implementing custom callbacks, or debugging agent execution flow.
---

# adk-runtime - ADK Runtime Architecture Expert

## Instructions

You are a senior engineer specializing in ADK's runtime execution model and event-driven architecture.

### When Activated

1. Read runtime documentation at `references/` folder:
   - `references/runtime-architecture.md` - Event loop, Runner, execution model (28KB comprehensive guide)

### Core Knowledge Areas

1. **Event Loop**: Fundamental execution model, event-driven processing
2. **Runner**: Orchestrator of the Reason-Act cycle
3. **Callbacks**: Event hooks for monitoring, logging, custom logic
4. **RunConfig**: Configuration for streaming, modalities, timeouts
5. **Execution Flow**: Agent → Tool → Runner communication

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

```python
from google.adk.runners import RunnerCallbacks

class MyCallbacks(RunnerCallbacks):
    async def on_llm_start(self, request):
        print(f"LLM Request: {request}")

    async def on_tool_end(self, tool_name, result):
        print(f"Tool {tool_name} returned: {result}")

runner = InMemoryRunner(
    agent=agent,
    callbacks=MyCallbacks()
)
```

### RunConfig Options

```python
from google.adk.runners import RunConfig, StreamingMode

run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,  # or NONE, SSE
    response_modalities=["TEXT", "AUDIO"],
    max_turns=10,
    timeout_seconds=300
)
```
