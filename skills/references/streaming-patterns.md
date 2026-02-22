# ADK Streaming Patterns

Comprehensive guide to real-time streaming, bidirectional communication, and LiveRequestQueue patterns for Google ADK.

## Live Models

| Model | Capabilities | Use Case |
|-------|-------------|----------|
| `gemini-live-2.5-flash-native-audio` | Native speech-to-speech | Voice assistants, real-time audio |
| `gemini-2.0-flash-live-001` | Text + audio streaming | Multimodal streaming |

## Core Components

### 1. LiveSession Wrapper

The `LiveSession` class wraps bidirectional streaming with LiveRequestQueue for multi-agent coordination.

```python
# adk_bidi/live_session.py
from google.adk.runners import Runner
from google.adk.streaming import LiveRequestQueue
import asyncio

class LiveSession:
    """Wrapper for bidirectional streaming with LiveRequestQueue."""

    def __init__(self, agent, model: str = "gemini-live-2.5-flash-native-audio"):
        self.agent = agent
        self.model = model
        self.runner = Runner(agent=agent, model=model)
        self.request_queue = LiveRequestQueue()

    async def start(self):
        """Start live session with bidirectional streaming."""
        # Start the runner with LiveRequestQueue
        response_stream = self.runner.run_live(
            live_request_queue=self.request_queue
        )

        # Process responses
        async for response in response_stream:
            yield response

    async def send_text(self, text: str):
        """Send text message to agent."""
        await self.request_queue.put({"type": "text", "content": text})

    async def send_audio(self, audio_data: bytes):
        """Send audio data to agent."""
        await self.request_queue.put({"type": "audio", "data": audio_data})

    async def send_tool_response(self, tool_name: str, result: dict):
        """Send tool execution result back to agent."""
        await self.request_queue.put({
            "type": "tool_response",
            "tool": tool_name,
            "result": result
        })

    async def close(self):
        """Close the live session."""
        await self.request_queue.close()
```

### 2. WebSocket Server Pattern

```python
# src/websocket_server.py
from fastapi import FastAPI, WebSocket
from adk_bidi import LiveSession
from google.adk.agents import Agent
import asyncio
import json

app = FastAPI()

agent = Agent(
    name="voice_agent",
    model="gemini-live-2.5-flash-native-audio",
    description="Real-time voice assistant",
    instruction="You are a helpful voice assistant...",
)

@app.websocket("/ws/voice")
async def voice_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time voice interaction."""
    await websocket.accept()

    # Create live session
    session = LiveSession(agent=agent)

    # Start receiving and sending concurrently
    async def receive_from_client():
        try:
            while True:
                data = await websocket.receive_bytes()
                # Send audio to agent
                await session.send_audio(data)
        except Exception as e:
            print(f"Client disconnected: {e}")
            await session.close()

    async def send_to_client():
        try:
            async for response in session.start():
                if response.get("type") == "audio":
                    # Send audio response to client
                    await websocket.send_bytes(response["data"])
                elif response.get("type") == "text":
                    # Send text response
                    await websocket.send_json(response)
        except Exception as e:
            print(f"Session error: {e}")

    # Run both tasks concurrently
    await asyncio.gather(
        receive_from_client(),
        send_to_client(),
    )
```

### 3. Multi-Agent Live Coordination

```python
# src/multi_agent_live.py
from adk_bidi import LiveSession
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

# Specialist agents
researcher = Agent(
    name="researcher",
    model="gemini-2.5-flash",
    description="Research specialist",
    instruction="Search and gather information...",
)

analyst = Agent(
    name="analyst",
    model="gemini-2.5-pro",
    description="Analysis specialist",
    instruction="Analyze data and extract insights...",
)

# Supervisor with live streaming
supervisor = Agent(
    name="supervisor",
    model="gemini-live-2.5-flash-native-audio",
    description="Multi-agent coordinator with live interaction",
    instruction="""
    You coordinate a team of specialists in real-time.

    Specialists:
    - researcher: Gathers information
    - analyst: Analyzes findings

    Workflow:
    1. Understand user query
    2. Delegate to appropriate specialist(s)
    3. Stream results back to user in real-time
    4. Synthesize final response
    """,
    tools=[
        AgentTool(agent=researcher),
        AgentTool(agent=analyst),
    ],
)

# Use LiveSession for real-time coordination
async def run_live_multi_agent():
    session = LiveSession(agent=supervisor)

    # Send user query
    await session.send_text("Research and analyze recent AI developments")

    # Stream responses
    async for response in session.start():
        if response.get("type") == "text":
            print(f"Response: {response['content']}")
        elif response.get("type") == "tool_call"):
            # Specialist agent was invoked
            print(f"Delegating to: {response['tool']}")
```

