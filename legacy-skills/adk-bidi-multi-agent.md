# adk-bidi-multi-agent

**Multi-Agent Real-Time Streaming for Google ADK**

Build production-ready multi-agent systems with bidirectional streaming, LiveRequestQueue, native audio models, and WebSocket integration. Create real-time voice assistants, multimodal agents, and coordinated agent teams.

## When to Use

Use this skill when:
- Building real-time voice or multimodal agents
- Implementing bidirectional streaming with LiveRequestQueue
- Creating multi-agent coordination in live sessions
- Using native audio models (`gemini-live-2.5-flash-native-audio`)
- Building WebSocket-based agent servers
- Coordinating multiple agents in real-time

## Quick Start

```bash
# Voice assistant with native audio
/adk-bidi-multi-agent --type "voice" \
  --model "gemini-live-2.5-flash-native-audio"

# Multi-agent supervisor with live streaming
/adk-bidi-multi-agent --type "supervisor" \
  --agents "researcher,analyst,writer"

# WebSocket server for real-time agents
/adk-bidi-multi-agent --type "websocket-server" \
  --modalities "TEXT,AUDIO"
```

## Parameters

```bash
--type "voice|multimodal|supervisor|websocket-server"  # Required
--model "gemini-live-2.5-flash-native-audio"           # Default native audio model
--agents "[agent1,agent2]"                             # For supervisor type
--modalities "TEXT|AUDIO|TEXT,AUDIO"                   # Response modalities
--enable-vad "true|false"                              # Voice Activity Detection
```

## Live Models

| Model | Capabilities |
|-------|-------------|
| `gemini-live-2.5-flash-native-audio` | Native speech-to-speech, voice interactions |
| `gemini-2.0-flash-live-001` | Text + audio streaming |

## Core Components

### 1. LiveSession Wrapper

Manages bidirectional streaming with LiveRequestQueue.

```python
from adk_bidi import LiveSession
from google.adk.runners import Runner

# Create live session
session = LiveSession(
    session_id="user_123",
    user_id="user_123",
    modality="AUDIO",
    enable_vad=True,
)

# Send different content types
session.send_text("Hello, how can I help?")
session.send_audio(audio_bytes, sample_rate=16000)
session.send_image(image_bytes, mime_type="image/jpeg")

# Signal activity
session.signal_activity_start()
session.signal_activity_end()

# Close session
session.close()
```

### 2. Streaming Configurations

Pre-built configurations for common use cases.

```python
from adk_bidi import StreamingPresets

# Voice-only with VAD
config = StreamingPresets.voice_only(
    enable_vad=True,
    start_sensitivity="LOW",
    end_sensitivity="HIGH",
)

# Text and audio multimodal
config = StreamingPresets.text_and_audio()

# Autonomous with proactive behavior
config = StreamingPresets.autonomous_proactive()

# Native audio model
config = StreamingPresets.native_audio()

# Custom configuration
config = StreamingPresets.custom(
    modalities=["TEXT", "AUDIO"],
    enable_vad=True,
    enable_proactivity=True,
    enable_affective_dialog=True,
)
```

### 3. Voice Agent

Native audio agent with personality and interruption handling.

```bash
/adk-bidi-multi-agent --type "voice" \
  --personality "friendly" \
  --enable-interruption "true"
```

**Generated Code:**
```python
from adk_bidi import VoiceAgent
from adk_bidi.agents.voice_agent import VoicePersonality, VoiceConfig

# Create voice agent with personality
agent = VoiceAgent(
    name="voice_assistant",
    instruction="You are a helpful voice assistant.",
    voice_config=VoiceConfig(
        personality=VoicePersonality.FRIENDLY,
        speaking_rate="normal",
        enable_emotions=True,
        enable_interruption=True,
        use_native_audio=True,  # Uses gemini-live-2.5-flash-native-audio
    ),
)

# Or use personality shorthand
agent = VoiceAgent(
    name="voice_assistant",
    instruction="You are a helpful assistant.",
    personality=VoicePersonality.PROFESSIONAL,
)

# Available personalities
# VoicePersonality.PROFESSIONAL - Business-appropriate
# VoicePersonality.FRIENDLY - Warm, approachable
# VoicePersonality.CASUAL - Relaxed, informal
# VoicePersonality.FORMAL - Highly formal
# VoicePersonality.ENTHUSIASTIC - Energetic, positive
# VoicePersonality.CALM - Soothing, measured
```

### 4. Multimodal Agent

Process text, audio, images, and video in real-time.

```bash
/adk-bidi-multi-agent --type "multimodal" \
  --modalities "TEXT,AUDIO,IMAGE"
```

**Generated Code:**
```python
from adk_bidi import MultimodalAgent
from adk_bidi.agents.multimodal_agent import MultimodalConfig

# Create multimodal agent
agent = MultimodalAgent(
    name="multimodal_assistant",
    instruction="You can see, hear, and read.",
    multimodal_config=MultimodalConfig(
        enable_text=True,
        enable_audio=True,
        enable_image=True,
        enable_video=False,
        response_modalities=["TEXT", "AUDIO"],
        image_analysis_detail="high",
    ),
)

# Process different modalities
await agent.process_text("What do you see?")
await agent.process_audio(audio_bytes, duration=2.5)
await agent.process_image(image_bytes, description="User's photo")
await agent.process_video_frame(frame_bytes, frame_number=1, timestamp=0.0)

# Get modality summary
summary = agent.get_modality_summary()
```

### 5. Multi-Agent Supervisor

Coordinate multiple agents in real-time sessions.

