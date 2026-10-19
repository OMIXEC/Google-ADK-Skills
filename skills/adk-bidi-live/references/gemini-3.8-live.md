# Gemini 3.8 Live

Verified 2026-10-19 from
<https://ai.google.dev/gemini-api/docs/models/gemini-3.8-live> (updated
September 2026).

## Specification

| Property | Value |
|---|---|
| Model code | `gemini-3.8-live` |
| Status | Stable |
| Inputs | Text, images, audio, video |
| Outputs | Text and audio (audio is the supported response modality) |
| Input token limit | 131,072 |
| Output token limit | 65,536 |
| Live API | Supported |
| Thinking | Supported — interleaved reasoning |
| Function calling | Supported (asynchronous by default) |
| Search grounding | Supported |
| Audio generation | Supported |
| Caching | Not supported |
| Code execution | Not supported |
| File search | Not supported |
| Maps grounding | Not supported |
| Image generation | Not supported |
| Structured outputs | Not supported |
| URL context | Not supported |
| Batch API | Not supported |

Do not size Live sessions from the 1M text-model window. Live is 131k in /
65k out.

## Reasoning

`gemini-3.8-live` reasons inline without adding a separate thinking phase.
**It does not accept `thinking_level` or `thinking_config`.** Omit both from
the session setup; sending them is not how this model is configured.

When the agent must reason in the background while the conversation continues,
switch to `gemini-3.8-live-extended-thinking`. That is a different model, not a
flag on this one.

## Function calling

Asynchronous execution (`behavior: NON_BLOCKING`) is the **default**. Synchronous
blocking mode remains available for compatibility by setting
`behavior: BLOCKING` on the tool declaration.

Function scheduling is supported: `SILENT`, `WHEN_IDLE`, `INTERRUPTED`.

## Session control

- `send_client_content` works across the whole session lifecycle, with explicit
  roles (`user` or `model`).
- `turn_complete=true` **unconditionally interrupts** active generation. Use it
  deliberately.
- Without `turn_complete`, the server waits for subsequent messages before
  responding.
- Audio is the response modality. If the application needs a text transcript,
  enable output audio transcription rather than asking for a text response.
- Turn coverage defaults to `TURN_INCLUDES_AUDIO_ACTIVITY_AND_ALL_VIDEO`: video
  frames are sent by default. Send frames only when needed to control context
  and cost.

## Removed or forced behavior

| Behavior | State |
|---|---|
| Proactive audio | **Permanently enabled.** `proactive_audio: false` returns an error. |
| Affective dialogue | **Removed from the API.** Delete `enable_affective_dialog` from existing code. |
| Text response modality | Not the supported Live output; use audio plus transcription. |

## Migrating from Gemini 3.1 Flash Live

1. **Model string** — `gemini-3.1-flash-live-preview` → `gemini-3.8-live`.
2. **Thinking** — remove `thinking_level` / `thinking_config` from the session
   setup. Use `gemini-3.8-live-extended-thinking` if background reasoning is
   required.
3. **Function calling** — expect `NON_BLOCKING` by default. Add
   `behavior: BLOCKING` only where a synchronous tool result is required.
4. **Client content** — `send_client_content` is now valid for the whole
   session. Re-check every `turn_complete=true`: it interrupts generation.
5. **Proactive audio** — remove any `proactive_audio: false` configuration.
6. **Affective dialogue** — remove `enable_affective_dialog`.
7. **Turn coverage** — decide explicitly whether every video frame should be
   sent; the default includes all video.
8. **Transcripts** — enable output audio transcription if the app displayed text
   before.

`gemini-3.1-flash-live-preview` and
`gemini-2.5-flash-native-audio-preview-12-2025` shut down **2026-11-17**.
