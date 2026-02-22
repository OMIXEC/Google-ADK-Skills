# Agent Registry Pattern

## Overview

The Agent Registry pattern provides centralized agent discovery, lifecycle management, and coordination for enterprise multi-agent systems.

## Core Responsibilities

1. **Discovery:** Find agents by name, domain, or capability
2. **Lifecycle:** Register, activate, deactivate, and unregister agents
3. **Metadata:** Track agent capabilities, status, and dependencies
4. **Health:** Monitor agent health and availability
5. **Routing:** Route requests to appropriate agents

## Basic Implementation

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
from google.adk.agents import LlmAgent
from enum import Enum

class AgentStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    FAILED = "failed"

@dataclass
class AgentMetadata:
    """Metadata about a registered agent."""
    name: str
    domain: str
    capabilities: Set[str]
    tags: Set[str]
    status: AgentStatus
    registered_at: datetime
    last_health_check: Optional[datetime] = None
    invocation_count: int = 0
    error_count: int = 0

    @property
    def error_rate(self) -> float:
        if self.invocation_count == 0:
            return 0.0
        return self.error_count / self.invocation_count

@dataclass
class AgentRegistry:
    """Central registry for agent discovery and management."""
    agents: Dict[str, LlmAgent] = field(default_factory=dict)
    metadata: Dict[str, AgentMetadata] = field(default_factory=dict)
    domain_index: Dict[str, Set[str]] = field(default_factory=dict)
    capability_index: Dict[str, Set[str]] = field(default_factory=dict)

    def register(
        self,
        agent: LlmAgent,
        domain: str,
        capabilities: List[str],
        tags: Optional[List[str]] = None,
    ) -> None:
        """Register an agent with the registry."""
        tags = tags or []

        # Store agent
        self.agents[agent.name] = agent

        # Create metadata
        self.metadata[agent.name] = AgentMetadata(
            name=agent.name,
            domain=domain,
            capabilities=set(capabilities),
            tags=set(tags),
            status=AgentStatus.ACTIVE,
            registered_at=datetime.now(),
        )

        # Update domain index
        if domain not in self.domain_index:
            self.domain_index[domain] = set()
        self.domain_index[domain].add(agent.name)

        # Update capability index
        for capability in capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = set()
            self.capability_index[capability].add(agent.name)

    def unregister(self, agent_name: str) -> None:
        """Remove agent from registry."""
        if agent_name not in self.agents:
            return

        # Get metadata for cleanup
        meta = self.metadata[agent_name]

        # Remove from domain index
        if meta.domain in self.domain_index:
            self.domain_index[meta.domain].discard(agent_name)

        # Remove from capability index
        for capability in meta.capabilities:
            if capability in self.capability_index:
                self.capability_index[capability].discard(agent_name)

        # Remove agent and metadata
        del self.agents[agent_name]
        del self.metadata[agent_name]

    def get_agent(self, name: str) -> Optional[LlmAgent]:
        """Get agent by name."""
        return self.agents.get(name)

    def get_domain_agents(self, domain: str) -> List[LlmAgent]:
        """Get all agents in a domain."""
        agent_names = self.domain_index.get(domain, set())
        return [self.agents[name] for name in agent_names if name in self.agents]

    def find_by_capability(self, capability: str) -> List[LlmAgent]:
        """Find agents with specific capability."""
        agent_names = self.capability_index.get(capability, set())
        return [self.agents[name] for name in agent_names if name in self.agents]

    def find_by_tag(self, tag: str) -> List[LlmAgent]:
        """Find agents with specific tag."""
        matching = [
            self.agents[name]
            for name, meta in self.metadata.items()
            if tag in meta.tags and name in self.agents
        ]
        return matching

    def get_active_agents(self) -> List[LlmAgent]:
        """Get all active agents."""
        active_names = [
            name for name, meta in self.metadata.items()
            if meta.status == AgentStatus.ACTIVE
        ]
        return [self.agents[name] for name in active_names if name in self.agents]

    def update_status(self, agent_name: str, status: AgentStatus) -> None:
        """Update agent status."""
        if agent_name in self.metadata:
            self.metadata[agent_name].status = status

    def record_invocation(self, agent_name: str, success: bool) -> None:
        """Record agent invocation for metrics."""
        if agent_name not in self.metadata:
            return

        meta = self.metadata[agent_name]
        meta.invocation_count += 1

        if not success:
            meta.error_count += 1

            # Auto-degrade if error rate too high
            if meta.error_rate > 0.1:  # 10% error rate
                meta.status = AgentStatus.DEGRADED

    def get_metadata(self, agent_name: str) -> Optional[AgentMetadata]:
        """Get agent metadata."""
        return self.metadata.get(agent_name)

    def list_all(self) -> List[AgentMetadata]:
        """List all registered agents with metadata."""
        return list(self.metadata.values())
