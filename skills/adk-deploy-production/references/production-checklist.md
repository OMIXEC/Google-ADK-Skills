# Production Readiness Checklist — ADK Agentic Workflows

48-item pre-production quality gate across 6 domains. Every item must pass before deploying to production. Block deploy on any unchecked item in Security section.

## Security (11 items)

- [ ] **S-01** Input validation at all entry points (Pydantic schemas + validators)
- [ ] **S-02** Content safety guardrails on user input AND model output (Model Armor double-shield)
- [ ] **S-03** All tools declare required permissions (`ToolPermissions` scoping)
- [ ] **S-04** No hardcoded secrets — all via env/Secret Manager
- [ ] **S-05** Secrets excluded from logs, error messages, and model context
- [ ] **S-06** Rate limiting on external API tools (token bucket, 60 calls/min default)
- [ ] **S-07** Auth middleware verifies JWT/OIDC on all sensitive endpoints
- [ ] **S-08** RLS or equivalent per-tenant isolation enabled on all databases
- [ ] **S-09** Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options) configured
- [ ] **S-10** CORS restricted to specific origins (never `*` in production)
- [ ] **S-11** MCP tool_filter allowlists only needed tools (never expose all MCP server tools)

## Observability (8 items)

- [ ] **O-01** Correlation ID generated at workflow entry and propagated to all nodes/tools
- [ ] **O-02** Every tool call logs: tool name, call_id, latency_ms, status
- [ ] **O-03** Every agent delegation logs: from agent, to agent, reason, correlation_id
- [ ] **O-04** Workflow start/end logged with total duration
- [ ] **O-05** Errors logged with full context (no secrets)
- [ ] **O-06** Metrics exported: workflow_duration_ms, node_errors_total, token_usage_total
- [ ] **O-07** Cost tracking enabled: per-session budget cap, per-node token accounting
- [ ] **O-08** Structured JSON logging with trace correlation (OTel trace_id + span_id in every entry)

## Memory & State (6 items)

- [ ] **M-01** SessionService backend matches scale: Firestore (serverless), Spanner (global), Redis (caching)
- [ ] **M-02** State keys use namespaced prefixes to avoid cross-agent collisions
- [ ] **M-03** `output_key` naming follows convention: `agent_name_result`
- [ ] **M-04** Token budget monitoring enabled — summarization triggers at 80% context capacity
- [ ] **M-05** Session checkpoints for long-running workflows (>5 min execution time)
- [ ] **M-06** Continuous learning configured: auto-save on exit, preload on entry (where applicable)

## FastAPI / Serving (8 items)

- [ ] **F-01** Application factory pattern (`get_fast_api_app()`) — testable, configurable
- [ ] **F-02** TrustedHostMiddleware configured with explicit allowed hosts
- [ ] **F-03** `/health` endpoint returns 200 when process is alive
- [ ] **F-04** `/ready` endpoint returns 200 only when runner is fully warmed up
- [ ] **F-05** Gunicorn with uvicorn workers (not uvicorn directly in production)
- [ ] **F-06** Non-root user in Dockerfile
- [ ] **F-07** Health check probes configured (startup, liveness, readiness)
- [ ] **F-08** Resource limits set: CPU, memory, max instances, concurrency

## Multi-Agent Workflow (6 items)

- [ ] **W-01** All nodes have timeout configuration (per-node, not just workflow-level)
- [ ] **W-02** Edges define typed data contracts between nodes
- [ ] **W-03** Error nodes/sinks defined for all failure paths — no unhandled graph states
- [ ] **W-04** Circuit breaker on external tool calls (fail threshold, recovery timeout)
- [ ] **W-05** Graceful degradation when optional nodes fail (workflow continues, logs warning)
- [ ] **W-06** HITL (Human-in-the-Loop) configured for high-stakes operations (deploy, publish, charge)

## LLM Quality & Safety (9 items)

- [ ] **L-01** Model pinned to specific version (never `latest` alias in production)
- [ ] **L-02** `output_schema` enforced for structured outputs (Pydantic model)
- [ ] **L-03** Prompt injection hardening: NEVER rules, safe default responses, role boundaries
- [ ] **L-04** Hallucination detection: factual grounding check against source documents
- [ ] **L-05** Adversarial eval suite passing: prompt injection, jailbreak, PII leakage
- [ ] **L-06** Eval pass rate 100% on success paths before deploy
- [ ] **L-07** Trajectory recall >= 0.8 (expected tool calls covered by actual)
- [ ] **L-08** Content safety settings configured per use case (HarmBlockThreshold)
- [ ] **L-09** Cost budget enforced: MAX_COST_PER_SESSION hard guard active

---

## Pre-Deploy Gate

```bash
#!/bin/bash
# scripts/production-gate.sh — Run before every deploy
set -euo pipefail

echo "=== ADK Production Readiness Gate ==="

echo "[1/6] Security checks..."
# Verify no hardcoded secrets
! grep -r "sk_live_\|AIza\|password\s*=" app/ --include="*.py" || { echo "FAIL: hardcoded secrets found"; exit 1; }

echo "[2/6] Observability checks..."
# Verify logging/metrics imports exist
grep -q "log_agent_event\|WorkflowLogger" app/*.py || echo "WARN: structured logging not found"

echo "[3/6] Memory checks..."
# Verify SessionService configured
grep -q "SessionService\|MemoryService" app/*.py || echo "WARN: no SessionService found"

echo "[4/6] Serving checks..."
# Verify Dockerfile has non-root user
grep -q "USER app" Dockerfile || { echo "FAIL: Dockerfile must run as non-root"; exit 1; }
grep -q "HEALTHCHECK" Dockerfile || echo "WARN: no HEALTHCHECK in Dockerfile"

echo "[5/6] Workflow checks..."
# Verify error paths exist
grep -q "error\|Error\|fallback\|on_error" app/workflow.py || echo "WARN: no error handling in workflow"

echo "[6/6] Quality checks..."
# Run eval suite
pytest tests/evals/ -v --eval-dataset evals/production.test.json || { echo "FAIL: eval gate"; exit 1; }

echo "=== ALL GATES PASSED ==="
```

## Post-Deploy Validation

- [ ] Smoke test: single request completes successfully within 30s
- [ ] Metrics appearing in dashboard (Cloud Monitoring / Grafana / Datadog)
- [ ] Logs appearing in central observability (Cloud Logging / Splunk / ELK)
- [ ] Alerts configured and firing test alert received
- [ ] Rollback plan tested (redeploy previous image tag)
- [ ] Runbook accessible to on-call (link to incident response doc)
