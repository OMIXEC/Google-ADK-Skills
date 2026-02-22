# WebSocket Patterns for Streaming Agents

**Production-ready WebSocket server patterns for real-time agent communication.**

## Overview

WebSocket servers enable:
- Real-time bidirectional communication
- Low-latency streaming (text, audio, video)
- Persistent connections
- Multi-client support
- Session management per connection

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Client (Browser, Mobile App)                            │
│   - WebSocket connection                                │
│   - Send text/audio/video                               │
│   - Receive streaming responses                         │
└─────────────────────────────────────────────────────────┘
                           │
                    WebSocket (ws://)
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ FastAPI WebSocket Server                                │
│   - Accept connections                                  │
│   - Route: /ws/{user_id}/{session_id}                   │
│   - Create LiveRequestQueue per connection              │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Runner.run_live()                                       │
│   - Process streaming events                            │
│   - Send responses back to client                       │
└─────────────────────────────────────────────────────────┘
```

## Basic WebSocket Server

### Minimal Example

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.adk.runners import Runner
from google.adk.agents import Agent, LiveRequestQueue
from google.genai import types
import asyncio
import json

app = FastAPI()

# Create agent
agent = Agent(
    name="websocket_agent",
    model="gemini-2.0-flash-live-001",
    instruction="You are a helpful assistant.",
)

runner = Runner(agent=agent, app_name="websocket_app")

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await websocket.accept()
    live_queue = LiveRequestQueue()

    try:
        async def receive_messages():
            """Receive from client, send to agent."""
            while True:
                message = await websocket.receive()

                if "text" in message:
                    data = json.loads(message["text"])
                    content = types.Content(parts=[types.Part(text=data["text"])])
                    live_queue.send_content(content)

        async def send_events():
            """Receive from agent, send to client."""
            async for event in runner.run_live(
                user_id=user_id,
                session_id=session_id,
                live_request_queue=live_queue,
            ):
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if part.text:
                            await websocket.send_json({"type": "text", "text": part.text})

        await asyncio.gather(receive_messages(), send_events())
    except WebSocketDisconnect:
        live_queue.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Complete Patterns

### Pattern 1: Text Streaming Server

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.adk.runners import Runner
from google.adk.agents import Agent, LiveRequestQueue
from google.genai import types
import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Text Streaming Agent Server")

# Create agent once
agent = Agent(
    name="text_agent",
    model="gemini-2.0-flash-live-001",
    instruction="You are a helpful text-based assistant.",
)

runner = Runner(agent=agent, app_name="text_streaming_app")

# RunConfig
run_config = types.RunConfig(
    response_modalities=["TEXT"],
)

@app.websocket("/ws/{user_id}/{session_id}")
async def text_streaming_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str
):
    """WebSocket endpoint for text streaming."""
    await websocket.accept()
    logger.info(f"Client connected: {user_id}/{session_id}")

    live_queue = LiveRequestQueue()

    try:
        async def receive_messages():
            """Receive text messages from client."""
            while True:
                try:
                    message = await websocket.receive()

                    if "text" in message:
                        data = json.loads(message["text"])

                        if data.get("type") == "message":
                            # Send to agent
                            content = types.Content(parts=[
                                types.Part(text=data["text"])
                            ])
                            live_queue.send_content(content)
                            logger.info(f"User message: {data['text']}")

                        elif data.get("type") == "close":
                            break

                except Exception as e:
                    logger.error(f"Receive error: {e}")
                    break

        async def send_events():
            """Send agent responses to client."""
            try:
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
                                logger.info(f"Agent response: {part.text[:50]}...")
            except Exception as e:
                logger.error(f"Send error: {e}")

        # Run both concurrently
        await asyncio.gather(receive_messages(), send_events())

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {user_id}/{session_id}")
    finally:
        live_queue.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
```

### Pattern 2: Audio Streaming Server

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.adk.runners import Runner
from google.adk.agents import Agent, LiveRequestQueue
from google.genai import types
import asyncio
import json
import logging

app = FastAPI(title="Audio Streaming Agent Server")

# Native audio agent
agent = Agent(
    name="audio_agent",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a voice assistant.",
)

runner = Runner(agent=agent, app_name="audio_streaming_app")

# Audio RunConfig with VAD
run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        ),
        voice_activity_detection=types.VoiceActivityDetection(
            disabled=False,
            start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
            end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
        ),
    ),
)

