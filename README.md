# Google-ADK-Skills

**27 production-grade Google ADK skills for Codex, OpenCode, Claude, Cline, Cursor, Gemini CLI, Windsurf, and `.agents` libraries**

Build sophisticated AI agents using Google's Agent Development Kit (ADK): multi-agent orchestration, LangGraph state machines, LiteLLM multi-provider routing, real-time bidirectional streaming, RAG pipelines, MCP tool integration, autonomous agents, and production deployment.

## ADK Python 2.x Baseline

- Target: `google-adk>=2.9.2,<3`, validated through **2.12.0** (2026-10-13).
- The **1.x line is still shipping in parallel** (latest 1.39.1); 2.x is not yet a replacement for every 1.x user.
- Python: **3.10** for 2.9.2–2.11.0, **3.11** for 2.12.0. Supported through 3.15. Use `uv` in repos that already standardize on it.
- New workflow guidance should prefer the 2.x `Agent` plus `Workflow` graph/dynamic orchestration. `SequentialAgent`, `ParallelAgent`, and `LoopAgent` still work in 2.12 but emit a `DeprecationWarning` and are slated for removal; use `Workflow` for new code.
- Read [`COMPATIBILITY.md`](COMPATIBILITY.md) before changing examples, model IDs, or migration guidance. Each skill carries the same version floor in its own `references/adk-2x-baseline.md`, so a standalone install is never missing it.
- **The SDK is never vendored.** `google-adk` installs from PyPI; always import from the installed `google.adk.*`. Context7 `/google/adk-docs` and the installed package are canonical. See [`MIGRATION.md`](MIGRATION.md).

Version posture, sources, and history: [`COMPATIBILITY.md`](COMPATIBILITY.md) · [`SOURCES.md`](SOURCES.md) · [`CHANGELOG.md`](CHANGELOG.md).

## Installation

### Option 1 — Skills CLI (canonical)

```bash
npx skills add OMIXEC/Google-ADK-Skills
```

