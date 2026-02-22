# Goal-Driven Planning for Autonomous Agents

## Overview

Goal-backward planning enables autonomous agents to decompose high-level goals into actionable sub-goals and tasks, then execute them systematically.

## Goal Hierarchy

```
Primary Goal
├── Sub-Goal 1
│   ├── Task 1.1
│   ├── Task 1.2
│   └── Task 1.3
├── Sub-Goal 2
│   ├── Task 2.1
│   └── Task 2.2
└── Sub-Goal 3
```

## Goal Model

```python
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum

class GoalStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class GoalPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Goal:
    """Represents a goal with sub-goals."""
    goal_id: str
    description: str
    success_criteria: List[str]
    status: GoalStatus = GoalStatus.PENDING
    priority: GoalPriority = GoalPriority.MEDIUM
    deadline: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0

    # Hierarchy
    parent_goal: Optional['Goal'] = None
    sub_goals: List['Goal'] = field(default_factory=list)

    # Planning
    planned_steps: List[str] = field(default_factory=list)
    completed_steps: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    blocked_by: List[str] = field(default_factory=list)

    def is_leaf(self) -> bool:
        """Check if goal is leaf (no sub-goals)."""
        return len(self.sub_goals) == 0

    def is_root(self) -> bool:
        """Check if goal is root (no parent)."""
        return self.parent_goal is None

    def add_sub_goal(self, sub_goal: 'Goal'):
        """Add sub-goal to this goal."""
        sub_goal.parent_goal = self
        self.sub_goals.append(sub_goal)

    def calculate_progress(self) -> float:
        """Calculate goal progress from sub-goals."""
        if self.is_leaf():
            # Leaf goal progress is based on completed steps
            if not self.planned_steps:
                return 0.0
            return len(self.completed_steps) / len(self.planned_steps)
        else:
            # Parent goal progress is average of sub-goals
            if not self.sub_goals:
                return 0.0
            sub_progress = [sg.calculate_progress() for sg in self.sub_goals]
            return sum(sub_progress) / len(sub_progress)

    def is_ready_to_start(self) -> bool:
        """Check if goal can be started."""
        # Goal must be pending and not blocked
        if self.status != GoalStatus.PENDING:
            return False

        if self.blocked_by:
            return False

        # Parent must be in progress
        if self.parent_goal and self.parent_goal.status != GoalStatus.IN_PROGRESS:
            return False

        return True

    def is_complete(self) -> bool:
        """Check if goal is complete."""
        if self.is_leaf():
            # Leaf goal complete if all steps done
            return (
                len(self.completed_steps) == len(self.planned_steps) and
                len(self.planned_steps) > 0
            )
        else:
            # Parent goal complete if all sub-goals complete
            return all(sg.status == GoalStatus.COMPLETED for sg in self.sub_goals)

    def mark_step_complete(self, step: str):
        """Mark a planned step as complete."""
        if step in self.planned_steps and step not in self.completed_steps:
            self.completed_steps.append(step)
            self.progress = self.calculate_progress()

    def start(self):
        """Start goal execution."""
        self.status = GoalStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self):
        """Mark goal as complete."""
        self.status = GoalStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 1.0

    def block(self, reason: str):
        """Block goal with reason."""
        self.status = GoalStatus.BLOCKED
        if reason not in self.blocked_by:
            self.blocked_by.append(reason)

    def unblock(self, reason: str):
        """Unblock goal."""
        if reason in self.blocked_by:
            self.blocked_by.remove(reason)

        if not self.blocked_by:
            self.status = GoalStatus.IN_PROGRESS
```

## Goal Decomposition

