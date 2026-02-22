# Logging Callback Examples

Complete examples for implementing comprehensive logging with ADK callbacks.

## Example 1: Basic Request/Response Logging

```python
import logging
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_request(ctx: CallbackContext, request: types.GenerateContentRequest):
    """Log LLM requests."""
    logger.info(f"=== LLM Request ===")
    logger.info(f"Agent: {ctx.agent_name}")
    logger.info(f"Model: {request.model}")
    logger.info(f"Session: {ctx.session_id}")

    # Log user message
    if request.contents:
        user_message = request.contents[-1].parts[0].text
        logger.info(f"User: {user_message[:100]}...")

    return None

def log_response(ctx: CallbackContext, response: types.GenerateContentResponse):
    """Log LLM responses."""
    logger.info(f"=== LLM Response ===")

    if response.candidates:
        response_text = response.candidates[0].content.parts[0].text
        logger.info(f"Assistant: {response_text[:100]}...")

    # Log token usage
    if hasattr(response, 'usage_metadata'):
        logger.info(f"Tokens - Input: {response.usage_metadata.prompt_token_count}, "
                   f"Output: {response.usage_metadata.candidates_token_count}")

    return None

# Create agent with logging
agent = LlmAgent(
    name="logged_agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=log_request,
    after_model_callback=log_response,
)

# Test
if __name__ == "__main__":
    response = agent.send_message("Hello, how are you?")
    print(response.text)
```

## Example 2: Structured JSON Logging

```python
import json
import logging
from datetime import datetime

class StructuredLogger:
    """Log to structured JSON format for analysis."""

    def __init__(self, log_file: str = "agent_logs.jsonl"):
        self.log_file = log_file

    def log_request(self, ctx: CallbackContext, request: types.GenerateContentRequest):
        """Log request as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "llm_request",
            "agent": ctx.agent_name,
            "session_id": ctx.session_id,
            "model": request.model,
            "turn_count": getattr(ctx, 'turn_count', 0),
        }

        # Extract user message
        if request.contents:
            user_message = request.contents[-1].parts[0].text
            log_entry["user_message"] = user_message
            log_entry["message_length"] = len(user_message)

        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        return None

    def log_response(self, ctx: CallbackContext, response: types.GenerateContentResponse):
        """Log response as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "llm_response",
            "agent": ctx.agent_name,
            "session_id": ctx.session_id,
        }

        if response.candidates:
            response_text = response.candidates[0].content.parts[0].text
            log_entry["response"] = response_text
            log_entry["response_length"] = len(response_text)

        # Token usage
        if hasattr(response, 'usage_metadata'):
            log_entry["tokens"] = {
                "input": response.usage_metadata.prompt_token_count,
                "output": response.usage_metadata.candidates_token_count,
                "total": (response.usage_metadata.prompt_token_count +
                         response.usage_metadata.candidates_token_count),
            }

        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        return None

# Use structured logger
logger = StructuredLogger("agent_logs.jsonl")

agent = LlmAgent(
    name="structured_logged_agent",
    model="gemini-2.0-flash-exp",
    before_model_callback=logger.log_request,
    after_model_callback=logger.log_response,
)
```

## Example 3: Tool Call Logging

