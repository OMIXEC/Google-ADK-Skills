# Model Armor for ADK-Based Products: Full Security Guide, Checklist & Templates

This document is the complete dev-team reference for integrating Google Cloud Model Armor into any ADK-based production or assistive-agent product. It covers architecture, every available filter, integration options, template design patterns, implementation code, and a full per-phase operational checklist.

---

## 1. What Model Armor Does and When to Use It

Model Armor is a Google Cloud runtime AI security service that operates at the **semantic layer** — inspecting actual text moving between users and LLMs, not at the network or IP level. It works as a stateless screening proxy that sits in front of and behind every LLM call, letting you define policies that detect and optionally block prompt injections, jailbreaks, sensitive data, malicious URLs, and responsible-AI violations.

### Core security flow for every ADK product

```
User Input
    │
    ▼
┌─────────────────────────────┐
│  INPUT SHIELD               │
│  Model Armor sanitizePrompt │  ← Blocks injections, jailbreaks, PII-in, malicious content
└─────────────────────────────┘
    │ (clean prompt only)
    ▼
ADK Agent (Gemini / tool use / sub-agents)
    │
    ▼
┌─────────────────────────────┐
│  OUTPUT SHIELD              │
│  Model Armor sanitizeResponse│ ← Blocks PII-out, harmful content, malicious URLs
└─────────────────────────────┘
    │ (safe response only)
    ▼
User
```

Model Armor processes all content **in memory only** — it does not log, store, or retain prompt or response content unless you explicitly enable Cloud Logging, giving you full control over data retention.

### When to use Model Armor in ADK products

| Scenario | Use Model Armor? | Priority |
|---|---|---|
| User-facing chat interface (external or internal) | Yes — mandatory for prod | Critical |
| Assistive agents with database or file tool access | Yes — mandatory | Critical |
| Multi-agent orchestration with sub-agents | Yes — wrap at orchestrator boundary | High |
| RAG applications retrieving internal documents | Yes — output shield minimum | High |
| Agentic systems calling external APIs or MCP tools | Yes — input and output | High |
| Internal-only developer testing | Optional — `Inspect only` mode recommended | Medium |
| Batch/offline pipelines without live user input | Optional — output shield advisable | Low |

---

## 2. Model Armor Filters Reference

### 2.1 Responsible AI Safety Filters

These filters screen for harmful content categories. All are configurable per threshold level. The CSAM filter is always on and cannot be disabled.

| Filter | What it catches | Default recommendation |
|---|---|---|
| Hate speech | Negative or harmful comments targeting identity or protected attributes | `HIGH` for prod start |
| Harassment | Threatening, intimidating, bullying, or abusive comments | `HIGH` for prod start |
| Sexually explicit | References to sexual acts or lewd content | `HIGH` for prod start |
| Dangerous content | Promotes or enables access to harmful goods, services, or activities | `HIGH` for prod start |
| CSAM | Child sexual abuse material references | Always on, non-configurable |

### 2.2 Prompt Injection and Jailbreak Detection

Detects attempts to override system instructions, extract credentials, bypass safety rules, or force unintended behavior from the agent. This is the most critical filter for any ADK product that connects an LLM to real tools, databases, or APIs.

| Threshold | Behavior | Recommended use case |
|---|---|---|
| `HIGH` | Near-certain injection only | Gemini Enterprise, high-traffic apps with low false-positive tolerance |
| `MEDIUM_AND_ABOVE` | Balanced | Standard production ADK apps |
| `LOW_AND_ABOVE` | Catches even subtle attempts | High-security zones; accept higher false-positive rate |

### 2.3 Sensitive Data Protection (SDP)

Integrates Google's Sensitive Data Protection to identify, redact, or block 150+ PII types.

**Basic configuration** — covers these built-in infotypes:
- Credit card numbers
- US Social Security Numbers (SSN)
- Financial account numbers
- US ITIN (Individual Taxpayer Identification Numbers)
- Google Cloud credentials
- Google Cloud API keys

