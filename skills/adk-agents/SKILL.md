---
name: adk-agents
description: >-
  Composes multiple ADK agents into a team: supervisor, router, sequential and parallel
  delegation, sub-agent handoff, and custom BaseAgent subclasses that control the run
  loop. Use when deciding which agent owns which job, how they delegate to each other,
  or when a prebuilt agent type cannot express the control flow. Don't use for edges
  between deterministic steps or fan-out topology (use adk-graph-workflows), for one
  agent's tools or memory (use adk-agent-architecture), for calls across processes (use
  adk-a2a), or for building a single agent from scratch (use adk-agent-builder).
compatibility: google-adk>=2.9.2,<3
---

# ADK Multi-Agent Systems

Compose agents into a team. Read `references/adk-2x-baseline.md` for the version
floor and imports.

## Pick the composition

| Pattern | Use when | Shape |
|---|---|---|
| Sequential | Fixed pipeline | `SequentialAgent(sub_agents=[...])` |
| Parallel | Independent work, one join | `ParallelAgent(sub_agents=[...])` |
| Routing | One specialist owns the request | Parent `Agent` with `sub_agents` and routing instructions |
| Supervisor | One agent reviews or escalates another's work | Parent with a reviewer sub-agent |
| Hierarchical | Manager, team, workers | Nested `sub_agents` |
| Dynamic or branching | Conditional edges, retry, loop, human input | `Workflow` — see `adk-graph-workflows` |

Routing and supervision are both "parent owns the transfer decision". The
difference is intent, not API: a router hands off and stops; a supervisor keeps
control and judges the result.

## Delegation

```python
from google.adk import Agent

writer = Agent(
    name="writer",
    model="gemini-3.8-flash",
    instruction="Write code that satisfies the stated requirements.",
)

reviewer = Agent(
    name="reviewer",
    model="gemini-3.8-flash",
    instruction="Review code for bugs and policy violations. Return findings only.",
)

orchestrator = Agent(
    name="orchestrator",
    model="gemini-3.8-flash",
    sub_agents=[writer, reviewer],
    instruction="""Coordinate code development:
    1. Delegate writing to 'writer'.
    2. Send the result to 'reviewer'.
    3. Iterate until the reviewer returns no blocking findings.""",
)
```

| Rule | Why |
|---|---|
| Name each sub-agent after its job | The model routes on names and descriptions |
| Give every sub-agent a bounded output contract | Open-ended sub-agents dominate the token budget |
| Set `disallow_transfer_to_parent` / `_peers` when a leaf must not bounce back | Prevents ping-pong |
| Use `mode='task'` for bounded delegation | The agent returns a `TaskResult` and hands control back |
| Prefer one supervisor over a mesh | Peer-to-peer transfer loops are hard to bound |

Task mode is covered in `adk-agent-builder` → `references/task-mode.md`.

## Routing

```python
router = Agent(
    name="router",
    model="gemini-3.8-flash",
    sub_agents=[billing_agent, technical_agent, general_agent],
    instruction="""Route the request to exactly one specialist:
    - Billing, invoices, refunds -> billing_agent
    - Errors, outages, configuration -> technical_agent
    - Anything else -> general_agent""",
)
```

Two rules that keep routing honest:

- The instruction must define the fallback. A router with no default has no
  defined behaviour for an unmatched request.
- Sub-agent descriptions must not overlap. Overlapping descriptions produce
  nondeterministic routing that reads as a model bug.

## Custom agents

When no built-in type expresses the control flow, subclass `BaseAgent`:

```python
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event
from google.genai import types


class EchoAgent(BaseAgent):
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        text = ""
        if ctx.user_content and ctx.user_content.parts:
            text = "".join(p.text for p in ctx.user_content.parts if p.text)
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            branch=ctx.branch,
            content=types.Content(
                role="model", parts=[types.Part(text=f"Echo: {text}")]
            ),
        )
```

A custom agent is responsible for yielding events, not for returning text. If
it needs to pause for a human, it yields an interrupt rather than blocking.

## Shared state

```python
# A sub-agent writes; downstream agents read
session.state["shared_context"] = {
    "user_requirements": requirements,
    "current_code": code,
    "review_feedback": [],
}
```

State is per session, not per agent. Namespace keys by owner
(`review.feedback`, not `feedback`) so parallel branches do not overwrite each
other. See `adk-agent-architecture` for memory layers.

## References

| File | Load when |
|---|---|
| `references/index.md` | Agents overview |
| `references/multi-agents.md` | Full multi-agent pattern guide |
| `references/llm-agents.md` | LLM agent configuration |
| `references/custom-agents.md` | Building a `BaseAgent` subclass |
| `references/config.md` | Agent configuration options |
| `references/models.md` | Model configuration |
| `references/manager/` | Manager-agent patterns |
| `references/README.md` | Crash-course tutorial |
| `references/adk-2x-baseline.md` | Version, imports, migration |

## Boundaries

- Graph edges, fan-out topology, and loops belong to `adk-graph-workflows`.
- One agent's tools, memory, and model belong to `adk-agent-architecture`.
- Cross-process calls belong to `adk-a2a`.
- Runtime internals before an agent boundary belong to `adk-architecture`.
