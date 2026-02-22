---
name: adk-enterprise-multi-agent
description: When would Claude invoke this? When building enterprise-scale multi-agent systems with hierarchical supervision, agent pools, domain-driven design, or coordinating 10+ agents for large organizations.
trigger: enterprise multi-agent, hierarchical agents, agent supervisor tree, agent registry, domain-driven agents, large-scale agent systems, 100+ agents, agent pool, cross-agent coordination
version: 1.0.0
category: enterprise
tags: [multi-agent, enterprise, scalability, supervision, hierarchy]
---

# ADK Enterprise Multi-Agent Architecture

Build enterprise-scale multi-agent systems supporting 100+ agents with hierarchical supervision, domain-driven design, and production-grade coordination.

## When to Use This Skill

Use enterprise multi-agent architecture when:
- Coordinating 10+ agents in a single system
- Building organizational AI aligned to business structure
- Implementing supervisor hierarchies (root → department → specialist)
- Deploying domain-driven agent teams
- Managing large-scale agent pools with discovery and load balancing

## Core Concepts

### 1. Hierarchical Supervisor Tree

Three-level architecture for enterprise scale:

```
Executive Coordinator (Gemini 2.5 Pro)
├── Customer Operations Supervisor (Gemini 2.5 Flash)
│   ├── Sales Specialist
│   ├── Support Specialist
│   └── Success Specialist
├── Product Operations Supervisor (Gemini 2.5 Flash)
│   ├── Development Specialist
│   ├── QA Specialist
│   └── Deployment Specialist
└── Business Operations Supervisor (Gemini 2.5 Flash)
    ├── Finance Specialist
    ├── HR Specialist
    └── Legal Specialist
```

**Design Principles:**
- Root coordinator uses Pro model for complex reasoning
- Supervisors use Flash for efficient delegation
- Specialists are optimized for specific tasks
- Each level adds ~3-5x agent fan-out

### 2. Domain-Driven Agent Design

Align agent teams to business domains using bounded contexts:

**Bounded Context = Business Domain + Agent Team**
- Customer domain → Customer operations agents
- Product domain → Product operations agents
- Business domain → Business operations agents

**Cross-domain coordination:**
- Event-driven messaging between domains
- Shared state through centralized services
- Clear ownership boundaries

### 3. Agent Registry Pattern

Centralized discovery and management:

```python
@dataclass
class AgentRegistry:
    """Enterprise agent registry for discovery and management."""
    agents: Dict[str, LlmAgent]
    supervisors: Dict[str, LlmAgent]

    def get_agent(self, name: str) -> LlmAgent:
        return self.agents.get(name) or self.supervisors.get(name)

    def get_domain_agents(self, domain: str) -> List[LlmAgent]:
        return [a for a in self.agents.values() if a.name.startswith(domain)]

    def register_agent(self, agent: LlmAgent, domain: str):
        self.agents[agent.name] = agent
```

## Implementation Guide

### Step 1: Define Enterprise Hierarchy

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Level 1: Executive Coordinator
executive_coordinator = LlmAgent(
    name="executive_coordinator",
    model="gemini-2.5-pro",  # Best reasoning for top-level decisions
    description="Enterprise coordinator for all business operations",
    instruction="""
    You are the enterprise AI coordinator. You manage:
    1. Customer Operations - sales, support, success
    2. Product Operations - development, QA, deployment
    3. Business Operations - finance, HR, legal

    Delegate to appropriate department supervisors.
    Synthesize cross-department insights.
    Escalate critical decisions to humans.
    """,
)

# Level 2: Department Supervisors
customer_ops = LlmAgent(
    name="customer_operations_supervisor",
    model="gemini-2.5-flash",
    description="Manages customer-facing agent teams",
    instruction="Coordinate sales, support, and success agents for optimal customer experience.",
)

product_ops = LlmAgent(
    name="product_operations_supervisor",
    model="gemini-2.5-flash",
    description="Manages product development agents",
    instruction="Coordinate development, QA, and deployment agents for product excellence.",
)

business_ops = LlmAgent(
    name="business_operations_supervisor",
    model="gemini-2.5-flash",
    description="Manages business function agents",
    instruction="Coordinate finance, HR, and legal agents for business operations.",
)

# Level 3: Specialist Agents
sales_agent = LlmAgent(
    name="sales_specialist",
    model="gemini-2.5-flash",
    description="Handles sales inquiries and lead qualification",
)

support_agent = LlmAgent(
    name="support_specialist",
    model="gemini-2.5-flash",
    description="Resolves customer support tickets",
)

dev_agent = LlmAgent(
    name="development_specialist",
    model="gemini-2.5-flash",
    description="Assists with code review and architecture",
)

qa_agent = LlmAgent(
    name="qa_specialist",
    model="gemini-2.5-flash",
    description="Performs testing and quality assurance",
)
```

### Step 2: Wire Hierarchy with AgentTool

```python
# Wire Level 2 to Level 3
customer_ops.tools = [
    AgentTool(agent=sales_agent),
    AgentTool(agent=support_agent),
]

product_ops.tools = [
    AgentTool(agent=dev_agent),
    AgentTool(agent=qa_agent),
]

# Wire Level 1 to Level 2
executive_coordinator.tools = [
    AgentTool(agent=customer_ops),
    AgentTool(agent=product_ops),
    AgentTool(agent=business_ops),
]
```

### Step 3: Add Enterprise Features

```python
from datetime import datetime
from typing import Dict, List
import logging

