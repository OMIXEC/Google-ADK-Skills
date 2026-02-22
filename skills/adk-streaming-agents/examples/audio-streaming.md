# Audio Streaming Example

**Complete example of audio streaming agent with native speech-to-speech.**

## Overview

This example demonstrates:
- Native audio streaming with `gemini-live-2.5-flash-native-audio`
- Voice Activity Detection (VAD) configuration
- Real-time audio capture and playback
- PyAudio integration
- Audio format handling (PCM 16-bit, 16kHz)

## Complete Implementation

### Full Audio Streaming Agent

```python
"""Audio streaming agent with native speech-to-speech."""
import asyncio
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import pyaudio
import wave

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE_INPUT = 16000   # Input: 16kHz
RATE_OUTPUT = 24000  # Output: 24kHz

# 1. Create native audio agent
agent = Agent(
    name="audio_streamer",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a friendly voice assistant. Speak naturally and conversationally.",
)

# 2. Create runner
runner = Runner(agent=agent, app_name="audio_streaming_app")

# 3. Configure audio streaming with VAD
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

async def run_audio_streaming_session():
    """Run audio streaming session with microphone and speakers."""
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Input stream (microphone)
    input_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE_INPUT,
        input=True,
        frames_per_buffer=CHUNK,
    )

    # Output stream (speakers)
    output_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE_OUTPUT,
        output=True,
    )

    live_queue = LiveRequestQueue()

    print("="*60)
    print("Audio Streaming Agent Started")
    print("Speak into your microphone...")
    print("Press Ctrl+C to stop")
    print("="*60)

    async def capture_audio():
        """Capture audio from microphone and send to agent."""
        try:
            while True:
                # Read audio chunk
                audio_data = input_stream.read(CHUNK, exception_on_overflow=False)

                # Send to agent
                live_queue.send_realtime(audio_data)

                # Small delay to avoid blocking
                await asyncio.sleep(0.01)

        except KeyboardInterrupt:
            print("\nStopping audio capture...")
        except Exception as e:
            print(f"Capture error: {e}")
        finally:
            live_queue.close()

    async def process_responses():
        """Process agent audio responses and play through speakers."""
        try:
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
                            print(".", end="", flush=True)  # Visual feedback

        except Exception as e:
            print(f"\nResponse error: {e}")

    # Run both tasks concurrently
    try:
        await asyncio.gather(capture_audio(), process_responses())
    finally:
        # Cleanup
        input_stream.stop_stream()
        input_stream.close()
        output_stream.stop_stream()
        output_stream.close()
        p.terminate()

if __name__ == "__main__":
    try:
        asyncio.run(run_audio_streaming_session())
    except KeyboardInterrupt:
        print("\n\nAudio streaming session ended.")
```

## Push-to-Talk Implementation

### With Manual Activity Signals

