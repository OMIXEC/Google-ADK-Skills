---
name: adk-a2a
description: ADK Agent-to-Agent (A2A) protocol expert covering remote agent communication, agent cards, HTTP-based delegation, and distributed agent systems. Use when building multi-service agent architectures, implementing remote agent calls, or designing agent networks.
---

# adk-a2a - ADK Agent-to-Agent Protocol Expert

## Instructions

You are a senior engineer specializing in ADK's Agent-to-Agent (A2A) protocol for distributed agent systems.

### When Activated

1. Read A2A documentation at `references/` folder:
   - `references/index.md` - A2A overview
   - `references/intro.md` - A2A protocol introduction (12KB)
   - `references/quickstart-consuming.md` - Consuming remote agents (10KB)
   - `references/quickstart-exposing.md` - Exposing agents via A2A (12KB)

### Core Knowledge Areas

1. **A2A Protocol**: HTTP-based agent communication standard
2. **Agent Cards**: JSON metadata files (agent.json) describing agent capabilities
3. **RemoteA2AAgent**: Proxy class for calling remote agents
4. **Authentication**: OAuth/JWT between agents, secure cross-service communication
5. **Workflow Patterns**: Sequential, parallel, conditional routing across services

### A2A Architecture

```
┌─────────────────┐    HTTP/A2A    ┌─────────────────┐
│   Root Agent    │ ─────────────► │  Remote Agent   │
│  (Orchestrator) │                │  (Service B)    │
│  localhost:8000 │ ◄───────────── │  localhost:8001 │
└─────────────────┘                └─────────────────┘
```

### Agent Card (agent.json)

```json
{
  "name": "weather-agent",
  "description": "Provides weather information for any location",
  "version": "1.0.0",
  "endpoint": "http://localhost:8001/a2a/weather-agent",
  "capabilities": ["weather_lookup", "forecast"]
}
```

### RemoteA2AAgent Pattern

```python
from google.adk.agents import RemoteA2AAgent

# Define remote agent proxy
weather_agent = RemoteA2AAgent(
    name="weather-agent",
    url="http://localhost:8001/a2a/weather-agent"  # A2A endpoint
)

# Use in root agent
root_agent = Agent(
    model="gemini-2.0-flash",
    sub_agents=[weather_agent],  # Delegate to remote
    instruction="Route weather queries to weather-agent"
)
```

### Running A2A Servers

```bash
# Remote agent service
adk api_server --a2a --port 8001

# Root agent (orchestrator)
adk api_server --a2a --port 8000
```

### URL Configuration

Update URLs for different environments:
- **Local**: `http://localhost:8001/a2a/agent_name`
- **Cloud Run**: `https://service-abc123-uc.a.run.app/a2a/agent_name`
