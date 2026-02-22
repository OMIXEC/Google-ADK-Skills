"""
Unified Multi-Agent Orchestrator

Combines voice, vision, tools, and MCP into a single production-ready orchestrator.
This is the root_agent for the ADK Bidi platform.

Usage:
    from adk_bidi.agent import UnifiedOrchestrator
    from adk_bidi.config import OrchestratorConfig

    config = OrchestratorConfig(mode="multimodal")
    orchestrator = UnifiedOrchestrator(config)
    await orchestrator.initialize()
    await orchestrator.run_interactive()
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
import asyncio
import os

from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import Runner
from google.adk.tools import FunctionTool, AgentTool
from google.genai import types

from adk_bidi.config import (
    OrchestratorConfig,
    OrchestratorMode,
    AgentConfig,
    MCPServerConfig,
    VoicePersonalityType,
)
from adk_bidi.core.streaming_config import StreamingPresets
from adk_bidi.memory.working_memory import WorkingMemory
from adk_bidi.memory.shared_memory import SharedMemory


@dataclass
class OrchestratorState:
    """Runtime state for the orchestrator."""
    session_id: str = ""
    user_id: str = ""
    turn_count: int = 0
    active_agents: List[str] = None
    last_delegation: Optional[str] = None

    def __post_init__(self):
        if self.active_agents is None:
            self.active_agents = []


class UnifiedOrchestrator:
    """
    Production-ready unified orchestrator that combines:
    - Voice agents with native audio
    - Vision/multimodal processing
    - MCP tool integration
    - Multi-agent coordination
    - Memory systems (working, shared, persistent)
    - Autonomous reasoning (optional)

    This is the main entry point for running ADK agents in production.

    Example:
        config = OrchestratorConfig(mode="multimodal")
        orchestrator = UnifiedOrchestrator(config)
        await orchestrator.initialize()
        await orchestrator.run_interactive()
    """

    def __init__(self, config: OrchestratorConfig):
        """
        Initialize the unified orchestrator.

        Args:
            config: OrchestratorConfig with all settings
        """
        self.config = config
        self.runner: Optional[Runner] = None
        self.live_queue: Optional[LiveRequestQueue] = None

        # Memory systems
        self.working_memory = WorkingMemory(
            max_size=config.memory.working_memory_size,
            recency_weight=config.memory.recency_weight,
            importance_weight=config.memory.importance_weight,
            access_weight=config.memory.access_weight,
        )
        self.shared_memory: Optional[SharedMemory] = None
        self.persistent_memory = None

        # Agents and tools
        self.specialist_agents: Dict[str, Agent] = {}
        self.mcp_toolsets: Dict[str, Any] = {}
        self.root_agent: Optional[Agent] = None

        # State
        self.state = OrchestratorState()
        self._initialized = False
        self._running = False

    async def initialize(self) -> None:
        """Initialize all orchestrator components."""
        if self._initialized:
            return

        # Validate configuration
        issues = self.config.validate()
        if issues:
            print(f"Configuration warnings: {issues}")

        # 1. Initialize memory systems
        await self._setup_memory()

        # 2. Setup MCP toolsets
        await self._setup_mcp_servers()

        # 3. Create specialist agents
        self._create_specialist_agents()

        # 4. Create root agent based on mode
        self._create_root_agent()

        # 5. Create runner
        self.runner = Runner(
            agent=self.root_agent,
            app_name=self.config.name,
        )

        self._initialized = True

    async def _setup_memory(self) -> None:
        """Setup memory systems based on configuration."""
        # Shared memory for multi-agent coordination
        if self.config.memory.enable_shared_memory:
            self.shared_memory = SharedMemory(
                conflict_strategy=self.config.memory.conflict_strategy,
            )

        # Persistent memory (Pinecone)
        if self.config.memory.enable_persistent_memory and self.config.pinecone_api_key:
            try:
                from adk_bidi.memory.persistent_store import PersistentMemoryStore
                self.persistent_memory = PersistentMemoryStore(
                    api_key=self.config.pinecone_api_key,
                    index_host=self.config.memory.pinecone_index,
                )
            except ImportError:
                print("Warning: Persistent memory requires pinecone package")

    async def _setup_mcp_servers(self) -> None:
        """Setup MCP server connections."""
        if not self.config.mcp_servers:
            return

        try:
            from google.adk.tools.mcp_tool import McpToolset
            from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
            from mcp import StdioServerParameters
        except ImportError:
            print("Warning: MCP tools require mcp package")
            return

        for server_config in self.config.mcp_servers:
            try:
                toolset = McpToolset(
                    connection_params=StdioConnectionParams(
                        server_params=StdioServerParameters(
                            command=server_config.command,
                            args=server_config.args,
                            env=server_config.env if server_config.env else None,
                        ),
                        timeout=server_config.timeout,
                    ),
                )
                self.mcp_toolsets[server_config.name] = toolset
            except Exception as e:
                print(f"Warning: Failed to setup MCP server {server_config.name}: {e}")

    def _create_specialist_agents(self) -> None:
        """Create specialist agents from configuration."""
        for agent_config in self.config.agents:
            # Collect tools for this agent
            tools = []
            for tool_name in agent_config.tools:
                if tool_name in self.mcp_toolsets:
                    tools.append(self.mcp_toolsets[tool_name])

            agent = Agent(
                name=agent_config.name,
                model=agent_config.model,
                description=agent_config.description,
                instruction=agent_config.instruction,
                tools=tools,
            )
            self.specialist_agents[agent_config.name] = agent

    def _create_root_agent(self) -> None:
        """Create the root agent based on operating mode."""
        mode = self.config.mode

        # Collect all MCP tools
        all_tools = list(self.mcp_toolsets.values())

        # Add memory tools
        all_tools.extend(self._create_memory_tools())

        if mode == OrchestratorMode.VOICE:
            self._create_voice_root_agent(all_tools)
        elif mode == OrchestratorMode.MULTIMODAL:
            self._create_multimodal_root_agent(all_tools)
        elif mode == OrchestratorMode.AUTONOMOUS:
            self._create_autonomous_root_agent(all_tools)
        else:  # TEXT mode
            self._create_text_root_agent(all_tools)

    def _create_memory_tools(self) -> List[FunctionTool]:
        """Create memory management tools."""
        tools = []

        def remember(key: str, value: str, importance: float = 0.5) -> str:
            """Store information in working memory."""
            self.working_memory.add(key, value, importance=importance)
            return f"Remembered: {key}"

        def recall(query: str, limit: int = 5) -> str:
            """Recall information from memory."""
            entries = self.working_memory.get_relevant(query, limit=limit)
            if not entries:
                return "No relevant memories found."
            return "\n".join([f"- {e.key}: {e.value}" for e in entries])

        tools.append(FunctionTool(remember))
        tools.append(FunctionTool(recall))

        if self.shared_memory:
            async def share_info(key: str, value: str) -> str:
                """Share information with other agents."""
                await self.shared_memory.write(key, value, self.config.name)
                return f"Shared: {key}"

            async def get_shared(key: str) -> str:
                """Get shared information from other agents."""
                result = await self.shared_memory.read(key)
                return result if result else "Not found in shared memory."

            tools.append(FunctionTool(share_info))
            tools.append(FunctionTool(get_shared))

        return tools

    def _create_text_root_agent(self, tools: List) -> None:
        """Create text-based supervisor agent."""
        instruction = self._build_supervisor_instruction()

        # Add specialist agents as AgentTools
        for agent in self.specialist_agents.values():
            tools.append(AgentTool(agent=agent))

        self.root_agent = Agent(
            name=self.config.name,
            model=self.config.model,
            description="Unified orchestrator managing specialists and tools",
            instruction=instruction,
            tools=tools,
        )

    def _create_voice_root_agent(self, tools: List) -> None:
        """Create voice-enabled root agent."""
        try:
            from adk_bidi.agents.voice_agent import VoiceAgent, VoiceConfig as VAConfig
            from adk_bidi.agents.voice_agent import VoicePersonality

            # Map personality
            personality_map = {
                VoicePersonalityType.PROFESSIONAL: VoicePersonality.PROFESSIONAL,
                VoicePersonalityType.FRIENDLY: VoicePersonality.FRIENDLY,
                VoicePersonalityType.CASUAL: VoicePersonality.CASUAL,
                VoicePersonalityType.FORMAL: VoicePersonality.FORMAL,
                VoicePersonalityType.ENTHUSIASTIC: VoicePersonality.ENTHUSIASTIC,
                VoicePersonalityType.CALM: VoicePersonality.CALM,
            }

            voice_config = VAConfig(
                personality=personality_map.get(
                    self.config.voice.personality,
                    VoicePersonality.FRIENDLY
                ),
                enable_emotions=self.config.voice.enable_emotions,
                enable_interruption=self.config.voice.enable_interruption,
                use_native_audio=self.config.voice.use_native_audio,
            )

            voice_agent = VoiceAgent(
                name=self.config.name,
                instruction=self._build_supervisor_instruction(),
                voice_config=voice_config,
                working_memory=self.working_memory,
                shared_memory=self.shared_memory,
                tools=tools,
            )

            # Add specialist agents
            for agent in self.specialist_agents.values():
                voice_agent.tools.append(AgentTool(agent=agent))

            self.root_agent = voice_agent.agent

        except ImportError:
            print("Warning: VoiceAgent not available, falling back to text mode")
            self._create_text_root_agent(tools)

    def _create_multimodal_root_agent(self, tools: List) -> None:
        """Create multimodal (voice + vision) root agent."""
        try:
            from adk_bidi.agents.multimodal_agent import MultimodalAgent, MultimodalConfig

            mm_config = MultimodalConfig(
                enable_text=True,
                enable_audio=True,
                enable_image=self.config.vision.enable_image,
                enable_video=self.config.vision.enable_video,
                response_modalities=["TEXT", "AUDIO"],
                image_analysis_detail=self.config.vision.image_detail,
            )

            mm_agent = MultimodalAgent(
                name=self.config.name,
                instruction=self._build_supervisor_instruction(),
                multimodal_config=mm_config,
                working_memory=self.working_memory,
                shared_memory=self.shared_memory,
                tools=tools,
            )

            # Add specialist agents
            for agent in self.specialist_agents.values():
                mm_agent.tools.append(AgentTool(agent=agent))

            self.root_agent = mm_agent.agent

        except ImportError:
            print("Warning: MultimodalAgent not available, falling back to voice mode")
            self._create_voice_root_agent(tools)

    def _create_autonomous_root_agent(self, tools: List) -> None:
        """Create autonomous reasoning root agent."""
        try:
            from adk_bidi.agents.autonomous_agent import AutonomousAgent

            auto_agent = AutonomousAgent(
                name=self.config.name,
                goal=self.config.autonomous.goal,
                instruction=self._build_supervisor_instruction(),
                working_memory=self.working_memory,
                shared_memory=self.shared_memory,
                persistent_memory=self.persistent_memory,
                max_thoughts=self.config.autonomous.max_thoughts,
                enable_proactivity=self.config.autonomous.enable_proactivity,
                tools=tools,
            )

            # Add specialist agents
            for agent in self.specialist_agents.values():
                auto_agent.tools.append(AgentTool(agent=agent))

            self.root_agent = auto_agent.agent

        except ImportError:
            print("Warning: AutonomousAgent not available, falling back to text mode")
            self._create_text_root_agent(tools)

    def _build_supervisor_instruction(self) -> str:
        """Build instruction for supervisor/root agent."""
        agent_descriptions = []
        for name, agent in self.specialist_agents.items():
            desc = getattr(agent, 'description', f"Agent: {name}")
            agent_descriptions.append(f"- **{name}**: {desc}")

        mcp_descriptions = []
        for name in self.mcp_toolsets.keys():
            mcp_descriptions.append(f"- **{name}**: External tool server")

        mode_instructions = {
            OrchestratorMode.TEXT: "Communicate through text messages.",
            OrchestratorMode.VOICE: "Communicate through voice. Keep responses concise and conversational.",
            OrchestratorMode.MULTIMODAL: "You can see images and hear audio. Respond naturally.",
            OrchestratorMode.AUTONOMOUS: "Think step by step. Use OODA loop: Observe, Orient, Decide, Act.",
        }

        return f"""You are a unified orchestrator managing a team of specialists and tools.

