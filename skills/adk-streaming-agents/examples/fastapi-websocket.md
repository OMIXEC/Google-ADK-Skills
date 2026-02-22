# FastAPI WebSocket Server Example

**Production-ready WebSocket server for streaming agents.**

## Overview

Complete FastAPI WebSocket server with:
- Text and audio streaming support
- Connection management
- Session persistence
- Health checks
- Error handling
- Logging

## Complete Implementation

```python
"""Production-ready FastAPI WebSocket server for streaming agents."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import asyncio
import json
import logging
from typing import Dict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ADK Streaming Agent Server",
    description="WebSocket server for real-time agent streaming",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create agent
agent = Agent(
    name="streaming_agent",
    model="gemini-2.0-flash-live-001",
    instruction="You are a helpful real-time assistant.",
)

# Create runner
runner = Runner(agent=agent, app_name="streaming_server")

# Track active connections
active_connections: Dict[str, WebSocket] = {}
session_stats: Dict[str, dict] = {}

# RunConfig presets
RUN_CONFIGS = {
    "text": types.RunConfig(
        response_modalities=["TEXT"],
    ),
    "audio": types.RunConfig(
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
    ),
    "multimodal": types.RunConfig(
        response_modalities=["TEXT", "AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
            )
        ),
    ),
}

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "ADK Streaming Agent Server",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws/{user_id}/{session_id}?mode={text|audio|multimodal}",
            "health": "/health",
            "stats": "/stats",
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_connections": len(active_connections),
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/stats")
async def get_stats():
    """Get session statistics."""
    return {
        "active_connections": len(active_connections),
        "total_sessions": len(session_stats),
        "sessions": session_stats,
    }

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str,
    mode: str = "text"
):
    """
    WebSocket endpoint for streaming agent.

    Query parameters:
        mode: text|audio|multimodal (default: text)
    """
    # Validate mode
    if mode not in RUN_CONFIGS:
        await websocket.close(code=1003, reason=f"Invalid mode: {mode}")
        return

    # Accept connection
    await websocket.accept()

    connection_id = f"{user_id}/{session_id}"
    logger.info(f"Connection accepted: {connection_id} (mode: {mode})")

    # Track connection
    active_connections[connection_id] = websocket
    session_stats[connection_id] = {
        "user_id": user_id,
        "session_id": session_id,
        "mode": mode,
        "connected_at": datetime.utcnow().isoformat(),
        "messages_sent": 0,
        "messages_received": 0,
    }

    # Create live queue
    live_queue = LiveRequestQueue()

    # Get run config for mode
    run_config = RUN_CONFIGS[mode]

    try:
        async def receive_messages():
            """Receive messages from client and send to agent."""
            nonlocal session_stats

            while True:
                try:
                    message = await websocket.receive()

                    # Text message
                    if "text" in message:
                        data = json.loads(message["text"])
                        logger.debug(f"Received text: {data}")

                        if data.get("type") == "message":
                            # Send text to agent
                            content = types.Content(parts=[
                                types.Part(text=data["text"])
                            ])
                            live_queue.send_content(content)
                            session_stats[connection_id]["messages_sent"] += 1

                        elif data.get("type") == "image":
                            # Send image with text
                            import base64
                            image_data = base64.b64decode(data["data"])
                            content = types.Content(parts=[
                                types.Part(text=data.get("text", "What's in this image?")),
                                types.Part(inline_data=types.Blob(
                                    mime_type=data.get("mime_type", "image/jpeg"),
                                    data=image_data,
                                ))
                            ])
                            live_queue.send_content(content)
                            session_stats[connection_id]["messages_sent"] += 1

                        elif data.get("type") == "activity_start":
                            live_queue.signal_activity_start()

                        elif data.get("type") == "activity_end":
                            live_queue.signal_activity_end()

                        elif data.get("type") == "close":
                            logger.info(f"Client requested close: {connection_id}")
                            break

                    # Binary message (audio/video)
                    elif "bytes" in message:
                        audio_data = message["bytes"]
                        live_queue.send_realtime(audio_data)
                        logger.debug(f"Received audio: {len(audio_data)} bytes")

                except WebSocketDisconnect:
                    logger.info(f"Client disconnected: {connection_id}")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "error": "Invalid JSON format"
                    })
                except Exception as e:
                    logger.error(f"Receive error: {e}", exc_info=True)
                    break

        async def send_events():
            """Process agent events and send to client."""
            nonlocal session_stats

            try:
                async for event in runner.run_live(
                    user_id=user_id,
                    session_id=session_id,
                    live_request_queue=live_queue,
                    run_config=run_config,
                ):
                    # Process content
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            # Text response
                            if part.text:
                                await websocket.send_json({
                                    "type": "text",
                                    "text": part.text,
                                })
                                session_stats[connection_id]["messages_received"] += 1
                                logger.debug(f"Sent text: {part.text[:50]}...")

                            # Audio/video response
                            if hasattr(part, 'inline_data') and part.inline_data:
                                await websocket.send_bytes(part.inline_data.data)
                                logger.debug(f"Sent audio: {len(part.inline_data.data)} bytes")

                    # Handle server events
                    if hasattr(event, 'server_content'):
                        await websocket.send_json({
                            "type": "server_event",
                            "event": str(event.server_content),
                        })

            except WebSocketDisconnect:
                logger.info(f"Client disconnected during send: {connection_id}")
            except Exception as e:
                logger.error(f"Send error: {e}", exc_info=True)

        # Run both tasks concurrently
        await asyncio.gather(receive_messages(), send_events())

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Cleanup
        live_queue.close()
        active_connections.pop(connection_id, None)

        # Update session stats
        if connection_id in session_stats:
            session_stats[connection_id]["disconnected_at"] = datetime.utcnow().isoformat()

        logger.info(f"Connection closed: {connection_id}")

@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Starting ADK Streaming Agent Server")
    logger.info(f"Agent: {agent.name}")
    logger.info(f"Model: {agent.model}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down ADK Streaming Agent Server")

    # Close all active connections
    for connection_id, websocket in list(active_connections.items()):
        try:
            await websocket.close(code=1001, reason="Server shutdown")
        except Exception as e:
            logger.error(f"Error closing connection {connection_id}: {e}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )
```

