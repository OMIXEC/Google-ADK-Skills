# ADK 2.14.0 live API compatibility review

Reviewed against the `google/adk-python` v2.14.0 tag and an isolated `google-adk==2.14.0` install. This is a selected API review; full skill-pack validation remains through 2.12.0.

Under VAD, do not send `LiveRequestQueue.send_audio_stream_end()` at every utterance boundary: it ends the input stream and flushes buffered audio. Send it when the microphone/input stream actually ends or is muted; use VAD/activity signals for utterance boundaries. `RunConfig` documents input/output audio transcription, `realtime_input_config` for VAD/turn handling, `session_resumption`, and `save_live_blob`; `save_live_audio` is deprecated. If `response_modalities` is omitted, `run_live` defaults to audio (and supplies AUDIO for native-audio models that reject an unset modality).

Do not infer supported model IDs from these API docs; verify the selected model separately before changing configuration.

Sources: [LiveRequestQueue](https://github.com/google/adk-python/blob/v2.14.0/docs/guides/live/live_request_queue/index.md), [live Runner](https://github.com/google/adk-python/blob/v2.14.0/docs/guides/runners/runner/live.md), [RunConfig](https://github.com/google/adk-python/blob/v2.14.0/docs/guides/agents/run_config/index.md).
