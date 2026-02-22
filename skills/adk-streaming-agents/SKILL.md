---
name: adk-streaming-agents
description: Build real-time streaming agents with LiveRequestQueue, Voice Activity Detection, native audio models, and multimodal streaming (text, audio, video). Supports bidirectional message queues, RunConfig streaming configurations, LiveContentOrTurn wrappers, and WebSocket server patterns for production-ready streaming agents.
version: 1.0.0
---

# adk-streaming-agents

**Real-Time Streaming Patterns for Google ADK**

Build production-ready streaming agents with LiveRequestQueue, Voice Activity Detection, native audio integration, and multimodal streaming. Create real-time conversational AI with bidirectional communication, WebSocket servers, and low-latency responses.

## When to Use

Use this skill when:
- Building real-time streaming agents with bidirectional communication
- Implementing LiveRequestQueue for message queuing
- Configuring Voice Activity Detection (VAD) for speech start/end
- Using native audio models for speech-to-speech
- Building multimodal streaming (text, audio, video)
- Creating WebSocket servers for streaming agents
- Optimizing latency for real-time interactions

## Quick Start

```bash
# Text streaming agent
/adk-streaming-agents --type "text-streaming" \
  --model "gemini-2.0-flash-live-001"

# Audio streaming with VAD
/adk-streaming-agents --type "audio-streaming" \
  --enable-vad "true" \
  --voice "Aoede"

# Multimodal streaming (text + audio)
/adk-streaming-agents --type "multimodal-streaming" \
  --modalities "TEXT,AUDIO"

# WebSocket server
/adk-streaming-agents --type "websocket-server" \
  --port "8000"
```

## Parameters

```bash
--type "text-streaming|audio-streaming|multimodal-streaming|websocket-server"  # Required
--model "gemini-2.0-flash-live-001"                     # Default live model
--modalities "TEXT|AUDIO|TEXT,AUDIO|TEXT,AUDIO,VIDEO"   # Response modalities
--enable-vad "true|false"                                # Voice Activity Detection
--voice "Aoede|Charon|Kore|Fenrir|Puck"                 # Prebuilt voice name
--port "8000"                                            # WebSocket server port
```

## Streaming Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Client (User Input)                                     │
│   - Text messages                                       │
│   - Audio streams (PCM, WAV)                           │
│   - Video frames                                        │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ LiveRequestQueue                                        │
│   - Bidirectional message queue                         │
│   - send_content() for structured messages              │
│   - send_realtime() for raw audio/video                │
│   - Signal activity start/end                           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Runner.run_live()                                       │
│   - Async generator yielding events                     │
│   - RunConfig for streaming settings                    │
│   - user_id + session_id for state                      │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Streaming Events (LiveContentOrTurn)                    │
│   - content.parts (text, audio, video)                  │
│   - Server events (turn start/end)                      │
│   - Tool use/results                                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Client (Agent Response)                                 │
│   - Incremental text chunks                             │
│   - Audio stream (real-time speech)                     │
│   - Multimodal content                                  │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. LiveRequestQueue

Bidirectional message queue for streaming communication.

```python
from google.adk.agents import LiveRequestQueue
from google.genai import types

# Create queue
live_queue = LiveRequestQueue()

# Send structured content (text, images)
content = types.Content(parts=[
    types.Part(text="Hello!"),
])
live_queue.send_content(content)

# Send realtime data (raw audio/video bytes)
audio_bytes = b"..."  # PCM 16-bit, 16kHz mono
live_queue.send_realtime(audio_bytes)

# Signal user activity (for VAD)
live_queue.signal_activity_start()
live_queue.signal_activity_end()

# Close queue when done
live_queue.close()
```

**Key Methods:**
- `send_content(content)` - Send structured Content with text/images
- `send_realtime(data)` - Send raw audio/video bytes
- `signal_activity_start()` - User started speaking
- `signal_activity_end()` - User stopped speaking
- `close()` - Close the queue and end session

For full details: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/live-request-queue.md

### 2. RunConfig for Streaming

Configure streaming behavior and modalities.

```python
from google.genai import types

# Basic streaming configuration
run_config = types.RunConfig(
    response_modalities=["TEXT", "AUDIO"],
)

# With speech configuration
run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Aoede"  # Warm, expressive voice
            )
        )
    ),
)

# With Voice Activity Detection
run_config = types.RunConfig(
    response_modalities=["TEXT", "AUDIO"],
    speech_config=types.SpeechConfig(
        voice_activity_detection=types.VoiceActivityDetection(
            disabled=False,
            start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
            end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
        ),
    ),
)
```

