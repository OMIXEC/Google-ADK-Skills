---
wave: 3
depends_on: [01-PLAN.md, 04-PLAN.md]
files_modified:
  - skills/adk-streaming-agents/SKILL.md
  - skills/adk-bidi-multi-agent.md
autonomous: false
requirements: [adk-streaming, realtime]
---

# Plan 06: Enhance Streaming and Real-Time Agent Skills

## Objective
Create comprehensive streaming skill and enhance bidi-multi-agent with all ADK streaming patterns: LiveRequestQueue, Voice Activity Detection, native audio, and multimodal streaming.

## must_haves
- [ ] LiveRequestQueue patterns fully documented
- [ ] Voice Activity Detection (VAD) configuration
- [ ] Native audio model integration
- [ ] Multimodal streaming (text, audio, video)
- [ ] WebSocket server patterns

## Tasks

<task id="6.1" type="create">
<title>Create Streaming Agents Skill</title>
<description>
Comprehensive streaming patterns from ADK:

**Streaming Components:**
1. **LiveRequestQueue** - Bidirectional message queue
2. **RunConfig** - Streaming configuration
3. **LiveContentOrTurn** - Content wrapper for streaming
4. **Voice Activity Detection** - Start/end detection

**Streaming Modes:**
1. **Text Streaming** - Incremental text responses
2. **Audio Streaming** - Real-time speech
3. **Multimodal Streaming** - Combined modalities
4. **Native Audio** - Direct speech-to-speech

**Code Example:**
```python
from google.adk.runners import Runner
from google.adk.agents import Agent, LiveRequestQueue
from google.genai import types

# Create agent with live model
agent = Agent(
    name="streaming_agent",
    model="gemini-2.0-flash-live-001",
    instruction="You are a real-time assistant.",
)

runner = Runner(agent=agent, app_name="streaming_app")

# Create live request queue
live_queue = LiveRequestQueue()

# Configure streaming
run_config = types.RunConfig(
    response_modalities=["TEXT", "AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
)

# Run streaming session
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=run_config,
):
    if event.content:
        for part in event.content.parts:
            if part.text:
                print(f"Text: {part.text}")
            if hasattr(part, 'inline_data') and part.inline_data:
                # Process audio data
                pass

# Send user input
content = types.Content(parts=[types.Part(text="Hello!")])
live_queue.send_content(content)

# Close when done
live_queue.close()
```
</description>
<files>
- skills/adk-streaming-agents/SKILL.md
- skills/adk-streaming-agents/references/live-request-queue.md
- skills/adk-streaming-agents/references/run-config.md
- skills/adk-streaming-agents/references/vad-config.md
- skills/adk-streaming-agents/examples/text-streaming.md
- skills/adk-streaming-agents/examples/audio-streaming.md
</files>
</task>

<task id="6.2" type="enhance">
<title>Enhance Bidi Multi-Agent Skill</title>
<description>
Upgrade existing skill with additional streaming patterns:

**New Patterns:**
1. **Interruption Handling** - User interrupts agent
2. **Turn Management** - Coordinated speaking
3. **Audio Format Conversion** - PCM, WAV, MP3
4. **Latency Optimization** - Real-time performance

**Native Audio Models:**
- `gemini-live-2.5-flash-native-audio` - Gemini Live API
- `gemini-2.0-flash-live-001` - Standard live model

**Code Example:**
```python
from google.adk.agents import Agent
from google.genai import types

# Native audio agent
native_agent = Agent(
    name="native_voice",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a voice assistant with native speech.",
)

# Configure VAD
run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_activity_detection=types.VoiceActivityDetection(
            disabled=False,
            start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
            end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
        ),
    ),
)
```
</description>
<files>
- skills/adk-bidi-multi-agent.md
- skills/adk-bidi-multi-agent/references/native-audio.md
- skills/adk-bidi-multi-agent/references/interruption-handling.md
</files>
</task>

<task id="6.3" type="create">
<title>Create WebSocket Integration Reference</title>
<description>
WebSocket patterns for real-time agent servers:

**Server Patterns:**
1. FastAPI WebSocket endpoint
2. Connection management
3. Session state per connection
4. Audio format handling

**Client Patterns:**
1. JavaScript/TypeScript client
2. Python asyncio client
3. Reconnection handling
4. Audio capture/playback

**Code Example:**
```python
from fastapi import FastAPI, WebSocket
from google.adk.runners import Runner
from google.adk.agents import LiveRequestQueue
import asyncio

app = FastAPI()

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await websocket.accept()
    live_queue = LiveRequestQueue()

    async def receive_messages():
        while True:
            data = await websocket.receive_bytes()
            # Process audio or text
            live_queue.send_realtime(data)

    async def send_events():
        async for event in runner.run_live(
            user_id=user_id,
            session_id=session_id,
            live_request_queue=live_queue,
        ):
            await websocket.send_json(event.to_dict())

    await asyncio.gather(receive_messages(), send_events())
```
</description>
<files>
- skills/adk-streaming-agents/references/websocket-patterns.md
- skills/adk-streaming-agents/examples/fastapi-websocket.md
- skills/adk-streaming-agents/examples/client-integration.md
</files>
</task>

## Verification Criteria
- [ ] Streaming skill covers all ADK streaming patterns
- [ ] VAD configuration is complete
- [ ] Native audio integration documented
- [ ] WebSocket examples work with ADK

## Acceptance
Streaming skills enable real-time voice and multimodal agents.