**Advanced configuration** — supports full SDP inspection templates with custom infotypes, custom regular expressions, de-identification, tokenization, and redaction rules. Use this for:
- GDPR PII (EU national IDs, EU phone numbers, IBAN)
- Healthcare (diagnosis codes, insurance IDs)
- Custom business secrets or contract identifiers

### 2.4 Malicious URL Detection

Scans prompts and responses for embedded URLs matching known phishing, malware, or threat-intelligence feeds. Important for:
- Agents that summarize web content
- Agents that handle external document uploads
- RAG pipelines that retrieve from unverified sources

### 2.5 Document Screening

Model Armor can screen the following document types for all active filters:
- PDFs, CSVs, TXT files
- DOCX, DOCM, DOTX, DOTM (Microsoft Word)
- PPTX, PPTM, POTX, POTM (Microsoft PowerPoint)
- XLSX, XLSM, XLTX, XLTM (Microsoft Excel)

Use document screening for any ADK tool that accepts file uploads as user input.

---

## 3. Confidence Thresholds

| Level | Detection probability | False positive risk | Best for |
|---|---|---|---|
| `HIGH` | High-confidence violations only | Very low | Production — prioritizes uninterrupted interactions |
| `MEDIUM_AND_ABOVE` | Medium or high confidence | Moderate | Standard enterprise apps — balanced protection |
| `LOW_AND_ABOVE` | Any indication including low confidence | High | Prompt injection/jailbreak only; not for general content categories |

**Starting recommendation:** Use `HIGH` for responsible AI categories (hate, harassment, sexually explicit, dangerous) and `MEDIUM_AND_ABOVE` for prompt injection and jailbreak in standard ADK products. Lower thresholds only after baseline testing confirms false-positive rates are acceptable.

---

## 4. Integration Options

| Integration path | How it works | Inspect only | Inspect + block | Coverage |
|---|---|---|---|---|
| **REST API** (Cloud Run ADK) | App code calls `sanitizeUserPrompt` and `sanitizeModelResponse`, then applies block logic | Yes | Yes (app enforces) | All models, all clouds |
| **Vertex AI inline** | Model Armor wraps Gemini `generateContent` automatically via floor settings or templates | Yes | Yes (inline) | Gemini non-streaming on GCP |
| **GKE + Service Extensions** | Inference gateway screens all traffic | Yes | Yes (inline) | OpenAI-format models on GCP |
| **Gemini Enterprise** | All user-agent-LLM traffic screened at gateway | Yes | Yes (inline) | All models |
| **MCP servers (Preview)** | Sanitizes MCP tool calls and responses using floor settings | Yes | Yes (inline) | MCP on GCP |

**For ADK on Cloud Run:** Use the REST API path. Your app code calls `sanitizeUserPrompt` before passing input to the agent and `sanitizeModelResponse` before returning output to the user.

**For Vertex AI Agent Engine:** Use Vertex AI inline integration with floor settings as the organization-wide baseline, plus templates for per-agent configuration.

---

## 5. Template Design Patterns

### 5.1 Separate input and output templates

Always create two distinct templates — one for user prompt sanitization and one for model response sanitization. Input and output have different risk profiles:

- **Input template:** Focused on preventing malicious inputs, prompt injections, jailbreak attempts, and PII being uploaded by users.
- **Output template:** Focused on preventing the model from leaking sensitive data, generating harmful content, returning malicious URLs, or producing off-brand responses.

### 5.2 Standard production templates

Use these as your starting point, then tune based on your specific domain.

#### Template A: `prod-input-standard`
For general enterprise ADK products with a user-facing chat interface.

```json
{
  "filterConfig": {
    "raiSettings": {
      "raiFilters": [
        { "filterType": "HATE",              "confidenceLevel": "HIGH" },
        { "filterType": "HARASSMENT",        "confidenceLevel": "HIGH" },
        { "filterType": "SEXUALLY_EXPLICIT", "confidenceLevel": "HIGH" },
        { "filterType": "DANGEROUS",         "confidenceLevel": "HIGH" }
      ]
    },
    "piAndJailbreakFilterSettings": {
      "filterEnforcement": "ENABLED",
      "confidenceLevel": "MEDIUM_AND_ABOVE"
    },
    "sdpSettings": {
      "basicConfig": {
        "filterEnforcement": "ENABLED"
      }
    }
  }
}
```