```

## Usage Examples

### Basic Registration

```python
# Create registry
registry = AgentRegistry()

# Create agents
sales_agent = LlmAgent(
    name="sales_specialist",
    model="gemini-2.5-flash",
    description="Handles sales inquiries",
)

support_agent = LlmAgent(
    name="support_specialist",
    model="gemini-2.5-flash",
    description="Resolves support tickets",
)

# Register agents
registry.register(
    agent=sales_agent,
    domain="customer_operations",
    capabilities=["lead_qualification", "pricing_quotes"],
    tags=["customer_facing", "revenue"],
)

registry.register(
    agent=support_agent,
    domain="customer_operations",
    capabilities=["ticket_resolution", "troubleshooting"],
    tags=["customer_facing", "support"],
)
```

### Discovery Patterns

```python
# Find by domain
customer_agents = registry.get_domain_agents("customer_operations")
# Returns: [sales_agent, support_agent]

# Find by capability
quote_agents = registry.find_by_capability("pricing_quotes")
# Returns: [sales_agent]

# Find by tag
customer_facing = registry.find_by_tag("customer_facing")
# Returns: [sales_agent, support_agent]

# Get specific agent
agent = registry.get_agent("sales_specialist")
```

### Health Monitoring

```python
import asyncio

class AgentHealthMonitor:
    """Monitor agent health in registry."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    async def check_agent_health(self, agent_name: str) -> bool:
        """Check if agent is healthy."""
        agent = self.registry.get_agent(agent_name)
        if not agent:
            return False

        try:
            # Simple health check - try to invoke with test request
            result = await agent.invoke("health check")
            self.registry.update_status(agent_name, AgentStatus.ACTIVE)
            return True

        except Exception:
            self.registry.update_status(agent_name, AgentStatus.FAILED)
            return False

    async def check_all_agents(self) -> Dict[str, bool]:
        """Check health of all registered agents."""
        results = {}

        for agent_name in self.registry.agents.keys():
            results[agent_name] = await self.check_agent_health(agent_name)

        return results

# Usage
monitor = AgentHealthMonitor(registry)
health_results = await monitor.check_all_agents()
```

### Dynamic Routing

```python
class AgentRouter:
    """Route requests to best available agent."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    async def route_by_capability(
        self,
        capability: str,
        request: str,
    ) -> Optional[dict]:
        """Route request to agent with capability."""

        # Find agents with capability
        candidates = self.registry.find_by_capability(capability)

        # Filter to active agents
        active = [
            a for a in candidates
            if self.registry.get_metadata(a.name).status == AgentStatus.ACTIVE
        ]

        if not active:
            return None

        # Select agent with lowest error rate
        best_agent = min(
            active,
            key=lambda a: self.registry.get_metadata(a.name).error_rate
        )

        # Invoke and record result
        try:
            result = await best_agent.invoke(request)
            self.registry.record_invocation(best_agent.name, success=True)
            return {"agent": best_agent.name, "result": result}

        except Exception as e:
            self.registry.record_invocation(best_agent.name, success=False)
            raise

