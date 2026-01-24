"""
MultimodalAgent - Agent supporting text, audio, and video input.

Provides agents that can process and respond to multiple
modalities simultaneously in real-time.
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


class Modality(Enum):
    """Supported input/output modalities."""
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"


@dataclass
class MultimodalConfig:
    """Configuration for multimodal agent."""
    enable_text: bool = True
    enable_audio: bool = True
    enable_image: bool = True
    enable_video: bool = False  # Video is just sequential images
    response_modalities: List[str] = field(default_factory=lambda: ["TEXT", "AUDIO"])
    image_analysis_detail: str = "auto"  # auto, low, high
    video_frame_rate: int = 1  # Frames per second to process


@dataclass
class ModalityContext:
    """Context for tracking modality-specific information."""
    last_text: str = ""
    last_audio_duration: float = 0.0
    last_image_description: str = ""
    image_count: int = 0
    audio_chunks_received: int = 0
    current_modalities: List[Modality] = field(default_factory=list)


class MultimodalAgent(BidiAgent):
    """
    Agent supporting text, audio, and video input.

    Processes multiple input types and provides appropriate
    responses based on the content type.

    Example:
        agent = MultimodalAgent(
            name="multimodal_assistant",
            instruction="You can see, hear, and read.",
        )
        # Send text
        await agent.process_text("What do you see?")
        # Send image
        await agent.process_image(image_bytes)
        # Send audio
        await agent.process_audio(audio_bytes)
    """

    def __init__(
        self,
        name: str,
        instruction: str,
        multimodal_config: Optional[MultimodalConfig] = None,
        tools: Optional[List[Any]] = None,
        working_memory: Optional[WorkingMemory] = None,
        shared_memory: Optional[SharedMemory] = None,
        **kwargs,
    ):
        """
        Initialize a multimodal agent.

        Args:
            name: Agent name
            instruction: Base instruction
            multimodal_config: Multimodal configuration
            tools: Available tools
            working_memory: Working memory instance
            shared_memory: Shared memory instance
            **kwargs: Additional arguments
        """
        self.multimodal_config = multimodal_config or MultimodalConfig()
        self.modality_context = ModalityContext()

        # Build enhanced instruction
        enhanced_instruction = self._build_multimodal_instruction(instruction)

        super().__init__(
            name=name,
            instruction=enhanced_instruction,
            model="gemini-2.0-flash-live-001",
            tools=tools,
            working_memory=working_memory,
            shared_memory=shared_memory,
            **kwargs,
        )

        # Add multimodal tools
        self._add_multimodal_tools()

    def _build_multimodal_instruction(self, base_instruction: str) -> str:
        """Build instruction with multimodal guidance."""
        modalities = []
        if self.multimodal_config.enable_text:
            modalities.append("text")
        if self.multimodal_config.enable_audio:
            modalities.append("audio/voice")
        if self.multimodal_config.enable_image or self.multimodal_config.enable_video:
            modalities.append("images/video")

        modality_list = ", ".join(modalities)

        instruction = f"""
{base_instruction}

**Multimodal Capabilities:**
You can receive and process: {modality_list}

**Input Handling:**
- When you receive text, respond conversationally
- When you receive audio, listen and respond appropriately
- When you receive images, describe and analyze what you see
- Combine information from multiple modalities when relevant

**Response Guidelines:**
- Reference specific visual elements when discussing images
- Acknowledge audio cues and respond to verbal context
- Integrate information across modalities for comprehensive responses
- Be specific about what you observe in each modality
"""

        if self.multimodal_config.enable_video:
            instruction += """
