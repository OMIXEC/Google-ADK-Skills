---
description: Build or modify a Google ADK agent using the bundled ADK skills
argument-hint: [agent goal or requirements]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

Build or modify a Google ADK agent for: $ARGUMENTS

First load the most specific bundled ADK skill before writing code:
- `adk-agent-builder` for single agents, graph nodes, modes, routing, and configs.
- `adk-agents` for multi-agent composition, supervisors, and delegation.
- `adk-tools` for function tools, MCP, OpenAPI, or Google tools.
- `adk-memory` for session state, persistence, and memory.
- `adk-deployment` for Cloud Run, Agent Engine, GKE, Docker, or CI/CD.
- `adk-bidi-live` for real-time voice/audio/live streaming agents.
- `adk-rag` for retrieval-augmented generation.

Read the selected skill references, inspect the current repository, then implement complete runnable code with imports, configuration, and an entrypoint. Do not hardcode credentials.
