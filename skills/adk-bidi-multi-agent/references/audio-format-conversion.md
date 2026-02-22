# Audio Format Conversion

**Convert audio between formats for ADK streaming agents.**

## Overview

ADK requires specific audio formats:
- **Input:** PCM 16-bit, 16kHz, mono
- **Output:** PCM 16-bit, 24kHz, mono

This guide covers converting from common formats (MP3, WAV, OGG, etc.) to ADK-compatible PCM.

## Required Format

### Input Audio (User → Agent)

```
Format: PCM (Pulse Code Modulation)
Bit depth: 16-bit
Sample rate: 16kHz (16,000 Hz)
Channels: 1 (mono)
Byte order: Little-endian
```

### Output Audio (Agent → User)

```
Format: PCM
Bit depth: 16-bit
Sample rate: 24kHz (24,000 Hz)
Channels: 1 (mono)
Byte order: Little-endian
```

## Conversion Tools

### Using pydub (Recommended)

```python
"""Convert audio using pydub."""
from pydub import AudioSegment
import io

def convert_to_pcm_16khz(audio_data: bytes, source_format: str = "mp3") -> bytes:
    """
    Convert audio to PCM 16-bit, 16kHz mono.

    Args:
        audio_data: Input audio bytes
        source_format: Source format (mp3, wav, ogg, m4a, flac, etc.)

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

# Usage
with open("input.mp3", "rb") as f:
    mp3_data = f.read()

pcm_data = convert_to_pcm_16khz(mp3_data, source_format="mp3")

# Send to agent
live_queue.send_realtime(pcm_data)
```

### Using ffmpeg-python

```python
"""Convert audio using ffmpeg."""
import ffmpeg
import io

def convert_with_ffmpeg(input_file: str) -> bytes:
    """
    Convert audio file to PCM 16kHz using ffmpeg.

    Args:
        input_file: Path to input audio file

    Returns:
        PCM 16-bit, 16kHz mono bytes
    """
    # Run ffmpeg
    out, _ = (
        ffmpeg
        .input(input_file)
        .output('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar='16000')
        .run(capture_stdout=True, capture_stderr=True)
    )

    return out

# Usage
pcm_data = convert_with_ffmpeg("input.mp3")
live_queue.send_realtime(pcm_data)
```

### Using scipy + numpy

```python
"""Convert WAV using scipy."""
from scipy.io import wavfile
import numpy as np

def convert_wav_to_pcm(wav_file: str) -> bytes:
    """
    Convert WAV file to PCM 16kHz.

    Args:
        wav_file: Path to WAV file

    Returns:
        PCM 16-bit, 16kHz mono bytes
    """
    # Read WAV file
    sample_rate, audio_data = wavfile.read(wav_file)

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)

    # Resample to 16kHz if needed
    if sample_rate != 16000:
        from scipy.signal import resample
        num_samples = int(len(audio_data) * 16000 / sample_rate)
        audio_data = resample(audio_data, num_samples)

    # Convert to 16-bit int
    audio_data = audio_data.astype(np.int16)

    # Convert to bytes
    pcm_bytes = audio_data.tobytes()

    return pcm_bytes

# Usage
pcm_data = convert_wav_to_pcm("input.wav")
live_queue.send_realtime(pcm_data)
```

## Format-Specific Conversions

### MP3 to PCM

```python
"""Convert MP3 to PCM."""
from pydub import AudioSegment

def mp3_to_pcm(mp3_file: str) -> bytes:
    """Convert MP3 to PCM 16kHz."""
    audio = AudioSegment.from_mp3(mp3_file)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)
    return audio.raw_data

# Usage
pcm_data = mp3_to_pcm("voice.mp3")
```

### WAV to PCM

```python
"""Convert WAV to PCM."""
from pydub import AudioSegment

def wav_to_pcm(wav_file: str) -> bytes:
    """Convert WAV to PCM 16kHz."""
    audio = AudioSegment.from_wav(wav_file)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)
    return audio.raw_data

# Usage
pcm_data = wav_to_pcm("voice.wav")
```

### OGG to PCM

```python
"""Convert OGG to PCM."""
from pydub import AudioSegment

def ogg_to_pcm(ogg_file: str) -> bytes:
    """Convert OGG to PCM 16kHz."""
    audio = AudioSegment.from_ogg(ogg_file)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)
    return audio.raw_data

# Usage
pcm_data = ogg_to_pcm("voice.ogg")
```

