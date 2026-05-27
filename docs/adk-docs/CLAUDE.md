# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Mission

Build Claude Code skills for Google's Agent Development Kit (ADK) covering: backend architecture, deployment, prompt engineering, tools, memory, MCP, A2A, agents, runtime, configs, LiteLLM proxy, and bidi models.

## Development Commands

### Python Environment
```bash
# Python 3.10+ required
pip install -e ".[dev]"        # or: uv pip install -e ".[dev]"
export SSL_CERT_FILE=$(python -m certifi)  # SSL fix for macOS
```

### Running ADK Apps
```bash
uvicorn main:app --reload      # FastAPI development server
adk web                        # ADK interactive Web UI
adk api_server                 # ADK production API server
adk api_server --a2a           # API server with A2A protocol
adk run                        # CLI testing
adk deploy                     # Deploy to Cloud Run/GKE/Vertex
```

### Testing
```bash
pytest                         # Run all tests
pytest tests/test_file.py::test_name  # Single test
```

## Repository Structure

```
ADK-SKILLS/
├── .claude/
│   └── skills/              # ADK domain skills (12 skills)
│       ├── adk-backend/     # Runtime, sessions, state
│       ├── adk-deployment/  # Cloud Run, GKE, Vertex AI
│       ├── adk-prompts/     # Instructions, few-shot, cost optimization
│       ├── adk-tools/       # Custom functions, built-in tools
│       ├── adk-memory/      # State, memory, persistence
│       ├── adk-mcp/         # MCP integration, MCPToolset
│       ├── adk-a2a/         # Agent-to-Agent protocol
│       ├── adk-agents/      # Multi-agent patterns
│       ├── adk-runtime/     # Event loop, callbacks
│       ├── adk-configs/     # YAML configs, env vars
│       ├── adk-litellm/     # 100+ model support via LiteLLM
│       └── adk-bidi-live/   # Native audio, Live API streaming
├── gcp-blogs/
│   ├── .claude/
│   │   ├── agents/          # Existing: adk-reviewer, docs-reviewer
│   │   └── skills/          # Existing: bidi, google-adk, vs20
│   └── [blog articles]      # Educational content with working examples
└── CLAUDE.md
```

## ADK Documentation Reference

Each skill has a `references/` folder with relevant ADK documentation copied locally:

| Skill | References Included |
|-------|---------------------|
| `adk-runtime` | runtime-architecture.md (28KB event loop guide) |
| `adk-memory` | session.md, state.md, memory.md, express-mode.md |
| `adk-tools` | function-tools.md, built-in-tools.md, mcp-tools.md, openapi-tools.md |
| `adk-mcp` | index.md, mcp-tools.md (51KB), ADK_MCP_Integration.md |
| `adk-a2a` | intro.md, quickstart-consuming.md, quickstart-exposing.md |
| `adk-agents` | multi-agents.md (45KB), llm-agents.md, custom-agents.md, models.md |
| `adk-deployment` | cloud-run.md, gke.md, agent-engine.md |
| `adk-bidi-live` | custom-streaming-ws.md (32KB), streaming-tools.md |
| `adk-litellm` | README.md, dad_joke_agent/ example |

Source documentation: `../Xheight-Projects/Aion-X/app/docs/ADK-agents/`

## ADK Architecture Overview

### Core Abstractions
- **Agent**: Blueprint with identity, instructions, tools
- **Tool**: Python function the agent can call
- **Runner**: Event loop orchestrating Reason-Act cycle
- **Session**: Conversation state and history
- **Memory**: Long-term recall across sessions
- **Artifact Service**: Non-textual data management

### Streaming Architecture (4-Phase Lifecycle)
1. **App Init**: Create Agent, Runner (once at startup)
2. **Session Init**: Create LiveRequestQueue, RunConfig (per session)
3. **Streaming Loop**: Bidirectional message flow via WebSocket
4. **Cleanup**: Close queue, cleanup resources

### Key Components
- `InMemoryRunner` / `Runner`: Agent execution orchestrator
- `LiveRequestQueue`: Bidirectional message passing for streaming
- `RunConfig`: Response modalities (`TEXT`, `AUDIO`), streaming modes
- `MCPToolset`: MCP server integration for external tools
- `RemoteA2AAgent`: Agent-to-Agent protocol proxy for distributed agents
- `LiteLlm`: Wrapper for 100+ LLM providers (OpenAI, Anthropic, etc.)

### Canonical Agent Structure
```
my_agent/
├── __init__.py
└── agent.py              # Defines root_agent variable
```

## Creating New Skills

Use the `skill-creator` skill or reference existing examples:
- `gcp-blogs/.claude/skills/bidi/SKILL.md` - Comprehensive skill with knowledge areas
- `gcp-blogs/.claude/skills/google-adk/SKILL.md` - Minimal skill pointing to SDK

### Skill Naming Convention
Skills are named `adk-{domain}` where domain is the ADK area:
`adk-backend`, `adk-deployment`, `adk-prompts`, `adk-tools`, `adk-memory`, `adk-mcp`, `adk-a2a`, `adk-agents`, `adk-runtime`, `adk-configs`, `adk-litellm`, `adk-bidi-live`

### SKILL.md Structure
Each skill has:
- `SKILL.md` - Skill definition with frontmatter and instructions
- `references/` - Local copies of relevant ADK documentation

```yaml
---
name: adk-{domain}
description: Brief description of what the skill covers and when to use it
---

# Skill Title

## Instructions
1. Read documentation at `references/` folder
2. [Domain-specific guidance with embedded patterns]
```

## Existing Agents (gcp-blogs/.claude/agents/)

- **adk-reviewer**: Reviews code/docs against ADK SDK, Gemini Live API, Vertex AI Live API
- **docs-reviewer**: Ensures documentation consistency in structure, style, and code samples

## Key ADK Patterns

### FastAPI WebSocket Streaming
```python
# Two concurrent tasks: upstream (client→agent) and downstream (agent→client)
async def ws_endpoint(websocket: WebSocket, user_id: str):
    live_request_queue = LiveRequestQueue()
    run_config = RunConfig(streaming_mode=StreamingMode.BIDI, response_modalities=["TEXT"])

    async with asyncio.TaskGroup() as tg:
        tg.create_task(agent_to_client(websocket, runner, live_request_queue, run_config))
        tg.create_task(client_to_agent(websocket, live_request_queue))
```

### Multi-Agent Patterns
- **Sequential**: Agent chain (writer → reviewer → refactorer)
- **Parallel**: Concurrent execution with aggregation
- **Routing**: LLM-based delegation to specialized agents
- **A2A Remote**: HTTP-based communication with remote agents via agent cards
