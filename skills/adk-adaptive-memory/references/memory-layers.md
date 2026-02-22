# Memory Layer Architecture

## Overview

This reference documents the four-layer memory architecture for adaptive agents, based on cognitive science principles.

## Memory Layers

### Layer 1: Working Memory (Short-term)

**Purpose:** Hold current conversation context and active task state

**Characteristics:**
- **Capacity:** 5-9 items (Miller's Law)
- **Duration:** Current session only
- **Storage:** In-memory dictionary
- **Use cases:** Current topic, user intent, conversation flow

**Implementation:**

```python
@dataclass
class WorkingMemory:
    """Short-term memory for current session."""
    current_topic: Optional[str] = None
    user_intent: Optional[str] = None
    conversation_flow: List[str] = field(default_factory=list)
    active_entities: Dict[str, any] = field(default_factory=dict)
    context_window: deque = field(default_factory=lambda: deque(maxlen=5))

    def update_context(self, user_input: str, agent_response: str):
        """Update working memory with new exchange."""
        self.context_window.append({
            "user": user_input,
            "agent": agent_response,
            "timestamp": datetime.now(),
        })

    def extract_entities(self, text: str):
        """Extract and store entities from text."""
        # Simple entity extraction (use NER in production)
        words = text.split()
        for word in words:
            if word.istitle() and len(word) > 1:
                self.active_entities[word] = {
                    "first_seen": datetime.now(),
                    "mentions": self.active_entities.get(word, {}).get("mentions", 0) + 1,
                }

    def get_context_summary(self) -> str:
        """Get summary of working memory for prompt."""
        if not self.context_window:
            return ""

        recent = list(self.context_window)[-3:]  # Last 3 exchanges
        summary = "Recent conversation:\n"
        for exchange in recent:
            summary += f"- User: {exchange['user'][:50]}...\n"

        if self.current_topic:
            summary += f"\nCurrent topic: {self.current_topic}"

        return summary

    def clear(self):
        """Clear working memory (end of session)."""
        self.context_window.clear()
        self.active_entities.clear()
        self.current_topic = None
        self.user_intent = None
```

**When to Use:**
- Maintaining conversation coherence
- Tracking mentioned entities
- Following multi-turn requests
- Disambiguating pronouns ("it", "this", "that")

### Layer 2: Episodic Memory (What Happened)

**Purpose:** Remember specific past interactions and events

**Characteristics:**
- **Capacity:** Unlimited (with decay)
- **Duration:** 30-90 days
- **Storage:** Vector database (Pinecone) or SQL with embeddings
- **Use cases:** "Last time we discussed...", "You previously asked about..."

**Implementation:**

```python
@dataclass
class EpisodicMemory:
    """Memory of past interaction episodes."""
    episodes: List[Episode] = field(default_factory=list)
    max_episodes: int = 1000

    def store_episode(
        self,
        user_id: str,
        summary: str,
        full_context: dict,
        outcome: str,
        sentiment: Optional[str] = None,
    ) -> Episode:
        """Store a new episode."""
        episode = Episode(
            episode_id=f"ep_{user_id}_{len(self.episodes)}",
            user_id=user_id,
            timestamp=datetime.now(),
            summary=summary,
            context=full_context,
            outcome=outcome,
            sentiment=sentiment,
        )

        self.episodes.append(episode)

        # Limit total episodes (FIFO)
        if len(self.episodes) > self.max_episodes:
            self.episodes.pop(0)

        return episode

    def recall_episodes_by_timeframe(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Episode]:
        """Recall episodes within timeframe."""
        return [
            ep for ep in self.episodes
            if start_date <= ep.timestamp <= end_date
        ]

    def recall_episodes_by_sentiment(self, sentiment: str) -> List[Episode]:
        """Recall episodes with specific sentiment."""
        return [ep for ep in self.episodes if ep.sentiment == sentiment]

    def get_recent_episodes(self, count: int = 10) -> List[Episode]:
        """Get most recent episodes."""
        return sorted(self.episodes, key=lambda e: e.timestamp, reverse=True)[:count]

    def summarize_episode_history(self) -> str:
        """Create summary of interaction history."""
        if not self.episodes:
            return "No previous interactions"

        total = len(self.episodes)
        recent = self.get_recent_episodes(5)

        summary = f"Total interactions: {total}\n\nRecent interactions:\n"
        for ep in recent:
            summary += f"- {ep.timestamp.strftime('%Y-%m-%d')}: {ep.summary[:50]}...\n"

        return summary

    def decay_old_episodes(self, days_threshold: int = 90):
        """Remove episodes older than threshold."""
        cutoff = datetime.now() - timedelta(days=days_threshold)
        self.episodes = [ep for ep in self.episodes if ep.timestamp >= cutoff]
```

**When to Use:**
- Recalling previous conversations
- Understanding user's journey
- Providing context-aware responses
- Avoiding repetition ("As we discussed before...")

### Layer 3: Semantic Memory (What Was Learned)

**Purpose:** Store learned facts, concepts, and user preferences

**Characteristics:**
- **Capacity:** Unlimited (with decay by usage)
- **Duration:** Indefinite (decays if unused)
- **Storage:** Knowledge graph or vector database
- **Use cases:** User preferences, learned facts, domain knowledge

**Implementation:**

```python
@dataclass
class SemanticMemory:
    """Memory of learned facts and knowledge."""
    facts: Dict[str, SemanticFact] = field(default_factory=dict)
    knowledge_graph: Dict[str, Set[str]] = field(default_factory=dict)

    def learn_fact(
        self,
        user_id: str,
        category: str,
        fact: str,
        confidence: float = 0.5,
        source: Optional[str] = None,
    ) -> SemanticFact:
        """Learn a new fact."""
        fact_id = f"{category}_{hash(fact) % 10000}"

        if fact_id in self.facts:
            # Reinforce existing fact
            existing = self.facts[fact_id]
            existing.confidence = min(1.0, existing.confidence + 0.1)
            existing.access_count += 1
            existing.last_accessed = datetime.now()
            return existing

        # Create new fact
        semantic_fact = SemanticFact(
            fact_id=fact_id,
            user_id=user_id,
            category=category,
            fact=fact,
            confidence=confidence,
            learned_at=datetime.now(),
            last_accessed=datetime.now(),
        )

        self.facts[fact_id] = semantic_fact

        # Add to knowledge graph
        if category not in self.knowledge_graph:
            self.knowledge_graph[category] = set()
        self.knowledge_graph[category].add(fact_id)

        return semantic_fact

    def recall_facts(
        self,
        category: Optional[str] = None,
        min_confidence: float = 0.5,
    ) -> List[SemanticFact]:
        """Recall facts, optionally filtered."""
        facts = list(self.facts.values())

        if category:
            facts = [f for f in facts if f.category == category]

        facts = [f for f in facts if f.confidence >= min_confidence]

        # Sort by confidence and recency
        facts.sort(key=lambda f: (f.confidence, f.last_accessed), reverse=True)

        return facts

    def get_related_facts(self, fact_id: str) -> List[SemanticFact]:
        """Get facts related to given fact."""
        if fact_id not in self.facts:
            return []

        fact = self.facts[fact_id]
        category = fact.category

        # Get other facts in same category
        related_ids = self.knowledge_graph.get(category, set())
        return [self.facts[fid] for fid in related_ids if fid != fact_id]

    def decay_unused_facts(self, days_threshold: int = 30, decay_rate: float = 0.1):
        """Decay confidence of facts not accessed recently."""
        cutoff = datetime.now() - timedelta(days=days_threshold)

        for fact in self.facts.values():
            if fact.last_accessed < cutoff:
                fact.confidence = max(0.0, fact.confidence - decay_rate)

        # Remove very low confidence facts
        self.facts = {
            k: v for k, v in self.facts.items() if v.confidence > 0.1
        }

    def export_knowledge_graph(self) -> dict:
        """Export knowledge graph for visualization."""
        return {
            "categories": list(self.knowledge_graph.keys()),
            "facts": [
                {
                    "id": f.fact_id,
                    "category": f.category,
                    "fact": f.fact,
                    "confidence": f.confidence,
                }
                for f in self.facts.values()
            ],
            "relationships": {
                cat: list(facts) for cat, facts in self.knowledge_graph.items()
            },
        }
```

**When to Use:**
- Storing user preferences permanently
- Building domain knowledge
- Learning user's interests
- Remembering important facts about user

### Layer 4: Procedural Memory (How To Do)

**Purpose:** Remember learned procedures and task patterns

**Characteristics:**
- **Capacity:** Unlimited
- **Duration:** Indefinite
- **Storage:** Pattern database
- **Use cases:** Workflow preferences, task sequences, automation patterns

**Implementation:**

```python
@dataclass
class ProceduralMemory:
    """Memory of learned procedures and patterns."""
    patterns: Dict[str, TaskPattern] = field(default_factory=dict)

    def learn_pattern(
        self,
        user_id: str,
        task_type: str,
        steps: List[str],
        success: bool,
    ) -> TaskPattern:
        """Learn or update a task pattern."""
        pattern_id = f"{task_type}_{user_id}"

        if pattern_id in self.patterns:
            # Update existing pattern
            pattern = self.patterns[pattern_id]
            pattern.times_used += 1

            if success:
                # Reinforce successful pattern
                pattern.success_rate = (
                    (pattern.success_rate * (pattern.times_used - 1) + 1.0)
                    / pattern.times_used
                )
                # Update preferred steps
                pattern.preferred_steps = steps
            else:
                # Reduce confidence in pattern
                pattern.success_rate = (
                    (pattern.success_rate * (pattern.times_used - 1) + 0.0)
                    / pattern.times_used
                )

            return pattern

        # Create new pattern
        pattern = TaskPattern(
            pattern_id=pattern_id,
            user_id=user_id,
            task_type=task_type,
            preferred_steps=steps,
            success_rate=1.0 if success else 0.0,
            times_used=1,
        )

        self.patterns[pattern_id] = pattern
        return pattern

    def recall_pattern(self, task_type: str, user_id: str) -> Optional[TaskPattern]:
        """Recall preferred pattern for task."""
        pattern_id = f"{task_type}_{user_id}"
        return self.patterns.get(pattern_id)

    def get_best_pattern_for_task(self, task_type: str) -> Optional[TaskPattern]:
        """Get best pattern for task type across all users."""
        candidates = [
            p for p in self.patterns.values()
            if p.task_type == task_type
        ]

        if not candidates:
            return None

        # Return pattern with highest success rate and usage
        return max(candidates, key=lambda p: (p.success_rate, p.times_used))

    def suggest_next_steps(
        self,
        task_type: str,
        current_step: str,
    ) -> List[str]:
        """Suggest next steps based on learned patterns."""
        pattern = self.get_best_pattern_for_task(task_type)

        if not pattern:
            return []

        try:
            current_index = pattern.preferred_steps.index(current_step)
            return pattern.preferred_steps[current_index + 1:]
        except (ValueError, IndexError):
            return pattern.preferred_steps
```

**When to Use:**
- Learning user's workflows
- Automating repetitive tasks
- Predicting next steps
- Optimizing task sequences

## Layer Integration

### Unified Memory System

```python
class UnifiedMemory:
    """Integrates all memory layers."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()

    def process_interaction(
        self,
        user_input: str,
        agent_response: str,
        task_type: Optional[str] = None,
        success: bool = True,
    ):
        """Process interaction across all memory layers."""

        # Layer 1: Update working memory
        self.working.update_context(user_input, agent_response)
        self.working.extract_entities(user_input)

        # Layer 2: Store episode
        episode = self.episodic.store_episode(
            user_id=self.user_id,
            summary=user_input[:100],
            full_context={
                "input": user_input,
                "response": agent_response,
                "entities": self.working.active_entities,
            },
            outcome=agent_response[:100],
        )

        # Layer 3: Extract and learn facts
        # (In production, use NLP to extract facts)
        if "prefer" in user_input.lower():
            self.semantic.learn_fact(
                user_id=self.user_id,
                category="preference",
                fact=user_input,
                confidence=0.7,
            )

        # Layer 4: Learn procedural pattern
        if task_type:
            steps = [s.strip() for s in agent_response.split("\n") if s.strip()]
            self.procedural.learn_pattern(
                user_id=self.user_id,
                task_type=task_type,
                steps=steps,
                success=success,
            )

    def get_full_context_for_prompt(self) -> str:
        """Generate comprehensive context from all memory layers."""
        context_parts = []

        # Working memory
        working_context = self.working.get_context_summary()
        if working_context:
            context_parts.append(f"## Current Context\n{working_context}")

        # Recent episodes
        recent_episodes = self.episodic.get_recent_episodes(3)
        if recent_episodes:
            context_parts.append("\n## Recent Interactions")
            for ep in recent_episodes:
                context_parts.append(
                    f"- {ep.timestamp.strftime('%Y-%m-%d')}: {ep.summary}"
                )

        # Learned facts
        facts = self.semantic.recall_facts(min_confidence=0.7)
        if facts:
            context_parts.append("\n## Known Facts")
            for fact in facts[:5]:  # Top 5 facts
                context_parts.append(f"- {fact.category}: {fact.fact}")

        return "\n".join(context_parts)

    def end_session(self):
        """End session and perform cleanup."""
        # Clear working memory
        self.working.clear()

        # Decay old memories
        self.episodic.decay_old_episodes(days_threshold=90)
        self.semantic.decay_unused_facts(days_threshold=30)
```

## Memory Persistence

### Saving to Storage

```python
import json
from pathlib import Path

class MemoryPersistence:
    """Persist memory layers to storage."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_memory(self, user_id: str, memory: UnifiedMemory):
        """Save all memory layers."""
        user_dir = self.storage_dir / user_id
        user_dir.mkdir(exist_ok=True)

        # Save episodic memory
        episodes_file = user_dir / "episodes.json"
        with open(episodes_file, "w") as f:
            json.dump(
                [asdict(ep) for ep in memory.episodic.episodes],
                f,
                default=str,
            )

        # Save semantic memory
        facts_file = user_dir / "facts.json"
        with open(facts_file, "w") as f:
            json.dump(
                [asdict(fact) for fact in memory.semantic.facts.values()],
                f,
                default=str,
            )

        # Save procedural memory
        patterns_file = user_dir / "patterns.json"
        with open(patterns_file, "w") as f:
            json.dump(
                [asdict(p) for p in memory.procedural.patterns.values()],
                f,
                default=str,
            )

    def load_memory(self, user_id: str) -> UnifiedMemory:
        """Load all memory layers."""
        memory = UnifiedMemory(user_id=user_id)
        user_dir = self.storage_dir / user_id

        if not user_dir.exists():
            return memory

        # Load episodic memory
        episodes_file = user_dir / "episodes.json"
        if episodes_file.exists():
            with open(episodes_file) as f:
                episodes_data = json.load(f)
                memory.episodic.episodes = [
                    Episode(**ep) for ep in episodes_data
                ]

        # Load semantic memory
        facts_file = user_dir / "facts.json"
        if facts_file.exists():
            with open(facts_file) as f:
                facts_data = json.load(f)
                for fact_dict in facts_data:
                    fact = SemanticFact(**fact_dict)
                    memory.semantic.facts[fact.fact_id] = fact

        # Load procedural memory
        patterns_file = user_dir / "patterns.json"
        if patterns_file.exists():
            with open(patterns_file) as f:
                patterns_data = json.load(f)
                for pattern_dict in patterns_data:
                    pattern = TaskPattern(**pattern_dict)
                    memory.procedural.patterns[pattern.pattern_id] = pattern

        return memory
```

## Best Practices

1. **Clear working memory at session end** - Prevents context leakage
2. **Decay unused memories** - Keeps knowledge fresh and relevant
3. **Limit episode storage** - Prevent unbounded growth
4. **Prioritize high-confidence facts** - Focus on verified knowledge
5. **Track pattern success rates** - Learn from failures
6. **Persist long-term layers** - Maintain continuity across sessions
7. **Respect privacy** - Implement data retention policies