```python
class GoalDecomposer:
    """Decompose high-level goals into actionable sub-goals."""

    def __init__(self, agent: "LlmAgent"):
        self.agent = agent

    async def decompose_goal(self, goal: Goal, max_depth: int = 3) -> Goal:
        """Recursively decompose goal into sub-goals."""

        # Don't decompose if already at max depth
        depth = self._calculate_depth(goal)
        if depth >= max_depth:
            return goal

        # Use LLM to generate sub-goals
        decomposition_prompt = f"""
        Goal: {goal.description}
        Success Criteria: {', '.join(goal.success_criteria)}

        Break this goal into 3-5 concrete sub-goals.
        Each sub-goal should be:
        1. Specific and measurable
        2. Independently achievable
        3. Contribute to the parent goal

        Format:
        Sub-goal 1: [description]
        Success: [criterion]

        Sub-goal 2: [description]
        Success: [criterion]
        """

        response = await self.agent.invoke(decomposition_prompt)

        # Parse sub-goals from response
        sub_goals = self._parse_sub_goals(response, goal)

        # Add to goal hierarchy
        for sub_goal in sub_goals:
            goal.add_sub_goal(sub_goal)

            # Recursively decompose if needed
            if self._should_decompose_further(sub_goal):
                await self.decompose_goal(sub_goal, max_depth)

        return goal

    def _calculate_depth(self, goal: Goal) -> int:
        """Calculate depth of goal in hierarchy."""
        depth = 0
        current = goal
        while current.parent_goal:
            depth += 1
            current = current.parent_goal
        return depth

    def _parse_sub_goals(self, llm_response: str, parent: Goal) -> List[Goal]:
        """Parse LLM response into sub-goals."""
        sub_goals = []

        # Simple parsing (use structured output in production)
        lines = llm_response.split("\n")
        current_description = None
        current_criteria = []

        for line in lines:
            line = line.strip()

            if line.startswith("Sub-goal"):
                if current_description:
                    # Create previous sub-goal
                    sub_goal = Goal(
                        goal_id=f"{parent.goal_id}.{len(sub_goals) + 1}",
                        description=current_description,
                        success_criteria=current_criteria,
                        priority=parent.priority,
                    )
                    sub_goals.append(sub_goal)

                # Start new sub-goal
                current_description = line.split(":", 1)[1].strip()
                current_criteria = []

            elif line.startswith("Success:"):
                criterion = line.split(":", 1)[1].strip()
                current_criteria.append(criterion)

        # Add final sub-goal
        if current_description:
            sub_goal = Goal(
                goal_id=f"{parent.goal_id}.{len(sub_goals) + 1}",
                description=current_description,
                success_criteria=current_criteria,
                priority=parent.priority,
            )
            sub_goals.append(sub_goal)

        return sub_goals

    def _should_decompose_further(self, goal: Goal) -> bool:
        """Determine if goal should be decomposed further."""
        # Decompose if goal is still high-level (>100 chars)
        if len(goal.description) > 100:
            return True

        # Decompose if goal has complex success criteria
        if len(goal.success_criteria) > 3:
            return True

        return False
```

## Task Planning

```python
class TaskPlanner:
    """Plan concrete tasks to achieve goals."""

    def __init__(self, agent: "LlmAgent"):
        self.agent = agent

    async def plan_tasks(self, goal: Goal) -> Goal:
        """Plan step-by-step tasks for goal."""

        planning_prompt = f"""
        Goal: {goal.description}
        Success Criteria: {', '.join(goal.success_criteria)}

        Create a step-by-step plan to achieve this goal.
        Include:
        1. Prerequisites/dependencies
        2. Concrete actions to take
        3. Verification steps
        4. Expected outcomes

        Format as numbered list:
        1. [action]
        2. [action]
        3. [action]
        """

        response = await self.agent.invoke(planning_prompt)

        # Parse tasks
        tasks = self._parse_tasks(response)
        goal.planned_steps = tasks

        return goal

    def _parse_tasks(self, llm_response: str) -> List[str]:
        """Parse tasks from LLM response."""
        tasks = []

        for line in llm_response.split("\n"):
            line = line.strip()

            # Match numbered lists: "1.", "2)", etc.
            if line and line[0].isdigit():
                # Remove number prefix
                task = line.split(".", 1)[-1].strip()
                if task:
                    tasks.append(task)

        return tasks

    async def replan(self, goal: Goal, reason: str) -> Goal:
        """Replan goal due to changed circumstances."""

        replan_prompt = f"""
        Original Goal: {goal.description}
        Original Plan: {goal.planned_steps}
        Completed Steps: {goal.completed_steps}

        Reason for Replanning: {reason}

        Create an updated plan that:
        1. Preserves completed work
        2. Addresses the issue: {reason}
        3. Gets us back on track toward the goal

        Provide updated step-by-step plan.
        """

        response = await self.agent.invoke(replan_prompt)

        # Update plan
        new_tasks = self._parse_tasks(response)
        goal.planned_steps = new_tasks

        return goal
```

