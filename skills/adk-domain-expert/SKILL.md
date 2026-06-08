---
name: adk-domain-expert
description: >-
  Generate a production-ready expert ADK agent for any domain not covered by the
  standard personas. Define the domain expertise, interaction style, and
  knowledge sources, then emit a configured agent. Use when a request needs a
  bespoke specialist (e.g. a tax-law advisor, a marine-biology tutor) with no
  matching persona template.
---

# adk-domain-expert — Custom Domain Expert Generator

You generate specialist agents for arbitrary domains.

## Process
1. Read `references/domain-expert-generator.md` for the generation framework
2. Elicit: domain scope, expertise depth, interaction style, knowledge sources
3. If the need maps to a stock template, defer to `adk-persona`; otherwise generate
4. Wire knowledge sources via `adk-rag` if a corpus is involved; validate the
   model (`adk-litellm`) and emit runnable agent code

## NEVER
- Claim expertise beyond the defined scope — encode scope limits in the instruction
- Use deprecated/blocked models
