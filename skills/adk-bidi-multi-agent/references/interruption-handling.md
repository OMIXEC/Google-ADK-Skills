# Interruption Handling and Turn Management

**Handle user interruptions and coordinate speaking turns in bidirectional streaming.**

## Overview

Interruption handling enables:
- User can interrupt agent mid-response
- Graceful turn-taking
- Stop agent speech immediately
- Resume or restart conversation
- Natural conversation flow

## Core Concepts

### 1. Interruption Types

**Hard Interruption:**
- User starts speaking while agent is speaking
- Immediately stop agent
- Process user input
- Discard remaining agent response

**Soft Interruption:**
- User starts speaking
- Agent finishes current sentence
- Then yields to user

**Barge-in:**
- User speaks over agent
- Agent stops immediately
- No buffer or delay

### 2. Turn Management

**Turn States:**
- `USER_SPEAKING` - User has the floor
- `AGENT_SPEAKING` - Agent has the floor
- `SILENCE` - No one speaking
- `TRANSITION` - Switching between speakers

## Implementation Patterns

### Pattern 1: Basic Interruption Handling

```python
"""Basic interruption handling with LiveRequestQueue."""
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import asyncio

agent = Agent(
    name="interruptible_agent",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a voice assistant. Be concise.",
)

runner = Runner(agent=agent, app_name="interruption_app")

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

class InterruptionManager:
    """Manage interruptions and turn-taking."""

    def __init__(self):
        self.is_agent_speaking = False
        self.is_user_speaking = False
        self.audio_queue = asyncio.Queue()
        self.interrupt_event = asyncio.Event()

    def user_started_speaking(self):
        """Signal that user started speaking."""
        self.is_user_speaking = True

        # If agent is speaking, interrupt
        if self.is_agent_speaking:
            print("\n[User interrupted agent]")
            self.interrupt_event.set()
            self.stop_agent_audio()

    def user_stopped_speaking(self):
        """Signal that user stopped speaking."""
        self.is_user_speaking = False

    def agent_started_speaking(self):
        """Signal that agent started speaking."""
        self.is_agent_speaking = True
        self.interrupt_event.clear()

    def agent_stopped_speaking(self):
        """Signal that agent stopped speaking."""
        self.is_agent_speaking = False

    def stop_agent_audio(self):
        """Stop playing agent audio."""
        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        self.is_agent_speaking = False

# Usage
interruption_mgr = InterruptionManager()

async def play_agent_audio():
    """Play agent audio with interruption handling."""
    while True:
        try:
            # Wait for audio or interruption
            audio_task = asyncio.create_task(interruption_mgr.audio_queue.get())
            interrupt_task = asyncio.create_task(interruption_mgr.interrupt_event.wait())

            done, pending = await asyncio.wait(
                [audio_task, interrupt_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            # Check if interrupted
            if interruption_mgr.interrupt_event.is_set():
                print("[Audio playback interrupted]")
                interruption_mgr.stop_agent_audio()
                continue

            # Play audio chunk
            if audio_task in done:
                audio_bytes = audio_task.result()
                # Play to output stream
                output_stream.write(audio_bytes)

        except asyncio.CancelledError:
            break
```

### Pattern 2: VAD-Based Interruption

```python
"""Use Voice Activity Detection for automatic interruption."""
from google.adk.agents import LiveRequestQueue
from google.genai import types

live_queue = LiveRequestQueue()

# Configure VAD for interruption detection
run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_activity_detection=types.VoiceActivityDetection(
            disabled=False,
            start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_MEDIUM,
            end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
        ),
    ),
)

# Track speaking state
is_agent_speaking = False

async def detect_interruption(audio_chunk: bytes):
    """Detect if user is speaking (potential interruption)."""
    # VAD detects user speech
    if vad_detected_speech(audio_chunk):
        if is_agent_speaking:
            # User interrupted agent
            print("[Interruption detected]")
            live_queue.signal_activity_start()
            # Stop agent audio playback
            stop_agent_audio()

        # Send user audio
        live_queue.send_realtime(audio_chunk)
    else:
        # Silence - agent can speak
        if is_agent_speaking:
            # Continue agent playback
            pass
```

### Pattern 3: Turn-Based Management

