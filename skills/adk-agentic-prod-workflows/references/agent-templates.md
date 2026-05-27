# Agent Templates

## Template Catalog

Each template defines: role, instruction structure, tool set, and when to use.

### 1. ReAct Worker Agent

General-purpose reasoning + action agent. Core building block.

```python
from google.adk import Agent
from google.adk.tools import FunctionTool

def process_order(order_id: str, action: str) -> dict:
    """Process an order. Action: 'validate', 'fulfill', 'cancel'."""
    ...

agent = Agent(
    name="order_worker",
    model="gemini-2.5-flash",
    instruction="""You are an order processing agent.
    For each request:
    1. Identify the required action (validate, fulfill, cancel)
    2. Call process_order with the correct parameters
    3. Report the result clearly

    If the action is unclear, ask for clarification before proceeding.""",
    tools=[FunctionTool(process_order)]
)
```

**When**: Task execution where clear tools exist. Most common worker type.
**Key**: Tool-first design. Agent reasons about WHICH tool to call, tools do the work.

### 2. RAG Worker Agent

Retrieval-Augmented Generation worker with knowledge base access.

```python
from google.adk import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval

retrieval_tool = VertexAiRagRetrieval(
    rag_corpus="projects/{PROJECT}/locations/us-central1/ragCorpora/{CORPUS}"
)

agent = Agent(
    name="knowledge_worker",
    model="gemini-2.5-flash",
    instruction="""You are a knowledge assistant.
    Always search the knowledge base before answering.
    Cite sources when providing information.
    If the knowledge base lacks relevant information, state that clearly.""",
    tools=[retrieval_tool]
)
```

**When**: Document Q&A, support knowledge base, internal wiki search.
**Key**: Retrieval is a tool, not embedded in instructions. Model decides when to search.

### 3. Router/Dispatcher Agent

Routes requests to specialized sub-agents.

```python
router = Agent(
    name="router",
    model="gemini-2.5-flash",
    sub_agents=[billing_agent, tech_agent, general_agent],
    instruction="""You are a request router.
    Classify the user's request and delegate:
    - Payment, invoice, subscription → billing_agent
    - Bug reports, errors, technical → tech_agent
    - Everything else → general_agent

    Do not answer questions yourself. Only route.""",
)
```

**When**: Multi-domain support, intent-based routing, triage systems.
**Key**: Router instruction is routing-only. No business logic. Sub-agents handle actual work.

### 4. Planner/Coordinator Agent

Plans multi-step tasks then delegates execution.

```python
planner = Agent(
    name="planner",
    model="gemini-2.5-pro",  # Stronger model for planning
    instruction="""You are a task planner.
    1. Analyze the user's goal
    2. Break it into sequential steps
    3. For each step, identify which agent can execute it
    4. Track progress in session.state['plan']

    Available agents: researcher (info gathering), coder (implementation),
    reviewer (quality check), deployer (deployment).

    Start by creating a plan, then delegate step by step.""",
    sub_agents=[researcher, coder, reviewer, deployer]
)
```

**When**: Complex multi-step tasks, project execution, goal decomposition.
**Key**: Use stronger model for planning (Pro vs Flash). Keep plan visible in session state.

### 5. Live/Multimodal Agent

Real-time bidirectional streaming with audio/video.

```python
from google.adk import Agent
from google.adk.agents import LiveRequestQueue

live_agent = Agent(
    name="voice_assistant",
    model="gemini-2.5-flash-live",
    instruction="""You are a voice assistant.
    Respond conversationally. Keep answers brief (under 30 seconds spoken).
    Use tools for real-time data lookup when needed.""",
    tools=[weather_tool, search_tool]
)

# Streaming setup
queue = LiveRequestQueue()
runner.run_async(
    agent=live_agent,
    live_request_queue=queue,
    run_config=RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO", "TEXT"]
    )
)
```

**When**: Voice assistants, real-time multimodal chat, interactive demos.
**Key**: Separate streaming infra (WebSocket server) from agent logic. `adk web` dev-only.

## Template Selection Guide

| Requirement | Template |
|-------------|----------|
| Execute specific tasks with defined tools | ReAct Worker |
| Answer questions from documents/knowledge base | RAG Worker |
| Classify and route requests | Router/Dispatcher |
| Plan and orchestrate complex multi-step tasks | Planner/Coordinator |
| Real-time voice/video interaction | Live/Multimodal |
| Custom orchestration logic, state-machine workflows | CustomAgent |
| External tools via MCP protocol | MCP-Integrated Agent |

## CustomAgent Template

When standard agent types don't fit, subclass `BaseAgent` for custom orchestration:

