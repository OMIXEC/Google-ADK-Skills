# A2A Deep-Dive for ADK Workflows

A2A (Agent-to-Agent) is the protocol for agents to communicate with other agents across process and language boundaries. ADK provides `RemoteA2AAgent` for clients and `AgentCard` for servers.

## Architecture

```
┌──────────────────┐                              ┌──────────────────┐
│  ADK Agent        │   A2A Protocol (SSE/HTTP)    │  Remote A2A Agent │
│  (Python)         │ ◄──────────────────────────► │  (Go/TS)          │
│  RemoteA2AAgent   │   AgentCard discovery        │  AgentCard        │
│                   │   Streaming events           │  /a2a endpoint    │
└──────────────────┘                              └──────────────────┘
```

## AgentCard — Exposing Your Agent

`AgentCard` is required for A2A. It describes the agent's capabilities, endpoint, and auth requirements.

### Python

```python
from google.adk.a2a import AgentCard

agent_card = AgentCard(
    name="prime_checker_agent",
    description="Checks whether a number is prime",
    url="https://my-agent-service.a.run.app/a2a/check_prime_agent",
    capabilities={
        "streaming": False,
        "push_notifications": False,
    },
    auth_scheme={
        "type": "bearer",
        "description": "GCP identity token for service-to-service auth",
    },
    version="1.0.0",
)
```

### Go

```go
import "google.golang.org/adk/a2a"

card := &a2a.AgentCard{
    Name:        "prime_checker_agent",
    Description: "Checks whether a number is prime",
    URL:         "https://my-agent-service.a.run.app/a2a/check_prime_agent",
    Capabilities: a2a.Capabilities{
        Streaming: false,
    },
    Version: "1.0.0",
}
```

### TypeScript

```typescript
import { AgentCard } from "@google/adk/a2a";

const card: AgentCard = {
  name: "prime_checker_agent",
  description: "Checks whether a number is prime",
  url: "https://my-agent-service.a.run.app/a2a/check_prime_agent",
  capabilities: { streaming: false },
  version: "1.0.0",
};
```

### AgentCard Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique agent name |
| `description` | Yes | What the agent does |
| `url` | Yes | RPC endpoint URL |
| `capabilities` | Yes | `streaming`, `push_notifications` |
| `auth_scheme` | No | Auth type and description |
| `version` | No | Semantic version |
| `docs_url` | No | Link to documentation |
| `examples` | No | Example queries and responses |

## RemoteA2AAgent — Calling Other Agents

### Python — Basic

```python
from google.adk.agents import RemoteA2AAgent

remote_agent = RemoteA2AAgent(
    name="math_checker",
    description="Calls remote prime checker agent",
    agent_card=AgentCard(
        name="prime_checker_agent",
        url="https://my-agent-service.a.run.app/a2a/check_prime_agent",
    ),
)

# Use as sub-agent in a workflow
root_agent = LlmAgent(
    name="math_assistant",
    sub_agents=[remote_agent],
    ...
)
```

### Python — With authentication

```python
import google.auth.transport.requests
import google.oauth2.id_token

class GCPCredentialProvider:
    """Provides GCP identity tokens for service-to-service A2A auth."""
    def get_headers(self) -> dict[str, str]:
        auth_req = google.auth.transport.requests.Request()
        token = google.oauth2.id_token.fetch_id_token(
            auth_req, "https://my-agent-service.a.run.app"
        )
        return {"Authorization": f"Bearer {token}"}

remote_agent = RemoteA2AAgent(
    name="secure_agent",
    agent_card=AgentCard(...),
    credential_provider=GCPCredentialProvider(),
)
```

### Go

```go
import "google.golang.org/adk/agent/a2aagent"

remoteAgent, err := a2aagent.New(a2aagent.Config{
    Name: "math_checker",
    AgentCard: &a2a.AgentCard{
        URL: "https://my-agent-service.a.run.app/a2a/check_prime_agent",
    },
})
```

## A2A Streaming

### Client-side — consume streaming events

```python
# RemoteA2AAgent with streaming enabled
remote_agent = RemoteA2AAgent(
    name="streaming_agent",
    agent_card=AgentCard(
        name="streaming_service",
        url="https://agent-service.a.run.app/a2a/stream",
        capabilities={"streaming": True},
    ),
)

# Consume streaming events
async for event in runner.run_async(...):
    if event.content:
        for part in event.content.parts:
            if part.text:
                print(part.text, end="", flush=True)  # Stream to user
            if part.function_call:
                print(f"\n[Tool call: {part.function_call.name}]")
```

### Server-side — expose streaming endpoint

```python
# A2A server with streaming (FastAPI + ADK)
from google.adk.a2a.server import A2AServer

a2a_server = A2AServer(
    agent=my_agent,
    agent_card=AgentCard(
        name="streaming_service",
        url="https://agent-service.a.run.app/a2a/stream",
        capabilities={"streaming": True},
    ),
)

# Mount on FastAPI
app = FastAPI()
app.mount("/a2a", a2a_server.build())
```

