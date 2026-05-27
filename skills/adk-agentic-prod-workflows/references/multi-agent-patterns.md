# Multi-Agent Coordination Patterns

## Pattern Catalog

### 1. Pipeline Pattern

Linear chain: Agent A → Agent B → Agent C.

```
[Input] → [Writer] → [Reviewer] → [Publisher] → [Output]
```

**When**: Ordered processing, each step depends on previous output.
**Implementation**: `SequentialAgent` or graph workflow with linear edges.
**Failure mode**: If step N fails, pipeline halts. Add dead-letter queue for failed outputs.

```python
pipeline = SequentialAgent(
    name="doc_pipeline",
    sub_agents=[writer, reviewer, publisher]
)
```

### 2. Coordinator/Dispatcher Pattern

Single coordinator delegates to specialized workers.

```
                      ┌→ [Billing Agent]
[User] → [Coordinator] ┼→ [Technical Agent]
                      └→ [General Agent]
```

**When**: Heterogeneous request types, one entry point, specialized handlers.
**Implementation**: Agent with `sub_agents` + LLM routing, or `IntentRouter` for keyword-based.

```python
coordinator = Agent(
    name="support_coordinator",
    model="gemini-2.5-flash",
    sub_agents=[billing, technical, general],
    instruction="Route to billing for payment questions, "
                "technical for bug reports, general otherwise."
)
```

**Anti-pattern**: Coordinator becoming monolithic. Keep coordinator instruction routing-only; move business logic to workers.

### 3. Hierarchical Pattern

Manager → Team Leads → Workers. Multi-level delegation.

```
                         ┌→ [Frontend Team Lead] ──→ [UI Dev] + [UX Dev]
[Manager] ──→ [Tech Lead] ┤
                         └→ [Backend Team Lead] ──→ [API Dev] + [DB Dev]
```

**When**: Complex domains where sub-teams need their own coordination.
**Implementation**: Nested agents — each team lead is itself an Agent with `sub_agents`.

```python
frontend_lead = Agent(
    name="frontend_lead",
    sub_agents=[ui_dev, ux_dev],
    instruction="Coordinate frontend: delegate UI to ui_dev, UX to ux_dev."
)

manager = Agent(
    name="manager",
    sub_agents=[tech_lead, frontend_lead, backend_lead],
    instruction="Plan project, delegate to team leads, synthesize results."
)
```

### 4. Collaborative Pattern

Peer agents share state, work toward common goal.

```
[RAG Agent] ←→ [Shared Memory] ←→ [Planner Agent]
    ↑                                  ↑
    └──────── [Reviewer Agent] ────────┘
```

**When**: Research, analysis, creative tasks where agents build on each other's work.
**Implementation**: Agents reading/writing `session.state["shared_context"]`.

```python
session.state["shared_context"] = {
    "research_findings": [],
    "analysis_results": {},
    "final_report": None
}

researcher = Agent(
    name="researcher",
    instruction="Store findings in session.state['shared_context']['research_findings']"
)
analyst = Agent(
    name="analyst",
    instruction="Read from research_findings, write to analysis_results"
)
```

### 5. Swarm/Fan-Out Pattern

Single request broadcast to N workers, results aggregated.

```
              ┌→ [Worker 1]
[Request] → [Fan-Out] ┼→ [Worker 2]  → [Aggregator] → [Result]
              └→ [Worker 3]
```

**When**: Multi-source search, independent validations, ensemble methods.
**Implementation**: `ParallelAgent` for template, or `asyncio.gather` for dynamic.

```python
# Template approach
parallel = ParallelAgent(
    name="multi_search",
    sub_agents=[web_search, doc_search, db_search]
)

# Dynamic approach
async def fan_out(workers, input):
    tasks = [worker.process(input) for worker in workers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return aggregate(results)
```

### 6. A2A (Agent-to-Agent) Remote Pattern

Agents communicate over HTTP via agent cards. Cross-service, cross-language. See `references/a2a-deep-dive.md` for full protocol reference.

