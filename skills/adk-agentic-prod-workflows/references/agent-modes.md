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

## Reasoning Architecture Taxonomy

Agent reasoning architecture determines HOW an agent thinks, not just WHAT ADK class it uses. Choose the reasoning pattern first, then map to the ADK agent type that supports it.

### Router

Simple classification → delegation. No iterative reasoning.

```
User Input → [Classify Intent] → Route to Handler → Response
```

```python
# Router: classify and delegate in one shot
router = LlmAgent(
    name="router",
    model="gemini-2.5-flash",
    instruction="""Classify the user's request into one category:
    - 'billing': Payment, invoices, refunds → transfer to billing_agent
    - 'support': Technical issues, bugs → transfer to support_agent
    - 'sales': Product questions, pricing → transfer to sales_agent
    Respond ONLY with the category name.""",
    sub_agents=[billing_agent, support_agent, sales_agent],
)
```

| Characteristic | Router |
|---------------|--------|
| Reasoning depth | Shallow (1 step) |
| Tool calls | None or 1 (classification) |
| Latency | Lowest |
| Cost | Lowest (flash-lite sufficient) |
| Best for | Customer service triage, simple FAQ bots |
| ADK mapping | `LlmAgent` with sub_agents for transfer |

### ReAct (Thought → Action → Observation)

Iterative reasoning with tool calls. The dominant production pattern.

```
User Input → Thought → Action (tool call) → Observation → Thought → Action → ... → Final Answer
```

```python
# ReAct: think, act, observe, repeat
react_agent = LlmAgent(
    name="react_researcher",
    model="gemini-2.5-flash",
    instruction="""You are a research agent using the ReAct pattern.

    Follow this cycle:
    1. THOUGHT: Analyze what you know and what you need
    2. ACTION: Call a tool to gather information
    3. OBSERVATION: Analyze the tool result
    4. Repeat 1-3 until you have sufficient information
    5. FINAL ANSWER: Synthesize findings with citations

    Always show your reasoning before taking action.""",
    tools=[web_search, db_query, calculate],
)
```

| Characteristic | ReAct |
|---------------|-------|
| Reasoning depth | Deep (3-10 iterations typical) |
| Tool calls | Multiple, interleaved with reasoning |
| Latency | Medium (multiple LLM calls) |
| Cost | Medium |
| Best for | Research, complex analysis, multi-step problem solving |
| ADK mapping | `LlmAgent` with tools (ReAct is default LLM behavior) |

### Plan-and-Execute

Create a plan first, then execute each step. Plan acts as a contract.

```
User Input → [Create Plan] → Step 1 → Step 2 → Step 3 → [Validate Plan] → Final Answer
```

```python
# Plan-and-Execute: plan first, then follow through
planner = LlmAgent(
    name="planner",
    model="gemini-2.5-pro",  # Stronger model for planning
    instruction="""Create a step-by-step plan to answer the user's question.
    Output as a numbered list. Each step must be actionable and verifiable.""",
    output_key="plan",
)

executor = LlmAgent(
    name="executor",
    model="gemini-2.5-flash",
    instruction="""Execute the plan in session.state['plan'].
    Complete each step before moving to the next.
    Mark steps as [DONE] when complete.
    If a step fails, note it and continue to the next.""",
    tools=[web_search, db_query, calculate, validate_step],
)

validate = LlmAgent(
    name="validator",
    model="gemini-2.5-flash",
    instruction="""Verify the execution plan was completed:
    1. Are all steps marked [DONE]?
    2. Do findings support the conclusion?
    3. Are there gaps or inconsistencies?
    If issues found, flag them. Otherwise, output final answer.""",
)

plan_execute_workflow = SequentialAgent(
    name="plan_execute",
    sub_agents=[planner, executor, validate],
)
```

| Characteristic | Plan-and-Execute |
|---------------|-----------------|
| Reasoning depth | Deep (explicit plan structure) |
| Tool calls | Many, structured by plan |
| Latency | Highest (planning + execution + validation) |
| Cost | Highest (pro for planning, flash for execution) |
| Best for | Complex multi-step tasks, regulated domains requiring auditable plans |
| ADK mapping | `SequentialAgent` with planner → executor → validator |

### Architecture Decision Matrix

| Factor | Router | ReAct | Plan-and-Execute |
|--------|--------|-------|-----------------|
| Task complexity | Low | Medium-High | High |
| Latency tolerance | <1s | 2-10s | 10-30s |
| Cost sensitivity | Very high | Medium | Low |
| Auditability | Low | Medium | High (plan is auditable) |
| Error recovery | None (reclassify) | Iterative self-correction | Step-level retry |
| Model rec | flash-lite | flash | pro (planner) + flash (executor) |
| ADK class | `LlmAgent` | `LlmAgent` + tools | `SequentialAgent` |

### Choosing: Decision Flow

```
Can it be answered in one shot?
  └─ YES → Router (LlmAgent, flash-lite)
  └─ NO  → Does it need step-by-step execution tracking?
            └─ YES → Plan-and-Execute (SequentialAgent)
            └─ NO  → ReAct (LlmAgent + tools)
```

### Hybrid: ReAct + Plan-and-Execute

```python
# Hybrid: Plan first, then ReAct within each step
hybrid = SequentialAgent(
    name="hybrid_reasoner",
    sub_agents=[
        planner,       # Plan-and-Execute phase 1: create plan
        react_executor,  # ReAct within each step (ReAct agent with tools)
        validator,     # Plan-and-Execute phase 3: validate completion
    ],
)
```

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
