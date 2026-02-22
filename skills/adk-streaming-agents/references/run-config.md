# RunConfig Reference

**Streaming configuration for agent behavior, modalities, voice, and VAD.**

## Overview

`RunConfig` controls how streaming agents behave:
- Response modalities (TEXT, AUDIO, VIDEO)
- Speech configuration (voice, VAD)
- System instructions override
- Streaming-specific settings

## Basic Usage

```python
from google.genai import types

# Text-only streaming
config = types.RunConfig(
    response_modalities=["TEXT"],
)

# Audio streaming with voice
config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
)

# Use with runner
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=config,
):
    # Process events
    pass
```

## API Reference

### RunConfig

```python
config = types.RunConfig(
    response_modalities=["TEXT", "AUDIO"],  # List of modalities
    speech_config=speech_config,             # Optional SpeechConfig
    system_instruction=instruction,          # Optional override
)
```

**Parameters:**
- `response_modalities`: List of output modalities (`["TEXT"]`, `["AUDIO"]`, `["TEXT", "AUDIO"]`)
- `speech_config`: Speech configuration (voice, VAD)
- `system_instruction`: Override agent's instruction for this session

### SpeechConfig

```python
speech_config = types.SpeechConfig(
    voice_config=voice_config,                # Voice configuration
    voice_activity_detection=vad_config,      # VAD configuration
)
```

**Parameters:**
- `voice_config`: Configure voice for audio responses
- `voice_activity_detection`: Configure VAD for speech detection

### VoiceConfig

```python
voice_config = types.VoiceConfig(
    prebuilt_voice_config=types.PrebuiltVoiceConfig(
        voice_name="Aoede"
    )
)
```

**Available voices:**
- `Aoede` - Warm, expressive (default)
- `Charon` - Deep, authoritative
- `Kore` - Clear, professional
- `Fenrir` - Energetic, dynamic
- `Puck` - Playful, friendly

### VoiceActivityDetection

```python
vad_config = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
)
```

**Parameters:**
- `disabled`: Enable/disable VAD (default: `False`)
- `start_of_speech_sensitivity`: Detection threshold for speech start
- `end_of_speech_sensitivity`: Detection threshold for speech end

For full VAD details: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/vad-config.md

## Configuration Patterns

### Pattern 1: Text-Only Streaming

For chat interfaces without audio.

```python
from google.genai import types

config = types.RunConfig(
    response_modalities=["TEXT"],
)

# Use with runner
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=config,
):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if part.text:
                print(part.text, end="", flush=True)
```

**Best for:**
- Chat interfaces
- Text-only applications
- Lower latency requirements

### Pattern 2: Audio-Only Streaming

For voice assistants without text.

```python
from google.genai import types

config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
)

async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=config,
):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Process audio
                audio_bytes = part.inline_data.data
```

**Best for:**
- Voice-only interfaces
- Hands-free applications
- Native audio models

### Pattern 3: Multimodal Streaming (Text + Audio)

For rich interfaces with both text and speech.

```python
from google.genai import types

config = types.RunConfig(
    response_modalities=["TEXT", "AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        )
    ),
)

async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=config,
):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if part.text:
                print(f"Text: {part.text}")
            if hasattr(part, 'inline_data') and part.inline_data:
                print(f"Audio: {len(part.inline_data.data)} bytes")
```

**Best for:**
- Accessible applications
- Multi-device support
- Fallback options

### Pattern 4: Voice with VAD

For natural voice conversations with automatic turn detection.

```python
from google.genai import types

config = types.RunConfig(
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
```

**Best for:**
- Natural conversations
- Automatic turn-taking
- Reduced false triggers

### Pattern 5: Override System Instruction

Temporarily change agent behavior for a session.

```python
from google.genai import types

config = types.RunConfig(
    response_modalities=["TEXT"],
    system_instruction="You are now a Python expert. Answer only Python questions.",
)

# Agent uses override instruction instead of original
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=config,
):
    # Agent follows override instruction
    pass
```

**Best for:**
- Session-specific behavior
- A/B testing
- User preferences

