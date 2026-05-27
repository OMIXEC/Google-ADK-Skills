---
name: template-sequential-go
description: Fixed-order pipeline using SequentialAgent. Go. Use for deterministic Write→Review→Publish chains.
---

# Sequential Template (Go)

Linear pipeline where sub-agents execute in order using ADK `sequentialagent.New()`. Each agent's output is available to the next via session state.

## When to Use

- Content pipelines (write → review → publish)
- Data processing (extract → transform → load)
- Multi-step validation flows
