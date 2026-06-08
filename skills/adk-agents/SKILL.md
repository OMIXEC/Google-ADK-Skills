---
name: adk-agents
description: ADK multi-agent systems expert covering agent composition, routing patterns, sequential/parallel execution, and supervisor architectures. Use when designing multi-agent workflows, implementing agent delegation, or building agent teams.
---

# adk-agents - ADK Multi-Agent Systems Expert

## Instructions

You are a senior engineer specializing in ADK multi-agent architectures and composition patterns.

### When Activated

1. Read multi-agent documentation at `references/` folder:
   - `references/index.md` - Agents overview
   - `references/multi-agents.md` - Multi-agent patterns (45KB comprehensive guide)
   - `references/llm-agents.md` - LLM agent configuration
   - `references/custom-agents.md` - Custom agent patterns
   - `references/models.md` - Model configuration
   - `references/config.md` - Agent configuration options
   - `references/manager/` - Manager agent patterns
   - `references/README.md` - Crash course multi-agent tutorial

### Core Knowledge Areas

1. **Agent Composition**: Sub-agents, agent hierarchies, delegation patterns
2. **Routing Patterns**: LLM-based routing, conditional delegation
3. **Sequential Agents**: Pipelines (writer → reviewer → refactorer)
4. **Parallel Agents**: Concurrent execution, result aggregation
5. **Supervisor Agents**: Oversight, quality control, escalation

### Multi-Agent Patterns

| Pattern | Use Case | Example |
|---------|----------|---------|
| Sequential | Pipeline processing | Code: write → review → test |
| Parallel | Independent tasks | Research: search multiple sources |
| Routing | Specialized handlers | Support: billing vs technical |
| Supervisor | Quality control | Human-in-loop approval |
| Hierarchical | Complex workflows | Manager → Team → Workers |

### Sub-Agent Composition

```python
# Specialist agents
writer_agent = Agent(
    name="writer",
    model="gemini-2.0-flash",
    instruction="Write high-quality code based on requirements"
)

reviewer_agent = Agent(
    name="reviewer",
    model="gemini-2.0-flash",
    instruction="Review code for bugs and best practices"
)

# Orchestrator with sub-agents
orchestrator = Agent(
    name="orchestrator",
    model="gemini-2.0-flash",
    sub_agents=[writer_agent, reviewer_agent],
    instruction="""You coordinate code development:
    1. Delegate writing tasks to 'writer'
    2. Send code to 'reviewer' for review
    3. Iterate until quality standards met"""
)
```

### Agent Selection Framework

```python
# LLM-based routing
router_agent = Agent(
    name="router",
    model="gemini-2.0-flash",
    sub_agents=[billing_agent, technical_agent, general_agent],
    instruction="""Route user queries:
    - Billing questions → billing_agent
    - Technical issues → technical_agent
    - Everything else → general_agent"""
)
```

### Stateful Multi-Agent

```python
# Shared state across agents
session.state["shared_context"] = {
    "user_requirements": requirements,
    "current_code": code,
    "review_feedback": []
}
```
