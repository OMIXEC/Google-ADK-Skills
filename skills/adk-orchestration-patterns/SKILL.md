---
name: adk-orchestration-patterns
version: 1.0.0
description: >
  Use when orchestrating multiple agents with Sequential, Parallel, Loop, or LLM-based routing.
  Supports static pipelines, dynamic delegation, conditional branching, and hierarchical multi-agent systems.
trigger_keywords:
  - orchestration
  - multi-agent coordination
  - sequential agents
  - parallel agents
  - loop agent
  - routing patterns
  - hierarchical agents
  - dynamic routing
  - agent pipeline
  - agent coordination
examples:
  - Sequential processing pipeline
  - Parallel task execution
  - Iterative refinement loop
  - LLM-based request routing
  - Hierarchical supervisor pattern
references:
  - agent-types.md
  - routing-patterns.md
templates: []
---

# ADK Orchestration Patterns

## Overview

Google ADK provides four fundamental agent types for orchestration, plus multiple routing patterns for building complex multi-agent systems. This skill covers all orchestration patterns from simple pipelines to hierarchical routing.

## When to Use This Skill

- Coordinating multiple specialized agents
- Building sequential processing pipelines
- Executing tasks in parallel
- Implementing iterative refinement workflows
- Creating intelligent routing systems
- Designing hierarchical multi-agent architectures

## Core Agent Types

### 1. SequentialAgent

Execute agents in a predetermined order. Each agent receives the output of the previous agent.

**Use Cases:**
- Multi-stage processing pipelines
- Sequential validation chains
- Step-by-step transformations
- Review workflows

**Example:**
```python
from google.adk.agents import SequentialAgent, LlmAgent

# Create specialized agents
researcher = LlmAgent(
    name="researcher",
    model="gemini-2.5-flash",
    instruction="Research the topic and gather information."
)

writer = LlmAgent(
    name="writer",
    model="gemini-2.5-flash",
    instruction="Write a comprehensive article based on research."
)

editor = LlmAgent(
    name="editor",
    model="gemini-2.5-flash",
    instruction="Edit and polish the article for publication."
)

# Sequential pipeline: research -> write -> edit
pipeline = SequentialAgent(
    name="content_pipeline",
    sub_agents=[researcher, writer, editor],
)

# Execute the pipeline
result = pipeline.run("Write an article about quantum computing")
```

### 2. ParallelAgent

Execute multiple agents concurrently. All agents receive the same input and their results are aggregated.

**Use Cases:**
- Multiple perspectives on the same problem
- Concurrent data processing
- Parallel validation checks
- Multi-source information gathering

**Example:**
```python
from google.adk.agents import ParallelAgent, LlmAgent

# Create parallel analyzers
technical_analyst = LlmAgent(
    name="technical",
    instruction="Analyze from technical perspective."
)

business_analyst = LlmAgent(
    name="business",
    instruction="Analyze from business perspective."
)

risk_analyst = LlmAgent(
    name="risk",
    instruction="Analyze potential risks and concerns."
)

# Parallel analysis
analysis_team = ParallelAgent(
    name="parallel_analysis",
    sub_agents=[technical_analyst, business_analyst, risk_analyst],
)

result = analysis_team.run("Should we adopt this new technology?")
```

### 3. LoopAgent

Execute agents iteratively with conditions. Supports refinement loops and iterative processing.

**Use Cases:**
- Iterative refinement
- Quality improvement loops
- Retry logic with intelligence
- Convergence algorithms

**Example:**
```python
from google.adk.agents import LoopAgent, LlmAgent

# Iterative refinement agent
refiner = LlmAgent(
    name="refiner",
    instruction="Improve the code quality, fix issues, and enhance clarity."
)

# Loop until quality threshold or max iterations
refinement_loop = LoopAgent(
    name="iterative_refinement",
    sub_agents=[refiner],
    max_iterations=5,
)

result = refinement_loop.run("Refine this code: def calc(x,y): return x+y")
```

### 4. LlmAgent with Dynamic Routing

Use an LLM to intelligently route requests to appropriate specialist agents.

**Use Cases:**
- Customer service routing
- Task delegation based on intent
- Adaptive workflow selection
- Smart request classification

**Example:**
```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Create specialist agents
billing_agent = LlmAgent(
    name="billing_specialist",
    instruction="Handle billing questions and payment issues."
)

support_agent = LlmAgent(
    name="support_specialist",
    instruction="Handle technical support and troubleshooting."
)

sales_agent = LlmAgent(
    name="sales_specialist",
    instruction="Handle product inquiries and sales questions."
)

# Coordinator with dynamic routing
coordinator = LlmAgent(
    name="coordinator",
    model="gemini-2.5-flash",
    description="Routes customer requests to appropriate specialists",
    tools=[
        AgentTool(agent=billing_agent),
        AgentTool(agent=support_agent),
        AgentTool(agent=sales_agent),
    ],
    instruction="""
    Analyze the customer request and route to the appropriate specialist:
    - Billing specialist for payment, invoice, or subscription issues
    - Support specialist for technical problems or how-to questions
    - Sales specialist for product features, pricing, or purchase questions
    """,
)

result = coordinator.run("I can't log into my account")
```