## Voice Assistant Patterns

### Basic Voice Agent

```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

def search_calendar(query: str) -> dict:
    """Search calendar events."""
    # Implementation
    return {"events": [...]}

def create_reminder(title: str, time: str) -> dict:
    """Create reminder."""
    # Implementation
    return {"reminder_id": "123"}

voice_agent = Agent(
    name="voice_assistant",
    model="gemini-live-2.5-flash-native-audio",
    description="Voice-enabled personal assistant",
    instruction="""
    You are a voice assistant helping with calendar and reminders.

    **Communication Style:**
    - Natural, conversational speech
    - Concise responses (voice context)
    - Confirm actions before executing

    **Capabilities:**
    - Search calendar events
    - Create reminders
    - Natural language understanding
    """,
    tools=[
        FunctionTool(search_calendar),
        FunctionTool(create_reminder),
    ],
)
```

### Voice Agent with VAD (Voice Activity Detection)

```python
from adk_bidi import LiveSession

class VoiceAgentWithVAD(LiveSession):
    """Voice agent with Voice Activity Detection."""

    def __init__(self, agent):
        super().__init__(agent)
        self.vad_enabled = True
        self.silence_threshold = 0.5  # seconds
        self.is_speaking = False

    async def process_audio(self, audio_chunk: bytes):
        """Process audio with VAD."""
        # Detect if audio contains speech
        has_speech = self.detect_speech(audio_chunk)

        if has_speech:
            self.is_speaking = True
            await self.send_audio(audio_chunk)
        elif self.is_speaking:
            # Silence detected after speech - end of utterance
            self.is_speaking = False
            await self.send_text("[END_OF_UTTERANCE]")

    def detect_speech(self, audio: bytes) -> bool:
        """Simple VAD - detect if audio contains speech."""
        # Implement VAD logic (energy threshold, model-based, etc.)
        energy = self.calculate_energy(audio)
        return energy > self.silence_threshold

    def calculate_energy(self, audio: bytes) -> float:
        """Calculate audio energy level."""
        # Simplified energy calculation
        import numpy as np
        audio_array = np.frombuffer(audio, dtype=np.int16)
        return np.abs(audio_array).mean() / 32768.0
```

## Streaming Response Handling

### Text Streaming

```python
from google.adk.runners import Runner

runner = Runner(agent=agent, model="gemini-2.5-flash")

# Stream text responses
async for chunk in runner.run_stream(prompt="Explain quantum computing"):
    if chunk.get("type") == "text":
        print(chunk["content"], end="", flush=True)
```

### Audio Streaming

```python
runner = Runner(agent=agent, model="gemini-live-2.5-flash-native-audio")

async for chunk in runner.run_stream(prompt="Tell me a story"):
    if chunk.get("type") == "audio":
        # Play audio chunk
        audio_player.play(chunk["data"])
    elif chunk.get("type") == "text":
        # Also get text transcript
        print(chunk["content"])
```

### Multimodal Streaming

```python
runner = Runner(agent=agent, model="gemini-2.0-flash-live-001")

async for chunk in runner.run_stream(
    prompt="Describe this image",
    modalities=["TEXT", "AUDIO"]
):
    if chunk.get("type") == "text":
        # Display text
        display_text(chunk["content"])
    elif chunk.get("type") == "audio":
        # Play audio description
        audio_player.play(chunk["data"])
```

## Real-Time Multi-Agent Patterns

### Pattern 1: Parallel Specialists with Live Aggregation

```python
async def parallel_live_agents(query: str):
    """Run multiple specialists in parallel, aggregate live."""
    # Create live sessions for each specialist
    researcher_session = LiveSession(agent=researcher)
    analyst_session = LiveSession(agent=analyst)

    # Send query to both
    await researcher_session.send_text(query)
    await analyst_session.send_text(query)

    # Aggregate responses in real-time
    async def aggregate():
        results = {"research": [], "analysis": []}

        async for response in researcher_session.start():
            results["research"].append(response)
            yield {"source": "researcher", "data": response}

        async for response in analyst_session.start():
            results["analysis"].append(response)
            yield {"source": "analyst", "data": response}

    # Stream aggregated results
    async for result in aggregate():
        print(f"[{result['source']}]: {result['data']}")
```

### Pattern 2: Sequential Live Pipeline

```python
async def live_pipeline(input_data: str):
    """Sequential pipeline with live streaming."""
    # Stage 1: Research
    research_session = LiveSession(agent=researcher)
    await research_session.send_text(input_data)

    research_results = []
    async for response in research_session.start():
        research_results.append(response)
        yield {"stage": "research", "data": response}

    # Stage 2: Analysis (uses research results)
    analysis_session = LiveSession(agent=analyst)
    await analysis_session.send_text(str(research_results))

    async for response in analysis_session.start():
        yield {"stage": "analysis", "data": response}
```