```python
class ToolLogger:
    """Comprehensive tool call logging."""

    def __init__(self):
        self.tool_calls = []

    def log_tool_call(self, ctx: CallbackContext, tool_call):
        """Log tool invocation."""
        logger.info(f"=== Tool Call ===")
        logger.info(f"Agent: {ctx.agent_name}")
        logger.info(f"Tool: {tool_call.name}")
        logger.info(f"Parameters: {json.dumps(tool_call.args, indent=2)}")

        # Store for analysis
        self.tool_calls.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": ctx.agent_name,
            "tool": tool_call.name,
            "params": tool_call.args,
        })

        return None

    def log_tool_result(self, ctx: CallbackContext, tool_result):
        """Log tool result."""
        logger.info(f"=== Tool Result ===")

        if isinstance(tool_result, dict):
            # Log success/failure
            success = tool_result.get("success", True)
            logger.info(f"Success: {success}")

            if not success:
                logger.warning(f"Error: {tool_result.get('error', 'Unknown error')}")
            else:
                logger.info(f"Result: {json.dumps(tool_result, indent=2)[:200]}...")

        return None

    def get_tool_stats(self):
        """Get tool usage statistics."""
        from collections import Counter

        tool_counts = Counter(call["tool"] for call in self.tool_calls)

        return {
            "total_calls": len(self.tool_calls),
            "unique_tools": len(tool_counts),
            "tool_usage": dict(tool_counts),
        }

# Use tool logger
tool_logger = ToolLogger()

agent = LlmAgent(
    name="tool_logged_agent",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool, database_tool],
    before_tool_callback=tool_logger.log_tool_call,
    after_tool_callback=tool_logger.log_tool_result,
)

# After conversation
print(tool_logger.get_tool_stats())
```

## Example 4: Database Logging

```python
import sqlite3
from datetime import datetime

class DatabaseLogger:
    """Log agent interactions to SQLite database."""

    def __init__(self, db_path: str = "agent_logs.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                session_id TEXT,
                model TEXT NOT NULL,
                user_message TEXT NOT NULL,
                message_length INTEGER
            )
        """)

        # Responses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                session_id TEXT,
                response_text TEXT NOT NULL,
                response_length INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                total_tokens INTEGER
            )
        """)

        # Tool calls table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                session_id TEXT,
                tool_name TEXT NOT NULL,
                parameters TEXT,
                success BOOLEAN,
                error_message TEXT
            )
        """)

        conn.commit()
        conn.close()

    def log_request(self, ctx: CallbackContext, request: types.GenerateContentRequest):
        """Log request to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        user_message = ""
        if request.contents:
            user_message = request.contents[-1].parts[0].text

        cursor.execute("""
            INSERT INTO requests (timestamp, agent_name, session_id, model, user_message, message_length)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            ctx.agent_name,
            ctx.session_id,
            request.model,
            user_message,
            len(user_message),
        ))

        conn.commit()
        conn.close()
        return None

    def log_response(self, ctx: CallbackContext, response: types.GenerateContentResponse):
        """Log response to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        response_text = ""
        input_tokens = 0
        output_tokens = 0

        if response.candidates:
            response_text = response.candidates[0].content.parts[0].text

        if hasattr(response, 'usage_metadata'):
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count

        cursor.execute("""
            INSERT INTO responses (timestamp, agent_name, session_id, response_text,
                                 response_length, input_tokens, output_tokens, total_tokens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            ctx.agent_name,
            ctx.session_id,
            response_text,
            len(response_text),
            input_tokens,
            output_tokens,
            input_tokens + output_tokens,
        ))

        conn.commit()
        conn.close()
        return None

    def log_tool_call(self, ctx: CallbackContext, tool_call):
        """Log tool call to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tool_calls (timestamp, agent_name, session_id, tool_name, parameters)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            ctx.agent_name,
            ctx.session_id,
            tool_call.name,
            json.dumps(tool_call.args),
        ))

        conn.commit()
        conn.close()
        return None

    def log_tool_result(self, ctx: CallbackContext, tool_result):
        """Update tool call with result."""
        # Could update the last tool_call record with success/error
        pass

    def query_stats(self, agent_name: str = None):
        """Query usage statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total requests
        if agent_name:
            cursor.execute("SELECT COUNT(*) FROM requests WHERE agent_name = ?", (agent_name,))
        else:
            cursor.execute("SELECT COUNT(*) FROM requests")
        total_requests = cursor.fetchone()[0]

        # Total tokens
        if agent_name:
            cursor.execute("SELECT SUM(total_tokens) FROM responses WHERE agent_name = ?", (agent_name,))
        else:
            cursor.execute("SELECT SUM(total_tokens) FROM responses")
        total_tokens = cursor.fetchone()[0] or 0

        # Tool calls
        if agent_name:
            cursor.execute("SELECT COUNT(*) FROM tool_calls WHERE agent_name = ?", (agent_name,))
        else:
            cursor.execute("SELECT COUNT(*) FROM tool_calls")
        total_tool_calls = cursor.fetchone()[0]

        conn.close()

        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_tool_calls": total_tool_calls,
        }

# Use database logger
db_logger = DatabaseLogger()

agent = LlmAgent(
    name="db_logged_agent",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool],
    before_model_callback=db_logger.log_request,
    after_model_callback=db_logger.log_response,
    before_tool_callback=db_logger.log_tool_call,
    after_tool_callback=db_logger.log_tool_result,
)

# Query stats
stats = db_logger.query_stats("db_logged_agent")
print(f"Total requests: {stats['total_requests']}")
print(f"Total tokens: {stats['total_tokens']}")
```

