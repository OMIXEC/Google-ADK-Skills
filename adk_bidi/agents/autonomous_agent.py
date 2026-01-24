"""
AutonomousAgent - Self-reasoning agent with proactive behavior.

Provides agents that can reason about their goals, plan actions,
and execute autonomously with minimal human intervention.
"""

from typing import Optional, List, Any, Dict, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from adk_bidi.agents.bidi_agent import BidiAgent
from adk_bidi.memory.working_memory import WorkingMemory
from adk_bidi.memory.shared_memory import SharedMemory
from adk_bidi.memory.persistent_store import PersistentMemoryStore, InMemoryPersistentStore


class ReasoningPhase(Enum):
    """Phases of the autonomous reasoning loop."""
    OBSERVE = "observe"
    THINK = "think"
    PLAN = "plan"
    ACT = "act"
    REFLECT = "reflect"


@dataclass
class ActionPlan:
    """A plan consisting of steps to achieve a goal."""
    goal: str
    steps: List[str]
    current_step: int = 0
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    results: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "steps": self.steps,
            "current_step": self.current_step,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "results": self.results,
        }


@dataclass
class Thought:
    """A recorded thought from the reasoning process."""
    observation: str
    reasoning: str
    phase: ReasoningPhase
    created_at: datetime = field(default_factory=datetime.now)


