# OODA Loop for Autonomous Agents

## Overview

The OODA Loop (Observe-Orient-Decide-Act) is a decision-making framework originally developed for military strategy, adapted here for autonomous AI agents.

## The OODA Loop Phases

### Phase 1: OBSERVE

**Purpose:** Gather and process all available information

**Activities:**
- Process user input and context
- Check environment state
- Review recent interactions
- Recall relevant memories
- Monitor progress toward goals

**Implementation:**

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class Observation:
    """Captured observation from environment."""
    timestamp: datetime
    source: str  # user, system, sensor, memory
    data: Dict[str, any]
    priority: str = "normal"  # low, normal, high, critical

class ObservePhase:
    """OBSERVE phase of OODA loop."""

    def __init__(self):
        self.observations: List[Observation] = []
        self.current_state: Dict[str, any] = {}

    async def observe_user_input(self, message: str, context: Dict = None):
        """Observe user input."""
        obs = Observation(
            timestamp=datetime.now(),
            source="user",
            data={
                "message": message,
                "context": context or {},
                "intent": self._detect_intent(message),
            },
            priority="high",
        )
        self.observations.append(obs)
        return obs

    async def observe_system_state(self):
        """Observe current system state."""
        state = {
            "memory_usage": self._get_memory_usage(),
            "active_tasks": self._get_active_tasks(),
            "resource_availability": self._check_resources(),
        }

        obs = Observation(
            timestamp=datetime.now(),
            source="system",
            data=state,
            priority="normal",
        )
        self.observations.append(obs)
        return obs

    async def observe_goal_progress(self, goal_id: str):
        """Observe progress toward goal."""
        progress = {
            "goal_id": goal_id,
            "completion": self._calculate_completion(goal_id),
            "blockers": self._identify_blockers(goal_id),
            "next_steps": self._suggest_next_steps(goal_id),
        }

        obs = Observation(
            timestamp=datetime.now(),
            source="goal_tracker",
            data=progress,
            priority="high",
        )
        self.observations.append(obs)
        return obs

    def get_observation_summary(self) -> str:
        """Summarize recent observations."""
        recent = self.observations[-10:]  # Last 10 observations

        summary = "Recent Observations:\n"
        for obs in recent:
            summary += (
                f"- [{obs.priority.upper()}] {obs.source}: "
                f"{self._summarize_data(obs.data)}\n"
            )

        return summary

    def _detect_intent(self, message: str) -> str:
        """Detect user intent."""
        # Simple intent detection (use NLU in production)
        if any(word in message.lower() for word in ["help", "how", "what"]):
            return "question"
        elif any(word in message.lower() for word in ["do", "create", "make"]):
            return "task"
        return "statement"

    def _summarize_data(self, data: Dict) -> str:
        """Create brief summary of observation data."""
        if "message" in data:
            return data["message"][:50] + "..."
        return str(data)[:50]
```

### Phase 2: ORIENT

**Purpose:** Analyze observations and understand context

**Activities:**
- Identify patterns in observations
- Relate observations to goals
- Assess opportunities and obstacles
- Update mental model of situation

**Implementation:**

```python
@dataclass
class Orientation:
    """Analysis and understanding of situation."""
    timestamp: datetime
    situation_assessment: str
    key_insights: List[str]
    opportunities: List[str]
    obstacles: List[str]
    recommended_approach: str

