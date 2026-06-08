---
name: adk-bidi-live
description: ADK bidirectional streaming and Live API expert covering real-time audio/video, WebSocket communication, LiveRequestQueue, Gemini Live API, and native audio models (gemini-live-2.5-flash-native-audio). Use when building real-time voice agents, implementing streaming chat, or working with multimodal live interactions.
---

# adk-bidi-live - ADK Bidi-Streaming & Live API Expert

## Instructions

You are a senior engineer specializing in ADK's bidirectional streaming and Live API integration.

### When Activated

1. Read streaming documentation at `references/` folder:
   - `references/index.md` - Streaming overview
   - `references/custom-streaming-ws.md` - WebSocket streaming (32KB guide)
   - `references/custom-streaming.md` - Custom streaming patterns (30KB)
   - `references/streaming-tools.md` - Tools in streaming context
   - `references/configuration.md` - Streaming configuration
2. Also see: `gcp-blogs/.claude/skills/bidi/SKILL.md` for existing bidi skill
3. Also see: `gcp-blogs/20251125_bidi_guide/article.md` for comprehensive guide

### Core Knowledge Areas

1. **4-Phase Lifecycle**: App init → Session init → Streaming loop → Cleanup
2. **Live API Integration**: Gemini Live API, Vertex AI Live API
3. **LiveRequestQueue**: Bidirectional message passing
4. **Native Audio**: `gemini-live-2.5-flash-native-audio` for real-time voice
5. **WebSocket Patterns**: FastAPI integration, concurrent task management

### Live Models

| Model | Capabilities |
|-------|-------------|
| `gemini-2.0-flash-live-001` | Text + audio streaming |
| `gemini-live-2.5-flash-native-audio` | Native audio processing |

### 4-Phase Lifecycle

```python
# Phase 1: App Initialization (once at startup)
agent = Agent(
    model="gemini-2.0-flash-live-001",  # or gemini-live-2.5-flash-native-audio
    tools=[google_search],
    instruction="You are a helpful voice assistant"
)
runner = InMemoryRunner(agent=agent, app_name="voice-app")

# Phase 2: Session Initialization (per connection)
live_request_queue = LiveRequestQueue()
run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["TEXT", "AUDIO"]
)

# Phase 3: Streaming Loop
async def streaming_session():
    async for event in runner.run_live(
        session_id=session_id,
        live_request_queue=live_request_queue,
        run_config=run_config
    ):
        yield event  # Stream to client

# Phase 4: Cleanup
live_request_queue.close()
```

### FastAPI WebSocket Pattern

```python
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    live_request_queue = LiveRequestQueue()

    async def agent_to_client():
        async for event in runner.run_live(...):
            await websocket.send_json(event.model_dump())

    async def client_to_agent():
        async for message in websocket.iter_text():
            data = json.loads(message)
            content = types.Content(parts=[types.Part(text=data["text"])])
            live_request_queue.send_content(content)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(agent_to_client())
        tg.create_task(client_to_agent())
```

### Response Modalities

```python
# Text only
run_config = RunConfig(response_modalities=["TEXT"])

# Audio only
run_config = RunConfig(response_modalities=["AUDIO"])

# Text + Audio (multimodal)
run_config = RunConfig(response_modalities=["TEXT", "AUDIO"])
```

### Key Components

- `LiveRequestQueue`: Queue for sending user input to model
- `live_request_queue.send_content()`: Send text/audio content
- `live_request_queue.close()`: Signal end of session
- `runner.run_live()`: Async generator yielding live events