class AutonomousAgent(BidiAgent):
    """
    Self-reasoning agent with proactive behavior.

    Implements the OODA loop (Observe, Orient, Decide, Act) with
    explicit reasoning and planning capabilities.

    Example:
        agent = AutonomousAgent(
            name="researcher",
            goal="Find and summarize the latest AI research papers",
        )
        # Agent will autonomously work towards goal
    """

    def __init__(
        self,
        name: str,
        goal: str,
        instruction: Optional[str] = None,
        model: str = "gemini-2.0-flash-live-001",
        tools: Optional[List[Any]] = None,
        working_memory: Optional[WorkingMemory] = None,
        shared_memory: Optional[SharedMemory] = None,
        persistent_memory: Optional[PersistentMemoryStore] = None,
        max_thoughts: int = 50,
        enable_proactivity: bool = True,
        **kwargs,
    ):
        """
        Initialize an autonomous agent.

        Args:
            name: Agent name
            goal: The agent's primary goal
            instruction: Optional additional instruction
            model: LLM model to use
            tools: Available tools
            working_memory: Working memory (with larger capacity)
            shared_memory: Shared memory for multi-agent coordination
            persistent_memory: Long-term memory storage
            max_thoughts: Maximum thoughts to retain
            enable_proactivity: Enable proactive behavior
            **kwargs: Additional arguments
        """
        self.goal = goal
        self.max_thoughts = max_thoughts
        self.enable_proactivity = enable_proactivity

        # Use larger working memory for autonomous reasoning
        if working_memory is None:
            working_memory = WorkingMemory(max_size=30)

        # Persistent memory for long-term recall
        self.persistent_memory = persistent_memory

        # Reasoning state
        self.thoughts: List[Thought] = []
        self.current_plan: Optional[ActionPlan] = None
        self.current_phase = ReasoningPhase.OBSERVE
        self.action_count = 0
        self.goal_progress = 0.0

        # Build autonomous instruction
        auto_instruction = self._build_autonomous_instruction(instruction)

        super().__init__(
            name=name,
            instruction=auto_instruction,
            model=model,
            tools=tools,
            working_memory=working_memory,
            shared_memory=shared_memory,
            memory_context_size=10,  # More context for reasoning
            **kwargs,
        )

        # Add reasoning tools
        self._add_reasoning_tools()

    def _build_autonomous_instruction(self, additional_instruction: Optional[str]) -> str:
        """Build instruction for autonomous operation."""
        instruction = f"""
You are an autonomous agent working towards the goal: {self.goal}

**Autonomous Reasoning Process:**
You operate using a structured reasoning loop:

1. **OBSERVE**: Process all available information
   - What inputs have you received?
   - What is the current state?
   - What do you know from memory?

2. **THINK**: Reason about the situation
   - How does this relate to your goal?
   - What are the key insights?
   - What are the constraints or challenges?

3. **PLAN**: Create or update your action plan
   - What steps will move you towards the goal?
   - What is the next logical action?
   - How will you measure progress?

4. **ACT**: Execute your plan
   - Use available tools to take action
   - Delegate to other agents if needed
   - Record the results

5. **REFLECT**: Evaluate outcomes
   - Did the action succeed?
   - What did you learn?
   - Should you adjust your approach?

**Tools Available:**
- `think`: Record your reasoning process
- `recall_memory`: Access long-term knowledge
- `store_memory`: Save important information for later
- `create_plan`: Create an action plan
- `update_progress`: Track goal progress

**Guidelines:**
- Always explain your reasoning before acting
- Be proactive - don't wait for instructions
- Learn from outcomes and adapt your approach
- Use memory to avoid repeating mistakes
- Break complex goals into manageable steps
"""

        if additional_instruction:
            instruction += f"\n\n**Additional Instructions:**\n{additional_instruction}"

        return instruction

    def _add_reasoning_tools(self) -> None:
        """Add autonomous reasoning tools."""
        self.tools.extend([
            FunctionTool(self.think),
            FunctionTool(self.create_plan),
            FunctionTool(self.get_current_plan),
            FunctionTool(self.complete_step),
            FunctionTool(self.update_progress),
            FunctionTool(self.recall_long_term),
            FunctionTool(self.store_long_term),
            FunctionTool(self.get_reasoning_summary),
        ])

    # Reasoning tools

    def think(self, observation: str, reasoning: str) -> str:
        """
        Record a thought in the reasoning process.

        Args:
            observation: What you observed
            reasoning: Your reasoning about it

        Returns:
            Confirmation message
        """
        thought = Thought(
            observation=observation,
            reasoning=reasoning,
            phase=self.current_phase,
        )
        self.thoughts.append(thought)

        # Trim old thoughts
        if len(self.thoughts) > self.max_thoughts:
            self.thoughts = self.thoughts[-self.max_thoughts:]

        # Store in working memory
        self.working_memory.add(
            key=f"thought_{len(self.thoughts)}",
            value={"observation": observation, "reasoning": reasoning},
            importance=0.8,
            source_agent=self.name,
        )

        return f"Thought recorded: {reasoning[:100]}..."

    def create_plan(self, goal: str, steps: List[str]) -> str:
        """
        Create an action plan.

        Args:
            goal: What the plan aims to achieve
            steps: List of steps to execute

        Returns:
            Confirmation message
        """
        self.current_plan = ActionPlan(goal=goal, steps=steps)

        self.working_memory.add(
            key="current_plan",
            value=self.current_plan.to_dict(),
            importance=0.9,
            source_agent=self.name,
        )

        return f"Plan created with {len(steps)} steps for: {goal}"

    def get_current_plan(self) -> str:
        """
        Get the current action plan.

        Returns:
            Plan details or message if no plan exists
        """
        if not self.current_plan:
            return "No current plan. Use create_plan to make one."

        plan = self.current_plan
        status_line = f"Goal: {plan.goal}\nStatus: {plan.status}"
        steps_display = []

        for i, step in enumerate(plan.steps):
            marker = "✓" if i < plan.current_step else "○" if i == plan.current_step else "·"
            steps_display.append(f"  {marker} {i+1}. {step}")

        return f"{status_line}\nProgress: {plan.current_step}/{len(plan.steps)}\n" + "\n".join(steps_display)

    def complete_step(self, result: str = "") -> str:
        """
        Mark the current step as complete and move to next.

        Args:
            result: Result or notes from completing the step

        Returns:
            Status message
        """
        if not self.current_plan:
            return "No current plan."

        plan = self.current_plan
        if plan.current_step >= len(plan.steps):
            plan.status = "completed"
            return "Plan already completed!"

        plan.results.append(result)
        plan.current_step += 1
        plan.status = "in_progress"

        if plan.current_step >= len(plan.steps):
            plan.status = "completed"
            return f"Plan completed! All {len(plan.steps)} steps done."

        next_step = plan.steps[plan.current_step]
        return f"Step completed. Next step ({plan.current_step + 1}/{len(plan.steps)}): {next_step}"

    def update_progress(self, progress: float, notes: str = "") -> str:
        """
        Update progress towards the goal.

        Args:
            progress: Progress as a percentage (0.0 to 1.0)
            notes: Optional notes about progress

        Returns:
            Progress update message
        """
        self.goal_progress = max(0.0, min(1.0, progress))

        self.working_memory.add(
            key="goal_progress",
            value=f"{self.goal_progress:.0%}: {notes}",
            importance=0.7,
            source_agent=self.name,
        )

        return f"Progress updated to {self.goal_progress:.0%}"

    def recall_long_term(self, query: str, top_k: int = 5) -> str:
        """
        Recall from long-term memory.

        Args:
            query: What to search for
            top_k: Number of results

        Returns:
            Relevant memories or not found message
        """
        if not self.persistent_memory:
            return "Long-term memory not available."

        memories = self.persistent_memory.recall(query, top_k=top_k)

        if not memories:
            return "No relevant memories found."

        results = []
        for mem in memories:
            results.append(f"- {mem['content']} (relevance: {mem['score']:.2f})")

        return "Recalled memories:\n" + "\n".join(results)

    def store_long_term(self, content: str, importance: str = "medium") -> str:
        """
        Store information in long-term memory.

        Args:
            content: Information to store
            importance: Importance level (low, medium, high)

        Returns:
            Confirmation message
        """
        if not self.persistent_memory:
            return "Long-term memory not available."

        importance_scores = {"low": 0.3, "medium": 0.5, "high": 0.8}
        memory_id = f"{self.name}_mem_{datetime.now().timestamp()}"

        success = self.persistent_memory.store_memory(
            memory_id=memory_id,
            content=content,
            importance=importance_scores.get(importance, 0.5),
            agent_id=self.name,
        )

        if success:
            return f"Stored in long-term memory: {content[:50]}..."
        return "Failed to store memory."

    def get_reasoning_summary(self) -> str:
        """
        Get a summary of recent reasoning.

        Returns:
            Summary of thoughts and progress
        """
        summary_lines = [
            f"Goal: {self.goal}",
            f"Progress: {self.goal_progress:.0%}",
            f"Actions taken: {self.action_count}",
            f"Current phase: {self.current_phase.value}",
            f"Thoughts recorded: {len(self.thoughts)}",
        ]

        # Recent thoughts
        if self.thoughts:
            summary_lines.append("\nRecent reasoning:")
            for thought in self.thoughts[-3:]:
                summary_lines.append(f"  - [{thought.phase.value}] {thought.reasoning[:100]}")

        # Current plan status
        if self.current_plan:
            summary_lines.append(f"\nPlan: {self.current_plan.goal}")
            summary_lines.append(f"  Steps: {self.current_plan.current_step}/{len(self.current_plan.steps)}")

        return "\n".join(summary_lines)

    # Phase management

    def advance_phase(self) -> ReasoningPhase:
        """Advance to the next reasoning phase."""
        phases = list(ReasoningPhase)
        current_idx = phases.index(self.current_phase)
        next_idx = (current_idx + 1) % len(phases)
        self.current_phase = phases[next_idx]
        return self.current_phase

    async def process_event(self, event: Any) -> Any:
        """Process events with autonomous reasoning."""
        event = await super().process_event(event)
        self.action_count += 1
        return event

    def get_autonomous_stats(self) -> Dict[str, Any]:
        """Get autonomous agent statistics."""
        base_stats = self.get_stats()
        base_stats.update({
            "goal": self.goal,
            "goal_progress": self.goal_progress,
            "current_phase": self.current_phase.value,
            "thoughts_count": len(self.thoughts),
            "action_count": self.action_count,
            "has_plan": self.current_plan is not None,
            "plan_status": self.current_plan.status if self.current_plan else "no_plan",
        })
        return base_stats