## Example 5: Real-time Monitoring Dashboard

```python
import time
from collections import deque
from threading import Lock

class RealtimeMonitor:
    """Real-time monitoring with metrics dashboard."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.lock = Lock()

        # Circular buffers for metrics
        self.request_times = deque(maxlen=window_size)
        self.response_times = deque(maxlen=window_size)
        self.token_counts = deque(maxlen=window_size)
        self.tool_calls = deque(maxlen=window_size)

        self.current_request_time = None

    def before_model(self, ctx: CallbackContext, request):
        """Start timing request."""
        self.current_request_time = time.time()
        return None

    def after_model(self, ctx: CallbackContext, response):
        """Calculate latency and log metrics."""
        if self.current_request_time:
            latency = time.time() - self.current_request_time

            with self.lock:
                self.response_times.append(latency)

                # Track tokens
                if hasattr(response, 'usage_metadata'):
                    total_tokens = (response.usage_metadata.prompt_token_count +
                                  response.usage_metadata.candidates_token_count)
                    self.token_counts.append(total_tokens)

        return None

    def before_tool(self, ctx: CallbackContext, tool_call):
        """Track tool calls."""
        with self.lock:
            self.tool_calls.append({
                "timestamp": time.time(),
                "tool": tool_call.name,
            })
        return None

    def get_metrics(self):
        """Get current metrics."""
        with self.lock:
            if not self.response_times:
                return {"status": "no data"}

            return {
                "requests_per_minute": len([
                    t for t in self.request_times
                    if time.time() - t < 60
                ]),
                "avg_latency_ms": sum(self.response_times) / len(self.response_times) * 1000,
                "p95_latency_ms": sorted(self.response_times)[int(len(self.response_times) * 0.95)] * 1000,
                "avg_tokens": sum(self.token_counts) / len(self.token_counts) if self.token_counts else 0,
                "tools_per_minute": len([
                    t for t in self.tool_calls
                    if time.time() - t["timestamp"] < 60
                ]),
                "total_requests": len(self.response_times),
            }

    def print_dashboard(self):
        """Print metrics dashboard."""
        metrics = self.get_metrics()

        print("\n" + "="*50)
        print("AGENT METRICS DASHBOARD")
        print("="*50)
        print(f"Requests/min:     {metrics.get('requests_per_minute', 0)}")
        print(f"Avg Latency:      {metrics.get('avg_latency_ms', 0):.1f} ms")
        print(f"P95 Latency:      {metrics.get('p95_latency_ms', 0):.1f} ms")
        print(f"Avg Tokens:       {metrics.get('avg_tokens', 0):.0f}")
        print(f"Tools/min:        {metrics.get('tools_per_minute', 0)}")
        print(f"Total Requests:   {metrics.get('total_requests', 0)}")
        print("="*50 + "\n")

# Use real-time monitor
monitor = RealtimeMonitor()

agent = LlmAgent(
    name="monitored_agent",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool, database_tool],
    before_model_callback=monitor.before_model,
    after_model_callback=monitor.after_model,
    before_tool_callback=monitor.before_tool,
)

# Print dashboard periodically
import threading

def print_metrics_loop():
    while True:
        time.sleep(10)
        monitor.print_dashboard()

# Start background metrics thread
# metrics_thread = threading.Thread(target=print_metrics_loop, daemon=True)
# metrics_thread.start()
```

