"""
MultiAgentSupervisor - Coordinated multi-agent orchestration.

Provides supervisor patterns for coordinating multiple agents
in real-time sessions with shared context and delegation.
"""

from typing import Optional, List, Any, Dict, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from google.adk.agents import Agent
from google.adk.tools import AgentTool, FunctionTool

from adk_bidi.memory.shared_memory import SharedMemory
from adk_bidi.memory.working_memory import WorkingMemory
from adk_bidi.agents.bidi_agent import BidiAgent


# Native audio model for real-time streaming
LIVE_MODEL = "gemini-live-2.5-flash-native-audio"


class DelegationStrategy(Enum):
    """Strategies for delegating to sub-agents."""
    SINGLE = "single"  # Route to one agent
    PARALLEL = "parallel"  # Multiple agents in parallel
    SEQUENTIAL = "sequential"  # Multiple agents in sequence
    CONSENSUS = "consensus"  # Multiple agents must agree


@dataclass
class DelegationResult:
    """Result from delegating to a sub-agent."""
    agent_name: str
    success: bool
    result: Any
    duration_ms: float
    error: Optional[str] = None


@dataclass
class SupervisorConfig:
    """Configuration for the supervisor."""
    max_delegation_depth: int = 3
    enable_parallel_delegation: bool = True
    require_explicit_delegation: bool = False
    auto_synthesize_results: bool = True
    delegation_timeout_ms: int = 30000


