# Model Armor Integration for ADK Workflows

Model Armor provides content safety filtering for Gemini model inputs and outputs. It is a double-shield architecture: input sanitization before the model, output validation after the model. This reference covers end-to-end integration: API wrapper, production templates, quota planning, and phase-gated rollout.

## Architecture

```
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  User Input  │───▶│ Input Shield     │───▶│  Gemini Model │───▶│ Output Shield    │───▶│  Safe Output │
│              │    │ (Model Armor)    │    │  (ADK Agent)  │    │ (Model Armor)    │    │              │
└──────────────┘    └────────┬─────────┘    └──────────────┘    └────────┬─────────┘    └──────────────┘
                             │                                            │
                      ┌──────▼──────┐                             ┌──────▼──────┐
                      │  Blocked?   │                             │  Blocked?   │
                      │  → Reject   │                             │  → Redact   │
                      └─────────────┘                             └─────────────┘
```

**Double-shield principle:** Input shield blocks unsafe content before it reaches the model. Output shield redacts or blocks unsafe model responses before they reach the user. Never rely on a single shield.

## REST API Wrapper

Model Armor exposes a REST API. Wrap it for ADK callback integration:

```python
"""model_armor_client.py — REST API wrapper for Model Armor."""
import os
import httpx
from typing import Literal

MODEL_ARMOR_ENDPOINT = os.getenv(
    "MODEL_ARMOR_ENDPOINT",
    "https://modelarmor.googleapis.com/v1/projects/{project}/locations/{location}/templates/{template}:sanitize",
)
MODEL_ARMOR_API_KEY = os.getenv("MODEL_ARMOR_API_KEY")
REQUEST_TIMEOUT = float(os.getenv("MODEL_ARMOR_TIMEOUT", "5.0"))


class ModelArmorClient:
    """Thin wrapper around Model Armor REST API."""

    def __init__(
        self,
        project: str | None = None,
        location: str = "us-central1",
        template: str = "default",
    ):
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.endpoint = MODEL_ARMOR_ENDPOINT.format(
            project=self.project, location=location, template=template
        )

    async def sanitize_input(self, text: str, user_id: str) -> dict:
        """Sanitize user input before it reaches the model.

        Returns:
            {"allowed": bool, "sanitized_text": str, "blocked_reason": str | None}
        """
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                self.endpoint,
                json={
                    "prompt": text,
                    "user_id": user_id,
                    "direction": "INPUT",
                },
                headers={"Authorization": f"Bearer {MODEL_ARMOR_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "allowed": not data.get("blocked", False),
                "sanitized_text": data.get("sanitized_prompt", text),
                "blocked_reason": data.get("blocked_reason"),
            }

    async def sanitize_output(self, text: str, user_id: str) -> dict:
        """Sanitize model output before returning to user.

        Returns:
            {"allowed": bool, "sanitized_text": str, "blocked_reason": str | None}
        """
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                self.endpoint,
                json={
                    "prompt": text,
                    "user_id": user_id,
                    "direction": "OUTPUT",
                },
                headers={"Authorization": f"Bearer {MODEL_ARMOR_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "allowed": not data.get("blocked", False),
                "sanitized_text": data.get("sanitized_response", text),
                "blocked_reason": data.get("blocked_reason"),
            }
```

## Double-Shield Agent Runner

Integrate Model Armor into ADK agent callbacks:

```python
"""shielded_runner.py — ADK agent with Model Armor double-shield."""
from google.adk.agents import LlmAgent
from model_armor_client import ModelArmorClient

armor = ModelArmorClient()


async def input_shield(callback_context):
    """Block unsafe user input before it reaches the model."""
    user_query = callback_context.state.get("user_query", "")
    if not user_query:
        return

    result = await armor.sanitize_input(
        text=user_query,
        user_id=callback_context.user_id,
    )
    if not result["allowed"]:
        callback_context.state["blocked"] = True
        callback_context.state["blocked_reason"] = result["blocked_reason"]
        # Prevent model call by raising — caught by ADK runner
        raise InputBlockedError(result["blocked_reason"])

    # Replace with sanitized version
    callback_context.state["user_query"] = result["sanitized_text"]


async def output_shield(callback_context):
    """Block or redact unsafe model output before user sees it."""
    response = callback_context.state.get("agent_response", "")
    if not response:
        return

    result = await armor.sanitize_output(
        text=response,
        user_id=callback_context.user_id,
    )
    if not result["allowed"]:
        callback_context.state["agent_response"] = (
            "I cannot provide that response. Please rephrase your question."
        )
        return

    callback_context.state["agent_response"] = result["sanitized_text"]


class InputBlockedError(Exception):
    pass


# Wire into agent
agent = LlmAgent(
    name="shielded_agent",
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant.",
    before_agent_callback=input_shield,
    after_agent_callback=output_shield,
)
```

## 4 Production Templates

### Template 1: Minimal (dev / prototype)

```yaml
# model-armor-minimal.yaml
template: basic_content_filter
settings:
  hate_speech: BLOCK_ONLY_HIGH
  harassment: BLOCK_ONLY_HIGH
  dangerous_content: BLOCK_ONLY_HIGH
  sexually_explicit: BLOCK_ONLY_HIGH
```

Use for: rapid prototyping, internal tools, non-user-facing agents.

### Template 2: Standard (default for production)

```yaml
# model-armor-standard.yaml
template: production_content_filter
settings:
  hate_speech: BLOCK_MEDIUM_AND_ABOVE
  harassment: BLOCK_MEDIUM_AND_ABOVE
  dangerous_content: BLOCK_MEDIUM_AND_ABOVE
  sexually_explicit: BLOCK_MEDIUM_AND_ABOVE
  pii_redaction: ENABLED
  prompt_injection_detection: ENABLED
  jailbreak_detection: ENABLED
  toxicity_threshold: 0.7
```

Use for: customer-facing agents, support bots, content generation.

### Template 3: Strict (high-risk / regulated)

```yaml
# model-armor-strict.yaml
template: strict_content_filter
settings:
  hate_speech: BLOCK_LOW_AND_ABOVE
  harassment: BLOCK_LOW_AND_ABOVE
  dangerous_content: BLOCK_LOW_AND_ABOVE
  sexually_explicit: BLOCK_LOW_AND_ABOVE
  pii_redaction: ENABLED
  prompt_injection_detection: ENABLED
  jailbreak_detection: ENABLED
  custom_blocklist: ENABLED
  toxicity_threshold: 0.3
  allowed_domains: ["approved-domain.com"]
```

Use for: healthcare, finance, legal, children-facing applications.

### Template 4: Multi-Region (global deployment)

```yaml
# model-armor-multi-region.yaml
regions:
  - us-central1      # Primary
  - europe-west4     # EU failover
  - asia-southeast1  # APAC failover
failover_strategy: active-passive  # or active-active
settings:
  inherit: production_content_filter
  region_specific_rules:
    europe-west4:
      data_residency: EU_ONLY
      gdpr_compliance: ENABLED
```

Use for: global deployments with regional compliance requirements.

## Quota Planning

### Quota Formula

```
Required QPS = (peak_users * avg_turns_per_session) * 2 + 25%
```

- `peak_users`: maximum concurrent users
- `avg_turns_per_session`: average model calls per user session
- `* 2`: input shield + output shield per turn
- `+ 25%`: safety margin for spikes, retries, reclassification

### Floor Settings

| Tier | Peak Users | Min QPS | Recommended Template |
|------|-----------|---------|---------------------|
| Dev/Test | <10 | 10 | Minimal |
| Small Prod | <100 | 50 | Standard |
| Medium Prod | <1,000 | 500 | Standard |
| Large Prod | <10,000 | 5,000 | Standard + Multi-Region |
| Enterprise | >10,000 | Custom | Strict + Multi-Region |

### Quota Request (gcloud)

```bash
gcloud model-armor quotas update \
  --project=${PROJECT_ID} \
  --location=${REGION} \
  --template=production_content_filter \
  --min-qps=${REQUIRED_QPS} \
  --max-qps=$((REQUIRED_QPS * 2))
```

