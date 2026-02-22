"""Multi-agent orchestration patterns."""

from adk_bidi.orchestration.supervisor import (
    MultiAgentSupervisor,
    HierarchicalSupervisor,
    SpecialistTeam,
    DelegationStrategy,
    DelegationResult,
    SupervisorConfig,
    LIVE_MODEL,
)
from adk_bidi.orchestration.router import (
    IntentRouter,
    ContextualRouter,
    PriorityRouter,
    IntentPattern,
    RoutingDecision,
    RouteConfig,
)
from adk_bidi.orchestration.swarm import (
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
