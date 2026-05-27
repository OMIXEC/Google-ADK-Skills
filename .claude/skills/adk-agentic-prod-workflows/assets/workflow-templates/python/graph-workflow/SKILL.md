---
name: graph-workflow-python
description: DAG-based ADK workflow template using GraphAgent with nodes, edges, and conditions. Python. Use for multi-step pipelines with branching logic.
---

# Graph Workflow (Python)

DAG-based workflow using `GraphAgent` — nodes represent agents, edges define transitions, conditions gate branching.

## When to Use

- Multi-step pipelines with conditional branching
- Approval workflows (validate → approve → process)
- Classification → routing patterns
- Any workflow where execution path depends on intermediate results

## Template Files

| File | Purpose |
|------|---------|
| `workflow.py` | Main workflow: agents, tools, graph assembly |
| `agents.py` | Agent definitions (validator, processor, etc.) |
| `tools.py` | Tool definitions with Pydantic schemas |
| `requirements.txt` | Dependencies |

## Key ADK Classes

- `GraphAgent` — workflow container
- `Node(id, agent)` — workflow step
- `Edge(source, target, condition)` — transition
- `Condition(lambda state: bool)` — branching gate