**Available Voices:**
- `Aoede` - Warm, expressive (default)
- `Charon` - Deep, authoritative
- `Kore` - Clear, professional
- `Fenrir` - Energetic, dynamic
- `Puck` - Playful, friendly

For full details: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/run-config.md

### 3. Voice Activity Detection (VAD)

Detect when user starts/stops speaking.

```python
from google.genai import types

vad_config = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
)

run_config = types.RunConfig(
    speech_config=types.SpeechConfig(
        voice_activity_detection=vad_config,
    ),
)
```

**Sensitivity Levels:**

| Sensitivity | Start Threshold | End Threshold |
|-------------|----------------|---------------|
| LOW | More lenient - catches soft speech | Longer pause needed |
| MEDIUM | Balanced | Balanced |
| HIGH | Stricter - ignores background noise | Shorter pause needed |

**Best Practices:**
- **Noisy environments:** HIGH start, LOW end (avoid false triggers)
- **Quiet environments:** LOW start, HIGH end (catch all speech)
- **Default:** LOW start, HIGH end (natural conversation)

For full details: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/vad-config.md

### 4. Native Audio Models

Speech-to-speech models without text intermediary.

```python
from google.adk.agents import Agent

# Native audio model
agent = Agent(
    name="native_voice_agent",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a voice assistant with natural speech.",
)

# Standard live model (text + audio)
agent = Agent(
    name="live_agent",
    model="gemini-2.0-flash-live-001",
    instruction="You are a multimodal assistant.",
)
```

**Model Comparison:**

| Model | Capabilities | Use Case |
|-------|-------------|----------|
| `gemini-live-2.5-flash-native-audio` | Native speech-to-speech | Voice-only interactions |
| `gemini-2.0-flash-live-001` | Text + audio streaming | Multimodal apps |

## Streaming Patterns

### Pattern 1: Text Streaming

Incremental text responses for chat interfaces.

```bash
/adk-streaming-agents --type "text-streaming"
```

**Generated Code:**
```python
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types

# Create agent
agent = Agent(
    name="text_streamer",
    model="gemini-2.0-flash-live-001",
    instruction="You are a helpful assistant.",
)

# Create runner
runner = Runner(agent=agent, app_name="text_streaming_app")

# Create live queue
live_queue = LiveRequestQueue()

# Configure text-only streaming
run_config = types.RunConfig(
    response_modalities=["TEXT"],
)

# Run streaming loop
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=run_config,
):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if part.text:
                print(f"Agent: {part.text}", end="", flush=True)

# Send user message
content = types.Content(parts=[types.Part(text="Hello!")])
live_queue.send_content(content)

# Close when done
live_queue.close()
```

For full example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/text-streaming.md

### Pattern 2: Audio Streaming

Real-time speech with Voice Activity Detection.

```bash
/adk-streaming-agents --type "audio-streaming" --enable-vad "true"
```

**Generated Code:**
```python
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import pyaudio

# Create native audio agent
agent = Agent(
    name="audio_streamer",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a voice assistant.",
)

runner = Runner(agent=agent, app_name="audio_streaming_app")

# Configure audio streaming with VAD
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

# Audio capture setup
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=1024,
)

# Live queue
live_queue = LiveRequestQueue()

# Capture and send audio
def capture_audio():
    while True:
        audio_data = stream.read(1024)
        live_queue.send_realtime(audio_data)

# Process streaming responses
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=run_config,
):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Play audio response
                audio_bytes = part.inline_data.data
                # Send to audio output
```

For full example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/audio-streaming.md

### Pattern 3: Multimodal Streaming

Combined text, audio, and video streaming.

```bash
/adk-streaming-agents --type "multimodal-streaming" --modalities "TEXT,AUDIO"
```

**Generated Code:**
```python
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types

# Create multimodal agent
agent = Agent(
    name="multimodal_streamer",
    model="gemini-2.0-flash-live-001",
    instruction="You can see, hear, and respond with text and speech.",
)

runner = Runner(agent=agent, app_name="multimodal_app")

# Configure multimodal streaming
run_config = types.RunConfig(
    response_modalities=["TEXT", "AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
)

live_queue = LiveRequestQueue()

# Send multimodal content
content = types.Content(parts=[
    types.Part(text="What do you see in this image?"),
    types.Part(inline_data=types.Blob(
        mime_type="image/jpeg",
        data=image_bytes,
    )),
])
live_queue.send_content(content)

# Process multimodal response
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=run_config,
):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if part.text:
                print(f"Text: {part.text}")
            if hasattr(part, 'inline_data') and part.inline_data:
                print(f"Audio: {len(part.inline_data.data)} bytes")
```

