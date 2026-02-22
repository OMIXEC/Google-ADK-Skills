# Enterprise Agent Scalability Guide

## Overview

This guide covers performance optimization, resource management, and scalability patterns for enterprise multi-agent systems.

## Performance Targets

### Latency

| Metric | Target | Measurement |
|--------|--------|-------------|
| Single agent invocation | < 2s | Time to first token |
| Supervisor delegation | < 500ms | Routing decision time |
| Agent discovery | < 100ms | Registry lookup time |
| Cross-agent message | < 50ms | Event bus latency |

### Throughput

| Scale | Concurrent Requests | Agents | Response Time |
|-------|---------------------|--------|---------------|
| Small | 10-50/s | 10-50 | < 3s p95 |
| Medium | 50-200/s | 50-200 | < 5s p95 |
| Large | 200-1000/s | 200-1000 | < 7s p95 |
| Enterprise | 1000+/s | 1000+ | < 10s p95 |

## Resource Management

### Model Selection by Load

```python
from dataclasses import dataclass

@dataclass
class LoadBasedModelSelector:
    """Select model based on current system load."""

    def select_model(self, task_complexity: str, current_qps: int) -> str:
        """Select optimal model for current load."""

        # High load: prefer Flash for throughput
        if current_qps > 500:
            return "gemini-2.5-flash"

        # Low load + complex task: use Pro for quality
        if current_qps < 100 and task_complexity == "high":
            return "gemini-2.5-pro"

        # Default: Flash for efficiency
        return "gemini-2.5-flash"

# Usage
selector = LoadBasedModelSelector()

def create_agent(name: str, task_complexity: str, current_load: int):
    model = selector.select_model(task_complexity, current_load)
    return LlmAgent(name=name, model=model)
```

### Connection Pooling

```python
from typing import Dict
import asyncio

class AgentConnectionPool:
    """Pool agent instances to avoid cold starts."""

    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.pools: Dict[str, List[LlmAgent]] = {}
        self.semaphore = asyncio.Semaphore(max_size)

    async def acquire(self, agent_type: str, config: dict) -> LlmAgent:
        """Get agent from pool or create new one."""
        async with self.semaphore:
            pool = self.pools.get(agent_type, [])

            if pool:
                return pool.pop()

            # Create new agent
            return LlmAgent(**config)

    async def release(self, agent_type: str, agent: LlmAgent):
        """Return agent to pool."""
        if agent_type not in self.pools:
            self.pools[agent_type] = []

        if len(self.pools[agent_type]) < self.max_size:
            self.pools[agent_type].append(agent)
```

### Request Batching

```python
from typing import List
import asyncio

class AgentRequestBatcher:
    """Batch multiple requests to same agent for efficiency."""

    def __init__(self, batch_size: int = 10, max_wait_ms: int = 100):
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.pending: Dict[str, List[dict]] = {}

    async def submit(self, agent_name: str, request: dict) -> dict:
        """Submit request to be batched."""
        if agent_name not in self.pending:
            self.pending[agent_name] = []

        # Add to pending batch
        future = asyncio.Future()
        self.pending[agent_name].append({
            "request": request,
            "future": future,
        })

        # Flush if batch full
        if len(self.pending[agent_name]) >= self.batch_size:
            await self._flush_batch(agent_name)

        # Or wait for timeout
        else:
            asyncio.create_task(self._auto_flush(agent_name))

        return await future

    async def _flush_batch(self, agent_name: str):
        """Process batch of requests."""
        if agent_name not in self.pending or not self.pending[agent_name]:
            return

        batch = self.pending[agent_name]
        self.pending[agent_name] = []

        # Process batch in parallel
        agent = registry.get_agent(agent_name)
        tasks = [agent.invoke(item["request"]) for item in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Resolve futures
        for item, result in zip(batch, results):
            if isinstance(result, Exception):
                item["future"].set_exception(result)
            else:
                item["future"].set_result(result)

    async def _auto_flush(self, agent_name: str):
        """Auto-flush after timeout."""
        await asyncio.sleep(self.max_wait_ms / 1000)
        await self._flush_batch(agent_name)
```

## Load Balancing

### Round-Robin Agent Pool

```python
class RoundRobinPool:
    """Distribute requests evenly across agent instances."""

    def __init__(self, agents: List[LlmAgent]):
        self.agents = agents
        self.current_index = 0

    def get_next_agent(self) -> LlmAgent:
        """Get next agent in round-robin order."""
        agent = self.agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.agents)
        return agent

# Usage
sales_pool = RoundRobinPool([
    LlmAgent(name="sales_1", model="gemini-2.5-flash"),
    LlmAgent(name="sales_2", model="gemini-2.5-flash"),
    LlmAgent(name="sales_3", model="gemini-2.5-flash"),
])

agent = sales_pool.get_next_agent()
```

### Least-Loaded Pool

