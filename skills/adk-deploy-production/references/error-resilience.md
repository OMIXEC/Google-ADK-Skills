# Error Handling & Resilience for ADK Workflows

Production workflows fail. Agents time out, tools error, networks partition. This reference covers patterns for handling failure gracefully at every level.

## Error Taxonomy

| Category | Examples | Strategy |
|----------|----------|----------|
| **Transient** | Network timeout, rate limit, 503 | Retry with backoff |
| **Permanent** | Invalid input, 400, auth failure | Fail fast, surface to user |
| **Partial** | One sub-agent failed, others OK | Degrade gracefully |
| **System** | OOM, process crash, infra | Restart, checkpoint resume |

## Per-Agent Error Handling

### Timeout configuration

```python
"""Per-agent timeout — prevent hung agents from blocking workflow."""
import asyncio

async def run_agent_with_timeout(agent, session_id, user_id, message, timeout_s: float = 30.0):
    try:
        events = []
        async with asyncio.timeout(timeout_s):
            async for event in runner.run_async(
                session_id=session_id,
                user_id=user_id,
                new_message=message,
            ):
                events.append(event)
        return events
    except asyncio.TimeoutError:
        return [create_error_event(
            error="Agent timed out",
            agent=agent.name,
            timeout_s=timeout_s,
        )]
```

### Tool-level retry with backoff

```python
"""Retry failed tool calls with exponential backoff + jitter."""
import random
import asyncio
from functools import wraps

def retry_with_backoff(
    max_retries: int = 3,
    base_delay_s: float = 1.0,
    max_delay_s: float = 30.0,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError, OSError),
):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return await fn(*args, **kwargs)
                except retryable_exceptions as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = min(base_delay_s * (2 ** attempt), max_delay_s)
                        jitter = random.uniform(0, delay * 0.1)
                        await asyncio.sleep(delay + jitter)
            raise last_error
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3, base_delay_s=1.0)
async def call_external_api(url: str, payload: dict) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
```

## Circuit Breaker

```python
"""Circuit breaker: stop calling failing dependency, recover after cooldown."""
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"           # Normal operation
    OPEN = "open"               # Failing, reject calls
    HALF_OPEN = "half_open"     # Testing if recovered

class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_s: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.half_open_calls = 0

    async def call(self, fn, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout_s:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit {self.name} is OPEN. "
                    f"Retry in {self.recovery_timeout_s - (time.time() - self.last_failure_time):.0f}s"
                )

        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls > self.half_open_max_calls:
                raise CircuitBreakerOpenError(f"Circuit {self.name} — too many half-open calls")

        try:
            result = await fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class CircuitBreakerOpenError(Exception):
    pass
```

## Dead-Letter Queue

```python
"""DLQ: persist failed agent outputs for later inspection and replay."""
import json
from datetime import datetime

class DeadLetterQueue:
    def __init__(self, store):  # store = any DB from database-integration.md
        self.store = store

    async def enqueue(
        self,
        agent_name: str,
        session_id: str,
        input_data: dict,
        error: str,
        error_type: str,
    ) -> str:
        """Send failed output to DLQ for later analysis."""
        entry = {
            "agent_name": agent_name,
            "session_id": session_id,
            "input": input_data,
            "error": error,
            "error_type": error_type,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_count": 0,
            "status": "pending",
        }
        entry_id = await self.store.insert("dead_letter_queue", entry)
        return entry_id

    async def replay(self, entry_id: str) -> dict:
        """Retry a failed message."""
        entry = await self.store.get("dead_letter_queue", entry_id)
        entry["retry_count"] += 1
        await self.store.update("dead_letter_queue", entry_id, entry)
        return entry

    async def purge(self, older_than_days: int = 30):
        """Clean up old DLQ entries."""
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        await self.store.delete_where(
            "dead_letter_queue",
            "timestamp < %s AND status = 'resolved'",
            (cutoff.isoformat(),),
        )
```

## Graceful Degradation

