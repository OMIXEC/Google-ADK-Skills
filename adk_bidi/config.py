"""
Configuration management for the ADK Bidi orchestrator.

Supports YAML configuration files and environment variable interpolation.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from enum import Enum
import os
import re
import yaml


class OrchestratorMode(str, Enum):
    """Operating modes for the orchestrator."""
    TEXT = "text"
    VOICE = "voice"
    MULTIMODAL = "multimodal"
    AUTONOMOUS = "autonomous"


class ConflictStrategy(str, Enum):
    """Memory conflict resolution strategies."""
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE = "merge"
    REJECT = "reject"


class VoicePersonalityType(str, Enum):
    """Voice personality types."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CASUAL = "casual"
    FORMAL = "formal"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"


class DelegationStrategy(str, Enum):
    """Multi-agent delegation strategies."""
    SINGLE = "single"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    CONSENSUS = "consensus"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30

    def __post_init__(self):
        # Resolve environment variables in args and env
        self.args = [_resolve_env_var(arg) for arg in self.args]
        self.env = {k: _resolve_env_var(v) for k, v in self.env.items()}


@dataclass
class AgentConfig:
    """Configuration for a specialist agent."""
    name: str
    instruction: str
    model: str = "gemini-2.5-flash"
    description: str = ""
    tools: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.description:
            self.description = f"Agent: {self.name}"


@dataclass
class MemoryConfig:
    """Memory system configuration."""
    working_memory_size: int = 20
    enable_shared_memory: bool = True
    enable_persistent_memory: bool = False
    pinecone_index: Optional[str] = None
    conflict_strategy: ConflictStrategy = ConflictStrategy.LAST_WRITE_WINS
    recency_weight: float = 0.4
    importance_weight: float = 0.4
    access_weight: float = 0.2

    def __post_init__(self):
        if isinstance(self.conflict_strategy, str):
            self.conflict_strategy = ConflictStrategy(self.conflict_strategy)
        if self.pinecone_index:
            self.pinecone_index = _resolve_env_var(self.pinecone_index)


@dataclass
class VoiceConfig:
    """Voice configuration for voice/multimodal modes."""
    personality: VoicePersonalityType = VoicePersonalityType.FRIENDLY
    speaking_rate: str = "normal"
    enable_emotions: bool = True
    enable_interruption: bool = True
    silence_threshold_ms: int = 500
    use_native_audio: bool = True

    def __post_init__(self):
        if isinstance(self.personality, str):
            self.personality = VoicePersonalityType(self.personality)


@dataclass
class VisionConfig:
    """Vision configuration for multimodal mode."""
    enable_image: bool = True
    enable_video: bool = False
    image_detail: str = "auto"  # auto, low, high
    video_frame_rate: int = 1
    max_image_size: int = 4096


@dataclass
class SupervisorConfig:
    """Multi-agent supervisor configuration."""
    delegation_strategy: DelegationStrategy = DelegationStrategy.SINGLE
    max_delegation_depth: int = 3
    enable_parallel_execution: bool = True
    consensus_threshold: float = 0.7

    def __post_init__(self):
        if isinstance(self.delegation_strategy, str):
            self.delegation_strategy = DelegationStrategy(self.delegation_strategy)


@dataclass
class AutonomousConfig:
    """Autonomous mode configuration."""
    goal: Optional[str] = None
    enable_proactivity: bool = True
    max_reasoning_steps: int = 50
    max_thoughts: int = 100
    reasoning_loop: str = "ooda"  # ooda, react, custom
    enable_long_term_memory: bool = True


