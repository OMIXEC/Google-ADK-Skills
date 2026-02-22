# Native Audio Models

**Speech-to-speech models without text intermediary for natural voice interactions.**

## Overview

Native audio models process speech directly without converting to text:
- Lower latency (no text transcription)
- Natural prosody and emotion preservation
- Direct speech-to-speech pipeline
- Better for voice-only applications

## Available Models

### gemini-live-2.5-flash-native-audio

**Capabilities:**
- Native speech-to-speech
- Voice emotion and prosody
- Real-time streaming
- No text intermediary

**Use cases:**
- Voice assistants
- Phone bots
- Voice-only interfaces
- Natural conversation

```python
from google.adk.agents import Agent

agent = Agent(
    name="native_voice_agent",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a friendly voice assistant.",
)
```

### gemini-2.0-flash-live-001

**Capabilities:**
- Text + audio streaming
- Multimodal input/output
- Text transcription available
- Flexible modalities

**Use cases:**
- Multimodal apps
- Chat + voice
- Text fallback needed
- Accessibility

```python
from google.adk.agents import Agent

agent = Agent(
    name="multimodal_agent",
    model="gemini-2.0-flash-live-001",
    instruction="You are a multimodal assistant.",
)
```

## Model Comparison

| Feature | Native Audio | Standard Live |
|---------|-------------|--------------|
| **Model** | `gemini-live-2.5-flash-native-audio` | `gemini-2.0-flash-live-001` |
| **Speech-to-speech** | Yes | No (text intermediary) |
| **Latency** | 100-300ms | 200-500ms |
| **Emotion/Prosody** | Preserved | Synthetic |
| **Text output** | No | Yes |
| **Multimodal** | Audio only | Text + Audio + Video |
| **Use case** | Voice-only | Multimodal apps |

## Native Audio Configuration

### Basic Setup

```python
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types

# 1. Create native audio agent
agent = Agent(
    name="voice_agent",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a natural-sounding voice assistant.",
)

# 2. Create runner
runner = Runner(agent=agent, app_name="native_audio_app")

# 3. Configure audio-only streaming
run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Aoede"  # Warm, expressive
            )
        )
    ),
)

# 4. Run streaming session
live_queue = LiveRequestQueue()

async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=run_config,
):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                # Process native audio
                audio_bytes = part.inline_data.data
                # Play directly (no text processing)
```

### With Voice Activity Detection

```python
from google.genai import types

# Native audio + VAD for natural turn-taking
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
```

## Advantages of Native Audio

### 1. Lower Latency

**Standard pipeline:**
```
User Speech → STT → Text → LLM → Text → TTS → Agent Speech
              ↑                            ↑
              200ms                        200ms
Total: ~500ms
```

**Native audio pipeline:**
```
User Speech → Native Model → Agent Speech
              ↑
              100-300ms
Total: ~200ms
```

### 2. Natural Prosody

Native audio preserves:
- Emotional tone
- Speech rhythm
- Intonation patterns
- Natural pauses
- Emphasis and stress

Example:
```python
# User says: "That's... AMAZING!" (with excitement)
# Native audio agent responds with matching enthusiasm

# Standard model would lose emotional context
```

### 3. No Text Intermediary

Benefits:
- Faster processing
- No transcription errors
- Direct speech understanding
- Emotion-aware responses

## Use Cases

### Voice-Only Interfaces

```python
"""Voice-only assistant with native audio."""
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import pyaudio

agent = Agent(
    name="voice_only",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a voice-only assistant. Be conversational and friendly.",
)

runner = Runner(agent=agent, app_name="voice_only_app")

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

# Audio I/O
p = pyaudio.PyAudio()
input_stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True)
output_stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)

live_queue = LiveRequestQueue()

# Capture and stream
async def capture_audio():
    while True:
        audio_data = input_stream.read(1024)
        live_queue.send_realtime(audio_data)
        await asyncio.sleep(0.01)

async def play_responses():
    async for event in runner.run_live(
        user_id="user_123",
        session_id="session_456",
        live_request_queue=live_queue,
        run_config=run_config,
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    output_stream.write(part.inline_data.data)

await asyncio.gather(capture_audio(), play_responses())
```

### Phone Bot

```python
"""Phone bot with native audio for natural conversations."""
from google.adk.agents import Agent
from google.genai import types

phone_bot = Agent(
    name="phone_assistant",
    model="gemini-live-2.5-flash-native-audio",
    instruction="""
    You are a friendly phone assistant for a restaurant.
    - Help customers with reservations
    - Answer questions about menu
    - Speak naturally and conversationally
    - Be warm and welcoming
    """,
)

run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        )
    ),
)
```

