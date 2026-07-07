# ADK Skills — Routing Rules

This repo provides 28 Claude Code skills for building Google ADK (Agent Development Kit) agents. All skills live in `skills/` with standard SKILL.md format.

## Vendored SDK — Source of Truth

Two ADK SDK folders are vendored side by side:

- **`adk-python-v2.3/`** — ADK 2.3.0 GA full source (`src/google/adk`, `pyproject.toml`). **Always reference `adk-python-v2.3/` for current API signatures.**
- **`adk-python-v1/`** — legacy repo helper tooling (`tools/`, `callbacks/`) + its `requirements.txt`. **`adk-python-v1/` exists only for migration diffing — never copy patterns from it into new code.**

The active runtime dependency is `google-adk>=2.3.0,<3` (installed from PyPI via root `requirements.txt`), not a path import of the vendored folder. Python **3.10+** required (`adk-python-v2.3/pyproject.toml`).

### v2.3 Core Concepts (assume available)

Verified against `adk-python-v2.3/src/google/adk/`:

- **Graph Workflow Runtime** — `node()` decorator (`workflow/_node.py`) defines function/LLM nodes; edges are `Edge` instances (`workflow/_graph.py`), **not** an `@edge` decorator. Fan-out runs nodes concurrently; fan-in via `JoinNode` (`workflow/_join_node.py`) which waits for all named predecessors.
- **Agent modes** — `LlmAgent.mode: Literal['chat', 'task', 'single_turn']` (`agents/llm_agent.py`). `task` delegates a scoped sub-task; `single_turn` completes without further user interaction; `chat` is the standard sub-agent.
- **Human-in-the-loop (HITL)** — `request_input` tool (`tools/_request_input_tool.py`) pauses a run for input; the workflow checkpoints and resumes via **`ctx.resume_inputs`** (`agents/context.py`) — **not** `ctx.resume_data`.
- **Task-mode coordination** — MAS coordination uses `mode='task'` plus `TaskRequest`/`TaskResult` and `FinishTaskTool` (`agents/llm/task/`). There is **no** standalone `Task` class.
- **Sessions/memory are v2.3-native** — `google.adk.sessions.*` and `google.adk.memory.*`. v1-persisted session/state is **not** schema-compatible with v2.3; do not reuse old persisted state.

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
| `adk-embeddings` | "embedding", "gemini-embedding-2", "vector store", "pgvector", "Cloud SQL", "Postgres session", "Firestore memory", "DatabaseSessionService", "vector search", "store embeddings in db" |
| `adk-migration` | "migrate 1.x to 2.3", "upgrade ADK", "breaking changes", "deprecated API", "GraphAgent removed", "MCPToolset error", "ctx.resume_data", "port to 2.3" |
| `adk-deployment` | "deploy", "Cloud Run", "Agent Engine", "GKE", "Terraform", "deployment manifest" |
| `adk-backend` | "backend", "server", "API for agent" |
| `adk-bidi-live` | "bidi", "live", "streaming audio", "voice agent", "real-time" |
| `adk-litellm` | "litellm", "OpenAI/Anthropic/Bedrock/OpenRouter model", "non-Google model", "model fallback", "cost optimization across providers" |
| `adk-model-routing` | "which model", "model routing", "select model", "thinking level", "effort", "thinking_budget", "reasoning depth", "model catalog", "fallback chain", "deprecated model" |
| `adk-langgraph` | "langgraph", "state machine workflow", "stateful graph", "conditional orchestration", "ADK↔LangGraph" |
| `adk-rag` | "RAG", "knowledge base", "vector search", "embeddings", "Pinecone", "Vertex AI RAG", "document ingestion" |
| `adk-persona` | "persona", "pre-built template", "character agent", "ready-made role" |
| `adk-domain-expert` | "domain expert", "specialist agent", "expert for <domain>" |
| `adk-autonomous-agent` | "autonomous agent", "self-reasoning", "OODA loop", "goal-directed", "proactive agent" |

Framework skills (`adk-litellm`, `adk-langgraph`) load their docs **context7-first** (via the context7 MCP if available) and fall back to bundled `references/`.

## Claude Code Subagents

`agents/` holds Claude Code subagent `.md` files (`adk-architect`, `adk-agent-builder`, `adk-debugger`, `adk-git-ops`, `adk-style-checker`, `adk-workflow-designer`, `adk-workflow-builder`, `adk-setup`). Each subagent **adaptively loads the matching skill** via the Skill tool before executing, so its routing block mirrors the table above.

## ADK Runtime Agents

`adk-runtime/agents/` holds the ADK Python runtime configs — `.agent.yaml` files (plus `root_agent.yaml`) loaded by the ADK runtime. Python tools and callbacks supporting these are in `adk-python-v1/` (legacy helper location, kept as reference). These are **not** Claude Code subagents.

## Installation

Primary path — see README for details:
- **skills.sh:** `npx skills add OMIXEC/Google-ADK-Skills`
- **Advanced installer:** `bash install.sh --interactive`
- **Package shim:** `npx google-adk-skills --interactive`
- **Claude plugin:** `/plugin marketplace add OMIXEC/Google-ADK-Skills` then `/plugin install google-adk-skills`

`install.sh` targets: `codex`, `opencode`, `claude`, `cline`, `cursor`, `gemini-cli`, `windsurf`, `agents-lib`, `all`, `auto`, plus custom `--skills-dir`.