#### Template B: `prod-output-standard`
For blocking PII and harmful content in model responses.

```json
{
  "filterConfig": {
    "raiSettings": {
      "raiFilters": [
        { "filterType": "HATE",              "confidenceLevel": "HIGH" },
        { "filterType": "HARASSMENT",        "confidenceLevel": "HIGH" },
        { "filterType": "SEXUALLY_EXPLICIT", "confidenceLevel": "HIGH" },
        { "filterType": "DANGEROUS",         "confidenceLevel": "HIGH" }
      ]
    },
    "sdpSettings": {
      "basicConfig": {
        "filterEnforcement": "ENABLED"
      }
    },
    "maliciousUriFilterSettings": {
      "filterEnforcement": "ENABLED"
    }
  }
}
```

#### Template C: `prod-input-high-security`
For ADK assistive agents accessing sensitive systems (databases, HR, finance, healthcare).

```json
{
  "filterConfig": {
    "raiSettings": {
      "raiFilters": [
        { "filterType": "HATE",              "confidenceLevel": "MEDIUM_AND_ABOVE" },
        { "filterType": "HARASSMENT",        "confidenceLevel": "MEDIUM_AND_ABOVE" },
        { "filterType": "SEXUALLY_EXPLICIT", "confidenceLevel": "HIGH" },
        { "filterType": "DANGEROUS",         "confidenceLevel": "MEDIUM_AND_ABOVE" }
      ]
    },
    "piAndJailbreakFilterSettings": {
      "filterEnforcement": "ENABLED",
      "confidenceLevel": "LOW_AND_ABOVE"
    },
    "sdpSettings": {
      "advancedConfig": {
        "inspectTemplate": "projects/PROJECT_ID/locations/LOCATION/inspectTemplates/TEMPLATE_ID",
        "deidentifyTemplate": "projects/PROJECT_ID/locations/LOCATION/deidentifyTemplates/TEMPLATE_ID"
      }
    },
    "maliciousUriFilterSettings": {
      "filterEnforcement": "ENABLED"
    }
  }
}
```

#### Template D: `dev-inspect-only`
For pre-production testing and baseline measurement. Logs all detections without blocking.

```json
{
  "filterConfig": {
    "raiSettings": {
      "raiFilters": [
        { "filterType": "HATE",              "confidenceLevel": "MEDIUM_AND_ABOVE" },
        { "filterType": "HARASSMENT",        "confidenceLevel": "MEDIUM_AND_ABOVE" },
        { "filterType": "SEXUALLY_EXPLICIT", "confidenceLevel": "MEDIUM_AND_ABOVE" },
        { "filterType": "DANGEROUS",         "confidenceLevel": "MEDIUM_AND_ABOVE" }
      ]
    },
    "piAndJailbreakFilterSettings": {
      "filterEnforcement": "ENABLED",
      "confidenceLevel": "MEDIUM_AND_ABOVE"
    },
    "sdpSettings": {
      "basicConfig": {
        "filterEnforcement": "ENABLED"
      }
    },
    "maliciousUriFilterSettings": {
      "filterEnforcement": "ENABLED"
    }
  }
}
```

Set enforcement to `INSPECT_ONLY` for this template. All hits are logged to Cloud Logging but nothing is blocked. Use this in dev and staging to measure baseline false-positive rates before switching to `INSPECT_AND_BLOCK` in prod.

---

## 6. Implementation Code

### 6.1 Enable Model Armor API

```bash
# Enable the API
gcloud services enable modelarmor.googleapis.com

# Set regional endpoint (replace LOCATION with your region)
gcloud config set api_endpoint_overrides/modelarmor \
  "https://modelarmor.LOCATION.rep.googleapis.com/"
```

### 6.2 Create templates via gcloud

```bash
# Create input template
gcloud model-armor templates create prod-input-standard \
  --location=LOCATION \
  --filter-config-file=prod-input-standard.json

# Create output template
gcloud model-armor templates create prod-output-standard \
  --location=LOCATION \
  --filter-config-file=prod-output-standard.json
```

