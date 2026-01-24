"""
BidiAgent - Base agent with bidirectional streaming and memory.

Provides the foundation for all bidirectional streaming agents
with integrated working memory and shared memory support.
"""

from typing import Optional, List, Any, Dict
from dataclasses import dataclass, field
from datetime import datetime

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from adk_bidi.memory.working_memory import WorkingMemory
from adk_bidi.memory.shared_memory import SharedMemory


@dataclass
class AgentContext:
    """Runtime context for the agent."""
    session_id: str = ""
    user_id: str = ""
    turn_count: int = 0
    last_input: str = ""
    last_output: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class BidiAgent:
    """
    Base agent with bidirectional streaming and memory.

    Provides the foundation for building real-time agents with:
    - Working memory for short-term context
    - Shared memory for multi-agent coordination
    - Event processing hooks for streaming
    - Memory injection into agent context

    Example:
        agent = BidiAgent(
            name="assistant",
            instruction="You are a helpful assistant.",
            model="gemini-2.0-flash-live-001"
        )
        await agent.initialize()
        agent.working_memory.add("user_name", "Alice", importance=0.8)
    """

    # Default models for bidirectional streaming
    DEFAULT_MODEL = "gemini-2.0-flash-live-001"
    NATIVE_AUDIO_MODEL = "gemini-live-2.5-flash-native-audio"

    def __init__(
        self,
        name: str,
        instruction: str,
        model: Optional[str] = None,
        description: str = "",
        tools: Optional[List[Any]] = None,
        working_memory: Optional[WorkingMemory] = None,
        shared_memory: Optional[SharedMemory] = None,
        memory_context_size: int = 5,
        include_memory_in_prompt: bool = True,
    ):
        """
        Initialize a bidirectional streaming agent.

        Args:
            name: Agent name (identifier)
            instruction: Agent instruction/system prompt
            model: LLM model to use (default: gemini-2.0-flash-live-001)
            description: Agent description for multi-agent systems
            tools: List of tools/functions available to the agent
            working_memory: Working memory instance (created if not provided)
            shared_memory: Shared memory for multi-agent coordination
            memory_context_size: Number of memory entries to include in context
            include_memory_in_prompt: Whether to inject memory into prompts
        """
        self.name = name
        self.description = description or f"Agent: {name}"
        self.base_instruction = instruction
        self.model = model or self.DEFAULT_MODEL
        self.memory_context_size = memory_context_size
        self.include_memory_in_prompt = include_memory_in_prompt

        # Memory systems
        self.working_memory = working_memory or WorkingMemory()
        self.shared_memory = shared_memory

        # Runtime context
        self.context = AgentContext()

        # Build tools list with memory tools
        self.tools = list(tools or [])
        self._add_memory_tools()

        # Create the underlying ADK agent
        self.agent = self._create_agent()

    def _add_memory_tools(self) -> None:
        """Add memory management tools to the agent."""
        self.tools.extend([
            FunctionTool(self.remember),
            FunctionTool(self.recall_context),
        ])

        if self.shared_memory:
            self.tools.extend([
                FunctionTool(self.share_information),
                FunctionTool(self.get_shared_information),
            ])

    def _create_agent(self) -> Agent:
        """Create the underlying ADK agent."""
        return Agent(
            name=self.name,
            model=self.model,
            description=self.description,
            instruction=self._build_instruction(),
            tools=self.tools,
        )

    def _build_instruction(self) -> str:
        """Build the full instruction with memory context."""
        instruction = self.base_instruction

        if self.include_memory_in_prompt:
            memory_context = self.get_memory_context()
            if memory_context:
                instruction = f"{instruction}\n\n{memory_context}"

        return instruction

    def get_memory_context(self) -> str:
        """
        Get working memory context for injection into prompts.

        Returns:
            Formatted memory context string
        """
        return self.working_memory.get_context_string(self.memory_context_size)

    # Memory tools (available to the agent)

    def remember(self, key: str, value: str, importance: str = "medium") -> str:
        """
        Store information in working memory.

        Args:
            key: A short identifier for this information
            value: The information to remember
            importance: Importance level (low, medium, high)

        Returns:
            Confirmation message
        """
        importance_scores = {"low": 0.3, "medium": 0.5, "high": 0.8}
        score = importance_scores.get(importance, 0.5)

        self.working_memory.add(
            key=key,
            value=value,
            importance=score,
            source_agent=self.name,
        )

        return f"Remembered: {key}"

    def recall_context(self, count: int = 5) -> str:
        """
        Recall recent context from working memory.

        Args:
            count: Number of items to recall

        Returns:
            Formatted context string
        """
        return self.working_memory.get_context_string(count)

    async def share_information(self, key: str, value: str) -> str:
        """
        Share information with other agents via shared memory.

        Args:
            key: The key to share under
            value: The information to share

        Returns:
            Confirmation message
        """
        if not self.shared_memory:
            return "Shared memory not available"

        success = await self.shared_memory.write(key, value, self.name)
        if success:
            return f"Shared '{key}' with other agents"
        return f"Failed to share '{key}'"

    async def get_shared_information(self, key: str) -> str:
        """
        Get information shared by other agents.

        Args:
            key: The key to retrieve

        Returns:
            The shared information or not found message
        """
        if not self.shared_memory:
            return "Shared memory not available"

        value = await self.shared_memory.read(key, self.name)
        if value is not None:
            return str(value)
        return f"No shared information found for '{key}'"

    # Event processing

    async def process_event(self, event: Any) -> Any:
        """
        Process a streaming event and update memory.

        Called for each event received from the Live API.
        Override in subclasses for custom processing.

        Args:
            event: The streaming event

        Returns:
            The processed event
        """
        # Update context
        self.context.turn_count += 1

        # Extract text from event for memory
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts') and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        self.context.last_output = part.text

                        # Store significant outputs in memory
                        if len(part.text) > 50:  # Only store substantial responses
                            self.working_memory.add(
                                key=f"response_{self.context.turn_count}",
                                value=part.text[:200],
                                importance=0.6,
                                source_agent=self.name,
                            )

        return event

    async def process_input(self, user_input: str) -> None:
        """
        Process user input before sending to agent.

        Args:
            user_input: The user's input text
        """
        self.context.last_input = user_input
        self.working_memory.add(
            key=f"user_input_{self.context.turn_count}",
            value=user_input[:200],
            importance=0.5,
            source_agent="user",
        )

    # Lifecycle methods

    async def initialize(self) -> None:
        """Initialize the agent (called before first use)."""
        pass

    async def cleanup(self) -> None:
        """Cleanup resources (called when done)."""
        pass

    def refresh_instruction(self) -> None:
        """Refresh the agent instruction with current memory context."""
        self.agent = self._create_agent()

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "name": self.name,
            "model": self.model,
            "turn_count": self.context.turn_count,
            "working_memory_size": len(self.working_memory),
            "tools_count": len(self.tools),
        }

    @property
    def adk_agent(self) -> Agent:
        """Get the underlying ADK agent."""
        return self.agent