**Mode:** {self.config.mode.value}
{mode_instructions.get(self.config.mode, '')}

**Specialist Agents:**
{chr(10).join(agent_descriptions) if agent_descriptions else "No specialist agents configured."}

**MCP Tool Servers:**
{chr(10).join(mcp_descriptions) if mcp_descriptions else "No MCP servers configured."}

**Your Responsibilities:**
1. Analyze user requests and delegate to appropriate specialists
2. Use MCP tools for external data and operations
3. Maintain context and coordinate multi-step tasks
4. Synthesize results from multiple sources
5. Provide clear, helpful responses

**Memory Tools:**
- Use `remember` to store important information
- Use `recall` to retrieve relevant context
- Use `share_info` to coordinate with other agents
- Use `get_shared` to access shared information

**Guidelines:**
- Route to specialists for their domain expertise
- Use tools for real-time data and external operations
- Keep track of conversation context
- Be proactive in offering assistance
"""

    async def run_interactive(self) -> None:
        """Run interactive session with the orchestrator."""
        if not self._initialized:
            await self.initialize()

        self._running = True
        self.live_queue = LiveRequestQueue()

        # Select streaming config based on mode
        if self.config.mode == OrchestratorMode.VOICE:
            run_config = StreamingPresets.native_audio()
        elif self.config.mode == OrchestratorMode.MULTIMODAL:
            run_config = StreamingPresets.text_and_audio()
        elif self.config.mode == OrchestratorMode.AUTONOMOUS:
            run_config = StreamingPresets.autonomous_proactive()
        else:
            run_config = StreamingPresets.text_only()

        print(f"\n{'='*50}")
        print(f"ADK Orchestrator: {self.config.name}")
        print(f"Mode: {self.config.mode.value}")
        print(f"Agents: {len(self.specialist_agents)}")
        print(f"MCP Servers: {len(self.mcp_toolsets)}")
        print(f"{'='*50}\n")
        print("Type 'quit' or 'exit' to end session.\n")

        async def process_events():
            """Process events from the agent."""
            try:
                async for event in self.runner.run_live(
                    user_id="interactive_user",
                    session_id="interactive_session",
                    live_request_queue=self.live_queue,
                    run_config=run_config,
                ):
                    self.state.turn_count += 1

                    # Handle response events
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts') and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    print(f"\nAssistant: {part.text}")
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    print("[Audio/Media response]")

                    # Handle tool calls
                    if hasattr(event, 'function_calls') and event.function_calls:
                        for fc in event.function_calls:
                            print(f"[Tool: {fc.name}]")

                    # Turn completion
                    if hasattr(event, 'turn_complete') and event.turn_complete:
                        print("\n> ", end="", flush=True)

            except Exception as e:
                print(f"\nEvent processing error: {e}")

        async def handle_input():
            """Handle user input."""
            while self._running:
                try:
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, "> "
                    )

                    if user_input.lower() in ['quit', 'exit', 'q']:
                        self._running = False
                        self.live_queue.close()
                        break

                    if user_input.strip():
                        # Store in memory
                        self.working_memory.add(
                            f"user_turn_{self.state.turn_count}",
                            user_input,
                            importance=0.6
                        )

                        content = types.Content(
                            parts=[types.Part(text=user_input)]
                        )
                        self.live_queue.send_content(content)

                except EOFError:
                    self._running = False
                    self.live_queue.close()
                    break

        try:
            await asyncio.gather(
                process_events(),
                handle_input(),
                return_exceptions=True,
            )
        except Exception as e:
            print(f"\nSession error: {e}")
        finally:
            print("\nSession ended.")

    async def process_message(self, message: str, user_id: str = "user") -> str:
        """
        Process a single message and return the response.

        Useful for API/programmatic usage.

        Args:
            message: User message to process
            user_id: User identifier

        Returns:
            Agent response as string
        """
        if not self._initialized:
            await self.initialize()

        # Use Runner for single-turn processing
        response = await self.runner.run(
            user_id=user_id,
            session_id=f"session_{user_id}",
            new_message=types.Content(parts=[types.Part(text=message)]),
        )

        # Extract text from response
        if response.content and response.content.parts:
            texts = [p.text for p in response.content.parts if hasattr(p, 'text') and p.text]
            return " ".join(texts)

        return ""

    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._running = False

        if self.live_queue:
            self.live_queue.close()

        # Cleanup MCP connections
        for name, toolset in self.mcp_toolsets.items():
            if hasattr(toolset, 'close'):
                try:
                    await toolset.close()
                except Exception as e:
                    print(f"Warning: Error closing MCP server {name}: {e}")

        self._initialized = False

    def get_root_agent(self) -> Agent:
        """Get the root agent for external integrations."""
        if not self.root_agent:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")
        return self.root_agent


def create_orchestrator(config: OrchestratorConfig) -> UnifiedOrchestrator:
    """Factory function to create a unified orchestrator."""
    return UnifiedOrchestrator(config)


# Convenience function for ADK web deployment
def get_root_agent(config_path: Optional[str] = None) -> Agent:
    """
    Get root agent for ADK web_deploy or other integrations.

    Args:
        config_path: Optional path to YAML configuration file

    Returns:
        Configured Agent instance
    """
    from adk_bidi.config import load_config, OrchestratorConfig
    from pathlib import Path

    if config_path:
        config = load_config(Path(config_path))
    else:
        config = OrchestratorConfig()

    orchestrator = UnifiedOrchestrator(config)
    asyncio.run(orchestrator.initialize())
    return orchestrator.get_root_agent()


# Default root_agent for simple imports
# Usage: from adk_bidi.agent import root_agent
root_agent = None  # Lazy initialization - use get_root_agent()