### 6.3 ADK Cloud Run integration — Python wrapper

This is the production-recommended pattern for ADK agents deployed on Cloud Run. Wrap the agent runner with both an input shield and an output shield function.

```python
# security/model_armor.py

import os
import logging
import google.auth
from google.auth.transport.requests import Request
import requests

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
INPUT_TEMPLATE_ID = os.environ["MODEL_ARMOR_INPUT_TEMPLATE"]
OUTPUT_TEMPLATE_ID = os.environ["MODEL_ARMOR_OUTPUT_TEMPLATE"]

MA_BASE_URL = f"https://modelarmor.{LOCATION}.rep.googleapis.com/v1"


def _get_token() -> str:
    """Get ADC token for Model Armor REST API calls."""
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token


def sanitize_input(user_text: str) -> tuple[bool, str, dict]:
    """
    Screen user prompt before sending to agent.
    Returns: (is_safe, text_or_block_message, raw_result)
    """
    try:
        token = _get_token()
        url = (
            f"{MA_BASE_URL}/projects/{PROJECT_ID}/locations/{LOCATION}"
            f"/templates/{INPUT_TEMPLATE_ID}:sanitizeUserPrompt"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {"userPromptData": {"text": user_text}}
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        filter_results = (
            result.get("sanitizationResult", {}).get("filterResults", {})
        )
        blocked_by = [
            f for f, d in filter_results.items()
            if d.get("matchState") == "MATCH_FOUND"
        ]

        if blocked_by:
            logger.warning(
                "Input blocked by Model Armor",
                extra={"filters_matched": blocked_by, "action": "INPUT_BLOCKED"}
            )
            return (
                False,
                "Your message could not be processed. Please rephrase your request.",
                result,
            )

        return True, user_text, result

    except Exception as e:
        logger.error(f"Model Armor input check error: {e}")
        # POLICY DECISION: fail-closed (safer) or fail-open (higher availability)
        # Fail-closed: return False, "Security check unavailable.", {}
        # Fail-open:   return True, user_text, {}
        raise  # Default: let error handler decide


def sanitize_output(response_text: str) -> tuple[bool, str, dict]:
    """
    Screen agent response before returning to user.
    Returns: (is_safe, text_or_block_message, raw_result)
    """
    try:
        token = _get_token()
        url = (
            f"{MA_BASE_URL}/projects/{PROJECT_ID}/locations/{LOCATION}"
            f"/templates/{OUTPUT_TEMPLATE_ID}:sanitizeModelResponse"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {"modelResponseData": {"text": response_text}}
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        filter_results = (
            result.get("sanitizationResult", {}).get("filterResults", {})
        )
        blocked_by = [
            f for f, d in filter_results.items()
            if d.get("matchState") == "MATCH_FOUND"
        ]

        if blocked_by:
            logger.warning(
                "Output blocked by Model Armor",
                extra={"filters_matched": blocked_by, "action": "OUTPUT_BLOCKED"}
            )
            return (
                False,
                "The response could not be returned due to a content policy violation.",
                result,
            )

        return True, response_text, result

    except Exception as e:
        logger.error(f"Model Armor output check error: {e}")
        raise
```

### 6.4 ADK agent runner with shields applied

```python
# apps/api/runner.py

import asyncio
from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService
from google.genai import types as genai_types
from agent.root_agent import root_agent
from security.model_armor import sanitize_input, sanitize_output

session_service = VertexAiSessionService(
    project=PROJECT_ID,
    location=LOCATION,
)

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def run_agent_with_shields(
    user_text: str, session_id: str, user_id: str
) -> str:
    # INPUT SHIELD
    input_safe, cleaned_input, _ = sanitize_input(user_text)
    if not input_safe:
        return cleaned_input

    # AGENT EXECUTION
    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=cleaned_input)]
    )
    final_text = ""
    async for event in runner.run_async(
        new_message=content,
        user_id=user_id,
        session_id=session_id,
    ):
        if hasattr(event, "text") and event.text:
            final_text = event.text

    # OUTPUT SHIELD
    output_safe, safe_output, _ = sanitize_output(final_text)
    if not output_safe:
        return safe_output

    return safe_output
```