### Pattern 4: WebSocket Server

Production-ready WebSocket server for streaming agents.

```bash
/adk-streaming-agents --type "websocket-server" --port "8000"
```

**Generated Code:**
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
    instruction="You are a helpful real-time assistant.",
)

runner = Runner(agent=agent, app_name="websocket_app")

# Run config
run_config = types.RunConfig(
    response_modalities=["TEXT", "AUDIO"],
)

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await websocket.accept()
    live_queue = LiveRequestQueue()

    async def receive_messages():
        """Receive messages from client and send to queue."""
        try:
            while True:
                message = await websocket.receive()

                # Handle text messages
                if "text" in message:
                    data = json.loads(message["text"])
                    if data.get("type") == "text":
                        content = types.Content(parts=[
                            types.Part(text=data["text"])
                        ])
                        live_queue.send_content(content)

                # Handle binary (audio/video)
                elif "bytes" in message:
                    live_queue.send_realtime(message["bytes"])
        except WebSocketDisconnect:
            live_queue.close()

    async def send_events():
        """Process agent events and send to client."""
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
                        if hasattr(part, 'inline_data') and part.inline_data:
                            await websocket.send_bytes(part.inline_data.data)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            live_queue.close()

    # Run both tasks concurrently
    await asyncio.gather(receive_messages(), send_events())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

For full details: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/websocket-patterns.md

## Event Types

### LiveContentOrTurn Events

```python
# Content event (agent response)
if hasattr(event, 'content') and event.content:
    for part in event.content.parts:
        if part.text:
            print(f"Text: {part.text}")
        if hasattr(part, 'inline_data') and part.inline_data:
            # Audio/video data
            data = part.inline_data.data
            mime_type = part.inline_data.mime_type

# Turn event (conversation markers)
if hasattr(event, 'server_content'):
    # Turn start, turn end, etc.
    pass

# Tool events
if hasattr(event, 'tool_call'):
    # Agent called a tool
    pass

if hasattr(event, 'tool_response'):
    # Tool returned result
    pass
```

## Latency Optimization

**Best Practices:**
1. **Use streaming models** - `gemini-2.0-flash-live-001` or `gemini-live-2.5-flash-native-audio`
2. **Minimize RunConfig overhead** - Only enable needed modalities
3. **Buffer audio appropriately** - 1024-2048 frames for real-time
4. **Use WebSocket for production** - Lower latency than HTTP polling
5. **Enable VAD correctly** - Reduce unnecessary processing
6. **Stream incrementally** - Don't wait for complete response

**Latency Metrics:**
- **Text streaming:** 50-200ms time-to-first-token
- **Audio streaming:** 200-500ms for first audio chunk
- **Native audio:** 100-300ms (no text intermediary)

## Full Example: Voice Assistant with Streaming

```python
"""Complete voice assistant with streaming, VAD, and native audio."""
import asyncio
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import pyaudio

# 1. Create native audio agent
agent = Agent(
    name="voice_assistant",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a friendly voice assistant.",
)

# 2. Create runner
runner = Runner(agent=agent, app_name="voice_app")

# 3. Configure streaming with VAD
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

# 4. Audio setup
p = pyaudio.PyAudio()
input_stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=1024,
)
output_stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=24000,
    output=True,
)

# 5. Run streaming session
async def run_voice_session():
    live_queue = LiveRequestQueue()

    async def capture_audio():
        """Capture microphone audio and send to queue."""
        while True:
            audio_data = input_stream.read(1024, exception_on_overflow=False)
            live_queue.send_realtime(audio_data)
            await asyncio.sleep(0.01)

    async def process_responses():
        """Process agent responses and play audio."""
        async for event in runner.run_live(
            user_id="user_123",
            session_id="session_456",
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Play audio response
                        audio_bytes = part.inline_data.data
                        output_stream.write(audio_bytes)

    # Run both tasks
    await asyncio.gather(capture_audio(), process_responses())

asyncio.run(run_voice_session())
```

## Environment Variables

```bash
# Google AI
GOOGLE_API_KEY=your_gemini_api_key

# OR for Vertex AI
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=TRUE
```

## Related Skills

- **adk-bidi-multi-agent**: Multi-agent streaming coordination
- **adk-agent-lifecycle**: Agent initialization patterns
- **adk-production-deployment**: Deploy streaming agents to production

## References

- LiveRequestQueue: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/live-request-queue.md
- RunConfig: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/run-config.md
- VAD Configuration: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/vad-config.md
- WebSocket Patterns: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/websocket-patterns.md
- Text Streaming Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/text-streaming.md
- Audio Streaming Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/audio-streaming.md