## A2A Error Handling

### Error types

| Error | When | Action |
|-------|------|--------|
| **Connection refused** | Remote agent down | Retry with backoff (3x, 2s/4s/8s) |
| **Timeout** | Remote agent too slow | Circuit break after 3 timeouts |
| **Auth failure (401)** | Token expired | Refresh token, retry once |
| **Not found (404)** | Wrong AgentCard URL | Fail permanently — check config |
| **Server error (500)** | Remote agent crashed | Retry with backoff, alert if persists |

### Retry wrapper for RemoteA2AAgent

```python
import asyncio
from typing import AsyncGenerator

class RetryingRemoteAgent:
    """Wraps RemoteA2AAgent with retry logic."""
    def __init__(self, agent, max_retries=3, base_delay=2.0):
        self.agent = agent
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.failure_count = 0
        self.circuit_open = False
        self.circuit_reset_after = 60.0  # seconds

    async def run(self, session_id, user_id, message):
        if self.circuit_open:
            raise Exception("Circuit breaker open — remote agent unavailable")

        for attempt in range(self.max_retries):
            try:
                async for event in self.agent.run_async(session_id, user_id, message):
                    yield event
                self.failure_count = 0
                return
            except (ConnectionError, TimeoutError) as e:
                self.failure_count += 1
                if self.failure_count >= 5:
                    self.circuit_open = True
                    asyncio.create_task(self._reset_circuit())
                    raise Exception(f"Circuit breaker opened after {self.failure_count} failures") from e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    raise

    async def _reset_circuit(self):
        await asyncio.sleep(self.circuit_reset_after)
        self.circuit_open = False
        self.failure_count = 0
```

## Cross-Language A2A

A2A is language-agnostic. Any agent can call any other agent as long as both agree on the A2A protocol.

### Python → Go

```python
# Python orchestrator calls Go worker agent
go_worker = RemoteA2AAgent(
    name="go_data_processor",
    agent_card=AgentCard(
        name="data_processor",
        url="https://go-worker.a.run.app/a2a/process",
    ),
)
```

### Go → TypeScript

```go
// Go orchestrator calls TS agent
tsAgent, _ := a2aagent.New(a2aagent.Config{
    Name: "ts_analytics",
    AgentCard: &a2a.AgentCard{
        URL: "https://ts-analytics.a.run.app/a2a/analyze",
    },
})
```

### Serialization contract

All A2A messages use the same structure regardless of language:

```json
{
  "session_id": "uuid",
  "user_id": "user-123",
  "content": {
    "role": "user",
    "parts": [{"text": "Is 17 prime?"}]
  }
}
```

Response events:

```json
{
  "content": {
    "role": "model",
    "parts": [{"text": "Yes, 17 is prime."}]
  },
  "actions": {"escalate": false}
}
```

## A2A Authentication

### GCP Service-to-Service (recommended for GCP workloads)

```python
# Both agents run on Cloud Run — use GCP identity tokens
import google.auth.transport.requests
import google.oauth2.id_token

def get_gcp_auth_headers(audience_url: str) -> dict:
    request = google.auth.transport.requests.Request()
    token = google.oauth2.id_token.fetch_id_token(request, audience_url)
    return {"Authorization": f"Bearer {token}"}
```

### API Key (for external/non-GCP)

```python
def get_apikey_headers(api_key: str) -> dict:
    return {"X-API-Key": api_key}
```

### Firebase Auth (for end-user identity propagation)

```python
# Propagate end-user Firebase token across A2A calls
def get_user_auth_headers(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}
```

## Service Discovery

### Static (recommended for most cases)

AgentCard URLs are configured in deployment config:

```yaml
# a2a_endpoints.yaml
remote_agents:
  prime_checker: "https://prime-checker-abc.a.run.app/a2a"
  data_processor: "https://data-processor-xyz.a.run.app/a2a"
```

### Dynamic (for large agent meshes)

Register AgentCards in a discovery service (Cloud DNS, Consul, custom registry):

```python
async def discover_agent(name: str) -> AgentCard:
    """Look up agent by name in discovery service."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://agent-registry.internal/discover/{name}")
        data = resp.json()
        return AgentCard(**data)
```

## A2A in Workflow Scaffolding

When scaffolding a workflow with `--with-a2a`:

1. Generate `AgentCard` for each agent exposed via A2A
2. Wire A2A endpoint (FastAPI mount or standalone server)
3. Generate `RemoteA2AAgent` wrappers for external dependencies
4. Add A2A auth provider (GCP identity token, API key, or Firebase)
5. Configure retry + circuit breaker
6. Add `a2a_endpoints.yaml` for service discovery
7. Add A2A health check (`GET /a2a/{agent_name}/health`)