## Goal Execution Engine

```python
class GoalExecutor:
    """Execute goals using goal-backward planning."""

    def __init__(self, agent: "LlmAgent"):
        self.agent = agent
        self.decomposer = GoalDecomposer(agent)
        self.planner = TaskPlanner(agent)
        self.current_goal: Optional[Goal] = None
        self.goal_stack: List[Goal] = []

    async def execute_goal(self, goal: Goal) -> bool:
        """Execute goal and all sub-goals."""

        # 1. Decompose into sub-goals
        await self.decomposer.decompose_goal(goal)

        # 2. Execute using depth-first approach
        success = await self._execute_recursive(goal)

        return success

    async def _execute_recursive(self, goal: Goal) -> bool:
        """Recursively execute goal and sub-goals."""

        # Start goal
        goal.start()
        self.current_goal = goal
        self.goal_stack.append(goal)

        try:
            if goal.is_leaf():
                # Leaf goal - plan and execute tasks
                await self.planner.plan_tasks(goal)
                success = await self._execute_tasks(goal)
            else:
                # Parent goal - execute sub-goals
                success = await self._execute_sub_goals(goal)

            # Mark complete if successful
            if success:
                goal.complete()
            else:
                goal.status = GoalStatus.FAILED

            return success

        except Exception as e:
            goal.block(str(e))
            return False

        finally:
            self.goal_stack.pop()
            self.current_goal = self.goal_stack[-1] if self.goal_stack else None

    async def _execute_tasks(self, goal: Goal) -> bool:
        """Execute planned tasks for leaf goal."""

        for i, task in enumerate(goal.planned_steps):
            # Execute task
            task_prompt = f"""
            Current Goal: {goal.description}
            Task: {task}
            Previous Steps: {goal.completed_steps}

            Execute this task and report the result.
            """

            try:
                result = await self.agent.invoke(task_prompt)

                # Verify success
                if await self._verify_task_success(task, result, goal):
                    goal.mark_step_complete(task)
                else:
                    # Task failed - consider replanning
                    if await self._should_replan(goal, task):
                        await self.planner.replan(goal, f"Task {i+1} failed")
                        return await self._execute_tasks(goal)  # Retry with new plan
                    else:
                        return False

            except Exception as e:
                goal.block(f"Task failed: {str(e)}")
                return False

        return True

    async def _execute_sub_goals(self, goal: Goal) -> bool:
        """Execute all sub-goals."""

        for sub_goal in goal.sub_goals:
            # Execute sub-goal recursively
            success = await self._execute_recursive(sub_goal)

            if not success:
                # Sub-goal failed - entire goal fails
                return False

            # Update parent progress
            goal.progress = goal.calculate_progress()

        return True

    async def _verify_task_success(
        self,
        task: str,
        result: str,
        goal: Goal,
    ) -> bool:
        """Verify if task completed successfully."""

        verification_prompt = f"""
        Task: {task}
        Result: {result}
        Goal Success Criteria: {', '.join(goal.success_criteria)}

        Did this task succeed? Answer yes or no and explain why.
        """

        response = await self.agent.invoke(verification_prompt)

        return "yes" in response.lower()

    async def _should_replan(self, goal: Goal, failed_task: str) -> bool:
        """Determine if goal should be replanned."""

        # Replan if less than 50% complete
        if goal.progress < 0.5:
            return True

        # Don't replan if near completion
        if goal.progress > 0.8:
            return False

        # Use LLM to decide
        decision_prompt = f"""
        Goal: {goal.description}
        Progress: {goal.progress:.0%}
        Failed Task: {failed_task}

        Should we create a new plan or continue with the current one?
        Answer: replan or continue
        """

        response = await self.agent.invoke(decision_prompt)
        return "replan" in response.lower()

    def get_execution_status(self) -> dict:
        """Get current execution status."""
        if not self.current_goal:
            return {"status": "idle"}

        return {
            "status": "executing",
            "current_goal": self.current_goal.description,
            "progress": self.current_goal.progress,
            "goal_stack_depth": len(self.goal_stack),
            "completed_steps": len(self.current_goal.completed_steps),
            "total_steps": len(self.current_goal.planned_steps),
        }
```

