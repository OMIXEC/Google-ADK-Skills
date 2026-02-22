# Voice Activity Detection (VAD) Configuration

**Automatic detection of when users start and stop speaking.**

## Overview

Voice Activity Detection (VAD) automatically detects:
- When user starts speaking (start-of-speech)
- When user stops speaking (end-of-speech)
- Background noise vs. actual speech
- Natural conversation turn-taking

This enables hands-free, natural conversations without manual triggers.

## Basic Usage

```python
from google.genai import types

vad_config = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
)

run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_activity_detection=vad_config,
    ),
)
```

## API Reference

### VoiceActivityDetection

```python
vad_config = types.VoiceActivityDetection(
    disabled=False,                          # Enable/disable VAD
    start_of_speech_sensitivity=sensitivity, # Start threshold
    end_of_speech_sensitivity=sensitivity,   # End threshold
)
```

**Parameters:**
- `disabled` (bool): Enable (`False`) or disable (`True`) VAD
- `start_of_speech_sensitivity`: How easily speech start is detected
- `end_of_speech_sensitivity`: How easily speech end is detected

### Start Sensitivity Levels

```python
types.StartSensitivity.START_SENSITIVITY_LOW      # More lenient
types.StartSensitivity.START_SENSITIVITY_MEDIUM   # Balanced
types.StartSensitivity.START_SENSITIVITY_HIGH     # Stricter
```

### End Sensitivity Levels

```python
types.EndSensitivity.END_SENSITIVITY_LOW     # Longer pause needed
types.EndSensitivity.END_SENSITIVITY_MEDIUM  # Balanced
types.EndSensitivity.END_SENSITIVITY_HIGH    # Shorter pause needed
```

## Sensitivity Guide

### Start-of-Speech Sensitivity

Controls how easily VAD triggers when user begins speaking.

| Level | Behavior | Use Case |
|-------|----------|----------|
| LOW | Catches soft speech, background noise | Quiet environments |
| MEDIUM | Balanced detection | Normal environments |
| HIGH | Ignores quiet sounds, strict threshold | Noisy environments |

**Examples:**

```python
# Quiet office - catch all speech
start_sensitivity = types.StartSensitivity.START_SENSITIVITY_LOW

# Busy cafe - ignore background chatter
start_sensitivity = types.StartSensitivity.START_SENSITIVITY_HIGH

# General use - balanced
start_sensitivity = types.StartSensitivity.START_SENSITIVITY_MEDIUM
```

### End-of-Speech Sensitivity

Controls how quickly VAD detects that user stopped speaking.

| Level | Behavior | Use Case |
|-------|----------|----------|
| LOW | Waits longer for silence | Thoughtful speakers, pauses |
| MEDIUM | Balanced timing | Normal conversation |
| HIGH | Triggers quickly on pause | Fast-paced conversation |

**Examples:**

```python
# User thinks while speaking - allow pauses
end_sensitivity = types.EndSensitivity.END_SENSITIVITY_LOW

# Quick back-and-forth - minimize latency
end_sensitivity = types.EndSensitivity.END_SENSITIVITY_HIGH

# Natural conversation - balanced
end_sensitivity = types.EndSensitivity.END_SENSITIVITY_MEDIUM
```

## Configuration Presets

### Preset 1: Default (Recommended)

Best for most use cases.

```python
vad_config = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
)
```

**Characteristics:**
- Catches all user speech (LOW start)
- Quick turn-taking (HIGH end)
- Natural conversation flow

### Preset 2: Noisy Environment

For cafes, offices, public spaces.

```python
vad_config = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_LOW,
)
```

**Characteristics:**
- Ignores background noise (HIGH start)
- Allows for interruptions (LOW end)
- Reduces false triggers

### Preset 3: Quiet Environment

For quiet rooms, phone calls, private spaces.

```python
vad_config = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_MEDIUM,
)
```

**Characteristics:**
- Catches soft speech (LOW start)
- Balanced turn-taking (MEDIUM end)
- Optimal for low noise

### Preset 4: Fast-Paced Conversation

For quick Q&A, customer support.

```python
vad_config = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_MEDIUM,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
)
```

**Characteristics:**
- Balanced start detection (MEDIUM start)
- Quick turn-taking (HIGH end)
- Minimal latency

### Preset 5: Thoughtful Speaker

For interviews, storytelling, explanations.

```python
vad_config = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_LOW,
)
```

**Characteristics:**
- Catches all speech (LOW start)
- Allows pauses (LOW end)
- Doesn't interrupt thinking

## Complete Examples

### Example 1: Voice Assistant (Default)

```python
from google.genai import types
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner

agent = Agent(
    name="voice_assistant",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a helpful voice assistant.",
)

runner = Runner(agent=agent, app_name="voice_app")

# Default VAD configuration
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

live_queue = LiveRequestQueue()

async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_queue,
    run_config=run_config,
):
    # VAD automatically detects speech start/end
    pass
```

### Example 2: Noisy Environment

```python
from google.genai import types

# Noisy cafe configuration
run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
        ),
        voice_activity_detection=types.VoiceActivityDetection(
            disabled=False,
            start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
            end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_LOW,
        ),
    ),
)
```

### Example 3: Manual Activity Signals

Even with VAD enabled, you can manually signal activity:

