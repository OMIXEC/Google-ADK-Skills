# Adaptive Agent Example

## Complete Adaptive Agent Implementation

This example demonstrates a production-ready adaptive agent that learns user preferences and provides personalized experiences.

## Full Implementation

```python
from google.adk.agents import LlmAgent
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
import json

# ============================================================================
# MEMORY MODELS
# ============================================================================

@dataclass
class UserPreference:
    """A learned user preference."""
    category: str
    preference: str
    confidence: float
    evidence: List[str]
    learned_at: datetime
    last_confirmed: datetime
    confirmation_count: int = 0

    def reinforce(self, observation: str):
        self.confidence = min(1.0, self.confidence + 0.1)
        self.evidence.append(observation)
        self.last_confirmed = datetime.now()
        self.confirmation_count += 1

    def decay(self, decay_rate: float = 0.05):
        self.confidence = max(0.0, self.confidence - decay_rate)

@dataclass
class Episode:
    """A remembered interaction episode."""
    episode_id: str
    user_id: str
    timestamp: datetime
    summary: str
    context: Dict
    outcome: str
    sentiment: Optional[str] = None

# ============================================================================
# ADAPTIVE MEMORY SYSTEM
# ============================================================================

class AdaptiveMemory:
    """Comprehensive memory system with preference learning."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.preferences: Dict[str, UserPreference] = {}
        self.episodes: List[Episode] = []
        self.working_memory = deque(maxlen=5)  # Last 5 exchanges

    def observe_interaction(
        self,
        user_input: str,
        agent_response: str,
        user_feedback: Optional[int] = None,
    ):
        """Learn from interaction."""
        # Analyze communication style
        self._analyze_communication_style(user_input)

        # Analyze expertise level
        self._analyze_expertise(user_input)

        # Analyze response preferences
        self._analyze_response_preferences(user_input, user_feedback)

        # Store episode
        episode = Episode(
            episode_id=f"ep_{len(self.episodes)}",
            user_id=self.user_id,
            timestamp=datetime.now(),
            summary=user_input[:100],
            context={"input_length": len(user_input)},
            outcome=agent_response[:100],
        )
        self.episodes.append(episode)

        # Update working memory
        self.working_memory.append({
            "user": user_input,
            "agent": agent_response,
            "timestamp": datetime.now(),
        })

    def _analyze_communication_style(self, user_input: str):
        """Analyze and learn communication style."""
        # Length preference
        word_count = len(user_input.split())

        if word_count < 15 or any(
            kw in user_input.lower()
            for kw in ["quick", "brief", "short", "tldr"]
        ):
            self.learn_preference(
                category="response_length",
                observation="User prefers concise responses",
            )
        elif word_count > 50 or any(
            kw in user_input.lower()
            for kw in ["detailed", "comprehensive", "explain"]
        ):
            self.learn_preference(
                category="response_length",
                observation="User appreciates detailed explanations",
            )

        # Formality
        formal_indicators = ["please", "thank you", "kindly", "would you"]
        casual_indicators = ["hey", "thanks", "gonna", "wanna"]

        formal_count = sum(
            1 for ind in formal_indicators if ind in user_input.lower()
        )
        casual_count = sum(
            1 for ind in casual_indicators if ind in user_input.lower()
        )

        if formal_count > casual_count:
            self.learn_preference(
                category="formality",
                observation="User prefers formal communication",
            )
        elif casual_count > formal_count:
            self.learn_preference(
                category="formality",
                observation="User prefers casual communication",
            )

    def _analyze_expertise(self, user_input: str):
        """Analyze and learn expertise level."""
        beginner_signals = [
            "what is", "how to", "i'm new", "beginner",
            "basic", "simple", "eli5"
        ]
        expert_signals = [
            "optimize", "performance", "architecture",
            "best practices", "trade-offs", "implementation"
        ]

        lower_input = user_input.lower()

        if any(signal in lower_input for signal in beginner_signals):
            self.learn_preference(
                category="expertise_level",
                observation="User is at beginner level",
            )
        elif any(signal in lower_input for signal in expert_signals):
            self.learn_preference(
                category="expertise_level",
                observation="User has expert-level knowledge",
            )

    def _analyze_response_preferences(
        self,
        user_input: str,
        feedback: Optional[int] = None,
    ):
        """Analyze response format preferences."""
        if "example" in user_input.lower() or "show me" in user_input.lower():
            self.learn_preference(
                category="response_format",
                observation="User prefers examples over theory",
            )

        if feedback:
            # Reinforce or adjust based on feedback
            if feedback >= 4:
                # Positive feedback - reinforce current preferences
                for pref in self.preferences.values():
                    pref.reinforce("Positive user feedback received")
            elif feedback <= 2:
                # Negative feedback - reduce confidence
                for pref in self.preferences.values():
                    pref.decay(decay_rate=0.2)

    def learn_preference(self, category: str, observation: str):
        """Learn or reinforce a preference."""
        if category in self.preferences:
            self.preferences[category].reinforce(observation)
        else:
            self.preferences[category] = UserPreference(
                category=category,
                preference=observation,
                confidence=0.3,
                evidence=[observation],
                learned_at=datetime.now(),
                last_confirmed=datetime.now(),
            )

    def get_adaptation_prompt(self) -> str:
        """Generate prompt additions from learned preferences."""
        if not self.preferences:
            return ""

        high_confidence_prefs = [
            pref for pref in self.preferences.values()
            if pref.confidence > 0.5
        ]

        if not high_confidence_prefs:
            return ""

        prompt_parts = ["\n## User Preferences (Learned)"]

        for pref in high_confidence_prefs:
            prompt_parts.append(
                f"- {pref.category}: {pref.preference} "
                f"(confidence: {pref.confidence:.2f})"
            )

        return "\n".join(prompt_parts)

    def get_recent_context(self) -> str:
        """Get recent conversation context."""
        if not self.working_memory:
            return ""

        context = "Recent conversation:\n"
        for exchange in list(self.working_memory)[-3:]:
            context += f"- User: {exchange['user'][:50]}...\n"

        return context

    def decay_memories(self):
        """Decay old memories."""
        # Decay preferences not confirmed recently
        cutoff = datetime.now() - timedelta(days=30)
        for pref in self.preferences.values():
            if pref.last_confirmed < cutoff:
                pref.decay(decay_rate=0.1)

        # Remove very low confidence preferences
        self.preferences = {
            k: v for k, v in self.preferences.items()
            if v.confidence > 0.1
        }

        # Remove old episodes
        episode_cutoff = datetime.now() - timedelta(days=90)
        self.episodes = [
            ep for ep in self.episodes
            if ep.timestamp > episode_cutoff
        ]

# ============================================================================
# ADAPTIVE AGENT
# ============================================================================

class AdaptiveAgent:
    """Agent that adapts to user preferences over time."""

    def __init__(
        self,
        user_id: str,
        base_instruction: str,
        model: str = "gemini-2.5-flash",
    ):
        self.user_id = user_id
        self.base_instruction = base_instruction
        self.model = model
        self.memory = AdaptiveMemory(user_id=user_id)
        self.agent = self._create_agent()
        self.interaction_count = 0

    def _create_agent(self) -> LlmAgent:
        """Create agent with adapted instruction."""
        # Combine base instruction with learned preferences
        adaptation = self.memory.get_adaptation_prompt()
        full_instruction = self.base_instruction

        if adaptation:
            full_instruction += f"\n{adaptation}"

        return LlmAgent(
            name=f"adaptive_agent_{self.user_id}",
            model=self.model,
            instruction=full_instruction,
        )

    async def invoke(
        self,
        user_input: str,
        include_context: bool = True,
    ) -> str:
        """Invoke agent and learn from interaction."""
        # Prepare input with context
        enhanced_input = user_input

        if include_context:
            context = self.memory.get_recent_context()
            if context:
                enhanced_input = f"{context}\n\nCurrent request: {user_input}"

        # Invoke agent
        response = await self.agent.invoke(enhanced_input)

        # Learn from interaction
        self.memory.observe_interaction(user_input, response)

        # Recreate agent with updated preferences every 5 interactions
        self.interaction_count += 1
        if self.interaction_count % 5 == 0:
            self.agent = self._create_agent()

        return response

    def provide_feedback(self, rating: int, comment: Optional[str] = None):
        """Accept explicit user feedback."""
        # Re-observe last interaction with feedback
        if self.memory.episodes:
            last_episode = self.memory.episodes[-1]
            self.memory.observe_interaction(
                last_episode.summary,
                last_episode.outcome,
                user_feedback=rating,
            )

        # Recreate agent with updated preferences
        self.agent = self._create_agent()

    def get_learned_preferences(self) -> List[dict]:
        """Export learned preferences."""
        return [
            {
                "category": pref.category,
                "preference": pref.preference,
                "confidence": pref.confidence,
                "confirmations": pref.confirmation_count,
            }
            for pref in self.memory.preferences.values()
        ]

    def save_memory(self, filepath: str):
        """Save memory to file."""
        data = {
            "user_id": self.user_id,
            "preferences": [
                {
                    **asdict(pref),
                    "learned_at": pref.learned_at.isoformat(),
                    "last_confirmed": pref.last_confirmed.isoformat(),
                }
                for pref in self.memory.preferences.values()
            ],
            "episodes": [
                {
                    **asdict(ep),
                    "timestamp": ep.timestamp.isoformat(),
                }
                for ep in self.memory.episodes
            ],
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load_memory(self, filepath: str):
        """Load memory from file."""
        with open(filepath) as f:
            data = json.load(f)

        # Load preferences
        for pref_data in data.get("preferences", []):
            pref = UserPreference(
                category=pref_data["category"],
                preference=pref_data["preference"],
                confidence=pref_data["confidence"],
                evidence=pref_data["evidence"],
                learned_at=datetime.fromisoformat(pref_data["learned_at"]),
                last_confirmed=datetime.fromisoformat(pref_data["last_confirmed"]),
                confirmation_count=pref_data.get("confirmation_count", 0),
            )
            self.memory.preferences[pref.category] = pref

        # Load episodes
        for ep_data in data.get("episodes", []):
            episode = Episode(
                episode_id=ep_data["episode_id"],
                user_id=ep_data["user_id"],
                timestamp=datetime.fromisoformat(ep_data["timestamp"]),
                summary=ep_data["summary"],
                context=ep_data["context"],
                outcome=ep_data["outcome"],
                sentiment=ep_data.get("sentiment"),
            )
            self.memory.episodes.append(episode)

        # Recreate agent with loaded preferences
        self.agent = self._create_agent()

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_learning_session():
    """Example of agent learning over multiple interactions."""

    # Create adaptive agent
    agent = AdaptiveAgent(
        user_id="user_123",
        base_instruction="You are a helpful Python programming assistant.",
    )

    # Interaction 1: User asks brief question
    response1 = await agent.invoke("Quick: what's a list comprehension?")
    print(f"Response 1: {response1}\n")

    # Interaction 2: User continues with brief style
    response2 = await agent.invoke("Short example please")
    print(f"Response 2: {response2}\n")

    # Agent learns preference for concise responses
    prefs = agent.get_learned_preferences()
    print(f"Learned preferences: {prefs}\n")

    # Interaction 3: User provides positive feedback
    agent.provide_feedback(rating=5, comment="Perfect, exactly what I needed")

    # Interaction 4: Agent applies learned preferences
    response4 = await agent.invoke("Explain decorators")
    print(f"Response 4 (adapted): {response4}\n")

    # Save learned preferences
    agent.save_memory("user_123_memory.json")

async def example_multi_session():
    """Example of preferences persisting across sessions."""

    # Session 1
    print("=== SESSION 1 ===")
    agent = AdaptiveAgent(
        user_id="user_456",
        base_instruction="You are a helpful assistant.",
    )

    await agent.invoke("I'm a beginner. What is Python?")
    await agent.invoke("How do I install it?")

    # Save memory
    agent.save_memory("user_456_memory.json")
    print(f"Preferences learned: {agent.get_learned_preferences()}\n")

    # Session 2 (next day)
    print("=== SESSION 2 (NEXT DAY) ===")
    agent2 = AdaptiveAgent(
        user_id="user_456",
        base_instruction="You are a helpful assistant.",
    )

    # Load previous session's memory
    agent2.load_memory("user_456_memory.json")
    print(f"Loaded preferences: {agent2.get_learned_preferences()}\n")

    # Agent remembers user is beginner
    response = await agent2.invoke("Tell me about classes")
    print(f"Response (adapted for beginner): {response}")

async def example_preference_evolution():
    """Example of preferences evolving over time."""

    agent = AdaptiveAgent(
        user_id="user_789",
        base_instruction="You are a coding tutor.",
    )

    # Week 1: Beginner questions
    print("=== WEEK 1: BEGINNER ===")
    await agent.invoke("What is a variable?")
    await agent.invoke("How do I create a function?")
    print(f"Preferences: {agent.get_learned_preferences()}\n")

    # Week 4: Intermediate questions
    print("=== WEEK 4: INTERMEDIATE ===")
    await agent.invoke("Explain list comprehensions")
    await agent.invoke("What are decorators?")
    print(f"Preferences: {agent.get_learned_preferences()}\n")

    # Week 12: Advanced questions
    print("=== WEEK 12: ADVANCED ===")
    await agent.invoke("Optimize this algorithm's time complexity")
    await agent.invoke("Explain metaclasses and their use cases")
    print(f"Preferences: {agent.get_learned_preferences()}\n")

    # Agent adapts expertise level over time

# ============================================================================
# RUN EXAMPLES
# ============================================================================

if __name__ == "__main__":
    import asyncio

    print("Example 1: Learning Session")
    print("=" * 50)
    asyncio.run(example_learning_session())

    print("\n\nExample 2: Multi-Session Persistence")
    print("=" * 50)
    asyncio.run(example_multi_session())

    print("\n\nExample 3: Preference Evolution")
    print("=" * 50)
    asyncio.run(example_preference_evolution())
```

