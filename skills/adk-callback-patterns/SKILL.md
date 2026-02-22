---
name: ADK Callback Patterns
description: This skill should be used when the user asks to "add callbacks to agent", "customize agent behavior", "intercept LLM calls", "add logging to agent", "implement guardrails", "track agent costs", "monitor tool execution", "transform agent inputs/outputs", or "add safety checks". Provides comprehensive patterns for using ADK's callback system to customize agent behavior at every execution stage.
version: 1.0.0
---

# ADK Callback Patterns

The ADK callback system enables powerful customization of agent behavior by intercepting and modifying execution at key points. Use callbacks for logging, monitoring, safety guardrails, cost tracking, and custom routing logic.

## Callback Types

The ADK provides four callback hooks:

| Callback | Trigger Point | Use Cases |
|----------|---------------|-----------|
| **before_model_callback** | Before LLM request | Input transformation, logging, cost estimation, routing |
| **after_model_callback** | After LLM response | Output filtering, safety checks, response transformation |
| **before_tool_callback** | Before tool execution | Input validation, authorization, logging |
| **after_tool_callback** | After tool execution | Output validation, error handling, monitoring |

## Callback Signature

All callbacks receive a `CallbackContext` and the relevant request/response object:

```python
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

def callback_function(
    ctx: CallbackContext,
    data: types.GenerateContentRequest | types.GenerateContentResponse | ToolCall | ToolResult,
):
    # Process data
    # Return None to continue normal flow
    # Return modified data to override
    # Raise exception to halt execution
    return None
```

## before_model_callback

Intercept and modify the request before it goes to the LLM.

### Basic Logging

```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
import logging

logger = logging.getLogger(__name__)

def log_llm_request(ctx: CallbackContext, request: types.GenerateContentRequest):
    """Log every LLM request for debugging."""
    logger.info(f"Agent: {ctx.agent_name}")
    logger.info(f"Model: {request.model}")
    logger.info(f"Messages: {len(request.contents)} messages")

    # Log user message
    if request.contents:
        last_message = request.contents[-1]
        logger.info(f"User input: {last_message.parts[0].text[:100]}...")

    return None  # Continue normal execution

agent = LlmAgent(
    name="logged_agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=log_llm_request,
)
```

### Input Transformation

```python
def add_context_to_request(ctx: CallbackContext, request: types.GenerateContentRequest):
    """Inject additional context into every request."""

    # Get user message
    user_message = request.contents[-1].parts[0].text

    # Add contextual information
    enhanced_message = f"""
    Current time: {datetime.now().isoformat()}
    User timezone: UTC
    Session ID: {ctx.session_id}

    User query: {user_message}
    """

    # Modify request
    request.contents[-1].parts[0].text = enhanced_message

    return request  # Return modified request

agent = LlmAgent(
    name="context_agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=add_context_to_request,
)
```

### Cost Tracking

```python
class CostTracker:
    """Track LLM API costs."""

    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0

    def estimate_cost(self, ctx: CallbackContext, request: types.GenerateContentRequest):
        """Estimate cost before making request."""
        self.request_count += 1

        # Estimate input tokens (rough approximation)
        input_text = " ".join(
            part.text for content in request.contents
            for part in content.parts
            if hasattr(part, 'text')
        )
        estimated_tokens = len(input_text.split()) * 1.3  # Rough estimate

        # Cost per 1K tokens (example rates)
        cost_per_1k = 0.00025  # Gemini Flash pricing

        estimated_cost = (estimated_tokens / 1000) * cost_per_1k

        self.total_tokens += estimated_tokens
        self.total_cost += estimated_cost

        logger.info(f"Estimated cost: ${estimated_cost:.6f}")
        logger.info(f"Total cost so far: ${self.total_cost:.4f}")

        return None

# Use with agent
tracker = CostTracker()

agent = LlmAgent(
    name="cost_tracked_agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=tracker.estimate_cost,
)

# After conversation
print(f"Total requests: {tracker.request_count}")
print(f"Total estimated cost: ${tracker.total_cost:.4f}")
```

### Request Routing

