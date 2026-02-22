"""
VoiceAgent - Native audio agent for voice interactions.

Provides voice-optimized agents using native audio models
with speech-to-speech capabilities.
"""

from typing import Optional, List, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from adk_bidi.agents.bidi_agent import BidiAgent
from adk_bidi.memory.working_memory import WorkingMemory
from adk_bidi.memory.shared_memory import SharedMemory


class VoicePersonality(Enum):
    """Pre-defined voice personalities."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CASUAL = "casual"
    FORMAL = "formal"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"


@dataclass
class VoiceConfig:
    """Configuration for voice agent behavior."""
    personality: VoicePersonality = VoicePersonality.FRIENDLY
    speaking_rate: str = "normal"  # slow, normal, fast
    enable_emotions: bool = True
    enable_interruption: bool = True
    silence_threshold_ms: int = 500
    use_native_audio: bool = True


class VoiceAgent(BidiAgent):
    """
    Native audio agent for voice interactions.

    Optimized for speech-to-speech communication with:
    - Native audio model support
    - Voice activity detection
    - Emotion-aware responses
    - Interruption handling

    Example:
        agent = VoiceAgent(
            name="voice_assistant",
            instruction="You are a friendly voice assistant.",
            personality=VoicePersonality.FRIENDLY,
        )
    """

    # Native audio model
    NATIVE_AUDIO_MODEL = "gemini-live-2.5-flash-native-audio"
    STANDARD_LIVE_MODEL = "gemini-2.0-flash-live-001"

    # Personality templates
    PERSONALITY_INSTRUCTIONS = {
        VoicePersonality.PROFESSIONAL: """
Speak in a professional, business-appropriate manner.
Use clear, concise language and maintain a respectful tone.
Avoid colloquialisms and maintain formality.""",

        VoicePersonality.FRIENDLY: """
Be warm, approachable, and conversational.
Use a casual but respectful tone.
Feel free to use light humor when appropriate.""",

        VoicePersonality.CASUAL: """
Be relaxed and informal in your speech.
Use everyday language and contractions.
Keep responses natural and conversational.""",

        VoicePersonality.FORMAL: """
Maintain a highly formal and respectful tone.
Use proper grammar and avoid contractions.
Be polite and deferential in your responses.""",

        VoicePersonality.ENTHUSIASTIC: """
Be energetic and positive in your responses.
Show excitement and engagement.
Use expressive language that conveys enthusiasm.""",

        VoicePersonality.CALM: """
Speak in a soothing, measured tone.
Be patient and reassuring.
Take your time and don't rush responses.""",
    }

    def __init__(
        self,
        name: str,
        instruction: str,
        voice_config: Optional[VoiceConfig] = None,
        personality: Optional[VoicePersonality] = None,
        tools: Optional[List[Any]] = None,
        working_memory: Optional[WorkingMemory] = None,
        shared_memory: Optional[SharedMemory] = None,
        **kwargs,
    ):
        """
        Initialize a voice agent.

        Args:
            name: Agent name
            instruction: Base instruction
            voice_config: Voice configuration
            personality: Voice personality (shorthand for voice_config)
            tools: Available tools
            working_memory: Working memory instance
            shared_memory: Shared memory instance
            **kwargs: Additional arguments passed to BidiAgent
        """
        self.voice_config = voice_config or VoiceConfig()

        # Apply personality shorthand
        if personality:
            self.voice_config.personality = personality

        # Select model based on native audio setting
        model = (
            self.NATIVE_AUDIO_MODEL
            if self.voice_config.use_native_audio
            else self.STANDARD_LIVE_MODEL
        )

        # Build enhanced instruction
        enhanced_instruction = self._build_voice_instruction(instruction)

        super().__init__(
            name=name,
            instruction=enhanced_instruction,
            model=model,
            tools=tools,
            working_memory=working_memory,
            shared_memory=shared_memory,
            **kwargs,
        )

        # Voice-specific state
        self.is_speaking = False
        self.was_interrupted = False
        self.turn_start_time: Optional[datetime] = None

    def _build_voice_instruction(self, base_instruction: str) -> str:
        """Build instruction with voice-specific guidance."""
        personality_text = self.PERSONALITY_INSTRUCTIONS.get(
            self.voice_config.personality,
            ""
        )

        voice_guidance = f"""
{base_instruction}

**Voice Interaction Guidelines:**
{personality_text}

- Keep responses conversational and natural for spoken delivery
- Use shorter sentences that are easy to speak and understand
- Pause naturally between ideas
- Respond to audio cues and adjust your tone accordingly
- If interrupted, acknowledge and adapt smoothly
"""

        if self.voice_config.enable_emotions:
            voice_guidance += """
- Detect emotional cues in the user's voice and respond empathetically
- Adjust your tone to match the conversation's emotional context
"""

        return voice_guidance

    async def on_speech_start(self) -> None:
        """Called when the agent starts speaking."""
        self.is_speaking = True
        self.turn_start_time = datetime.now()

    async def on_speech_end(self) -> None:
        """Called when the agent finishes speaking."""
        self.is_speaking = False
        if self.turn_start_time:
            duration = (datetime.now() - self.turn_start_time).total_seconds()
            self.working_memory.add(
                key="last_speech_duration",
                value=f"{duration:.1f} seconds",
                importance=0.3,
            )

    async def on_interruption(self) -> None:
        """Called when the user interrupts the agent."""
        self.was_interrupted = True
        self.is_speaking = False
        self.working_memory.add(
            key="interruption_noted",
            value="User interrupted - adapting response",
            importance=0.7,
        )

    async def process_event(self, event: Any) -> Any:
        """Process voice events with additional handling."""
        event = await super().process_event(event)

        # Track turn completion
        if hasattr(event, 'turn_complete') and event.turn_complete:
            await self.on_speech_end()

        # Track interruptions
        if hasattr(event, 'interrupted') and event.interrupted:
            await self.on_interruption()

        return event

    def get_voice_stats(self) -> Dict[str, Any]:
        """Get voice-specific statistics."""
        base_stats = self.get_stats()
        base_stats.update({
            "personality": self.voice_config.personality.value,
            "use_native_audio": self.voice_config.use_native_audio,
            "is_speaking": self.is_speaking,
            "was_interrupted": self.was_interrupted,
        })
        return base_stats