```python
"""Fallback when primary agent fails — return degraded but useful response."""
from enum import Enum

class DegradationLevel(Enum):
    FULL = "full"           # All agents healthy
    PARTIAL = "partial"     # Some agents down, others working
    MINIMAL = "minimal"     # Only fallback available
    UNAVAILABLE = "down"    # Nothing works

class DegradedWorkflow:
    def __init__(self):
        self.agent_health: dict[str, bool] = {}

    async def run_with_degradation(self, agents: dict, input_data: dict) -> dict:
        """Run agents in priority order. Stop when one succeeds."""
        for name, agent in agents.items():
            if not self.agent_health.get(name, True):
                continue
            try:
                return await self._run_single(agent, input_data)
            except Exception as e:
                self.agent_health[name] = False
                # Log failure but continue to next agent
                continue

        # Ultimate fallback — static response
        return {"status": "degraded", "message": "All agents unavailable. Try again later."}

    async def _run_single(self, agent, input_data) -> dict:
        async with asyncio.timeout(10.0):
            result = await agent.run(input_data)
            return result

# Usage: primary LLM agent → fallback to cached agent → fallback to static
workflow = DegradedWorkflow()
result = await workflow.run_with_degradation(
    agents={
        "primary_llm": llm_agent,
        "cached_responses": cache_agent,
        "static_fallback": static_responder,
    },
    input_data={"query": "..."},
)
```

## Error Propagation Across Agent Boundaries

```python
"""Standard error envelope for cross-agent communication."""

from pydantic import BaseModel

class AgentError(BaseModel):
    agent_name: str
    error_type: str  # timeout, tool_failure, invalid_input, model_error
    message: str
    retryable: bool
    details: dict = {}

async def handle_agent_error(error: AgentError, workflow_state: dict):
    """Central error handler — decide: retry, skip, fail, or degrade."""
    if error.retryable and workflow_state.get("retry_count", 0) < 3:
        workflow_state["retry_count"] = workflow_state.get("retry_count", 0) + 1
        return "retry"
    elif error.error_type == "timeout":
        return "degrade"  # Use fallback agent
    elif error.error_type == "tool_failure":
        return "skip"  # Skip this agent, continue workflow
    else:
        return "fail"  # Surface to user
```

## Workflow-Level Timeout & SLA

```python
"""Workflow-level SLA enforcement."""
import time

class WorkflowSLA:
    def __init__(self, max_duration_s: float = 300.0, per_agent_timeout_s: float = 60.0):
        self.max_duration_s = max_duration_s
        self.per_agent_timeout_s = per_agent_timeout_s
        self.start_time = time.monotonic()
        self.agent_timings: dict[str, float] = {}

    def check_elapsed(self) -> bool:
        """Returns True if still within SLA."""
        return (time.monotonic() - self.start_time) < self.max_duration_s

    def remaining_budget(self) -> float:
        """Seconds remaining in workflow SLA."""
        return max(0, self.max_duration_s - (time.monotonic() - self.start_time))

    def record_agent(self, name: str, duration_s: float):
        self.agent_timings[name] = duration_s

    def report(self) -> dict:
        return {
            "total_elapsed_s": time.monotonic() - self.start_time,
            "within_sla": self.check_elapsed(),
            "agent_timings": self.agent_timings,
        }

# Usage
sla = WorkflowSLA(max_duration_s=120.0, per_agent_timeout_s=30.0)
for agent in workflow_agents:
    if not sla.check_elapsed():
        raise WorkflowSLAExceededError(f"SLA exceeded after {sla.report()['total_elapsed_s']:.1f}s")
    t0 = time.monotonic()
    await run_agent(agent)
    sla.record_agent(agent.name, time.monotonic() - t0)
```

## Observability Integration

```python
"""Structured error logging with correlation IDs."""
import logging
import uuid

logger = logging.getLogger("adk.workflow.errors")

def log_error(
    error: Exception,
    agent_name: str,
    correlation_id: str,
    session_id: str,
    extra: dict = {},
):
    logger.error(
        json.dumps({
            "event": "agent_error",
            "correlation_id": correlation_id,
            "session_id": session_id,
            "agent": agent_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "retryable": isinstance(error, (ConnectionError, TimeoutError)),
            **extra,
        })
    )
```

## Production Checklist

- [ ] Every external tool call has timeout + retry
- [ ] Circuit breaker on all external service calls
- [ ] DLQ for failed agent outputs (debug replay capability)
- [ ] Graceful degradation: fallback agents for critical paths
- [ ] Workflow-level SLA with timeout enforcement
- [ ] Error taxonomy applied consistently (transient/retry, permanent/fail)
- [ ] Correlation IDs propagated across all agents and tools
- [ ] Structured error logs with all context fields
- [ ] Alert thresholds: >5% error rate, >3 circuit breaks, >0 DLQ growth
- [ ] Error budget tracking per SLO period
