"""
StreamingPresets - Pre-configured streaming configurations.

Provides ready-to-use RunConfig presets for common streaming scenarios:
- Voice-only agents with VAD
- Text + audio multimodal
- Autonomous proactive agents
- Video streaming with transcription
"""

from typing import Optional
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types


_START_SENSITIVITY = {
    "LOW": types.StartSensitivity.START_SENSITIVITY_LOW,
    "HIGH": types.StartSensitivity.START_SENSITIVITY_HIGH,
}
_END_SENSITIVITY = {
    "LOW": types.EndSensitivity.END_SENSITIVITY_LOW,
    "HIGH": types.EndSensitivity.END_SENSITIVITY_HIGH,
}


class StreamingPresets:
    """
    Pre-configured streaming configurations for common use cases.

    Example:
        config = StreamingPresets.voice_only()
        runner.run_live(session_id=sid, run_config=config, ...)
    """

    @staticmethod
    def voice_only(
        enable_vad: bool = True,
        speech_start_sensitivity: str = "LOW",
        speech_end_sensitivity: str = "HIGH",
    ) -> RunConfig:
        """
        Native audio model configuration for voice-only agents.

        Optimized for low-latency voice interactions with automatic
        voice activity detection (VAD).

        Args:
            enable_vad: Enable automatic voice activity detection
            speech_start_sensitivity: Sensitivity for detecting speech start
            speech_end_sensitivity: Sensitivity for detecting speech end

        Returns:
            RunConfig configured for voice-only streaming
        """
        config_kwargs = {
            "streaming_mode": StreamingMode.BIDI,
            "response_modalities": ["AUDIO"],
            "input_audio_transcription": types.AudioTranscriptionConfig(),
            "output_audio_transcription": types.AudioTranscriptionConfig(),
            "session_resumption": types.SessionResumptionConfig(),
        }

        if enable_vad:
            # Map sensitivity strings to types
            start_sens = _START_SENSITIVITY.get(
                str(speech_start_sensitivity).upper(),
                types.StartSensitivity.START_SENSITIVITY_LOW,
            )
            end_sens = _END_SENSITIVITY.get(
                str(speech_end_sensitivity).upper(),
                types.EndSensitivity.END_SENSITIVITY_HIGH,
            )

            config_kwargs["realtime_input_config"] = types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    disabled=False,
                    start_of_speech_sensitivity=start_sens,
                    end_of_speech_sensitivity=end_sens,
                    prefix_padding_ms=0,
                    silence_duration_ms=500,
                )
            )

        return RunConfig(**config_kwargs)

    @staticmethod
    def text_only() -> RunConfig:
        """
        Text-only streaming configuration.

        For agents that only need text input/output without audio.

        Returns:
            RunConfig configured for text-only streaming
        """
        return RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=["TEXT"],
            session_resumption=types.SessionResumptionConfig(),
        )

    @staticmethod
    def text_and_audio(
        enable_transcription: bool = True,
    ) -> RunConfig:
        """
        Multimodal text + audio configuration.

        Supports both text and audio input/output with optional
        transcription for accessibility.

        Args:
            enable_transcription: Enable audio transcription

        Returns:
            RunConfig configured for text + audio streaming
        """
        config_kwargs = {
            "streaming_mode": StreamingMode.BIDI,
            "response_modalities": ["AUDIO"],
            "session_resumption": types.SessionResumptionConfig(),
        }

        if enable_transcription:
            config_kwargs["input_audio_transcription"] = types.AudioTranscriptionConfig()
            config_kwargs["output_audio_transcription"] = types.AudioTranscriptionConfig()

        return RunConfig(**config_kwargs)

    @staticmethod
    def autonomous_proactive() -> RunConfig:
        """
        Live session with proactive audio.

        Proactive audio is permanently enabled on Gemini 3.8 Live;
        `proactive_audio=False` is an error. Affective dialogue was removed
        from the API, so no emotion flag is emitted here.

        Returns:
            RunConfig configured for autonomous proactive behavior
        """
        return RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=["AUDIO"],
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            session_resumption=types.SessionResumptionConfig(),
            proactivity=types.ProactivityConfig(proactive_audio=True),
        )

    @staticmethod
    def video_streaming(
        include_audio: bool = True,
        enable_transcription: bool = True,
    ) -> RunConfig:
        """
        Video streaming configuration with optional audio.

        For agents processing video frames with optional audio input.

        Args:
            include_audio: Include audio in the stream
            enable_transcription: Enable audio transcription

        Returns:
            RunConfig configured for video streaming
        """
        modalities = ["TEXT"]
        if include_audio:
            modalities.append("AUDIO")

        config_kwargs = {
            "streaming_mode": StreamingMode.BIDI,
            "response_modalities": modalities,
            "session_resumption": types.SessionResumptionConfig(),
        }

        if include_audio and enable_transcription:
            config_kwargs["input_audio_transcription"] = types.AudioTranscriptionConfig()
            config_kwargs["output_audio_transcription"] = types.AudioTranscriptionConfig()

        return RunConfig(**config_kwargs)

    @staticmethod
    def native_audio(
        model_variant: str = "default",
    ) -> RunConfig:
        """
        Native audio model configuration for speech-to-speech.

        Optimized for models like gemini-3.8-live
        that process audio natively without transcription.

        Args:
            model_variant: Native audio model variant

        Returns:
            RunConfig configured for native audio processing
        """
        return RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=["AUDIO"],
            session_resumption=types.SessionResumptionConfig(),
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    disabled=False,
                    start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
                    end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                )
            ),
        )

    @staticmethod
    def custom(
        modalities: list[str],
        enable_vad: bool = False,
        enable_transcription: bool = False,
        enable_proactivity: bool = True,
        enable_session_resumption: bool = True,
        vad_config: Optional[dict] = None,
    ) -> RunConfig:
        """
        Custom streaming configuration with full control.

        Args:
            modalities: List of response modalities (["TEXT"], ["AUDIO"], or both)
            enable_vad: Enable voice activity detection
            enable_transcription: Enable audio transcription
            enable_proactivity: Kept for API compatibility; proactive audio is always on
            enable_session_resumption: Enable session resumption
            vad_config: Custom VAD configuration dict

        Returns:
            Custom RunConfig based on parameters
        """
        config_kwargs = {
            "streaming_mode": StreamingMode.BIDI,
            "response_modalities": modalities,
        }

        if enable_session_resumption:
            config_kwargs["session_resumption"] = types.SessionResumptionConfig()

        if enable_transcription and "AUDIO" in modalities:
            config_kwargs["input_audio_transcription"] = types.AudioTranscriptionConfig()
            config_kwargs["output_audio_transcription"] = types.AudioTranscriptionConfig()

        if enable_proactivity:
            config_kwargs["proactivity"] = types.ProactivityConfig(proactive_audio=True)

        if enable_vad:
            vad_settings = vad_config or {}
            config_kwargs["realtime_input_config"] = types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    disabled=False,
                    start_of_speech_sensitivity=vad_settings.get(
                        "start_sensitivity", types.StartSensitivity.START_SENSITIVITY_LOW
                    ),
                    end_of_speech_sensitivity=vad_settings.get(
                        "end_sensitivity", types.EndSensitivity.END_SENSITIVITY_HIGH
                    ),
                    prefix_padding_ms=vad_settings.get("prefix_padding_ms", 0),
                    silence_duration_ms=vad_settings.get("silence_duration_ms", 500),
                )
            )

        return RunConfig(**config_kwargs)


# Convenience aliases
VOICE_CONFIG = StreamingPresets.voice_only()
TEXT_CONFIG = StreamingPresets.text_only()
MULTIMODAL_CONFIG = StreamingPresets.text_and_audio()
AUTONOMOUS_CONFIG = StreamingPresets.autonomous_proactive()
