# ADK Workflow Types & Patterns

## Overview

ADK supports composing agents into workflows — deterministic or dynamic structures that control execution order, branching, and data flow between agents and nodes. Choose the workflow type based on complexity, flexibility needs, and runtime determinism requirements.

## Workflow Type Selection

```
Need fixed order? → Template (Sequential/Parallel/Loop)
Need branching + merging? → Graph-based
Need runtime flexibility? → Dynamic
Need shared state + delegation? → Collaborative
```

## 1. Template Workflows

Fixed execution patterns with no LLM-based routing. Deterministic and predictable.

### SequentialAgent

```python
from google.adk.agents import SequentialAgent

workflow = SequentialAgent(
    name="code_pipeline",
    sub_agents=[writer_agent, reviewer_agent, deployer_agent]
)
# Executes writer → reviewer → deployer in strict order
```

Use for: CI/CD pipelines, data processing chains, document generation pipelines.

### ParallelAgent

```python
from google.adk.agents import ParallelAgent

workflow = ParallelAgent(
    name="multi_search",
    sub_agents=[web_search, doc_search, code_search]
)
# All agents run concurrently, results aggregated
```

Use for: multi-source search, independent validation checks, fan-out processing.

### LoopAgent

```python
from google.adk.agents import LoopAgent

workflow = LoopAgent(
    name="refinement_loop",
    sub_agents=[writer_agent, reviewer_agent],
    max_iterations=5,
    stop_condition=lambda ctx: ctx.get("quality_score", 0) >= 0.9
)
# Writer → Reviewer repeats until quality gate passes
```

Use for: iterative refinement, code review cycles, quality-gated pipelines.

## 2. Graph-Based Workflows

Directed acyclic graphs (DAGs) where nodes are agents or deterministic functions, edges represent data/control flow.

```python
from google.adk.agents import GraphAgent
from google.adk.agents.graph import Node, Edge

workflow = GraphAgent(name="order_processing")

# Define nodes
validate = Node(name="validate", agent=validator_agent)
enrich = Node(name="enrich", agent=enrichment_agent)
approve = Node(name="approve", agent=approval_agent)
notify = Node(name="notify", agent=notification_agent)

workflow.add_node(validate)
workflow.add_node(enrich)
workflow.add_node(approve)
workflow.add_node(notify)

# Define edges
workflow.add_edge(Edge(source=validate, target=enrich))
workflow.add_edge(Edge(source=enrich, target=approve,
                       condition=lambda ctx: ctx["amount"] > 1000))
workflow.add_edge(Edge(source=approve, target=notify))
```

Use for: order processing, multi-stage ETL, complex business logic with branching.

Key considerations:
- Each node is independently testable
- Edges carry typed data contracts
- Conditions are pure functions (no side effects)
- Timeouts configurable per node

## 3. Dynamic Workflows

Agents and edges created programmatically at runtime. Highest flexibility.

```python
from google.adk import Agent, Runner

class DynamicWorkflowBuilder:
    def __init__(self, runner: Runner):
        self.runner = runner
        self.nodes: list[Agent] = []

    def add_agent(self, agent: Agent):
        self.nodes.append(agent)

    def route(self, result, candidates: list[Agent]) -> Agent:
        # Programmatic routing logic
        scores = {a.name: self._score(result, a) for a in candidates}
        return max(candidates, key=lambda a: scores[a.name])

    def _score(self, result, agent) -> float:
        # Custom scoring for routing decisions
        ...
```

Use for: adaptive pipelines where next steps depend on intermediate results, exploration systems, self-organizing agent swarms.

## 4. Collaborative Workflows

Single coordinator agent manages sub-agents with shared memory/session.

```python
coordinator = Agent(
    name="coordinator",
    model="gemini-2.5-pro",
    sub_agents=[researcher, analyst, writer],
    instruction="""You are a research coordinator.
    Delegate tasks to specialists based on:
    - Information gathering → researcher
    - Data analysis → analyst
    - Report writing → writer
    Share findings via session.state['shared_context']."""
)
```

Use for: research projects, complex analysis, multi-perspective problem solving.

Key considerations:
- Shared state structure defined upfront
- Coordinator handles conflict resolution
- Sub-agents use working memory for context
- Session state persists across delegations

## Workflow Architecture Decision Matrix

| Factor | Template | Graph | Dynamic | Collaborative |
|--------|----------|-------|---------|---------------|
| Determinism | High | Medium-High | Low | Low-Medium |
| Flexibility | Low | Medium | High | High |
| Testability | High | High | Medium | Medium |
| Scalability | High | High | Medium | Medium |
| Debug complexity | Low | Medium | High | Medium |
| LLM calls per step | Variable | Variable | Variable | High (coordinator) |

## Production Hardening Checklist