### 6.5 Fail-open vs fail-closed policy

| Policy | When Model Armor is unavailable | Use when |
|---|---|---|
| **Fail-closed** | Block all requests; return error to user | High-security, regulated environments; assistive agents with sensitive data access |
| **Fail-open** | Allow requests to pass through; log the bypass | High-availability consumer apps where uptime outweighs marginal security risk |

Always log fail-open bypasses with severity `WARNING` so they are visible in Cloud Monitoring alert policies.

### 6.6 Multi-language support

Enable multi-language detection when serving non-English users. Supported natively: Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Spanish.

Per-request method:
```python
payload = {
    "userPromptData": {"text": user_text},
    "multiLanguageDetection": {"enableMultiLanguageDetection": True}
}
```

Or configure once at the template level via REST API to avoid per-request overhead.

---

## 7. Floor Settings

Floor settings define **organization-wide minimum security baselines** across all templates in a project. They are the lowest-precedence layer but ensure no deployed agent can run below the minimum policy floor.

**Configuration precedence (highest to lowest):**
1. Per-request template config
2. Model Armor floor settings
3. Vertex AI default safety filters

Set floor settings when:
- Multiple teams deploy ADK agents and a guaranteed minimum policy is required.
- Using MCP servers (the MCP integration currently supports floor settings only, not templates).
- A centralized policy is needed that individual app configs cannot remove.

```bash
POST https://modelarmor.LOCATION.rep.googleapis.com/v1/projects/PROJECT_ID/locations/LOCATION/floorSetting

{
  "filterConfig": {
    "piAndJailbreakFilterSettings": {
      "filterEnforcement": "ENABLED",
      "confidenceLevel": "HIGH"
    },
    "sdpSettings": {
      "basicConfig": {
        "filterEnforcement": "ENABLED"
      }
    }
  }
}
```

---

## 8. Quota Planning

Model Armor defaults to **1,200 QPM per project**. For ADK products that call both `sanitizeUserPrompt` and `sanitizeModelResponse` per interaction, 2 Model Armor calls are consumed per agent turn.

**Quota formula:**
```
Required QPM = (peak users per minute × avg turns per session) × 2
              + 25% buffer for spikes

Example: 300 peak users/min × 1.5 avg turns × 2 calls = 900 QPM
With 25% buffer → request 1,125–1,200 QPM
```

Monitor for `429 RESOURCE_EXHAUSTED` errors in Cloud Logging — this signals quota exhaustion, which triggers fail-open or fail-closed behavior depending on your error policy.

---

## 9. Observability and Monitoring

Model Armor logs events to Cloud Logging under service `modelarmor.googleapis.com`. Enable this before going to production.

### Recommended log filter

```
resource.type="modelarmor_template"
log_name="projects/PROJECT_ID/logs/modelarmor.googleapis.com%2Fsanitize"
```

### Cloud Monitoring alerts to configure

| Alert | Condition | Severity | Action |
|---|---|---|---|
| High input block rate | Input blocks > X% of requests in window | Warning | Review false-positive rate; tune thresholds |
| High output block rate | Output blocks > X% of responses in window | Warning | Investigate model behavior or data leakage pattern |
| 429 quota exceeded | Model Armor HTTP 429 errors | Critical | Request quota increase; check fail-open bypasses |
| Service unavailability | Model Armor call failures above threshold | Critical | Validate fail-closed policy; alert on-call |
| Security Command Center finding | Model Armor floor setting violation | Critical | Immediate review; possible adversarial probe |

Model Armor sends floor setting violations as findings to Security Command Center automatically.

---

## 10. Production Checklist

Use this checklist for every new ADK product or major release involving Model Armor.

---

### Phase 1 — Initial Setup

- [ ] Model Armor API enabled in the target project
- [ ] Regional endpoint configured matching the deployment region (Cloud Run or Agent Engine)
- [ ] Runtime service account granted appropriate role to call Model Armor APIs (`roles/modelarmor.user` or project-level equivalent)
- [ ] Cloud Logging enabled for `modelarmor.googleapis.com` in the project
- [ ] Security Command Center enabled for floor setting violation findings

