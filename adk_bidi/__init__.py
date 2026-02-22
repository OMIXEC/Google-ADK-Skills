"""
ADK Bidi - Multi-Agent Real-Time Platform

Production-ready bidirectional streaming with multi-agent memory,
real-time coordination, and autonomous experience.

Quick Start:
    # Interactive session
    python -m adk_bidi

    # Voice mode
    python -m adk_bidi --mode voice

    # With configuration
    python -m adk_bidi --config root_agent.yaml

Programmatic Usage:
    from adk_bidi import UnifiedOrchestrator, OrchestratorConfig

    config = OrchestratorConfig(mode="multimodal")
    orchestrator = UnifiedOrchestrator(config)
    await orchestrator.initialize()
    await orchestrator.run_interactive()
"""

# Core streaming
from adk_bidi.core.live_session import LiveSession
from adk_bidi.core.streaming_config import StreamingPresets

# Memory systems
from adk_bidi.memory.working_memory import WorkingMemory
from adk_bidi.memory.shared_memory import SharedMemory
from adk_bidi.memory.persistent_store import PersistentMemoryStore

# Agent types
from adk_bidi.agents.bidi_agent import BidiAgent
from adk_bidi.agents.voice_agent import VoiceAgent
from adk_bidi.agents.multimodal_agent import MultimodalAgent
from adk_bidi.agents.autonomous_agent import AutonomousAgent

# Orchestration
from adk_bidi.orchestration.supervisor import MultiAgentSupervisor
from adk_bidi.orchestration.router import IntentRouter
from adk_bidi.orchestration.swarm import AgentSwarm

# Configuration
from adk_bidi.config import (
    OrchestratorConfig,
    OrchestratorMode,
    AgentConfig,
    MCPServerConfig,
    MemoryConfig,
    VoiceConfig,
    VisionConfig,
    load_config,
    save_config,
    get_voice_preset,
    get_multimodal_preset,
    get_autonomous_preset,
    get_enterprise_preset,
)

# Unified orchestrator
from adk_bidi.agent import UnifiedOrchestrator, create_orchestrator, get_root_agent

__all__ = [
    # Core
    "LiveSession",
    "StreamingPresets",
    # Memory
    "WorkingMemory",
    "SharedMemory",
    "PersistentMemoryStore",
    # Agents
    "BidiAgent",
    "VoiceAgent",
    "MultimodalAgent",
    "AutonomousAgent",
    # Orchestration
    "MultiAgentSupervisor",
    "IntentRouter",
    "AgentSwarm",
    # Configuration
    "OrchestratorConfig",
    "OrchestratorMode",
    "AgentConfig",
    "MCPServerConfig",
    "MemoryConfig",
    "VoiceConfig",
    "VisionConfig",
    "load_config",
    "save_config",
    "get_voice_preset",
    "get_multimodal_preset",
    "get_autonomous_preset",
    "get_enterprise_preset",
    # Unified Orchestrator
    "UnifiedOrchestrator",
    "create_orchestrator",
    "get_root_agent",
]

__version__ = "1.0.0"