### M4A to PCM

```python
"""Convert M4A to PCM."""
from pydub import AudioSegment

def m4a_to_pcm(m4a_file: str) -> bytes:
    """Convert M4A to PCM 16kHz."""
    audio = AudioSegment.from_file(m4a_file, format="m4a")
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)
    return audio.raw_data

# Usage
pcm_data = m4a_to_pcm("voice.m4a")
```

### WebM to PCM

```python
"""Convert WebM (browser audio) to PCM."""
from pydub import AudioSegment

def webm_to_pcm(webm_data: bytes) -> bytes:
    """Convert WebM to PCM 16kHz."""
    audio = AudioSegment.from_file(
        io.BytesIO(webm_data),
        format="webm"
    )
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)
    return audio.raw_data

# Usage (from browser MediaRecorder)
webm_blob = await websocket.receive_bytes()
pcm_data = webm_to_pcm(webm_blob)
live_queue.send_realtime(pcm_data)
```

## Real-Time Streaming Conversion

### Stream MP3 to PCM

```python
"""Stream MP3 file to PCM chunks."""
from pydub import AudioSegment
import asyncio

async def stream_mp3_to_pcm(mp3_file: str, chunk_duration_ms: int = 100):
    """
    Stream MP3 file as PCM chunks.

    Args:
        mp3_file: Path to MP3 file
        chunk_duration_ms: Chunk size in milliseconds

    Yields:
        PCM chunks
    """
    # Load and convert
    audio = AudioSegment.from_mp3(mp3_file)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)

    # Chunk and stream
    for i in range(0, len(audio), chunk_duration_ms):
        chunk = audio[i:i + chunk_duration_ms]
        yield chunk.raw_data
        await asyncio.sleep(chunk_duration_ms / 1000.0)

# Usage
async for pcm_chunk in stream_mp3_to_pcm("long_audio.mp3", chunk_duration_ms=100):
    live_queue.send_realtime(pcm_chunk)
```

### Microphone to PCM (PyAudio)

```python
"""Capture microphone and convert to PCM."""
import pyaudio

def setup_microphone_stream():
    """Setup microphone for PCM 16kHz capture."""
    p = pyaudio.PyAudio()

    stream = p.open(
        format=pyaudio.paInt16,  # 16-bit
        channels=1,               # Mono
        rate=16000,               # 16kHz
        input=True,
        frames_per_buffer=1024,
    )

    return stream

# Usage
mic_stream = setup_microphone_stream()

while True:
    # Audio is already in correct format (PCM 16-bit, 16kHz, mono)
    pcm_chunk = mic_stream.read(1024, exception_on_overflow=False)
    live_queue.send_realtime(pcm_chunk)
```

## Output Conversion

### PCM to WAV (Save Agent Response)

```python
"""Save agent audio response as WAV file."""
import wave

def save_pcm_as_wav(pcm_data: bytes, output_file: str, sample_rate: int = 24000):
    """
    Save PCM data as WAV file.

    Args:
        pcm_data: PCM audio bytes
        output_file: Output WAV file path
        sample_rate: Sample rate (24000 for agent output)
    """
    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(1)           # Mono
        wf.setsampwidth(2)           # 16-bit (2 bytes)
        wf.setframerate(sample_rate) # Sample rate
        wf.writeframes(pcm_data)

# Usage - collect agent responses
agent_audio_chunks = []

async for event in runner.run_live(...):
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                agent_audio_chunks.append(part.inline_data.data)

# Save as WAV
all_audio = b''.join(agent_audio_chunks)
save_pcm_as_wav(all_audio, "agent_response.wav", sample_rate=24000)
```

### PCM to MP3 (Compress Agent Response)

```python
"""Convert agent PCM output to MP3."""
from pydub import AudioSegment
import io

def pcm_to_mp3(pcm_data: bytes, sample_rate: int = 24000) -> bytes:
    """
    Convert PCM to MP3.

    Args:
        pcm_data: PCM audio bytes
        sample_rate: Sample rate

    Returns:
        MP3 audio bytes
    """
    # Create AudioSegment from raw PCM
    audio = AudioSegment(
        data=pcm_data,
        sample_width=2,      # 16-bit
        frame_rate=sample_rate,
        channels=1           # Mono
    )

    # Export as MP3
    mp3_buffer = io.BytesIO()
    audio.export(mp3_buffer, format="mp3", bitrate="128k")

    return mp3_buffer.getvalue()

# Usage
agent_pcm = b''.join(agent_audio_chunks)
mp3_data = pcm_to_mp3(agent_pcm, sample_rate=24000)

with open("agent_response.mp3", "wb") as f:
    f.write(mp3_data)
```