```bash
/adk-bidi-multi-agent --type "supervisor" \
  --agents "researcher,analyst,writer"
```

**Generated Code:**
```python
from google.adk.agents import Agent
from adk_bidi import MultiAgentSupervisor, SharedMemory

# Create specialist agents
researcher = Agent(
    name="researcher",
    model="gemini-live-2.5-flash-native-audio",
    description="Research specialist for finding information",
    instruction="You are a research specialist.",
)

analyst = Agent(
    name="analyst",
    model="gemini-live-2.5-flash-native-audio",
    description="Data analyst for interpreting findings",
    instruction="You are a data analyst.",
)

writer = Agent(
    name="writer",
    model="gemini-live-2.5-flash-native-audio",
    description="Technical writer for creating reports",
    instruction="You are a technical writer.",
)

# Create supervisor with shared memory
shared_memory = SharedMemory()
supervisor = MultiAgentSupervisor(
    agents=[researcher, analyst, writer],
    shared_memory=shared_memory,
    instruction="Coordinate tasks by delegating to specialists.",
)

# Handle request (supervisor routes to appropriate agent)
agent = await supervisor.handle_request(
    user_input="Research AI trends and write a report",
    session_id="session_123",
)

# Use with Runner
runner = Runner(
    agent=supervisor.get_supervisor_agent(),
    app_name="multi_agent_app",
)
```

### 6. WebSocket Server

FastAPI WebSocket server for real-time agent interactions.

```bash
/adk-bidi-multi-agent --type "websocket-server" \
  --modalities "TEXT,AUDIO"
```

**Generated Code:**
```python
from adk_bidi.core.websocket_server import create_websocket_app, MultiAgentWebSocketServer
from adk_bidi import MultiAgentSupervisor, StreamingPresets
from google.adk.runners import Runner
from google.adk.agents import Agent
import uvicorn

# Create agents
assistant = Agent(
    name="assistant",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a helpful real-time assistant.",
)

# Create supervisor
supervisor = MultiAgentSupervisor(agents=[assistant])

# Create runner
runner = Runner(
    agent=supervisor.get_supervisor_agent(),
    app_name="realtime_app",
)

# Create WebSocket app
app = create_websocket_app(
    runner=runner,
    run_config=StreamingPresets.text_and_audio(),
)

# Run server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Client Connection:**
```javascript
// JavaScript WebSocket client
const ws = new WebSocket("ws://localhost:8000/ws/user123/session456");

// Send text
ws.send(JSON.stringify({ type: "text", text: "Hello!" }));

// Send audio (PCM 16-bit, 16kHz)
ws.send(audioArrayBuffer);

// Receive events
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.content?.parts) {
        for (const part of data.content.parts) {
            if (part.text) console.log("Text:", part.text);
            if (part.inline_data) console.log("Audio:", part.inline_data);
        }
    }
};
```

## Full Example: Voice Assistant with Multi-Agent Support

```python
"""Complete voice assistant with multi-agent coordination."""
import asyncio
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
from adk_bidi import (
    VoiceAgent,
    MultiAgentSupervisor,
    SharedMemory,
    StreamingPresets,
)
from adk_bidi.agents.voice_agent import VoicePersonality

# 1. Create specialist agents
knowledge_agent = Agent(
    name="knowledge",
    model="gemini-live-2.5-flash-native-audio",
    description="Answers factual questions",
    instruction="You answer factual questions accurately.",
)

task_agent = Agent(
    name="task_helper",
    model="gemini-live-2.5-flash-native-audio",
    description="Helps with tasks and reminders",
    instruction="You help users with tasks and reminders.",
)

# 2. Create voice agent as interface
voice_agent = VoiceAgent(
    name="voice_interface",
    instruction="You are a friendly voice assistant.",
    personality=VoicePersonality.FRIENDLY,
)

# 3. Create supervisor
shared_memory = SharedMemory()
supervisor = MultiAgentSupervisor(
    agents=[knowledge_agent, task_agent, voice_agent.adk_agent],
    shared_memory=shared_memory,
)

# 4. Set up runner
runner = Runner(
    agent=supervisor.get_supervisor_agent(),
    app_name="voice_assistant",
)

# 5. Run live session
async def run_voice_session():
    live_queue = LiveRequestQueue()
    run_config = StreamingPresets.native_audio()

    async def stream_events():
        async for event in runner.run_live(
            user_id="user_123",
            session_id="session_456",
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            # Process events
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if part.text:
                        print(f"Agent: {part.text}")
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Handle audio response
                        pass
            yield event

    # Send user input
    content = types.Content(parts=[types.Part(text="What's the weather like?")])
    live_queue.send_content(content)

    # Process responses
    async for event in stream_events():
        pass

    live_queue.close()

asyncio.run(run_voice_session())
```

## 4-Phase Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: App Initialization (once at startup)           │
│   - Create Agent with live model                        │
│   - Create Runner with app_name                         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 2: Session Initialization (per connection)        │
│   - Create LiveRequestQueue                             │
│   - Configure RunConfig (modalities, VAD, etc.)         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3: Streaming Loop (during session)                │
│   - runner.run_live() yields events                     │
│   - live_queue.send_content() for user input            │
│   - live_queue.send_realtime() for audio/video          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 4: Cleanup (session end)                          │
│   - live_queue.close()                                  │
│   - Clean up resources                                  │
└─────────────────────────────────────────────────────────┘
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

- **adk-memory-manager**: Multi-agent memory system
- **adk-autonomous-agent**: Self-reasoning autonomous agents
- **adk-multi-agent-orchestrator**: Agent team patterns
