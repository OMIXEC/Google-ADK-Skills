---
name: ADK Real-Time & Voice Agents
description: This skill should be used when the user asks to "build a voice agent", "create a real-time streaming agent", "live session setup", "multimodal agent", "audio agent", or "bidirectional streaming". Provides comprehensive guidance for implementing voice agents, real-time streaming, and multimodal interaction.
version: 1.0.0
---

# ADK Real-Time & Voice Agents

Real-time agents enable live interaction with voice, audio, and streaming responses. This skill covers voice agents using Gemini's native audio model, WebSocket streaming, and multimodal input.

## Voice Agents with Gemini Live

Gemini 2.5 Flash Native Audio supports native voice interaction:

```python
from adk_bidi.agents import VoiceAgent

voice_agent = VoiceAgent(
    model="gemini-live-2.5-flash-native-audio",
    api_key=os.getenv("GOOGLE_API_KEY")
)

# Stream audio input and output
response = voice_agent.stream_audio(
    input_audio=input_stream,
    output_audio=output_stream
)
```

### Voice Agent Features

- Native audio processing (no transcription step)
- Low latency response
- Natural conversation flow
- Bidirectional streaming
- Real-time interruption support

### Building a Voice Agent

```python
class FitnessCoachVoiceAgent(VoiceAgent):
    def __init__(self):
        super().__init__(
            model="gemini-live-2.5-flash-native-audio",
            system_prompt="""You are a motivational fitness coach.
            Respond naturally to voice input with workout advice.
            Keep responses conversational and encouraging."""
        )

    def handle_workout_request(self, user_audio_stream):
        """Process user's voice request and respond."""
        return self.stream_audio(user_audio_stream)
```

## Streaming Responses

Agents can stream responses for real-time display:

```python
response_stream = agent.ask_streaming(prompt)

for chunk in response_stream:
    print(chunk, end="", flush=True)  # Real-time display
```

Benefits:
- Faster perceived response time
- Better UX for long responses
- Live data updates
- Interactive experiences

## Bidirectional Communication with WebSockets

Enable live communication with WebSocket servers:

```python
from adk_bidi.core import WebSocketServer
from adk_bidi.agents import StreamingAgent

class LiveAgent(StreamingAgent):
    def __init__(self):
        super().__init__()
        self.ws_server = WebSocketServer(port=8000)
        self.ws_server.on_message(self.handle_message)

    async def handle_message(self, message, client_id):
        """Handle incoming WebSocket message."""
        response = await self.ask_async(message)

        # Stream response back
        await self.ws_server.send_stream(
            response,
            client_id=client_id
        )
```

### WebSocket Client

```python
import websockets
import asyncio

async def send_to_agent(message):
    async with websockets.connect("ws://localhost:8000") as ws:
        await ws.send(message)

        # Stream responses
        async for response in ws:
            print(response, end="", flush=True)

asyncio.run(send_to_agent("Hello, agent!"))
```

## Multimodal Input

Agents can accept text, audio, images, and video:

```python
from adk_bidi.agents import MultimodalAgent

agent = MultimodalAgent()

# Text input
response = agent.ask("Explain this concept")

# Audio input
response = agent.process_audio(audio_file)

# Image input
response = agent.analyze_image(image_file)

# Video input
response = agent.analyze_video(video_file)

# Mixed input
response = agent.process(
    text="Analyze this image: ",
    image=image_file
)
```

## Building Real-Time Systems

### Architecture

```
User → WebSocket → Agent Server → LLM
                       ↓
                   Streaming Output
                       ↓
                 Real-time Display
```

### Implementation Pattern

```python
import asyncio
import json
from fastapi import FastAPI, WebSocketException
from fastapi.websockets import WebSocket

app = FastAPI()
agent = MyStreamingAgent()

@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Receive message
            message = await websocket.receive_text()

            # Stream response
            async for chunk in agent.ask_streaming_async(message):
                await websocket.send_text(json.dumps({
                    "type": "stream",
                    "content": chunk
                }))

            # Signal completion
            await websocket.send_text(json.dumps({
                "type": "complete"
            }))

    except WebSocketException:
        pass
```

## Event-Based Communication

Agents can emit events for real-time updates:

```python
class EventDrivenAgent(Agent):
    def __init__(self):
        super().__init__()
        self.event_bus = EventBus()

    def process_with_events(self, request: str):
        # Emit start event
        self.event_bus.emit("agent:started", {"request": request})

        # Process
        for step in self._reasoning_steps:
            self.event_bus.emit("agent:step", {
                "step": step,
                "progress": "..."
            })

        # Emit result
        self.event_bus.emit("agent:complete", {
            "result": final_result
        })
```

## Low-Latency Optimization

For responsive real-time systems:

### Use Streaming

```python
# Instead of waiting for complete response
response = agent.ask(prompt)  # Slow

# Stream response chunks
for chunk in agent.ask_streaming(prompt):  # Fast
    send_to_client(chunk)
```

### Use Async

```python
# Non-blocking, multiple concurrent connections
async def handle_request(request):
    return await agent.ask_async(request)

# Handle many concurrent requests
results = await asyncio.gather(*[
    handle_request(req) for req in requests
])
```

### Cache Results

```python
@functools.lru_cache(maxsize=100)
def ask_with_cache(prompt: str):
    return agent.ask(prompt)
```

## Error Handling

For robust real-time systems:

```python
try:
    async for chunk in agent.ask_streaming_async(prompt):
        await websocket.send_text(chunk)

except ConnectionError:
    # Network error
    await websocket.send_text(json.dumps({
        "type": "error",
        "message": "Connection lost"
    }))

except AgentTimeoutError:
    # Agent took too long
    await websocket.send_text(json.dumps({
        "type": "error",
        "message": "Request timeout"
    }))

except Exception as e:
    # Other errors
    await websocket.send_text(json.dumps({
        "type": "error",
        "message": str(e)
    }))
```

## Supporting Resources

### References
- **`references/voice-agents.md`** - Voice agent implementation details
- **`references/streaming-architecture.md`** - Streaming and real-time patterns
- **`references/websocket-guide.md`** - WebSocket server setup

### Examples
- **`examples/voice-fitness-coach.py`** - Voice agent example
- **`examples/streaming-agent.py`** - Streaming response agent
- **`examples/websocket-agent-server.py`** - WebSocket server example

## Next Steps

1. **Choose interaction mode** - Voice, streaming, or WebSocket?
2. **Build agent** - Implement using appropriate class
3. **Set up audio/streaming** - Configure input/output
4. **Test locally** - Verify real-time interaction
5. **Deploy** - Use adk-production-deployment skill with WebSocket support

See **adk-custom-agent-builder** skill for agent implementation details.