- [ ] All nodes have timeout configuration
- [ ] Edges define typed data contracts
- [ ] Error nodes/sinks defined for failure paths
- [ ] Correlation ID propagated across all nodes
- [ ] Each node emits structured logs with span context
- [ ] Circuit breaker on external tool calls
- [ ] Graceful degradation when optional nodes fail

## Agent Mode Selection

Choose which ADK agent type to use at each workflow node. See `references/agent-modes.md` for full API reference.

| Agent Type | When to Use | Nesting |
|-----------|-------------|---------|
| `LlmAgent` | Single model + tools + instruction. Core primitive. | — |
| `ParallelAgent` | Fan-out to heterogeneous sub-agents, aggregate results | Contains 2+ `LlmAgent` |
| `SequentialAgent` | Fixed-order pipeline, output→input passing | Contains 2+ `LlmAgent` |
| `LoopAgent` | Iterative refinement with quality gate, max_iterations | Contains 1+ `LlmAgent` |
| `GraphAgent` | DAG with conditions, branching, merging | Contains `LlmAgent` per node |
| `CustomAgent` | Subclass `BaseAgent` for custom orchestration logic | Programmatic |

Quick decision tree:
```
Need fixed pipeline? → SequentialAgent
Need parallel fan-out? → ParallelAgent
Need iterative refinement? → LoopAgent
Need branching + merging? → GraphAgent
Need programmatic control? → CustomAgent (subclass BaseAgent)
Need single model + tools? → LlmAgent
```

## CustomAgent Decision Tree

When standard agent types don't fit, subclass `BaseAgent`:

```python
from google.adk.agents import BaseAgent

class MyCustomAgent(BaseAgent):
    """Custom orchestration when built-in types don't fit."""
    async def _run_async_impl(self, ctx):
        # Custom logic: conditional execution, dynamic tool selection,
        # external state machines, or multi-model chaining.
        ...
```

**Use `CustomAgent` when:**
- Execution order depends on external state
- Need to interleave model calls with deterministic steps
- Building custom retry/fallback logic
- Implementing state-machine driven workflows

**Don't use `CustomAgent` when:**
- Standard `SequentialAgent`/`ParallelAgent`/`GraphAgent` fits
- You just need a single model call → use `LlmAgent`

## Heterogeneous ParallelAgent

Standard `ParallelAgent` fans out identical tasks. For heterogeneous parallel agents (different roles, different tools):

```python
from google.adk.agents import ParallelAgent

# Each sub-agent has different tools and instructions
rag_agent = LlmAgent(name="rag", tools=[retrieval_tool])
classifier = LlmAgent(name="classifier", tools=[classify_tool])
code_executor = LlmAgent(name="code_exec", tools=[code_exec_tool])

parallel = ParallelAgent(
    name="heterogeneous_fan_out",
    sub_agents=[rag_agent, classifier, code_executor],
)
# All three run concurrently with their own tools and instructions.
# Results available via sub-agent output keys.
```

## Scheduled & Cron Triggers

For workflows that run on a schedule (not request-driven):

```python
# Cloud Scheduler → Pub/Sub → Cloud Run workflow trigger
# Workflow entrypoint receives Pub/Sub push event

import functions_framework

@functions_framework.http
def workflow_trigger(request):
    """Triggered by Cloud Scheduler via Pub/Sub push."""
    import asyncio
    runner = InProcessRunner(agent=workflow_agent)
    result = asyncio.run(runner.run(query="Execute scheduled workflow"))
    return {"status": "ok", "result": result}
```

**Schedule options:**
- Cloud Scheduler + Pub/Sub → Cloud Run (GCP)
- EventBridge Scheduler → Lambda (AWS)
- Logic Apps schedule → Container Apps (Azure)
- Kubernetes CronJob → GKE/EKS/AKS

## Human-in-the-Loop Patterns

Insert human review/approval steps into automated workflows:

```python
approval_request = Agent(
    name="approval_requester",
    model="gemini-2.5-flash",
    instruction="""Generate an approval request for the human reviewer.
    Output format: {"action": "request_approval", "summary": "...", "details": {...}}""",
)

human_approval_node = Node(
    id="human_approval",
    # This node returns control to the caller with a pending status.
    # The caller handles presenting the approval UI and resubmitting.
    agent=approval_request,
)

# In GraphAgent, route to human node when approval needed:
Edge(
    source="processor",
    target="human_approval",
    condition=Condition(lambda state: state.get("requires_approval", False)),
)
```

**HITL patterns:**
1. **Review-gate**: Agent output → human reviews → approve/reject → continue/stop
2. **Edit-approve**: Agent drafts → human edits → agent finalizes
3. **Escalation**: Agent confidence < threshold → route to human
4. **Override**: Human can override any automated decision

Use `after_agent_callback` to implement HITL checks without blocking the workflow.