class InteractiveVoiceAgent(VoiceAgent):
    """
    Voice agent with interactive features.

    Adds proactive behavior and affective dialog capabilities
    for more engaging voice interactions.
    """

    def __init__(
        self,
        name: str,
        instruction: str,
        enable_proactivity: bool = True,
        enable_affective_dialog: bool = True,
        **kwargs,
    ):
        """
        Initialize an interactive voice agent.

        Args:
            name: Agent name
            instruction: Base instruction
            enable_proactivity: Enable proactive agent behavior
            enable_affective_dialog: Enable emotion-aware responses
            **kwargs: Additional arguments
        """
        self.enable_proactivity = enable_proactivity
        self.enable_affective_dialog = enable_affective_dialog

        super().__init__(
            name=name,
            instruction=instruction,
            **kwargs,
        )

        # Track user engagement
        self.silence_count = 0
        self.engagement_level = 0.5

    def _build_voice_instruction(self, base_instruction: str) -> str:
        """Build instruction with interactive features."""
        instruction = super()._build_voice_instruction(base_instruction)

        if self.enable_proactivity:
            instruction += """

**Proactive Behavior:**
- If the conversation pauses, you may offer helpful suggestions
- Anticipate user needs and provide relevant information
- Ask clarifying questions when appropriate
"""

        if self.enable_affective_dialog:
            instruction += """

**Emotional Intelligence:**
- Pay attention to the user's emotional state
- Respond with appropriate empathy and understanding
- Adjust your energy level to match or complement the user
- Offer support or encouragement when needed
"""

        return instruction

    async def on_silence_detected(self) -> None:
        """Called when extended silence is detected."""
        self.silence_count += 1

        if self.enable_proactivity and self.silence_count >= 2:
            self.working_memory.add(
                key="silence_noticed",
                value="Extended silence - may want to prompt user",
                importance=0.6,
            )

    def update_engagement(self, level: float) -> None:
        """Update user engagement tracking."""
        self.engagement_level = max(0.0, min(1.0, level))
        self.working_memory.add(
            key="engagement_level",
            value=f"{self.engagement_level:.2f}",
            importance=0.4,
        )


class MultilingualVoiceAgent(VoiceAgent):
    """
    Voice agent with multilingual support.

    Automatically detects and responds in the user's language.
    """

    SUPPORTED_LANGUAGES = [
        "en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko",
        "ar", "hi", "ru", "nl", "pl", "tr", "vi", "th", "id",
    ]

    def __init__(
        self,
        name: str,
        instruction: str,
        primary_language: str = "en",
        supported_languages: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Initialize a multilingual voice agent.

        Args:
            name: Agent name
            instruction: Base instruction
            primary_language: Default language code
            supported_languages: List of supported language codes
            **kwargs: Additional arguments
        """
        self.primary_language = primary_language
        self.supported_languages = supported_languages or self.SUPPORTED_LANGUAGES
        self.detected_language = primary_language

        super().__init__(
            name=name,
            instruction=instruction,
            **kwargs,
        )

    def _build_voice_instruction(self, base_instruction: str) -> str:
        """Build instruction with multilingual support."""
        instruction = super()._build_voice_instruction(base_instruction)

        languages = ", ".join(self.supported_languages[:5])
        instruction += f"""

**Multilingual Support:**
- You can understand and respond in multiple languages: {languages}, and more
- Detect the user's language and respond in the same language
- If asked to switch languages, do so smoothly
- Maintain the same personality across languages
"""

        return instruction

    async def detect_language(self, text: str) -> str:
        """Detect language from text (basic implementation)."""
        # This is a placeholder - in production, use a proper detection library
        self.detected_language = self.primary_language
        return self.detected_language

    async def process_input(self, user_input: str) -> None:
        """Process input with language detection."""
        await super().process_input(user_input)
        await self.detect_language(user_input)
        self.working_memory.add(
            key="detected_language",
            value=self.detected_language,
            importance=0.5,
        )