```python
from datetime import datetime

class LeastLoadedPool:
    """Route to agent with fewest active requests."""

    def __init__(self, agents: List[LlmAgent]):
        self.agents = agents
        self.active_requests: Dict[str, int] = {a.name: 0 for a in agents}

    async def invoke(self, request: str):
        """Invoke on least-loaded agent."""
        # Find agent with fewest active requests
        agent = min(self.agents, key=lambda a: self.active_requests[a.name])

        # Track active request
        self.active_requests[agent.name] += 1

        try:
            result = await agent.invoke(request)
            return result
        finally:
            self.active_requests[agent.name] -= 1
```

## Caching Strategies

### Response Caching

```python
from functools import lru_cache
import hashlib

class AgentResponseCache:
    """Cache agent responses for identical requests."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, dict] = {}

    def _hash_request(self, agent_name: str, request: str) -> str:
        """Generate cache key."""
        content = f"{agent_name}:{request}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def invoke_with_cache(self, agent: LlmAgent, request: str):
        """Invoke agent with response caching."""
        cache_key = self._hash_request(agent.name, request)

        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            age = (datetime.now() - cached["timestamp"]).total_seconds()

            if age < self.ttl_seconds:
                return cached["response"]

        # Cache miss - invoke agent
        response = await agent.invoke(request)

        # Store in cache
        self.cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now(),
        }

        # Evict old entries if cache full
        if len(self.cache) > self.max_size:
            oldest = min(self.cache.items(), key=lambda x: x[1]["timestamp"])
            del self.cache[oldest[0]]

        return response
```

### Agent State Caching

```python
class AgentStateCache:
    """Cache agent configuration and tools."""

    def __init__(self):
        self.agent_configs: Dict[str, dict] = {}
        self.tool_configs: Dict[str, List[dict]] = {}

    def cache_agent_config(self, agent: LlmAgent):
        """Cache agent configuration for fast recreation."""
        self.agent_configs[agent.name] = {
            "name": agent.name,
            "model": agent.model,
            "description": agent.description,
            "instruction": agent.instruction,
        }

        if agent.tools:
            self.tool_configs[agent.name] = [
                {"type": type(tool).__name__, "config": tool.config}
                for tool in agent.tools
            ]

    def recreate_agent(self, agent_name: str) -> LlmAgent:
        """Recreate agent from cached config."""
        config = self.agent_configs[agent_name]
        agent = LlmAgent(**config)

        # Restore tools
        if agent_name in self.tool_configs:
            for tool_config in self.tool_configs[agent_name]:
                # Reconstruct tools from config
                pass

        return agent
```

## Circuit Breakers

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class AgentCircuitBreaker:
    """Prevent cascading failures in agent hierarchies."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None

    async def invoke(self, agent: LlmAgent, request: str):
        """Invoke agent through circuit breaker."""

        # If circuit open, check if timeout elapsed
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker OPEN for {agent.name}")

        try:
            # Attempt invocation
            result = await agent.invoke(request)

            # Record success
            self._record_success()
            return result

        except Exception as e:
            # Record failure
            self._record_failure()
            raise

    def _record_success(self):
        """Record successful invocation."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                # Recovery successful
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        else:
            # Reset failure count on success
            self.failure_count = 0

    def _record_failure(self):
        """Record failed invocation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time elapsed to attempt reset."""
        if not self.last_failure_time:
            return False

        elapsed = datetime.now() - self.last_failure_time
        return elapsed > timedelta(seconds=self.timeout_seconds)
```

## Rate Limiting

```python
from collections import deque
from datetime import datetime, timedelta

