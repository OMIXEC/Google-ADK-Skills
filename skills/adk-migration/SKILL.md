---
name: adk-migration
description: >-
  Migrate ADK agents from 1.x to 2.3. Covers breaking API changes (graph
  Workflow vs GraphAgent, McpToolset, BuiltInCodeExecutor, ctx.resume_inputs,
  agent modes), renamed imports, deploy CLI changes, model/thinking/embedding
  updates, and session/state incompatibility. Use when upgrading an ADK 1.x
  codebase to 2.3, auditing code for deprecated 1.x APIs, or resolving 2.3
  import/attribute errors.
---

# adk-migration — ADK 1.x → 2.3

Port an ADK 1.x codebase to 2.3 (`google-adk>=2.3.0,<3`). Every mapping below is
verified against `adk-python-v2.3/src/google/adk`. Reference that tree for
signatures — never `adk-python-v1/`.

## When to use

- Upgrading an ADK 1.x project to 2.3.
- Diagnosing 2.3 `ImportError`/`AttributeError` from old symbol names.
- Auditing a codebase for deprecated 1.x patterns before shipping.

## Breaking-change checklist

Scan the codebase (`grep`) for each left-hand pattern and apply the fix:

| 1.x (deprecated / removed) | 2.3 |
|----------------------------|-----|
| `GraphAgent`, `builder.add_node/add_edge`, `Condition`, `google.adk.agents.graph` | `Workflow` + `node()` + `Edge(from_node, to_node, route)` + `JoinNode` |
| `@edge` decorator | `Edge(...)` class instances |
| `ctx.resume_data` | `ctx.resume_inputs` |
| `MCPToolset` | `McpToolset` |
| `connection_params=StdioServerParameters(...)` | `connection_params=StdioConnectionParams(server_params=StdioServerParameters(...))` |
| `from ...tools import code_execution` (+ in `tools=`) | `BuiltInCodeExecutor` (`google.adk.code_executors`) via `code_executor=` |
| `from google.adk.sessions import VertexAiMemoryBankService` | `from google.adk.memory import VertexAiMemoryBankService` |
| `RemoteA2AAgent` | `RemoteA2aAgent` (`google.adk.agents.remote_a2a_agent`) |
| `adk deploy cloud-run` / `adk deploy vertex` | `adk deploy cloud_run` / `adk deploy agent_engine` |
| `thinking_budget=<int>` | `thinking_level="minimal\|low\|medium\|high"` |
| `temperature` / `top_p` / `top_k` / `candidate_count` on Gemini 3.x | remove (no longer recommended / unsupported) |
| `gemini-2.0-*`, `gemini-1.5-*`, `gemini-2.5-*`, `gemini-pro` | `gemini-3.5-flash` / `gemini-3.1-flash-lite` / `gemini-3.1-pro-preview` |
| `gemini-live-2.5-flash-native-audio`, `gemini-2.0-flash-live-001` | `gemini-3.1-flash-live-preview` |
| `text-embedding-004`, `embedding-001` | `gemini-embedding-2` |
| `google-adk` 1.x pin, Python 3.11-only | `google-adk>=2.3.0,<3`, Python **3.10+**, `google-genai` v2.0.0+ |

Full old→new code samples: `references/api-changes.md`. Model/thinking/embedding
detail: `references/models-config.md`.

## Structural rules new/enforced in 2.3

- **`output_schema` XOR tools** — an `LlmAgent` with `output_schema` may not have
  tools, sub-agents, or transfer. Split reasoning leaves (schema) from tool leaves.
- **Agent modes** — `LlmAgent.mode: Literal['chat', 'task', 'single_turn']`.
- **Graph runtime** — `node()` functions + `Edge` instances + `JoinNode` fan-in
  (`google.adk.workflow`); `Workflow` exported top-level (`from google.adk import Workflow`).
- **HITL** — `request_input` tool pauses a run; resume reads `ctx.resume_inputs`.

## Data / state incompatibility

- **Session/state schema is not compatible** between 1.x and 2.3. Do not reuse
  1.x-persisted sessions; start fresh or migrate with the tools under
  `adk-python-v2.3/src/google/adk/sessions/migration/`.
- **Embedding spaces are incompatible** across embedding models — moving to
  `gemini-embedding-2` requires **re-embedding all stored vectors**.

## Migration procedure

1. Pin `google-adk>=2.3.0,<3` and `google-genai>=2.0.0`; set Python 3.10+.
2. Run the checklist grep-and-replace (start with imports, then call sites).
3. Convert any `GraphAgent`/`add_edge` graphs to `Workflow`/`Edge`/`JoinNode`.
4. Split any `LlmAgent` that has both `output_schema` and tools.
5. Update model IDs + `thinking_level`; drop sampling params on 3.x.
6. Re-embed stored vectors if changing embedding model.
7. Verify (below).

## Verify

```bash
# no deprecated symbols remain
grep -rnE "GraphAgent|add_edge\(|MCPToolset[^a-z]|ctx\.resume_data|@edge\b|thinking_budget|gemini-(2\.|1\.)" src/
python -c "import google.adk; print(google.adk.__version__)"   # 2.3.x
```

Then run the app / tests. Related skills: `adk-model-routing` (models + thinking),
`adk-embeddings` (embedding/DB migration), `adk-tools`/`adk-mcp` (tool/MCP APIs).
