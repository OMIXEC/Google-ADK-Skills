# ADK Skills — Routing Rules

This repo provides 25 Claude Code skills for building Google ADK (Agent Development Kit) agents. All skills live in `skills/` with standard SKILL.md format.

## Skill Routing

When a user request matches a trigger below, invoke the corresponding skill.

| Skill | Triggers |
|-------|----------|
| `adk-agentic-prod-workflows` | "build a workflow", "design multi-agent system", "scaffold agent project", "deploy ADK agent", "production workflow", "graph/parallel/sequential/loop agent", "CI/CD for agents" |
| `adk-agent-builder` | "create an agent", "build agent", "add agent node", "configure agent mode", "task mode", "single-turn agent" |
| `adk-agents` | "multi-agent system", "agent composition", "supervisor", "agent team", "delegation", "routing patterns" |
| `adk-architecture` | "how does ADK work", "event flow", "resumption", "checkpoint", "BaseNode", "NodeRunner", "runner roles", "LLM context orchestration" |
| `adk-runtime` | "runtime", "runner", "context lifecycle", "invocation context", "span design" |
| `adk-debug` | "debug agent", "inspect session", "troubleshoot tool call", "event flow issue", "model problem" |
| `adk-git` | "commit", "push", "pull", "rebase", "branch", "PR", "cherry-pick" |
| `adk-sample-creator` | "create a sample", "add example", "demonstrate agent pattern", "fan-out example" |
| `adk-setup` | "set up ADK", "install ADK", "configure environment", "get started", "prepare to contribute" |
| `adk-style` | "code style", "format code", "naming convention", "lint", "typing", "Pydantic pattern", "testing rules" |
| `adk-tools` | "bind tools", "function tool", "OpenAPI tool", "Google API tool", "tool catalog" |
| `adk-configs` | "agent config", "agent YAML", "config schema" |
| `adk-prompts` | "instruction", "prompt engineering", "system prompt for agent" |
| `adk-mcp` | "MCP integration", "MCP toolset", "StdioServerParameters", "SseServerParams" |
| `adk-a2a` | "A2A", "agent-to-agent", "cross-language agent", "AgentCard", "RemoteA2AAgent" |
| `adk-memory` | "memory", "SessionService", "session state", "persistence" |
| `adk-deployment` | "deploy", "Cloud Run", "Agent Engine", "GKE", "Terraform", "deployment manifest" |
| `adk-backend` | "backend", "server", "API for agent" |
| `adk-bidi-live` | "bidi", "live", "streaming audio", "voice agent", "real-time" |
| `adk-litellm` | "litellm", "OpenAI/Anthropic/Bedrock/OpenRouter model", "non-Google model", "model fallback", "cost optimization across providers" |
| `adk-langgraph` | "langgraph", "state machine workflow", "stateful graph", "conditional orchestration", "ADK↔LangGraph" |
| `adk-rag` | "RAG", "knowledge base", "vector search", "embeddings", "Pinecone", "Vertex AI RAG", "document ingestion" |
| `adk-persona` | "persona", "pre-built template", "character agent", "ready-made role" |
| `adk-domain-expert` | "domain expert", "specialist agent", "expert for <domain>" |
| `adk-autonomous-agent` | "autonomous agent", "self-reasoning", "OODA loop", "goal-directed", "proactive agent" |

Framework skills (`adk-litellm`, `adk-langgraph`) load their docs **context7-first** (via the context7 MCP if available) and fall back to bundled `references/`.

## Claude Code Subagents

`agents/` holds Claude Code subagent `.md` files (`adk-architect`, `adk-agent-builder`, `adk-debugger`, `adk-git-ops`, `adk-style-checker`, `adk-workflow-designer`, `adk-workflow-builder`, `adk-setup`). Each subagent **adaptively loads the matching skill** via the Skill tool before executing, so its routing block mirrors the table above.

## ADK Runtime Agents

`adk-runtime/agents/` holds the ADK Python runtime configs — `.agent.yaml` files (plus `root_agent.yaml`) loaded by the ADK runtime. Python tools and callbacks supporting these are in `adk-python/`. These are **not** Claude Code subagents.

## Installation

Three ways — see README for details:
- **Script (canonical, no auth):** `bash install.sh --target claude-code` or `curl -fsSL .../install.sh | bash`
- **npx:** `npx claude-adk-skills --target claude-code`
- **Claude plugin:** `/plugin marketplace add OMIXEC/Claude-ADK-Skills` then `/plugin install claude-adk-skills`

`install.sh` targets: `--target claude-code` (default), `gemini-cli`, `opencode`, `cursor`, `all`.
