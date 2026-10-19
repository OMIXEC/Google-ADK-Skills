---
name: adk-agent-orchestration
description: >-
  Controls how an ADK agent runs over time: autonomous OODA loops with explicit planning
  and stop conditions, and LangGraph state machines for cyclic or branching control flow
  with ADK tools as nodes. Use when the agent must pursue a goal without per-step input,
  plan its own steps, drive an inspectable state machine, or checkpoint long-running
  control flow. Don't use for the static shape of a native ADK workflow (use
  adk-graph-workflows), for the contents of one agent (use adk-agent-architecture), or
  for choosing a persona (use adk-agent-personas).
compatibility: google-adk>=2.9.2,<3
---

# Agent Orchestration

Two runtimes for the same question: who decides what happens next?

| Control flow | Use |
|---|---|
| Data-dependent, cyclic, inspectable state | LangGraph |
| Goal-directed with no fixed graph | OODA loop |
| Fixed DAG, fan-out/fan-in, or template pipeline | Native ADK — use `adk-graph-workflows` |

Do not add LangGraph weight to a straight line. Do not build an OODA loop when
a fixed workflow would terminate reliably.

## Doc loading: context7 first

LangGraph and ADK interop evolve fast. Load the freshest docs adaptively:

1. If the **context7 MCP** is available, call it first:
   `resolve-library-id "langgraph"` → `get-library-docs` for the topic at hand
   (graphs, `StateGraph`, conditional edges, checkpointing).
2. Otherwise, read `references/langgraph-orchestration.md` — the bundled
   ADK↔LangGraph integration guide (state schema, nodes, edges, conditional
   routing, ADK tool nodes).

context7 is optional enrichment; the bundled reference is always sufficient.

## LangGraph path

1. Define the state schema first. Every node reads and writes this state.
2. Wrap ADK tools or agents as nodes; keep side effects inside them.
3. Wire edges and conditional routing, then add an explicit terminal condition.
4. Add checkpointing only if a resume after failure is a real requirement.
5. Validate model IDs with `adk-model-routing`; emit runnable graph code.

## OODA path

1. Read `references/autonomous-agents.md` for the loop and planning scaffold.
2. Define the goal, success criteria, and **stop conditions**: max iterations,
   budget, and a quality gate that can actually fail.
3. Implement Observe → Orient → Decide → Act with reasoning traces that a
   human can audit.
4. Put irreversible external actions behind an approval or guard step.

## Non-negotiables

- An autonomous loop without a stop condition is a bug.
- An OODA agent must not take irreversible actions unattended.
- A LangGraph node must not hide a second control loop inside it.
- Retired or blocked model IDs are never valid, in either runtime.

## References

| File | Load when |
|---|---|
| `references/autonomous-agents.md` | Building or reviewing an OODA loop |
| `references/langgraph-orchestration.md` | Building an ADK↔LangGraph graph |

## Boundaries

- Native graph and template workflows belong to `adk-graph-workflows`.
- Agent contents — tools, memory, MCP, A2A — belong to
  `adk-agent-architecture`.
