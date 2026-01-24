"""
AgentSwarm - Parallel agent execution for concurrent tasks.

Provides swarm patterns for executing multiple agents in parallel
with result aggregation and coordination.
"""

from typing import Optional, List, Any, Dict, Callable, Union, Tuple
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


class AggregationStrategy(Enum):
    """Strategies for aggregating swarm results."""
    FIRST = "first"  # Return first result
    ALL = "all"  # Return all results
    MAJORITY = "majority"  # Return majority consensus
    BEST = "best"  # Return best result by score
    MERGE = "merge"  # Merge all results


@dataclass
class SwarmTask:
    """A task to be executed by the swarm."""
    task_id: str
    description: str
    agent_name: Optional[str] = None  # Specific agent or None for any
    priority: int = 0
    timeout_ms: int = 30000
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmResult:
    """Result from a swarm task execution."""
    task_id: str
    agent_name: str
    success: bool
    result: Any
    duration_ms: float
    error: Optional[str] = None
    score: float = 0.0


@dataclass
class SwarmConfig:
    """Configuration for the swarm."""
    max_concurrent: int = 5
    default_timeout_ms: int = 30000
    aggregation_strategy: AggregationStrategy = AggregationStrategy.ALL
    enable_retry: bool = True
    max_retries: int = 2
    coordination_model: str = LIVE_MODEL


