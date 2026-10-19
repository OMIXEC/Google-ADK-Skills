# Configurating streaming behaviour

There are some configurations you can set for live(streaming) agents.

It's set by RunConfig. You should use RunConfig with your Runner.run_live(...).

For example, if you want to set voice config, you can leverage speech_config.

```python
voice_config = genai_types.VoiceConfig(
    prebuilt_voice_config=genai_types.PrebuiltVoiceConfigDict(
        voice_name='Aoede'
    )
)
speech_config = genai_types.SpeechConfig(voice_config=voice_config)
run_config = RunConfig(speech_config=speech_config)

runner.run_live(
    ...,
    run_config=run_config,
)
```


