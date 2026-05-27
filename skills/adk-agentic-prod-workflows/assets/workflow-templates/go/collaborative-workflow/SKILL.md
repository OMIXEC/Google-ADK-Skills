---
name: collaborative-workflow-go
description: Coordinator + sub-agents sharing state. Go. Use for multi-agent collaboration with shared context.
---

# Collaborative Workflow (Go)

Coordinator delegates to specialized sub-agents that share session state. Each worker reads and writes to a shared state map.

## When to Use

- Multiple specialists collaborating on one task
- Shared context across agents (research → write → review)
- Coordinator pattern where one agent manages task distribution