# Usage
router = AgentRouter(registry)
result = await router.route_by_capability("pricing_quotes", "Quote for 100 licenses")
```

## Advanced Features

### Dependency Management

```python
@dataclass
class AgentRegistryWithDependencies(AgentRegistry):
    """Registry with dependency tracking."""
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)

    def register_with_dependencies(
        self,
        agent: LlmAgent,
        domain: str,
        capabilities: List[str],
        depends_on: Optional[List[str]] = None,
    ):
        """Register agent with dependencies."""
        # Basic registration
        self.register(agent, domain, capabilities)

        # Track dependencies
        if depends_on:
            self.dependencies[agent.name] = set(depends_on)

    def get_dependencies(self, agent_name: str) -> Set[str]:
        """Get agent dependencies."""
        return self.dependencies.get(agent_name, set())

    def get_dependents(self, agent_name: str) -> Set[str]:
        """Get agents that depend on this agent."""
        dependents = set()
        for name, deps in self.dependencies.items():
            if agent_name in deps:
                dependents.add(name)
        return dependents

    def can_unregister(self, agent_name: str) -> bool:
        """Check if agent can be safely unregistered."""
        # Agent can be unregistered if no active agents depend on it
        dependents = self.get_dependents(agent_name)

        for dependent in dependents:
            meta = self.metadata.get(dependent)
            if meta and meta.status == AgentStatus.ACTIVE:
                return False

        return True

# Usage
registry = AgentRegistryWithDependencies()

registry.register_with_dependencies(
    agent=order_processor,
    domain="orders",
    capabilities=["process_order"],
    depends_on=["payment_validator", "inventory_checker"],
)
```

### Version Management

```python
from typing import Dict, List

@dataclass
class VersionedAgent:
    """Agent with version information."""
    agent: LlmAgent
    version: str
    deprecated: bool = False
    successor: Optional[str] = None