---

### Phase 2 — Template Design

- [ ] Separate input template created (`prod-input-*`)
- [ ] Separate output template created (`prod-output-*`)
- [ ] Template IDs stored in Secret Manager or environment variables — never hardcoded
- [ ] Template filter categories chosen based on use-case risk profile (Section 3)
- [ ] Confidence levels set to `HIGH` for responsible AI categories as initial prod baseline
- [ ] Prompt injection/jailbreak set to `MEDIUM_AND_ABOVE` or `LOW_AND_ABOVE` based on sensitivity
- [ ] SDP configuration selected: Basic (US PII) or Advanced (custom infotypes, GDPR, healthcare)
- [ ] Malicious URL detection enabled for any agent handling external content or document uploads
- [ ] Multi-language detection enabled if product serves non-English users
- [ ] Floor settings configured for org-wide minimum baseline
- [ ] Document screening enabled for any tool that accepts file uploads (PDF, DOCX, XLSX, etc.)

---

### Phase 3 — Integration

- [ ] `sanitize_input()` called before passing user text to ADK agent runner
- [ ] `sanitize_output()` called before returning agent response to user
- [ ] Both shield functions have structured logging with `action`, `filters_matched`, and `session_id` context
- [ ] Fail-open vs fail-closed policy decided and documented for the product
- [ ] Error handling prevents Model Armor exceptions from exposing raw error details to users
- [ ] All Model Armor calls are wrapped in try/except with proper escalation
- [ ] Block messages shown to users are generic (do not reveal filter names or rule details)
- [ ] Template IDs injected as env vars from Secret Manager, not committed to source

---

### Phase 4 — Testing and Validation

- [ ] **Safe prompt test:** Known-safe prompts pass without false-positive blocks
- [ ] **Injection test:** Known jailbreak prompts (e.g., "Ignore your previous instructions...") are blocked
- [ ] **Input PII test:** Inputs with credit card numbers, SSNs, Google API keys are blocked or flagged
- [ ] **Output PII test:** Agent response containing PII is blocked before reaching user
- [ ] **Malicious URL test:** Response containing known phishing URL is blocked
- [ ] **Document test (if applicable):** Malicious PDF or document upload triggers correct filters
- [ ] **Multi-language test (if applicable):** Non-English injections/jailbreaks are caught
- [ ] **Fail-closed test:** Model Armor made unavailable; verify request is blocked, not leaked
- [ ] False-positive rate measured against representative real-user queries
- [ ] Results logged and reviewed before switching from `Inspect only` to `Inspect and block`

---

### Phase 5 — Production Launch

- [ ] All prod templates switched from `INSPECT_ONLY` to `INSPECT_AND_BLOCK`
- [ ] Cloud Monitoring alerts configured (block rate, quota, availability — Section 9)
- [ ] Cloud Logging filters and dashboards set up for Model Armor service
- [ ] Quota estimated and verified sufficient with 25% buffer (Section 8)
- [ ] Security Command Center receiving Model Armor findings
- [ ] Runbook written covering: high block rate, quota exhaustion, Model Armor unavailability
- [ ] On-call alert routing includes Model Armor critical alerts

---

### Phase 6 — Ongoing Operations

- [ ] Block rate reviewed weekly in first month, monthly thereafter
- [ ] False positive reports from users tracked and fed back to threshold tuning
- [ ] Template versions tracked alongside code versions in release notes
- [ ] Any template change requires passing Phase 4 testing before prod rollout
- [ ] Quota reviewed and adjusted when traffic grows significantly
- [ ] SDP template updated when new sensitive data types are introduced
- [ ] Floor settings reviewed at org level quarterly

---

## 11. Security Template for Assistive Agents

Assistive agents that help users with tasks involving private or sensitive data — HR, support, productivity, accessibility, field ops — require additional controls on top of standard production templates.

### Recommended configuration for assistive agents