class AgentSwarm:
    """
    Parallel agent execution swarm.

    Executes multiple agents concurrently for parallel task
    processing with result aggregation.

    Example:
        swarm = AgentSwarm(
            agents=[researcher1, researcher2, analyst],
            config=SwarmConfig(max_concurrent=3),
        )
        results = await swarm.execute_parallel([task1, task2, task3])
    """

    def __init__(
        self,
        agents: List[Union[Agent, BidiAgent]],
        shared_memory: Optional[SharedMemory] = None,
        config: Optional[SwarmConfig] = None,
    ):
        """
        Initialize the agent swarm.

        Args:
            agents: List of agents in the swarm
            shared_memory: Shared memory for coordination
            config: Swarm configuration
        """
        self.config = config or SwarmConfig()
        self.shared_memory = shared_memory or SharedMemory()

        # Register agents
        self.agents: Dict[str, Union[Agent, BidiAgent]] = {}
        self.agent_availability: Dict[str, bool] = {}

        for agent in agents:
            name = agent.name if isinstance(agent, BidiAgent) else agent.name
            self.agents[name] = agent
            self.agent_availability[name] = True

        # Execution tracking
        self.active_tasks: Dict[str, SwarmTask] = {}
        self.results_history: List[SwarmResult] = []
        self.execution_semaphore = asyncio.Semaphore(self.config.max_concurrent)

        # Create coordinator agent
        self.coordinator = self._create_coordinator()

    def _create_coordinator(self) -> Agent:
        """Create the swarm coordinator agent."""
        agent_list = "\n".join(
            f"- {name}" for name in self.agents.keys()
        )

        return Agent(
            name="swarm_coordinator",
            model=self.config.coordination_model,
            description="Coordinates parallel agent execution",
            instruction=f"""You coordinate a swarm of agents executing tasks in parallel.

**Available Agents:**
{agent_list}

**Your Role:**
1. Distribute tasks to available agents
2. Monitor execution progress
3. Aggregate results from multiple agents
4. Handle failures and retries
5. Optimize task assignment

Use the provided tools to manage swarm execution.""",
            tools=[
                FunctionTool(self.get_swarm_status),
                FunctionTool(self.get_results_summary),
            ],
        )

    async def execute_task(
        self,
        task: SwarmTask,
        agent: Optional[Union[Agent, BidiAgent]] = None,
    ) -> SwarmResult:
        """
        Execute a single task with a swarm agent.

        Args:
            task: Task to execute
            agent: Specific agent or None to select automatically

        Returns:
            Execution result
        """
        async with self.execution_semaphore:
            # Select agent
            if agent is None:
                if task.agent_name and task.agent_name in self.agents:
                    agent = self.agents[task.agent_name]
                else:
                    agent = self._select_available_agent()

            if agent is None:
                return SwarmResult(
                    task_id=task.task_id,
                    agent_name="none",
                    success=False,
                    result=None,
                    duration_ms=0,
                    error="No available agent",
                )

            agent_name = agent.name if isinstance(agent, BidiAgent) else agent.name

            # Mark agent as busy
            self.agent_availability[agent_name] = False
            self.active_tasks[task.task_id] = task

            start_time = datetime.now()

            try:
                # Store task in shared memory
                await self.shared_memory.write(
                    key=f"task_{task.task_id}",
                    value=task.description,
                    agent_id=agent_name,
                )

                # Simulate task execution (actual execution would use Runner)
                # In real usage, this would be:
                # async for event in runner.run_live(...):
                #     process event

                duration_ms = (datetime.now() - start_time).total_seconds() * 1000

                result = SwarmResult(
                    task_id=task.task_id,
                    agent_name=agent_name,
                    success=True,
                    result=f"Task {task.task_id} completed by {agent_name}",
                    duration_ms=duration_ms,
                    score=0.8,
                )

            except asyncio.TimeoutError:
                result = SwarmResult(
                    task_id=task.task_id,
                    agent_name=agent_name,
                    success=False,
                    result=None,
                    duration_ms=task.timeout_ms,
                    error="Task timed out",
                )

            except Exception as e:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                result = SwarmResult(
                    task_id=task.task_id,
                    agent_name=agent_name,
                    success=False,
                    result=None,
                    duration_ms=duration_ms,
                    error=str(e),
                )

            finally:
                # Mark agent as available
                self.agent_availability[agent_name] = True
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]

            self.results_history.append(result)
            return result

    async def execute_parallel(
        self,
        tasks: List[SwarmTask],
        aggregation: Optional[AggregationStrategy] = None,
    ) -> List[SwarmResult]:
        """
        Execute multiple tasks in parallel.

        Args:
            tasks: List of tasks to execute
            aggregation: Optional aggregation strategy override

        Returns:
            List of results (may be aggregated based on strategy)
        """
        strategy = aggregation or self.config.aggregation_strategy

        # Create coroutines for all tasks
        coroutines = [self.execute_task(task) for task in tasks]

        # Execute in parallel
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(SwarmResult(
                    task_id=tasks[i].task_id,
                    agent_name="unknown",
                    success=False,
                    result=None,
                    duration_ms=0,
                    error=str(result),
                ))
            else:
                processed_results.append(result)

        # Apply aggregation strategy
        return self._aggregate_results(processed_results, strategy)

    def _aggregate_results(
        self,
        results: List[SwarmResult],
        strategy: AggregationStrategy,
    ) -> List[SwarmResult]:
        """Aggregate results based on strategy."""
        if not results:
            return results

        if strategy == AggregationStrategy.FIRST:
            # Return first successful result
            for result in results:
                if result.success:
                    return [result]
            return [results[0]]  # Return first even if failed

        elif strategy == AggregationStrategy.BEST:
            # Return highest scored result
            successful = [r for r in results if r.success]
            if successful:
                best = max(successful, key=lambda r: r.score)
                return [best]
            return [results[0]]

        elif strategy == AggregationStrategy.MAJORITY:
            # Return results that appear most frequently
            # (simplified: return all successful)
            successful = [r for r in results if r.success]
            return successful if successful else results

        elif strategy == AggregationStrategy.MERGE:
            # Merge all results into one
            merged_result = []
            for result in results:
                if result.success and result.result:
                    merged_result.append(str(result.result))

            if merged_result:
                return [SwarmResult(
                    task_id="merged",
                    agent_name="swarm",
                    success=True,
                    result="\n".join(merged_result),
                    duration_ms=sum(r.duration_ms for r in results),
                    score=sum(r.score for r in results if r.success) / len([r for r in results if r.success]),
                )]
            return results

        else:  # ALL
            return results

    def _select_available_agent(self) -> Optional[Union[Agent, BidiAgent]]:
        """Select an available agent."""
        for name, available in self.agent_availability.items():
            if available:
                return self.agents[name]
        return None

    async def broadcast_task(
        self,
        task: SwarmTask,
    ) -> List[SwarmResult]:
        """
        Broadcast a task to all agents.

        Args:
            task: Task to broadcast

        Returns:
            Results from all agents
        """
        tasks = []
        for name in self.agents.keys():
            agent_task = SwarmTask(
                task_id=f"{task.task_id}_{name}",
                description=task.description,
                agent_name=name,
                priority=task.priority,
                timeout_ms=task.timeout_ms,
                metadata=task.metadata,
            )
            tasks.append(agent_task)

        return await self.execute_parallel(tasks)

    async def race_task(
        self,
        task: SwarmTask,
        num_agents: int = 2,
    ) -> SwarmResult:
        """
        Race multiple agents on the same task, return first result.

        Args:
            task: Task to race
            num_agents: Number of agents to race

        Returns:
            First successful result
        """
        available = [
            name for name, avail in self.agent_availability.items()
            if avail
        ][:num_agents]

        if not available:
            return SwarmResult(
                task_id=task.task_id,
                agent_name="none",
                success=False,
                result=None,
                duration_ms=0,
                error="No available agents",
            )

        tasks = [
            SwarmTask(
                task_id=f"{task.task_id}_{name}",
                description=task.description,
                agent_name=name,
                timeout_ms=task.timeout_ms,
            )
            for name in available
        ]

        results = await self.execute_parallel(
            tasks,
            aggregation=AggregationStrategy.FIRST,
        )

        return results[0] if results else SwarmResult(
            task_id=task.task_id,
            agent_name="none",
            success=False,
            result=None,
            duration_ms=0,
            error="No results",
        )

    # Tools for coordinator

    def get_swarm_status(self) -> str:
        """
        Get current swarm status.

        Returns:
            Formatted status string
        """
        lines = ["Swarm Status:"]
        lines.append(f"Agents: {len(self.agents)}")
        lines.append(f"Active tasks: {len(self.active_tasks)}")

        available_count = sum(1 for a in self.agent_availability.values() if a)
        lines.append(f"Available agents: {available_count}/{len(self.agents)}")

        lines.append("\nAgent Status:")
        for name, available in self.agent_availability.items():
            status = "available" if available else "busy"
            lines.append(f"  - {name}: {status}")

        return "\n".join(lines)

    def get_results_summary(self, limit: int = 10) -> str:
        """
        Get summary of recent results.

        Args:
            limit: Maximum results to show

        Returns:
            Formatted summary
        """
        if not self.results_history:
            return "No results yet."

        recent = self.results_history[-limit:]
        successful = sum(1 for r in recent if r.success)

        lines = [
            f"Recent Results ({successful}/{len(recent)} successful):",
        ]

        for result in recent:
            status = "✓" if result.success else "✗"
            lines.append(
                f"  {status} {result.task_id}: {result.agent_name} "
                f"({result.duration_ms:.0f}ms)"
            )

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Get swarm statistics."""
        total = len(self.results_history)
        successful = sum(1 for r in self.results_history if r.success)
        avg_duration = (
            sum(r.duration_ms for r in self.results_history) / total
            if total > 0 else 0
        )

        return {
            "agent_count": len(self.agents),
            "available_agents": sum(1 for a in self.agent_availability.values() if a),
            "active_tasks": len(self.active_tasks),
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": successful / total if total > 0 else 0,
            "avg_duration_ms": avg_duration,
        }


class CompetitiveSwarm(AgentSwarm):
    """
    Competitive swarm where agents compete on tasks.

    Agents are scored based on performance, and higher-scoring
    agents get priority for future tasks.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agent_scores: Dict[str, float] = {
            name: 1.0 for name in self.agents.keys()
        }

    async def execute_task(
        self,
        task: SwarmTask,
        agent: Optional[Union[Agent, BidiAgent]] = None,
    ) -> SwarmResult:
        """Execute task and update agent scores."""
        result = await super().execute_task(task, agent)

        # Update agent score
        if result.agent_name in self.agent_scores:
            if result.success:
                # Increase score for success
                self.agent_scores[result.agent_name] = min(
                    2.0,
                    self.agent_scores[result.agent_name] + 0.1,
                )
            else:
                # Decrease score for failure
                self.agent_scores[result.agent_name] = max(
                    0.5,
                    self.agent_scores[result.agent_name] - 0.1,
                )

        return result

    def _select_available_agent(self) -> Optional[Union[Agent, BidiAgent]]:
        """Select best available agent by score."""
        available = [
            (name, self.agent_scores.get(name, 1.0))
            for name, avail in self.agent_availability.items()
            if avail
        ]

        if not available:
            return None

        # Select highest scored available agent
        best_name = max(available, key=lambda x: x[1])[0]
        return self.agents[best_name]

    def get_leaderboard(self) -> str:
        """Get agent leaderboard by score."""
        sorted_agents = sorted(
            self.agent_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        lines = ["Agent Leaderboard:"]
        for i, (name, score) in enumerate(sorted_agents, 1):
            lines.append(f"  {i}. {name}: {score:.2f}")

        return "\n".join(lines)


class CollaborativeSwarm(AgentSwarm):
    """
    Collaborative swarm where agents work together.

    Results are shared between agents to build on
    each other's work.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collaboration_chain: List[str] = []

    async def execute_chain(
        self,
        initial_task: SwarmTask,
        chain_length: int = 3,
    ) -> List[SwarmResult]:
        """
        Execute a collaboration chain.

        Each agent builds on the previous agent's result.

        Args:
            initial_task: Starting task
            chain_length: Number of agents in chain

        Returns:
            Results from chain
        """
        results = []
        current_task = initial_task
        previous_result = None

        for i in range(chain_length):
            # Select next agent (round-robin through available)
            agents_list = list(self.agents.keys())
            agent_name = agents_list[i % len(agents_list)]

            # Add previous result to task context
            if previous_result and previous_result.success:
                current_task = SwarmTask(
                    task_id=f"{initial_task.task_id}_chain_{i}",
                    description=f"{initial_task.description}\n\nPrevious result: {previous_result.result}",
                    agent_name=agent_name,
                    timeout_ms=initial_task.timeout_ms,
                )

                # Share with all agents
                await self.shared_memory.write(
                    key=f"chain_result_{i-1}",
                    value=str(previous_result.result),
                    agent_id=agent_name,
                )

            result = await self.execute_task(current_task)
            results.append(result)
            previous_result = result

            self.collaboration_chain.append(agent_name)

        return results
