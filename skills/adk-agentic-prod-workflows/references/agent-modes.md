# ADK Agent Modes Reference

Complete reference for every ADK agent type: when to use each, full configuration surface, lifecycle, and code examples.

## Decision Tree

```
Need a single model-based agent?
  └─→ LlmAgent

Need multiple agents running concurrently?
  └─→ ParallelAgent

Need agents in a fixed order, output→input?
  └─→ SequentialAgent

Need to iterate until quality gate passes?
  └─→ LoopAgent

Need complex branching/merging with conditions?
  └─→ GraphAgent

Need to extend agent behavior beyond built-in types?
  └─→ CustomAgent (subclass BaseAgent)

Need to call an agent in another process/language?
  └─→ RemoteA2AAgent
```

---

## LlmAgent

The core agent primitive. Wraps an LLM with tools, memory, and instructions.

### Full Configuration Surface

```python
from google.adk.agents import LlmAgent
from google.genai import types
from pydantic import BaseModel, Field

# Input/output schemas
class InputSchema(BaseModel):
    query: str = Field(description="User's question")
    context: str | None = Field(default=None, description="Optional context")

class OutputSchema(BaseModel):
    answer: str = Field(description="Agent's answer")
    confidence: float = Field(description="Confidence score 0.0-1.0")
    sources: list[str] = Field(description="Source references")

agent = LlmAgent(
    # ── Core ──────────────────────────────────
    name="my_agent",                    # Required — unique agent name
    description="What this agent does", # Used for routing and agent cards
    model="gemini-2.5-flash",           # Model string or BaseLlm instance

    # ── Instructions ──────────────────────────
    instruction="""You are a helpful assistant.
        Use tools when you need specific information.
        Always cite sources in your response.""",
    global_instruction="Always be concise and factual.", # Appended to every turn

    # ── Tools ──────────────────────────────────
    tools=[my_tool, MCPToolset(...)],   # FunctionTool, MCPToolset, BaseToolset

    # ── Sub-agents ────────────────────────────
    sub_agents=[specialist_agent],      # Agents this agent can transfer to

    # ── Content generation config ─────────────
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        max_output_tokens=4096,
        stop_sequences=["END"],
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
        ],
    ),

    # ── Input/Output validation ───────────────
    input_schema=InputSchema,           # Validate user input with Pydantic
    output_schema=OutputSchema,         # Enforce structured JSON output
    output_key="agent_result",          # Key to store output in session.state

    # ── Content strategy ──────────────────────
    include_contents="default",         # "default" or "none"
    examples=[                          # Few-shot examples
        types.Example(
            input=types.Content(role="user", parts=[types.Part(text="What is 2+2?")]),
            output=types.Content(role="model", parts=[types.Part(text="4")]),
        ),
    ],

    # ── Callbacks ──────────────────────────────
    before_agent_callback=before_fn,    # Called before agent processing
    after_agent_callback=after_fn,      # Called after agent processing
    before_model_callback=before_model, # Called before each model call
    after_model_callback=after_model,   # Called after each model call
    before_tool_callback=before_tool,   # Called before each tool call
    after_tool_callback=after_tool,     # Called after each tool call

    # ── Code execution ────────────────────────
    code_executor=my_executor,          # Execute code blocks from model

    # ── Planner ───────────────────────────────
    planner=my_planner,                 # Planning strategy for complex tasks

    # ── Transfer control ─────────────────────
    disallow_transfer_to_parent=False,
    disallow_transfer_to_peers=False,
)
```

### When to Use LlmAgent

| Scenario | Recommended |
|----------|-------------|
| Single-step Q&A | `LlmAgent` with tools |
| Multi-step reasoning | `LlmAgent` with planner |
| Structured output needed | `LlmAgent` with `output_schema` |
| Need to call external APIs | `LlmAgent` with MCPToolset |
| Need code execution | `LlmAgent` with `code_executor` |

### Lifecycle

```
before_agent_callback → before_model_callback → [model call] → after_model_callback
    → [if tool calls: before_tool_callback → tool execute → after_tool_callback]
    → [loop back to before_model_callback if more tool calls]
    → after_agent_callback → emit Event
```

---

## ParallelAgent

Fan-out execution: all sub-agents run concurrently. Use when tasks are independent.

### Python

```python
from google.adk.agents import ParallelAgent, LlmAgent

# Heterogeneous sub-agents — each does different work
researcher_1 = LlmAgent(name="web_search", instruction="Search web for X.", output_key="web")
researcher_2 = LlmAgent(name="db_query", instruction="Query DB for X.", output_key="db")
researcher_3 = LlmAgent(name="cache_lookup", instruction="Check cache for X.", output_key="cache")

parallel = ParallelAgent(
    name="multi_source_search",
    description="Search web, DB, and cache concurrently",
    sub_agents=[researcher_1, researcher_2, researcher_3],
)

# Each sub-agent writes to its output_key.
# After all complete, session.state has:
# state["web"], state["db"], state["cache"]
```

