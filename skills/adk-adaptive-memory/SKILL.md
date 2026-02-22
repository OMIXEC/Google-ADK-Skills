---
name: adk-adaptive-memory
description: When would Claude invoke this? When building AI agents that learn and adapt to user preferences over time, remember past interactions, or provide personalized experiences based on learned patterns.
trigger: adaptive memory, user preference learning, personalization, memory layers, episodic memory, semantic memory, procedural memory, pinecone integration, user context, interaction history
version: 1.0.0
category: advanced
tags: [memory, personalization, learning, rag, user-preferences]
---

# ADK Adaptive Memory System

Build AI agents with multi-layered memory that learns user preferences and adapts behavior over time for personalized experiences.

## When to Use This Skill

Use adaptive memory when:
- Building conversational agents that remember user context across sessions
- Creating personalized assistants that learn communication styles
- Implementing agents that adapt to user expertise levels
- Building systems that learn user preferences from interactions
- Developing long-term memory for multi-session conversations

## Core Concepts

### Memory Architecture

Four-layer memory system based on cognitive science:

```
┌─────────────────────────────────────────┐
│ 1. Working Memory (Short-term)         │
│    - Current session context            │
│    - Active conversation state          │
│    - TTL: Session duration              │
├─────────────────────────────────────────┤
│ 2. Episodic Memory (What happened)     │
│    - Past interaction summaries         │
│    - Conversation history               │
│    - TTL: 30-90 days                    │
├─────────────────────────────────────────┤
│ 3. Semantic Memory (What was learned)  │
│    - Learned facts and preferences      │
│    - User knowledge graph               │
│    - TTL: Indefinite (decays by usage)  │
├─────────────────────────────────────────┤
│ 4. Procedural Memory (How to do)       │
│    - Learned task patterns              │
│    - Workflow preferences               │
│    - TTL: Indefinite                    │
└─────────────────────────────────────────┘
```

### Preference Learning

Agents learn preferences through observation and reinforcement:

**Categories:**
- Communication style (formal/casual, verbose/concise)
- Expertise level (beginner/intermediate/expert)
- Topic interests and priorities
- Time preferences (quick vs detailed responses)
- Learning patterns (examples-first vs concepts-first)

**Confidence Scores:**
- 0.0-0.3: Initial observation
- 0.3-0.7: Pattern emerging
- 0.7-1.0: Strong preference confirmed

## Implementation Guide

