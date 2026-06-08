---
name: adk-autonomous-agent
description: >-
  Build autonomous, self-reasoning ADK agents with proactive, goal-directed
  execution using the OODA loop (Observe, Orient, Decide, Act) and explicit
  planning. Use when a request asks for an agent that runs without per-step human
  follow-up, plans its own steps, or pursues a goal autonomously.
---

# adk-autonomous-agent — Self-Reasoning Autonomous Agents

You build agents that plan and act toward a goal with minimal human intervention.

## Process
1. Read `references/autonomous-agents.md` for the OODA-loop pattern and planning scaffold
2. Define the goal, success criteria, and stop conditions (max iterations, budget)
3. Implement Observe → Orient → Decide → Act with explicit reasoning traces
4. Add a quality/exit gate so the loop terminates; validate the model (`adk-litellm`)

## NEVER
- Build an unbounded loop — always set max iterations and a stop condition
- Use deprecated/blocked models
- Let the agent take irreversible external actions without a guard/approval step
