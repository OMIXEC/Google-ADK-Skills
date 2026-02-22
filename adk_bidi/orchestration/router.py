"""
IntentRouter - Intent-based routing to specialist agents.

Provides intelligent routing of requests to appropriate agents
based on intent classification and context.
"""

from typing import Optional, List, Any, Dict, Callable, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

from google.adk.agents import Agent
from google.adk.tools import AgentTool, FunctionTool

from adk_bidi.memory.shared_memory import SharedMemory
from adk_bidi.memory.working_memory import WorkingMemory
from adk_bidi.agents.bidi_agent import BidiAgent


# Native audio model for real-time streaming
LIVE_MODEL = "gemini-live-2.5-flash-native-audio"


@dataclass
class IntentPattern:
    """Pattern for matching user intent."""
    name: str
    patterns: List[str]  # Regex patterns
    keywords: List[str]  # Keywords to match
    priority: int = 0
    examples: List[str] = field(default_factory=list)


@dataclass
class RoutingDecision:
    """Result of routing decision."""
    agent_name: str
    intent: str
    confidence: float
    reasoning: str
    fallback: Optional[str] = None


@dataclass
class RouteConfig:
    """Configuration for a route."""
    agent: Union[Agent, BidiAgent]
    intents: List[IntentPattern]
    fallback: bool = False
    priority: int = 0


