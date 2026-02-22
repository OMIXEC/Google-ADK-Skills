# Text Streaming Example

**Complete example of text streaming agent with incremental responses.**

## Overview

This example demonstrates:
- Text-only streaming responses
- LiveRequestQueue for message queuing
- Incremental text rendering
- Multiple message handling
- Session management

## Complete Implementation

### Server Code

```python
"""Text streaming agent with incremental responses."""
import asyncio
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types

# 1. Create text streaming agent
agent = Agent(
    name="text_streamer",
    model="gemini-2.0-flash-live-001",
    instruction="You are a helpful assistant. Provide detailed, informative responses.",
)

# 2. Create runner
runner = Runner(agent=agent, app_name="text_streaming_app")

# 3. Configure text-only streaming
run_config = types.RunConfig(
    response_modalities=["TEXT"],
)

async def run_text_streaming_session():
    """Run a text streaming session."""
    live_queue = LiveRequestQueue()

    async def send_messages():
        """Send user messages to agent."""
        messages = [
            "Hello! Tell me about streaming in AI.",
            "What are the benefits of streaming responses?",
            "How does it compare to batch processing?",
        ]

        for msg in messages:
            print(f"\n\nUser: {msg}")
            content = types.Content(parts=[types.Part(text=msg)])
            live_queue.send_content(content)

            # Wait for response to complete
            await asyncio.sleep(5)

        # Close queue when done
        await asyncio.sleep(2)
        live_queue.close()

    async def receive_responses():
        """Process streaming text responses."""
        print("\n" + "="*60)
        print("Starting text streaming session...")
        print("="*60)

        try:
            async for event in runner.run_live(
                user_id="user_123",
                session_id="session_456",
                live_request_queue=live_queue,
                run_config=run_config,
            ):
                # Process text content
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if part.text:
                            # Print incrementally (no newline)
                            print(part.text, end="", flush=True)

        except Exception as e:
            print(f"\nError: {e}")

    # Run both tasks concurrently
    await asyncio.gather(send_messages(), receive_responses())

if __name__ == "__main__":
    asyncio.run(run_text_streaming_session())
```

## Example Output

```
============================================================
Starting text streaming session...
============================================================


User: Hello! Tell me about streaming in AI.
Agent: Hello! Streaming in AI refers to the ability to process
and deliver information incrementally, rather than waiting for
the complete response. This provides several advantages:

1. **Improved user experience** - Users see responses immediately
2. **Lower perceived latency** - First token appears quickly
3. **Better resource utilization** - Process chunks as they arrive
4. **Graceful degradation** - Partial responses better than nothing


User: What are the benefits of streaming responses?
Agent: Streaming responses offer multiple benefits:

**For Users:**
- Immediate feedback reduces waiting time
- Can read early parts while later parts generate
- Better engagement with real-time progress

**For Systems:**
- More efficient memory usage
- Can start downstream processing earlier
- Better handling of long responses
- Improved scalability


User: How does it compare to batch processing?
Agent: Streaming vs. batch processing comparison:

**Streaming:**
✓ Low latency - first token in milliseconds
✓ Progressive rendering - immediate user feedback
✓ Memory efficient - process chunks incrementally
✗ More complex implementation
✗ Network overhead per chunk

**Batch:**
✓ Simpler implementation
✓ Lower network overhead
✗ High latency - wait for complete response
✗ Poor UX for long responses
✗ Memory spikes for large responses

For interactive applications, streaming is generally preferred.
```

## Chat Interface Implementation

### With User Input

```python
"""Interactive text streaming chat."""
import asyncio
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import sys

agent = Agent(
    name="chat_agent",
    model="gemini-2.0-flash-live-001",
    instruction="You are a helpful assistant. Be concise but informative.",
)

runner = Runner(agent=agent, app_name="chat_app")

run_config = types.RunConfig(
    response_modalities=["TEXT"],
)

async def interactive_chat():
    """Interactive chat session."""
    live_queue = LiveRequestQueue()

    async def user_input_loop():
        """Handle user input."""
        while True:
            try:
                # Read user input (non-blocking)
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "\nYou: "
                )

                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("Goodbye!")
                    live_queue.close()
                    break

                # Send to agent
                content = types.Content(parts=[types.Part(text=user_input)])
                live_queue.send_content(content)

            except Exception as e:
                print(f"Input error: {e}")
                break

    async def agent_response_loop():
        """Process agent responses."""
        try:
            async for event in runner.run_live(
                user_id="user_123",
                session_id="session_456",
                live_request_queue=live_queue,
                run_config=run_config,
            ):
                if hasattr(event, 'content') and event.content:
                    # Track if we've started printing
                    started = False

                    for part in event.content.parts:
                        if part.text:
                            if not started:
                                print("\nAgent: ", end="", flush=True)
                                started = True
                            print(part.text, end="", flush=True)

                    # New line after complete response
                    if started:
                        print()

        except Exception as e:
            print(f"\nAgent error: {e}")

    # Run both loops
    await asyncio.gather(user_input_loop(), agent_response_loop())

if __name__ == "__main__":
    print("="*60)
    print("Interactive Text Streaming Chat")
    print("Type 'exit' or 'quit' to end the conversation")
    print("="*60)

    asyncio.run(interactive_chat())
```