### ParallelAgent inside SequentialAgent

```python
from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent

fetch_1 = LlmAgent(name="api1", output_key="api1_data")
fetch_2 = LlmAgent(name="api2", output_key="api2_data")

gather = ParallelAgent(name="gather", sub_agents=[fetch_1, fetch_2])

synthesize = LlmAgent(
    name="synthesize",
    instruction="Combine api1_data and api2_data from state into a report.",
)

pipeline = SequentialAgent(name="fetch_then_synthesize", sub_agents=[gather, synthesize])
```

### Go

```go
import "google.golang.org/adk/agent/workflowagents/parallelagent"

parallelSearch, _ := parallelagent.New(parallelagent.Config{
    AgentConfig: agent.Config{
        Name:      "multi_source_search",
        SubAgents: []agent.Agent{webSearch, dbSearch, cacheSearch},
    },
})
```

### When to Use

- Searching multiple independent sources (APIs, DBs, cache)
- Running multiple validations in parallel
- Multi-modal processing (text + image + audio concurrently)

---

## SequentialAgent

Linear chain: sub-agents execute one after another. Output of Agent N is available to Agent N+1 via `session.state`.

### Python

```python
from google.adk.agents import SequentialAgent, LlmAgent

writer = LlmAgent(
    name="writer",
    instruction="Write a blog post draft about {topic}. Store in 'draft'.",
    output_key="draft",
)

reviewer = LlmAgent(
    name="reviewer",
    instruction="Review the draft from session.state['draft']. Store feedback in 'review'.",
    output_key="review",
)

editor = LlmAgent(
    name="editor",
    instruction="Revise the draft using feedback from session.state['review']. Publish final version.",
    output_key="final",
)

pipeline = SequentialAgent(
    name="content_pipeline",
    description="Writer → Reviewer → Editor pipeline",
    sub_agents=[writer, reviewer, editor],
)
```

### Go

```go
import "google.golang.org/adk/agent/workflowagents/sequentialagent"

pipeline, _ := sequentialagent.New(sequentialagent.Config{
    AgentConfig: agent.Config{
        Name:      "content_pipeline",
        SubAgents: []agent.Agent{writerAgent, reviewerAgent, editorAgent},
    },
})
```

### When to Use

- Content creation pipelines (write → review → publish)
- Data processing pipelines (extract → transform → load)
- Multi-step validation (syntax → logic → security → deploy)

---

## LoopAgent

Iterate a set of sub-agents until a quality gate passes or max iterations reached.

### Python

```python
from google.adk.agents import LoopAgent, LlmAgent
from google.adk.tools.tool_context import ToolContext

# Quality gate tool — signals loop exit
def exit_loop(tool_context: ToolContext):
    """Call when output meets quality bar. Exits the loop."""
    tool_context.actions.escalate = True
    return {}

generator = LlmAgent(
    name="generator",
    instruction="Generate content based on requirements in state['requirements'].",
    tools=[exit_loop],
    output_key="content",
)

critic = LlmAgent(
    name="critic",
    instruction="""Review state['content'].
        If quality meets requirements, call exit_loop().
        Otherwise, provide specific improvement feedback in state['feedback'].""",
    tools=[exit_loop],
    output_key="feedback",
)

loop = LoopAgent(
    name="iterative_refinement",
    description="Generate → Critique → Improve → Repeat until quality gate passes",
    sub_agents=[generator, critic],
    max_iterations=5,
)
```

### Go

```go
import "google.golang.org/adk/agent/workflowagents/loopagent"

loop, _ := loopagent.New(loopagent.Config{
    AgentConfig: agent.Config{
        Name:      "iterative_refinement",
        SubAgents: []agent.Agent{generator, critic},
    },
    MaxIterations: 5, // 0 = indefinite
})
```

### When to Use

- Content refinement: generate → critique → improve → loop
- Code generation with tests: generate code → run tests → fix → loop
- RAG with quality gates: retrieve → evaluate completeness → refine query → loop
- Self-improving agents: produce output → evaluate → refine → loop

### Quality Gate Patterns

```python
# Pattern 1: Tool-based gate (exit_loop function)
def quality_ok(tool_context: ToolContext):
    tool_context.actions.escalate = True
    return {}

# Pattern 2: State-based gate (in after_agent_callback)
async def check_quality(callback_context):
    if callback_context.state.get("quality_score", 0) >= 0.9:
        callback_context.actions.escalate = True
```

---

## GraphAgent

