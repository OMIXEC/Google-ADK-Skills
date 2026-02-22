# ADK Callback Types Reference

Complete reference for all ADK callback types and their specifications.

## Callback Execution Flow

```
User Input
    ↓
┌─────────────────────────┐
│ before_model_callback   │ → Modify request, add context, log
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│   LLM API Call          │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ after_model_callback    │ → Filter output, validate, transform
└─────────────────────────┘
    ↓
  Tool call needed?
    ↓ (yes)
┌─────────────────────────┐
│ before_tool_callback    │ → Authorize, validate, log
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│   Tool Execution        │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ after_tool_callback     │ → Handle errors, cache, transform
└─────────────────────────┘
    ↓
  More tool calls needed?
    ↓ (loop)
    ↓
  Response to User
```

## before_model_callback

### Signature

```python
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

def before_model_callback(
    ctx: CallbackContext,
    request: types.GenerateContentRequest,
) -> Optional[types.GenerateContentRequest]:
    """Called before sending request to LLM.

    Args:
        ctx: Callback context with agent and session info
        request: The LLM request about to be sent

    Returns:
        None to continue unchanged
        Modified request to override
        Raises exception to halt execution
    """
    return None
```

### Request Object Structure

```python
request = types.GenerateContentRequest(
    model: str,                          # "gemini-2.0-flash-exp"
    contents: List[types.Content],       # Conversation history
    system_instruction: Optional[str],   # System prompt
    tools: List[types.Tool],             # Available tools
    generation_config: types.GenerationConfig,  # Temperature, etc.
)

# Access contents
for content in request.contents:
    for part in content.parts:
        if hasattr(part, 'text'):
            print(part.text)  # User/assistant text
        elif hasattr(part, 'function_call'):
            print(part.function_call)  # Tool call
```

### Use Cases

| Use Case | Pattern |
|----------|---------|
| **Logging** | Log request metadata, don't modify |
| **Context injection** | Add timestamp, user info to message |
| **Request routing** | Change model based on query complexity |
| **Cost estimation** | Calculate token count, estimate cost |
| **Input validation** | Check for prohibited content |
| **Rate limiting** | Check quota, throttle requests |

### Examples

**Add User Context:**

```python
def add_user_context(ctx: CallbackContext, request: types.GenerateContentRequest):
    """Add user metadata to request."""
    user_id = getattr(ctx, 'user_id', 'anonymous')
    user_message = request.contents[-1].parts[0].text

    enhanced = f"[User: {user_id}] {user_message}"
    request.contents[-1].parts[0].text = enhanced

    return request
```

**Dynamic Model Selection:**

```python
def select_model(ctx: CallbackContext, request: types.GenerateContentRequest):
    """Choose model based on query length."""
    user_message = request.contents[-1].parts[0].text

    if len(user_message) < 100:
        request.model = "gemini-2.0-flash-exp"  # Fast for short queries
    else:
        request.model = "gemini-2.0-pro-exp"  # Pro for long queries

    return request
```

**Request Validation:**

```python
def validate_request(ctx: CallbackContext, request: types.GenerateContentRequest):
    """Block requests with prohibited content."""
    user_message = request.contents[-1].parts[0].text

    prohibited = ["example_banned_word"]

    if any(word in user_message.lower() for word in prohibited):
        raise ValueError("Request contains prohibited content")

    return None
```

## after_model_callback

### Signature

```python
def after_model_callback(
    ctx: CallbackContext,
    response: types.GenerateContentResponse,
) -> Optional[types.GenerateContentResponse]:
    """Called after receiving LLM response.

    Args:
        ctx: Callback context
        response: The LLM response

    Returns:
        None to continue unchanged
        Modified response to override
        Raises exception to halt/retry
    """
    return None
```

### Response Object Structure

```python
response = types.GenerateContentResponse(
    candidates: List[types.Candidate],   # Response candidates
    usage_metadata: types.UsageMetadata, # Token counts
)

# Access response text
if response.candidates:
    candidate = response.candidates[0]
    text = candidate.content.parts[0].text

    # Safety ratings
    for rating in candidate.safety_ratings:
        print(f"{rating.category}: {rating.probability}")

# Token usage
print(f"Input tokens: {response.usage_metadata.prompt_token_count}")
print(f"Output tokens: {response.usage_metadata.candidates_token_count}")
```

