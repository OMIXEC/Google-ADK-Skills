---
wave: 3
depends_on: [02-PLAN.md, 03-PLAN.md]
files_modified:
  - skills/adk-orchestration-patterns/SKILL.md
  - skills/adk-multi-agent-orchestrator.md
  - skills/adk-langgraph-orchestrator.md
autonomous: false
requirements: [adk-orchestration, multi-agent]
---

# Plan 05: Enhance Orchestration and Multi-Agent Skills

## Objective
Enhance existing orchestration skills with comprehensive patterns from ADK documentation: Sequential, Parallel, Loop agents, hierarchical routing, and workflow patterns.

## must_haves
- [ ] All ADK orchestration agent types documented
- [ ] Hierarchical multi-agent routing patterns
- [ ] State management in orchestrated systems
- [ ] LangGraph integration patterns enhanced

## Tasks

<task id="5.1" type="create">
<title>Create Orchestration Patterns Skill</title>
<description>
Comprehensive orchestration patterns from ADK:

**Agent Types:**
1. **SequentialAgent** - Execute agents in order
2. **ParallelAgent** - Execute agents concurrently
3. **LoopAgent** - Iterative execution with conditions
4. **LlmAgent** - LLM-powered routing decisions

**Routing Patterns:**
1. **Static Routing** - Predetermined agent sequence
2. **Dynamic Routing** - LLM-based delegation
3. **Conditional Routing** - Rule-based branching
4. **Hierarchical Routing** - Tree of supervisors

**Code Examples:**
```python
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent, LlmAgent

# Sequential: A -> B -> C
sequential = SequentialAgent(
    name="pipeline",
    sub_agents=[agent_a, agent_b, agent_c],
)

# Parallel: A, B, C concurrently
parallel = ParallelAgent(
    name="parallel_tasks",
    sub_agents=[agent_a, agent_b, agent_c],
)

# Loop: Repeat until condition
loop = LoopAgent(
    name="iterative",
    sub_agents=[processor_agent],
    max_iterations=5,
)

# Dynamic routing with LLM
coordinator = LlmAgent(
    name="coordinator",
    model="gemini-2.5-flash",
    description="Routes requests to specialists",
    sub_agents=[billing_agent, support_agent, sales_agent],
    instruction="Route to appropriate specialist based on user intent.",
)
```
</description>
<files>
- skills/adk-orchestration-patterns/SKILL.md
- skills/adk-orchestration-patterns/references/agent-types.md
- skills/adk-orchestration-patterns/references/routing-patterns.md
- skills/adk-orchestration-patterns/examples/sequential-pipeline.md
- skills/adk-orchestration-patterns/examples/parallel-workers.md
- skills/adk-orchestration-patterns/examples/hierarchical-routing.md
</files>
</task>

<task id="5.2" type="enhance">
<title>Enhance Multi-Agent Orchestrator Skill</title>
<description>
Upgrade existing skill with additional patterns:

**New Patterns:**
1. **Debate Pattern** - Multiple agents argue perspectives
2. **Consensus Pattern** - Agents vote on outcomes
3. **Specialist Team** - Domain experts collaborate
4. **Review Chain** - Sequential review process

**State Sharing:**
- Shared memory across agents
- Event-driven communication
- Artifact passing

**Code Example:**
```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Debate pattern
optimist = LlmAgent(name="optimist", instruction="Argue positive aspects")
pessimist = LlmAgent(name="pessimist", instruction="Argue negative aspects")
moderator = LlmAgent(
    name="moderator",
    instruction="Present both perspectives, synthesize conclusions",
    tools=[AgentTool(agent=optimist), AgentTool(agent=pessimist)],
)
```
</description>
<files>
- skills/adk-multi-agent-orchestrator.md
- skills/adk-multi-agent-orchestrator/references/team-patterns.md
</files>
</task>

<task id="5.3" type="enhance">
<title>Enhance LangGraph Orchestrator Skill</title>
<description>
Upgrade existing skill with advanced LangGraph patterns:

**New Patterns:**
1. **Conditional Branching** - Complex decision trees
2. **Human-in-the-Loop** - Approval workflows
3. **Checkpointing** - State persistence and recovery
4. **Streaming Integration** - Real-time LangGraph

**Code Example:**
```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    approval_needed: bool
    approved: bool

def check_approval(state: AgentState) -> str:
    if state["approval_needed"] and not state["approved"]:
        return "wait_for_approval"
    return "continue"

builder = StateGraph(AgentState)
builder.add_node("process", process_node)
builder.add_node("wait_for_approval", approval_node)
builder.add_conditional_edges("process", check_approval)

# Add checkpointing
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
```
</description>
<files>
- skills/adk-langgraph-orchestrator.md
- skills/adk-langgraph-orchestrator/references/advanced-patterns.md
</files>
</task>

## Verification Criteria
- [ ] All ADK orchestration types documented
- [ ] Multi-agent patterns cover common use cases
- [ ] LangGraph integration is production-ready
- [ ] State management patterns are clear

## Acceptance
Orchestration skills provide comprehensive multi-agent guidance.