class TextBidiAgent(BidiAgent):
    """
    Text-only bidirectional agent.

    Optimized for text-based streaming without audio/video.
    """

    def __init__(self, name: str, instruction: str, **kwargs):
        super().__init__(
            name=name,
            instruction=instruction,
            model="gemini-2.0-flash-live-001",
            **kwargs,
        )


class ConversationalAgent(BidiAgent):
    """
    Conversational agent with enhanced context tracking.

    Maintains conversation history and provides better
    context management for multi-turn dialogues.
    """

    def __init__(
        self,
        name: str,
        instruction: str,
        max_history: int = 10,
        **kwargs,
    ):
        super().__init__(
            name=name,
            instruction=instruction,
            **kwargs,
        )
        self.max_history = max_history
        self.conversation_history: List[Dict[str, str]] = []

    async def process_input(self, user_input: str) -> None:
        """Track conversation history."""
        await super().process_input(user_input)

        self.conversation_history.append({
            "role": "user",
            "content": user_input,
        })

        # Trim history
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

    async def process_event(self, event: Any) -> Any:
        """Track assistant responses in history."""
        event = await super().process_event(event)

        if self.context.last_output:
            self.conversation_history.append({
                "role": "assistant",
                "content": self.context.last_output,
            })

        return event

    def get_conversation_summary(self, turns: int = 5) -> str:
        """Get a summary of recent conversation."""
        recent = self.conversation_history[-turns * 2:]
        lines = []
        for entry in recent:
            role = entry["role"].capitalize()
            content = entry["content"][:100]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
