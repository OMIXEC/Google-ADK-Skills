# Tool Design for ADK Production Workflows

## Core Principles

1. **Tools do work, agents decide**: Agent reasons about which tool to call. Tool executes deterministically.
2. **Side-effect isolation**: External calls (APIs, DBs, files) live in tools, never in agent instructions.
3. **Observable by default**: Every tool call emits structured event with latency, status, and correlation ID.

## Tool Categories

| Category | Marking | Examples | Requirements |
|----------|---------|----------|-------------|
| **Pure/Read** | `side_effect: false` | DB query, search, fetch | Timeout, error schema |
| **Mutation** | `side_effect: true` | Create order, send email, deploy | Timeout, retry, idempotency, error schema |
| **External API** | `side_effect: true` | Stripe API, GitHub API | Timeout, retry (3x with backoff), circuit breaker |

## Canonical Tool Signature

```python
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field
from typing import Optional
import time
import uuid
import logging

logger = logging.getLogger(__name__)

class CreateOrderParams(BaseModel):
    """Schema for create_order tool. ADK uses this for model context."""
    customer_id: str = Field(description="Customer identifier")
    items: list[dict] = Field(description="List of {sku: str, quantity: int}")
    idempotency_key: str = Field(description="Unique key to prevent duplicate orders")

class CreateOrderResult(BaseModel):
    """Structured return type. Models can reason about this."""
    order_id: str
    status: str  # "created" | "duplicate" | "error"
    total_amount: float

def create_order(params: CreateOrderParams) -> CreateOrderResult:
    """Create a new order. Idempotent: same idempotency_key returns existing order."""
    call_id = str(uuid.uuid4())
    start = time.monotonic()

    try:
        # Check for duplicate
        existing = order_db.find_by_idempotency(params.idempotency_key)
        if existing:
            logger.info("Tool call duplicate", extra={
                "tool": "create_order", "call_id": call_id,
                "idempotency_key": params.idempotency_key, "status": "duplicate"
            })
            return CreateOrderResult(order_id=existing.id, status="duplicate",
                                     total_amount=existing.total)

        # Process order
        order = order_service.create(params.customer_id, params.items)
        order_db.store_idempotency(params.idempotency_key, order.id)

        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info("Tool call succeeded", extra={
            "tool": "create_order", "call_id": call_id, "latency_ms": elapsed_ms,
            "order_id": order.id, "status": "ok"
        })
        return CreateOrderResult(order_id=order.id, status="created",
                                 total_amount=order.total_amount)

    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.error("Tool call failed", extra={
            "tool": "create_order", "call_id": call_id, "latency_ms": elapsed_ms,
            "error": str(e), "idempotency_key": params.idempotency_key
        })
        return CreateOrderResult(order_id="", status="error", total_amount=0.0)

# Register as ADK tool
create_order_tool = FunctionTool(create_order)
```

## Error Handling Protocol

Every tool MUST:

1. **Return structured error, never raise**: Model can't reason about exceptions. Return error status in result type.
2. **Log with context**: `tool` name, `call_id`, `latency_ms`, input summary (no secrets), error detail.
3. **Timeout**: Set `max_execution_time` on tool parameters for long-running operations.
4. **Never leak secrets**: Sanitize parameters before logging. Use `repr()` or explicit sanitizers.

```python
# Anti-pattern: raising exceptions
def bad_tool(query: str) -> dict:
    result = api.call(query)
    if result.error:
        raise Exception(f"API failed: {result.error}")  # Model can't handle this
    return result

# Correct: structured error return
def good_tool(query: str) -> dict:
    result = api.call(query, timeout=10)
    return {
        "data": result.data if result.ok else None,
        "error": result.error if not result.ok else None,
        "ok": result.ok
    }
```

## Retry & Circuit Breaker

For mutation tools:

```python
from functools import wraps
import time

def with_retry(max_retries=3, base_delay=1.0):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except RetryableError as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Retry {attempt+1}/{max_retries} after {delay}s")
                        time.sleep(delay)
            raise last_error
        return wrapper
    return decorator

@with_retry(max_retries=3, base_delay=1.0)
def call_external_api(endpoint: str, payload: dict) -> dict:
    ...
```