### Step 1: Define Memory Models

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class MemoryType(Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

@dataclass
class UserPreference:
    """A learned user preference."""
    category: str  # communication_style, topics, time_preferences, etc.
    preference: str
    confidence: float  # 0.0 to 1.0
    evidence: List[str]  # Supporting observations
    learned_at: datetime
    last_confirmed: datetime
    confirmation_count: int = 0

    def reinforce(self, observation: str):
        """Reinforce preference with new observation."""
        self.confidence = min(1.0, self.confidence + 0.1)
        self.evidence.append(observation)
        self.last_confirmed = datetime.now()
        self.confirmation_count += 1

    def decay(self, decay_rate: float = 0.05):
        """Decay confidence if not recently confirmed."""
        self.confidence = max(0.0, self.confidence - decay_rate)

@dataclass
class Episode:
    """A remembered interaction episode."""
    episode_id: str
    user_id: str
    timestamp: datetime
    summary: str
    context: Dict[str, any]
    outcome: str
    sentiment: Optional[str] = None

@dataclass
class SemanticFact:
    """A learned semantic fact."""
    fact_id: str
    user_id: str
    category: str
    fact: str
    confidence: float
    learned_at: datetime
    last_accessed: datetime
    access_count: int = 0

@dataclass
class TaskPattern:
    """A learned procedural pattern."""
    pattern_id: str
    user_id: str
    task_type: str
    preferred_steps: List[str]
    success_rate: float
    times_used: int
```

### Step 2: Implement Adaptive Memory System

```python
@dataclass
class AdaptiveMemory:
    """Memory system that learns user preferences over time."""
    user_id: str
    working_memory: Dict[str, any] = field(default_factory=dict)
    preferences: Dict[str, UserPreference] = field(default_factory=dict)
    episodes: List[Episode] = field(default_factory=list)
    facts: Dict[str, SemanticFact] = field(default_factory=dict)
    patterns: Dict[str, TaskPattern] = field(default_factory=dict)

    def observe_interaction(
        self,
        user_input: str,
        agent_response: str,
        user_feedback: Optional[str] = None,
    ):
        """Learn from a user interaction."""
        # Analyze communication style
        if len(user_input.split()) < 10:
            self.learn_preference(
                category="communication_style",
                observation="User prefers concise responses",
            )
        else:
            self.learn_preference(
                category="communication_style",
                observation="User appreciates detailed explanations",
            )

        # Analyze expertise level
        if any(term in user_input.lower() for term in ["what is", "explain", "how to"]):
            self.learn_preference(
                category="expertise_level",
                observation="User benefits from explanatory content",
            )

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

    def learn_preference(self, category: str, observation: str):
        """Learn or reinforce a preference from observation."""
        if category in self.preferences:
            # Reinforce existing preference
            pref = self.preferences[category]
            pref.reinforce(observation)
        else:
            # Create new preference
            self.preferences[category] = UserPreference(
                category=category,
                preference=observation,
                confidence=0.3,
                evidence=[observation],
                learned_at=datetime.now(),
                last_confirmed=datetime.now(),
            )

    def get_adaptation_prompt(self) -> str:
        """Generate prompt additions based on learned preferences."""
        if not self.preferences:
            return ""

        prompt_parts = ["\n## Learned User Preferences"]

        # Only include high-confidence preferences
        for pref in self.preferences.values():
            if pref.confidence > 0.5:
                prompt_parts.append(
                    f"- **{pref.category}**: {pref.preference} "
                    f"(confidence: {pref.confidence:.2f})"
                )

        return "\n".join(prompt_parts) if len(prompt_parts) > 1 else ""

    def recall_similar_episodes(
        self,
        current_context: str,
        limit: int = 5,
    ) -> List[Episode]:
        """Recall similar past episodes."""
        # Simple keyword matching (use embeddings for production)
        keywords = set(current_context.lower().split())

        scored_episodes = [
            (
                episode,
                len(set(episode.summary.lower().split()) & keywords),
            )
            for episode in self.episodes
        ]

        # Sort by relevance
        scored_episodes.sort(key=lambda x: x[1], reverse=True)

        return [ep for ep, score in scored_episodes[:limit] if score > 0]

    def learn_fact(self, category: str, fact: str, confidence: float = 0.5):
        """Store a semantic fact."""
        fact_id = f"{category}_{len(self.facts)}"
        self.facts[fact_id] = SemanticFact(
            fact_id=fact_id,
            user_id=self.user_id,
            category=category,
            fact=fact,
            confidence=confidence,
            learned_at=datetime.now(),
            last_accessed=datetime.now(),
        )

    def recall_facts(self, category: Optional[str] = None) -> List[SemanticFact]:
        """Recall semantic facts, optionally filtered by category."""
        if category:
            return [f for f in self.facts.values() if f.category == category]
        return list(self.facts.values())

    def decay_unused_memories(self, days_threshold: int = 30):
        """Decay confidence of unused preferences."""
        cutoff = datetime.now().timestamp() - (days_threshold * 24 * 3600)

        for pref in self.preferences.values():
            if pref.last_confirmed.timestamp() < cutoff:
                pref.decay(decay_rate=0.1)

        # Remove very low confidence preferences
        self.preferences = {
            k: v for k, v in self.preferences.items() if v.confidence > 0.1
        }
```

### Step 3: Integrate with Agent

```python
from google.adk.agents import LlmAgent

class AdaptiveAgent:
    """Agent with adaptive memory capabilities."""

    def __init__(self, user_id: str, base_instruction: str):
        self.user_id = user_id
        self.base_instruction = base_instruction
        self.memory = AdaptiveMemory(user_id=user_id)

        # Create agent (will be recreated with adapted prompt)
        self.agent = self._create_agent()

    def _create_agent(self) -> LlmAgent:
        """Create agent with adapted instruction based on learned preferences."""
        # Get adaptation prompt from memory
        adaptation = self.memory.get_adaptation_prompt()

        # Combine base instruction with adaptations
        full_instruction = self.base_instruction
        if adaptation:
            full_instruction += f"\n\n{adaptation}"

        return LlmAgent(
            name=f"adaptive_agent_{self.user_id}",
            model="gemini-2.5-flash",
            instruction=full_instruction,
        )

    async def invoke(self, user_input: str) -> str:
        """Invoke agent and learn from interaction."""
        # Recall similar past episodes for context
        similar_episodes = self.memory.recall_similar_episodes(user_input)

        # Add episode context to working memory
        if similar_episodes:
            episode_context = "\n".join([
                f"- {ep.timestamp.strftime('%Y-%m-%d')}: {ep.summary}"
                for ep in similar_episodes[:3]
            ])
            context_prompt = f"\n\nRelevant past interactions:\n{episode_context}"
            enhanced_input = user_input + context_prompt
        else:
            enhanced_input = user_input

        # Invoke agent
        response = await self.agent.invoke(enhanced_input)

        # Learn from interaction
        self.memory.observe_interaction(user_input, response)

        # Recreate agent with updated preferences
        self.agent = self._create_agent()

        return response

    def provide_feedback(self, feedback: str, rating: int):
        """Learn from explicit user feedback."""
        if rating >= 4:
            # Positive feedback - reinforce current preferences
            for pref in self.memory.preferences.values():
                pref.reinforce(f"User provided positive feedback: {feedback}")
        elif rating <= 2:
            # Negative feedback - reduce confidence
            for pref in self.memory.preferences.values():
                pref.decay(decay_rate=0.2)
```

### Step 4: Add Pinecone Integration for Long-term Memory

```python
from pinecone import Pinecone
from typing import List

class PineconeMemoryStore:
    """Long-term memory storage using Pinecone vector database."""

    def __init__(self, index_name: str, dimension: int = 768):
        self.pc = Pinecone()
        self.index = self.pc.Index(index_name)
        self.dimension = dimension

    async def store_preference(self, user_id: str, preference: UserPreference):
        """Store preference as vector for semantic retrieval."""
        # Create text representation
        text = f"{preference.category}: {preference.preference}"

        # Generate embedding
        embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[text],
            parameters={"input_type": "passage"},
        ).data[0].values

        # Store in Pinecone
        self.index.upsert(vectors=[{
            "id": f"{user_id}_{preference.category}",
            "values": embedding,
            "metadata": {
                "user_id": user_id,
                "category": preference.category,
                "preference": preference.preference,
                "confidence": preference.confidence,
                "learned_at": preference.learned_at.isoformat(),
                "confirmation_count": preference.confirmation_count,
            }
        }])

    async def recall_relevant_preferences(
        self,
        user_id: str,
        context: str,
        top_k: int = 5,
    ) -> List[UserPreference]:
        """Retrieve preferences relevant to current context."""
        # Generate query embedding
        query_embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[context],
            parameters={"input_type": "query"},
        ).data[0].values

        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            filter={"user_id": user_id},
            top_k=top_k,
            include_metadata=True,
        )

        # Convert to UserPreference objects
        preferences = []
        for match in results.matches:
            if match.score > 0.7:  # Relevance threshold
                meta = match.metadata
                pref = UserPreference(
                    category=meta["category"],
                    preference=meta["preference"],
                    confidence=meta["confidence"],
                    evidence=[],  # Not stored in vector DB
                    learned_at=datetime.fromisoformat(meta["learned_at"]),
                    last_confirmed=datetime.now(),
                    confirmation_count=meta["confirmation_count"],
                )
                preferences.append(pref)

        return preferences

    async def store_episode(self, user_id: str, episode: Episode):
        """Store interaction episode."""
        text = f"{episode.summary} - Outcome: {episode.outcome}"

        embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[text],
        ).data[0].values

        self.index.upsert(vectors=[{
            "id": episode.episode_id,
            "values": embedding,
            "metadata": {
                "user_id": user_id,
                "summary": episode.summary,
                "outcome": episode.outcome,
                "timestamp": episode.timestamp.isoformat(),
            }
        }])

    async def recall_similar_episodes(
        self,
        user_id: str,
        context: str,
        top_k: int = 5,
    ) -> List[Episode]:
        """Recall similar past episodes using semantic search."""
        query_embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[context],
        ).data[0].values

        results = self.index.query(
            vector=query_embedding,
            filter={"user_id": user_id},
            top_k=top_k,
            include_metadata=True,
        )

        episodes = []
        for match in results.matches:
            meta = match.metadata
            episode = Episode(
                episode_id=match.id,
                user_id=user_id,
                timestamp=datetime.fromisoformat(meta["timestamp"]),
                summary=meta["summary"],
                context={},
                outcome=meta["outcome"],
            )
            episodes.append(episode)

        return episodes