### Use Cases

| Use Case | Pattern |
|----------|---------|
| **Safety filtering** | Check safety ratings, block unsafe responses |
| **Output formatting** | Convert to markdown, JSON, etc. |
| **Response validation** | Verify JSON format, required fields |
| **Content moderation** | Filter inappropriate language |
| **Token tracking** | Log token usage for billing |
| **Response caching** | Cache responses for similar queries |

### Examples

**Safety Filtering:**

```python
def filter_unsafe(ctx: CallbackContext, response: types.GenerateContentResponse):
    """Block unsafe responses."""
    if response.candidates:
        candidate = response.candidates[0]

        for rating in candidate.safety_ratings:
            if rating.probability in ["HIGH", "MEDIUM"]:
                # Override with safe message
                from google.genai.types import Content, Part
                candidate.content = Content(
                    parts=[Part(text="I cannot provide that information.")]
                )
                return response

    return None
```

**Token Usage Logging:**

```python
class TokenTracker:
    def __init__(self):
        self.total_input = 0
        self.total_output = 0

    def track_tokens(self, ctx: CallbackContext, response: types.GenerateContentResponse):
        """Track token usage."""
        if hasattr(response, 'usage_metadata'):
            self.total_input += response.usage_metadata.prompt_token_count
            self.total_output += response.usage_metadata.candidates_token_count

            logger.info(f"Tokens - Input: {self.total_input}, Output: {self.total_output}")

        return None
```

**JSON Validation:**

```python
def validate_json_output(ctx: CallbackContext, response: types.GenerateContentResponse):
    """Ensure response is valid JSON when expected."""
    if response.candidates:
        text = response.candidates[0].content.parts[0].text

        # Extract JSON if wrapped in markdown
        if "```json" in text:
            json_text = text.split("```json")[1].split("```")[0].strip()
        else:
            json_text = text

        try:
            import json
            json.loads(json_text)  # Validate
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise ValueError("Response is not valid JSON")

    return None
```

## before_tool_callback

### Signature

```python
def before_tool_callback(
    ctx: CallbackContext,
    tool_call: types.FunctionCall,
) -> Optional[types.FunctionCall]:
    """Called before executing a tool.

    Args:
        ctx: Callback context
        tool_call: The tool call about to be executed

    Returns:
        None to continue unchanged
        Modified tool_call to override
        Raises exception to prevent execution
    """
    return None
```

### ToolCall Object Structure

```python
tool_call = types.FunctionCall(
    name: str,                    # Tool name
    args: Dict[str, Any],         # Tool parameters
)

# Access tool call info
print(f"Tool: {tool_call.name}")
print(f"Parameters: {tool_call.args}")
```

### Use Cases

| Use Case | Pattern |
|----------|---------|
| **Authorization** | Check user permissions for tool |
| **Input validation** | Validate parameters before execution |
| **Logging** | Log all tool invocations |
| **Rate limiting** | Throttle tool calls |
| **Parameter transformation** | Modify parameters before execution |
| **Dry run mode** | Log without executing |

### Examples

**Authorization:**

```python
class ToolAuthorizer:
    def __init__(self, user_role: str):
        self.user_role = user_role
        self.permissions = {
            "admin": ["read", "write", "delete"],
            "user": ["read", "write"],
            "guest": ["read"],
        }

    def authorize(self, ctx: CallbackContext, tool_call):
        """Check permissions before tool execution."""
        tool_permissions = {
            "read_file": "read",
            "write_file": "write",
            "delete_file": "delete",
        }

        required = tool_permissions.get(tool_call.name)
        allowed = self.permissions.get(self.user_role, [])

        if required and required not in allowed:
            raise PermissionError(f"Role '{self.user_role}' cannot use {tool_call.name}")

        return None