```python
def route_by_complexity(ctx: CallbackContext, request: types.GenerateContentRequest):
    """Route simple requests to faster model."""

    user_message = request.contents[-1].parts[0].text

    # Detect simple queries
    simple_patterns = [
        "what is",
        "define",
        "explain briefly",
        "summarize in one sentence",
    ]

    is_simple = any(pattern in user_message.lower() for pattern in simple_patterns)

    if is_simple:
        # Switch to faster, cheaper model
        request.model = "gemini-2.0-flash-exp"
        logger.info("Routing to Flash model (simple query)")
    else:
        # Use default model for complex queries
        logger.info("Using default model (complex query)")

    return request

agent = LlmAgent(
    name="adaptive_agent",
    model="gemini-2.0-pro-exp",  # Default to Pro
    before_model_callback=route_by_complexity,
)
```

## after_model_callback

Intercept and modify the LLM response before it's processed.

### Safety Guardrails

```python
def safety_filter(ctx: CallbackContext, response: types.GenerateContentResponse):
    """Filter unsafe or inappropriate content."""

    # Check safety ratings
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]

        if hasattr(candidate, 'safety_ratings'):
            for rating in candidate.safety_ratings:
                if rating.probability in ["HIGH", "MEDIUM"]:
                    logger.warning(f"Safety concern: {rating.category}")

                    # Override response
                    from google.genai.types import Content, Part
                    response.candidates[0].content = Content(
                        parts=[Part(text="I cannot provide that information as it may be inappropriate.")]
                    )
                    return response

    return None  # Continue if safe

agent = LlmAgent(
    name="safe_agent",
    model="gemini-2.0-flash-exp",
    after_model_callback=safety_filter,
)
```

### Response Transformation

```python
def format_as_markdown(ctx: CallbackContext, response: types.GenerateContentResponse):
    """Ensure all responses are properly formatted markdown."""

    if response.candidates:
        text = response.candidates[0].content.parts[0].text

        # Add markdown formatting if missing
        if not any(marker in text for marker in ['#', '**', '```']):
            # Simple text - add basic formatting
            formatted = f"**Response:**\n\n{text}"

            # Update response
            response.candidates[0].content.parts[0].text = formatted

    return response

agent = LlmAgent(
    name="markdown_agent",
    model="gemini-2.0-flash-exp",
    after_model_callback=format_as_markdown,
)
```

### Response Validation

```python
def validate_json_response(ctx: CallbackContext, response: types.GenerateContentResponse):
    """Validate that response is valid JSON when expected."""

    # Check if JSON was requested
    user_message = ctx.conversation_history[-1].text if ctx.conversation_history else ""

    if "json" in user_message.lower():
        response_text = response.candidates[0].content.parts[0].text

        try:
            # Try to parse JSON
            import json
            json.loads(response_text)
            logger.info("Response is valid JSON")

        except json.JSONDecodeError:
            logger.warning("Response is not valid JSON, requesting retry")

            # Could modify response or raise exception to retry
            from google.genai.types import Content, Part
            response.candidates[0].content = Content(
                parts=[Part(text='{"error": "Failed to generate valid JSON. Please try again."}')]
            )

    return response

agent = LlmAgent(
    name="json_agent",
    model="gemini-2.0-flash-exp",
    after_model_callback=validate_json_response,
)
```

### Response Monitoring

```python
class ResponseMonitor:
    """Monitor response quality and latency."""

    def __init__(self):
        self.responses = []
        self.latencies = []

    def monitor_response(self, ctx: CallbackContext, response: types.GenerateContentResponse):
        """Track response metrics."""
        import time

        # Calculate latency (if timing was recorded)
        latency = getattr(ctx, 'latency', None)
        if latency:
            self.latencies.append(latency)

        # Track response length
        if response.candidates:
            text = response.candidates[0].content.parts[0].text
            self.responses.append({
                "length": len(text),
                "timestamp": time.time(),
                "agent": ctx.agent_name,
            })

            # Log statistics
            if len(self.responses) % 10 == 0:
                avg_length = sum(r["length"] for r in self.responses) / len(self.responses)
                logger.info(f"Avg response length: {avg_length:.0f} chars")

                if self.latencies:
                    avg_latency = sum(self.latencies) / len(self.latencies)
                    logger.info(f"Avg latency: {avg_latency:.2f}s")

        return None

