# LiveRequestQueue Reference

**Bidirectional message queue for streaming communication between client and agent.**

## Overview

`LiveRequestQueue` is the core component for streaming agents in Google ADK. It provides a bidirectional queue that:
- Accepts user input (text, audio, video, images)
- Sends messages to the agent during live sessions
- Manages conversation flow with activity signals
- Handles both structured content and raw realtime data

## Basic Usage

```python
from google.adk.agents import LiveRequestQueue
from google.genai import types

# Create queue
live_queue = LiveRequestQueue()

# Send content
content = types.Content(parts=[types.Part(text="Hello!")])
live_queue.send_content(content)

# Close when done
live_queue.close()
```

## API Reference

### Constructor

```python
live_queue = LiveRequestQueue()
```

No parameters needed. Creates an empty queue ready to accept messages.

### Methods

#### send_content(content: Content)

Send structured content to the agent.

```python
from google.genai import types

# Text message
content = types.Content(parts=[
    types.Part(text="Hello, how are you?")
])
live_queue.send_content(content)

# Text with image
content = types.Content(parts=[
    types.Part(text="What do you see?"),
    types.Part(inline_data=types.Blob(
        mime_type="image/jpeg",
        data=image_bytes,
    ))
])
live_queue.send_content(content)

# Multiple parts
content = types.Content(parts=[
    types.Part(text="Analyze this data:"),
    types.Part(inline_data=types.Blob(
        mime_type="application/json",
        data=json_bytes,
    ))
])
live_queue.send_content(content)
```

**When to use:** Sending structured messages with text, images, or other non-realtime data.

#### send_realtime(data: bytes)

Send raw audio or video bytes to the agent.

```python
# Send audio chunk (PCM 16-bit, 16kHz mono)
audio_chunk = b"..."  # Raw audio bytes
live_queue.send_realtime(audio_chunk)

# Send video frame
video_frame = b"..."  # Raw video frame bytes
live_queue.send_realtime(video_frame)
```

**Format requirements:**
- **Audio:** PCM 16-bit, 16kHz, mono (single channel)
- **Video:** Raw frame bytes (format depends on model)

**When to use:** Streaming audio or video in real-time.

#### signal_activity_start()

Signal that user has started an activity (e.g., started speaking).

```python
# User started speaking
live_queue.signal_activity_start()

# Send audio
live_queue.send_realtime(audio_bytes)
```

**When to use:**
- Voice Activity Detection (VAD) enabled
- User starts speaking
- Helps agent understand when to listen

#### signal_activity_end()

Signal that user has stopped an activity (e.g., stopped speaking).

```python
# User stopped speaking
live_queue.signal_activity_end()
```

**When to use:**
- Voice Activity Detection (VAD) enabled
- User stops speaking
- Triggers agent to process complete utterance

#### close()

Close the queue and end the streaming session.

```python
live_queue.close()
```

**When to use:** Session is complete, cleanup needed.

## Usage Patterns

### Pattern 1: Text Chat Streaming

```python
from google.adk.agents import LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types

live_queue = LiveRequestQueue()

# Send user message
def send_message(text: str):
    content = types.Content(parts=[types.Part(text=text)])
    live_queue.send_content(content)

# Use with runner
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
):
    # Process events
    pass

# Send messages
send_message("Hello!")
send_message("How are you?")

# Close when done
live_queue.close()
```

### Pattern 2: Audio Streaming with VAD

```python
import pyaudio
from google.adk.agents import LiveRequestQueue

live_queue = LiveRequestQueue()

# Audio capture setup
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=1024,
)

# VAD state tracking
is_speaking = False

def process_audio_chunk(audio_data: bytes, vad_detected: bool):
    global is_speaking

    # Detected start of speech
    if vad_detected and not is_speaking:
        live_queue.signal_activity_start()
        is_speaking = True

    # Send audio
    live_queue.send_realtime(audio_data)

    # Detected end of speech
    if not vad_detected and is_speaking:
        live_queue.signal_activity_end()
        is_speaking = False

# Capture and process
while True:
    audio_data = stream.read(1024)
    vad_detected = detect_voice_activity(audio_data)  # Your VAD logic
    process_audio_chunk(audio_data, vad_detected)
```