```python
"""Explicit turn management for coordinated speaking."""
from enum import Enum
import asyncio

class TurnState(Enum):
    """Turn states."""
    USER_TURN = "user"
    AGENT_TURN = "agent"
    TRANSITION = "transition"

class TurnManager:
    """Manage speaking turns between user and agent."""

    def __init__(self):
        self.current_turn = TurnState.USER_TURN
        self.turn_lock = asyncio.Lock()

    async def request_turn(self, speaker: TurnState):
        """Request speaking turn."""
        async with self.turn_lock:
            if self.current_turn != speaker:
                print(f"[Turn changed: {self.current_turn.value} → {speaker.value}]")
                self.current_turn = speaker

    async def yield_turn(self):
        """Yield current turn."""
        async with self.turn_lock:
            if self.current_turn == TurnState.USER_TURN:
                self.current_turn = TurnState.AGENT_TURN
            else:
                self.current_turn = TurnState.USER_TURN

    def can_speak(self, speaker: TurnState) -> bool:
        """Check if speaker can speak."""
        return self.current_turn == speaker

# Usage
turn_mgr = TurnManager()

async def user_input_handler():
    """Handle user input with turn management."""
    while True:
        # Wait for user turn
        if not turn_mgr.can_speak(TurnState.USER_TURN):
            await asyncio.sleep(0.1)
            continue

        # Capture user audio
        audio_chunk = capture_audio()

        if vad_detected_speech(audio_chunk):
            # User is speaking
            await turn_mgr.request_turn(TurnState.USER_TURN)
            live_queue.send_realtime(audio_chunk)
        else:
            # User finished - yield to agent
            await turn_mgr.yield_turn()

async def agent_output_handler():
    """Handle agent output with turn management."""
    async for event in runner.run_live(...):
        # Wait for agent turn
        if not turn_mgr.can_speak(TurnState.AGENT_TURN):
            continue

        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Agent is speaking
                    await turn_mgr.request_turn(TurnState.AGENT_TURN)
                    play_audio(part.inline_data.data)
```

### Pattern 4: Interruption with State Recovery

```python
"""Handle interruption with ability to resume or restart."""
from collections import deque

class ResumableAudioPlayer:
    """Audio player that can be interrupted and resumed."""

    def __init__(self):
        self.audio_buffer = deque()
        self.is_playing = False
        self.is_interrupted = False
        self.current_position = 0

    def add_audio_chunk(self, audio_bytes: bytes):
        """Add audio chunk to buffer."""
        self.audio_buffer.append(audio_bytes)

    def interrupt(self):
        """Interrupt playback."""
        self.is_interrupted = True
        self.is_playing = False
        print("[Playback interrupted]")

    def resume(self):
        """Resume playback from interruption point."""
        if self.is_interrupted:
            print(f"[Resuming from position {self.current_position}]")
            self.is_interrupted = False
            self.is_playing = True

    def restart(self):
        """Restart playback from beginning."""
        print("[Restarting playback]")
        self.current_position = 0
        self.is_interrupted = False
        self.is_playing = True

    def clear(self):
        """Clear audio buffer (discard interrupted response)."""
        self.audio_buffer.clear()
        self.current_position = 0
        self.is_interrupted = False

    async def play(self):
        """Play audio with interruption support."""
        self.is_playing = True

        while self.audio_buffer:
            if self.is_interrupted:
                # Pause until resumed or cleared
                await asyncio.sleep(0.1)
                continue

            # Get next chunk
            audio_chunk = self.audio_buffer.popleft()
            self.current_position += 1

            # Play chunk
            output_stream.write(audio_chunk)

        self.is_playing = False

# Usage
player = ResumableAudioPlayer()

# Add audio chunks
async for event in runner.run_live(...):
    for part in event.content.parts:
        if hasattr(part, 'inline_data') and part.inline_data:
            player.add_audio_chunk(part.inline_data.data)

# User interrupts
if user_started_speaking():
    player.interrupt()

# Resume or restart?
if user_says("continue"):
    player.resume()
elif user_says("start over"):
    player.restart()
else:
    player.clear()  # Discard interrupted response
```

## Complete Example

### Full Interruption System