```
[Python Agent] ──HTTP/A2A──→ [Go Agent] ──HTTP/A2A──→ [TS Tool Server]
```

**When**: Distributed systems, cross-language, separate deployment units.
**Implementation**: `RemoteA2AAgent` wrapping remote agent cards.

```python
from google.adk.agents import RemoteA2AAgent
from google.adk.a2a import AgentCard

# Client side — calling a remote agent
remote_agent = RemoteA2AAgent(
    name="go_processor",
    agent_card=AgentCard(
        name="Go Processor",
        url="https://processor-service.run.app",
        capabilities={"streaming": True},
        auth_scheme="bearer_token",
    ),
)

# Server side — exposing your agent via A2A
from google.adk.a2a import A2AServer
server = A2AServer(
    agent=my_agent,
    card=AgentCard(
        name="My Python Agent",
        description="Handles X and Y",
        url="https://my-agent.run.app",
        capabilities={"streaming": True, "a2a": True},
        auth_scheme="bearer_token",
    ),
)
```

**Cross-language A2A**: Python↔Go↔TS via standard JSON-RPC 2.0 serialization. Each side uses native ADK SDK. No shared code needed.

**Auth propagation**: GCP identity tokens, Firebase tokens, or API keys sent as `Authorization: Bearer <token>` in A2A requests. Token validated at receiving end.

**Service discovery**:
- **Static**: Agent card URLs in config/environment
- **Dynamic**: Agent card registry (GCS bucket, Firestore collection, custom registry service)

### 7. MCP-Based Coordination Pattern

Coordination via shared MCP tool servers instead of direct agent-to-agent calls. See `references/mcp-integration.md` for full protocol reference.

```
[Coordinator Agent] ──MCPToolset──→ [MCP Server: DB Tools]
       │
       ├──MCPToolset──→ [MCP Server: API Tools]
       │
       └──MCPToolset──→ [MCP Server: Search Tools]
```

**When**: Tool-first architectures where agents share tool servers; side-effect isolation across language boundaries; centralized tool governance.

**Implementation**:

```python
from google.adk.tools import MCPToolset
from google.adk.tools.mcp import StdioServerParameters

coordinator = Agent(
    name="mcp_coordinator",
    model="gemini-2.5-flash",
    instruction="Use tools from connected MCP servers to complete tasks.",
    tools=[
        MCPToolset(connection_params=StdioServerParameters(
            command="python3", args=["mcp_servers/db_server.py"]
        )),
        MCPToolset(connection_params=StdioServerParameters(
            command="python3", args=["mcp_servers/api_server.py"]
        )),
    ],
)
```

**MCP vs A2A decision**:
| Factor | MCP | A2A |
|--------|-----|-----|
| Communication model | Tool calls (request/response) | Agent messages (delegation) |
| State | Stateless (tools are stateless) | Stateful (agents have memory) |
| Language boundary | Tools in any language via stdio/SSE | Agents in any language via HTTP |
| Best for | External APIs, DB access, utilities | Agent delegation, complex reasoning |

## Pattern Selection Guide

| Requirement | Pattern |
|-------------|---------|
| Fixed order processing | Pipeline |
| Heterogeneous requests, one entry | Coordinator/Dispatcher |
| Complex multi-team | Hierarchical |
| Shared knowledge building | Collaborative |
| Independent parallel tasks | Swarm/Fan-Out |
| Cross-service, cross-language (agent delegation) | A2A Remote |
| Shared tool servers, side-effect isolation | MCP-Based Coordination |

## Production Rules

1. **Timeout every delegation**: Coordinator → Worker should have deadline.
2. **Error isolation**: Worker failure must not crash coordinator.
3. **State hygiene**: Workers write results, never read/write arbitrary state.
4. **Correlation ID**: Pass through all delegations for tracing.
5. **Max delegation depth**: Limit hierarchical depth (recommend: 3 max).
