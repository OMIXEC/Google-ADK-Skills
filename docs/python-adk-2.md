# Python ADK 2.x Reference

Use this reference before writing or updating Python ADK code. It reflects the current `google/adk-python` 2.x line checked from Context7 plus the official GitHub repository and ADK docs.

## Version Baseline

- Latest observed GitHub release: `v2.3.0` (`google-adk`), released 2026-06-18.
- Package: `google-adk>=2.3.0,<3` for new production Python projects unless a project explicitly pins a tested lower version.
- Python requirement: `>=3.10`; official metadata advertises Python 3.10 through 3.14.
- ADK 2.0 includes breaking changes from 1.x in the agent API, event model, and session schema.
- ADK 2.0 sessions are readable by ADK 1.28+ with extra fields ignored, but are incompatible with older 1.x versions.

## Core Imports

Prefer the top-level 2.x API in examples:

```python
from google.adk import Agent, Workflow
```

Use module imports only when a concrete API requires them:

```python
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.runners import Runner, RunConfig, StreamingMode
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool, google_search, exit_loop
from google.adk.tools.mcp_tool import McpToolset
from mcp import StdioServerParameters
```

## Agent and Workflow Guidance

- `Agent` defines model behavior, instruction, tools, and sub-agent delegation.
- `Workflow` is the 2.x graph-based orchestration primitive for deterministic flows.
- Prefer `Workflow` for branching, fan-out/fan-in, loops, retries, dynamic nodes, human input, and nested workflows.
- `SequentialAgent`, `ParallelAgent`, and `LoopAgent` remain useful deterministic template workflows, but official docs say Python 2.0 supersedes template workflows with graph-based and dynamic workflows for new complex work.
- Use `output_key` to store intermediate agent output in session state for downstream nodes.
- Preserve the ADK constraint: an LLM agent using `output_schema` must not also declare tools or tool-based transfer behavior. Split reasoning/schema leaves from tool leaves.

## Task API and A2A

- ADK 2.x adds a Task API for structured agent-to-agent delegation, multi-turn task mode, single-turn controlled output, mixed delegation patterns, human-in-the-loop, and task agents as workflow nodes.
- A2A support is documented for Python but marked experimental. Treat remote delegation as a production integration boundary: explicit agent cards, auth propagation, timeouts, retries, circuit breakers, and sanitized telemetry are required.
- Do not assume older `RemoteA2AAgent` examples are current without checking the latest `google/adk-python` source or API reference.

## MCP Tools

Current MCP examples use `McpToolset` as an agent toolset:

```python
from google.adk import Agent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

filesystem = McpToolset(
    connection_params=StdioConnectionParams(server_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    )),
    tool_filter=["read_file", "list_directory"],
    tool_name_prefix="fs_",
)

root_agent = Agent(
    name="mcp_agent",
    model="gemini-3.5-flash",
    instruction="Use filesystem tools only when needed.",
    tools=[filesystem],
)
```

For remote MCP servers, use the current connection-parameter class from ADK/MCP docs and require auth, allowlisted tools, timeout/retry, and confirmation for side effects.

## Live and Streaming

- Keep Live API work on `RunConfig` plus `runner.run_live(...)` with a `LiveRequestQueue`.
- Prefer current live-capable model IDs from the project model router. Avoid stale `gemini-2.0-flash-exp` and `gemini-2.0-flash-live-001` examples unless the target project explicitly still supports them.
- `gemini-3.1-flash-live-preview` is the preferred live model for low-latency speech (see the adk-model-routing skill).
- ADK 2.3.0 release notes include Live API translation config in `RunConfig` and model-specific input transcription handling for Gemini Live 3.1 models.

## Migration Checklist From 1.x

1. Replace stale model examples (`gemini-2.0-flash*`) with `gemini-3.1-flash-lite`, `gemini-3.5-flash`, or `gemini-3.1-pro-preview` based on task complexity.
2. Replace hand-rolled graph examples built around older `GraphAgent` imports with `Workflow` unless the project has verified a current graph compatibility API.
3. Audit callback examples against the latest callback docs. Do not rely on old `RunnerCallbacks` names without source verification.
4. Audit sessions for 2.x schema compatibility before rolling forward production traffic.
5. Re-run focused runtime, session, memory, tool, MCP, A2A, and Live tests after changing a project from `google-adk` 1.x to 2.x.
