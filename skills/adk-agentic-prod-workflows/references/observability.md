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

## Cost Estimation & Token Tracking

Track token usage to estimate costs across workflow runs:

```python
# Token tracking metrics
TOKEN_USAGE = Counter(
    "token_usage_total", "LLM token usage by model",
    ["workflow_name", "node_name", "model", "token_type"]  # token_type: input|output
)
WORKFLOW_COST = Counter(
    "workflow_cost_cents_total", "Estimated cost in cents",
    ["workflow_name"]
)

# Approximate pricing per 1M tokens (update with current pricing)
MODEL_PRICING = {
    "gemini-2.5-flash":        {"input": 0.15, "output": 0.60},
    "gemini-2.5-pro":          {"input": 1.25, "output": 10.00},
    "gemini-2.5-flash-lite":   {"input": 0.075, "output": 0.30},
}

def record_token_usage(workflow: str, node: str, model: str,
                       input_tokens: int, output_tokens: int):
    TOKEN_USAGE.labels(workflow, node, model, "input").inc(input_tokens)
    TOKEN_USAGE.labels(workflow, node, model, "output").inc(output_tokens)
    
    pricing = MODEL_PRICING.get(model, {"input": 0, "output": 0})
    cost_cents = (
        (input_tokens / 1_000_000) * pricing["input"] +
        (output_tokens / 1_000_000) * pricing["output"]
    ) * 100
    WORKFLOW_COST.labels(workflow).inc(cost_cents)
```

**Cost alerts:**
- `workflow_cost_cents_total` rate > $1/hour → investigate
- Per-node token usage spike (>2x baseline) → possible prompt regression
- Track cost per workflow run for billing/chargeback

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