class EnterpriseAgentMonitor:
    """Monitor agent health and performance."""

    def __init__(self):
        self.metrics: Dict[str, List[dict]] = {}
        self.logger = logging.getLogger(__name__)

    def record_invocation(self, agent_name: str, duration: float, success: bool):
        if agent_name not in self.metrics:
            self.metrics[agent_name] = []

        self.metrics[agent_name].append({
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "success": success,
        })

    def get_agent_health(self, agent_name: str) -> dict:
        if agent_name not in self.metrics:
            return {"status": "unknown"}

        recent = self.metrics[agent_name][-100:]  # Last 100 invocations
        success_rate = sum(1 for m in recent if m["success"]) / len(recent)
        avg_duration = sum(m["duration"] for m in recent) / len(recent)

        return {
            "status": "healthy" if success_rate > 0.95 else "degraded",
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "total_invocations": len(recent),
        }

# Integrate monitoring
monitor = EnterpriseAgentMonitor()

# Wrap agents with monitoring
def monitored_invoke(agent: LlmAgent, original_invoke):
    async def wrapper(*args, **kwargs):
        start = datetime.now()
        try:
            result = await original_invoke(*args, **kwargs)
            duration = (datetime.now() - start).total_seconds()
            monitor.record_invocation(agent.name, duration, True)
            return result
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            monitor.record_invocation(agent.name, duration, False)
            raise
    return wrapper
```

### Step 4: Implement Agent Pool

```python
from typing import Optional

class AgentPool:
    """Dynamic agent pool with load balancing."""

    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.active_agents: Dict[str, LlmAgent] = {}
        self.agent_usage: Dict[str, int] = {}

    def get_or_create_agent(self, agent_type: str, config: dict) -> LlmAgent:
        """Get least-used agent or create new one if under pool size."""
        # Find least-used agent of this type
        type_agents = {
            name: agent for name, agent in self.active_agents.items()
            if agent.name.startswith(agent_type)
        }

        if type_agents:
            # Return least-used
            least_used = min(type_agents.items(), key=lambda x: self.agent_usage.get(x[0], 0))
            self.agent_usage[least_used[0]] = self.agent_usage.get(least_used[0], 0) + 1
            return least_used[1]

        # Create new if under pool size
        if len(type_agents) < self.pool_size:
            agent = LlmAgent(**config)
            agent_id = f"{agent_type}_{len(type_agents)}"
            self.active_agents[agent_id] = agent
            self.agent_usage[agent_id] = 1
            return agent

        # Reuse existing (fallback)
        return list(type_agents.values())[0]
```

## Enterprise Patterns

### Agent Registry Pattern

See reference: `@references/agent-registry.md`

### Scalability Guide

See reference: `@references/scalability-guide.md`

### Hierarchy Design

See reference: `@references/hierarchy-patterns.md`

## Examples

- **Enterprise Hierarchy:** `@examples/enterprise-hierarchy.md`
- **Domain-Driven Agents:** `@examples/domain-driven-agents.md`

## Production Considerations

### Monitoring and Observability

```python
# Log all agent interactions
import structlog

logger = structlog.get_logger()

logger.info(
    "agent_invoked",
    agent=agent.name,
    supervisor=supervisor.name,
    domain=domain,
    user_id=user_id,
)
```

### Cost Allocation

Track API costs per agent:

```python
def calculate_agent_cost(agent_name: str, token_usage: dict) -> float:
    """Calculate cost based on model and token usage."""
    model_costs = {
        "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},  # per 1K tokens
        "gemini-2.5-flash": {"input": 0.000075, "output": 0.0003},
    }

    agent = registry.get_agent(agent_name)
    costs = model_costs[agent.model]

    input_cost = (token_usage["input"] / 1000) * costs["input"]
    output_cost = (token_usage["output"] / 1000) * costs["output"]

    return input_cost + output_cost
```

### Access Control

```python
from typing import Set

class AgentAccessControl:
    """Role-based access control for agents."""

    def __init__(self):
        self.permissions: Dict[str, Set[str]] = {}

    def grant_access(self, user_id: str, agent_name: str):
        if user_id not in self.permissions:
            self.permissions[user_id] = set()
        self.permissions[user_id].add(agent_name)

    def can_access(self, user_id: str, agent_name: str) -> bool:
        return agent_name in self.permissions.get(user_id, set())

    def get_accessible_agents(self, user_id: str) -> List[str]:
        return list(self.permissions.get(user_id, set()))
```

## Testing

```python
import pytest

@pytest.mark.asyncio
async def test_enterprise_hierarchy():
    """Test complete hierarchy delegation."""
    # Create hierarchy
    executive = create_executive_coordinator()

    # Test delegation
    result = await executive.invoke("Process customer support ticket #12345")

    # Should route: executive -> customer_ops -> support_specialist
    assert "customer_operations" in result.agent_path
    assert "support_specialist" in result.agent_path

@pytest.mark.asyncio
async def test_agent_pool_load_balancing():
    """Test pool distributes load evenly."""
    pool = AgentPool(pool_size=3)

    # Create 10 requests
    agents = [pool.get_or_create_agent("sales", {}) for _ in range(10)]

    # Check distribution
    usage = pool.agent_usage
    max_usage = max(usage.values())
    min_usage = min(usage.values())

    # Should be balanced within 2 requests
    assert max_usage - min_usage <= 2
```

## Related Skills

- **adk-agent-orchestration:** Basic multi-agent patterns
- **adk-session-management:** Cross-agent state coordination
- **adk-callback-patterns:** Enterprise monitoring hooks
- **adk-adaptive-memory:** Shared memory across agents

## References

- [Agent Registry Pattern](@references/agent-registry.md)
- [Hierarchy Design](@references/hierarchy-patterns.md)
- [Scalability Guide](@references/scalability-guide.md)