## Voice Characteristics

### Aoede (Default)

**Characteristics:**
- Warm, expressive
- Natural inflection
- Friendly tone

**Best for:**
- General assistants
- Customer service
- Conversational AI

```python
voice_config = types.VoiceConfig(
    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
)
```

### Charon

**Characteristics:**
- Deep, authoritative
- Clear pronunciation
- Professional tone

**Best for:**
- News reading
- Announcements
- Formal applications

```python
voice_config = types.VoiceConfig(
    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
)
```

### Kore

**Characteristics:**
- Clear, professional
- Neutral tone
- Precise articulation

**Best for:**
- Business applications
- Technical support
- Educational content

```python
voice_config = types.VoiceConfig(
    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
)
```

### Fenrir

**Characteristics:**
- Energetic, dynamic
- Enthusiastic tone
- Upbeat delivery

**Best for:**
- Entertainment
- Motivational content
- Youth-oriented apps

```python
voice_config = types.VoiceConfig(
    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Fenrir")
)
```

### Puck

**Characteristics:**
- Playful, friendly
- Casual tone
- Approachable style

**Best for:**
- Games
- Children's apps
- Casual interactions

```python
voice_config = types.VoiceConfig(
    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
)
```

## Complete Examples

### Example 1: Text Chat

```python
from google.genai import types
from google.adk.runners import Runner
from google.adk.agents import Agent, LiveRequestQueue

agent = Agent(name="chat_agent", model="gemini-2.0-flash-live-001")
runner = Runner(agent=agent, app_name="chat_app")

config = types.RunConfig(
    response_modalities=["TEXT"],
)

live_queue = LiveRequestQueue()

async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=config,
):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if part.text:
                print(part.text, end="", flush=True)
```

### Example 2: Voice Assistant

```python
from google.genai import types
from google.adk.runners import Runner
from google.adk.agents import Agent, LiveRequestQueue

agent = Agent(
    name="voice_agent",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a helpful voice assistant.",
)
runner = Runner(agent=agent, app_name="voice_app")

config = types.RunConfig(
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

live_queue = LiveRequestQueue()

async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=config,
):
    # Process audio responses
    pass
```

### Example 3: Multimodal Assistant

```python
from google.genai import types
from google.adk.runners import Runner
from google.adk.agents import Agent, LiveRequestQueue

agent = Agent(
    name="multimodal_agent",
    model="gemini-2.0-flash-live-001",
    instruction="You are a multimodal assistant.",
)
runner = Runner(agent=agent, app_name="multimodal_app")

config = types.RunConfig(
    response_modalities=["TEXT", "AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        )
    ),
)

live_queue = LiveRequestQueue()

async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=config,
):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if part.text:
                print(f"Text: {part.text}")
            if hasattr(part, 'inline_data') and part.inline_data:
                print(f"Audio: {len(part.inline_data.data)} bytes")
```

## Best Practices

1. **Match modalities to use case** - Don't enable unnecessary modalities
2. **Choose appropriate voice** - Match voice personality to application
3. **Configure VAD for environment** - Adjust sensitivity based on noise
4. **Cache RunConfig** - Reuse configuration objects
5. **Test voice options** - Evaluate different voices with users

## Modality Matrix

| Modality | Use Case | Latency | Bandwidth |
|----------|----------|---------|-----------|
| TEXT only | Chat apps | Low | Low |
| AUDIO only | Voice assistants | Medium | High |
| TEXT + AUDIO | Accessible apps | Medium | High |
| All modalities | Rich apps | High | Very High |

## Performance Tips

1. **TEXT-only is fastest** - Lowest latency, smallest bandwidth
2. **AUDIO increases latency** - Speech synthesis adds processing time
3. **Multiple modalities multiply overhead** - Only enable what you need
4. **Native audio models are faster** - Use `gemini-live-2.5-flash-native-audio` for voice-only

## See Also

- LiveRequestQueue: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/live-request-queue.md
- VAD Configuration: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/vad-config.md
- WebSocket Patterns: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/websocket-patterns.md