# Use with agent
monitor = ResponseMonitor()

agent = LlmAgent(
    name="monitored_agent",
    model="gemini-2.0-flash-exp",
    after_model_callback=monitor.monitor_response,
)
```

## before_tool_callback

Intercept tool calls before execution.

### Tool Logging

```python
def log_tool_calls(ctx: CallbackContext, tool_call):
    """Log every tool invocation."""
    logger.info(f"Agent: {ctx.agent_name}")
    logger.info(f"Tool: {tool_call.name}")
    logger.info(f"Parameters: {tool_call.parameters}")

    return None

agent = LlmAgent(
    name="tool_logged_agent",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool, database_tool],
    before_tool_callback=log_tool_calls,
)
```

### Tool Authorization

```python
class ToolAuthorizer:
    """Authorize tool calls based on user permissions."""

    def __init__(self, user_permissions: set):
        self.user_permissions = user_permissions

    def authorize_tool(self, ctx: CallbackContext, tool_call):
        """Check if user is authorized for this tool."""

        # Define required permissions for each tool
        tool_permissions = {
            "delete_file": "admin",
            "update_database": "write",
            "read_file": "read",
            "search_database": "read",
        }

        required_permission = tool_permissions.get(tool_call.name)

        if required_permission and required_permission not in self.user_permissions:
            logger.warning(f"Unauthorized tool call: {tool_call.name}")

            # Raise exception to prevent execution
            raise PermissionError(f"You don't have permission to use {tool_call.name}")

        return None

# Use with agent
authorizer = ToolAuthorizer(user_permissions={"read", "write"})

agent = LlmAgent(
    name="authorized_agent",
    model="gemini-2.0-flash-exp",
    tools=[read_tool, write_tool, delete_tool],
    before_tool_callback=authorizer.authorize_tool,
)
```

### Tool Input Validation

```python
def validate_tool_input(ctx: CallbackContext, tool_call):
    """Validate tool parameters before execution."""

    # Validate file paths
    if tool_call.name in ["read_file", "write_file"]:
        file_path = tool_call.parameters.get("path", "")

        # Block access to sensitive directories
        forbidden_paths = ["/etc", "/root", "~/.ssh"]

        if any(file_path.startswith(fp) for fp in forbidden_paths):
            raise ValueError(f"Access to {file_path} is not allowed")

    # Validate database queries
    if tool_call.name == "execute_query":
        query = tool_call.parameters.get("sql", "")

        # Block dangerous SQL commands
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER"]

        if any(keyword in query.upper() for keyword in dangerous_keywords):
            raise ValueError(f"Query contains forbidden keyword")

    return None

agent = LlmAgent(
    name="validated_agent",
    model="gemini-2.0-flash-exp",
    tools=[file_tools, db_tools],
    before_tool_callback=validate_tool_input,
)
```

## after_tool_callback

Intercept tool results after execution.

### Error Handling

```python
def handle_tool_errors(ctx: CallbackContext, tool_result):
    """Handle tool errors gracefully."""

    # Check for errors in result
    if isinstance(tool_result, dict) and not tool_result.get("success", True):
        error = tool_result.get("error", "Unknown error")
        tool_name = tool_result.get("tool_name", "unknown")

        logger.error(f"Tool {tool_name} failed: {error}")

        # Transform error into user-friendly message
        user_message = {
            "success": False,
            "message": f"I encountered an issue: {error}. Let me try a different approach.",
            "original_error": error,
        }

        return user_message

    return None