```

**Input Validation:**

```python
def validate_file_paths(ctx: CallbackContext, tool_call):
    """Validate file path parameters."""
    if tool_call.name in ["read_file", "write_file"]:
        file_path = tool_call.args.get("path", "")

        # Block dangerous paths
        if file_path.startswith("/etc") or file_path.startswith("/root"):
            raise ValueError(f"Access to {file_path} is forbidden")

        # Require absolute paths
        if not file_path.startswith("/"):
            raise ValueError("File path must be absolute")

    return None
```

**Tool Call Logging:**

```python
class ToolLogger:
    def __init__(self):
        self.calls = []

    def log_tool_call(self, ctx: CallbackContext, tool_call):
        """Log every tool invocation."""
        self.calls.append({
            "timestamp": time.time(),
            "agent": ctx.agent_name,
            "tool": tool_call.name,
            "params": tool_call.args,
        })

        logger.info(f"Tool call: {tool_call.name}")
        return None
```

## after_tool_callback

### Signature

```python
def after_tool_callback(
    ctx: CallbackContext,
    tool_result: Any,
) -> Optional[Any]:
    """Called after tool execution completes.

    Args:
        ctx: Callback context
        tool_result: The tool's return value

    Returns:
        None to continue unchanged
        Modified result to override
        Raises exception to halt
    """
    return None
```

### Use Cases

| Use Case | Pattern |
|----------|---------|
| **Error handling** | Transform errors to user-friendly messages |
| **Result caching** | Cache results to avoid redundant calls |
| **Output sanitization** | Remove sensitive data from results |
| **Logging** | Log tool results for debugging |
| **Result transformation** | Format results for better LLM understanding |
| **Monitoring** | Track tool success/failure rates |

### Examples

**Error Handling:**

```python
def handle_errors(ctx: CallbackContext, tool_result):
    """Transform tool errors into user-friendly messages."""
    if isinstance(tool_result, dict):
        if not tool_result.get("success", True):
            error = tool_result.get("error", "Unknown error")

            return {
                "success": False,
                "user_message": f"I encountered an issue: {error}. Let me try another approach.",
                "original_error": error,
            }

    return None
```

**Result Caching:**

```python
import hashlib
import json

class ResultCache:
    def __init__(self, ttl=300):
        self.cache = {}
        self.ttl = ttl

    def cache_result(self, ctx: CallbackContext, tool_result):
        """Cache tool results."""
        tool_call = getattr(ctx, 'current_tool_call', None)

        if tool_call:
            cache_key = hashlib.md5(
                json.dumps({
                    "tool": tool_call.name,
                    "args": tool_call.args,
                }, sort_keys=True).encode()
            ).hexdigest()

            self.cache[cache_key] = {
                "result": tool_result,
                "timestamp": time.time(),
            }

        return None

    def get_cached(self, tool_name, args):
        """Retrieve cached result if fresh."""
        cache_key = hashlib.md5(
            json.dumps({
                "tool": tool_name,
                "args": args,
            }, sort_keys=True).encode()
        ).hexdigest()

        cached = self.cache.get(cache_key)

        if cached and (time.time() - cached["timestamp"]) < self.ttl:
            return cached["result"]

        return None
