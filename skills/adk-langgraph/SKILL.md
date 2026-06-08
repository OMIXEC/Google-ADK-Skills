---
name: adk-langgraph
description: >-
  Orchestrate stateful, multi-agent ADK workflows with LangGraph: graphs, state
  machines, conditional edges, and LLM-driven routing, using ADK tools as nodes.
  Use when a request mentions LangGraph, a state-machine/graph workflow, complex
  branching orchestration, or ADK↔LangGraph interop.
---

# adk-langgraph — LangGraph Orchestration for ADK

You build stateful agent graphs with LangGraph that drive ADK tools/agents.

## Doc loading: context7-first, local fallback

LangGraph evolves fast. **Load the freshest docs adaptively:**

1. If the **context7 MCP** is available, call it first:
   `resolve-library-id "langgraph"` → `get-library-docs` for the topic at hand
   (graphs, `StateGraph`, conditional edges, checkpointing).
2. Otherwise (or to confirm the ADK interop pattern), read the bundled reference:
   `references/langgraph-orchestration.md` — the full ADK↔LangGraph integration
   guide (905 lines: state schema, nodes, edges, conditional routing, ADK tool nodes).

context7 is optional runtime enrichment; the bundled reference is always sufficient.

## When to reach for LangGraph (vs native ADK workflows)
- You need an explicit, inspectable **state machine** with cyclic/branching control flow
- Routing decisions depend on accumulated graph state, not just the last message
- You want LangGraph's checkpointing alongside ADK tools as graph nodes

For simple linear/parallel/loop pipelines, prefer native ADK
(`adk-agentic-prod-workflows` / `adk-agents`) — don't add LangGraph weight.

## Process
1. Load docs (context7 → else `references/`)
2. Define the state schema and the node set (ADK tools/agents wrapped as nodes)
3. Wire edges + conditional routing; add a terminal condition
4. Validate models (`adk-litellm`); emit runnable graph code

## NEVER
- Use deprecated/blocked models
- Build a graph with no terminal/exit edge