```

## Usage Examples

### Basic Adaptive Agent

```python
# Create adaptive agent
agent = AdaptiveAgent(
    user_id="user_123",
    base_instruction="You are a helpful assistant.",
)

# First interaction
response1 = await agent.invoke("Quick summary of Python classes please")
# Agent learns: User prefers concise responses

# Second interaction
response2 = await agent.invoke("What are decorators?")
# Agent adapts prompt to be more concise based on learned preference

# Third interaction with explicit feedback
response3 = await agent.invoke("Explain async/await")
agent.provide_feedback("Perfect length!", rating=5)
# Reinforces concise communication preference
```

### Multi-Session Personalization

```python
# Session 1
agent = AdaptiveAgent(user_id="user_123", base_instruction="...")
await agent.invoke("I'm a beginner in Python")
# Learns: expertise_level = beginner

# Session 2 (next day)
agent = AdaptiveAgent(user_id="user_123", base_instruction="...")
# Loads previous preferences from memory
await agent.invoke("How do I use list comprehensions?")
# Agent automatically adapts to beginner level based on previous session
```

### Pinecone-Backed Long-term Memory

```python
# Create Pinecone store
memory_store = PineconeMemoryStore(index_name="user-memories")

# Store learned preferences
for pref in agent.memory.preferences.values():
    await memory_store.store_preference("user_123", pref)