## Routing Patterns

### Static Routing

Predetermined agent sequence defined at design time.

```python
from google.adk.agents import SequentialAgent

# Fixed sequence: validate -> process -> notify
workflow = SequentialAgent(
    name="static_workflow",
    sub_agents=[validator, processor, notifier],
)
```

### Dynamic Routing

LLM decides which agent(s) to invoke based on input.

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

router = LlmAgent(
    name="smart_router",
    tools=[AgentTool(agent=agent_a), AgentTool(agent=agent_b)],
    instruction="Choose the best agent for this request.",
)
```

### Conditional Routing

Rule-based branching based on agent outputs or state.

```python
from google.adk.agents import SequentialAgent, LlmAgent

# Custom logic in application layer
def route_based_on_result(initial_result):
    if initial_result.contains_error:
        return error_handler.run(initial_result)
    else:
        return success_handler.run(initial_result)

classifier = LlmAgent(name="classifier", instruction="Classify input")
initial = classifier.run(user_input)
final = route_based_on_result(initial)
```

### Hierarchical Routing

Tree of supervisors delegating to sub-teams.

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Team leads
engineering_lead = LlmAgent(
    name="engineering_lead",
    tools=[AgentTool(agent=backend_dev), AgentTool(agent=frontend_dev)],
    instruction="Delegate to backend or frontend developers.",
)

product_lead = LlmAgent(
    name="product_lead",
    tools=[AgentTool(agent=designer), AgentTool(agent=researcher)],
    instruction="Delegate to designers or researchers.",
)

# Executive coordinator
cto = LlmAgent(
    name="cto",
    tools=[AgentTool(agent=engineering_lead), AgentTool(agent=product_lead)],
    instruction="Delegate to engineering or product teams.",
)

result = cto.run("We need to redesign the user dashboard")
```

## State Management in Orchestrated Systems

### Passing State Between Agents

Agents can pass context via their output:

```python
from google.adk.agents import SequentialAgent, LlmAgent

collector = LlmAgent(
    name="collector",
    instruction="Gather requirements and output structured JSON."
)

builder = LlmAgent(
    name="builder",
    instruction="Build solution based on the requirements JSON from previous agent."
)

pipeline = SequentialAgent(
    name="build_pipeline",
    sub_agents=[collector, builder],
)
```

### Shared Memory

Use external state management for shared context:

```python
from google.adk.agents import LlmAgent, ParallelAgent

# Agents can share context via tools or external storage
shared_context = {"project_id": "abc123", "deadline": "2026-03-01"}

agent_a = LlmAgent(
    name="agent_a",
    instruction=f"Use project context: {shared_context}",
)

agent_b = LlmAgent(
    name="agent_b",
    instruction=f"Use project context: {shared_context}",
)
```

### Event-Driven Communication

Agents can communicate via callbacks or event systems:

```python
class EventBus:
    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)

    def get_events(self):
        return self.events

bus = EventBus()

# Agents use tools to publish/subscribe to events
```

## Best Practices

1. **Choose the Right Pattern:**
   - Sequential: When order matters and each step depends on previous
   - Parallel: When tasks are independent and can run concurrently
   - Loop: When iterative refinement or retry logic is needed
   - LLM Router: When routing logic is complex or context-dependent

2. **Design for Composability:**
   - Each agent should have a clear, single responsibility
   - Agent outputs should be self-contained and informative
   - Avoid deep nesting (keep hierarchies to 2-3 levels)

3. **Handle Failures Gracefully:**
   - Implement error handling at each level
   - Use try/except in custom orchestration logic
   - Provide fallback agents or default behaviors

4. **Optimize for Performance:**
   - Use Parallel agents for I/O-bound tasks
   - Limit Loop iterations to prevent infinite loops
   - Cache agent results when appropriate

5. **Monitor and Debug:**
   - Log agent transitions and decisions
   - Track execution time for each agent
   - Use descriptive agent names for observability

## Common Patterns

### Research-Write-Edit Pipeline

```python
pipeline = SequentialAgent(
    name="content_creation",
    sub_agents=[researcher, writer, editor],
)
```

### Multi-Perspective Analysis

```python
analysis = ParallelAgent(
    name="comprehensive_analysis",
    sub_agents=[technical_expert, business_expert, legal_expert],
)
```

### Quality Refinement Loop

```python
quality_loop = LoopAgent(
    name="quality_improvement",
    sub_agents=[analyzer, improver],
    max_iterations=3,
)
```

### Customer Service Router

```python
customer_service = LlmAgent(
    name="customer_service",
    tools=[
        AgentTool(agent=billing_agent),
        AgentTool(agent=support_agent),
        AgentTool(agent=sales_agent),
    ],
    instruction="Route customer to appropriate specialist.",
)
```

## Related Skills

- @adk-multi-agent-orchestrator (Team patterns and collaboration)
- @adk-langgraph-orchestrator (Advanced graph-based orchestration)
- @adk-callback-patterns (Monitoring orchestrated agents)
- @adk-session-management (State management in orchestration)

## Reference Documentation

- @agent-types - Detailed specifications for each agent type
- @routing-patterns - Advanced routing strategies and examples
