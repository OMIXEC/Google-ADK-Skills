# ADK 2.14.0 compatibility review

Reviewed against the google/adk-python v2.14.0 tag and an isolated google-adk==2.14.0 install. This is a selected API review; full skill-pack validation remains through 2.12.0.

- Move Runner(plugins=...) to App(plugins=[...]) and pass app=app to Runner. The old argument is deprecated; combining app and plugins raises ValueError.
- Replace LlmAgent(global_instruction=...) with GlobalInstructionPlugin at App level.
- SequentialAgent, ParallelAgent, and LoopAgent are deprecated for new compositions. Prefer Workflow; Workflow cannot yet be an LlmAgent sub-agent.
- Prefer validated App construction; legacy Runner(app_name, agent) has looser validation.

For bidirectional live audio, do not call `LiveRequestQueue.send_audio_stream_end()` at ordinary utterance boundaries; reserve it for when the input stream ends (for example, the microphone is muted). The 2.14.0 `RunConfig` includes input/output audio transcription, `realtime_input_config`, `session_resumption`, and `save_live_blob`; `save_live_audio` is deprecated.

Sources: https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/runners.py ; https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/agents/llm_agent.py ; https://github.com/google/adk-python/blob/v2.14.0/pyproject.toml ; https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/agents/sequential_agent.py