class IntentRouter:
    """
    Intent-based router for directing requests to agents.

    Routes user requests to appropriate specialist agents based
    on intent classification, keywords, and patterns.

    Example:
        router = IntentRouter()
        router.add_route(
            agent=technical_support,
            intents=[IntentPattern(name="tech_help", keywords=["error", "bug", "broken"])],
        )
        agent = await router.route("My app shows an error")
    """

    def __init__(
        self,
        shared_memory: Optional[SharedMemory] = None,
        working_memory: Optional[WorkingMemory] = None,
        enable_llm_routing: bool = True,
        model: str = LIVE_MODEL,
        fallback_agent: Optional[Union[Agent, BidiAgent]] = None,
    ):
        """
        Initialize the intent router.

        Args:
            shared_memory: Shared memory for context
            working_memory: Working memory for routing history
            enable_llm_routing: Use LLM for complex routing decisions
            model: LLM model for routing decisions
            fallback_agent: Agent to use when no route matches
        """
        self.shared_memory = shared_memory or SharedMemory()
        self.working_memory = working_memory or WorkingMemory()
        self.enable_llm_routing = enable_llm_routing
        self.model = model

        self.routes: Dict[str, RouteConfig] = {}
        self.fallback_agent = fallback_agent
        self.routing_history: List[RoutingDecision] = []

        # Create routing agent for LLM-based decisions
        self.routing_agent: Optional[Agent] = None
        if enable_llm_routing:
            self._create_routing_agent()

    def _create_routing_agent(self) -> None:
        """Create LLM agent for complex routing decisions."""
        self.routing_agent = Agent(
            name="router",
            model=self.model,
            description="Routes requests to appropriate specialist agents",
            instruction="""You are a routing agent that determines which specialist agent should handle a request.

Analyze the user's request and return a JSON response with:
- agent_name: The name of the agent to handle this request
- intent: The classified intent
- confidence: Your confidence level (0.0 to 1.0)
- reasoning: Brief explanation of your decision

Consider:
- The specific needs expressed in the request
- Keywords and context that indicate intent
- Previous routing history for this session
- Which agent is best equipped to help

Always route to the most specific agent that can help.""",
            tools=[
                FunctionTool(self.get_available_agents),
                FunctionTool(self.get_routing_history),
            ],
        )

    def add_route(
        self,
        agent: Union[Agent, BidiAgent],
        intents: List[IntentPattern],
        is_fallback: bool = False,
        priority: int = 0,
    ) -> None:
        """
        Add a routing configuration.

        Args:
            agent: Agent to route to
            intents: Intent patterns that trigger this route
            is_fallback: Whether this is a fallback route
            priority: Priority for conflict resolution
        """
        name = agent.name if isinstance(agent, BidiAgent) else agent.name

        self.routes[name] = RouteConfig(
            agent=agent,
            intents=intents,
            fallback=is_fallback,
            priority=priority,
        )

        if is_fallback:
            self.fallback_agent = agent

        # Update routing agent instruction
        if self.enable_llm_routing:
            self._update_routing_instruction()

    def _update_routing_instruction(self) -> None:
        """Update routing agent with current routes."""
        route_descriptions = []
        for name, config in self.routes.items():
            agent = config.agent
            if isinstance(agent, BidiAgent):
                desc = agent.description
            else:
                desc = getattr(agent, 'description', f"Agent: {name}")

            intent_names = [i.name for i in config.intents]
            route_descriptions.append(
                f"- **{name}**: {desc}\n  Intents: {', '.join(intent_names)}"
            )

        routes_text = "\n".join(route_descriptions)

        self.routing_agent = Agent(
            name="router",
            model=self.model,
            description="Routes requests to appropriate specialist agents",
            instruction=f"""You are a routing agent. Analyze requests and route to the appropriate agent.

**Available Agents:**
{routes_text}

Return your routing decision as structured output.""",
            tools=[
                FunctionTool(self.get_available_agents),
                FunctionTool(self.get_routing_history),
            ],
        )

    def _pattern_match(self, text: str) -> Optional[Tuple[str, IntentPattern, float]]:
        """Match text against intent patterns."""
        text_lower = text.lower()
        best_match = None
        best_score = 0.0

        for name, config in self.routes.items():
            for intent in config.intents:
                score = 0.0

                # Keyword matching
                keyword_matches = sum(
                    1 for kw in intent.keywords
                    if kw.lower() in text_lower
                )
                if intent.keywords:
                    score += (keyword_matches / len(intent.keywords)) * 0.5

                # Pattern matching
                for pattern in intent.patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        score += 0.5
                        break

                # Add priority bonus
                score += config.priority * 0.1

                if score > best_score:
                    best_score = score
                    best_match = (name, intent, score)

        return best_match if best_match and best_match[2] > 0.2 else None

    async def route(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        force_agent: Optional[str] = None,
    ) -> Tuple[Union[Agent, BidiAgent], RoutingDecision]:
        """
        Route a request to the appropriate agent.

        Args:
            user_input: User's request
            context: Optional additional context
            force_agent: Force routing to specific agent

        Returns:
            Tuple of (agent, routing_decision)
        """
        # Force specific agent
        if force_agent and force_agent in self.routes:
            decision = RoutingDecision(
                agent_name=force_agent,
                intent="forced",
                confidence=1.0,
                reasoning="Explicitly requested agent",
            )
            agent = self.routes[force_agent].agent
            self._record_decision(decision)
            return agent, decision

        # Try pattern matching first
        pattern_result = self._pattern_match(user_input)

        if pattern_result and pattern_result[2] >= 0.5:
            name, intent, confidence = pattern_result
            decision = RoutingDecision(
                agent_name=name,
                intent=intent.name,
                confidence=confidence,
                reasoning=f"Pattern match on intent: {intent.name}",
            )
            agent = self.routes[name].agent
            self._record_decision(decision)
            return agent, decision

        # Fall back to LLM routing if enabled
        if self.enable_llm_routing and self.routing_agent:
            # Store context for routing agent
            self.working_memory.add(
                key="routing_request",
                value=user_input,
                importance=0.8,
            )

            # Return routing agent for external execution
            decision = RoutingDecision(
                agent_name="router",
                intent="llm_routing",
                confidence=0.7,
                reasoning="Using LLM for complex routing decision",
            )
            self._record_decision(decision)
            return self.routing_agent, decision

        # Use fallback agent
        if self.fallback_agent:
            decision = RoutingDecision(
                agent_name=self.fallback_agent.name if isinstance(self.fallback_agent, BidiAgent) else self.fallback_agent.name,
                intent="fallback",
                confidence=0.3,
                reasoning="No specific route matched, using fallback",
            )
            self._record_decision(decision)
            return self.fallback_agent, decision

        raise ValueError("No route found and no fallback configured")

    def _record_decision(self, decision: RoutingDecision) -> None:
        """Record routing decision in history."""
        self.routing_history.append(decision)

        # Keep last 50 decisions
        if len(self.routing_history) > 50:
            self.routing_history = self.routing_history[-50:]

        # Store in working memory
        self.working_memory.add(
            key=f"route_{len(self.routing_history)}",
            value=f"{decision.intent} -> {decision.agent_name}",
            importance=0.5,
        )

    # Tools for routing agent

    def get_available_agents(self) -> str:
        """
        Get list of available agents for routing.

        Returns:
            Formatted list of agents
        """
        lines = ["Available Agents:"]
        for name, config in self.routes.items():
            agent = config.agent
            if isinstance(agent, BidiAgent):
                desc = agent.description
            else:
                desc = getattr(agent, 'description', 'No description')

            intents = [i.name for i in config.intents]
            lines.append(f"- {name}: {desc}")
            lines.append(f"  Handles: {', '.join(intents)}")

        return "\n".join(lines)

    def get_routing_history(self, limit: int = 5) -> str:
        """
        Get recent routing history.

        Args:
            limit: Maximum entries to return

        Returns:
            Formatted routing history
        """
        if not self.routing_history:
            return "No routing history yet."

        history = self.routing_history[-limit:]
        lines = ["Recent Routing:"]

        for decision in history:
            lines.append(
                f"- {decision.intent} -> {decision.agent_name} "
                f"(confidence: {decision.confidence:.2f})"
            )

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        route_counts = {}
        for decision in self.routing_history:
            route_counts[decision.agent_name] = route_counts.get(decision.agent_name, 0) + 1

        return {
            "total_routes": len(self.routes),
            "total_decisions": len(self.routing_history),
            "route_distribution": route_counts,
            "llm_routing_enabled": self.enable_llm_routing,
            "has_fallback": self.fallback_agent is not None,
        }