```python
from google.adk.agents import BaseAgent

class CustomOrchestrator(BaseAgent):
    """Custom agent with programmatic control flow."""
    
    def __init__(self, name: str, workers: list):
        super().__init__(name=name)
        self.workers = workers
    
    async def _run_async_impl(self, ctx):
        # Custom pre-processing
        validated = await self._validate_input(ctx.session.state.get("query"))
        if not validated["ok"]:
            return {"status": "rejected", "reason": validated["reason"]}
        
        # Dynamic worker selection based on input
        worker = self._select_worker(validated["category"])
        
        # Custom retry logic
        for attempt in range(3):
            result = await worker.run(ctx)
            if result["status"] == "ok":
                break
        
        # Custom post-processing
        return self._format_output(result)
    
    def _select_worker(self, category: str):
        for w in self.workers:
            if w.handles(category):
                return w
        return self.workers[0]
```

**When to subclass BaseAgent vs compose:**
| Approach | Use when |
|----------|----------|
| Compose (use built-in types) | Standard patterns: sequential, parallel, graph, loop |
| Subclass BaseAgent | Custom execution order, state-machine, external control flow |

## MCP-Integrated Agent Template

Use `MCPToolset` to connect agents to external tool servers. See `references/mcp-integration.md` for full details.

```python
from google.adk import Agent
from google.adk.tools import MCPToolset, FunctionTool
from google.adk.tools.mcp import StdioServerParameters, SseServerParams

# Local MCP server (stdio transport)
local_mcp = MCPToolset(
    connection_params=StdioServerParameters(
        command="python3",
        args=["mcp_servers/db_tools.py"],
    )
)

# Remote MCP server (SSE transport)
remote_mcp = MCPToolset(
    connection_params=SseServerParams(
        url="https://tools.example.com/sse",
        headers={"Authorization": "Bearer ${TOOLS_API_KEY}"},
    )
)

agent = Agent(
    name="mcp_agent",
    model="gemini-2.5-flash",
    instruction="Use MCP tools for external operations. Use FunctionTool for internal logic.",
    tools=[
        FunctionTool(internal_helper),  # Pure functions, internal logic
        local_mcp,                      # DB access, local utilities
        remote_mcp,                     # External APIs, shared services
    ],
)
```

**MCP vs FunctionTool:**
| Factor | FunctionTool | MCPToolset |
|--------|-------------|------------|
| Location | Same process | Separate process/server |
| Language | Same as agent | Any language |
| Transport | In-process call | stdio / SSE / HTTP |
| Best for | Pure functions, internal logic | External APIs, DB access, multi-language tools |

## Async Tool Patterns

Long-running tools should be async to avoid blocking the event loop:

```python
import asyncio
from google.adk.tools import FunctionTool

async def async_api_call(query: str, timeout: float = 30.0) -> dict:
    """Async tool for external API calls."""
    try:
        result = await asyncio.wait_for(
            external_api.fetch(query),
            timeout=timeout,
        )
        return {"status": "ok", "data": result}
    except asyncio.TimeoutError:
        return {"status": "error", "error": f"Timeout after {timeout}s"}

# ADK FunctionTool handles async functions natively
api_tool = FunctionTool(async_api_call)
```

**Async tool rules:**
- Use `asyncio.wait_for` with explicit timeout
- Return structured error (never raise) for timeout
- Set `max_execution_time` on tool params for long operations

## Output Schema Validation

Use Pydantic `output_schema` to enforce structured output. **Important: `output_schema` disables tool calling for that agent.** See `references/output-validation.md`.

```python
from pydantic import BaseModel, Field

class AnalysisResult(BaseModel):
    summary: str = Field(description="One-paragraph summary")
    sentiment: str = Field(pattern=r"^(positive|negative|neutral)$")
    key_points: list[str] = Field(min_length=1, max_length=5)
    confidence: float = Field(ge=0.0, le=1.0)

analyzer = Agent(
    name="analyzer",
    model="gemini-2.5-flash",
    instruction="Analyze the input and return structured results.",
    output_schema=AnalysisResult,  # Enforces this schema, disables tools
)
```

## Agent Instruction Best Practices

1. **Be specific about when to delegate**: "Route to billing for payment questions" not "choose the best agent".
2. **Define tool calling explicit triggers**: "When you need order status, call `get_order_status`".
3. **Set clear boundaries**: "Do not answer questions yourself. Only route."
4. **Handle ambiguity**: "If the action is unclear, ask for clarification."
5. **Use JSON output for machine-consumable results**: `response_mime_type="application/json"`

## Model Selection

| Role | Recommended Model | Reason |
|------|-------------------|--------|
| Worker (simple tasks) | `gemini-2.5-flash` | Fast, cost-effective |
| Worker (complex reasoning) | `gemini-2.5-pro` | Better reasoning |
| Router/Dispatcher | `gemini-2.5-flash` | Classification is low-complexity |
| Planner/Coordinator | `gemini-2.5-pro` | Planning needs strong reasoning |
| Live/Multimodal | `gemini-2.5-flash-live` | Native audio/video support |
| RAG Worker | `gemini-2.5-flash` | Retrieval + synthesis |