```

**Data Sanitization:**

```python
def sanitize_output(ctx: CallbackContext, tool_result):
    """Remove sensitive fields from tool results."""
    sensitive_fields = ["password", "api_key", "token", "ssn", "credit_card"]

    def redact(obj):
        if isinstance(obj, dict):
            return {
                k: "***REDACTED***" if k.lower() in sensitive_fields else redact(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [redact(item) for item in obj]
        return obj

    return redact(tool_result)
```

## CallbackContext API

```python
class CallbackContext:
    """Context object passed to all callbacks."""

    # Agent information
    agent_name: str              # Name of the agent
    agent_id: str                # Unique agent identifier

    # Session information
    session_id: Optional[str]    # Current session ID
    user_id: Optional[str]       # User identifier

    # Conversation state
    conversation_history: List   # Previous turns
    turn_count: int              # Number of turns so far

    # Tool information (in tool callbacks)
    current_tool_call: Optional[types.FunctionCall]
    current_tool_name: Optional[str]

    # Custom attributes
    # You can set custom attributes on ctx for inter-callback communication
    # ctx.my_custom_field = "value"
```

### Setting Custom Context

```python
def callback_a(ctx: CallbackContext, data):
    """First callback sets custom data."""
    ctx.custom_metric = 42
    return None

def callback_b(ctx: CallbackContext, data):
    """Second callback reads custom data."""
    metric = getattr(ctx, 'custom_metric', None)
    if metric:
        logger.info(f"Metric from callback_a: {metric}")
    return None
```

## Callback Chaining

Multiple callbacks execute in sequence:

```python
def callback_1(ctx, data):
    logger.info("Callback 1")
    data.field_a = "modified by callback 1"
    return data

def callback_2(ctx, data):
    logger.info("Callback 2")
    # Sees modification from callback 1
    assert data.field_a == "modified by callback 1"
    data.field_b = "modified by callback 2"
    return data

# Both callbacks execute in order
agent = LlmAgent(
    name="agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=callback_1,  # Only one callback per hook
)

# To chain multiple callbacks, use a wrapper:
def combined_callback(ctx, data):
    data = callback_1(ctx, data) or data
    data = callback_2(ctx, data) or data
    return data

agent = LlmAgent(
    name="agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=combined_callback,
)
```

## Performance Considerations

### Callback Timing

Callbacks run on the critical execution path:

```
User input → [before_model] → LLM call → [after_model] → [before_tool] → Tool → [after_tool] → Response
              ↑ Fast          ↑ Slow     ↑ Fast          ↑ Fast         ↑ Varies ↑ Fast
```

**Guidelines:**
- Keep callbacks under 100ms when possible
- Avoid network calls in callbacks (use async background tasks instead)
- Cache expensive computations
- Use lazy loading for resources

### Async Callbacks

For long-running operations, use async patterns:

```python
import asyncio

async def async_callback(ctx, data):
    """Async callback for I/O operations."""
    # Non-blocking I/O
    result = await fetch_data_async()

    # Process result
    data.extra_field = result

    return data

# Note: ADK callback support varies by language
# Check documentation for async callback support
```

## Error Handling

### Callback Exceptions

```python
def callback_with_error_handling(ctx, data):
    """Callback with proper error handling."""
    try:
        # Callback logic
        result = process(data)
        return result

    except ValueError as e:
        # Expected errors - log and continue
        logger.warning(f"Validation error: {e}")
        return None

    except Exception as e:
        # Unexpected errors - log and optionally halt
        logger.error(f"Callback error: {e}", exc_info=True)

        # Option 1: Continue despite error
        return None

        # Option 2: Halt execution
        # raise
```

### Graceful Degradation

```python
def optional_enhancement(ctx, data):
    """Callback that enhances but doesn't break on failure."""
    try:
        # Try to add enhancement
        enhanced = enhance(data)
        return enhanced
    except:
        # Enhancement failed, continue with original
        logger.warning("Enhancement failed, using original data")
        return None  # Continue with unmodified data
```

## Testing Callbacks

```python
import pytest
from unittest.mock import Mock

def test_callback():
    """Test callback in isolation."""
    # Create mock context
    ctx = Mock()
    ctx.agent_name = "test_agent"
    ctx.session_id = "test_session"

    # Create test data
    from google.genai.types import GenerateContentRequest, Content, Part
    request = GenerateContentRequest(
        model="gemini-2.0-flash-exp",
        contents=[Content(parts=[Part(text="Hello")])],
    )

    # Call callback
    result = my_callback(ctx, request)

    # Assert expected behavior
    assert result is not None
    assert result.contents[-1].parts[0].text == "Expected modification"

def test_callback_error_handling():
    """Test callback handles errors gracefully."""
    ctx = Mock()
    bad_data = None

    # Should not raise
    result = my_callback(ctx, bad_data)
    assert result is None  # Graceful handling
```

## Related Documentation

- ADK Callbacks Guide: [Official Documentation]
- Google GenAI Types: [API Reference]
- Callback Patterns: **adk-callback-patterns** skill
