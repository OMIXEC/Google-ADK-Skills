# Observability for ADK Workflows

## Three Pillars

### 1. Structured Logging

Every workflow component emits JSON-structured logs with consistent fields.

**Required log fields for every event:**

```json
{
  "timestamp": "2026-05-27T14:00:00.000Z",
  "level": "INFO",
  "correlation_id": "wf_abc123",
  "workflow": "order_processing",
  "node": "validator",
  "agent": "order_validator",
  "call_id": "call_def456",
  "message": "Validation complete",
  "latency_ms": 145,
  "status": "ok"
}
```

**Log levels:**
- `INFO`: Normal operation (tool called, agent delegated, workflow step complete)
- `WARNING`: Degraded operation (retry succeeded, fallback used, timeout approaching)
- `ERROR`: Failed operation (tool error, agent crash, workflow path broken)
- `DEBUG`: Diagnostic detail (full prompt, tool parameters, raw responses — sanitized)

**Implementation:**

```python
import logging
import json
import uuid
import time
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
workflow_id_var: ContextVar[str] = ContextVar("workflow_id", default="")

class WorkflowLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra.setdefault("correlation_id", correlation_id_var.get())
        extra.setdefault("workflow", workflow_id_var.get())
        extra.setdefault("timestamp", time.strftime("%Y-%m-%dT%H:%M:%S.000Z"))
        kwargs["extra"] = extra
        return msg, kwargs

logger = WorkflowLogger(logging.getLogger(__name__), {})
```

### 2. Distributed Tracing

Propagate trace context across workflow nodes, tool calls, and A2A boundaries.

**Span hierarchy:**

```
Workflow Run (root span)
├── Node: Validator (child span)
│   ├── Tool: validate_order (grandchild)
│   └── Tool: check_inventory (grandchild)
├── Node: Enricher (child span)
│   └── Tool: fetch_customer_data (grandchild)
└── Node: Approver (child span)
    └── Agent delegation: approval_agent (grandchild)
```

**Implementation pattern:**

```python
import contextlib
import time

@contextlib.contextmanager
def trace_span(name: str, span_type: str = "node"):
    span_id = str(uuid.uuid4())
    start = time.monotonic()
    logger.info(f"Span start", extra={"span_id": span_id, "span_name": name, "span_type": span_type})
    try:
        yield span_id
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        logger.error(f"Span error", extra={
            "span_id": span_id, "span_name": name, "latency_ms": elapsed, "error": str(e)
        })
        raise
    finally:
        elapsed = (time.monotonic() - start) * 1000
        logger.info(f"Span end", extra={
            "span_id": span_id, "span_name": name, "latency_ms": elapsed
        })

# Usage in workflow node
def execute_node(order):
    with trace_span("order_validation", "node") as span_id:
        with trace_span("validate_order_tool", "tool"):
            result = validate_order(order)
        return result
```

### 3. Metrics

Emit metrics for monitoring and alerting.

**Core workflow metrics:**

| Metric | Type | Description | Alert |
|--------|------|-------------|-------|
| `workflow_duration_ms` | Histogram | End-to-end workflow latency | p95 > 30s |
| `node_duration_ms` | Histogram | Per-node latency | p95 > 10s |
| `tool_call_duration_ms` | Histogram | Per-tool latency | p95 > 5s |
| `node_errors_total` | Counter | Errors per node | rate > 0 |
| `tool_call_errors_total` | Counter | Tool call errors | rate > 0 |
| `agent_delegations_total` | Counter | Coordinator → worker delegations | — |
| `token_usage_total` | Counter | LLM token consumption | — |
| `workflow_success_rate` | Gauge | Successful / total runs | < 0.95 |

**Implementation (Prometheus-compatible):**

```python
# metrics.py
WORKFLOW_DURATION = Histogram(
    "workflow_duration_ms", "Workflow end-to-end latency",
    ["workflow_name"], buckets=[100, 500, 1000, 5000, 15000, 30000]
)
NODE_DURATION = Histogram(
    "node_duration_ms", "Per-node latency",
    ["workflow_name", "node_name"], buckets=[50, 100, 500, 1000, 5000]
)
NODE_ERRORS = Counter(
    "node_errors_total", "Node error count",
    ["workflow_name", "node_name", "error_type"]
)
TOKEN_USAGE = Counter(
    "token_usage_total", "LLM token usage",
    ["workflow_name", "node_name", "model"]
)
```

## Cloud Logging Integration

For GCP deployments, use Cloud Logging-compatible format:

```python
import google.cloud.logging

client = google.cloud.logging.Client()
cloud_logger = client.logger("adk-workflow")

def log_workflow_event(event_type: str, **fields):
    cloud_logger.log_struct({
        "severity": fields.get("level", "INFO"),
        "event_type": event_type,
        "correlation_id": correlation_id_var.get(),
        "workflow": workflow_id_var.get(),
        **fields
    })
```

## Go Observability (slog + OpenTelemetry)

