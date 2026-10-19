# ADK Skills — Routing Rules

This repo provides 26 Claude Code skills for building Google ADK (Agent Development Kit) agents. All skills live in `skills/` with standard SKILL.md format.

## ADK 2.x Source Policy

Current ADK guidance is source-backed. **The SDK is never vendored into this repo:**

- **Canonical sources:** Context7 `/google/adk-docs`, the installed `google.adk` package, and `google/adk-python` at the matching tag.
- **No local SDK folder.** There is no vendored SDK checkout, no local helper tree, and no committed source mirror. Never path-import the SDK.
- **Version:** `google-adk>=2.9.2,<3` from PyPI (root `requirements.txt`), validated through 2.12.0. Python **3.10** for 2.9.2–2.11.0, **3.11** for 2.12.0.

### 2.x Core Concepts (assume available)

Verified against Context7 `/google/adk-docs` and the installed `google.adk` package:

- **Graph Workflow Runtime** — `Workflow` plus `node()` define graph/dynamic orchestration. Use route maps and `Event(route=...)` for conditional routing. There is **no** `@edge` decorator in current docs.
- **Dynamic nodes** — `ctx.run_node(...)` schedules nodes at runtime; orchestrator nodes that call interactive nodes must use `rerun_on_resume=True`.
- **MCP tools** — current Python examples use `McpToolset` with `StdioConnectionParams` or `StreamableHTTPConnectionParams`. Treat `MCPToolset` as stale/deprecated spelling in this repo's generated examples.
- **Human-in-the-loop (HITL)** — `RequestInput` pauses a workflow for user input; do not use the old **`ctx.resume_data`** spelling.
- **Task-mode coordination** — MAS coordination uses `mode='task'` plus task request/result concepts. Do not invent a standalone `Task` class.
- **Sessions/memory are 2.x-native** — `google.adk.sessions.*` and `google.adk.memory.*`. v1-persisted session/state is **not** schema-compatible with 2.x; do not reuse old persisted state.

## Skill Routing

When a user request matches a trigger below, invoke the corresponding skill.

| Skill | Triggers |
|-------|----------|
| `adk-agent-builder` | "create an agent", "build agent", "task mode", "single-turn agent", "add a tool" |
| `adk-agent-personas` | "persona", "character agent", "domain expert", "specialist agent", "ready-made role" |
| `adk-agent-architecture` | "agent internals", "tool boundaries", "session state", "MCP vs A2A", "structured output" |
| `adk-agents` | "multi-agent", "supervisor", "agent team", "delegation", "routing patterns" |
| `adk-agent-orchestration` | "autonomous agent", "OODA", "goal-directed", "langgraph", "state machine", "checkpointed graph" |
| `adk-graph-workflows` | "build a workflow", "graph workflow", "fan-out", "conditional routing", "scaffold workflow" |
| `adk-runtime` | "runtime", "runner", "callbacks", "Reason-Act", "invocation context" |
| `adk-backend` | "backend", "server", "API for agent", "session endpoint" |
| `adk-configs` | "agent config", "agent YAML", "config schema" |
| `adk-a2a` | "A2A", "agent-to-agent", "AgentCard", "remote agent", "cross-language agent" |
| `adk-mcp` | "MCP", "McpToolset", "MCP server", "toolbox" |
| `adk-bidi-live` | "bidi", "live", "streaming audio", "voice agent", "real-time" |
| `adk-tools` | "bind tools", "function tool", "OpenAPI tool", "Google API tool", "tool catalog" |
| `adk-prompts` | "instruction", "prompt engineering", "system prompt", "few-shot" |
| `adk-rag` | "RAG", "knowledge base", "Pinecone", "Vertex AI RAG", "document ingestion" |
| `adk-embeddings` | "embedding", "gemini-embedding-2", "pgvector", "DatabaseSessionService", "vector store" |
| `adk-memory` | "memory", "SessionService", "long-term memory", "cross-session" |
| `adk-model-routing` | "which model", "thinking level", "model catalog", "deprecated model", "fallback chain" |
| `adk-litellm` | "litellm", "OpenAI/Anthropic/Bedrock/OpenRouter", "non-Google model", "provider fallback" |
| `adk-deploy-production` | "production readiness", "CI/CD for agents", "guardrails", "observability", "pre-deploy checklist", "retries" |
| `adk-deployment` | "adk deploy", "Cloud Run", "GKE", "Agent Engine", "Dockerfile", "Kubernetes manifest" |
| `adk-debug` | "debug agent", "inspect session", "tool call failed", "agent loops", "not discovered by adk web" |
| `adk-migration` | "migrate 1.x to 2.x", "breaking changes", "GraphAgent", "ctx.resume_data", "upgrade ADK" |
| `adk-architecture` | "how does ADK work", "event flow", "BaseNode", "NodeRunner", "resumption", "checkpoint" |
| `adk-skills-authoring` | "create a skill", "SKILL.md", "SkillToolset", "skill registry", "skill won't load" |
| `adk-typescript-go-parity` | "Go ADK", "TypeScript ADK", "port to Go/TS", "parity" |

Framework skills (`adk-litellm`, `adk-agent-orchestration`) load their docs **context7-first** (via the context7 MCP if available) and fall back to bundled `references/`.

## Claude Code Subagents

`agents/` holds Claude Code subagent `.md` files (`adk-architect`, `adk-agent-builder`, `adk-debugger`, `adk-git-ops`, `adk-style-checker`, `adk-workflow-designer`, `adk-workflow-builder`, `adk-setup`). Each subagent **adaptively loads the matching skill** via the Skill tool before executing, so its routing block mirrors the table above. The `git-ops`, `setup`, and `style-checker` subagents depend on skills that now live in `contributing/`; install them with `install.sh --with-contributing` or those three will run without their reference material.

## Examples

`examples/bidi_orchestrator/` is a runnable bidirectional/voice orchestrator demo, including its own `root_agent.yaml` orchestrator config. It is **not** a skill and **not** a Claude Code subagent. The former `adk-runtime/` `.agent.yaml` format was retired — nothing loaded it.

## Installation

Primary path — see README for details:
- **skills CLI (canonical):** `npx skills add OMIXEC/Google-ADK-Skills`
- **Advanced installer:** `bash install.sh --interactive`
- **Claude plugin:** `/plugin marketplace add OMIXEC/Google-ADK-Skills` then `/plugin install google-adk-skills`

`install.sh` targets: `codex`, `opencode`, `claude`, `cline`, `cursor`, `gemini-cli`, `windsurf`, `agents-lib`, `all`, `auto`, plus custom `--skills-dir`.