## Testing

```python
import pytest

@pytest.mark.asyncio
async def test_preference_learning():
    """Test that agent learns communication preferences."""
    agent = AdaptiveAgent(
        user_id="test_user",
        base_instruction="You are helpful.",
    )

    # Simulate concise preference
    for _ in range(5):
        await agent.invoke("Quick answer please")

    prefs = agent.get_learned_preferences()
    assert any("concise" in p["preference"].lower() for p in prefs)
    assert all(p["confidence"] > 0.3 for p in prefs)

@pytest.mark.asyncio
async def test_memory_persistence():
    """Test saving and loading memory."""
    agent1 = AdaptiveAgent(user_id="persist_test", base_instruction="Help")

    await agent1.invoke("I prefer brief answers")
    agent1.save_memory("test_memory.json")

    agent2 = AdaptiveAgent(user_id="persist_test", base_instruction="Help")
    agent2.load_memory("test_memory.json")

    assert len(agent2.get_learned_preferences()) > 0

@pytest.mark.asyncio
async def test_feedback_integration():
    """Test that feedback adjusts preferences."""
    agent = AdaptiveAgent(user_id="feedback_test", base_instruction="Help")

    await agent.invoke("Test input")

    prefs_before = agent.get_learned_preferences()
    agent.provide_feedback(rating=5)
    prefs_after = agent.get_learned_preferences()

    # Confidence should increase with positive feedback
    if prefs_before and prefs_after:
        assert prefs_after[0]["confidence"] >= prefs_before[0]["confidence"]
```