```go
import (
    "context"
    "log/slog"
    "os"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/prometheus"
    "go.opentelemetry.io/otel/metric"
    sdkmetric "go.opentelemetry.io/otel/sdk/metric"
    "go.opentelemetry.io/otel/trace"
)

// Structured logging with slog (Go 1.21+)
var logger = slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))

type WorkflowContext struct {
    CorrelationID string
    WorkflowName  string
}

func (wc WorkflowContext) LogAttrs() []slog.Attr {
    return []slog.Attr{
        slog.String("correlation_id", wc.CorrelationID),
        slog.String("workflow", wc.WorkflowName),
    }
}

func runNode(ctx context.Context, wc WorkflowContext, nodeName string) error {
    logger.LogAttrs(ctx, slog.LevelInfo, "node start",
        append(wc.LogAttrs(), slog.String("node", nodeName))...)
    defer func() {
        logger.LogAttrs(ctx, slog.LevelInfo, "node end",
            append(wc.LogAttrs(), slog.String("node", nodeName))...)
    }()
    // ... node logic
    return nil
}
```

## TypeScript Observability (pino + OpenTelemetry JS)

```typescript
import pino from 'pino';
import { trace, SpanStatusCode } from '@opentelemetry/api';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  mixin() {
    return { correlation_id: correlationIdVar.get() };
  },
});

const tracer = trace.getTracer('adk-workflow');

async function runNode(name: string, fn: () => Promise<void>) {
  const span = tracer.startSpan(name);
  logger.info({ node: name }, 'node start');
  try {
    await fn();
    span.setStatus({ code: SpanStatusCode.OK });
  } catch (error) {
    span.setStatus({ code: SpanStatusCode.ERROR, message: String(error) });
    throw error;
  } finally {
    span.end();
    logger.info({ node: name }, 'node end');
  }
}
```

## Cost Tracking & Per-Session Budget Enforcement

Track token usage and cost in real-time. Enforce per-session budgets with hard caps.

### Cost Constants

```python
# Pricing per 1M tokens (USD). Update monthly from ai.google.dev/pricing.
COST_PER_1M_INPUT = {
    "gemini-2.5-flash-lite": 0.075,
    "gemini-2.5-flash":      0.15,
    "gemini-2.5-pro":        1.25,
}

COST_PER_1M_OUTPUT = {
    "gemini-2.5-flash-lite": 0.30,
    "gemini-2.5-flash":      0.60,
    "gemini-2.5-pro":        10.00,
}

# Never exceed this per session (hard cap). Tune per use case.
MAX_COST_PER_SESSION_USD = 1.00


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for a single model call."""
    input_cost = (input_tokens / 1_000_000) * COST_PER_1M_INPUT.get(model, 0)
    output_cost = (output_tokens / 1_000_000) * COST_PER_1M_OUTPUT.get(model, 0)
    return input_cost + output_cost
```

### Cost Tracking Callback Pair

```python
"""cost_tracker.py — before_model + after_model callback pair for cost tracking."""
import time
from contextvars import ContextVar

session_cost_var: ContextVar[float] = ContextVar("session_cost", default=0.0)
call_start_var: ContextVar[float] = ContextVar("call_start", default=0.0)


async def before_model_callback_timer(callback_context):
    """Capture model call start time and check budget."""
    if session_cost_var.get() >= MAX_COST_PER_SESSION_USD:
        # Hard budget guard — return a canned response, skip model call
        callback_context.state["budget_exceeded"] = True
        return types.LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="Session budget exceeded. Please try again later.")],
            )
        )
    call_start_var.set(time.monotonic())
    return None  # Proceed with model call


async def after_model_callback_cost(callback_context):
    """Record token usage and cost after model response."""
    if callback_context.state.get("budget_exceeded"):
        return

    elapsed_ms = (time.monotonic() - call_start_var.get()) * 1000
    usage = callback_context.usage_metadata

    if usage:
        cost = estimate_cost(
            model=callback_context.agent.model,
            input_tokens=usage.prompt_token_count or 0,
            output_tokens=usage.candidates_token_count or 0,
        )
        current_total = session_cost_var.get() + cost
        session_cost_var.set(current_total)

        WORKFLOW_COST.labels(callback_context.state.get("workflow_name", "unknown")).inc(cost * 100)
        TOKEN_USAGE.labels(
            callback_context.state.get("workflow_name", "unknown"),
            callback_context.agent.name,
            callback_context.agent.model,
            "input",
        ).inc(usage.prompt_token_count or 0)
        TOKEN_USAGE.labels(
            callback_context.state.get("workflow_name", "unknown"),
            callback_context.agent.name,
            callback_context.agent.model,
            "output",
        ).inc(usage.candidates_token_count or 0)

        logger.info("Model call cost", extra={
            "model": callback_context.agent.model,
            "agent": callback_context.agent.name,
            "input_tokens": usage.prompt_token_count,
            "output_tokens": usage.candidates_token_count,
            "cost_usd": cost,
            "session_cost_total": current_total,
            "latency_ms": elapsed_ms,
        })

# Wire into agent
agent = LlmAgent(
    name="cost_tracked_agent",
    model="gemini-2.5-flash",
    before_model_callback=before_model_callback_timer,
    after_model_callback=after_model_callback_cost,
)
```