### Pattern 3: Multimodal Input

```python
from google.adk.agents import LiveRequestQueue
from google.genai import types

live_queue = LiveRequestQueue()

# Send text + image
def send_multimodal(text: str, image_bytes: bytes):
    content = types.Content(parts=[
        types.Part(text=text),
        types.Part(inline_data=types.Blob(
            mime_type="image/jpeg",
            data=image_bytes,
        ))
    ])
    live_queue.send_content(content)

# Send text + audio
def send_text_with_audio(text: str, audio_bytes: bytes):
    # First send text
    content = types.Content(parts=[types.Part(text=text)])
    live_queue.send_content(content)

    # Then stream audio
    live_queue.send_realtime(audio_bytes)

send_multimodal("What's in this image?", image_data)
```

### Pattern 4: WebSocket Integration

```python
from fastapi import WebSocket
from google.adk.agents import LiveRequestQueue
from google.genai import types
import json

async def handle_websocket(websocket: WebSocket):
    live_queue = LiveRequestQueue()

    try:
        while True:
            message = await websocket.receive()

            # Text message
            if "text" in message:
                data = json.loads(message["text"])
                if data["type"] == "text":
                    content = types.Content(parts=[
                        types.Part(text=data["text"])
                    ])
                    live_queue.send_content(content)
                elif data["type"] == "activity_start":
                    live_queue.signal_activity_start()
                elif data["type"] == "activity_end":
                    live_queue.signal_activity_end()

            # Binary message (audio/video)
            elif "bytes" in message:
                live_queue.send_realtime(message["bytes"])

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        live_queue.close()
```

## Common Patterns

### Queue Lifecycle

```
1. Create LiveRequestQueue
2. Pass to runner.run_live()
3. Send messages via send_content() or send_realtime()
4. Close queue when session ends
```

### Message Types

| Method | Data Type | Use Case |
|--------|-----------|----------|
| `send_content()` | Structured Content | Text, images, documents |
| `send_realtime()` | Raw bytes | Audio streams, video frames |
| `signal_activity_start()` | Signal | User started speaking |
| `signal_activity_end()` | Signal | User stopped speaking |

### Audio Format

For `send_realtime()` with audio:
- **Format:** PCM (Pulse Code Modulation)
- **Bit depth:** 16-bit
- **Sample rate:** 16kHz
- **Channels:** Mono (1 channel)

```python
# Example with pyaudio
stream = p.open(
    format=pyaudio.paInt16,  # 16-bit
    channels=1,              # Mono
    rate=16000,              # 16kHz
    input=True,
)

audio_chunk = stream.read(1024)
live_queue.send_realtime(audio_chunk)
```

## Best Practices

1. **Create queue before runner.run_live()** - Queue must exist before starting live session
2. **Always close the queue** - Prevents resource leaks
3. **Use send_content for structured data** - Text, images, JSON
4. **Use send_realtime for audio/video** - Raw streaming data
5. **Signal activity for VAD** - Improves speech recognition accuracy
6. **Handle queue in try/finally** - Ensure cleanup on errors

```python
live_queue = LiveRequestQueue()
try:
    async for event in runner.run_live(
        user_id="user_123",
        session_id="session_456",
        live_request_queue=live_queue,
    ):
        # Process events
        pass
finally:
    live_queue.close()
```

## Error Handling

```python
from google.adk.agents import LiveRequestQueue

live_queue = LiveRequestQueue()

try:
    # Send content
    live_queue.send_content(content)
except Exception as e:
    print(f"Failed to send content: {e}")
finally:
    # Always close
    live_queue.close()
```

## Integration with Runner

```python
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types

agent = Agent(name="streaming_agent", model="gemini-2.0-flash-live-001")
runner = Runner(agent=agent, app_name="app")

live_queue = LiveRequestQueue()

# Run live session with queue
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=types.RunConfig(response_modalities=["TEXT"]),
):
    # Process streaming events
    if hasattr(event, 'content') and event.content:
        print(event.content)

# Send messages during session
live_queue.send_content(types.Content(parts=[types.Part(text="Hello!")]))
```

## See Also

- RunConfig: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/run-config.md
- VAD Configuration: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/vad-config.md
- WebSocket Patterns: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/websocket-patterns.md
