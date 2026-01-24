"""
LiveSession - Wrapper for LiveRequestQueue bidirectional streaming.

Provides a simplified interface for managing real-time streaming sessions
with text, audio, image, and video input support.
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types


@dataclass
class SessionMetadata:
    """Metadata for tracking session state."""
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    is_active: bool = True


class LiveSession:
    """
    Manages bidirectional streaming session with LiveRequestQueue.

    Provides methods for sending text, audio, images, and activity signals
    to the Live API for real-time agent interactions.

    Example:
        session = LiveSession(session_id="user123", user_id="user123")
        session.send_text("Hello, how can I help?")
        session.send_audio(audio_bytes, sample_rate=16000)
        session.close()
    """

    def __init__(
        self,
        session_id: str,
        user_id: str = "default",
        modality: str = "AUDIO",
        enable_transcription: bool = True,
        enable_session_resumption: bool = True,
    ):
        """
        Initialize a live streaming session.

        Args:
            session_id: Unique identifier for this session
            user_id: User identifier for the session
            modality: Response modality ("TEXT", "AUDIO", or both)
            enable_transcription: Enable audio transcription
            enable_session_resumption: Enable session resumption for reconnection
        """
        self.session_id = session_id
        self.user_id = user_id
        self.queue = LiveRequestQueue()
        self.metadata = SessionMetadata(session_id=session_id, user_id=user_id)

        # Build run configuration
        config_kwargs = {
            "streaming_mode": StreamingMode.BIDI,
            "response_modalities": [modality] if isinstance(modality, str) else modality,
        }

        if enable_transcription:
            config_kwargs["input_audio_transcription"] = types.AudioTranscriptionConfig()
            config_kwargs["output_audio_transcription"] = types.AudioTranscriptionConfig()

        if enable_session_resumption:
            config_kwargs["session_resumption"] = types.SessionResumptionConfig()

        self.config = RunConfig(**config_kwargs)

    def send_text(self, text: str, role: str = "user") -> None:
        """
        Send text content to the agent.

        Args:
            text: The text message to send
            role: The role of the sender (default: "user")
        """
        content = types.Content(
            role=role,
            parts=[types.Part(text=text)]
        )
        self.queue.send_content(content)
        self._update_activity()

    def send_audio(self, audio_data: bytes, sample_rate: int = 16000) -> None:
        """
        Send audio data to the agent in real-time.

        Args:
            audio_data: Raw PCM audio bytes
            sample_rate: Audio sample rate in Hz (default: 16000)
        """
        blob = types.Blob(
            mime_type=f"audio/pcm;rate={sample_rate}",
            data=audio_data
        )
        self.queue.send_realtime(blob)
        self._update_activity()

    def send_image(self, image_data: bytes, mime_type: str = "image/jpeg") -> None:
        """
        Send image data to the agent.

        Args:
            image_data: Raw image bytes
            mime_type: Image MIME type (default: "image/jpeg")
        """
        blob = types.Blob(mime_type=mime_type, data=image_data)
        self.queue.send_realtime(blob)
        self._update_activity()

    def send_video_frame(self, frame_data: bytes, mime_type: str = "image/jpeg") -> None:
        """
        Send a video frame to the agent.

        Args:
            frame_data: Raw frame bytes (typically JPEG)
            mime_type: Frame MIME type (default: "image/jpeg")
        """
        self.send_image(frame_data, mime_type)

    def signal_activity_start(self) -> None:
        """Signal the start of user activity (e.g., started speaking)."""
        self.queue.send_activity_start()
        self._update_activity()

    def signal_activity_end(self) -> None:
        """Signal the end of user activity (e.g., stopped speaking)."""
        self.queue.send_activity_end()
        self._update_activity()

    def close(self) -> None:
        """Close the streaming session and release resources."""
        self.queue.close()
        self.metadata.is_active = False

    def _update_activity(self) -> None:
        """Update session activity metadata."""
        self.metadata.last_activity = datetime.now()
        self.metadata.message_count += 1

    @property
    def is_active(self) -> bool:
        """Check if the session is still active."""
        return self.metadata.is_active

    def get_stats(self) -> dict:
        """Get session statistics."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.metadata.created_at.isoformat(),
            "last_activity": self.metadata.last_activity.isoformat(),
            "message_count": self.metadata.message_count,
            "is_active": self.metadata.is_active,
            "duration_seconds": (datetime.now() - self.metadata.created_at).total_seconds(),
        }


class MultimodalLiveSession(LiveSession):
    """
    Extended LiveSession with multimodal input handling.

    Supports combined text, audio, and video streaming with
    automatic content type detection.
    """

    def __init__(
        self,
        session_id: str,
        user_id: str = "default",
        enable_video: bool = True,
        enable_affective_dialog: bool = False,
        enable_proactivity: bool = False,
    ):
        """
        Initialize a multimodal live session.

        Args:
            session_id: Unique identifier for this session
            user_id: User identifier
            enable_video: Enable video frame processing
            enable_affective_dialog: Enable emotion-aware responses
            enable_proactivity: Enable proactive agent behavior
        """
        super().__init__(
            session_id=session_id,
            user_id=user_id,
            modality=["TEXT", "AUDIO"],
        )

        # Extend config for multimodal
        config_kwargs = {
            "streaming_mode": StreamingMode.BIDI,
            "response_modalities": ["TEXT", "AUDIO"],
            "input_audio_transcription": types.AudioTranscriptionConfig(),
            "output_audio_transcription": types.AudioTranscriptionConfig(),
            "session_resumption": types.SessionResumptionConfig(),
        }

        if enable_affective_dialog:
            config_kwargs["enable_affective_dialog"] = True

        if enable_proactivity:
            config_kwargs["proactivity"] = types.ProactivityConfig(proactive_audio=True)

        self.config = RunConfig(**config_kwargs)
        self.enable_video = enable_video

    def send_multimodal(
        self,
        text: Optional[str] = None,
        audio: Optional[bytes] = None,
        image: Optional[bytes] = None,
    ) -> None:
        """
        Send multimodal content in a single call.

        Args:
            text: Optional text content
            audio: Optional audio bytes (PCM)
            image: Optional image bytes (JPEG)
        """
        if text:
            self.send_text(text)
        if audio:
            self.send_audio(audio)
        if image and self.enable_video:
            self.send_image(image)
