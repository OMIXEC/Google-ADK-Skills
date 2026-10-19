---
name: adk-agent-personas
description: >-
  Instantiates a ready-made or bespoke persona agent: 30+ pre-built templates (tutor,
  coach, analyst, support rep, and others) plus a generator for domains with no matching
  template. Use when the request is about who the agent is: its role, expertise,
  interaction style, and scope. Don't use for how the agent runs over time (use
  adk-agent-orchestration), for its tools and memory (use adk-agent-architecture), or
  for a corpus-backed specialist (choose the persona here, then wire the corpus with
  adk-rag).
compatibility: google-adk>=2.9.2,<3
---

# Agent Personas

Two ways in: reuse a template, or generate a specialist. Both end at the same
place — a runnable agent definition with a bounded role.

## Choose the path

| Situation | Path |
|---|---|
| The role matches a known archetype | Template, then customize |
| The domain is specific and no template fits | Generator |
| The role is a thin wrapper around a corpus | Persona first, then `adk-rag` |

Read `references/persona-templates.md` to match a template. If nothing fits,
read `references/domain-expert-generator.md` and generate.

## Process

1. **Match or reject.** Scan the template catalog before writing anything.
   Rejecting every template is a valid outcome; duplicating one is not.
2. **Fix the scope.** Name what the persona knows, what it must refuse, and
   where it hands off. A persona without scope limits will answer anything.
3. **Set the instruction.** Role, audience, tone, allowed actions, refusal
   behavior, and escalation path. No personality padding.
4. **Pick the model.** Route by task complexity with `adk-model-routing`.
5. **Attach only the tools the role needs.** Tool design belongs to
   `adk-agent-architecture`.
6. **Emit runnable code** and a short note on what to customize.

## Guardrails

- Keep a template's safety and scope limits when customizing. Removing them is
  a rewrite, not a customization.
- Never claim expertise beyond the defined scope; encode the boundary in the
  instruction.
- Do not use retired or blocked model IDs.
- A persona is not an autonomy grant. If the agent must pursue a goal without
  step-by-step input, that is `adk-agent-orchestration`.

## References

| File | Load when |
|---|---|
| `references/persona-templates.md` | Matching a request to a pre-built role |
| `references/domain-expert-generator.md` | Generating a specialist for a new domain |

## Boundaries

- Runtime control, autonomous loops, and LangGraph state machines belong to
  `adk-agent-orchestration`.
- Tools, memory, MCP, and A2A belong to `adk-agent-architecture`.
