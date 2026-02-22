# Enterprise Agent Hierarchy Patterns

## Overview

This reference documents proven patterns for designing agent hierarchies at enterprise scale (10-1000+ agents).

## Pattern 1: Three-Level Supervision

**When to use:** Organizations with clear department structure (10-100 agents)

### Structure

```
Level 1 (Root): Executive Coordinator
├── Level 2 (Supervisors): Department Heads
│   └── Level 3 (Workers): Specialist Agents
```

### Characteristics

- **Root:** 1 coordinator (Gemini Pro for complex reasoning)
- **Supervisors:** 3-10 department heads (Gemini Flash for efficiency)
- **Workers:** 5-50 specialists per department (Gemini Flash, task-optimized)

### Example

```python
# Level 1: Executive (1 agent)
executive = LlmAgent(
    name="ceo_agent",
    model="gemini-2.5-pro",
    description="Coordinates all enterprise operations",
)

# Level 2: Department Supervisors (5 agents)
departments = {
    "sales": LlmAgent(name="sales_supervisor", model="gemini-2.5-flash"),
    "support": LlmAgent(name="support_supervisor", model="gemini-2.5-flash"),
    "engineering": LlmAgent(name="engineering_supervisor", model="gemini-2.5-flash"),
    "marketing": LlmAgent(name="marketing_supervisor", model="gemini-2.5-flash"),
    "operations": LlmAgent(name="operations_supervisor", model="gemini-2.5-flash"),
}

# Level 3: Specialists (20+ agents)
sales_specialists = [
    LlmAgent(name="lead_qualifier", model="gemini-2.5-flash"),
    LlmAgent(name="proposal_writer", model="gemini-2.5-flash"),
    LlmAgent(name="contract_reviewer", model="gemini-2.5-flash"),
]

# Wire hierarchy
departments["sales"].tools = [AgentTool(agent=a) for a in sales_specialists]
executive.tools = [AgentTool(agent=sup) for sup in departments.values()]
```

**Fan-out:** 1 → 5 → 20 = 25 total agents

## Pattern 2: Domain-Driven Hierarchy

**When to use:** Complex organizations with bounded contexts (100-1000 agents)

### Structure

```
Root Coordinator
├── Domain A Coordinator
│   ├── Subdomain A1 Team Lead
│   │   ├── A1 Specialist 1
│   │   └── A1 Specialist 2
│   └── Subdomain A2 Team Lead
└── Domain B Coordinator
```

### Characteristics

- Mirrors DDD bounded contexts
- Each domain has internal hierarchy
- Cross-domain coordination at coordinator level
- Clear ownership boundaries

### Example: E-commerce Platform

```python
# Root
platform_coordinator = LlmAgent(name="platform_coordinator", model="gemini-2.5-pro")

# Domain Coordinators
customer_domain = LlmAgent(name="customer_domain_coordinator", model="gemini-2.5-flash")
product_domain = LlmAgent(name="product_domain_coordinator", model="gemini-2.5-flash")
order_domain = LlmAgent(name="order_domain_coordinator", model="gemini-2.5-flash")

# Customer Domain Subdomains
customer_profile_lead = LlmAgent(name="customer_profile_lead", model="gemini-2.5-flash")
customer_support_lead = LlmAgent(name="customer_support_lead", model="gemini-2.5-flash")

# Customer Profile Specialists
profile_agents = [
    LlmAgent(name="profile_updater", model="gemini-2.5-flash"),
    LlmAgent(name="preference_analyzer", model="gemini-2.5-flash"),
]

# Wire domain hierarchy
customer_profile_lead.tools = [AgentTool(agent=a) for a in profile_agents]
customer_domain.tools = [
    AgentTool(agent=customer_profile_lead),
    AgentTool(agent=customer_support_lead),
]
platform_coordinator.tools = [
    AgentTool(agent=customer_domain),
    AgentTool(agent=product_domain),
    AgentTool(agent=order_domain),
]
```

## Pattern 3: Matrix Organization

**When to use:** Cross-functional teams (50-500 agents)

### Structure

```
Product Teams (vertical) × Capabilities (horizontal)

Product A Lead ─┐
Product B Lead ─┼─→ Backend Capability Pool
Product C Lead ─┘    Frontend Capability Pool
                     Data Capability Pool
```

### Characteristics

- Products are primary hierarchy
- Capabilities are shared pools
- Dynamic allocation from pools to products
- Reusable specialist agents

### Example

```python
# Product teams (vertical)
product_teams = {
    "payments": LlmAgent(name="payments_lead", model="gemini-2.5-flash"),
    "checkout": LlmAgent(name="checkout_lead", model="gemini-2.5-flash"),
    "inventory": LlmAgent(name="inventory_lead", model="gemini-2.5-flash"),
}

# Capability pools (horizontal)
backend_pool = [
    LlmAgent(name="api_specialist_1", model="gemini-2.5-flash"),
    LlmAgent(name="api_specialist_2", model="gemini-2.5-flash"),
]

frontend_pool = [
    LlmAgent(name="ui_specialist_1", model="gemini-2.5-flash"),
    LlmAgent(name="ui_specialist_2", model="gemini-2.5-flash"),
]

# Dynamic allocation
class CapabilityPool:
    def assign_to_product(self, product_lead: LlmAgent, capability: str, duration: int):
        """Assign specialist from pool to product team."""
        if capability == "backend":
            specialist = self._get_available(backend_pool)
        elif capability == "frontend":
            specialist = self._get_available(frontend_pool)

        product_lead.tools.append(AgentTool(agent=specialist))
        # Schedule return to pool after duration
```

