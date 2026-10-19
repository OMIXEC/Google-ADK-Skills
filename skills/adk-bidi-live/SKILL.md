---
name: adk-bidi-live
description: >-
  Builds real-time ADK experiences on the Live API: bidirectional audio and video,
  WebSocket streaming, LiveRequestQueue, and Gemini 3.8 Live models. Use when
  building a voice agent, streaming chat, or multimodal live interaction, or when
  migrating a 2.5/3.1 Live model to gemini-3.8-live. Don't use for
  request/response agents (use adk-agent-builder), for tool design (use
  adk-tools), or for deploying the live endpoint (use adk-deploy-production).
compatibility: google-adk>=2.9.2,<3
---

# ADK Bidi-Streaming and Live API

## Read first

1. `references/gemini-3.8-live.md` — the model contract: 131k in / 65k out, no
   `thinking_level`, async function calling by default, removed affective
   dialogue, forced proactive audio.
2. `references/adk-2x-baseline.md` — ADK 2.x version and import baseline.
3. The rest of `references/` as needed:
   - `index.md` — streaming overview
   - `custom-streaming-ws.md` — WebSocket streaming
   - `custom-streaming.md` — custom streaming patterns
   - `streaming-tools.md` — tools in a streaming context
   - `configuration.md` — streaming configuration

## Live models

| Model | Use |
|---|---|
| `gemini-3.8-live` | Default low-latency audio-to-audio voice, interleaved reasoning |
| `gemini-3.8-live-extended-thinking` | Voice plus background reasoning |
| `gemini-3.5-live-translate-preview` | Live translation |

`gemini-3.1-flash-live-preview` and
`gemini-2.5-flash-native-audio-preview-12-2025` shut down **2026-11-17**.
Migrate before then; do not start new work on either.

## Non-negotiables for 3.8 Live

- **Omit `thinking_level` and `thinking_config`.** The model rejects them. For
  background reasoning use `gemini-3.8-live-extended-thinking`.
- **Audio is the response modality.** Text comes from output audio
  transcription, not from a `TEXT` response modality.
- **`turn_complete=true` interrupts generation.** Send it only when you intend
  to cut the model off.
- **Proactive audio is always on.** `proactive_audio: false` errors.
- **Affective dialogue is gone.** Remove `enable_affective_dialog`.
- **All video frames are sent by default** (`TURN_INCLUDES_AUDIO_ACTIVITY_AND_ALL_VIDEO`).
  Narrow it when context or cost matters.
- **Function calls are asynchronous by default** (`NON_BLOCKING`). Set
  `behavior: BLOCKING` only where a synchronous result is required.

## 4-phase lifecycle

```python
# Phase 1: app initialization (once at startup)
agent = Agent(
    model="gemini-3.8-live",
    tools=[google_search],
    instruction="You are a helpful voice assistant",
)
runner = Runner(agent=agent, app_name="voice-app")

# Phase 2: session initialization (per connection)
live_request_queue = LiveRequestQueue()
run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["AUDIO"],
)

# Phase 3: streaming loop
async def streaming_session():
    async for event in runner.run_live(
        session_id=session_id,
        live_request_queue=live_request_queue,
        run_config=run_config,
    ):
        yield event

# Phase 4: cleanup
live_request_queue.close()
```

Do not add a thinking config to `RunConfig` for `gemini-3.8-live`.

## FastAPI WebSocket pattern

```python
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    live_request_queue = LiveRequestQueue()

    async def agent_to_client():
        async for event in runner.run_live(...):
            await websocket.send_json(event.model_dump())

    async def client_to_agent():
        async for message in websocket.iter_text():
            data = json.loads(message)
            content = types.Content(parts=[types.Part(text=data["text"])])
            live_request_queue.send_content(content)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(agent_to_client())
        tg.create_task(client_to_agent())
```

`send_client_content` is valid for the entire session, with an explicit `user`
or `model` role. Do not set `turn_complete=true` on every message; it interrupts
whatever the model is saying.

## Key components

- `LiveRequestQueue` — queue for user input into the model.
- `live_request_queue.send_content()` — send text, audio, or video content.
- `live_request_queue.close()` — signal end of session.
- `runner.run_live()` — async generator yielding live events.

## Boundaries

- The agent's tools belong to `adk-tools`.
- Model selection outside Live belongs to `adk-model-routing`.
- Deploying the WebSocket service belongs to `adk-deploy-production`.