class VersionedAgentRegistry:
    """Registry supporting multiple agent versions."""

    def __init__(self):
        self.agents: Dict[str, Dict[str, VersionedAgent]] = {}
        self.default_versions: Dict[str, str] = {}

    def register_version(
        self,
        agent: LlmAgent,
        version: str,
        is_default: bool = False,
    ):
        """Register specific version of agent."""
        if agent.name not in self.agents:
            self.agents[agent.name] = {}

        self.agents[agent.name][version] = VersionedAgent(
            agent=agent,
            version=version,
        )

        if is_default or len(self.agents[agent.name]) == 1:
            self.default_versions[agent.name] = version

    def get_agent(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional[LlmAgent]:
        """Get agent, optionally by version."""
        if name not in self.agents:
            return None

        # Use default version if not specified
        if version is None:
            version = self.default_versions.get(name)
            if version is None:
                return None

        versioned = self.agents[name].get(version)
        return versioned.agent if versioned else None

    def deprecate_version(
        self,
        name: str,
        version: str,
        successor_version: str,
    ):
        """Mark version as deprecated."""
        if name in self.agents and version in self.agents[name]:
            self.agents[name][version].deprecated = True
            self.agents[name][version].successor = successor_version

# Usage
versioned_registry = VersionedAgentRegistry()

# Register v1
sales_v1 = LlmAgent(name="sales_agent", model="gemini-2.5-flash")
versioned_registry.register_version(sales_v1, version="1.0", is_default=True)

# Register v2
sales_v2 = LlmAgent(name="sales_agent", model="gemini-2.5-pro")
versioned_registry.register_version(sales_v2, version="2.0", is_default=True)

# Deprecate v1
versioned_registry.deprecate_version("sales_agent", "1.0", successor_version="2.0")

# Get agents
agent_default = versioned_registry.get_agent("sales_agent")  # Returns v2
agent_v1 = versioned_registry.get_agent("sales_agent", version="1.0")  # Returns v1
```

## Integration with Agent Hierarchy

```python
class HierarchicalAgentRegistry(AgentRegistry):
    """Registry with hierarchy support."""

    def __init__(self):
        super().__init__()
        self.parent_child_map: Dict[str, Set[str]] = {}

    def register_with_parent(
        self,
        agent: LlmAgent,
        domain: str,
        capabilities: List[str],
        parent: Optional[str] = None,
    ):
        """Register agent with parent relationship."""
        self.register(agent, domain, capabilities)

        if parent:
            if parent not in self.parent_child_map:
                self.parent_child_map[parent] = set()
            self.parent_child_map[parent].add(agent.name)

    def get_children(self, agent_name: str) -> List[LlmAgent]:
        """Get child agents."""
        child_names = self.parent_child_map.get(agent_name, set())
        return [self.agents[name] for name in child_names if name in self.agents]

    def get_hierarchy(self, root_name: str) -> dict:
        """Get complete hierarchy from root."""
        def build_tree(name: str) -> dict:
            children = self.get_children(name)
            return {
                "name": name,
                "agent": self.get_agent(name),
                "metadata": self.get_metadata(name),
                "children": [build_tree(child.name) for child in children],
            }

        return build_tree(root_name)

# Usage
registry = HierarchicalAgentRegistry()

# Register hierarchy
registry.register_with_parent(
    agent=executive_coordinator,
    domain="enterprise",
    capabilities=["coordinate"],
)

registry.register_with_parent(
    agent=sales_supervisor,
    domain="sales",
    capabilities=["supervise_sales"],
    parent="executive_coordinator",
)

registry.register_with_parent(
    agent=sales_specialist,
    domain="sales",
    capabilities=["handle_sales_inquiry"],
    parent="sales_supervisor",
)

# Get hierarchy
hierarchy = registry.get_hierarchy("executive_coordinator")
```

## Best Practices

### 1. Naming Conventions

```python
# Use descriptive, hierarchical names
"enterprise.sales.lead_qualifier"
"enterprise.sales.quote_generator"
"enterprise.support.ticket_resolver"
```

### 2. Capability Granularity

```python
# Too broad
capabilities=["sales"]  # Not useful for routing

# Too specific
capabilities=["generate_quote_for_enterprise_saas_annual_subscription"]  # Too narrow

# Just right
capabilities=["lead_qualification", "pricing_quotes", "contract_generation"]
```

### 3. Health Check Frequency

```python
# Check frequently used agents more often
async def adaptive_health_check(registry: AgentRegistry):
    for agent_name, meta in registry.metadata.items():
        # High traffic agents: check every 30s
        if meta.invocation_count > 1000:
            interval = 30

        # Medium traffic: check every 5 min
        elif meta.invocation_count > 100:
            interval = 300

        # Low traffic: check every 30 min
        else:
            interval = 1800

        # Schedule health check
        await asyncio.sleep(interval)
        await monitor.check_agent_health(agent_name)
```

### 4. Graceful Degradation

```python
# Fallback to similar agents if primary unavailable
async def invoke_with_fallback(
    registry: AgentRegistry,
    primary_agent: str,
    request: str,
):
    # Try primary agent
    agent = registry.get_agent(primary_agent)
    if agent and registry.get_metadata(primary_agent).status == AgentStatus.ACTIVE:
        return await agent.invoke(request)

    # Fall back to agents with same capabilities
    meta = registry.get_metadata(primary_agent)
    for capability in meta.capabilities:
        candidates = registry.find_by_capability(capability)
        for candidate in candidates:
            if candidate.name != primary_agent:
                return await candidate.invoke(request)

    raise Exception(f"No available agents for request")
```

## Testing

```python
import pytest

@pytest.fixture
def registry():
    return AgentRegistry()

def test_register_and_discover(registry):
    """Test basic registration and discovery."""
    agent = LlmAgent(name="test_agent", model="gemini-2.5-flash")

    registry.register(
        agent=agent,
        domain="test",
        capabilities=["test_capability"],
        tags=["test_tag"],
    )

    # Test discovery methods
    assert registry.get_agent("test_agent") == agent
    assert agent in registry.get_domain_agents("test")
    assert agent in registry.find_by_capability("test_capability")
    assert agent in registry.find_by_tag("test_tag")

def test_status_tracking(registry):
    """Test agent status updates."""
    agent = LlmAgent(name="status_test", model="gemini-2.5-flash")
    registry.register(agent, "test", ["test"])

    # Initial status
    assert registry.get_metadata("status_test").status == AgentStatus.ACTIVE

    # Update status
    registry.update_status("status_test", AgentStatus.DEGRADED)
    assert registry.get_metadata("status_test").status == AgentStatus.DEGRADED

def test_error_rate_tracking(registry):
    """Test error rate calculation."""
    agent = LlmAgent(name="error_test", model="gemini-2.5-flash")
    registry.register(agent, "test", ["test"])

    # Record invocations
    for _ in range(90):
        registry.record_invocation("error_test", success=True)
    for _ in range(10):
        registry.record_invocation("error_test", success=False)

    meta = registry.get_metadata("error_test")
    assert meta.invocation_count == 100
    assert meta.error_count == 10
    assert meta.error_rate == 0.1
```