class OrientPhase:
    """ORIENT phase of OODA loop."""

    def __init__(self, goal: str):
        self.goal = goal
        self.orientations: List[Orientation] = []

    async def orient(
        self,
        observations: List[Observation],
        agent: "LlmAgent",
    ) -> Orientation:
        """Analyze observations and understand situation."""

        # Prepare context for analysis
        context = self._prepare_analysis_context(observations)

        # Use LLM for orientation
        orientation_prompt = f"""
        Current Goal: {self.goal}

        Observations:
        {context}

        Analyze the situation:
        1. What is happening right now?
        2. How does this relate to the goal?
        3. What patterns do you observe?
        4. What opportunities exist?
        5. What obstacles are present?
        6. What is the optimal approach?

        Provide your analysis in structured format.
        """

        response = await agent.invoke(orientation_prompt)

        # Parse response into orientation
        orientation = self._parse_orientation(response)
        self.orientations.append(orientation)

        return orientation

    def _prepare_analysis_context(
        self,
        observations: List[Observation],
    ) -> str:
        """Prepare observation context for analysis."""
        context_parts = []

        for obs in observations[-5:]:  # Last 5 observations
            context_parts.append(
                f"- [{obs.source}] {obs.data}"
            )

        return "\n".join(context_parts)

    def _parse_orientation(self, llm_response: str) -> Orientation:
        """Parse LLM response into Orientation object."""
        # Simple parsing (use structured output in production)
        return Orientation(
            timestamp=datetime.now(),
            situation_assessment=llm_response[:200],
            key_insights=self._extract_insights(llm_response),
            opportunities=self._extract_opportunities(llm_response),
            obstacles=self._extract_obstacles(llm_response),
            recommended_approach=self._extract_approach(llm_response),
        )

    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from analysis."""
        # Simple extraction (use NLP in production)
        insights = []
        for line in text.split("\n"):
            if "insight" in line.lower() or "pattern" in line.lower():
                insights.append(line.strip())
        return insights

    def _extract_opportunities(self, text: str) -> List[str]:
        """Extract identified opportunities."""
        opportunities = []
        for line in text.split("\n"):
            if "opportunity" in line.lower() or "can" in line.lower():
                opportunities.append(line.strip())
        return opportunities

    def _extract_obstacles(self, text: str) -> List[str]:
        """Extract identified obstacles."""
        obstacles = []
        for line in text.split("\n"):
            if "obstacle" in line.lower() or "blocker" in line.lower():
                obstacles.append(line.strip())
        return obstacles

    def _extract_approach(self, text: str) -> str:
        """Extract recommended approach."""
        # Extract conclusion or recommendation
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if "recommend" in line.lower() or "approach" in line.lower():
                return "\n".join(lines[i:i+3])
        return lines[-1] if lines else ""
```

### Phase 3: DECIDE

**Purpose:** Select optimal action

**Activities:**
- Generate action options
- Evaluate each option
- Consider trade-offs
- Select best action
- Plan fallback

**Implementation:**

```python
@dataclass
class ActionOption:
    """Possible action to take."""
    action_id: str
    description: str
    expected_outcome: str
    estimated_cost: float  # time, resources
    success_probability: float
    risks: List[str]

@dataclass
class Decision:
    """Decision about what action to take."""
    timestamp: datetime
    selected_action: ActionOption
    rationale: str
    alternatives_considered: List[ActionOption]
    fallback_plan: Optional[ActionOption]

class DecidePhase:
    """DECIDE phase of OODA loop."""

    def __init__(self):
        self.decisions: List[Decision] = []

    async def decide(
        self,
        orientation: Orientation,
        available_actions: List[str],
        agent: "LlmAgent",
    ) -> Decision:
        """Select optimal action based on orientation."""

        # Generate action options
        options = await self._generate_options(
            orientation,
            available_actions,
            agent,
        )

        # Evaluate options
        evaluated_options = self._evaluate_options(options, orientation)

        # Select best option
        selected = self._select_best_option(evaluated_options)

        # Identify fallback
        fallback = self._select_fallback(evaluated_options, selected)

        # Create decision
        decision = Decision(
            timestamp=datetime.now(),
            selected_action=selected,
            rationale=self._generate_rationale(selected, orientation),
            alternatives_considered=evaluated_options,
            fallback_plan=fallback,
        )

        self.decisions.append(decision)
        return decision

    async def _generate_options(
        self,
        orientation: Orientation,
        available_actions: List[str],
        agent: "LlmAgent",
    ) -> List[ActionOption]:
        """Generate possible action options."""

        options_prompt = f"""
        Situation: {orientation.situation_assessment}

        Opportunities: {orientation.opportunities}
        Obstacles: {orientation.obstacles}

        Available actions: {', '.join(available_actions)}

        Generate 3-5 action options with:
        - Description
        - Expected outcome
        - Estimated effort
        - Success probability
        - Potential risks
        """

        response = await agent.invoke(options_prompt)

        # Parse into ActionOption objects
        return self._parse_action_options(response)

    def _evaluate_options(
        self,
        options: List[ActionOption],
        orientation: Orientation,
    ) -> List[ActionOption]:
        """Score and rank options."""

        for option in options:
            # Calculate score
            score = (
                option.success_probability * 0.5 +
                (1.0 - option.estimated_cost) * 0.3 +
                (1.0 - len(option.risks) * 0.1) * 0.2
            )
            option.score = score

        # Sort by score
        return sorted(options, key=lambda o: o.score, reverse=True)

    def _select_best_option(
        self,
        evaluated_options: List[ActionOption],
    ) -> ActionOption:
        """Select highest-scoring option."""
        return evaluated_options[0] if evaluated_options else None

    def _select_fallback(
        self,
        evaluated_options: List[ActionOption],
        selected: ActionOption,
    ) -> Optional[ActionOption]:
        """Select fallback option."""
        # Second-best option as fallback
        if len(evaluated_options) > 1:
            return evaluated_options[1]
        return None

    def _generate_rationale(
        self,
        selected: ActionOption,
        orientation: Orientation,
    ) -> str:
        """Generate explanation for decision."""
        return (
            f"Selected '{selected.description}' because: "
            f"{selected.expected_outcome}. "
            f"Success probability: {selected.success_probability:.0%}. "
            f"Aligns with: {orientation.recommended_approach}"
        )

    def _parse_action_options(self, llm_response: str) -> List[ActionOption]:
        """Parse LLM response into ActionOption objects."""
        # Simplified parsing
        options = []
        # In production, use structured output or JSON parsing
        return options
```

### Phase 4: ACT

**Purpose:** Execute selected action

**Activities:**
- Execute decision
- Use tools and resources
- Monitor execution
- Record results
- Handle errors

**Implementation:**

```python
@dataclass
class ActionResult:
    """Result of action execution."""
    action_id: str
    success: bool
    outcome: str
    duration: float
    resources_used: Dict[str, float]
    errors: List[str]
    side_effects: List[str]

class ActPhase:
    """ACT phase of OODA loop."""

    def __init__(self):
        self.action_results: List[ActionResult] = []

    async def act(
        self,
        decision: Decision,
        agent: "LlmAgent",
    ) -> ActionResult:
        """Execute selected action."""

        action = decision.selected_action
        start_time = datetime.now()

        try:
            # Execute action
            outcome = await self._execute_action(action, agent)

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            # Record result
            result = ActionResult(
                action_id=action.action_id,
                success=True,
                outcome=outcome,
                duration=duration,
                resources_used=self._calculate_resources_used(action),
                errors=[],
                side_effects=[],
            )

        except Exception as e:
            # Action failed - try fallback
            if decision.fallback_plan:
                result = await self._execute_fallback(
                    decision.fallback_plan,
                    agent,
                    str(e),
                )
            else:
                # No fallback - record failure
                result = ActionResult(
                    action_id=action.action_id,
                    success=False,
                    outcome=f"Failed: {str(e)}",
                    duration=(datetime.now() - start_time).total_seconds(),
                    resources_used={},
                    errors=[str(e)],
                    side_effects=[],
                )

        self.action_results.append(result)
        return result

    async def _execute_action(
        self,
        action: ActionOption,
        agent: "LlmAgent",
    ) -> str:
        """Execute the action."""
        # Invoke agent with action
        prompt = f"Execute action: {action.description}"
        result = await agent.invoke(prompt)
        return result

    async def _execute_fallback(
        self,
        fallback: ActionOption,
        agent: "LlmAgent",
        original_error: str,
    ) -> ActionResult:
        """Execute fallback action."""
        start_time = datetime.now()

        try:
            outcome = await self._execute_action(fallback, agent)

            return ActionResult(
                action_id=fallback.action_id,
                success=True,
                outcome=f"Fallback succeeded: {outcome}",
                duration=(datetime.now() - start_time).total_seconds(),
                resources_used={},
                errors=[f"Original action failed: {original_error}"],
                side_effects=["Used fallback plan"],
            )

        except Exception as e:
            return ActionResult(
                action_id=fallback.action_id,
                success=False,
                outcome=f"Fallback also failed: {str(e)}",
                duration=(datetime.now() - start_time).total_seconds(),
                resources_used={},
                errors=[original_error, str(e)],
                side_effects=[],
            )

    def _calculate_resources_used(self, action: ActionOption) -> Dict[str, float]:
        """Calculate resources consumed by action."""
        return {
            "time": action.estimated_cost,
            "api_calls": 1,
        }
```

### Phase 5: REFLECT (Loop Back)

**Purpose:** Evaluate outcomes and adapt

**Activities:**
- Assess action results
- Compare to expectations
- Identify learnings
- Update approach
- Loop back to OBSERVE

**Implementation:**

```python
@dataclass
class Reflection:
    """Reflection on action outcomes."""
    timestamp: datetime
    action_evaluated: str
    expected_outcome: str
    actual_outcome: str
    success_assessment: bool
    learnings: List[str]
    adaptations: List[str]

class ReflectPhase:
    """REFLECT phase - evaluate and loop back."""

    def __init__(self):
        self.reflections: List[Reflection] = []

    async def reflect(
        self,
        decision: Decision,
        result: ActionResult,
        agent: "LlmAgent",
    ) -> Reflection:
        """Reflect on action outcomes."""

        # Prepare reflection prompt
        reflection_prompt = f"""
        Action taken: {decision.selected_action.description}
        Expected outcome: {decision.selected_action.expected_outcome}
        Actual outcome: {result.outcome}
        Success: {result.success}

        Reflect on this action:
        1. Did it achieve the intended outcome?
        2. What went well?
        3. What could be improved?
        4. What did we learn?
        5. How should we adapt our approach?
        """

        response = await agent.invoke(reflection_prompt)

        # Parse reflection
        reflection = Reflection(
            timestamp=datetime.now(),
            action_evaluated=decision.selected_action.description,
            expected_outcome=decision.selected_action.expected_outcome,
            actual_outcome=result.outcome,
            success_assessment=result.success,
            learnings=self._extract_learnings(response),
            adaptations=self._extract_adaptations(response),
        )

        self.reflections.append(reflection)
        return reflection

    def _extract_learnings(self, text: str) -> List[str]:
        """Extract learnings from reflection."""
        learnings = []
        for line in text.split("\n"):
            if "learn" in line.lower() or "insight" in line.lower():
                learnings.append(line.strip())
        return learnings

    def _extract_adaptations(self, text: str) -> List[str]:
        """Extract suggested adaptations."""
        adaptations = []
        for line in text.split("\n"):
            if "adapt" in line.lower() or "improve" in line.lower():
                adaptations.append(line.strip())
        return adaptations

    def get_reflection_summary(self) -> str:
        """Summarize recent reflections."""
        recent = self.reflections[-5:]

        summary = "Recent Reflections:\n"
        for refl in recent:
            summary += (
                f"- {refl.action_evaluated}: "
                f"{'Success' if refl.success_assessment else 'Failed'}\n"
            )
            if refl.learnings:
                summary += f"  Learned: {refl.learnings[0]}\n"

        return summary
```

## Complete OODA Loop Integration

```python
class OODALoop:
    """Complete OODA Loop for autonomous agent."""

    def __init__(self, agent: "LlmAgent", goal: str):
        self.agent = agent
        self.goal = goal

        # Phase managers
        self.observe = ObservePhase()
        self.orient = OrientPhase(goal=goal)
        self.decide = DecidePhase()
        self.act = ActPhase()
        self.reflect = ReflectPhase()

        # Cycle counter
        self.cycle_count = 0

    async def run_cycle(
        self,
        trigger: str,
        available_actions: List[str],
    ) -> dict:
        """Run one complete OODA cycle."""

        self.cycle_count += 1

        # Phase 1: OBSERVE
        await self.observe.observe_user_input(trigger)
        await self.observe.observe_system_state()
        await self.observe.observe_goal_progress(self.goal)

        # Phase 2: ORIENT
        orientation = await self.orient.orient(
            observations=self.observe.observations,
            agent=self.agent,
        )

        # Phase 3: DECIDE
        decision = await self.decide.decide(
            orientation=orientation,
            available_actions=available_actions,
            agent=self.agent,
        )

        # Phase 4: ACT
        result = await self.act.act(
            decision=decision,
            agent=self.agent,
        )

        # Phase 5: REFLECT
        reflection = await self.reflect.reflect(
            decision=decision,
            result=result,
            agent=self.agent,
        )

        return {
            "cycle": self.cycle_count,
            "orientation": orientation,
            "decision": decision,
            "result": result,
            "reflection": reflection,
        }

    def get_loop_summary(self) -> str:
        """Get summary of OODA loop activity."""
        return f"""
