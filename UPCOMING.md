# Upcoming Enhancements — ADK Skills Curriculum Alignment

Cross-reference audit of `adk-agentic-prod-workflows` against `docs/adk-course/` curriculum standards. Prioritized by production impact.

## CRITICAL (blocks production use)

### Model Armor Integration (zero coverage)

`docs/adk-course/adk-model-armor-security-guide.md` has complete implementation: 4 template configs, REST API wrapper, agent runner with double-shield, 6-phase 48-item production checklist, quota formula, floor settings, anti-patterns. Skill's `references/security-guardrails.md` has input validation but never mentions Model Armor.

Create `references/model-armor.md` with: architecture diagram, REST API wrapper code, 4 production templates, quota formula `(peak_users * avg_turns) * 2 + 25%`, 6-phase checklist. Wire into SKILL.md under production deployment.

### ADK Plugin System (SecurityPlugin)

`ADK Production Guideline.md` L97-113 shows `BasePlugin` subclass cascading `input_guardrail`, `tool_guardrail`, `output_guardrail` to all sub-agents. Skill covers per-agent callbacks but not Plugin system for global enforcement.

Add to `references/security-guardrails.md`: `SecurityPlugin(BasePlugin)` pattern, how plugins cascade to sub-agents, when Plugin vs per-agent callbacks.

## HIGH PRIORITY (should fix before first user)

### Cost & Latency Auditing Callbacks

`ADK Production Guideline.md` L407-455 has `before_model_callback_timer` + `after_model_callback_cost` with `usage_metadata`, per-session budget cap, hard budget guard returning `LlmResponse`. Skill has no cost-per-call tracking.

Add to `references/observability.md`: cost tracking callback pair, `COST_PER_1M_INPUT`/`COST_PER_1M_OUTPUT` constants, `MAX_COST_PER_SESSION` guard, latency histogram.

### Continuous Learning Pattern

`adk-continues-learning.md` L31-45: `PreloadMemoryTool` on entry + `after_agent_callback` auto-save on exit. Skill's `references/memory-management.md` mentions `add_session_to_memory` but not auto-save callback.

Add to `references/memory-management.md`: continuous learning section with auto-save callback, PreloadMemoryTool registration, preload-on-entry + save-on-exit diagram.

### Structured JSON Logging with Trace Correlation

`ADK Production Guideline.md` L258-278: `log_agent_event()` embeds `trace_id` and `span_id` from OTel into every JSON log entry with `json_fields` extra. Skill's `references/observability.md` has logging but no trace-log correlation.

Add to `references/observability.md`: structured logging with trace correlation, `google.cloud.logging` setup, Cloud Trace filter recipes.

### FastAPI Production Bootstrap

`ADK Production Guideline.md` L286-362: production FastAPI bootstrap with `get_fast_api_app()`, `TrustedHostMiddleware`, CORS, `/health` + `/ready` endpoints, security-hardened Dockerfile (non-root user, gunicorn, uvicorn worker, keepalive), Cloud Run configuration table.

Add to `references/deployment-matrix.md` or `assets/`: production FastAPI bootstrap, security-hardened Dockerfile, Cloud Run config table.

### ADK Built-in Eval Framework

`ADK Eval Guide.md`: 4-step eval with `AgentEvaluator.evaluate()`, ROUGE metric for final response, 6 trajectory evaluation methods (exact, in-order, any-order, precision, recall, single-tool), `*.test.json` vs evalsets, pytest integration.

Add to `references/testing-strategies.md`: ADK native eval section covering AgentEvaluator, ROUGE scoring, trajectory matching methods, `*.test.json` format, pytest integration, Web UI eval tab.

### Redis Memory (adk-redis)

`ADK Production Guideline.md` L617-688: 3 integration patterns (Framework-Managed, LLM-Controlled REST Tools, MCP Tools). Skill covers VertexAiMemoryBankService but not adk-redis.

Add to `references/memory-management.md`: Redis section with 3 patterns, RedisVL, semantic caching, hybrid search.

## MEDIUM PRIORITY (improve over time)

### Production Checklists

`ADK Production Guideline.md` L462-535: 48-item checklist across Security (11), Observability (8), Memory (6), FastAPI (8), Multi-Agent (6), LLM Quality (8).

Create `references/production-checklist.md` with full 6-section checklist, or add as appendix to SKILL.md.

### Human-in-the-Loop Implementation

`MAS-Memory-RAG.md` L84-88 describes HITL as critical for high-stakes operations. Skill mentions HITL briefly but no concrete implementation.

Add to `references/adk-workflows.md`: HITL implementation with approval tool, checkpoint pattern, user confirmation flow.

### Custom Memory Backend Implementations

`ADK Production Guideline.md`: Milvus (billion-scale vector DB), Firestore (GCP NoSQL), cognee (knowledge graph). Skill only covers Vertex AI Memory Bank.

Add to `references/memory-management.md`: custom backend examples (Milvus `expr=f'user_id == "{user_id}"'` user isolation, Firestore async client, cognee graph memory).

### Professional Agent Reasoning Taxonomy

`MAS-Memory-RAG.md` classifies agents by reasoning architecture: Router, ReAct (Thought->Action->Observation), Plan-and-Execute. Skill's `references/agent-modes.md` covers ADK class types but not reasoning architecture.

Add to `references/agent-modes.md`: reasoning architecture section (Router vs ReAct vs Plan-Execute), when to use each, ADK class mappings.

## Template Coverage Gaps

- **Go**: Only graph-workflow exists. Missing: dynamic, collaborative, template-sequential, template-parallel
- **TS**: Only workflow-client and agent-server. Missing: agent-side templates for dynamic, collaborative, parallel, sequential, loop
- **LoopAgent/CycleAgent**: No template in any language beyond Python template-loop

## Recommended New Files

| File | Purpose |
|------|---------|
| `references/model-armor.md` | Full Model Armor integration: architecture, 4 templates, REST API wrapper, double-shield runner, 6-phase checklist, quota formula |
| `references/production-checklist.md` | 48-item 6-section pre-production quality gate |

## Recommended File Updates

| File | Add Section |
|------|-------------|
| `references/security-guardrails.md` | Plugin system (SecurityPlugin), Model Armor integration pointer |
| `references/observability.md` | Cost/latency tracking callbacks, structured logging with trace correlation |
| `references/memory-management.md` | Continuous learning (auto-save + preload), adk-redis 3 patterns, Milvus/Firestore/cognee backends |
| `references/deployment-matrix.md` | FastAPI production bootstrap, security-hardened Dockerfile |
| `references/testing-strategies.md` | ADK native eval framework (AgentEvaluator, ROUGE, trajectory methods, *.test.json) |
| `references/adk-workflows.md` | HITL implementation pattern |
| `references/agent-modes.md` | Reasoning architecture taxonomy (Router/ReAct/Plan-Execute) |

## Orchestration Recommendation

Wire into auto-run per project:

- `init_adk_workflow.py`: Add `--with-model-armor` flag generating `security/model_armor.py`, template JSONs, shielded runner
- `SKILL.md`: Add Model Armor to reference loading table, production checklist to validation section
- `compose_workflow.py`: Add cost/latency tracking callback injection into generated workflows
- Post-generation: Run production checklist as post-scaffold gate
