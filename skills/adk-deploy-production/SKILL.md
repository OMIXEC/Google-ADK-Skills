---
name: adk-deploy-production
description: >-
  Takes an ADK agent or workflow to production: CI/CD pipelines, container and cloud
  targets, identity and database integration, guardrails, observability, resilience,
  evaluation, and the pre-deploy checklist. Use when packaging an agent, wiring auth or
  a database, adding tracing and metrics, designing retries and fallbacks, or deciding
  whether a build is safe to ship. Don't use for the provider's own deploy command
  syntax (use adk-deployment), for designing the workflow graph (use
  adk-graph-workflows), or for agent internals (use adk-agent-architecture).
compatibility: google-adk>=2.9.2,<3
---

# ADK Deploy to Production

Own everything between "the agent works on my machine" and "the agent serves
traffic": the artifact, the pipeline, the credentials, the guardrails, the
telemetry, and the gate that says stop.

Read `references/adk-2x-baseline.md` for the version floor and Python matrix.

## Deployment path

| Stage | Command / artifact |
|---|---|
| Install | `uv sync` or `uv pip install -r requirements.txt` |
| Lint | `ruff check .` |
| Unit test | `pytest tests/ -v` |
| Eval gate | `python evals/test_harness.py` |
| Package | `python scripts/package_workflow.py --source app/ --name <name> --target <target>` |
| Build | `docker build -t <name> .` |
| Deploy | Target-specific command from `references/deployment-matrix.md` |

Default target is Cloud Run. Agent Engine, GKE, Vertex AI Endpoints, App
Engine, ECS/Fargate, EKS, Lambda, SageMaker, Container Apps, AKS, App Service,
Azure ML, and local Docker are all covered in the deployment matrix.

`package_workflow.py` generates the Dockerfile, the target manifest, and the
environment template. The Dockerfile must run as non-root and expose a health
check.

## Non-negotiables

- **No secrets in code.** `${YOUR_PROJECT_ID}` / `${YOUR_API_KEY}` placeholders;
  real values from Secret Manager or the platform's secret store.
- **Input validation at every entry point**, before the model sees the request.
- **Scoped credentials per node.** One broad service account for the whole
  workflow is a finding, not a design.
- **Structured logs with a correlation ID** propagated across nodes.
- **A pre-deploy gate.** `references/production-checklist.md` is the gate; a
  failing security item blocks the deploy.

## Identity and data

If the workflow is user-facing, design identity before the database:
`UserContext` from verified claims, `user_id` and `tenant_id` injected into
every tool call, row-level security where the store supports it, and
application-level filtering where it does not.

- `references/auth-providers.md` — 13 providers, OIDC/JWKS, SAML bridge.
- `references/database-integration.md` — Postgres, MySQL, Spanner, Oracle,
  Mongo, Redis, Firestore, Bigtable, DynamoDB, SQLite, Convex.
- `references/identity-db-integration.md` — the combined checklist.

## Safety and quality

- `references/security-guardrails.md` — per-agent callbacks plus a global
  `SecurityPlugin`.
- `references/model-armor.md` — input and output content screening.
- `references/output-validation.md` — schemas, quality gates, grounding checks.
- `references/error-resilience.md` — retry with jitter, circuit breaker,
  dead-letter queue, graceful degradation.
- `references/observability.md` — spans, metrics, cost tracking.

## Evaluation and tests

Test the whole flow, not just the agents:

| Layer | What it proves |
|---|---|
| Unit | Agent logic and tool functions |
| Integration | Graph wiring with externals mocked |
| API | `adk api_server` endpoints |
| Web E2E | `adk web` flows with Playwright |
| Eval | Success, degenerate, safety, and performance scenarios |
| Security | Prompt injection, SQLi, XSS, tenant isolation |
| Performance | Latency, concurrency, memory |

`assets/evals/` carries the harness and config; `assets/cicd/` carries the
GitHub Actions and Cloud Build pipelines. `references/testing-strategies.md`
holds the full patterns.

## References

| File | Load when |
|---|---|
| `references/deployment-matrix.md` | Choosing a cloud target or writing IaC |
| `references/cicd-patterns.md` | Generating a pipeline |
| `references/production-checklist.md` | Before any deploy |
| `references/security-guardrails.md` | Adding guardrails |
| `references/model-armor.md` | Content screening |
| `references/observability.md` | Tracing, metrics, cost |
| `references/error-resilience.md` | Retries, breakers, fallbacks |
| `references/output-validation.md` | Structured output and quality gates |
| `references/testing-strategies.md` | Test layers and CI wiring |
| `references/auth-providers.md` | Identity provider patterns |
| `references/database-integration.md` | Database patterns |
| `references/identity-db-integration.md` | Combined identity + data design |
| `references/adk-2x-baseline.md` | Version, imports, migration |

## Boundaries

- Workflow shape belongs to `adk-graph-workflows`.
- Agent internals belong to `adk-agent-architecture`.