The `skills` CLI ([`vercel-labs/skills`](https://github.com/vercel-labs/skills)) is the primary install path for agent skills. It resolves the collection straight from GitHub: no npm publish and no registry listing are involved.

### Option 2 — Repo installer (custom targets and advanced options)

```bash
# Auto-detect installed tools/config dirs and install all skills
curl -fsSL https://raw.githubusercontent.com/OMIXEC/Google-ADK-Skills/main/install.sh | bash

# Guided install with target/method/runtime/skill prompts
git clone https://github.com/OMIXEC/Google-ADK-Skills.git
cd Google-ADK-Skills
bash install.sh --interactive
```

By default the installer only installs skill folders. It does not require Python, pip, Google credentials, GitHub auth, or shell rc changes.

Main target paths:

| Target | Skills directory |
|--------|------------------|
| `codex` | `~/.codex/skills` |
| `opencode` | `~/.opencode/skills` |
| `claude` | `~/.claude/skills` |
| `cline` | `~/.cline/skills` |
| `cursor` | `~/.cursor/skills` |
| `gemini-cli` | `~/.gemini/skills` |
| `windsurf` | `~/.windsurf/skills` |
| `agents-lib` | `~/.agents/skills` |

The installer also installs bundled subagents and slash commands where the target supports them:

| Target | Agents directory | Commands directory |
|--------|------------------|--------------------|
| `claude` | `~/.claude/agents` | `~/.claude/commands` |
| `agents-lib` | `~/.agents/agents` | `~/.agents/commands` |

Flags:

```bash
--target <codex|opencode|claude|cline|cursor|gemini-cli|windsurf|agents-lib|all|auto>
--copy                 Copy skill folders instead of symlinking them
--install-dir <path>   Checkout/cache location, default: ~/.google-adk-skills
--skills-dir <path>    Install into a custom tool skills directory
--scope <user|global>  User home install or global /usr/local/share install
--ref <branch-or-tag>  Git ref to install, default: main
--skills <list|all>    Comma-separated skills to install, default: all
--interactive          Prompt for target, method, runtime, evals, and skills
--no-agents            Do not install bundled subagent definitions
--no-commands          Do not install bundled slash commands
--with-evals           Keep tests/ in the install checkout
--with-contributing    Also install contributing/ (skills for hacking on adk-python)
--with-runtime         Create a Python venv and install runtime dependencies
--shell-integration    Add the adk alias/PATH entry to your shell rc file
--force                Replace existing non-symlink skill directories
```

Examples:

```bash
# Install for Codex and replace any existing copied skills
bash install.sh --target codex --copy --force

# Install into the main skills paths for every supported tool
bash install.sh --target all

# Install globally for every supported tool (requires writable /usr/local/share)
sudo bash install.sh --target all --scope global

# Install only selected skills
bash install.sh --target opencode --skills adk-agents,adk-tools,adk-memory

# Install into any compatible custom skills directory
bash install.sh --skills-dir ~/.my-agent-tool/skills --copy

# Install into the shared .agents library
bash install.sh --target agents-lib --copy

# Install skills plus the Python runtime helpers
bash install.sh --target claude --with-runtime --shell-integration
```

### Option 3 — Claude plugin (skills + agents + commands + MCP)

```
/plugin marketplace add OMIXEC/Google-ADK-Skills
/plugin install google-adk-skills
```

The plugin is the only channel that installs the skills together with the bundled subagents, slash commands, and the context7 MCP server. Use Option 1 when you only want the skills, and Option 2 for non-Claude targets, selective installs, runtime helpers, or global installs.

### Prerequisites

- Skills-only install: `bash` plus either `git`, `curl`, or `wget`.
- Runtime helpers: Python 3.10+ and pip, enabled with `--with-runtime` (ADK 2.3 requires Python 3.10+).
- ADK usage after install: `GOOGLE_API_KEY` or the credentials required by the models/tools you choose.
- Optional: `PINECONE_API_KEY` for RAG and `LITELLM_*` keys for multi-provider routing.

---

## Skills (27)

| Skill | Description |
|-------|-------------|
| `adk-a2a` | Agent-to-Agent protocol — agent cards, remote delegation, streaming tasks, auth propagation |
| `adk-agent-architecture` | Agent internals — modes, tool boundaries, MCP, A2A, memory, structured output, model choice |
| `adk-agent-builder` | Build one agent — instruction, tools, task/single-turn modes, first test |
| `adk-agent-orchestration` | Runtime control — OODA loops, LangGraph state machines, stop conditions |
| `adk-agent-personas` | Personas — 30+ templates plus a bespoke domain-expert generator |
| `adk-agents` | Multi-agent composition — supervisor, router, delegation patterns |
| `adk-architecture` | ADK internals — node/graph execution, Context, Events, checkpoint/resume, tracing |
| `adk-backend` | Service layer — HTTP server, session endpoints, request lifecycle |
| `adk-bidi-live` | Real-time — Live API, audio/video, WebSocket, LiveRequestQueue |
| `adk-configs` | Declarative config — YAML agents, environment variables, agent cards |
| `adk-debug` | Debugging — `adk run`/`adk web`, sessions, events, tool calls, symptom catalogue |
| `adk-deploy-production` | Production readiness — CI/CD, guardrails, observability, resilience, evals, checklist |
| `adk-deployment` | Deploy commands — Cloud Run, GKE, Agent Engine, Docker and Kubernetes manifests |
| `adk-embeddings` | Embeddings and persistence — `gemini-embedding-2`, DB SessionService, pgvector/Firestore vector |
| `adk-graph-workflows` | Workflow shape — graph/dynamic/collaborative/template, scaffolding, composition |
| `adk-litellm` | Provider routing — 100+ providers, fallbacks, cost trade-offs |
| `adk-mcp` | MCP — `McpToolset`, stdio/streamable HTTP, discovery, database toolboxes |
| `adk-memory` | Memory policy — session state, long-term memory, persistence, cross-session recall |
| `adk-migration` | 1.x → 2.x through 2.12.0 — breaking changes, renamed APIs, session incompatibility |
| `adk-model-routing` | Model selection — Gemini 3.x catalog, `thinking_level`, fallback chains, retirement |
| `adk-performance-scaling` | Performance — latency, concurrency, quota, context caching, compaction, cost per turn |
| `adk-prompts` | Instructions — system prompts, few-shot examples, output shape, token cost |
| `adk-rag` | RAG — Pinecone or Vertex AI RAG, ingestion, chunking, grounding |
| `adk-runtime` | Execution internals — event loop, Runner, callbacks, Reason-Act cycle |
| `adk-skills-authoring` | Skills subsystem — SKILL.md contract, loader, registry, `SkillToolset` |
| `adk-tools` | Tools — function tools, Google built-ins, OpenAPI integrations, composition |
| `adk-typescript-go-parity` | Go/TypeScript templates and parity notes |

Skills are routed automatically via CLAUDE.md trigger words. You can also invoke any skill explicitly:

```
Build a customer support agent with session memory and Cloud Run deployment
```

Claude Code matches the request to `adk-agent-builder` + `adk-memory` + `adk-deployment` and loads the relevant skills.

---

## Quick Start

### Create a multi-agent workflow

```
Design a research pipeline with a web-search agent, an analyst, and a writer — deploy to Cloud Run
```

Triggers: `adk-agents` → `adk-graph-workflows` → `adk-deploy-production`

### Use a non-Google model

```
Route this agent to Claude claude-opus-4-7 via LiteLLM with a Gemini fallback
```

Triggers: `adk-litellm`

### Add RAG to an agent

```
Build a knowledge base agent with Pinecone ingestion for PDF documents
```

Triggers: `adk-rag`

### Real-time voice agent

```
Create a voice assistant using the native audio model with WebSocket streaming
```

Triggers: `adk-bidi-live`

### LangGraph orchestration

```
Build a stateful customer onboarding workflow with conditional branching using LangGraph
```

Triggers: `adk-agent-orchestration`

---

## Project Structure

```
Google-ADK-Skills/
├── .agents/
│   └── library.json         ← generic .agents library metadata
├── .claude-plugin/
│   ├── plugin.json          ← Claude plugin manifest
│   └── marketplace.json     ← marketplace listing
├── skills/                  ← 27 product skills (each: SKILL.md + references/)
│   ├── adk-a2a/
│   ├── adk-agent-builder/
│   ├── adk-graph-workflows/
│   ├── adk-agents/
│   ├── ... (27 total)
│   └── adk-tools/
├── contributing/            ← 8 contributor-only skills (opt-in: --with-contributing)
├── agents/                  ← Claude Code subagents (.md files, auto-loaded by Claude)
│   ├── architect.md
│   ├── agent-builder.md
│   ├── debugger.md
│   ├── git-ops.md
│   ├── setup.md
│   ├── style-checker.md
│   ├── workflow-builder.md
│   └── workflow-designer.md
├── commands/                ← Slash commands for installing, building, and validating ADK skills
│   ├── adk-build-agent.md
│   ├── adk-install-skills.md
│   └── adk-validate-skills.md
├── examples/
│   └── bidi_orchestrator/   ← runnable bidirectional/voice orchestrator demo
│       └── root_agent.yaml  ← its orchestrator config
├── bin/
│   └── cli.js               ← npx shim → shells out to install.sh
├── tests/                   ← pytest skill validation suite
├── scripts/                 ← quick_validate.py, eval helpers
├── docs/                    ← local ADK reference docs
├── mcp_servers/
│   └── CATALOG.md
├── skills.sh.json           ← skills.sh repo page grouping metadata
├── install.sh               ← canonical installer (no auth, HTTPS clone + tarball fallback)
├── package.json             ← npx entry point
├── CLAUDE.md                ← dispatcher routing rules
└── requirements.txt
```

**`agents/` vs `examples/`**

- `agents/*.md` — Claude Code subagent definitions. Each auto-loads the matching ADK skill via the Skill tool before executing. These run inside Claude Code.
- `examples/bidi_orchestrator/` — a runnable bidirectional/voice orchestrator demo with its own `root_agent.yaml`. Not a skill and not a subagent.

---

## Environment Variables

```bash
# Google AI (required)
GOOGLE_API_KEY=your_gemini_api_key

# Pinecone (RAG features)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_HOST=your_index_host

# LiteLLM providers (optional, use whichever you need)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
AWS_ACCESS_KEY_ID=your_aws_key        # Bedrock
OPENROUTER_API_KEY=your_openrouter_key

# MCP Servers
BRAVE_API_KEY=your_brave_api_key
GITHUB_TOKEN=your_github_token

# GCP Deployment
GOOGLE_CLOUD_PROJECT=your_project_id
```

---

## Requirements

```
google-adk>=2.9.2,<3
langgraph>=0.2.0
pinecone>=5.0.0
google-cloud-aiplatform>=2.2
fastapi>=0.100.0
uvicorn>=0.20.0
```

---

## Documentation

- [Google ADK Docs](https://google.github.io/adk-docs/)
- [LiteLLM Docs](https://docs.litellm.ai/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Pinecone Docs](https://docs.pinecone.io/)

---

## License

MIT License — see LICENSE for details.