class ResearchAgent(AutonomousAgent):
    """
    Autonomous research agent.

    Specialized for information gathering, analysis, and synthesis.
    """

    def __init__(
        self,
        name: str,
        research_topic: str,
        **kwargs,
    ):
        goal = f"Research and synthesize information about: {research_topic}"

        instruction = """
**Research Methodology:**
1. Define key questions to answer
2. Gather information from available sources
3. Cross-reference and verify facts
4. Synthesize findings into coherent summary
5. Identify gaps and areas needing more research

**Output Guidelines:**
- Cite sources when possible
- Distinguish between facts and interpretations
- Note confidence levels in findings
- Highlight key insights and conclusions
"""

        super().__init__(
            name=name,
            goal=goal,
            instruction=instruction,
            **kwargs,
        )


class TaskAgent(AutonomousAgent):
    """
    Autonomous task execution agent.

    Specialized for completing specific tasks with clear steps.
    """

    def __init__(
        self,
        name: str,
        task_description: str,
        success_criteria: List[str],
        **kwargs,
    ):
        goal = f"Complete task: {task_description}"

        criteria_text = "\n".join(f"- {c}" for c in success_criteria)
        instruction = f"""
**Task:** {task_description}

**Success Criteria:**
{criteria_text}

**Execution Guidelines:**
- Break the task into clear, actionable steps
- Verify each step before moving to the next
- Handle errors gracefully and report issues
- Confirm completion against success criteria
"""

        super().__init__(
            name=name,
            goal=goal,
            instruction=instruction,
            **kwargs,
        )
        self.success_criteria = success_criteria
