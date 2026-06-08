# CLAUDE-ADK-SKILLS

**25 Production-Grade Google ADK Skills for Claude Code**

Build sophisticated AI agents using Google's Agent Development Kit (ADK): multi-agent orchestration, LangGraph state machines, LiteLLM multi-provider routing, real-time bidirectional streaming, RAG pipelines, MCP tool integration, autonomous agents, and production deployment.

## Installation

### Option 1 — Script (canonical, no auth required)

```bash
# Auto-detect your IDE
curl -fsSL https://raw.githubusercontent.com/OMIXEC/Claude-ADK-Skills/main/install.sh | bash

# Or clone first, then install
git clone https://github.com/OMIXEC/Claude-ADK-Skills.git
cd Claude-ADK-Skills
bash install.sh --target claude-code
```

Flags: `--target <claude-code|gemini-cli|opencode|cursor|all>`, `--copy` (copy files instead of symlink), `--install-dir <path>`, `--with-evals` (include tests/ and scripts/).

### Option 2 — npx

```bash
npx claude-adk-skills
npx claude-adk-skills --target cursor --copy
```

### Option 3 — Claude Plugin Marketplace

```
/plugin marketplace add OMIXEC/Claude-ADK-Skills
/plugin install claude-adk-skills
```

### Prerequisites

- Python 3.11+
- Git (optional — installer falls back to tarball download when git is unavailable)
- `GOOGLE_API_KEY` (Gemini)
- Optional: `PINECONE_API_KEY` (RAG), `LITELLM_*` keys (multi-provider)

---

## Skills (25)

| Skill | Description |
|-------|-------------|
| `adk-a2a` | Agent-to-Agent protocol — remote agent calls, agent cards, HTTP delegation, distributed agent networks |
| `adk-agent-builder` | Build, configure, and iterate on ADK agents — task mode, single-turn mode, graph-based workflows |
| `adk-agentic-prod-workflows` | Production multi-agent workflow scaffold — graph/parallel/sequential/loop patterns, CI/CD, evals, observability |
| `adk-agents` | Multi-agent composition — routing patterns, sequential/parallel execution, supervisor architectures |
| `adk-architecture` | ADK internals — graph orchestration, event flow, BaseNode, NodeRunner, resumption, checkpointing |
| `adk-autonomous-agent` | Self-reasoning agents — OODA loop, goal-directed execution, autonomous planning without per-step prompts |
| `adk-backend` | Backend services — runtime event loops, session management, state handling, Runner/Agent execution model |
| `adk-bidi-live` | Real-time streaming — Live API, native audio (`gemini-live-2.5-flash-native-audio`), WebSocket, LiveRequestQueue |
| `adk-configs` | Agent configuration — YAML agent definitions, environment variables, agent cards, deployment configs |
| `adk-debug` | Debugging — session inspection, tool call tracing, event flow diagnosis, model troubleshooting |
| `adk-deployment` | Production deployment — Cloud Run, GKE, Vertex AI Agent Engine, Docker, CI/CD pipelines |
| `adk-domain-expert` | Bespoke specialist agents for any domain not covered by standard personas (tax law, marine biology, etc.) |
| `adk-git` | Git operations — commit, push, pull, rebase, branch, PR, cherry-pick with ADK commit conventions |
| `adk-langgraph` | LangGraph orchestration — state machines, conditional edges, LLM-driven routing, ADK↔LangGraph interop |
| `adk-litellm` | 100+ LLM providers — OpenAI, Anthropic, Bedrock, OpenRouter, Ollama, vLLM; model switching, cost optimization |
| `adk-mcp` | MCP integration — MCPToolset, StdioServerParameters, SseServerParams, database toolboxes |
| `adk-memory` | Memory and state — session state, long-term memory, persistence backends, cross-session recall |
| `adk-persona` | 30+ pre-built personas — tutor, coach, analyst, support rep; ready-made templates with optimized instructions |
| `adk-prompts` | Prompt engineering — agent instructions, few-shot examples, system prompts, token cost optimization |
| `adk-rag` | Retrieval-augmented generation — Pinecone (self-managed) or Vertex AI RAG (managed), embeddings, ingestion |
| `adk-runtime` | Runtime architecture — event loops, Runner model, callbacks, Reason-Act cycle, internals |
| `adk-sample-creator` | Author new samples and examples for the ADK Python repository |
| `adk-setup` | Local dev environment setup — install dependencies, configure credentials, prepare for contributing |
| `adk-style` | Code style — Python idioms, codebase conventions, imports, typing, Pydantic patterns, formatting |
| `adk-tools` | Tools — custom function tools, Google built-in tools (Search, Code Execution), OpenAPI integrations |

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

Triggers: `adk-agents` → `adk-agentic-prod-workflows` → `adk-deployment`

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

Triggers: `adk-langgraph`

---

## Project Structure

```
Claude-ADK-Skills/
├── .claude-plugin/
│   ├── plugin.json          ← Claude plugin manifest
│   └── marketplace.json     ← marketplace listing
├── skills/                  ← 25 skill directories (each: SKILL.md + references/)
│   ├── adk-a2a/
│   ├── adk-agent-builder/
│   ├── adk-agentic-prod-workflows/
│   ├── adk-agents/
│   ├── ... (25 total)
│   └── adk-tools/
├── agents/                  ← Claude Code subagents (.md files, auto-loaded by Claude)
│   ├── architect.md
│   ├── agent-builder.md
│   ├── debugger.md
│   ├── git-ops.md
│   ├── setup.md
│   ├── style-checker.md
│   ├── workflow-builder.md
│   └── workflow-designer.md
├── adk-runtime/
│   └── agents/              ← ADK Python runtime configs (.agent.yaml, loaded by ADK runner)
│       ├── root_agent.yaml
│       ├── architect.agent.yaml
│       └── ... (11 configs)
├── bin/
│   └── cli.js               ← npx shim → shells out to install.sh
├── tests/                   ← pytest skill validation suite
├── scripts/                 ← quick_validate.py, eval helpers
├── docs/                    ← local ADK reference docs
├── mcp_servers/
│   └── CATALOG.md
├── install.sh               ← canonical installer (no auth, HTTPS clone + tarball fallback)
├── package.json             ← npx entry point
├── CLAUDE.md                ← dispatcher routing rules
└── requirements.txt
```

**`agents/` vs `adk-runtime/agents/`**

- `agents/*.md` — Claude Code subagent definitions. Each auto-loads the matching ADK skill via the Skill tool before executing. These run inside Claude Code.
- `adk-runtime/agents/*.agent.yaml` — ADK Python runtime agent configs consumed by the ADK runner (`google-adk`). These configure Gemini-based agents in the ADK execution environment.

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
google-adk>=1.0.0
litellm>=1.0.0
langgraph>=0.2.0
pinecone>=5.0.0
vertexai>=1.0.0
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