OODA Loop Summary:
Cycles completed: {self.cycle_count}
Goal: {self.goal}

{self.observe.get_observation_summary()}

{self.reflect.get_reflection_summary()}
"""
```

## Usage Example

```python
from google.adk.agents import LlmAgent

# Create agent
agent = LlmAgent(
    name="autonomous_agent",
    model="gemini-2.5-flash",
)

# Create OODA loop
loop = OODALoop(
    agent=agent,
    goal="Complete user tasks efficiently",
)

# Run cycle
cycle_result = await loop.run_cycle(
    trigger="User needs help with Python",
    available_actions=["search_web", "write_code", "explain_concept"],
)

# Check results
print(f"Orientation: {cycle_result['orientation'].situation_assessment}")
print(f"Decision: {cycle_result['decision'].selected_action.description}")
print(f"Result: {cycle_result['result'].outcome}")
print(f"Learnings: {cycle_result['reflection'].learnings}")
```

## Best Practices

1. **Fast Cycles:** Run OODA loops quickly to adapt rapidly
2. **Continuous Observation:** Never stop observing the environment
3. **Mental Model Updates:** Keep orientation current with new information
4. **Decision Confidence:** Track confidence in decisions
5. **Action Monitoring:** Watch execution closely
6. **Learning Integration:** Apply reflections to future cycles
7. **Interrupt Handling:** Allow new observations to interrupt current cycle
8. **Parallel Loops:** Run multiple OODA loops for different sub-goals
