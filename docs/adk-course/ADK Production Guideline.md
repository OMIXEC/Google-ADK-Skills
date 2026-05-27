**ADK Production Guideline**

Here is the complete production-ready Google ADK engineering reference, organized across all eight pillars you requested. The PDF artifact could not be finalized due to tool limits, but the full structured guide is below — copy-paste ready.

---

# **Google ADK Production-Ready Engineering Guide**

## **1 · Security Guardrails with Callbacks**

ADK's six callback hooks map directly to OWASP LLM Top-10 defenses. The architecture is a **three-layer pipeline**: validate input before the LLM sees it, authorize tools before any side effect, and sanitize output before the user receives it.[linkedin](https://www.linkedin.com/pulse/building-secure-ai-agents-hands-on-guide-google-adk-ameya-suvarna-cmwpc)[youtube](https://www.youtube.com/watch?v=j9YyZM2OBS8)

## **Callback Lifecycle**

| Hook | Trigger | Primary Defense | Returns to Block? |
| ----- | ----- | ----- | ----- |
| `before_agent_callback` | Agent start | Auth / rate-limit | `LlmResponse` |
| `after_agent_callback` | Agent end | Audit trail | No |
| `before_model_callback` | Pre-LLM | Prompt injection | `LlmResponse` |
| `after_model_callback` | Post-LLM | PII redaction | Modify in-place |
| `before_tool_callback` | Pre-tool | Authz / limits | `dict` error |
| `after_tool_callback` | Post-tool | Result filtering | Modify in-place |

## **Input Guardrail — Prompt Injection (LLM01)**

python  
`import re`  
`from typing import Optional`  
`from google.adk.agents.callback_context import CallbackContext`  
`from google.adk.models import LlmRequest, LlmResponse`  
`from google.genai import types`

`INJECTION_PATTERNS = [`  
    `r"ignore previous instructions",`  
    `r"system prompt",`  
    `r"forget your instructions",`  
    `r"jailbreak",`  
    `r"act as (DAN|an? unrestricted)",`  
`]`

`def input_guardrail(`  
    `callback_context: CallbackContext,`  
    `llm_request: LlmRequest,`  
`) -> Optional[LlmResponse]:`  
    `if not llm_request.contents:`  
        `return None`  
    `text = (llm_request.contents[-1].parts[0].text or "").lower()`  
    `for pattern in INJECTION_PATTERNS:`  
        `if re.search(pattern, text):`  
            `callback_context.state["security_blocked"] = True`  
            `return LlmResponse(`  
                `content=types.Content(parts=[`  
                    `types.Part(text="Request blocked: policy violation.")`  
                `])`  
            `)`  
    `return None`

## **Tool Guardrail — Excessive Agency (LLM06)**

python  
`TOOL_LIMITS = {`  
    `"transfer_funds": {"max_amount": 1_000.0},`  
    `"send_email":     {"max_recipients": 5},`  
    `"delete_records": {"requires_confirmation": True},`  
`}`

`def tool_guardrail(tool, args, tool_context):`  
    `limits = TOOL_LIMITS.get(tool.name)`  
    `if not limits:`  
        `return None`  
    `if "max_amount" in limits:`  
        `if float(args.get("amount", 0)) > limits["max_amount"]:`  
            `return {"error": f"Exceeds limit ${limits['max_amount']:.0f}"}`  
    `if limits.get("requires_confirmation"):`  
        `if not tool_context.state.get("user_confirmed"):`  
            `return {"error": "Tool requires explicit user confirmation."}`  
    `return None`

## **Output Guardrail — PII Redaction (LLM02)**

python  
`PII_PATTERNS = {`  
    `"credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",`  
    `"ssn":         r"\b\d{3}-\d{2}-\d{4}\b",`  
    `"email":       r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",`  
`}`  
`REPLACEMENT = {"credit_card": "[CC-REDACTED]", "ssn": "[SSN-REDACTED]",`  
               `"email": "[EMAIL-REDACTED]"}`

`def output_guardrail(callback_context, llm_response):`  
    `if not (llm_response.content and llm_response.content.parts):`  
        `return None`  
    `text = llm_response.content.parts[0].text or ""`  
    `for name, pattern in PII_PATTERNS.items():`  
        `text = re.sub(pattern, REPLACEMENT[name], text)`  
    `llm_response.content.parts[0].text = text`  
    `return None  # Modified in-place`

## **Enterprise Plugins & Model Armor**