class MultiAgentSupervisor:
    """
    Coordinates multiple agents in real-time sessions.

    The supervisor manages a team of specialist agents, routing
    requests to the appropriate agent(s) and synthesizing results.

    Example:
        supervisor = MultiAgentSupervisor(
            agents=[researcher, writer, analyst],
            shared_memory=SharedMemory(),
        )
        # Supervisor routes to appropriate agent
        result = await supervisor.handle_request("Research AI trends")
    """

    def __init__(
        self,
        agents: List[Union[Agent, BidiAgent]],
        shared_memory: Optional[SharedMemory] = None,
        working_memory: Optional[WorkingMemory] = None,
        config: Optional[SupervisorConfig] = None,
        instruction: Optional[str] = None,
        model: str = LIVE_MODEL,
    ):
        """
        Initialize the multi-agent supervisor.

        Args:
            agents: List of agents to supervise
            shared_memory: Shared memory for coordination
            working_memory: Working memory for context
            config: Supervisor configuration
            instruction: Optional custom instruction
            model: LLM model for the supervisor (default: gemini-live-2.5-flash-native-audio)
        """
        self.config = config or SupervisorConfig()
        self.shared_memory = shared_memory or SharedMemory()
        self.working_memory = working_memory or WorkingMemory(max_size=30)
        self.model = model

        # Track agents
        self.agents: Dict[str, Union[Agent, BidiAgent]] = {}
        self.agent_tools: List[AgentTool] = []

        for agent in agents:
            self._register_agent(agent)

        # Delegation tracking
        self.delegation_history: List[DelegationResult] = []
        self.current_delegation_depth = 0

        # Create supervisor agent
        self.supervisor = self._create_supervisor(instruction)

    def _register_agent(self, agent: Union[Agent, BidiAgent]) -> None:
        """Register an agent with the supervisor."""
        # Handle BidiAgent wrapper
        if isinstance(agent, BidiAgent):
            adk_agent = agent.adk_agent
            name = agent.name
        else:
            adk_agent = agent
            name = agent.name

        self.agents[name] = agent
        self.agent_tools.append(AgentTool(agent=adk_agent))

    def _create_supervisor(self, custom_instruction: Optional[str]) -> Agent:
        """Create the supervisor agent."""
        # Build agent descriptions
        agent_descriptions = []
        for name, agent in self.agents.items():
            if isinstance(agent, BidiAgent):
                desc = agent.description
            else:
                desc = getattr(agent, 'description', f"Agent: {name}")
            agent_descriptions.append(f"- **{name}**: {desc}")

        agent_list = "\n".join(agent_descriptions)

        base_instruction = f"""You are a supervisor coordinating a team of specialist agents.

**Available Agents:**
{agent_list}

**Your Responsibilities:**
1. Analyze incoming requests to determine the best agent(s) to handle them
2. Delegate tasks to appropriate specialists
3. Coordinate multi-agent workflows when needed
4. Synthesize results from multiple agents
5. Maintain context across the conversation

**Delegation Guidelines:**
- Route simple requests to a single appropriate agent
- For complex tasks, break them down and coordinate multiple agents
- Use parallel delegation when tasks are independent
- Use sequential delegation when tasks have dependencies
- Always provide context to agents about the broader task

**Tools Available:**
- Each agent is available as a tool you can call
- Use `get_agent_status` to check agent availability
- Use `share_context` to share information between agents
- Use `get_delegation_history` to review past delegations

**Quality Standards:**
- Ensure responses fully address the user's request
- Verify agent outputs before synthesizing
- Ask for clarification if the request is ambiguous
"""

        if custom_instruction:
            base_instruction += f"\n\n**Additional Instructions:**\n{custom_instruction}"

        # Add management tools
        management_tools = [
            FunctionTool(self.get_agent_status),
            FunctionTool(self.share_context),
            FunctionTool(self.get_delegation_history),
            FunctionTool(self.delegate_to_multiple),
        ]

        return Agent(
            name="supervisor",
            model=self.model,
            description="Multi-agent supervisor coordinating specialist agents",
            instruction=base_instruction,
            tools=self.agent_tools + management_tools,
        )

    # Management tools

    def get_agent_status(self) -> str:
        """
        Get status of all supervised agents.

        Returns:
            Status summary of all agents
        """
        status_lines = ["Agent Status:"]
        for name, agent in self.agents.items():
            if isinstance(agent, BidiAgent):
                stats = agent.get_stats()
                status_lines.append(
                    f"- {name}: turns={stats.get('turn_count', 0)}, "
                    f"memory={stats.get('working_memory_size', 0)}"
                )
            else:
                status_lines.append(f"- {name}: available")

        return "\n".join(status_lines)

    async def share_context(self, key: str, value: str, target_agents: str = "all") -> str:
        """
        Share context with agents via shared memory.

        Args:
            key: Context key
            value: Context value
            target_agents: Comma-separated agent names or "all"

        Returns:
            Confirmation message
        """
        success = await self.shared_memory.write(key, value, "supervisor")

        if success:
            targets = (
                list(self.agents.keys())
                if target_agents == "all"
                else [t.strip() for t in target_agents.split(",")]
            )
            return f"Context '{key}' shared with: {', '.join(targets)}"
        return f"Failed to share context '{key}'"

    def get_delegation_history(self, limit: int = 10) -> str:
        """
        Get recent delegation history.

        Args:
            limit: Maximum number of entries

        Returns:
            Formatted delegation history
        """
        if not self.delegation_history:
            return "No delegations recorded yet."

        history = self.delegation_history[-limit:]
        lines = ["Recent Delegations:"]

        for result in history:
            status = "✓" if result.success else "✗"
            lines.append(
                f"- {status} {result.agent_name}: {result.duration_ms:.0f}ms"
            )
            if result.error:
                lines.append(f"  Error: {result.error}")

        return "\n".join(lines)

    async def delegate_to_multiple(
        self,
        agents: str,
        task: str,
        strategy: str = "parallel",
    ) -> str:
        """
        Delegate a task to multiple agents.

        Args:
            agents: Comma-separated list of agent names
            task: Task description
            strategy: "parallel" or "sequential"

        Returns:
            Combined results from agents
        """
        agent_names = [a.strip() for a in agents.split(",")]
        invalid = [a for a in agent_names if a not in self.agents]

        if invalid:
            return f"Unknown agents: {', '.join(invalid)}"

        # Store task in shared memory
        await self.shared_memory.write("current_task", task, "supervisor")

        if strategy == "parallel":
            return f"Delegating to {len(agent_names)} agents in parallel: {', '.join(agent_names)}"
        else:
            return f"Delegating to {len(agent_names)} agents sequentially: {', '.join(agent_names)}"

    # Core functionality

    async def handle_request(
        self,
        user_input: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """
        Handle a user request through the supervisor.

        Args:
            user_input: User's input
            session_id: Session identifier
            metadata: Optional additional metadata

        Returns:
            The supervisor agent for running
        """
        # Store input in shared memory
        await self.shared_memory.write(
            key=f"user_input_{session_id}",
            value=user_input,
            agent_id="supervisor",
        )

        # Store in working memory
        self.working_memory.add(
            key="last_user_request",
            value=user_input,
            importance=0.9,
            source_agent="user",
        )

        if metadata:
            self.working_memory.add(
                key="request_metadata",
                value=str(metadata),
                importance=0.4,
                source_agent="system",
            )

        return self.supervisor

    def add_agent(self, agent: Union[Agent, BidiAgent]) -> None:
        """Add an agent to the supervised team."""
        self._register_agent(agent)
        # Recreate supervisor with updated agent list
        self.supervisor = self._create_supervisor(None)

    def remove_agent(self, name: str) -> bool:
        """Remove an agent from the supervised team."""
        if name in self.agents:
            del self.agents[name]
            self.agent_tools = [
                tool for tool in self.agent_tools
                if tool.agent.name != name
            ]
            self.supervisor = self._create_supervisor(None)
            return True
        return False

    def get_supervisor_agent(self) -> Agent:
        """Get the supervisor agent for use with Runner."""
        return self.supervisor

    def get_stats(self) -> Dict[str, Any]:
        """Get supervisor statistics."""
        return {
            "agent_count": len(self.agents),
            "agents": list(self.agents.keys()),
            "delegations": len(self.delegation_history),
            "successful_delegations": sum(
                1 for d in self.delegation_history if d.success
            ),
            "working_memory_size": len(self.working_memory),
        }


class HierarchicalSupervisor(MultiAgentSupervisor):
    """
    Hierarchical supervisor with sub-supervisors.

    Supports multi-level agent hierarchies where supervisors
    can delegate to other supervisors.
    """

    def __init__(
        self,
        agents: List[Union[Agent, BidiAgent]],
        sub_supervisors: Optional[List["MultiAgentSupervisor"]] = None,
        **kwargs,
    ):
        """
        Initialize hierarchical supervisor.

        Args:
            agents: Direct agent reports
            sub_supervisors: Child supervisors
            **kwargs: Additional arguments for MultiAgentSupervisor
        """
        super().__init__(agents=agents, **kwargs)

        self.sub_supervisors: Dict[str, MultiAgentSupervisor] = {}

        if sub_supervisors:
            for supervisor in sub_supervisors:
                self.add_sub_supervisor(supervisor)

    def add_sub_supervisor(self, supervisor: "MultiAgentSupervisor") -> None:
        """Add a sub-supervisor to the hierarchy."""
        name = f"team_{supervisor.supervisor.name}"
        self.sub_supervisors[name] = supervisor

        # Add sub-supervisor's supervisor as an agent
        self.agents[name] = supervisor.supervisor
        self.agent_tools.append(AgentTool(agent=supervisor.supervisor))

        # Recreate main supervisor
        self.supervisor = self._create_supervisor(None)

    def get_hierarchy_stats(self) -> Dict[str, Any]:
        """Get statistics for the entire hierarchy."""
        stats = self.get_stats()
        stats["sub_supervisors"] = {}

        for name, sub_supervisor in self.sub_supervisors.items():
            stats["sub_supervisors"][name] = sub_supervisor.get_stats()

        return stats


class SpecialistTeam:
    """
    Pre-configured team of specialist agents.

    Factory for creating common team configurations.
    """

    @staticmethod
    def research_team(shared_memory: Optional[SharedMemory] = None) -> MultiAgentSupervisor:
        """Create a research-focused team."""
        researcher = Agent(
            name="researcher",
            model=LIVE_MODEL,
            description="Research specialist for finding and analyzing information",
            instruction="You are a research specialist. Find, analyze, and synthesize information.",
        )

        analyst = Agent(
            name="analyst",
            model=LIVE_MODEL,
            description="Data analyst for interpreting findings",
            instruction="You are a data analyst. Interpret findings and identify patterns.",
        )

        writer = Agent(
            name="writer",
            model=LIVE_MODEL,
            description="Technical writer for creating reports",
            instruction="You are a technical writer. Create clear, well-structured reports.",
        )

        return MultiAgentSupervisor(
            agents=[researcher, analyst, writer],
            shared_memory=shared_memory,
            instruction="Coordinate research tasks by delegating to appropriate specialists.",
        )

    @staticmethod
    def support_team(shared_memory: Optional[SharedMemory] = None) -> MultiAgentSupervisor:
        """Create a customer support team."""
        greeter = Agent(
            name="greeter",
            model=LIVE_MODEL,
            description="Initial contact and triage",
            instruction="You greet users and understand their needs. Route to specialists.",
        )

        technical = Agent(
            name="technical_support",
            model=LIVE_MODEL,
            description="Technical issue resolution",
            instruction="You resolve technical issues. Provide step-by-step solutions.",
        )

        billing = Agent(
            name="billing_support",
            model=LIVE_MODEL,
            description="Billing and account questions",
            instruction="You handle billing and account questions. Be accurate and helpful.",
        )

        return MultiAgentSupervisor(
            agents=[greeter, technical, billing],
            shared_memory=shared_memory,
            instruction="Provide excellent customer support by routing to the right specialist.",
        )