### Latency Histogram

```python
# Per-node latency with p50/p95/p99 tracking
NODE_LATENCY = Histogram(
    "node_latency_ms", "Per-node end-to-end latency",
    ["workflow_name", "node_name"],
    buckets=[50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000],
)

MODEL_LATENCY = Histogram(
    "model_latency_ms", "Model call latency",
    ["workflow_name", "agent_name", "model"],
    buckets=[100, 250, 500, 1000, 2500, 5000, 10000],
)

TOOL_LATENCY = Histogram(
    "tool_latency_ms", "Tool call latency",
    ["workflow_name", "tool_name"],
    buckets=[10, 50, 100, 250, 500, 1000, 5000],
)
```

**Cost alerts:**
- Session cost > $0.50 approaching cap → WARNING
- Session cost hits $MAX_COST_PER_SESSION_USD → block further calls (hard guard)
- Per-node token usage spike (>2x baseline) → possible prompt regression
- Track cost per workflow run for billing/chargeback

### Token Tracking Metrics

```python
TOKEN_USAGE = Counter(
    "token_usage_total", "LLM token usage by model",
    ["workflow_name", "node_name", "model", "token_type"]  # token_type: input|output
)
WORKFLOW_COST = Counter(
    "workflow_cost_cents_total", "Estimated cost in cents",
    ["workflow_name"]
)
```

## Structured JSON Logging with Trace Correlation

Embed OpenTelemetry trace context into every JSON log entry for unified log-trace correlation.

### Python: google.cloud.logging + OTel

```python
"""structured_logging.py — JSON logs with trace/span correlation."""
import logging
import json
from contextvars import ContextVar
from opentelemetry import trace

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
span_id_var: ContextVar[str] = ContextVar("span_id", default="")
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class TraceLogFilter(logging.Filter):
    """Inject OTel trace context into every log record."""
    def filter(self, record):
        record.trace_id = trace_id_var.get() or ""
        record.span_id = span_id_var.get() or ""
        record.correlation_id = correlation_id_var.get() or ""
        return True


def log_agent_event(
    event_type: str,
    message: str,
    level: str = "INFO",
    **json_fields,
):
    """Emit a structured JSON log entry with trace correlation.

    Every log entry automatically includes trace_id, span_id, and correlation_id.
    Additional fields passed as kwargs are serialized into the JSON payload.
    """
    span = trace.get_current_span()
    trace_id = format(span.get_span_context().trace_id, "032x") if span else ""
    span_id = format(span.get_span_context().span_id, "016x") if span else ""

    log_entry = {
        "severity": level,
        "event_type": event_type,
        "message": message,
        "trace_id": trace_id,
        "span_id": span_id,
        "correlation_id": correlation_id_var.get(),
        "logging.googleapis.com/trace": f"projects/{PROJECT_ID}/traces/{trace_id}",
        "logging.googleapis.com/spanId": span_id,
        **json_fields,
    }
    # Remove None values
    log_entry = {k: v for k, v in log_entry.items() if v is not None}

    if level == "ERROR":
        cloud_logger.log_struct(log_entry, severity="ERROR")
    elif level == "WARNING":
        cloud_logger.log_struct(log_entry, severity="WARNING")
    else:
        cloud_logger.log_struct(log_entry, severity="INFO")


# Usage in callbacks
async def after_tool_log(callback_context):
    log_agent_event(
        event_type="tool_call_complete",
        message=f"Tool {callback_context.tool_name} completed",
        tool_name=callback_context.tool_name,
        tool_call_id=callback_context.tool_call_id,
        latency_ms=callback_context.latency_ms,
        status="ok" if not callback_context.error else "error",
        error=str(callback_context.error) if callback_context.error else None,
    )
```

### Cloud Trace Filter Recipes

In Cloud Logging explorer, use these filters to correlate logs with traces:

```
# Find all logs for a specific trace
trace="projects/my-project/traces/ABC123..."

# Find all ERROR logs for a trace
trace="projects/my-project/traces/ABC123..." severity>=ERROR

# Find slow tool calls in a trace
trace="projects/my-project/traces/ABC123..." jsonPayload.event_type="tool_call_complete" jsonPayload.latency_ms>500

# Find all events for a workflow run
jsonPayload.correlation_id="wf_abc123"
```

## Observability Checklist

- [ ] Correlation ID generated at workflow entry and propagated to all nodes/tools
- [ ] Every tool call logs: tool name, call_id, latency_ms, status
- [ ] Every agent delegation logs: from agent, to agent, reason, correlation_id
- [ ] Workflow start/end logged with total duration
- [ ] Errors logged with full context (no secrets)
- [ ] Metrics exported for workflow duration, node errors, token usage
- [ ] Log level configurable via environment variable (`LOG_LEVEL`)
- [ ] Sensitive data (API keys, PII, tokens) excluded from logs
- [ ] Go: slog structured logging + OpenTelemetry traces
- [ ] TS: pino structured logging + OpenTelemetry JS traces
- [ ] Token usage tracked per node with cost estimation
- [ ] Cost alerts configured for budget monitoring