**Video Processing:**
- Track changes across video frames
- Describe motion and temporal events
- Note transitions and significant moments
"""

        return instruction

    def _add_multimodal_tools(self) -> None:
        """Add multimodal-specific tools."""
        self.tools.extend([
            FunctionTool(self.describe_last_image),
            FunctionTool(self.get_modality_summary),
        ])

    # Multimodal processing methods

    async def process_text(self, text: str) -> None:
        """Process text input."""
        self.modality_context.last_text = text
        if Modality.TEXT not in self.modality_context.current_modalities:
            self.modality_context.current_modalities.append(Modality.TEXT)

        await self.process_input(text)

    async def process_audio(self, audio_data: bytes, duration: float = 0.0) -> None:
        """
        Process audio input.

        Args:
            audio_data: Audio bytes (PCM)
            duration: Duration in seconds
        """
        self.modality_context.audio_chunks_received += 1
        self.modality_context.last_audio_duration = duration

        if Modality.AUDIO not in self.modality_context.current_modalities:
            self.modality_context.current_modalities.append(Modality.AUDIO)

        self.working_memory.add(
            key="audio_received",
            value=f"Audio chunk #{self.modality_context.audio_chunks_received}",
            importance=0.4,
        )

    async def process_image(
        self,
        image_data: bytes,
        description: Optional[str] = None,
    ) -> None:
        """
        Process image input.

        Args:
            image_data: Image bytes
            description: Optional description of the image context
        """
        self.modality_context.image_count += 1

        if Modality.IMAGE not in self.modality_context.current_modalities:
            self.modality_context.current_modalities.append(Modality.IMAGE)

        context_desc = description or f"Image #{self.modality_context.image_count}"
        self.modality_context.last_image_description = context_desc

        self.working_memory.add(
            key=f"image_{self.modality_context.image_count}",
            value=context_desc,
            importance=0.6,
        )

    async def process_video_frame(
        self,
        frame_data: bytes,
        frame_number: int,
        timestamp: float,
    ) -> None:
        """
        Process a video frame.

        Args:
            frame_data: Frame bytes
            frame_number: Frame sequence number
            timestamp: Frame timestamp in seconds
        """
        if Modality.VIDEO not in self.modality_context.current_modalities:
            self.modality_context.current_modalities.append(Modality.VIDEO)

        # Process as image with timestamp context
        await self.process_image(
            frame_data,
            description=f"Video frame {frame_number} at {timestamp:.1f}s",
        )

    # Tool methods

    def describe_last_image(self) -> str:
        """
        Get description of the last received image.

        Returns:
            Description of the last image
        """
        if not self.modality_context.last_image_description:
            return "No images have been received yet."
        return f"Last image: {self.modality_context.last_image_description}"

    def get_modality_summary(self) -> str:
        """
        Get summary of received modalities.

        Returns:
            Summary of current modality context
        """
        active = [m.value for m in self.modality_context.current_modalities]
        if not active:
            return "No modalities have been received yet."

        summary = f"Active modalities: {', '.join(active)}\n"
        summary += f"Images received: {self.modality_context.image_count}\n"
        summary += f"Audio chunks: {self.modality_context.audio_chunks_received}"

        return summary

    async def process_event(self, event: Any) -> Any:
        """Process streaming events with modality tracking."""
        event = await super().process_event(event)

        # Track content modalities from events
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts') and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        mime_type = part.inline_data.mime_type
                        if mime_type.startswith('audio/'):
                            if Modality.AUDIO not in self.modality_context.current_modalities:
                                self.modality_context.current_modalities.append(Modality.AUDIO)
                        elif mime_type.startswith('image/'):
                            if Modality.IMAGE not in self.modality_context.current_modalities:
                                self.modality_context.current_modalities.append(Modality.IMAGE)

        return event

    def reset_modality_context(self) -> None:
        """Reset the modality context for a new conversation."""
        self.modality_context = ModalityContext()

    def get_multimodal_stats(self) -> Dict[str, Any]:
        """Get multimodal-specific statistics."""
        base_stats = self.get_stats()
        base_stats.update({
            "active_modalities": [m.value for m in self.modality_context.current_modalities],
            "images_received": self.modality_context.image_count,
            "audio_chunks": self.modality_context.audio_chunks_received,
            "config": {
                "text_enabled": self.multimodal_config.enable_text,
                "audio_enabled": self.multimodal_config.enable_audio,
                "image_enabled": self.multimodal_config.enable_image,
                "video_enabled": self.multimodal_config.enable_video,
            },
        })
        return base_stats


class VisionAgent(MultimodalAgent):
    """
    Vision-focused multimodal agent.

    Optimized for image and video analysis with
    specialized vision capabilities.
    """

    def __init__(
        self,
        name: str,
        instruction: str,
        detail_level: str = "high",
        **kwargs,
    ):
        """
        Initialize a vision agent.

        Args:
            name: Agent name
            instruction: Base instruction
            detail_level: Image analysis detail (low, auto, high)
            **kwargs: Additional arguments
        """
        config = MultimodalConfig(
            enable_image=True,
            enable_video=True,
            image_analysis_detail=detail_level,
        )

        vision_instruction = f"""
{instruction}

**Vision Specialist:**
- Provide detailed visual analysis
- Identify objects, text, people, and scenes
- Describe spatial relationships
- Note colors, textures, and visual details
- Track motion and changes in video
"""

        super().__init__(
            name=name,
            instruction=vision_instruction,
            multimodal_config=config,
            **kwargs,
        )


class AccessibilityAgent(MultimodalAgent):
    """
    Accessibility-focused multimodal agent.

    Provides detailed descriptions for users who may have
    visual or auditory impairments.
    """

    def __init__(
        self,
        name: str,
        instruction: str,
        **kwargs,
    ):
        """
        Initialize an accessibility agent.

        Args:
            name: Agent name
            instruction: Base instruction
            **kwargs: Additional arguments
        """
        accessibility_instruction = f"""
{instruction}

**Accessibility Guidelines:**
- Provide comprehensive descriptions of visual content
- Describe scenes in detail for users who cannot see
- Identify text in images and read it aloud
- Describe people, actions, and environments clearly
- Use spatial language (left, right, foreground, background)
- Alert to important visual information immediately
- Be patient and thorough in descriptions
"""

        super().__init__(
            name=name,
            instruction=accessibility_instruction,
            **kwargs,
        )