agent = LlmAgent(
    name="resilient_agent",
    model="gemini-2.0-flash-exp",
    tools=[api_tool, database_tool],
    after_tool_callback=handle_tool_errors,
)
```

### Result Caching

```python
class ResultCache:
    """Cache tool results to avoid redundant calls."""

    def __init__(self):
        self.cache = {}

    def cache_result(self, ctx: CallbackContext, tool_result):
        """Cache tool results."""
        import hashlib
        import json

        # Create cache key from tool call
        tool_call = getattr(ctx, 'current_tool_call', None)
        if tool_call:
            cache_key = hashlib.md5(
                json.dumps({
                    "tool": tool_call.name,
                    "params": tool_call.parameters,
                }, sort_keys=True).encode()
            ).hexdigest()

            # Store result
            self.cache[cache_key] = {
                "result": tool_result,
                "timestamp": time.time(),
            }

            logger.info(f"Cached result for {tool_call.name}")

        return None

    def get_cached_result(self, tool_name: str, parameters: dict):
        """Retrieve cached result if available."""
        import hashlib
        import json
        import time

        cache_key = hashlib.md5(
            json.dumps({
                "tool": tool_name,
                "params": parameters,
            }, sort_keys=True).encode()
        ).hexdigest()

        cached = self.cache.get(cache_key)

        # Return if cached and fresh (< 5 minutes old)
        if cached and (time.time() - cached["timestamp"]) < 300:
            logger.info(f"Using cached result for {tool_name}")
            return cached["result"]

        return None

# Use with agent
cache = ResultCache()