For 10+ agents, use a `Plugin` to apply guardrails globally instead of per-agent. Google Cloud **Model Armor** adds administrator-level jailbreak and toxicity filtering as a second enforcement layer — integrate it by calling the REST API inside `before_model_callback`.[youtube](https://www.youtube.com/watch?v=j9YyZM2OBS8)

python  
`from google.adk.plugins import BasePlugin`

`class SecurityPlugin(BasePlugin):`  
    `name = "security_plugin"`  
    `async def before_model_callback(self, ctx, req): return input_guardrail(ctx, req)`  
    `async def before_tool_callback(self, tool, args, ctx): return tool_guardrail(tool, args, ctx)`  
    `async def after_model_callback(self, ctx, res): return output_guardrail(ctx, res)`

`agent = LlmAgent(name="prod_agent", model="gemini-2.5-flash",`  
                 `tools=[...], plugins=[SecurityPlugin()])`

⚠️ **Never** rely solely on LLM self-refusal. Always combine `before_model_callback` \+ `before_tool_callback` \+ Model Armor as complementary layers.

---

## **2 · Observability — OpenTelemetry & Dynatrace**

ADK natively emits OpenTelemetry spans for every LLM call, tool invocation, and agent handoff. Google Cloud Trace is the default backend; Dynatrace (extension released March 2026\) provides AI agent topology dashboards, cost-per-interaction metrics, and SLA alerting.cloud.google+1

## **OTel Setup — Cloud Trace Backend**

python  
*`# pip install google-adk[opentelemetry] opentelemetry-exporter-gcp-trace`*  
`from opentelemetry import trace`  
`from opentelemetry.sdk.trace import TracerProvider`  
`from opentelemetry.sdk.trace.export import BatchSpanProcessor`  
`from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter`  
`from opentelemetry.sdk.resources import Resource, SERVICE_NAME`

`resource = Resource({SERVICE_NAME: "adk-production-agent"})`  
`provider = TracerProvider(resource=resource)`  
`exporter = CloudTraceSpanExporter(project_id="your-project-id")`  
`provider.add_span_processor(BatchSpanProcessor(exporter))`  
`trace.set_tracer_provider(provider)`  
*`# ADK auto-detects the provider — no extra config needed`*

## **Dynatrace OTLP Export**

python  
`from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter`

`otlp = OTLPSpanExporter(`  
    `endpoint="https://<env>.live.dynatrace.com/api/v2/otlp/v1/traces",`  
    `headers={"Authorization": f"Api-Token {os.environ['DT_API_TOKEN']}"},`  
`)`  
`provider.add_span_processor(BatchSpanProcessor(otlp))`  
*`# Dynatrace maps: call_llm → LLM node | execute_tool → Tool node`*

## **Custom Span Enrichment via Callbacks**

python  
`from opentelemetry import trace as otel_trace`

`def before_tool_callback_otel(tool, args, tool_context):`  
    `span = otel_trace.get_current_span()`  
    `span.set_attribute("adk.tool.name", tool.name)`  
    `span.set_attribute("adk.session.id", tool_context.session.id)`  
    `span.set_attribute("adk.user.id", tool_context.session.user_id)`  
    `return None`

`def after_model_callback_otel(callback_context, llm_response):`  
    `if llm_response.usage_metadata:`  
        `span = otel_trace.get_current_span()`  
        `span.set_attribute("adk.llm.input_tokens",`  
                           `llm_response.usage_metadata.prompt_token_count)`  
        `span.set_attribute("adk.llm.output_tokens",`  
                           `llm_response.usage_metadata.candidates_token_count)`  
    `return None`

## **Key Metrics to Alert On**

| Metric | Span Attribute | Alert Threshold |
| ----- | ----- | ----- |
| LLM Latency p99 | `call_llm` duration | \> 8 seconds |
| Tool Failure Rate | `execute_tool` status=ERROR | \> 2% |
| Token Input / Turn | `adk.llm.input_tokens` | \> 30k |
| Agent Retries | `adk.agent.retry_count` | \> 3 per session |
| Blocked Requests | `security_blocked=true` | \> 0.5% traffic |
| Memory Fetch Latency | `memory_service.query` | \> 500ms |

📝 Filter Cloud Trace by `span.name='call_llm'` to isolate pure model latency from tool I/O overhead.[cloud.google](https://docs.cloud.google.com/stackdriver/docs/instrumentation/ai-agent-adk)

---

## **3 · Memory Management**

ADK separates memory into three layers:cloud.google+1

| Layer | Class | Persistence | Use For |
| ----- | ----- | ----- | ----- |
| Turn State | `session.state` dict | Single turn | Tool→agent params |
| Session History | `session.events` | Session lifetime | Conversation context |
| Session (Dev) | `InMemorySessionService` | In-process only | Unit tests only |
| Session (Prod) | `VertexAiSessionService` | Cloud-persisted | All production |
| Long-Term Memory | `VertexAiMemoryBankService` | Permanent | User prefs, past facts |

## **VertexAI Session Service (Production)**

python  
`from google.adk import Runner`  
`from google.adk.sessions import VertexAiSessionService`  
`import vertexai`

`vertexai.init(project="your-project-id", location="us-central1")`  
`client = vertexai.Client(project="your-project-id", location="us-central1")`  
`agent_engine = client.agent_engines.create()`  
`agent_engine_id = agent_engine.api_resource.name.split("/")[-1]`

`session_service = VertexAiSessionService(`  
    `project="your-project-id",`  
    `location="us-central1",`  
    `agent_engine_id=agent_engine_id,`  
`)`  
`runner = Runner(agent=root_agent, app_name="prod-app",`  
                `session_service=session_service)`

`session = await session_service.create_session(`  
    `app_name="prod-app", user_id="user-abc-123",`  
    `state={"preferred_language": "en", "user_tier": "premium"},`  
`)`

## **Long-Term Memory Bank**

python  
`from google.adk.memory import VertexAiMemoryBankService`

`memory_service = VertexAiMemoryBankService(`  
    `project="your-project-id", location="us-central1",`  
    `agent_engine_id=agent_engine_id,`  
`)`  
`runner = Runner(agent=root_agent, app_name="prod-app",`  
                `session_service=session_service,`  
                `memory_service=memory_service)`

*`# After session ends — distill events into long-term facts`*  
`await memory_service.add_session_to_memory(session)`

*`# Manual retrieval`*  
`results = await memory_service.search_memory(`  
    `app_name="prod-app", user_id="user-abc-123",`  
    `query="user's preferred payment method",`  
`)`

**State Key Conventions:**

* `temp:*` — cleared between turns (e.g., `temp:tool_result`)  
* `user:*` — user-level settings (e.g., `user:language`)  
* `audit:*` — immutable audit trail entries  
  ⚠️ `InMemorySessionService` is not suitable for Cloud Run (stateless containers) — all sessions are lost on pod restart.[cloud.google](https://cloud.google.com/blog/topics/developers-practitioners/remember-this-agent-state-and-memory-with-adk)

---

## **4 · Logging to Cloud Trace**

Correlate structured logs with OTel trace context so you can click from a Cloud Trace span directly to the associated Cloud Logging entry.signoz+1

python  
`import logging, json`  
`import google.cloud.logging`  
`from opentelemetry import trace as otel_trace`

`log_client = google.cloud.logging.Client(project="your-project-id")`  
`log_client.setup_logging()`  
`logger = logging.getLogger("adk.agent")`

`def log_agent_event(event_type: str, context: dict):`  
    `span = otel_trace.get_current_span()`  
    `ctx  = span.get_span_context()`  
    `entry = {`  
        `"event_type": event_type,`  
        `"trace_id":   format(ctx.trace_id, "032x") if ctx.is_valid else None,`  
        `"span_id":    format(ctx.span_id, "016x") if ctx.is_valid else None,`  
        `**context,`  
    `}`  
    `logger.info(json.dumps(entry), extra={"json_fields": entry})`

## **Cloud Trace Filter Recipes**

| Scenario | Filter |
| ----- | ----- |
| LLM calls for a session | `span.name='call_llm' AND labels.session_id='ID'` |
| Blocked security events | `jsonPayload.event_type='security_blocked'` |
| Slow tool calls (\>2s) | `span.name='execute_tool' AND duration_ms > 2000` |
| High token turns | `jsonPayload.input_tokens > 20000` |
| User session trace | `labels.user_id='user-abc-123' AND span.name='agent_run'` |

---

## **5 · FastAPI Deployment Best Practices**

ADK's `get_fast_api_app()` auto-wires Runner, SessionService, and streaming endpoints. Layer it with Gunicorn \+ Uvicorn workers, security middleware, and proper Cloud Run configuration.github+1

## **Production App Bootstrap**

python  
*`# main.py`*  
`import os`  
`import uvicorn`  
`from fastapi import FastAPI`  
`from fastapi.middleware.cors import CORSMiddleware`  
`from fastapi.middleware.trustedhost import TrustedHostMiddleware`  
`from google.adk.cli.fast_api import get_fast_api_app`

`ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")`  
`SESSION_DB = os.getenv("SESSION_DB_URL")  # PostgreSQL, not SQLite`

`app: FastAPI = get_fast_api_app(`  
    `agent_dir=os.path.dirname(__file__),`  
    `session_db_url=SESSION_DB,`  
    `allow_origins=ALLOWED_ORIGINS,  # Never use ["*"] in production`  
    `web=False,                       # Disable dev UI in production`  
`)`

`app.add_middleware(TrustedHostMiddleware,`  
                   `allowed_hosts=["*.run.app", "api.yourapp.com"])`  
`app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS,`  
                   `allow_methods=["POST", "GET"],`  
                   `allow_headers=["Authorization", "Content-Type"])`

`@app.get("/health")`  
`async def health(): return {"status": "ok"}`

`@app.get("/ready")`  
`async def readiness(): return {"status": "ready"}`

`if __name__ == "__main__":`  
    `uvicorn.run("main:app", host="0.0.0.0", port=8080,`  
                `workers=1, loop="uvloop")`

## **Dockerfile (Production-Hardened)**

text  
`FROM python:3.11-slim`  
`RUN groupadd -r adk && useradd -r -g adk adk`  
`WORKDIR /app`  
`COPY requirements.txt .`  
`RUN pip install --no-cache-dir -r requirements.txt`  
`COPY . .`  
`RUN chown -R adk:adk /app`  
`USER adk`  
`CMD ["gunicorn", "main:app",`  
     `"--workers", "2",`  
     `"--worker-class", "uvicorn.workers.UvicornWorker",`  
     `"--bind", "0.0.0.0:8080",`  
     `"--timeout", "120",`  
     `"--keepalive", "5"]`

## **Cloud Run Configuration**

| Setting | Recommended Value | Reason |
| ----- | ----- | ----- |
| Min instances | ≥ 1 | Avoid cold start on streaming |
| Request timeout | 120–300s | Multi-step agentic tasks |
| CPU always-on | Enabled | Prevent mid-stream CPU throttle |
| Memory | 1GB+ | Tool caches, in-memory buffers |
| Service Account | Least privilege | Vertex AI User \+ Trace Agent only |
| Session DB | Cloud SQL (PostgreSQL) | HA, not SQLite |
| Secrets | Secret Manager mounts | Never plaintext env vars |

---

## **6 · Multi-Agent Workflows**

ADK supports four orchestration patterns:[youngju](https://www.youngju.dev/blog/ai-platform/2026-04-12-google-adk-practical-guide.en)

| Pattern | Class | Use Case |
| ----- | ----- | ----- |
| Sequential | `SequentialAgent` | ETL pipelines, ordered steps |
| Parallel | `ParallelAgent` | Multi-source fan-out |
| Hierarchical | `LlmAgent` as orchestrator | Domain specialist routing |
| Loop | `LoopAgent` | Iterative refinement |
| A2A Remote | `A2AClient` tool | Cross-service agent calls |

## **Hierarchical Orchestrator**

python  
`from google.adk.agents import LlmAgent`

`research_agent = LlmAgent(`  
    `name="research_agent", model="gemini-2.5-flash",`  
    `description="Searches web for factual information",`  
    `tools=[google_search_tool],`  
    `before_model_callback=input_guardrail,`  
    `before_tool_callback=tool_guardrail,`  
`)`  
`analysis_agent = LlmAgent(`  
    `name="analysis_agent", model="gemini-2.5-pro",`  
    `description="Performs deep analysis on provided data",`  
`)`  
`orchestrator = LlmAgent(`  
    `name="orchestrator", model="gemini-2.5-flash",`  
    `instruction="Route research tasks to research_agent, analysis to analysis_agent.",`  
    `sub_agents=[research_agent, analysis_agent],`  
    `plugins=[SecurityPlugin()],  # Cascades to all sub-agents`  
`)`

## **A2A Security Requirements**

* Authenticate inter-agent calls with **service-account JWT tokens**, not API keys[youtube](https://www.youtube.com/watch?v=j9YyZM2OBS8)  
* Enforce **HTTPS** everywhere — Cloud Run auto-provisions TLS  
* Validate calling agent identity in `before_agent_callback` on the receiving side  
* Log every A2A call with: source agent, target agent, user\_id, and latency

---

## **7 · Cost & Latency Auditing Callbacks**

The `after_model_callback` captures `usage_metadata` directly from LlmResponse.dev+1

## **Full Cost \+ Latency Tracker**

python  
`import time, json`  
`from typing import Optional`

`COST_PER_1M_INPUT  = 0.075   # USD — Gemini 2.5 Flash (verify current rates)`  
`COST_PER_1M_OUTPUT = 0.30`  
`MAX_COST_PER_SESSION = 0.50  # Hard budget cap per session`

`def before_model_callback_timer(callback_context, llm_request):`  
    `callback_context.state["llm_start_time"] = time.monotonic()`  
    `return None`

`def after_model_callback_cost(callback_context, llm_response):`  
    `latency_ms = (time.monotonic() -`  
                  `callback_context.state.pop("llm_start_time", 0)) * 1000`  
    `usage = llm_response.usage_metadata`  
    `if not usage: return None`

    `input_t  = usage.prompt_token_count or 0`  
    `output_t = usage.candidates_token_count or 0`  
    `call_cost = (input_t / 1_000_000 * COST_PER_1M_INPUT +`  
                 `output_t / 1_000_000 * COST_PER_1M_OUTPUT)`

    `s = callback_context.state`  
    `s["total_input_tokens"]  = s.get("total_input_tokens",  0) + input_t`  
    `s["total_output_tokens"] = s.get("total_output_tokens", 0) + output_t`  
    `s["total_cost_usd"]      = s.get("total_cost_usd",    0.0) + call_cost`  
    `s["total_llm_calls"]     = s.get("total_llm_calls",     0) + 1`

    `log_agent_event("llm_call_metered", {`  
        `"input_tokens": input_t, "output_tokens": output_t,`  
        `"latency_ms": round(latency_ms, 1),`  
        `"call_cost_usd": round(call_cost, 6),`  
        `"session_cost_usd": round(s["total_cost_usd"], 4),`  
    `})`  
    `# Hard budget guard`  
    `if s["total_cost_usd"] > MAX_COST_PER_SESSION:`  
        `return LlmResponse(content=types.Content(parts=[`  
            `types.Part(text="Session budget exceeded. Please start a new session.")`  
        `]))`  
    `return None`

**Latency Optimization Strategies**:youngju+1

* Use `gemini-2.5-flash` for routing/guardrail checks; reserve Pro for complex reasoning  
* **Short-circuit** in `before_model_callback` when session state already has the answer  
* **Cache** deterministic tool results in `session.state` with a TTL timestamp  
* Set `max_output_tokens` per agent to prevent runaway verbose responses  
* Use **streaming** (`/run_sse`) to improve perceived latency for end users  
* Monitor **p50/p95/p99 latency separately** — outliers hide in averages

---

## **8 · Agent Quality Evaluation Checklists**

Use these gates before promoting any ADK agent to production.dev+1

## **🔒 Security Readiness**

* ☐ `before_model_callback` implements injection detection with tested regex patterns  
* ☐ `before_tool_callback` enforces parameter limits for all side-effectful tools  
* ☐ `after_model_callback` redacts PII patterns (CC, SSN, email, phone) from all outputs  
* ☐ `SecurityPlugin` registered and covers all agents (not just root)  
* ☐ Model Armor enabled for regulated workloads (finance, healthcare, legal)  
* ☐ Service Account uses least-privilege IAM — no owner/editor roles  
* ☐ All secrets in Secret Manager — never in code or environment variables  
* ☐ CORS origins explicitly allowlisted — no wildcard `*` in production  
* ☐ A2A calls authenticated with service-account JWT tokens  
* ☐ Security callback test suite with adversarial prompt fixtures passes 100%  
* ☐ Rate limiting enabled per `user_id` to prevent abuse

## **📊 Observability & Monitoring**

* ☐ OTel `TracerProvider` configured with `BatchSpanProcessor` (not `Simple`)  
* ☐ Cloud Trace / Dynatrace backend receiving spans from staging  
* ☐ Custom span attributes: `session_id`, `user_id`, `agent_name` on every span  
* ☐ `after_model_callback` captures `input_tokens` and `output_tokens` per call  
* ☐ Structured JSON logs emitted to Cloud Logging with trace correlation  
* ☐ Alerts set: p99 latency \> 8s, error rate \> 2%, blocked requests \> 0.5%  
* ☐ Cost dashboard configured with per-agent, per-user breakdowns  
* ☐ Dynatrace ADK extension displaying AI service topology

## **🧠 Memory & Session Management**

* ☐ `InMemorySessionService` replaced with `VertexAiSessionService` in all envs  
* ☐ `VertexAiMemoryBankService` configured for cross-session recall  
* ☐ `add_session_to_memory()` called at session end  
* ☐ Session state key naming convention documented (`temp:`, `user:`, `audit:`)  
* ☐ Session TTL / `max_events` policy configured to bound context window costs  
* ☐ Session data does not persist PII beyond minimum required retention period

## **🚀 FastAPI & Deployment**

* ☐ Dockerfile uses non-root user, no secrets in image layers  
* ☐ Gunicorn \+ `UvicornWorker` used — not `uvicorn --reload`  
* ☐ PostgreSQL (Cloud SQL) used for `session_db_url` — not SQLite  
* ☐ Cloud Run `min-instances ≥ 1` with CPU always-on for streaming  
* ☐ `/health` and `/ready` respond within 1 second  
* ☐ `web=False` (ADK dev UI disabled) in production  
* ☐ Canary or blue/green deployment configured for zero-downtime updates  
* ☐ Container image scanning (Artifact Analysis) enabled in CI/CD

## **🤖 Multi-Agent Workflow Quality**

* ☐ All sub-agents have explicit `description` fields (used by orchestrator for routing)  
* ☐ `SecurityPlugin` applied at orchestrator level (cascades to sub-agents)  
* ☐ Sub-agent state handoff documented and tested (key conventions)  
* ☐ Maximum delegation depth set to prevent infinite loops  
* ☐ A2A endpoint URLs in config, not hardcoded in agent definitions  
* ☐ Agent-to-agent calls logged with source, target, and correlation IDs

## **✅ LLM Response Quality Gates**

* ☐ Factual accuracy evaluated on domain-specific golden dataset (≥ 85% pass rate)  
* ☐ Instruction-following tested with adversarial edge cases  
* ☐ Tool call accuracy: correct tool selected with correct parameters  
* ☐ Multi-turn coherence tested across ≥ 10 turns  
* ☐ Latency SLA verified under load: p50 \< 3s, p95 \< 8s, p99 \< 15s  
* ☐ Cost per interaction within budget target (e.g. \< $0.05 per turn)  
* ☐ Regression test suite added to CI/CD on every agent code change  
* ☐ Fallback behavior defined for empty/malformed LLM responses

---

## **Quick-Reference Requirements**

text  
`google-adk[opentelemetry,vertexai]`  
`opentelemetry-exporter-gcp-trace`  
`opentelemetry-exporter-otlp-proto-grpc`  
`google-cloud-logging`  
`google-cloud-trace`  
`gunicorn`  
`uvloop`  
`fastapi`

The Dynatrace ADK Observability hub extension (March 2026\) provides zero-config AI service topology, agent health dashboards, and cost monitoring out of the box once your OTLP exporter is pointed at the Dynatrace endpoint. The OTel instrumentation guide on Google Cloud Observability confirms that ADK applications auto-emit `call_llm` and `execute_tool` spans without manual instrumentation — you only need to set the tracer provider.dynatrace+2

There are five production-grade MemoryService backends for Google ADK, each suited for different scale, architecture, and retrieval needs — ranging from the managed Vertex AI Memory Bank to self-hosted vector databases.adk+2

## **The `BaseMemoryService` Contract**

ADK defines only the interface for long-term memory — the storage backend is entirely up to you. Any backend must implement two async methods:[milvus](https://milvus.io/blog/how-to-build-productionready-ai-agents-with-longterm-memory-using-google-adk-and-milvus.md)

python  
`from google.adk.memory import BaseMemoryService`

`class MyMemoryService(BaseMemoryService):`  
    `async def add_session_to_memory(self, session: Session) -> None:`  
        `# Distill session events into persistent storage`  
        `...`

    `async def search_memory(`  
        `self, *, app_name: str, user_id: str, query: str`  
    `) -> SearchMemoryResponse:`  
        `# Semantic or keyword retrieval, scoped by user_id`  
        `...`

The `Runner` calls `search_memory` automatically before each agent turn and expects you to call `add_session_to_memory` at session end.[adk](https://adk.dev/sessions/memory/)

---

## **Backend Options at a Glance**

| Backend | Package | Retrieval Type | Managed? | Best For |
| ----- | ----- | ----- | ----- | ----- |
| `InMemoryMemoryService` | `google-adk` built-in | Exact match | No | Dev / unit tests only |
| `VertexAiMemoryBankService` | `google-adk[vertexai]` | Semantic (Vertex) | Yes (GCP) | GCP-native production |
| `adk-redis` | `adk-redis` | Semantic \+ hybrid | Self/Cloud | Low-latency, real-time |
| Milvus | `pymilvus` | Vector similarity | Self-hosted | Billion-scale, open-source |
| cognee | `cognee` | Graph \+ semantic | Self/Cloud | Knowledge graph memory |

---

## **1 · `VertexAiMemoryBankService` — GCP-Native (Recommended Default)**

The simplest path if you're already on GCP. Vertex AI manages embedding, storage, and retrieval:[adk](https://adk.dev/sessions/memory/)

python  
`from google.adk.memory import VertexAiMemoryBankService`  
`from google.adk import Runner`

`memory_service = VertexAiMemoryBankService(`  
    `project="your-project-id",`  
    `location="us-central1",`  
    `agent_engine_id=agent_engine_id,  # From VertexAiSessionService setup`  
`)`

`runner = Runner(`  
    `agent=root_agent,`  
    `app_name="prod-app",`  
    `session_service=session_service,`  
    `memory_service=memory_service,`  
`)`

*`# After each session ends — distill events into long-term facts`*  
`await memory_service.add_session_to_memory(completed_session)`

**Tradeoffs:** Zero infrastructure to manage; retrieval quality tied to Vertex AI embedding models; no customization of the index or scoring function.

---

## **2 · Redis (`adk-redis`) — Low-Latency Hybrid Search**

Redis Labs released the `adk-redis` package (April 2026\) implementing both `BaseMemoryService` and `BaseSessionService` using **Redis Agent Memory Server** \+ **RedisVL** for vector similarity, hybrid search, and semantic caching.redis+1

## **Three Integration Patterns[redis](https://redis.io/docs/latest/integrate/google-adk/integration-patterns/)**

**Pattern A — Framework-Managed (Invisible Infrastructure)**

python  
`from adk_redis.sessions import RedisWorkingMemorySessionService, RedisWorkingMemorySessionServiceConfig`  
`from adk_redis.memory import RedisLongTermMemoryService, RedisLongTermMemoryServiceConfig`

`runner = Runner(`  
    `agent=agent,`  
    `app_name="my_app",`  
    `session_service=RedisWorkingMemorySessionService(`  
        `config=RedisWorkingMemorySessionServiceConfig(`  
            `api_base_url="http://redis-agent-memory:8088",`  
            `default_namespace="my_app",`  
        `)`  
    `),`  
    `memory_service=RedisLongTermMemoryService(`  
        `config=RedisLongTermMemoryServiceConfig(`  
            `api_base_url="http://redis-agent-memory:8088",`  
            `default_namespace="my_app",`  
        `)`  
    `),`  
`)`

Memory extraction runs in the background; agent code never touches it directly.[redis](https://redis.io/docs/latest/integrate/google-adk/integration-patterns/)

**Pattern B — LLM-Controlled REST Tools**

python  
`from adk_redis.tools.memory import (`  
    `SearchMemoryTool, CreateMemoryTool,`  
    `UpdateMemoryTool, DeleteMemoryTool, MemoryToolConfig,`  
`)`

`config = MemoryToolConfig(`  
    `api_base_url="http://redis-agent-memory:8088",`  
    `default_namespace="my_app",`  
    `recency_boost=True,  # Newer memories rank higher`  
`)`

`agent = LlmAgent(`  
    `model="gemini-2.5-flash",`  
    `tools=[`  
        `SearchMemoryTool(config=config),`  
        `CreateMemoryTool(config=config),`  
        `UpdateMemoryTool(config=config),`  
        `DeleteMemoryTool(config=config),`  
    `],`  
`)`

The LLM decides *when* to search and *what* to persist — gives the agent genuine memory autonomy.[redis](https://redis.io/docs/latest/integrate/google-adk/integration-patterns/)

**Pattern C — MCP Tools (Most Portable)**

python  
`from adk_redis.tools.mcp_memory import create_memory_mcp_toolset`

`memory_tools = create_memory_mcp_toolset(`  
    `server_url="http://redis-agent-memory:9000",  # SSE endpoint`  
    `tool_filter=["search_long_term_memory", "create_long_term_memories"],`  
`)`  
*`# Swap backends without changing any agent code`*

Swap the Redis backend for any MCP-compatible memory server with zero agent changes.[redis](https://redis.io/docs/latest/integrate/google-adk/integration-patterns/)

**Hybrid (Most Powerful):** Combine framework-managed services on the `Runner` with LLM REST tools on the `Agent` — background auto-extraction plus explicit LLM CRUD control.[redis](https://redis.io/docs/latest/integrate/google-adk/integration-patterns/)

---

## **3 · Milvus — Billion-Scale Open-Source Vector DB**

Implement `BaseMemoryService` manually with Milvus as the storage layer. The key advantages are **hybrid queries** (vector similarity \+ scalar filter for `user_id` isolation), sub-10ms query latency at scale, and support for HNSW/DiskANN index types:[milvus](https://milvus.io/blog/how-to-build-productionready-ai-agents-with-longterm-memory-using-google-adk-and-milvus.md)

python  
`from pymilvus import connections, Collection`  
`import google.generativeai as genai`  
`from google.adk.memory import BaseMemoryService`

`class MilvusMemoryService(BaseMemoryService):`  
    `def __init__(self, collection: Collection, embedding_model: str):`  
        `self.collection = collection`  
        `self.embedding_model = embedding_model`

    `async def add_session_to_memory(self, session):`  
        `# Extract text from session events, embed, and insert`  
        `for event in session.events:`  
            `if event.content and event.content.parts:`  
                `text = event.content.parts[0].text or ""`  
                `embedding = genai.embed_content(`  
                    `model=self.embedding_model, content=text,`  
                    `task_type="retrieval_document",`  
                `)["embedding"]`  
                `self.collection.insert([{`  
                    `"user_id": session.user_id,`  
                    `"session_id": session.id,`  
                    `"content": text,`  
                    `"embedding": embedding,`  
                `}])`  
        `self.collection.flush()`

    `async def search_memory(self, *, app_name, user_id, query):`  
        `query_vec = genai.embed_content(`  
            `model=self.embedding_model, content=query,`  
            `task_type="retrieval_query",`  
        `)["embedding"]`  
        `self.collection.load()`  
        `results = self.collection.search(`  
            `data=[query_vec],`  
            `anns_field="embedding",`  
            `param={"metric_type": "COSINE", "params": {"nprobe": 10}},`  
            `limit=5,`  
            `expr=f'user_id == "{user_id}"',  # Strict user isolation`  
            `output_fields=["content"],`  
        `)`  
        `# Wrap in SearchMemoryResponse...`

The `expr=f'user_id == "{user_id}"'` filter is the critical line for **user isolation** — it prevents cross-user memory leakage at the query level, not the application level.[milvus](https://milvus.io/blog/how-to-build-productionready-ai-agents-with-longterm-memory-using-google-adk-and-milvus.md)

---

## **4 · Firestore Custom Backend — GCP-Native Scalable NoSQL**

Best when you want GCP-managed infrastructure without Vertex AI Memory Bank, or need structured document storage alongside semantic retrieval:

python  
`from google.cloud import firestore`  
`from google.adk.memory import BaseMemoryService`

`class FirestoreMemoryService(BaseMemoryService):`  
    `def __init__(self, project_id: str):`  
        `self.db = firestore.AsyncClient(project=project_id)`

    `async def add_session_to_memory(self, session):`  
        `doc_ref = (`  
            `self.db.collection("memories")`  
                   `.document(session.user_id)`  
                   `.collection("facts")`  
                   `.document()`  
        `)`  
        `# Store distilled facts as structured documents`  
        `await doc_ref.set({`  
            `"session_id": session.id,`  
            `"events": [str(e) for e in session.events[-20:]],`  
            `"created_at": firestore.SERVER_TIMESTAMP,`  
        `})`

    `async def search_memory(self, *, app_name, user_id, query):`  
        `# Use Firestore full-text search or integrate Vertex AI`  
        `# Matching for semantic queries`  
        `docs = await (`  
            `self.db.collection("memories")`  
                   `.document(user_id)`  
                   `.collection("facts")`  
                   `.order_by("created_at", direction=firestore.Query.DESCENDING)`  
                   `.limit(10)`  
                   `.get()`  
        `)`  
        `# Combine with Vertex AI embedding match for semantic ranking`  
        `...`

📝 Firestore alone provides recency-based retrieval. For semantic search, combine it with Vertex AI Matching Engine embeddings indexed separately.

---

## **5 · Scoping Rules Across All Backends**

Regardless of backend, ADK's **prefix-based scoping** determines data visibility:[milvus](https://milvus.io/blog/how-to-build-productionready-ai-agents-with-longterm-memory-using-google-adk-and-milvus.md)

| Prefix | Scope | Cleared When |
| :---: | :---: | :---: |

| Prefix | Scope | Cleared When |
| ----- | ----- | ----- |
| `temp:key` | Current session only | Session ends (auto) |
| `user:key` | All sessions for this `user_id` | Manual delete |
| `app:key` | All users, all sessions | Manual delete |

Your `add_session_to_memory` implementation must respect these prefixes to correctly bucket what gets promoted to long-term storage vs. discarded.

---

## **Decision Guide**

* **GCP-only, minimal ops** → `VertexAiMemoryBankService`  
* **Low latency \+ semantic caching \+ real-time** → `adk-redis` (framework or hybrid pattern)  
* **Large-scale open-source, billions of memories, strict user isolation** → Milvus custom backend  
* **Need LLM to control its own memory explicitly** → `adk-redis` REST tools or MCP pattern  
* **Knowledge graph / relationship memory** → cognee integration[cognee](https://www.cognee.ai/blog/integrations/google-adk-cognee-integration-build-agents-with-persistent-memory)  
* **Already on Firestore / Cloud SQL** → Custom `BaseMemoryService` wrapping existing DB

