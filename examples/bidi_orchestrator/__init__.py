"""
ADK Bidi - Multi-Agent Real-Time Platform

Production-ready bidirectional streaming with multi-agent memory,
real-time coordination, and autonomous experience.

Quick Start:
    # Interactive session
    python -m bidi_orchestrator

    # Voice mode
    python -m bidi_orchestrator --mode voice

    # With configuration
    python -m bidi_orchestrator --config root_agent.yaml

Programmatic Usage:
    from bidi_orchestrator import UnifiedOrchestrator, OrchestratorConfig

    config = OrchestratorConfig(mode="multimodal")
    orchestrator = UnifiedOrchestrator(config)
    await orchestrator.initialize()
    await orchestrator.run_interactive()
"""

# Core streaming
from bidi_orchestrator.core.live_session import LiveSession
from bidi_orchestrator.core.streaming_config import StreamingPresets

# Memory systems
from bidi_orchestrator.memory.working_memory import WorkingMemory
from bidi_orchestrator.memory.shared_memory import SharedMemory
from bidi_orchestrator.memory.persistent_store import PersistentMemoryStore

# Agent types
from bidi_orchestrator.agents.bidi_agent import BidiAgent
from bidi_orchestrator.agents.voice_agent import VoiceAgent
from bidi_orchestrator.agents.multimodal_agent import MultimodalAgent
from bidi_orchestrator.agents.autonomous_agent import AutonomousAgent

# Orchestration
from bidi_orchestrator.orchestration.supervisor import MultiAgentSupervisor
from bidi_orchestrator.orchestration.router import IntentRouter
from bidi_orchestrator.orchestration.swarm import AgentSwarm

# Configuration
from bidi_orchestrator.config import (
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
from bidi_orchestrator.agent import UnifiedOrchestrator, create_orchestrator, get_root_agent

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