# Later session - recall relevant preferences
context = "User asking about advanced Python patterns"
relevant_prefs = await memory_store.recall_relevant_preferences(
    user_id="user_123",
    context=context,
)

# Apply recalled preferences to agent
for pref in relevant_prefs:
    agent.memory.preferences[pref.category] = pref
```

## Advanced Patterns

### Preference Categories

See reference: `@references/preference-learning.md`

### Memory Layer Design

See reference: `@references/memory-layers.md`

## Examples

- **Adaptive Agent:** `@examples/adaptive-agent.md`
- **Pinecone Integration:** `@examples/pinecone-integration.md`

## Production Considerations

### Privacy and Data Retention

```python
class PrivacyAwareMemory(AdaptiveMemory):
    """Memory system with privacy controls."""

    def __init__(self, user_id: str, retention_days: int = 90):
        super().__init__(user_id)
        self.retention_days = retention_days

    def purge_old_episodes(self):
        """Remove episodes older than retention period."""
        cutoff = datetime.now().timestamp() - (self.retention_days * 24 * 3600)
        self.episodes = [
            ep for ep in self.episodes
            if ep.timestamp.timestamp() >= cutoff
        ]

    def export_user_data(self) -> dict:
        """Export all user data for GDPR compliance."""
        return {
            "user_id": self.user_id,
            "preferences": [asdict(p) for p in self.preferences.values()],
            "episodes": [asdict(e) for e in self.episodes],
            "facts": [asdict(f) for f in self.facts.values()],
        }

    def delete_all_data(self):
        """Delete all user data."""
        self.preferences.clear()
        self.episodes.clear()
        self.facts.clear()
        self.patterns.clear()
```

### Testing Adaptation

```python
import pytest

@pytest.mark.asyncio
async def test_preference_learning():
    """Test that agent learns preferences."""
    agent = AdaptiveAgent(user_id="test_user", base_instruction="You are helpful.")

    # Send concise inputs
    for _ in range(5):
        await agent.invoke("Quick fact")

    # Check learned preference
    assert "communication_style" in agent.memory.preferences
    pref = agent.memory.preferences["communication_style"]
    assert pref.confidence > 0.5
    assert "concise" in pref.preference.lower()

@pytest.mark.asyncio
async def test_episode_recall():
    """Test episode recall."""
    agent = AdaptiveAgent(user_id="test_user", base_instruction="...")

    # Create episodes
    await agent.invoke("How do I install Python?")
    await agent.invoke("What is pip?")

    # Recall similar episodes
    episodes = agent.memory.recall_similar_episodes("Python installation help")
    assert len(episodes) > 0
    assert "install" in episodes[0].summary.lower()
```

## Related Skills

- **adk-session-management:** Session state persistence
- **adk-rag-integration:** Vector database integration
- **adk-enterprise-multi-agent:** Cross-agent memory sharing
- **adk-callback-patterns:** Memory update hooks

## References

- [Memory Layers](@references/memory-layers.md)
- [Preference Learning](@references/preference-learning.md)