| Control | Setting | Reason |
|---|---|---|
| Prompt injection threshold | `LOW_AND_ABOVE` | Assistive users share personal context that attackers could weaponize as injection vectors |
| SDP config | Advanced with custom infotypes | Assistive agents handle more varied PII: names, addresses, medical info, preferences |
| RAI — dangerous content | `MEDIUM_AND_ABOVE` | Assistive agents may be queried on healthcare or safety topics |
| Output malicious URL | Always enabled | Assistive agents may summarize or relay third-party content |
| Fail policy | Fail-closed | Assistive context is high-trust; partial failure is safer than silent bypass |
| User-facing block message | Generic + escalation path | "I cannot process this request. If this is an error, contact support at [link]" |
| Logging | Enabled with session and user ID context | Required for audit, accessibility compliance, and support resolution |

### Extra controls for accessibility-focused assistive agents

For agents specifically designed for hearing-impaired or vision-impaired users, or any agent with elevated trust over personal communications or environment access:

- Apply the `prod-input-high-security` template to all inputs.
- Add output topic controls via Model Armor custom topics if the agent must stay in a defined domain.
- Log every Model Armor action with the user session ID so accessibility incidents can be reviewed without exposing PII in logs.
- Use Advanced SDP with de-identification in the output template so any accidentally retrieved personal data is redacted before reaching the user's interface layer.

---

## 12. Security Anti-Patterns

| Anti-pattern | Problem | Correct approach |
|---|---|---|
| Calling Model Armor only on input, not output | Agent can still leak PII or generate harmful responses | Always apply both input and output shields |
| Using one template for both input and output | Loses granular control and traceability | Separate templates per direction |
| Treating prompt instructions as security controls | LLM instructions can be overridden by injection | Model Armor + IAM are the real controls; prompts are guidance only |
| Starting with `LOW_AND_ABOVE` on all categories | Creates very high false-positive rates; degrades UX and erodes user trust | Start with `HIGH` for responsible AI; tune down only after testing |
| Hardcoding template IDs in application code | Breaks template rotation and audit traceability | Store template IDs in env vars or Secret Manager |
| Not enabling Cloud Logging before launch | `Inspect only` phase produces no useful data without logging | Enable Cloud Logging on day one |
| Ignoring quota limits until production traffic hits them | 429 errors cause fail-open bypasses if not handled | Estimate quota before launch, add 25% buffer, set 429 alert |
| Sharing one template across dev/staging/prod | Prod settings pollute dev or dev relaxed settings reach prod | One template set per environment |

---

## 13. Quick Reference Card

```
MODEL ARMOR — ADK QUICK REFERENCE
══════════════════════════════════════════════════

EVERY USER-FACING ADK PRODUCT MUST HAVE:
  ✓ Input template  (prod-input-*)
  ✓ Output template (prod-output-*)
  ✓ sanitize_input()  BEFORE agent
  ✓ sanitize_output() BEFORE user
  ✓ Cloud Logging enabled
  ✓ Fail-closed or fail-open policy documented

MINIMUM FILTER BASELINE (PROD):
  RAI filters (hate/harassment/explicit/dangerous) → HIGH
  Prompt injection + jailbreak                     → MEDIUM_AND_ABOVE
  SDP basic                                        → ENABLED
  Malicious URL                                    → ENABLED (if external content)

ASSISTIVE / HIGH-SECURITY AGENTS — ADD:
  Prompt injection threshold → LOW_AND_ABOVE
  SDP                        → Advanced with custom infotypes
  Fail policy                → Fail-closed

FLOOR SETTINGS (ORG-WIDE MINIMUM):
  Prompt injection + jailbreak → HIGH
  SDP basic                    → ENABLED

QUOTA FORMULA:
  Required QPM = (peak users/min × avg turns) × 2
  Add 25% buffer → request increase if >1200 QPM

INCIDENT SIGNALS:
  429 RESOURCE_EXHAUSTED     → quota exceeded
  Block rate spike           → tune thresholds or investigate probe
  SCC finding                → immediate review required
  Fail-open bypass warning   → investigate Model Armor availability

PRECEDENCE ORDER (highest → lowest):
  1. Per-request template config
  2. Model Armor floor settings
  3. Vertex AI default safety filters
```