## WebRTC Integration

### WebRTC Signaling Server

```python
from fastapi import FastAPI, WebSocket
from adk_bidi import LiveSession
import json

app = FastAPI()

@app.websocket("/webrtc/signaling")
async def webrtc_signaling(websocket: WebSocket):
    """WebRTC signaling for peer-to-peer voice/video."""
    await websocket.accept()

    session = LiveSession(agent=voice_agent)

    async def handle_signaling():
        async for message in websocket.iter_json():
            if message["type"] == "offer":
                # Handle WebRTC offer
                answer = create_webrtc_answer(message["sdp"])
                await websocket.send_json({"type": "answer", "sdp": answer})

            elif message["type"] == "ice_candidate":
                # Handle ICE candidate
                add_ice_candidate(message["candidate"])

            elif message["type"] == "audio":
                # Forward audio to agent
                await session.send_audio(message["data"])

    async def stream_agent_audio():
        async for response in session.start():
            if response.get("type") == "audio":
                # Stream agent audio to WebRTC peer
                await websocket.send_json({
                    "type": "audio",
                    "data": response["data"]
                })

    await asyncio.gather(
        handle_signaling(),
        stream_agent_audio(),
    )
```

## Performance Optimization

### 1. Buffer Management

```python
class BufferedLiveSession(LiveSession):
    """LiveSession with buffered audio for smoother streaming."""

    def __init__(self, agent, buffer_size: int = 4096):
        super().__init__(agent)
        self.buffer_size = buffer_size
        self.audio_buffer = bytearray()

    async def send_audio_buffered(self, audio_chunk: bytes):
        """Buffer audio before sending."""
        self.audio_buffer.extend(audio_chunk)

        if len(self.audio_buffer) >= self.buffer_size:
            # Send full buffer
            await self.send_audio(bytes(self.audio_buffer))
            self.audio_buffer.clear()
```

### 2. Connection Pooling

```python
class LiveSessionPool:
    """Pool of LiveSession connections for load balancing."""

    def __init__(self, agent, pool_size: int = 5):
        self.agent = agent
        self.pool = []
        self.pool_size = pool_size

    async def initialize(self):
        """Initialize session pool."""
        for _ in range(self.pool_size):
            session = LiveSession(agent=self.agent)
            self.pool.append(session)

    async def get_session(self) -> LiveSession:
        """Get available session from pool."""
        # Simple round-robin
        return self.pool[0]  # Implement proper selection logic
```

### 3. Latency Optimization

```python
# Use lower latency model for real-time
agent = Agent(
    name="low_latency_agent",
    model="gemini-live-2.5-flash-native-audio",  # Optimized for speed
    description="Low-latency voice agent",
)

# Minimize processing in streaming path
async def optimized_streaming():
    session = LiveSession(agent=agent)

    async for response in session.start():
        # Direct streaming - no buffering
        yield response  # Immediately yield without processing
```

## Error Handling

### Graceful Disconnection

```python
async def resilient_live_session(agent):
    """Live session with reconnection logic."""
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            session = LiveSession(agent=agent)

            async for response in session.start():
                yield response

            break  # Success

        except ConnectionError as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise
            await asyncio.sleep(2 ** retry_count)  # Exponential backoff

        finally:
            await session.close()
```

### Timeout Handling

```python
import asyncio

async def session_with_timeout(agent, timeout: int = 30):
    """Live session with timeout."""
    session = LiveSession(agent=agent)

    try:
        async for response in asyncio.wait_for(session.start(), timeout=timeout):
            yield response
    except asyncio.TimeoutError:
        print(f"Session timeout after {timeout}s")
    finally:
        await session.close()
```

## Testing Real-Time Agents

### Mock LiveSession

```python
class MockLiveSession:
    """Mock LiveSession for testing."""

    def __init__(self, mock_responses: list):
        self.mock_responses = mock_responses
        self.sent_messages = []

    async def send_text(self, text: str):
        self.sent_messages.append({"type": "text", "content": text})

    async def send_audio(self, audio: bytes):
        self.sent_messages.append({"type": "audio", "data": audio})

    async def start(self):
        for response in self.mock_responses:
            yield response

# Test
async def test_voice_agent():
    mock_session = MockLiveSession([
        {"type": "text", "content": "Hello!"},
        {"type": "audio", "data": b"audio_data"},
    ])

    responses = []
    async for response in mock_session.start():
        responses.append(response)

    assert len(responses) == 2
```

## Related Files

- @agent-patterns.md - Agent architecture patterns
- @tool-catalog.md - Tool integration patterns
- @deployment-configs.md - Deployment configurations
