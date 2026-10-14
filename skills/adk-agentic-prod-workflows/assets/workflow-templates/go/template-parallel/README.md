---
name: template-parallel-go
description: Fan-out to independent workers using ParallelAgent. Go. Use for concurrent search, multi-source fetch, parallel validation.
---

# Parallel Template (Go)

Fan-out execution where all sub-agents run concurrently using ADK `parallelagent.New()`. Each worker writes to its own output. Total wall time = slowest worker.

## When to Use

- Multi-source search (web + DB + cache simultaneously)
- Parallel validation checks
- Concurrent API calls for data enrichment
- Any task where sub-tasks are independent