## Web Interface (FastAPI + HTML)

### Server

```python
"""Web-based text streaming chat."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import asyncio
import json

app = FastAPI()

agent = Agent(
    name="web_chat_agent",
    model="gemini-2.0-flash-live-001",
    instruction="You are a helpful web assistant.",
)

runner = Runner(agent=agent, app_name="web_chat_app")

run_config = types.RunConfig(
    response_modalities=["TEXT"],
)

@app.get("/")
async def get_chat_page():
    """Serve chat interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Text Streaming Chat</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; }
            #chat { height: 400px; border: 1px solid #ccc; padding: 10px; overflow-y: scroll; }
            .message { margin: 10px 0; }
            .user { color: blue; }
            .agent { color: green; }
            #input { width: 80%; padding: 10px; }
            #send { padding: 10px 20px; }
        </style>
    </head>
    <body>
        <h1>Text Streaming Chat</h1>
        <div id="chat"></div>
        <input type="text" id="input" placeholder="Type your message...">
        <button id="send">Send</button>

        <script>
            const ws = new WebSocket("ws://localhost:8000/ws/user_123/session_456");
            const chat = document.getElementById("chat");
            const input = document.getElementById("input");
            const send = document.getElementById("send");

            let currentMessage = null;

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === "text") {
                    if (!currentMessage) {
                        currentMessage = document.createElement("div");
                        currentMessage.className = "message agent";
                        currentMessage.innerHTML = "<strong>Agent:</strong> ";
                        chat.appendChild(currentMessage);
                    }

                    currentMessage.innerHTML += data.text;
                    chat.scrollTop = chat.scrollHeight;
                }

                if (data.type === "complete") {
                    currentMessage = null;
                }
            };

            send.onclick = () => {
                const text = input.value.trim();
                if (text) {
                    // Show user message
                    const userMsg = document.createElement("div");
                    userMsg.className = "message user";
                    userMsg.innerHTML = `<strong>You:</strong> ${text}`;
                    chat.appendChild(userMsg);

                    // Send to agent
                    ws.send(JSON.stringify({ type: "message", text: text }));

                    input.value = "";
                    chat.scrollTop = chat.scrollHeight;
                }
            };

            input.addEventListener("keypress", (e) => {
                if (e.key === "Enter") send.click();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    """WebSocket endpoint for text streaming."""
    await websocket.accept()
    live_queue = LiveRequestQueue()

    try:
        async def receive_messages():
            while True:
                message = await websocket.receive()
                if "text" in message:
                    data = json.loads(message["text"])
                    if data.get("type") == "message":
                        content = types.Content(parts=[types.Part(text=data["text"])])
                        live_queue.send_content(content)

        async def send_responses():
            async for event in runner.run_live(
                user_id=user_id,
                session_id=session_id,
                live_request_queue=live_queue,
                run_config=run_config,
            ):
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if part.text:
                            await websocket.send_json({
                                "type": "text",
                                "text": part.text,
                            })

        await asyncio.gather(receive_messages(), send_responses())

    except WebSocketDisconnect:
        pass
    finally:
        live_queue.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Testing

### Unit Test

```python
"""Test text streaming functionality."""
import asyncio
import pytest
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types

@pytest.mark.asyncio
async def test_text_streaming():
    """Test text streaming returns expected content."""
    agent = Agent(
        name="test_agent",
        model="gemini-2.0-flash-live-001",
        instruction="You are a test assistant. Respond with 'OK' to any message.",
    )

    runner = Runner(agent=agent, app_name="test_app")
    run_config = types.RunConfig(response_modalities=["TEXT"])

    live_queue = LiveRequestQueue()

    # Send test message
    content = types.Content(parts=[types.Part(text="Test")])
    live_queue.send_content(content)

    # Collect response
    response_text = ""
    async for event in runner.run_live(
        user_id="test_user",
        session_id="test_session",
        live_request_queue=live_queue,
        run_config=run_config,
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

        # Break after first response
        if response_text:
            break

    live_queue.close()

    assert "OK" in response_text
```

## Best Practices

1. **Print incrementally** - Use `flush=True` and `end=""` for real-time display
2. **Handle empty responses** - Check for content existence
3. **Close queue properly** - Always call `live_queue.close()`
4. **Use asyncio.gather** - Run send/receive concurrently
5. **Add error handling** - Catch exceptions in both loops

## See Also

- Audio Streaming Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/audio-streaming.md
- LiveRequestQueue Reference: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/live-request-queue.md
- WebSocket Patterns: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/websocket-patterns.md