```python
from google.adk.agents import LiveRequestQueue

live_queue = LiveRequestQueue()

# Manual signal (overrides VAD)
live_queue.signal_activity_start()

# Send audio
live_queue.send_realtime(audio_bytes)

# Manual end signal
live_queue.signal_activity_end()
```

### Example 4: Disabled VAD (Manual Control)

```python
from google.genai import types

# Disable VAD for manual control
run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_activity_detection=types.VoiceActivityDetection(
            disabled=True,  # Manual control only
        ),
    ),
)

# Must manually signal activity
live_queue.signal_activity_start()
# ... audio streaming ...
live_queue.signal_activity_end()
```

## How VAD Works

### Detection Pipeline

```
1. Audio Input
   ↓
2. Energy Level Analysis
   - Measure audio amplitude
   - Compare to noise floor
   ↓
3. Speech Classification
   - Identify speech vs noise
   - Apply sensitivity threshold
   ↓
4. Start Detection
   - Speech detected above threshold
   - Trigger start-of-speech event
   ↓
5. Ongoing Speech
   - Continue processing
   - Monitor for silence
   ↓
6. End Detection
   - Silence detected below threshold
   - Trigger end-of-speech event
   ↓
7. Process Complete Utterance
```

### Timing Behavior

**Start-of-Speech:**
- LOW: ~50-100ms of audio triggers detection
- MEDIUM: ~100-200ms of audio needed
- HIGH: ~200-300ms of audio needed

**End-of-Speech:**
- LOW: ~800-1000ms silence needed
- MEDIUM: ~500-700ms silence needed
- HIGH: ~300-500ms silence needed

*Note: Timings are approximate and may vary.*

## Best Practices

### 1. Choose Based on Environment

```python
# Quiet home office
vad = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
)

# Busy call center
vad = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_LOW,
)
```

### 2. Test with Real Users

```python
# A/B test different sensitivities
configs = {
    "default": (types.StartSensitivity.START_SENSITIVITY_LOW,
                types.EndSensitivity.END_SENSITIVITY_HIGH),
    "noisy": (types.StartSensitivity.START_SENSITIVITY_HIGH,
              types.EndSensitivity.END_SENSITIVITY_LOW),
}

for name, (start, end) in configs.items():
    vad = types.VoiceActivityDetection(
        disabled=False,
        start_of_speech_sensitivity=start,
        end_of_speech_sensitivity=end,
    )
    # Test and measure user satisfaction
```

### 3. Allow User Configuration

```python
def create_vad_config(user_preferences: dict):
    """Create VAD config from user preferences."""
    return types.VoiceActivityDetection(
        disabled=user_preferences.get("vad_disabled", False),
        start_of_speech_sensitivity=user_preferences.get(
            "start_sensitivity",
            types.StartSensitivity.START_SENSITIVITY_LOW
        ),
        end_of_speech_sensitivity=user_preferences.get(
            "end_sensitivity",
            types.EndSensitivity.END_SENSITIVITY_HIGH
        ),
    )
```

### 4. Combine with Manual Signals

```python
# Use VAD for automatic detection
# But allow manual override for critical moments

if critical_section:
    live_queue.signal_activity_start()
    # Ensure VAD doesn't trigger early end
else:
    # Let VAD handle automatically
    pass
```

## Troubleshooting

### Problem: False Start Triggers

**Symptom:** Agent thinks user is speaking when they're not

**Solution:** Increase start sensitivity

```python
vad = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,  # Stricter
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
)
```

### Problem: Missed Speech

**Symptom:** User speaks but agent doesn't respond

**Solution:** Decrease start sensitivity

```python
vad = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,  # More lenient
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
)
```

### Problem: Agent Interrupts User

**Symptom:** Agent starts talking while user is still speaking

**Solution:** Decrease end sensitivity (wait longer)

```python
vad = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_LOW,  # Wait longer
)
```

### Problem: Long Pauses Before Agent Response

**Symptom:** Agent takes too long to respond after user stops

**Solution:** Increase end sensitivity (respond faster)

```python
vad = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,  # Faster
)
```

## Environment-Specific Recommendations

| Environment | Start | End | Reason |
|-------------|-------|-----|--------|
| Quiet room | LOW | HIGH | Catch all speech, quick turn-taking |
| Office | MEDIUM | MEDIUM | Balance noise and responsiveness |
| Cafe | HIGH | LOW | Ignore background, allow interruptions |
| Phone call | LOW | MEDIUM | Clear audio, natural pauses |
| Car | HIGH | LOW | Road noise, safety pauses |
| Public space | HIGH | MEDIUM | Filter noise, reasonable timing |

## Integration with LiveRequestQueue

VAD works automatically with LiveRequestQueue:

```python
from google.adk.agents import LiveRequestQueue
from google.genai import types

live_queue = LiveRequestQueue()

# Configure VAD
run_config = types.RunConfig(
    speech_config=types.SpeechConfig(
        voice_activity_detection=types.VoiceActivityDetection(
            disabled=False,
            start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
            end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
        ),
    ),
)

# VAD automatically signals activity
# No manual signal_activity_start/end needed (unless overriding)

# Stream audio
live_queue.send_realtime(audio_bytes)

# VAD handles detection automatically
```

## See Also

- LiveRequestQueue: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/live-request-queue.md
- RunConfig: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/run-config.md
- Audio Streaming Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/audio-streaming.md