## Usage Example

```python
from google.adk.agents import LlmAgent

# Create agent
agent = LlmAgent(
    name="goal_driven_agent",
    model="gemini-2.5-flash",
)

# Define primary goal
primary_goal = Goal(
    goal_id="research_project",
    description="Research and write comprehensive report on AI trends",
    success_criteria=[
        "Report covers major trends in AI",
        "At least 10 credible sources cited",
        "Actionable insights provided",
        "Report is well-structured and readable",
    ],
    priority=GoalPriority.HIGH,
    deadline=datetime.now() + timedelta(days=7),
)

# Create executor
executor = GoalExecutor(agent)

# Execute goal
success = await executor.execute_goal(primary_goal)

# Check results
if success:
    print(f"Goal completed successfully!")
    print(f"Progress: {primary_goal.progress:.0%}")
    print(f"Completed in: {primary_goal.completed_at - primary_goal.created_at}")
else:
    print(f"Goal failed or blocked")
    print(f"Blocked by: {primary_goal.blocked_by}")
    print(f"Progress: {primary_goal.progress:.0%}")
```

## Proactive Goal Setting

```python
class ProactiveGoalGenerator:
    """Generate goals proactively based on context."""

    def __init__(self, agent: "LlmAgent"):
        self.agent = agent

    async def suggest_goals(
        self,
        context: str,
        user_history: List[dict],
    ) -> List[Goal]:
        """Suggest goals based on context and user history."""

        suggestion_prompt = f"""
        Context: {context}
        User History: {self._summarize_history(user_history)}

        Suggest 3 goals that would be helpful based on this context.
        Goals should be:
        1. Relevant to current situation
        2. Anticipate user needs
        3. Actionable by the agent

        Format:
        Goal 1: [description]
        Success: [criteria]
        Priority: [low|medium|high]
        """

        response = await self.agent.invoke(suggestion_prompt)

        # Parse suggested goals
        goals = self._parse_suggested_goals(response)

        return goals

    def _summarize_history(self, history: List[dict]) -> str:
        """Summarize user history."""
        if not history:
            return "No previous interactions"

        recent = history[-5:]
        summary = ", ".join([h.get("action", "") for h in recent])
        return f"Recent actions: {summary}"

    def _parse_suggested_goals(self, llm_response: str) -> List[Goal]:
        """Parse suggested goals from LLM response."""
        goals = []
        # Simplified parsing
        # In production, use structured output
        return goals
```

## Best Practices

1. **Clear Success Criteria:** Define measurable success criteria for each goal
2. **Appropriate Decomposition:** Break goals into 3-5 sub-goals per level
3. **Adaptive Planning:** Replan when circumstances change
4. **Progress Tracking:** Update progress frequently
5. **Dependency Management:** Track and resolve blockers
6. **Priority-Based Execution:** Execute high-priority goals first
7. **Deadline Awareness:** Monitor deadlines and adjust plans
8. **Verification:** Verify task completion against success criteria