## Production Considerations

### Rate Limiting Preference Updates

```python
class RateLimitedAdaptiveAgent(AdaptiveAgent):
    """Adaptive agent with rate-limited preference updates."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_adaptation = datetime.now()
        self.min_adaptation_interval = timedelta(hours=1)

    async def invoke(self, user_input: str, **kwargs) -> str:
        response = await super().invoke(user_input, **kwargs)

        # Only recreate agent if enough time has passed
        now = datetime.now()
        if now - self.last_adaptation > self.min_adaptation_interval:
            self.agent = self._create_agent()
            self.last_adaptation = now

        return response
```

### A/B Testing Adaptations

```python
class ABTestingAdaptiveAgent(AdaptiveAgent):
    """Agent with A/B testing for preference effectiveness."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.control_responses = []
        self.treatment_responses = []
        self.current_variant = "control"

    async def invoke(self, user_input: str, **kwargs) -> str:
        # Alternate between adapted and base agent
        if self.current_variant == "control":
            # Use base instruction without adaptations
            temp_agent = LlmAgent(
                name="control",
                model=self.model,
                instruction=self.base_instruction,
            )
            response = await temp_agent.invoke(user_input)
            self.control_responses.append(response)
            self.current_variant = "treatment"
        else:
            # Use adapted agent
            response = await super().invoke(user_input, **kwargs)
            self.treatment_responses.append(response)
            self.current_variant = "control"

        return response

    def get_ab_test_results(self) -> dict:
        """Compare control vs treatment performance."""
        return {
            "control_count": len(self.control_responses),
            "treatment_count": len(self.treatment_responses),
            # Add metrics comparison
        }
```