```python
"""Push-to-talk audio streaming with manual VAD signals."""
import asyncio
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import pyaudio
import keyboard  # pip install keyboard

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE_INPUT = 16000
RATE_OUTPUT = 24000

agent = Agent(
    name="push_to_talk_agent",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a voice assistant.",
)

runner = Runner(agent=agent, app_name="push_to_talk_app")

run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        ),
    ),
)

async def push_to_talk_session():
    """Push-to-talk audio session."""
    p = pyaudio.PyAudio()

    input_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE_INPUT,
        input=True,
        frames_per_buffer=CHUNK,
    )

    output_stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE_OUTPUT,
        output=True,
    )

    live_queue = LiveRequestQueue()
    is_recording = False

    print("="*60)
    print("Push-to-Talk Audio Agent")
    print("Hold SPACE to talk, release to send")
    print("Press ESC to quit")
    print("="*60)

    async def handle_input():
        """Handle push-to-talk input."""
        nonlocal is_recording

        while True:
            try:
                # Check if space is pressed
                if keyboard.is_pressed('space'):
                    if not is_recording:
                        print("\n[Recording...]", end="", flush=True)
                        live_queue.signal_activity_start()
                        is_recording = True

                    # Capture audio while space is held
                    audio_data = input_stream.read(CHUNK, exception_on_overflow=False)
                    live_queue.send_realtime(audio_data)

                else:
                    if is_recording:
                        print(" [Sent]")
                        live_queue.signal_activity_end()
                        is_recording = False

                # Check for exit
                if keyboard.is_pressed('esc'):
                    print("\n\nExiting...")
                    live_queue.close()
                    break

                await asyncio.sleep(0.01)

            except Exception as e:
                print(f"\nInput error: {e}")
                break

    async def process_audio():
        """Process and play audio responses."""
        try:
            async for event in runner.run_live(
                user_id="user_123",
                session_id="session_456",
                live_request_queue=live_queue,
                run_config=run_config,
            ):
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            audio_bytes = part.inline_data.data
                            output_stream.write(audio_bytes)

        except Exception as e:
            print(f"\nAudio error: {e}")

    try:
        await asyncio.gather(handle_input(), process_audio())
    finally:
        input_stream.stop_stream()
        input_stream.close()
        output_stream.stop_stream()
        output_stream.close()
        p.terminate()

if __name__ == "__main__":
    asyncio.run(push_to_talk_session())
```

## File-Based Audio Streaming

### Stream Audio from File

```python
"""Stream audio from WAV file to agent."""
import asyncio
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import wave
import pyaudio

agent = Agent(
    name="file_audio_agent",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are analyzing audio content.",
)

runner = Runner(agent=agent, app_name="file_audio_app")

run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
)

async def stream_audio_file(file_path: str):
    """Stream audio from WAV file to agent."""
    # Open WAV file
    wf = wave.open(file_path, 'rb')

    # Setup audio output
    p = pyaudio.PyAudio()
    output_stream = p.open(
        format=p.get_format_from_width(wf.getsampwidth()),
        channels=1,
        rate=24000,
        output=True,
    )

    live_queue = LiveRequestQueue()

    async def send_file_audio():
        """Read file and send to agent."""
        print(f"Streaming audio from: {file_path}")

        chunk_size = 1024
        data = wf.readframes(chunk_size)

        while data:
            live_queue.send_realtime(data)
            data = wf.readframes(chunk_size)
            await asyncio.sleep(0.01)  # Simulate real-time

        print("File streaming complete")
        await asyncio.sleep(1)
        live_queue.close()

    async def receive_response():
        """Process agent response."""
        print("Waiting for agent response...")

        async for event in runner.run_live(
            user_id="user_123",
            session_id="session_456",
            live_request_queue=live_queue,
            run_config=run_config,
        ):
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        audio_bytes = part.inline_data.data
                        output_stream.write(audio_bytes)
                        print(".", end="", flush=True)

    try:
        await asyncio.gather(send_file_audio(), receive_response())
    finally:
        wf.close()
        output_stream.stop_stream()
        output_stream.close()
        p.terminate()

if __name__ == "__main__":
    # Example: stream a WAV file
    asyncio.run(stream_audio_file("input_audio.wav"))
```

## Audio Format Conversion

### Convert to Required Format

```python
"""Convert audio to ADK-compatible format."""
from pydub import AudioSegment
import io

def convert_to_pcm_16khz(audio_data: bytes, source_format: str = "mp3") -> bytes:
    """
    Convert audio to PCM 16-bit, 16kHz mono.

    Args:
        audio_data: Input audio bytes
        source_format: Source format (mp3, wav, ogg, etc.)

    Returns:
        PCM 16-bit, 16kHz mono bytes
    """
    # Load audio
    audio = AudioSegment.from_file(
        io.BytesIO(audio_data),
        format=source_format
    )

    # Convert to mono
    audio = audio.set_channels(1)

    # Convert to 16kHz
    audio = audio.set_frame_rate(16000)

    # Convert to 16-bit
    audio = audio.set_sample_width(2)  # 2 bytes = 16 bits

    # Export as raw PCM
    pcm_data = audio.raw_data

    return pcm_data

# Usage example
with open("input.mp3", "rb") as f:
    mp3_data = f.read()

pcm_data = convert_to_pcm_16khz(mp3_data, source_format="mp3")

# Now send to agent
live_queue.send_realtime(pcm_data)
```