DAG-based workflow: nodes are agents or deterministic steps, edges define routing with conditions.

### Python

```python
from google.adk.agents import GraphAgent, Node, Edge, Condition, LlmAgent

classifier = LlmAgent(name="classifier", instruction="Classify input as 'code' or 'text'.")
code_handler = LlmAgent(name="code_handler", instruction="Handle code requests.")
text_handler = LlmAgent(name="text_handler", instruction="Handle text requests.")

def route_by_type(state) -> str:
    """Condition function: return target node name."""
    return "code_handler" if state.get("type") == "code" else "text_handler"

graph = GraphAgent(
    name="router_workflow",
    description="Classify input then route to specialized handler",
    nodes=[
        Node(name="classifier", agent=classifier),
        Node(name="code_handler", agent=code_handler),
        Node(name="text_handler", agent=text_handler),
    ],
    edges=[
        Edge(source="classifier", target=Condition(fn=route_by_type)),
    ],
)
```

### When to Use

- Complex routing with branch logic
- Fan-out/fan-in patterns (one input → multiple processors → aggregate)
- Multi-path workflows where the next step depends on results
- Pipelines that need conditional skip/retry paths

---

## CustomAgent

Subclass `BaseAgent` when built-in agent types don't fit your orchestration pattern.

### Python

```python
from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, SequentialAgent

class MyCustomAgent(BaseAgent):
    """Orchestrates a custom workflow combining multiple agent types."""

    # Pydantic fields for sub-agents
    preprocessor: LlmAgent
    refinement_loop: LoopAgent
    postprocessor: SequentialAgent

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        name: str,
        preprocessor: LlmAgent,
        generator: LlmAgent,
        critic: LlmAgent,
        formatter: LlmAgent,
        validator: LlmAgent,
    ):
        refinement_loop = LoopAgent(
            name="refine",
            sub_agents=[generator, critic],
            max_iterations=3,
        )
        postprocessor = SequentialAgent(
            name="postprocess",
            sub_agents=[formatter, validator],
        )

        super().__init__(
            name=name,
            preprocessor=preprocessor,
            refinement_loop=refinement_loop,
            postprocessor=postprocessor,
            sub_agents=[preprocessor, refinement_loop, postprocessor],
        )
```

### When to Use CustomAgent

| Scenario | Use CustomAgent? |
|----------|-----------------|
| Unique orchestration pattern not in built-in types | Yes |
| Combining Parallel + Sequential + Loop in custom order | Yes |
| Need custom state management between agents | Yes |
| Simple sequential pipeline | No — use SequentialAgent |
| Simple parallel fan-out | No — use ParallelAgent |
| Just adding a few tools to an LLM | No — use LlmAgent |

---

## Agent Type Selection Guide

| You want to... | Use |
|----------------|-----|
| Answer questions, call tools, generate content | `LlmAgent` |
| Run multiple independent tasks concurrently | `ParallelAgent` |
| Run tasks in a fixed order (pipeline) | `SequentialAgent` |
| Iterate until quality is good enough | `LoopAgent` |
| Route to different handlers based on input | `GraphAgent` |
| Compose multiple agent types in custom way | `CustomAgent` |
| Call an agent in another service/language | `RemoteA2AAgent` |
| Search + generate with grounding | `LlmAgent` with `include_grounding=True` |
| Execute generated code safely | `LlmAgent` with `code_executor` |
| Enforce structured output | `LlmAgent` with `output_schema` |

## Composition Patterns

```python
# Pattern: Parallel → Aggregate (most common production pattern)
fetch_a = LlmAgent(name="fetch_a", output_key="a_data")
fetch_b = LlmAgent(name="fetch_b", output_key="b_data")
fetch_all = ParallelAgent(name="fetch_all", sub_agents=[fetch_a, fetch_b])
aggregate = LlmAgent(
    name="aggregate",
    instruction="Combine a_data and b_data from state.",
)
workflow = SequentialAgent(name="fetch_aggregate", sub_agents=[fetch_all, aggregate])

# Pattern: Loop with quality gate
gen = LlmAgent(name="gen", tools=[exit_loop], output_key="output")
critic = LlmAgent(name="critic", tools=[exit_loop])
refine = LoopAgent(name="refine", sub_agents=[gen, critic], max_iterations=5)

# Pattern: Graph with conditional routing
classifier = LlmAgent(name="classify")
handler_a = LlmAgent(name="handler_a")
handler_b = LlmAgent(name="handler_b")
router = GraphAgent(
    name="router",
    nodes=[Node(name="classify", agent=classifier),
           Node(name="handler_a", agent=handler_a),
           Node(name="handler_b", agent=handler_b)],
    edges=[Edge(source="classify", target=Condition(fn=route_fn))],
)
```