## Pattern 4: Event-Driven Mesh

**When to use:** Microservices-style agent systems (100-10000 agents)

### Structure

```
No fixed hierarchy - agents subscribe to event topics

Agent A ─┐
Agent B ─┼─→ Event Bus ─→ Topic 1, Topic 2, Topic 3
Agent C ─┘
```

### Characteristics

- Peer-to-peer coordination
- Publish-subscribe model
- No central supervisor
- High scalability

### Example

```python
from typing import Callable, Dict, List

class AgentEventBus:
    def __init__(self):
        self.subscriptions: Dict[str, List[Callable]] = {}

    def subscribe(self, topic: str, handler: Callable):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(handler)

    async def publish(self, topic: str, event: dict):
        handlers = self.subscriptions.get(topic, [])
        for handler in handlers:
            await handler(event)

# Create event bus
bus = AgentEventBus()

# Agents subscribe to relevant topics
async def order_created_handler(event: dict):
    order_agent = LlmAgent(name="order_processor", model="gemini-2.5-flash")
    await order_agent.invoke(f"Process order: {event}")

async def inventory_check_handler(event: dict):
    inventory_agent = LlmAgent(name="inventory_checker", model="gemini-2.5-flash")
    await inventory_agent.invoke(f"Check inventory: {event}")

bus.subscribe("order.created", order_created_handler)
bus.subscribe("order.created", inventory_check_handler)

# Publish events
await bus.publish("order.created", {"order_id": "12345", "items": [...]})
```

## Choosing a Pattern

| Pattern | Agents | Use Case | Complexity |
|---------|--------|----------|------------|
| Three-Level | 10-100 | Traditional org structure | Low |
| Domain-Driven | 100-1000 | Complex domains | Medium |
| Matrix | 50-500 | Cross-functional teams | Medium |
| Event-Driven | 100-10000 | Microservices architecture | High |

## Hybrid Patterns

Combine patterns for specific needs:

### Hybrid: Three-Level + Event Bus

```python
# Use three-level for supervision
executive = create_three_level_hierarchy()

# Add event bus for cross-domain coordination
bus = AgentEventBus()

# Supervisors publish domain events
async def sales_supervisor_handler(request):
    result = await sales_supervisor.invoke(request)
    await bus.publish("sales.lead_qualified", {"lead_id": result.lead_id})

# Other domains subscribe
bus.subscribe("sales.lead_qualified", marketing_automation_handler)
```

## Best Practices

### 1. Limit Fan-out per Level

- Root: 3-7 supervisors (cognitive limit)
- Supervisors: 5-10 workers
- Beyond 10, add intermediate level

### 2. Model Selection by Level

- **Root (L1):** Gemini 2.5 Pro (complex reasoning)
- **Supervisors (L2):** Gemini 2.5 Flash (efficient delegation)
- **Workers (L3):** Gemini 2.5 Flash (task execution)

### 3. Clear Responsibility Boundaries

Each agent should have:
- Single clear purpose
- Non-overlapping responsibilities
- Defined input/output contracts

### 4. Failure Isolation

- Supervisor failures don't cascade to workers
- Worker failures don't block siblings
- Root has circuit breakers for each supervisor

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
async def invoke_supervisor_with_retry(supervisor: LlmAgent, request: str):
    try:
        return await supervisor.invoke(request)
    except Exception as e:
        logger.error(f"Supervisor {supervisor.name} failed: {e}")
        # Return degraded response or route to backup supervisor
        return await backup_supervisor.invoke(request)
```

## Anti-Patterns

### 1. Too Many Levels

**Problem:** 5+ levels create communication overhead

```python
# Anti-pattern: Too deep
root → region → country → city → department → team → individual
```

**Solution:** Flatten to 3-4 levels max

### 2. Unbalanced Trees

**Problem:** Some branches much deeper than others

```python
# Anti-pattern
root → sales → specialist (2 levels)
root → engineering → backend → api → auth → jwt_handler (5 levels)
```

**Solution:** Normalize depth across branches

### 3. God Agent

**Problem:** One agent does everything

```python
# Anti-pattern
super_agent.tools = [all_100_specialists]
```

**Solution:** Add intermediate supervisors

## Monitoring Hierarchy Health

```python
def analyze_hierarchy_balance(root: LlmAgent) -> dict:
    """Analyze hierarchy for balance issues."""
    depths = []

    def measure_depth(agent: LlmAgent, depth: int = 0):
        if not agent.tools:
            depths.append(depth)
            return

        for tool in agent.tools:
            if isinstance(tool, AgentTool):
                measure_depth(tool.agent, depth + 1)

    measure_depth(root)

    return {
        "max_depth": max(depths),
        "min_depth": min(depths),
        "avg_depth": sum(depths) / len(depths),
        "balanced": max(depths) - min(depths) <= 1,  # Within 1 level
    }
```

## Scaling Guidelines

| Agent Count | Recommended Pattern | Levels | Monitoring |
|-------------|---------------------|--------|------------|
| 10-50 | Three-Level | 3 | Basic logging |
| 50-200 | Domain-Driven | 3-4 | Structured logs + metrics |
| 200-1000 | Domain-Driven or Matrix | 4 | Full observability stack |
| 1000+ | Event-Driven Mesh | 3-4 per domain | Distributed tracing |