### Emotion-Aware Assistant

```python
"""Assistant that responds to emotional cues."""
from google.adk.agents import Agent

emotion_agent = Agent(
    name="emotion_aware",
    model="gemini-live-2.5-flash-native-audio",
    instruction="""
    You are an empathetic voice assistant.
    - Listen to the user's tone and emotion
    - Respond with matching emotional warmth
    - Be supportive and understanding
    - Adapt your tone to the conversation
    """,
)

# Native audio preserves user's emotional state
# Agent can respond appropriately
```

## Best Practices

### 1. Use for Voice-Only Apps

```python
# Good: Voice-only interface
agent = Agent(
    model="gemini-live-2.5-flash-native-audio",
    instruction="Voice assistant for hands-free interaction",
)

# Not ideal: Need text output
agent = Agent(
    model="gemini-2.0-flash-live-001",  # Use multimodal instead
    instruction="Assistant with text chat",
)
```

### 2. Configure Appropriate Voice

```python
# Match voice to use case
voices = {
    "customer_service": "Kore",      # Professional, clear
    "friend_bot": "Aoede",           # Warm, friendly
    "announcer": "Charon",           # Authoritative, deep
    "kids_app": "Puck",              # Playful, fun
}

run_config = types.RunConfig(
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=voices["customer_service"]
            )
        )
    ),
)
```

### 3. Enable VAD for Natural Conversation

```python
# VAD essential for native audio
run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_activity_detection=types.VoiceActivityDetection(
            disabled=False,  # Enable for turn-taking
            start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
            end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
        ),
    ),
)
```

### 4. Optimize Audio Format

```python
# Input: PCM 16-bit, 16kHz, mono
input_stream = p.open(
    format=pyaudio.paInt16,  # 16-bit
    channels=1,               # Mono
    rate=16000,               # 16kHz
    input=True,
)

# Output: PCM 16-bit, 24kHz, mono
output_stream = p.open(
    format=pyaudio.paInt16,  # 16-bit
    channels=1,               # Mono
    rate=24000,               # 24kHz (agent output)
    output=True,
)
```

## Limitations

### No Text Output

```python
# Native audio does NOT provide text
async for event in runner.run_live(...):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            # part.text is NOT available
            # Only part.inline_data (audio)
            pass
```

**Solution:** Use `gemini-2.0-flash-live-001` if text needed.

### Audio-Only Modality

```python
# Cannot process images, video, documents with native audio
# Use multimodal model for non-audio inputs
```

### Voice Selection Limited

```python
# Only prebuilt voices available
# Cannot customize voice characteristics
# Use available voices: Aoede, Charon, Kore, Fenrir, Puck
```

## Migration from Standard to Native

### Before (Standard Model)

```python
agent = Agent(
    name="voice_agent",
    model="gemini-2.0-flash-live-001",
    instruction="Voice assistant",
)

run_config = types.RunConfig(
    response_modalities=["TEXT", "AUDIO"],  # Both modalities
)

# Process text and audio
async for event in runner.run_live(...):
    for part in event.content.parts:
        if part.text:
            print(part.text)  # Text available
        if part.inline_data:
            play_audio(part.inline_data.data)
```

### After (Native Audio)

```python
agent = Agent(
    name="voice_agent",
    model="gemini-live-2.5-flash-native-audio",  # Native model
    instruction="Voice assistant",
)

run_config = types.RunConfig(
    response_modalities=["AUDIO"],  # Audio only
)

# Process audio only
async for event in runner.run_live(...):
    for part in event.content.parts:
        # No part.text available
        if hasattr(part, 'inline_data') and part.inline_data:
            play_audio(part.inline_data.data)  # Direct audio
```

## Performance Comparison

| Metric | Native Audio | Standard Live |
|--------|-------------|--------------|
| Time to first audio | 100-300ms | 200-500ms |
| Total latency | 200-400ms | 400-700ms |
| Emotion preservation | Excellent | Synthetic |
| Natural prosody | Yes | Limited |
| Text availability | No | Yes |

## See Also

- Interruption Handling: @/home/omixec/Claude-ADK-Skills/skills/adk-bidi-multi-agent/references/interruption-handling.md
- Audio Format Conversion: @/home/omixec/Claude-ADK-Skills/skills/adk-bidi-multi-agent/references/audio-format-conversion.md
- VAD Configuration: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/vad-config.md
