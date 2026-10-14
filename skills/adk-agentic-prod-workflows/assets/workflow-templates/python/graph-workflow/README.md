---
name: graph-workflow-python
description: DAG-based ADK 2.x Workflow template using START and edge tuples. Python. Use for multi-step pipelines with branching logic.
---

# Graph Workflow (Python)

DAG-based workflow using ADK 2.x `Workflow` — nodes represent agents or functions, edges define transitions, route maps gate branching.

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

- `Workflow` — workflow container
- `Node(id, agent)` — workflow step
- `Edge(source, target, condition)` — transition
- `Condition(lambda state: bool)` — branching gate