@dataclass
class ServerConfig:
    """WebSocket/API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    enable_cors: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    max_connections: int = 100


@dataclass
class OrchestratorConfig:
    """
    Main orchestrator configuration.

    Combines all subsystem configurations into a unified config
    that can be loaded from YAML or constructed programmatically.

    Example YAML:
    ```yaml
    name: my_orchestrator
    mode: multimodal
    model: gemini-live-2.5-flash-native-audio

    agents:
      - name: researcher
        instruction: "Research specialist"
        tools: [brave_search]

    mcp_servers:
      - name: sqlite
        command: uvx
        args: [mcp-server-sqlite, --db-path, data.db]

    memory:
      working_memory_size: 30
      enable_persistent_memory: true

    voice:
      personality: professional
    ```
    """

    # Core settings
    name: str = "adk_orchestrator"
    mode: OrchestratorMode = OrchestratorMode.TEXT
    model: str = "gemini-live-2.5-flash-native-audio"

    # Agent configuration
    agents: List[AgentConfig] = field(default_factory=list)

    # MCP servers
    mcp_servers: List[MCPServerConfig] = field(default_factory=list)

    # Subsystem configurations
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    supervisor: SupervisorConfig = field(default_factory=SupervisorConfig)
    autonomous: AutonomousConfig = field(default_factory=AutonomousConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

    # Session settings
    continuous_session: bool = False
    session_timeout_seconds: int = 3600
    enable_session_resumption: bool = True

    # API keys (loaded from environment if not set)
    google_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None
    pinecone_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None

    def __post_init__(self):
        """Load API keys from environment and validate configuration."""
        # Convert string mode to enum
        if isinstance(self.mode, str):
            self.mode = OrchestratorMode(self.mode)

        # Load API keys from environment if not set
        self.google_api_key = self.google_api_key or os.getenv("GOOGLE_API_KEY")
        self.pinecone_api_key = self.pinecone_api_key or os.getenv("PINECONE_API_KEY")

        # Set autonomous goal if in autonomous mode
        if self.mode == OrchestratorMode.AUTONOMOUS and not self.autonomous.goal:
            self.autonomous.goal = "Help users accomplish their tasks"

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        if not self.google_api_key:
            issues.append("GOOGLE_API_KEY not set")

        if self.memory.enable_persistent_memory and not self.pinecone_api_key:
            issues.append("Persistent memory enabled but PINECONE_API_KEY not set")

        if self.mode in [OrchestratorMode.VOICE, OrchestratorMode.MULTIMODAL]:
            if "native-audio" not in self.model and "live" not in self.model:
                issues.append(f"Voice/multimodal mode requires streaming model, got: {self.model}")

        return issues


def _resolve_env_var(value: str) -> str:
    """
    Resolve ${VAR} patterns to environment variables.

    Examples:
        "${GOOGLE_API_KEY}" -> actual API key value
        "data/${USER}/db" -> "data/alice/db"
    """
    if not isinstance(value, str):
        return value

    pattern = r'\$\{([^}]+)\}'

    def replacer(match):
        var_name = match.group(1)
        return os.getenv(var_name, match.group(0))

    return re.sub(pattern, replacer, value)


def load_config(path: Path) -> OrchestratorConfig:
    """
    Load configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file

    Returns:
        OrchestratorConfig instance

    Example:
        config = load_config(Path("root_agent.yaml"))
    """
    with open(path) as f:
        data = yaml.safe_load(f) or {}

    return _parse_config_dict(data)


def load_config_from_string(yaml_content: str) -> OrchestratorConfig:
    """
    Load configuration from a YAML string.

    Args:
        yaml_content: YAML configuration as string

    Returns:
        OrchestratorConfig instance
    """
    data = yaml.safe_load(yaml_content) or {}
    return _parse_config_dict(data)


def _parse_config_dict(data: Dict[str, Any]) -> OrchestratorConfig:
    """Parse configuration dictionary into OrchestratorConfig."""
    # Parse nested configurations
    if "memory" in data and isinstance(data["memory"], dict):
        data["memory"] = MemoryConfig(**data["memory"])

    if "voice" in data and isinstance(data["voice"], dict):
        data["voice"] = VoiceConfig(**data["voice"])

    if "vision" in data and isinstance(data["vision"], dict):
        data["vision"] = VisionConfig(**data["vision"])

    if "supervisor" in data and isinstance(data["supervisor"], dict):
        data["supervisor"] = SupervisorConfig(**data["supervisor"])

    if "autonomous" in data and isinstance(data["autonomous"], dict):
        data["autonomous"] = AutonomousConfig(**data["autonomous"])

    if "server" in data and isinstance(data["server"], dict):
        data["server"] = ServerConfig(**data["server"])

    if "agents" in data:
        data["agents"] = [
            AgentConfig(**a) if isinstance(a, dict) else a
            for a in data["agents"]
        ]

    if "mcp_servers" in data:
        data["mcp_servers"] = [
            MCPServerConfig(**s) if isinstance(s, dict) else s
            for s in data["mcp_servers"]
        ]

    return OrchestratorConfig(**data)


def save_config(config: OrchestratorConfig, path: Path) -> None:
    """
    Save configuration to a YAML file.

    Args:
        config: OrchestratorConfig instance
        path: Path to save the YAML file
    """
    data = _config_to_dict(config)

    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def _config_to_dict(config: OrchestratorConfig) -> Dict[str, Any]:
    """Convert OrchestratorConfig to dictionary for YAML serialization."""
    import dataclasses

    def convert(obj):
        if dataclasses.is_dataclass(obj):
            result = {}
            for f in dataclasses.fields(obj):
                value = getattr(obj, f.name)
                if value != f.default and value != (f.default_factory() if f.default_factory is not dataclasses.MISSING else None):
                    result[f.name] = convert(value)
            return result
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, list):
            return [convert(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        else:
            return obj

    return convert(config)


# Default configuration presets
def get_voice_preset() -> OrchestratorConfig:
    """Get preset configuration for voice-only mode."""
    return OrchestratorConfig(
        name="voice_assistant",
        mode=OrchestratorMode.VOICE,
        model="gemini-live-2.5-flash-native-audio",
        voice=VoiceConfig(
            personality=VoicePersonalityType.FRIENDLY,
            enable_emotions=True,
            enable_interruption=True,
        ),
        continuous_session=True,
    )


def get_multimodal_preset() -> OrchestratorConfig:
    """Get preset configuration for multimodal mode."""
    return OrchestratorConfig(
        name="multimodal_assistant",
        mode=OrchestratorMode.MULTIMODAL,
        model="gemini-live-2.5-flash-native-audio",
        voice=VoiceConfig(
            personality=VoicePersonalityType.PROFESSIONAL,
            enable_emotions=True,
        ),
        vision=VisionConfig(
            enable_image=True,
            enable_video=True,
            image_detail="high",
        ),
        continuous_session=True,
    )


def get_autonomous_preset(goal: str) -> OrchestratorConfig:
    """Get preset configuration for autonomous mode."""
    return OrchestratorConfig(
        name="autonomous_agent",
        mode=OrchestratorMode.AUTONOMOUS,
        model="gemini-2.5-flash",
        autonomous=AutonomousConfig(
            goal=goal,
            enable_proactivity=True,
            max_reasoning_steps=50,
            enable_long_term_memory=True,
        ),
        memory=MemoryConfig(
            enable_persistent_memory=True,
            working_memory_size=30,
        ),
    )


def get_enterprise_preset() -> OrchestratorConfig:
    """Get preset configuration for enterprise multi-agent deployment."""
    return OrchestratorConfig(
        name="enterprise_orchestrator",
        mode=OrchestratorMode.MULTIMODAL,
        model="gemini-live-2.5-flash-native-audio",
        agents=[
            AgentConfig(
                name="researcher",
                instruction="You are a research specialist. Search for information and verify facts.",
                model="gemini-2.5-flash",
                description="Research and information gathering",
            ),
            AgentConfig(
                name="analyst",
                instruction="You analyze data and extract actionable insights.",
                model="gemini-2.5-pro",
                description="Data analysis and insights",
            ),
            AgentConfig(
                name="writer",
                instruction="You create clear, well-structured content and reports.",
                model="gemini-2.5-flash",
                description="Content creation and documentation",
            ),
        ],
        supervisor=SupervisorConfig(
            delegation_strategy=DelegationStrategy.SINGLE,
            max_delegation_depth=3,
        ),
        memory=MemoryConfig(
            enable_shared_memory=True,
            enable_persistent_memory=True,
            working_memory_size=30,
        ),
        voice=VoiceConfig(
            personality=VoicePersonalityType.PROFESSIONAL,
        ),
    )
