---
name: adk-agent-architecture
description: >-
  Designs the internals of an ADK 2.x agent or cooperating set: agent modes,
  tool boundaries, MCP and A2A integration, session state and memory, structured
  output, and model routing. Use when deciding what one agent is made of, which
  tools it may call, how it talks to another agent, what it remembers between
  turns, or which model it should use. Don't use for how nodes and edges connect
  (use adk-graph-workflows), for CI/CD, containers, or cloud deployment (use
  adk-deploy-production), for LangGraph state machines or autonomous goal loops
  (use adk-langgraph or adk-autonomous-agent), or for non-Google provider
  wiring (use adk-litellm).
compatibility: google-adk>=2.9.2,<3
---

# ADK Agent Architecture

Design one agent's contract: what it knows, what it may do, what it returns,
and what survives the next turn. For the shape of a multi-agent flow, use
`adk-graph-workflows`.

Read `references/adk-2x-baseline.md` first. It carries the version floor,
Python matrix, core imports, and the migration cautions.

## The five decisions

| Decision | Choose from | Reference |
|---|---|---|
| **Agent mode** | `Agent` / `LlmAgent`, workflow node, `SequentialAgent`, `ParallelAgent`, `LoopAgent`, custom `BaseAgent`, remote A2A | `references/agent-modes.md` |
| **Tools** | Function tools, built-in tools, OpenAPI, MCP toolsets, agent-as-tool | `references/tool-design.md` |
| **Protocol** | In-process delegation, MCP for external tools, A2A for cross-process agents | `references/mcp-integration.md`, `references/a2a-deep-dive.md` |
| **State** | `session.state`, SessionService backend, persistent memory | `references/memory-management.md` |
| **Model** | Complexity tier, task type, live audio, embeddings | `references/model-routing.md` |

## Rules that decide the design

- **Tools do side effects.** Network, disk, database, and mutation calls go in
  tools, never in the instruction.
- **`output_schema` excludes tools.** Split a schema-producing leaf from a
  tool-using leaf; do not try to have both.
- **Tool boundaries are trust boundaries.** Mark read-only versus mutating,
  give every external call a timeout, a bounded retry, and a typed error return.
- **MCP is for external surfaces.** Use `McpToolset` with an explicit
  `tool_filter`; prefer a function tool for pure in-process logic.
- **A2A is a production boundary.** AgentCard, auth propagation, timeouts,
  retries, and sanitized telemetry are part of the design, not an afterthought.
- **Memory has layers.** Session state for the turn, SessionService for the
  session, an external store for cross-session facts. Do not treat one as the
  other.
- **Models are pinned.** Route by complexity (`gemini-3.1-flash-lite`,
  `gemini-3.5-flash`, `gemini-3.1-pro-preview`) and never ship a `latest` alias
  or a retired model ID.

## Agent templates

`references/agent-templates.md` maps a role to a starting shape:
planner, worker, router, retrieval worker, reviewer, live interface,
deployer. Pick the role first, then the mode, then the tools.

## Model catalog

`references/model-cache.json` is the checked-in catalog. Refresh it with:

```bash
python scripts/fetch_models.py --check-only   # CI gate: fail on stale IDs
python scripts/fetch_models.py --output references/model-cache.json
```

## References

| File | Load when |
|---|---|
| `references/agent-modes.md` | Choosing or subclassing an agent type |
| `references/agent-templates.md` | Mapping a role to an agent shape |
| `references/tool-design.md` | Defining tool signatures and side effects |
| `references/mcp-integration.md` | Building or consuming an MCP server |
| `references/a2a-deep-dive.md` | Crossing a process or language boundary |
| `references/memory-management.md` | Session, state, and persistent memory |
| `references/model-routing.md` | Selecting a model or rejecting a retired one |
| `references/model-cache.json` | Current catalog data |
| `references/adk-2x-baseline.md` | Version, imports, migration |

## Boundaries

- Edges, fan-out, and workflow shape belong to `adk-graph-workflows`.
- Packaging and deployment belong to `adk-deploy-production`.
- Provider abstraction for non-Google models belongs to `adk-litellm`.