@app.websocket("/ws/{user_id}/{session_id}")
async def audio_streaming_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str
):
    """WebSocket endpoint for audio streaming."""
    await websocket.accept()
    live_queue = LiveRequestQueue()

    try:
        async def receive_audio():
            """Receive audio from client."""
            while True:
                try:
                    message = await websocket.receive()

                    # Binary audio data
                    if "bytes" in message:
                        audio_data = message["bytes"]
                        live_queue.send_realtime(audio_data)

                    # Control messages
                    elif "text" in message:
                        data = json.loads(message["text"])
                        if data.get("type") == "activity_start":
                            live_queue.signal_activity_start()
                        elif data.get("type") == "activity_end":
                            live_queue.signal_activity_end()
                        elif data.get("type") == "close":
                            break

                except Exception as e:
                    print(f"Receive error: {e}")
                    break

        async def send_audio():
            """Send audio responses to client."""
            try:
                async for event in runner.run_live(
                    user_id=user_id,
                    session_id=session_id,
                    live_request_queue=live_queue,
                    run_config=run_config,
                ):
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                # Send audio bytes
                                await websocket.send_bytes(part.inline_data.data)
            except Exception as e:
                print(f"Send error: {e}")

        await asyncio.gather(receive_audio(), send_audio())

    except WebSocketDisconnect:
        pass
    finally:
        live_queue.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Pattern 3: Multimodal Server (Text + Audio)

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.adk.runners import Runner
from google.adk.agents import Agent, LiveRequestQueue
from google.genai import types
import asyncio
import json

app = FastAPI(title="Multimodal Streaming Agent Server")

agent = Agent(
    name="multimodal_agent",
    model="gemini-2.0-flash-live-001",
    instruction="You are a multimodal assistant supporting text and voice.",
)

runner = Runner(agent=agent, app_name="multimodal_app")

run_config = types.RunConfig(
    response_modalities=["TEXT", "AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        )
    ),
)

@app.websocket("/ws/{user_id}/{session_id}")
async def multimodal_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str
):
    """WebSocket endpoint for multimodal streaming."""
    await websocket.accept()
    live_queue = LiveRequestQueue()

    try:
        async def receive_messages():
            """Receive text and audio from client."""
            while True:
                try:
                    message = await websocket.receive()

                    # Text message
                    if "text" in message:
                        data = json.loads(message["text"])

                        if data.get("type") == "text":
                            content = types.Content(parts=[
                                types.Part(text=data["text"])
                            ])
                            live_queue.send_content(content)

                        elif data.get("type") == "image":
                            # Base64 encoded image
                            import base64
                            image_data = base64.b64decode(data["data"])
                            content = types.Content(parts=[
                                types.Part(text=data.get("text", "What's in this image?")),
                                types.Part(inline_data=types.Blob(
                                    mime_type=data["mime_type"],
                                    data=image_data,
                                ))
                            ])
                            live_queue.send_content(content)

                    # Audio bytes
                    elif "bytes" in message:
                        live_queue.send_realtime(message["bytes"])

                except Exception as e:
                    print(f"Receive error: {e}")
                    break

        async def send_responses():
            """Send text and audio responses."""
            try:
                async for event in runner.run_live(
                    user_id=user_id,
                    session_id=session_id,
                    live_request_queue=live_queue,
                    run_config=run_config,
                ):
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            # Send text
                            if part.text:
                                await websocket.send_json({
                                    "type": "text",
                                    "text": part.text,
                                })

                            # Send audio
                            if hasattr(part, 'inline_data') and part.inline_data:
                                await websocket.send_bytes(part.inline_data.data)
            except Exception as e:
                print(f"Send error: {e}")

        await asyncio.gather(receive_messages(), send_responses())

    except WebSocketDisconnect:
        pass
    finally:
        live_queue.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Client Patterns

### JavaScript Client (Text)

```javascript
// Text streaming client
class TextStreamingClient {
    constructor(userId, sessionId) {
        this.ws = new WebSocket(`ws://localhost:8000/ws/${userId}/${sessionId}`);
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        this.ws.onopen = () => {
            console.log("Connected to agent");
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === "text") {
                console.log("Agent:", data.text);
                this.onMessage(data.text);
            }
        };

        this.ws.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        this.ws.onclose = () => {
            console.log("Disconnected from agent");
        };
    }

    sendMessage(text) {
        this.ws.send(JSON.stringify({
            type: "message",
            text: text,
        }));
    }

    close() {
        this.ws.send(JSON.stringify({ type: "close" }));
        this.ws.close();
    }

    onMessage(text) {
        // Override this in implementation
        console.log("Received:", text);
    }
}