## Async Tool Patterns

Long-running tools should be async to avoid blocking the event loop:

```python
import asyncio
from google.adk.tools import FunctionTool

async def async_fetch_data(source: str, timeout: float = 30.0) -> dict:
    """Async tool — ADK handles async functions natively."""
    try:
        result = await asyncio.wait_for(
            external_api.fetch(source),
            timeout=timeout,
        )
        return {"status": "ok", "data": result}
    except asyncio.TimeoutError:
        return {"status": "error", "error": f"Timeout after {timeout}s"}

fetch_tool = FunctionTool(async_fetch_data)
```

**Async rules:**
- Use `asyncio.wait_for` with explicit timeout on every external call
- Return structured error (never raise) for timeout/cancellation
- Coroutine tools run on the event loop — don't block with CPU-bound work
- For CPU-bound work, use `FunctionTool(sync_function)` — ADK wraps in executor

## MCP Tool Integration

Use `MCPToolset` to connect agents to tools in other processes/languages. See `references/mcp-integration.md` for full reference.

```python
from google.adk.tools import MCPToolset, FunctionTool
from google.adk.tools.mcp import StdioServerParameters, SseServerParams

# MCP for side effects, external APIs, multi-language tools
db_tools = MCPToolset(connection_params=StdioServerParameters(
    command="python3", args=["mcp_servers/db_server.py"]
))
api_tools = MCPToolset(connection_params=SseServerParams(
    url="https://tools.example.com/sse",
    headers={"Authorization": "Bearer ${TOOLS_API_KEY}"},
))

# FunctionTool for pure functions and internal logic
internal_tools = FunctionTool(transform_data)

agent = Agent(
    name="hybrid_agent",
    model="gemini-2.5-flash",
    tools=[internal_tools, db_tools, api_tools],
)
```

**Decision matrix:**

| Factor | FunctionTool | MCPToolset |
|--------|-------------|------------|
| Process boundary | Same process | Separate process/server |
| Language | Must match agent | Any language |
| Transport | In-process call | stdio / SSE / HTTP |
| Latency | ~microseconds | ~milliseconds (local), ~10-100ms (remote) |
| Best for | Pure functions, internal logic | External APIs, DBs, shared services, multi-lang |
| Auth | No additional auth | Auth at transport level |

## Tool Versioning Strategy

When evolving tools, maintain backward compatibility:

```python
from pydantic import BaseModel, Field
from typing import Optional

# v1: original signature
class CreateOrderParamsV1(BaseModel):
    customer_id: str
    items: list[dict]

# v2: adds optional fields (backward compatible)
class CreateOrderParamsV2(CreateOrderParamsV1):
    priority: str = "normal"  # New optional field with default
    metadata: Optional[dict] = None  # New optional field
    # Original fields unchanged — existing callers unaffected

def create_order(params: CreateOrderParamsV2) -> dict:
    # Accepts both v1 and v2 callers
    ...
```

**Versioning rules:**
- New optional fields OK (backward compatible)
- Never remove or rename existing fields (breaking)
- Deprecate fields with `Field(deprecated=True)` and comment
- If breaking change is needed, create new tool: `create_order_v2`
- Document deprecation timeline in tool description

## Tool Design Checklist

For each tool, verify:

- [ ] Pydantic params schema with `Field(description=...)` for each field
- [ ] Pydantic return type with clear status field
- [ ] Structured logging: `tool`, `call_id`, `latency_ms`, `status`
- [ ] Timeout configured for external calls
- [ ] Retry (max 3) for mutation tools with exponential backoff + jitter
- [ ] Idempotency for mutation tools (idempotency key pattern)
- [ ] Error returned in result, not raised as exception
- [ ] No secrets in logs
- [ ] `side_effect: true|false` documented
- [ ] Pure tools are deterministic (same input → same output, no external state)
- [ ] Async functions use `asyncio.wait_for` with timeout
- [ ] MCP tools have auth at transport level and `tool_filter` allowlisting
- [ ] Tool versioning plan documented for evolution
