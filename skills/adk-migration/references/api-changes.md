# API Changes — ADK 1.x → 2.3 (old → new)

Verified through Context7 `/google/adk-docs` and the local `adk-python-v2.3/`
mirror when present. Each block shows the removed/deprecated 1.x form and the
2.3 replacement.

## Graph workflows

`GraphAgent` / `builder.add_node` / `add_edge` / `Condition` /
`google.adk.agents.graph` are **gone**. Use `Workflow` + `node()` + `Edge` +
`JoinNode`.

```python
# 1.x (removed)
from google.adk.agents.graph import GraphAgent, Node, Edge, Condition
builder = GraphAgent()
builder.add_node("plan", plan_fn)
builder.add_edge("plan", "search", condition=Condition(...))

# 2.3
from google.adk import Workflow
from google.adk.workflow import node, Edge, JoinNode, START

@node
def plan(ctx): ...

workflow = Workflow(edges=[
    Edge(from_node=START, to_node="plan"),
    Edge(from_node="plan", to_node="search", route=...),
])
```

Fan-in uses `JoinNode` (waits for all named predecessors). `Edge` fields are
`from_node` / `to_node` / `route` — not `source` / `target` / `condition`.

## Agent modes & schema rule

```python
# 2.3: mode is explicit
agent = LlmAgent(model="gemini-3.5-flash", name="worker",
                 mode="task")   # 'chat' | 'task' | 'single_turn'
```

An `LlmAgent` with `output_schema` must have **no** tools / sub-agents / transfer.
Split reasoning (schema) and acting (tools) into separate leaves.

## Human-in-the-loop / resume

```python
# 1.x
answer = ctx.resume_data["approval"]

# 2.3
answer = ctx.resume_inputs["approval"]   # keyed by interrupt id
```

Use the `request_input` tool (`google.adk.tools`) to pause; `rerun_on_resume`
controls replay.

## MCP tools

```python
# 1.x (deprecated)
from google.adk.tools.mcp_tool import MCPToolset
toolset = MCPToolset(connection_params=StdioServerParameters(command="npx", args=[...]))

# 2.3
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters
toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(command="npx", args=[...]),
    ),
)
```

`McpToolset` is the class (`MCPToolset` is a deprecated alias). Passing
`StdioServerParameters` directly to `connection_params` is deprecated — wrap it in
`StdioConnectionParams`. SSE/HTTP use `SseConnectionParams`.

## Built-in code execution

```python
# 1.x (not importable in 2.3)
from google.adk.tools import code_execution
agent = LlmAgent(..., tools=[code_execution, other_tool])

# 2.3
from google.adk.code_executors import BuiltInCodeExecutor
agent = LlmAgent(..., code_executor=BuiltInCodeExecutor())  # NOT in tools=
```

## Memory service import

```python
# 1.x
from google.adk.sessions import VertexAiMemoryBankService
# 2.3
from google.adk.memory import VertexAiMemoryBankService
```

## A2A

```python
# 1.x casing
from google.adk.agents import RemoteA2AAgent
# 2.3
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a   # expose an agent
```

## Deploy CLI

```bash
# 1.x
adk deploy cloud-run ...
adk deploy vertex ...
# 2.3 (underscored subcommands)
adk deploy cloud_run ...
adk deploy agent_engine ...
```

## Sample / Workflow imports

```python
# wrong / 1.x
from google.adk.workflow._workflow_class import Workflow
# 2.3
from google.adk import Workflow
from google.adk.workflow import node, Edge, JoinNode, START
```
