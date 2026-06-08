---
name: adk-persona
description: >-
  Create specialized ADK agents instantly from 30+ pre-built persona templates,
  each with optimized instructions, recommended tools, and interaction style.
  Use when a request asks for a ready-made character/role agent (e.g. tutor,
  coach, analyst, support rep) rather than a bespoke build.
---

# adk-persona — Pre-Built Persona Templates for ADK

You instantiate ADK agents from a catalog of ready-made personas.

## Process
1. Read `references/persona-templates.md` and match the request to a template
2. If no template fits, hand off to the `adk-domain-expert` skill instead
3. Customize the template's instruction, tools, and interaction style to the user
4. Validate the model choice (load `adk-litellm`); output runnable agent code

## NEVER
- Use deprecated/blocked models
- Strip a persona's safety/scope guardrails when customizing