agent = LlmAgent(
    name="cached_agent",
    model="gemini-2.0-flash-exp",
    tools=[expensive_api_tool],
    after_tool_callback=cache.cache_result,
)
```

### Result Transformation

```python
def sanitize_tool_output(ctx: CallbackContext, tool_result):
    """Remove sensitive data from tool results."""

    if isinstance(tool_result, dict):
        # Remove sensitive fields
        sensitive_fields = ["password", "api_key", "token", "secret", "ssn"]

        def remove_sensitive(obj):
            if isinstance(obj, dict):
                return {
                    k: "***REDACTED***" if k.lower() in sensitive_fields else remove_sensitive(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [remove_sensitive(item) for item in obj]
            else:
                return obj

        sanitized = remove_sensitive(tool_result)
        return sanitized

    return None

agent = LlmAgent(
    name="sanitized_agent",
    model="gemini-2.0-flash-exp",
    tools=[user_data_tool],
    after_tool_callback=sanitize_tool_output,
)
```

## Combining Multiple Callbacks

Use all four callbacks together for comprehensive control:

```python
class AgentMonitor:
    """Comprehensive agent monitoring and control."""

    def __init__(self):
        self.request_count = 0
        self.tool_calls = []
        self.errors = []

    def before_model(self, ctx: CallbackContext, request):
        """Log and modify requests."""
        self.request_count += 1
        logger.info(f"Request #{self.request_count}")
        return None

    def after_model(self, ctx: CallbackContext, response):
        """Validate responses."""
        # Safety check
        if hasattr(response, 'candidates') and response.candidates:
            # Check for safety issues
            pass
        return None

    def before_tool(self, ctx: CallbackContext, tool_call):
        """Authorize and log tool calls."""
        self.tool_calls.append({
            "name": tool_call.name,
            "params": tool_call.parameters,
        })
        logger.info(f"Tool call: {tool_call.name}")
        return None

    def after_tool(self, ctx: CallbackContext, tool_result):
        """Handle tool errors."""
        if isinstance(tool_result, dict) and not tool_result.get("success", True):
            self.errors.append(tool_result)
        return None

# Create fully monitored agent
monitor = AgentMonitor()

agent = LlmAgent(
    name="fully_monitored_agent",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool, database_tool],
    before_model_callback=monitor.before_model,
    after_model_callback=monitor.after_model,
    before_tool_callback=monitor.before_tool,
    after_tool_callback=monitor.after_tool,
)

# Use agent
response = agent.send_message("What's the weather in Tokyo?")

# Check metrics
print(f"Requests: {monitor.request_count}")
print(f"Tool calls: {len(monitor.tool_calls)}")
print(f"Errors: {len(monitor.errors)}")
```

## Callback Return Values

Callbacks can return three types of values:

| Return Value | Behavior |
|--------------|----------|
| `None` | Continue normal execution (no modification) |
| Modified data | Override with modified request/response/result |
| Exception raised | Halt execution and propagate error |

```python
def example_callback(ctx, data):
    # Option 1: No modification
    return None

    # Option 2: Modify and return
    data.something = "modified"
    return data

    # Option 3: Halt execution
    raise ValueError("Something went wrong")
```

## CallbackContext Reference

The `CallbackContext` object provides information about the current execution:

```python
from google.adk.agents.callback_context import CallbackContext

def callback(ctx: CallbackContext, data):
    # Agent information
    agent_name = ctx.agent_name

    # Session information
    session_id = ctx.session_id

    # Conversation history
    history = ctx.conversation_history

    # Tool information (in tool callbacks)
    current_tool = getattr(ctx, 'current_tool_call', None)

    # Custom attributes (set by other callbacks)
    custom_data = getattr(ctx, 'custom_field', None)

    return None
```

## Best Practices

### 1. Keep Callbacks Fast

Callbacks run on the critical path - avoid slow operations:

```python
# Good - fast logging
def quick_log(ctx, data):
    logger.info(f"Request to {ctx.agent_name}")
    return None

# Bad - slow external call
def slow_callback(ctx, data):
    requests.post("http://analytics.com/log", json=data)  # Blocks execution
    return None
```

### 2. Handle Errors Gracefully

```python
def safe_callback(ctx, data):
    try:
        # Callback logic
        process(data)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        # Don't propagate errors unless critical
        return None
```

### 3. Use Classes for Stateful Callbacks

```python
class StatefulCallback:
    def __init__(self):
        self.state = {}

    def callback(self, ctx, data):
        # Access and modify state
        self.state[ctx.session_id] = data
        return None
```

### 4. Document Callback Behavior

```python
def transform_request(ctx, request):
    """Add timestamp to all LLM requests.

    Args:
        ctx: Callback context
        request: LLM request object

    Returns:
        Modified request with timestamp in system message
    """
    # Implementation
    return request
```

## Common Patterns

### Retry Logic

```python
class RetryCallback:
    """Retry failed tool calls."""

    def __init__(self, max_retries=3):
        self.max_retries = max_retries
        self.retry_counts = {}

    def retry_on_failure(self, ctx, tool_result):
        """Retry failed tool calls."""
        tool_call = getattr(ctx, 'current_tool_call', None)

        if tool_call and isinstance(tool_result, dict):
            if not tool_result.get("success", True):
                key = f"{ctx.session_id}:{tool_call.name}"
                retries = self.retry_counts.get(key, 0)

                if retries < self.max_retries:
                    self.retry_counts[key] = retries + 1
                    logger.info(f"Retrying {tool_call.name} (attempt {retries + 1})")

                    # Raise exception to trigger retry
                    raise Exception("Tool failed, retrying...")

        return None
```

### A/B Testing

```python
import random

def ab_test_models(ctx, request):
    """Randomly route to different models for testing."""
    if random.random() < 0.5:
        request.model = "gemini-2.0-flash-exp"
        logger.info("Using Flash (variant A)")
    else:
        request.model = "gemini-2.0-pro-exp"
        logger.info("Using Pro (variant B)")

    return request
```

### Performance Profiling

```python
import time

class Profiler:
    def __init__(self):
        self.timings = {}

    def start_timer(self, ctx, request):
        ctx.start_time = time.time()
        return None

    def end_timer(self, ctx, response):
        if hasattr(ctx, 'start_time'):
            duration = time.time() - ctx.start_time
            self.timings[ctx.agent_name] = self.timings.get(ctx.agent_name, [])
            self.timings[ctx.agent_name].append(duration)

            logger.info(f"LLM call took {duration:.2f}s")

        return None

profiler = Profiler()

agent = LlmAgent(
    name="profiled_agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=profiler.start_timer,
    after_model_callback=profiler.end_timer,
)
```

## Related Skills

- **adk-tool-builder** - Create tools that work with callbacks
- **adk-agent-testing** - Test agents with callbacks
- **adk-session-management** - Combine callbacks with session state
- **adk-multi-agent-orchestrator** - Use callbacks in multi-agent systems

## Next Steps

1. **Identify use case** - Logging, safety, monitoring, etc.
2. **Choose callback type** - Before/after model/tool
3. **Implement callback function** - With proper error handling
4. **Test thoroughly** - Verify behavior and performance
5. **Monitor in production** - Track callback impact on latency