## Browser Integration

### JavaScript Audio Capture to PCM

```javascript
/**
 * Capture browser audio and convert to PCM.
 */
class AudioCapturer {
    constructor() {
        this.audioContext = new AudioContext({ sampleRate: 16000 });
        this.mediaStream = null;
    }

    async start() {
        // Get microphone access
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
            }
        });

        // Create MediaRecorder
        const mediaRecorder = new MediaRecorder(this.mediaStream, {
            mimeType: 'audio/webm;codecs=opus'
        });

        mediaRecorder.ondataavailable = async (event) => {
            if (event.data.size > 0) {
                // Convert WebM to PCM
                const pcmData = await this.webmToPcm(event.data);

                // Send to server
                websocket.send(pcmData);
            }
        };

        // Start recording (send every 100ms)
        mediaRecorder.start(100);
    }

    async webmToPcm(webmBlob) {
        // Decode WebM
        const arrayBuffer = await webmBlob.arrayBuffer();
        const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

        // Get audio data (already 16kHz mono from getUserMedia config)
        const channelData = audioBuffer.getChannelData(0);

        // Convert float32 to int16 (PCM)
        const pcmData = new Int16Array(channelData.length);
        for (let i = 0; i < channelData.length; i++) {
            const s = Math.max(-1, Math.min(1, channelData[i]));
            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        return pcmData.buffer;
    }
}

// Usage
const capturer = new AudioCapturer();
await capturer.start();
```

## Validation

### Verify PCM Format

```python
"""Verify audio is in correct PCM format."""
def validate_pcm_format(pcm_data: bytes, expected_rate: int = 16000) -> bool:
    """
    Validate PCM format.

    Args:
        pcm_data: PCM audio bytes
        expected_rate: Expected sample rate

    Returns:
        True if valid
    """
    # Check byte length
    if len(pcm_data) % 2 != 0:
        print("Error: PCM data length not divisible by 2 (not 16-bit)")
        return False

    # Check sample count
    num_samples = len(pcm_data) // 2
    duration_seconds = num_samples / expected_rate

    print(f"PCM Format Validation:")
    print(f"  Total bytes: {len(pcm_data)}")
    print(f"  Samples: {num_samples}")
    print(f"  Duration: {duration_seconds:.2f} seconds")
    print(f"  Sample rate: {expected_rate} Hz")
    print(f"  Channels: 1 (mono)")
    print(f"  Bit depth: 16-bit")

    return True

# Usage
validate_pcm_format(pcm_data, expected_rate=16000)
```

## Common Issues

### Issue: Audio Too Fast/Slow

**Cause:** Incorrect sample rate

**Solution:**
```python
# Ensure correct sample rate
audio = audio.set_frame_rate(16000)  # For input
audio = audio.set_frame_rate(24000)  # For output
```

### Issue: Distorted Audio

**Cause:** Incorrect bit depth or stereo→mono conversion

**Solution:**
```python
# Proper stereo to mono
audio = audio.set_channels(1)  # Average channels

# Proper bit depth
audio = audio.set_sample_width(2)  # 16-bit
```

### Issue: Large File Sizes

**Cause:** Uncompressed PCM

**Solution:**
```python
# Compress to MP3 for storage
audio.export("output.mp3", format="mp3", bitrate="128k")
```

## Best Practices

1. **Use pydub for flexibility** - Handles many formats
2. **Validate format** - Check sample rate, channels, bit depth
3. **Stream in chunks** - Don't load entire file to memory
4. **Compress for storage** - PCM is large, use MP3/OGG for storage
5. **Test with various sources** - Different browsers/devices/formats

## Dependencies

```bash
# Install required packages
pip install pydub ffmpeg-python scipy numpy

# Install ffmpeg (system dependency)
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html
```

## See Also

- Native Audio Models: @/home/omixec/Claude-ADK-Skills/skills/adk-bidi-multi-agent/references/native-audio.md
- Interruption Handling: @/home/omixec/Claude-ADK-Skills/skills/adk-bidi-multi-agent/references/interruption-handling.md
- Audio Streaming Example: @/home/omixec/Claude-ADK-Skills/skills/adk-streaming-agents/examples/audio-streaming.md