class ContextualRouter(IntentRouter):
    """
    Router with enhanced context awareness.

    Considers conversation history, user preferences, and
    session context for routing decisions.
    """

    def __init__(self, context_window: int = 5, **kwargs):
        """
        Initialize contextual router.

        Args:
            context_window: Number of previous turns to consider
            **kwargs: Arguments for IntentRouter
        """
        super().__init__(**kwargs)
        self.context_window = context_window
        self.conversation_context: List[Dict[str, str]] = []

    async def route(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        force_agent: Optional[str] = None,
    ) -> Tuple[Union[Agent, BidiAgent], RoutingDecision]:
        """Route with conversation context."""
        # Add to conversation context
        self.conversation_context.append({
            "input": user_input,
            "timestamp": datetime.now().isoformat(),
        })

        # Trim context window
        if len(self.conversation_context) > self.context_window:
            self.conversation_context = self.conversation_context[-self.context_window:]

        # Build enhanced context
        enhanced_context = context or {}
        enhanced_context["conversation_history"] = self.conversation_context

        # Check for context continuation
        if len(self.routing_history) > 0:
            last_decision = self.routing_history[-1]
            # If previous agent handled similar intent, prefer continuity
            if last_decision.confidence > 0.7:
                enhanced_context["previous_agent"] = last_decision.agent_name

        return await super().route(user_input, enhanced_context, force_agent)


class PriorityRouter(IntentRouter):
    """
    Router with priority-based selection.

    When multiple routes match, selects based on priority
    and load balancing considerations.
    """

    def __init__(self, enable_load_balancing: bool = True, **kwargs):
        """
        Initialize priority router.

        Args:
            enable_load_balancing: Enable load-based routing
            **kwargs: Arguments for IntentRouter
        """
        super().__init__(**kwargs)
        self.enable_load_balancing = enable_load_balancing
        self.agent_load: Dict[str, int] = {}

    def _pattern_match(self, text: str) -> Optional[Tuple[str, IntentPattern, float]]:
        """Match with priority and load consideration."""
        result = super()._pattern_match(text)

        if result and self.enable_load_balancing:
            name, intent, score = result

            # Adjust score based on current load
            current_load = self.agent_load.get(name, 0)
            if current_load > 5:
                # Look for alternative routes with lower load
                for alt_name, config in self.routes.items():
                    if alt_name != name:
                        alt_load = self.agent_load.get(alt_name, 0)
                        if alt_load < current_load - 2:
                            # Check if alternative can handle this
                            for alt_intent in config.intents:
                                if any(kw in text.lower() for kw in alt_intent.keywords):
                                    return (alt_name, alt_intent, score * 0.9)

        return result

    async def route(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        force_agent: Optional[str] = None,
    ) -> Tuple[Union[Agent, BidiAgent], RoutingDecision]:
        """Route with load tracking."""
        agent, decision = await super().route(user_input, context, force_agent)

        # Update load tracking
        self.agent_load[decision.agent_name] = self.agent_load.get(decision.agent_name, 0) + 1

        return agent, decision

    def release_agent(self, agent_name: str) -> None:
        """Release agent after task completion."""
        if agent_name in self.agent_load:
            self.agent_load[agent_name] = max(0, self.agent_load[agent_name] - 1)

    def get_load_stats(self) -> Dict[str, int]:
        """Get current load distribution."""
        return dict(self.agent_load)
