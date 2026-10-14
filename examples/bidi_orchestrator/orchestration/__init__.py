"""Multi-agent orchestration patterns."""

from bidi_orchestrator.orchestration.supervisor import (
    MultiAgentSupervisor,
    HierarchicalSupervisor,
    SpecialistTeam,
    DelegationStrategy,
    DelegationResult,
    SupervisorConfig,
    LIVE_MODEL,
)
from bidi_orchestrator.orchestration.router import (
    IntentRouter,
    ContextualRouter,
    PriorityRouter,
    IntentPattern,
    RoutingDecision,
    RouteConfig,
)
from bidi_orchestrator.orchestration.swarm import (
    AgentSwarm,
    CompetitiveSwarm,
    CollaborativeSwarm,
    SwarmTask,
    SwarmResult,
    SwarmConfig,
    AggregationStrategy,
)

__all__ = [
    # Supervisor
    "MultiAgentSupervisor",
    "HierarchicalSupervisor",
    "SpecialistTeam",
    "DelegationStrategy",
    "DelegationResult",
    "SupervisorConfig",
    "LIVE_MODEL",
    # Router
    "IntentRouter",
    "ContextualRouter",
    "PriorityRouter",
    "IntentPattern",
    "RoutingDecision",
    "RouteConfig",
    # Swarm
    "AgentSwarm",
    "CompetitiveSwarm",
    "CollaborativeSwarm",
    "SwarmTask",
    "SwarmResult",
    "SwarmConfig",
    "AggregationStrategy",
]