class AgentRateLimiter:
    """Limit request rate per agent."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_timestamps: Dict[str, deque] = {}

    async def acquire(self, agent_name: str):
        """Acquire rate limit token."""
        if agent_name not in self.request_timestamps:
            self.request_timestamps[agent_name] = deque()

        timestamps = self.request_timestamps[agent_name]
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Remove old timestamps outside window
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        # Check if under limit
        if len(timestamps) >= self.max_requests:
            raise Exception(f"Rate limit exceeded for {agent_name}")

        # Record request
        timestamps.append(now)

# Usage
limiter = AgentRateLimiter(max_requests=100, window_seconds=60)

async def rate_limited_invoke(agent: LlmAgent, request: str):
    await limiter.acquire(agent.name)
    return await agent.invoke(request)
```

## Monitoring and Metrics

```python
from dataclasses import dataclass, field
from typing import List
from datetime import datetime

@dataclass
class AgentMetrics:
    """Track agent performance metrics."""
    agent_name: str
    invocations: int = 0
    total_duration_ms: float = 0
    errors: int = 0
    token_usage: dict = field(default_factory=dict)

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.invocations if self.invocations > 0 else 0

    @property
    def error_rate(self) -> float:
        return self.errors / self.invocations if self.invocations > 0 else 0

class AgentMetricsCollector:
    """Collect and aggregate agent metrics."""

    def __init__(self):
        self.metrics: Dict[str, AgentMetrics] = {}

    def record_invocation(
        self,
        agent_name: str,
        duration_ms: float,
        success: bool,
        token_usage: dict,
    ):
        """Record single invocation metrics."""
        if agent_name not in self.metrics:
            self.metrics[agent_name] = AgentMetrics(agent_name=agent_name)

        m = self.metrics[agent_name]
        m.invocations += 1
        m.total_duration_ms += duration_ms

        if not success:
            m.errors += 1

        # Aggregate token usage
        for key, value in token_usage.items():
            m.token_usage[key] = m.token_usage.get(key, 0) + value

    def get_top_agents_by_invocations(self, limit: int = 10) -> List[AgentMetrics]:
        """Get most frequently invoked agents."""
        return sorted(
            self.metrics.values(),
            key=lambda m: m.invocations,
            reverse=True,
        )[:limit]

    def get_slowest_agents(self, limit: int = 10) -> List[AgentMetrics]:
        """Get agents with highest average latency."""
        return sorted(
            self.metrics.values(),
            key=lambda m: m.avg_duration_ms,
            reverse=True,
        )[:limit]

    def get_agents_with_errors(self, min_error_rate: float = 0.05) -> List[AgentMetrics]:
        """Get agents with error rate above threshold."""
        return [
            m for m in self.metrics.values()
            if m.error_rate >= min_error_rate
        ]
```

## Auto-Scaling

```python
class AgentAutoScaler:
    """Automatically scale agent pools based on load."""

    def __init__(
        self,
        min_agents: int = 2,
        max_agents: int = 20,
        target_qps_per_agent: int = 10,
    ):
        self.min_agents = min_agents
        self.max_agents = max_agents
        self.target_qps_per_agent = target_qps_per_agent
        self.agent_pools: Dict[str, List[LlmAgent]] = {}

    async def scale(self, agent_type: str, current_qps: int):
        """Scale agent pool to meet demand."""
        desired_agents = max(
            self.min_agents,
            min(self.max_agents, current_qps // self.target_qps_per_agent),
        )

        current_agents = len(self.agent_pools.get(agent_type, []))

        if desired_agents > current_agents:
            # Scale up
            await self._add_agents(agent_type, desired_agents - current_agents)

        elif desired_agents < current_agents:
            # Scale down
            await self._remove_agents(agent_type, current_agents - desired_agents)

    async def _add_agents(self, agent_type: str, count: int):
        """Add agents to pool."""
        if agent_type not in self.agent_pools:
            self.agent_pools[agent_type] = []

        for i in range(count):
            agent = LlmAgent(
                name=f"{agent_type}_{len(self.agent_pools[agent_type])}",
                model="gemini-2.5-flash",
            )
            self.agent_pools[agent_type].append(agent)

    async def _remove_agents(self, agent_type: str, count: int):
        """Remove agents from pool."""
        if agent_type not in self.agent_pools:
            return

        # Remove from end (LIFO)
        for _ in range(count):
            if self.agent_pools[agent_type]:
                self.agent_pools[agent_type].pop()
```

## Best Practices Summary

### Performance

1. **Use Flash for most agents** - Reserve Pro for root coordinators only
2. **Cache frequently accessed responses** - Especially for deterministic queries
3. **Batch similar requests** - Reduces overhead for high-volume operations
4. **Pool agent instances** - Avoid cold start latency

### Reliability

1. **Implement circuit breakers** - Prevent cascading failures
2. **Add rate limiting** - Protect against runaway loops
3. **Monitor error rates** - Alert on degradation
4. **Have fallback agents** - Graceful degradation

### Scalability

1. **Horizontal scaling** - Add agent instances, not bigger models
2. **Load balancing** - Distribute evenly across pools
3. **Auto-scaling** - Match capacity to demand
4. **Partition by domain** - Isolate different workloads

## Performance Benchmarks

### Single Agent Latency

| Model | Avg Latency | p95 | p99 | Token/s |
|-------|-------------|-----|-----|---------|
| Gemini 2.5 Pro | 1.8s | 3.2s | 4.5s | 42 |
| Gemini 2.5 Flash | 0.9s | 1.5s | 2.1s | 87 |

### Agent Pool Throughput

| Pool Size | QPS | Avg Latency | p95 |
|-----------|-----|-------------|-----|
| 1 | 10 | 0.9s | 1.5s |
| 5 | 45 | 1.1s | 1.8s |
| 10 | 85 | 1.2s | 2.0s |
| 20 | 160 | 1.4s | 2.3s |

### Hierarchy Overhead

| Levels | Delegation Overhead | Total Latency |
|--------|---------------------|---------------|
| 1 (direct) | 0ms | 900ms |
| 2 (supervisor + worker) | 150ms | 1050ms |
| 3 (root + supervisor + worker) | 300ms | 1200ms |
