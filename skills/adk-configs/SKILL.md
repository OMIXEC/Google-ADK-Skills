---
name: adk-configs
description: ADK configuration expert covering YAML agent definitions, environment variables, agent cards, and deployment configs. Use when setting up ADK projects, managing environment-specific settings, or defining agents declaratively.
---

# adk-configs - ADK Configuration Expert

## Instructions

You are a senior engineer specializing in ADK configuration patterns and project setup.

### When Activated

1. Read `../../docs/python-adk-2.md` for current ADK 2.x dependency and API defaults.
2. Read agent configuration at `../adk-agents/references/config.md`
3. Read A2A agent cards at `../adk-a2a/references/` for agent.json patterns
4. The configuration patterns are embedded in this skill

### Core Knowledge Areas

1. **YAML Agent Definitions**: Declarative agent configuration
2. **Environment Variables**: API keys, endpoints, feature flags
3. **Agent Cards**: JSON metadata for A2A discovery
4. **pyproject.toml**: Python project configuration, dependencies
5. **Deployment Configs**: Docker, Kubernetes, Cloud Run settings

### Project Structure

```
my_adk_project/
├── src/
│   └── my_app/
│       ├── agents/
│       │   └── my_agent/
│       │       ├── __init__.py
│       │       ├── agent.py          # Defines root_agent
│       │       └── agent.yaml        # Optional YAML config
│       └── tools/
├── .env                              # Environment variables
├── pyproject.toml                    # Dependencies
└── agent.json                        # Agent card (for A2A)
```

### Environment Variables

```bash
# .env file
GOOGLE_API_KEY=your-api-key
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Optional
ADK_LOG_LEVEL=DEBUG
ADK_STREAMING_MODE=BIDI
```

### YAML Agent Definition

```yaml
# agent.yaml
name: my-agent
model: gemini-3.5-flash
instruction: |
  You are a helpful assistant.
  Always be concise and accurate.
tools:
  - google_search
  - custom_tool
generate_content_config:
  max_output_tokens: 1024
```

### pyproject.toml

```toml
[project]
name = "my-adk-app"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "google-adk>=2.3.0,<3",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.24.0"]
```

### Agent Card (agent.json)

```json
{
  "name": "my-agent",
  "version": "1.0.0",
  "description": "Description of agent capabilities",
  "endpoint": "http://localhost:8000/a2a/my-agent",
  "capabilities": ["capability1", "capability2"]
}
```
