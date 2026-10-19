# ADK 2.x Baseline

Version and API facts this skill depends on. Checked against
`google/adk-python@v2.12.0` (SHA `38381f65f2bee0f70a89f938ee64e51b34916fa7`).

## Version baseline

- Target: `google-adk>=2.9.2,<3`; validated through **2.12.0** (2026-10-13).
- Python: **3.10** for 2.9.2–2.11.0; **3.11** for 2.12.0. Supported through 3.15.
- The **1.x line still ships in parallel** (1.39.1). 2.x is not a drop-in
  replacement for every 1.x project.
- The SDK is never vendored. Import from the installed `google.adk.*`.
- 2.x changed the agent API, event model, and session schema. Sessions written
  by 2.x are readable by 1.28+ with extra fields ignored; older 1.x cannot read
  them.

## Core imports

```python
from google.adk import Agent, Workflow
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.runners import Runner, RunConfig, StreamingMode
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool, google_search, exit_loop
```

Import only what the task needs. Prefer the top-level `Agent` / `Workflow`
surface in examples.

## Agent and workflow rules

- `Agent` holds model, instruction, tools, and sub-agent delegation.
- `Workflow` is the 2.x graph primitive: branching, fan-out/fan-in, loops,
  retries, dynamic nodes, human input, nested workflows.
- `SequentialAgent`, `ParallelAgent`, and `LoopAgent` remain valid deterministic
  templates; prefer `Workflow` for new complex orchestration.
- `output_key` stores a node's output in session state for downstream nodes.
- An LLM agent with `output_schema` must not also declare tools or tool-based
  transfer. Split schema leaves from tool leaves.

## Model IDs

Prefer current IDs: `gemini-3.5-flash`, `gemini-3.1-flash-lite`,
`gemini-3.1-pro-preview`, `gemini-3.1-flash-live-preview` (live audio).
Avoid stale `gemini-2.0-flash*` examples unless the project pins them.

## Migration cautions

1. Replace stale model IDs with the current set above.
2. Replace pre-2.x graph examples with `Workflow` unless a compatibility API is
   verified.
3. Audit callbacks against current source; do not rely on old callback names.
4. Audit sessions for 2.x schema compatibility before shifting traffic.
5. Re-run runtime, session, memory, tool, MCP, A2A, and Live tests after a 1.x
   to 2.x move.