## Running the Server

### Development

```bash
# Install dependencies
pip install fastapi uvicorn[standard] google-genai google-adk

# Set API key
export GOOGLE_API_KEY=your_api_key

# Run server
python server.py
```

### Production with Uvicorn

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Production with Gunicorn

```bash
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY server.py .

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### requirements.txt

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
google-genai==0.2.0
google-adk==0.1.0
```

### Build and Run

```bash
# Build image
docker build -t adk-streaming-server .

# Run container
docker run -d \
  -p 8000:8000 \
  -e GOOGLE_API_KEY=your_api_key \
  --name adk-server \
  adk-streaming-server
```

## Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# OR for Vertex AI
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Optional
LOG_LEVEL=INFO
MAX_CONNECTIONS=100
```

## Testing

### Test Health Endpoint

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "active_connections": 0,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Test Stats Endpoint

```bash
curl http://localhost:8000/stats
```

**Response:**
```json
{
  "active_connections": 2,
  "total_sessions": 5,
  "sessions": {
    "user_123/session_456": {
      "user_id": "user_123",
      "session_id": "session_456",
      "mode": "text",
      "connected_at": "2024-01-15T10:25:00.000Z",
      "messages_sent": 5,
      "messages_received": 5
    }
  }
}
```

### Test WebSocket Connection

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/user_123/session_456?mode=text"

    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "type": "message",
            "text": "Hello, agent!"
        }))

        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        print(f"Agent: {data['text']}")

asyncio.run(test_websocket())
```

## Monitoring

### Prometheus Metrics

```python
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

# Metrics
connections_total = Counter('websocket_connections_total', 'Total WebSocket connections')
connections_active = Gauge('websocket_connections_active', 'Active WebSocket connections')
message_duration = Histogram('message_processing_duration_seconds', 'Message processing duration')

# Add metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Update metrics in endpoint
@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(...):
    connections_total.inc()
    connections_active.inc()

    try:
        # ... existing code ...
        pass
    finally:
        connections_active.dec()
```

### Logging

```python
# Configure structured logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## Security

### Add Authentication

```python
from fastapi import Header, HTTPException

async def verify_token(authorization: str = Header(None)):
    """Verify authentication token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ")[1]
    # Verify token (implement your logic)
    if not is_valid_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    return token

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str,
    token: str = Header(None)
):
    # Verify token before accepting
    if not verify_websocket_token(token):
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()
    # ... rest of implementation
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.websocket("/ws/{user_id}/{session_id}")
@limiter.limit("10/minute")
async def websocket_endpoint(...):
    # ... implementation
    pass
```

## See Also

- Client Integration: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/client-integration.md
- WebSocket Patterns: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/websocket-patterns.md
- Text Streaming Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/text-streaming.md
