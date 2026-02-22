---
name: ADK Multi-Agent Workflows
description: This skill should be used when the user asks to "build a multi-agent system", "agent coordination", "agent team", "orchestration patterns", "langgraph workflow", or "agent workflow". Provides comprehensive guidance for designing and implementing coordinated multi-agent systems with various orchestration patterns.
version: 1.0.0
---

# ADK Multi-Agent Workflows

Multi-agent systems coordinate multiple specialized agents to solve complex problems. This skill covers orchestration patterns, state management, and implementation with LangGraph.

## Core Concepts

### Agents as Specialists

Each agent specializes in a domain:
- Researcher agent knows how to research
- Analyst agent knows how to analyze
- Writer agent knows how to write
- Supervisor agent routes to specialists

### Orchestration Patterns

Five primary patterns for coordinating agents:

**Supervisor Pattern**
- One supervisor agent receives requests
- Evaluates which specialist best handles request
- Routes to appropriate agent
- Collects and synthesizes responses
- Best for: Customer service, support systems, general task routing

**Hierarchical Pattern**
- Tree of agents, each handling increasing complexity
- Parent agents oversee child agents
- Requests escalate based on complexity
- Best for: Enterprise systems, support tiers, escalation workflows

**Conditional Routing Pattern**
- Route based on request properties
- Different paths for different scenarios
- LangGraph nodes and edges
- Best for: Decision trees, complex logic, conditional processes

**Debate Pattern**
- Multiple agents argue different perspectives
- Observer synthesizes positions
- Consensus or ranked outcomes
- Best for: Decision support, analysis, controversial topics

**Tool Use Routing Pattern**
- Agents specialized by tool set
- Each agent masters specific tools
- Router selects best agent for task
- Best for: Multi-domain operations, specialized tool mastery

### State Management

Multi-agent systems maintain state:
- Request context
- Intermediate results
- Agent outputs
- Final synthesis

Use LangGraph for state transitions and memory.

## Implementation with LangGraph

LangGraph enables building multi-agent workflows as directed graphs:

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class AgentState(TypedDict):
    request: str
    research_findings: str
    analysis: str
    final_response: str

# Create graph
graph = StateGraph(AgentState)

# Add nodes (agents)
graph.add_node("researcher", researcher_agent.process)
graph.add_node("analyst", analyst_agent.process)
graph.add_node("synthesizer", synthesizer_agent.process)

# Add edges (workflow paths)
graph.add_edge(START, "researcher")
graph.add_edge("researcher", "analyst")
graph.add_edge("analyst", "synthesizer")
graph.add_edge("synthesizer", END)

# Compile
workflow = graph.compile()

# Execute
result = workflow.invoke({"request": "Analyze market opportunity in X"})
```

## Orchestration Patterns - Detailed

### Pattern 1: Supervisor

```python
class SupervisorOrchestrator:
    def __init__(self, agents: dict):
        self.supervisor = Agent(role="supervisor")
        self.specialists = agents

    def handle_request(self, request: str):
        # Supervisor routes to specialist
        best_agent = self.supervisor.choose_agent(request, self.specialists.keys())

        # Specialist handles
        result = self.specialists[best_agent].process(request)

        # Supervisor synthesizes if needed
        return result
```

Best for: General task routing, support systems, team coordination

### Pattern 2: Hierarchical

```python
class HierarchicalOrchestrator:
    def __init__(self):
        self.level_1 = SimpleAgent()
        self.level_2 = AdvancedAgent()
        self.level_3 = ExpertAgent()

    def handle_request(self, request: str):
        # Level 1 handles simple requests
        if self._is_simple(request):
            return self.level_1.process(request)

        # Level 2 handles complex requests
        if self._is_complex(request):
            return self.level_2.process(request)

        # Level 3 handles expert requests
        return self.level_3.process(request)
```

Best for: Escalation workflows, support tiers, enterprise systems

### Pattern 3: Conditional Routing

```python
from langgraph.graph import StateGraph

graph = StateGraph(State)

# Different paths for different request types
def route_request(state):
    if "urgent" in state["request"].lower():
        return "urgent_handler"
    elif "complex" in state["request"].lower():
        return "research"
    else:
        return "simple"

graph.add_conditional_edges(START, route_request)
```

Best for: Decision trees, complex routing, multi-path workflows

### Pattern 4: Debate

```python
class DebateOrchestrator:
    def __init__(self, agents: list):
        self.agents = agents
        self.observer = Agent(role="observer")

    def debate_topic(self, topic: str) -> dict:
        # Each agent argues position
        positions = [agent.argue(topic) for agent in self.agents]

        # Observer synthesizes
        consensus = self.observer.synthesize(positions)

        return {
            "positions": positions,
            "synthesis": consensus
        }
```

Best for: Analysis, controversial topics, decision support

### Pattern 5: Tool Use Routing

```python
class ToolRoutingOrchestrator:
    def __init__(self):
        self.sql_expert = Agent(tools=[sql_tools])
        self.api_expert = Agent(tools=[api_tools])
        self.code_expert = Agent(tools=[code_tools])

    def execute_task(self, task: str):
        # Determine which tools needed
        required_tools = self._analyze_requirements(task)

        # Select best agent
        best_agent = self._select_agent(required_tools)

        # Execute
        return best_agent.process(task)
```

Best for: Multi-domain operations, specialized tool mastery

## State Management with LangGraph

### State Definition

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Input
    original_request: str

    # Intermediate
    messages: Annotated[list, add_messages]
    research_findings: str
    analysis_results: str

    # Output
    final_response: str
    confidence: float
```

### Reducing State

```python
# Update state after each agent
def reduce_state(state, agent_output):
    state["messages"].append(agent_output)
    state["analysis_results"] = agent_output.get("analysis")
    return state
```

### Accessing State in Agents

```python
def researcher_process(state):
    request = state["original_request"]
    findings = conduct_research(request)
    return {"research_findings": findings}
```

## Testing Multi-Agent Systems

### Scenario Testing

```python
test_scenarios = [
    {
        "request": "Analyze market opportunity",
        "expected_pattern": "research→analysis→synthesis"
    },
    {
        "request": "Urgent support issue",
        "expected_pattern": "supervisor→specialist"
    }
]

for scenario in test_scenarios:
    result = orchestrator.handle_request(scenario["request"])
    assert_correct_flow(result, scenario["expected_pattern"])
```

### Performance Testing

```python
import time

start = time.time()
result = orchestrator.handle_request(request)
elapsed = time.time() - start

assert elapsed < 5.0, "Response took too long"
assert "final_response" in result
```

## Supporting Resources

### References
- **`references/patterns.md`** - Detailed pattern descriptions with examples
- **`references/langgraph-guide.md`** - LangGraph architecture and patterns
- **`references/state-management.md`** - State design and management

### Examples
- **`examples/supervisor-example.py`** - Supervisor pattern implementation
- **`examples/hierarchical-example.py`** - Hierarchical pattern
- **`examples/langgraph-workflow.py`** - LangGraph multi-agent system

## Next Steps

1. **Choose orchestration pattern** matching your use case
2. **Define agent specialists** - What does each agent do?
3. **Design state structure** - What data flows between agents?
4. **Build with LangGraph** - Implement graph nodes and edges
5. **Test workflows** - Verify correct agent execution paths
6. **Deploy** - Use adk-production-deployment skill

See **adk-custom-agent-builder** skill for building individual agents.

See **adk-knowledge-systems** skill for sharing knowledge across agents.