```python
"""Complete interruption handling system."""
import asyncio
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import pyaudio

# Setup
agent = Agent(
    name="interruptible_voice",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a voice assistant. Be conversational.",
)

runner = Runner(agent=agent, app_name="interruption_demo")

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

class InterruptionSystem:
    """Complete interruption handling system."""

    def __init__(self):
        self.is_agent_speaking = False
        self.is_user_speaking = False
        self.agent_audio_queue = asyncio.Queue()
        self.stop_playback = asyncio.Event()

    async def run(self):
        """Run interruption system."""
        live_queue = LiveRequestQueue()

        async def capture_user_audio():
            """Capture user audio and detect interruptions."""
            while True:
                audio_chunk = input_stream.read(1024, exception_on_overflow=False)

                # Simple VAD (you would use actual VAD here)
                energy = sum(abs(b) for b in audio_chunk) / len(audio_chunk)

                if energy > 100:  # Speech detected
                    if not self.is_user_speaking:
                        # User started speaking
                        self.is_user_speaking = True
                        live_queue.signal_activity_start()

                        # Check for interruption
                        if self.is_agent_speaking:
                            print("\n[User interrupted agent - stopping playback]")
                            self.stop_playback.set()
                            self.is_agent_speaking = False

                            # Clear agent audio queue
                            while not self.agent_audio_queue.empty():
                                self.agent_audio_queue.get_nowait()

                    # Send user audio
                    live_queue.send_realtime(audio_chunk)

                else:  # Silence
                    if self.is_user_speaking:
                        # User stopped speaking
                        self.is_user_speaking = False
                        live_queue.signal_activity_end()

                await asyncio.sleep(0.01)

        async def receive_agent_audio():
            """Receive agent audio responses."""
            async for event in runner.run_live(
                user_id="user_123",
                session_id="session_456",
                live_request_queue=live_queue,
                run_config=run_config,
            ):
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            # Queue audio for playback
                            await self.agent_audio_queue.put(part.inline_data.data)

        async def play_agent_audio():
            """Play agent audio with interruption handling."""
            while True:
                try:
                    # Wait for audio or stop signal
                    get_audio = asyncio.create_task(self.agent_audio_queue.get())
                    wait_stop = asyncio.create_task(self.stop_playback.wait())

                    done, pending = await asyncio.wait(
                        [get_audio, wait_stop],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    # Cancel pending
                    for task in pending:
                        task.cancel()

                    # Check if stopped
                    if self.stop_playback.is_set():
                        self.stop_playback.clear()
                        continue

                    # Play audio
                    if get_audio in done:
                        audio_bytes = get_audio.result()

                        if not self.is_user_speaking:
                            self.is_agent_speaking = True
                            output_stream.write(audio_bytes)
                            self.is_agent_speaking = False

                except asyncio.CancelledError:
                    break

        # Run all tasks
        await asyncio.gather(
            capture_user_audio(),
            receive_agent_audio(),
            play_agent_audio(),
        )

# Run system
system = InterruptionSystem()
asyncio.run(system.run())
```

## Best Practices

### 1. Clear Audio Buffers on Interruption

```python
# Good: Clear buffered audio when interrupted
if user_interrupted:
    while not audio_queue.empty():
        audio_queue.get_nowait()
    stop_playback()

# Bad: Continue playing stale audio
if user_interrupted:
    stop_playback()  # Queue still has old audio
```

### 2. Use VAD for Detection

```python
# Good: Use VAD for automatic detection
run_config = types.RunConfig(
    speech_config=types.SpeechConfig(
        voice_activity_detection=types.VoiceActivityDetection(
            disabled=False,  # Enable VAD
        ),
    ),
)

# Less ideal: Manual interruption buttons
if button_pressed:
    interrupt_agent()
```

### 3. Provide Visual Feedback

```python
# Show who is speaking
if is_user_speaking:
    print("[User speaking...]")
elif is_agent_speaking:
    print("[Agent speaking...]")
else:
    print("[Silence]")
```

### 4. Handle Rapid Interruptions

```python
# Debounce rapid interruptions
last_interrupt_time = 0
INTERRUPT_COOLDOWN = 0.5  # seconds

if user_speaking and is_agent_speaking:
    current_time = time.time()
    if current_time - last_interrupt_time > INTERRUPT_COOLDOWN:
        interrupt_agent()
        last_interrupt_time = current_time
```

## Common Issues

### Issue: Audio Continues After Interruption

**Cause:** Audio buffer not cleared

**Solution:**
```python
# Clear all queued audio
while not audio_queue.empty():
    try:
        audio_queue.get_nowait()
    except:
        break
```

### Issue: Interruption Too Slow

**Cause:** Large audio buffers

**Solution:**
```python
# Use smaller buffer chunks
output_stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=24000,
    output=True,
    frames_per_buffer=512,  # Smaller buffer = faster stop
)
```

### Issue: False Interruptions

**Cause:** Background noise triggers VAD

**Solution:**
```python
# Increase start sensitivity
vad_config = types.VoiceActivityDetection(
    disabled=False,
    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,  # Stricter
)
```

## See Also

- Native Audio Models: @/home/omixec/Claude-ADK-Skills/skills/adk-bidi-multi-agent/references/native-audio.md
- VAD Configuration: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/vad-config.md
- Audio Format Conversion: @/home/omixec/Claude-ADK-Skills/skills/adk-bidi-multi-agent/references/audio-format-conversion.md
