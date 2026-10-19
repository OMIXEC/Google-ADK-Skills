# Deployment Sizing

Sizing starts from one measured number: **concurrent turns per instance at p95
latency**. Everything else is arithmetic. This file covers the host, not the
agent; the deploy commands and manifests live in `adk-deployment`.

## The formula

```
instances = ceil(peak_concurrent_turns / measured_turns_per_instance)
```

Measure `turns_per_instance` with the load test below. If you have not
measured it, you do not have a size — you have a guess that autoscaling will
discover at the worst moment.

## Session service decides whether you can scale horizontally

| Session service | Multi-instance safe | Notes |
|---|---|---|
| `InMemorySessionService` | **No** | State disappears on restart and is not shared between instances |
| `DatabaseSessionService` | Yes | SQLAlchemy async URL; size the pool to concurrency |
| `SqliteSessionService` | **No** | Single file; dev and single-node only |
| `FirestoreSessionService` | Yes | `google.adk.integrations.firestore` |
| `VertexAiSessionService` | Yes | Managed sessions for Agent Engine deployments |

Choosing an in-memory service and then scaling to two instances is the most
common production failure in this area: turns work, then silently lose
context.

## Cloud Run

Levers, in order of effect:

| Lever | What it changes |
|---|---|
| Concurrency per instance | In-flight requests one instance accepts |
| Min instances | Cold-start tail at the cost of idle billing |
| CPU always allocated | Decode-heavy agents; request-based CPU throttles between responses |
| Request timeout | Long agent turns; raise it above your p99 |
| Max instances | Caps spend and protects model quota |

Rules of thumb:

- Set concurrency from the load test, not from the platform default. An agent
  turn holds a connection for seconds, unlike a static HTTP handler.
- Keep max instances × concurrency below your model quota, or autoscaling will
  convert a queue into 429s.
- If the service is CPU-throttled during streaming, allocate CPU always.

## GKE

| Lever | What it changes |
|---|---|
| Replicas / HPA | Horizontal scale on concurrency or in-flight requests |
| CPU and memory requests | Scheduling and throttling |
| Startup probe | Time for imports and client init before traffic |
| Pod disruption budget | Availability during node rotation |

Scale on concurrency, not CPU: agent pods are usually waiting on a model, not
burning cores. A CPU-target HPA will under-provision exactly when latency
matters.

## Vertex AI Agent Engine

Managed runtime. You choose the agent and the session/memory services; Google
chooses the machines.

- Prefer `VertexAiSessionService` and `VertexAiMemoryBankService`.
- `RunConfig(service_tier=ServiceTier.DEFERRED)` lets long agent work survive a
  client disconnect on Agent Engine — the managed runtime continues the turn.
- Cold start is shorter than self-managed containers, but still non-zero; warm
  with a health check that exercises one trivial turn.

## Cold start

Three things dominate startup:

1. **Imports.** Importing heavy optional integrations at module scope adds
   seconds. Import inside the tool or integration that needs them.
2. **Client construction.** Build the model client once at module scope, not
   per request.
3. **Session backend connection.** Establish the pool in the app lifespan, and
   fail readiness until it succeeds.

## Load test

Test the HTTP surface, not the Python API, so the result includes your
deployment:

```python
# locustfile.py
import json
import os

from locust import HttpUser, between, task


class AgentUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def turn(self):
        self.client.post(
            "/run",
            data=json.dumps(
                {
                    "query": "Summarize the account status",
                    "user_id": os.environ.get("LOAD_USER", "load-test"),
                }
            ),
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
```

Watch three numbers, not one:

| Metric | Meaning | Acceptable |
|---|---|---|
| p95 end-to-end | Includes queue and model | Your product target |
| Error rate | 429/5xx/timeouts | < 1% steady state |
| Tokens per second per instance | Cost per instance at load | Stable as load rises |

If throughput rises while p95 stays flat, add instances. If p95 rises with
throughput, you are saturated at a shared resource: model quota, DB pool, or
CPU.

## Checklist

- [ ] `turns_per_instance` measured at target p95
- [ ] Session service is multi-instance safe
- [ ] `max_instances × concurrency` is below model quota
- [ ] CPU allocation matches the streaming profile
- [ ] Readiness fails until the session backend is connected
- [ ] Retry policy is set and tools are idempotent
- [ ] Load test runs against the deployed HTTP surface
- [ ] Cost per 1,000 turns is recorded and tracked over releases