## Example 6: Log Rotation and Management

```python
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

class ManagedLogger:
    """Logger with rotation and management."""

    def __init__(self, log_dir: str = "logs"):
        import os
        os.makedirs(log_dir, exist_ok=True)

        # Main log file with size-based rotation
        self.main_logger = logging.getLogger("agent.main")
        main_handler = RotatingFileHandler(
            f"{log_dir}/agent.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
        )
        main_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.main_logger.addHandler(main_handler)
        self.main_logger.setLevel(logging.INFO)

        # Error log file
        self.error_logger = logging.getLogger("agent.errors")
        error_handler = RotatingFileHandler(
            f"{log_dir}/errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s - %(exc_info)s'
        ))
        self.error_logger.addHandler(error_handler)
        self.error_logger.setLevel(logging.ERROR)

        # Daily audit log
        self.audit_logger = logging.getLogger("agent.audit")
        audit_handler = TimedRotatingFileHandler(
            f"{log_dir}/audit.log",
            when="midnight",
            interval=1,
            backupCount=30,  # Keep 30 days
        )
        audit_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        self.audit_logger.addHandler(audit_handler)
        self.audit_logger.setLevel(logging.INFO)

    def log_request(self, ctx: CallbackContext, request):
        """Log request to main log."""
        user_message = request.contents[-1].parts[0].text if request.contents else ""
        self.main_logger.info(f"Request from {ctx.agent_name}: {user_message[:100]}")
        self.audit_logger.info(f"USER_REQUEST|{ctx.session_id}|{user_message[:50]}")
        return None

    def log_response(self, ctx: CallbackContext, response):
        """Log response."""
        if response.candidates:
            response_text = response.candidates[0].content.parts[0].text
            self.main_logger.info(f"Response: {response_text[:100]}")
        return None

    def log_tool_error(self, ctx: CallbackContext, tool_result):
        """Log tool errors."""
        if isinstance(tool_result, dict) and not tool_result.get("success", True):
            error = tool_result.get("error", "Unknown error")
            self.error_logger.error(f"Tool error in {ctx.agent_name}: {error}")
        return None

# Use managed logger
managed_logger = ManagedLogger()

agent = LlmAgent(
    name="managed_logged_agent",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool],
    before_model_callback=managed_logger.log_request,
    after_model_callback=managed_logger.log_response,
    after_tool_callback=managed_logger.log_tool_error,
)
```

## Analyzing Logs

### Example: Parse JSON logs

```python
import json
from collections import Counter
from datetime import datetime

def analyze_jsonl_logs(log_file: str):
    """Analyze JSON line logs."""
    events = []

    with open(log_file, 'r') as f:
        for line in f:
            events.append(json.loads(line))

    # Count events by type
    event_types = Counter(e["event"] for e in events)

    # Calculate average response time
    responses = [e for e in events if e["event"] == "llm_response"]
    if responses:
        avg_tokens = sum(e["tokens"]["total"] for e in responses if "tokens" in e) / len(responses)
    else:
        avg_tokens = 0

    # Find errors
    errors = [e for e in events if "error" in e]

    print(f"Total events: {len(events)}")
    print(f"Event types: {dict(event_types)}")
    print(f"Average tokens: {avg_tokens:.0f}")
    print(f"Errors: {len(errors)}")

    return {
        "total_events": len(events),
        "event_types": dict(event_types),
        "avg_tokens": avg_tokens,
        "errors": errors,
    }

# Analyze logs
stats = analyze_jsonl_logs("agent_logs.jsonl")
```

## Best Practices

1. **Use structured logging** - JSON format enables easy analysis
2. **Rotate log files** - Prevent disk space issues
3. **Separate concerns** - Different log files for errors, audit, debug
4. **Include context** - Agent name, session ID, timestamps
5. **Sanitize sensitive data** - Don't log passwords, API keys
6. **Monitor performance** - Track callback overhead
7. **Archive old logs** - Compress and archive to reduce storage