// Usage
const client = new TextStreamingClient("user_123", "session_456");

client.onMessage = (text) => {
    document.getElementById("chat").innerHTML += `<p>Agent: ${text}</p>`;
};

client.sendMessage("Hello, how are you?");
```

### JavaScript Client (Audio)

```javascript
// Audio streaming client
class AudioStreamingClient {
    constructor(userId, sessionId) {
        this.ws = new WebSocket(`ws://localhost:8000/ws/${userId}/${sessionId}`);
        this.audioContext = new AudioContext({ sampleRate: 24000 });
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        this.ws.onopen = () => {
            console.log("Audio connection established");
            this.startAudioCapture();
        };

        this.ws.onmessage = async (event) => {
            // Audio response
            if (event.data instanceof Blob) {
                const audioData = await event.data.arrayBuffer();
                this.playAudio(audioData);
            }
        };
    }

    async startAudioCapture() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                // Convert to PCM and send
                this.ws.send(event.data);
            }
        };

        mediaRecorder.start(100); // Send chunks every 100ms
    }

    async playAudio(audioData) {
        const audioBuffer = await this.audioContext.decodeAudioData(audioData);
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);
        source.start();
    }

    close() {
        this.ws.close();
    }
}

// Usage
const audioClient = new AudioStreamingClient("user_123", "session_456");
```

### Python Client

```python
import asyncio
import websockets
import json

async def text_client(user_id: str, session_id: str):
    """Python WebSocket client for text streaming."""
    uri = f"ws://localhost:8000/ws/{user_id}/{session_id}"

    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "type": "message",
            "text": "Hello from Python!",
        }))

        # Receive responses
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "text":
                print(f"Agent: {data['text']}")

# Run client
asyncio.run(text_client("user_123", "session_456"))
```

## Advanced Patterns

### Pattern 4: Connection Management

```python
from fastapi import FastAPI, WebSocket
from typing import Dict
import asyncio

app = FastAPI()

# Track active connections
active_connections: Dict[str, WebSocket] = {}

@app.websocket("/ws/{user_id}/{session_id}")
async def managed_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await websocket.accept()

    # Track connection
    connection_id = f"{user_id}/{session_id}"
    active_connections[connection_id] = websocket

    try:
        # ... streaming logic ...
        pass
    finally:
        # Remove connection
        active_connections.pop(connection_id, None)

@app.post("/broadcast")
async def broadcast_message(message: str):
    """Broadcast message to all connections."""
    for connection in active_connections.values():
        await connection.send_json({"type": "broadcast", "text": message})
```

### Pattern 5: Reconnection Handling

```python
from fastapi import WebSocket
import uuid

# Session persistence
sessions = {}

@app.websocket("/ws/{user_id}")
async def reconnectable_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()

    # Resume or create session
    session_id = sessions.get(user_id, str(uuid.uuid4()))
    sessions[user_id] = session_id

    # Send session ID to client
    await websocket.send_json({"type": "session_id", "id": session_id})

    # ... streaming with session_id ...
```

### Pattern 6: Health Check

```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_connections": len(active_connections),
    }
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### requirements.txt

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
google-genai==0.2.0
google-adk==0.1.0
```

### Docker Compose

```yaml
version: '3.8'

services:
  websocket-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    restart: unless-stopped
```

## Best Practices

1. **Always close LiveRequestQueue** - Prevents resource leaks
2. **Handle WebSocketDisconnect** - Clean up resources
3. **Use asyncio.gather** - Run send/receive concurrently
4. **Track active connections** - Enable broadcasting, monitoring
5. **Implement health checks** - Monitor server status
6. **Add error handling** - Log and recover from errors
7. **Use environment variables** - Secure API keys
8. **Enable CORS for web clients** - Cross-origin requests

## See Also

- LiveRequestQueue: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/live-request-queue.md
- RunConfig: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/run-config.md
- FastAPI WebSocket Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/fastapi-websocket.md