## Recording and Saving

### Save Agent Responses

```python
"""Record and save agent audio responses."""
import asyncio
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types
import wave

agent = Agent(
    name="recording_agent",
    model="gemini-live-2.5-flash-native-audio",
    instruction="You are a voice assistant.",
)

runner = Runner(agent=agent, app_name="recording_app")

run_config = types.RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
)

async def record_agent_response(output_file: str):
    """Record agent response to WAV file."""
    live_queue = LiveRequestQueue()

    # Send prompt
    content = types.Content(parts=[types.Part(text="Tell me a short story.")])
    live_queue.send_content(content)

    # Collect audio chunks
    audio_chunks = []

    async for event in runner.run_live(
        user_id="user_123",
        session_id="session_456",
        live_request_queue=live_queue,
        run_config=run_config,
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    audio_chunks.append(part.inline_data.data)

        # Check if response is complete (implementation-specific)
        if len(audio_chunks) > 50:  # Arbitrary limit for example
            break

    live_queue.close()

    # Save to WAV file
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(24000)  # 24kHz output
        wf.writeframes(b''.join(audio_chunks))

    print(f"Audio saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(record_agent_response("agent_response.wav"))
```

## Testing

### Unit Test for Audio Streaming

```python
"""Test audio streaming functionality."""
import asyncio
import pytest
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.genai import types

@pytest.mark.asyncio
async def test_audio_streaming():
    """Test audio streaming returns audio data."""
    agent = Agent(
        name="test_audio_agent",
        model="gemini-live-2.5-flash-native-audio",
        instruction="Respond with a short greeting.",
    )

    runner = Runner(agent=agent, app_name="test_audio_app")

    run_config = types.RunConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
            )
        ),
    )

    live_queue = LiveRequestQueue()

    # Send test message
    content = types.Content(parts=[types.Part(text="Say hello")])
    live_queue.send_content(content)

    # Collect audio response
    audio_received = False

    async for event in runner.run_live(
        user_id="test_user",
        session_id="test_session",
        live_request_queue=live_queue,
        run_config=run_config,
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    audio_received = True
                    break

        if audio_received:
            break

    live_queue.close()

    assert audio_received, "No audio data received from agent"
```

## Best Practices

1. **Use correct audio format** - PCM 16-bit, 16kHz for input
2. **Handle overflow** - Use `exception_on_overflow=False` for input stream
3. **Small chunks** - 1024 frames is optimal for real-time
4. **Close streams** - Always close PyAudio streams in finally block
5. **Error handling** - Catch audio device errors
6. **Visual feedback** - Print dots or status during streaming
7. **Cleanup resources** - Terminate PyAudio properly

## Troubleshooting

### No Audio Output

**Issue:** Agent responds but no sound plays

**Solution:**
```python
# Check output stream configuration
output_stream = p.open(
    format=FORMAT,
    channels=1,
    rate=24000,  # Must match agent output rate
    output=True,
)
```

### Choppy Audio

**Issue:** Audio playback is choppy or stuttering

**Solution:**
```python
# Increase buffer size
output_stream = p.open(
    format=FORMAT,
    channels=1,
    rate=24000,
    output=True,
    frames_per_buffer=2048,  # Larger buffer
)
```

### Input Overflow Errors

**Issue:** "Input overflowed" errors

**Solution:**
```python
# Disable overflow exceptions
audio_data = input_stream.read(
    CHUNK,
    exception_on_overflow=False  # Ignore overflow
)
```

## See Also

- Text Streaming Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/text-streaming.md
- VAD Configuration: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/vad-config.md
- WebSocket Patterns: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/references/websocket-patterns.md