## 6-Phase Production Checklist

### Phase 1: API Enablement
- [ ] Model Armor API enabled in GCP project
- [ ] Service account created with `modelarmor.sanitizer` role
- [ ] API key or workload identity configured
- [ ] VPC Service Controls perimeter includes Model Armor (if applicable)

### Phase 2: Template Configuration
- [ ] Template YAML reviewed by security team
- [ ] Content categories aligned with risk assessment
- [ ] PII redaction enabled if PII may appear in prompts
- [ ] Custom blocklist populated (competitor names, internal codenames, etc.)
- [ ] Jailbreak detection enabled for user-facing agents
- [ ] Toxicity threshold tuned per use case (start conservative, relax with data)

### Phase 3: Client Integration
- [ ] `ModelArmorClient` wrapper deployed with agent code
- [ ] Client configured with 5s timeout + 3 retries
- [ ] Circuit breaker: if Model Armor unavailable, block (fail-closed) or allow (fail-open) — decide per use case
- [ ] Fallback response configured: "I cannot process that request. Please try again."
- [ ] Client metrics exported: latency, error rate, block rate

### Phase 4: Callback Wiring
- [ ] `before_agent_callback` wired to input shield
- [ ] `after_agent_callback` wired to output shield
- [ ] Input shield raises `InputBlockedError` on block (no model call)
- [ ] Output shield replaces blocked response with safe fallback
- [ ] Blocked requests logged with correlation ID (no PII in logs)
- [ ] Both shields tested with adversarial inputs

### Phase 5: Testing & Validation
- [ ] Unit tests: client mock, shield logic, fallback behavior
- [ ] Integration tests: end-to-end with real Model Armor endpoint
- [ ] Adversarial tests: prompt injection, jailbreak, PII leakage, hate speech
- [ ] Latency test: Model Armor adds <200ms p95 per shield
- [ ] Load test: Model Armor handles peak QPS without errors
- [ ] Regional failover test (multi-region deployments)

### Phase 6: Production Monitoring
- [ ] Dashboard: block rate by category, latency p50/p95/p99, error rate
- [ ] Alert: block rate spike (>2x baseline in 5 min)
- [ ] Alert: Model Armor error rate >1%
- [ ] Alert: Model Armor latency p95 >1s
- [ ] Weekly review: blocked prompts sample (anonymized) for false positive analysis
- [ ] Monthly review: template tuning based on false positive/negative trends
- [ ] Quarterly review: quota adequacy check against growth projections
- [ ] Incident response runbook for Model Armor outage

## Anti-Patterns

| Anti-Pattern | Why Bad | Correct |
|-------------|---------|---------|
| Only output shield, no input shield | Unsafe content reaches model, wastes tokens, risks model compliance | Always use both shields |
| Fail-open on Model Armor outage | Unsafe content passes through during outage | Fail-closed for regulated; fail-open with logging for non-critical |
| Hardcoded API key | Key leaks in logs, version control | Use Secret Manager or workload identity |
| Blocking without logging | Cannot audit false positives or improve templates | Log every block with: `correlation_id`, `category`, `direction`, timestamp |
| Same template for dev and prod | Dev allows patterns that break in prod | Separate templates; prod uses Standard or Strict |
| No latency budget | Model Armor adds hidden latency to every turn | Budget 200ms p95; alert if p99 >1s |
| Ignoring false positives | Over-blocking degrades user experience | Weekly review of blocked samples; tune thresholds |

## Integration with SecurityPlugin

Model Armor can be enforced globally via `SecurityPlugin` (see `security-guardrails.md`):

```python
from security_plugin import SecurityPlugin

plugin = SecurityPlugin(
    input_guardrail=armor_input_shield,
    output_guardrail=armor_output_shield,
)
# All sub-agents inherit Model Armor shields automatically
agent = LlmAgent(
    name="root",
    plugins=[plugin],
    sub_agents=[child_agent],  # child_agent also gets shields
)
```

Prefer `SecurityPlugin` for global enforcement across all agents in a workflow. Use per-agent callbacks only when specific agents need different shield configurations.
