# User Preference Learning

## Overview

This reference documents strategies for learning user preferences from interactions and adapting agent behavior accordingly.

## Preference Categories

### 1. Communication Style

**What to learn:**
- Formality level (formal vs casual)
- Response length (concise vs detailed)
- Tone (professional vs friendly)
- Use of examples (code-first vs explanation-first)

**Detection Signals:**

```python
class CommunicationStyleDetector:
    """Detect user's preferred communication style."""

    def analyze_formality(self, user_input: str) -> str:
        """Detect formality level."""
        formal_indicators = ["please", "thank you", "kindly", "would you"]
        casual_indicators = ["hey", "thanks", "gonna", "wanna"]

        formal_count = sum(1 for ind in formal_indicators if ind in user_input.lower())
        casual_count = sum(1 for ind in casual_indicators if ind in user_input.lower())

        if formal_count > casual_count:
            return "formal"
        elif casual_count > formal_count:
            return "casual"
        return "neutral"

    def analyze_length_preference(self, user_input: str) -> str:
        """Detect preferred response length."""
        short_indicators = ["quick", "brief", "tldr", "short", "summary"]
        detailed_indicators = ["detailed", "explain", "elaborate", "deep dive"]

        if any(ind in user_input.lower() for ind in short_indicators):
            return "concise"
        elif any(ind in user_input.lower() for ind in detailed_indicators):
            return "detailed"

        # Infer from input length
        word_count = len(user_input.split())
        return "concise" if word_count < 20 else "detailed"

    def analyze_example_preference(self, user_input: str) -> str:
        """Detect preference for examples vs explanations."""
        example_indicators = ["example", "show me", "code", "demo"]
        theory_indicators = ["why", "how does", "explain", "concept"]

        if any(ind in user_input.lower() for ind in example_indicators):
            return "examples_first"
        elif any(ind in user_input.lower() for ind in theory_indicators):
            return "concepts_first"
        return "balanced"
```

**Adaptation Example:**

```python
def adapt_communication_style(base_instruction: str, preferences: dict) -> str:
    """Adapt instruction based on communication preferences."""
    adaptations = []

    formality = preferences.get("formality", "neutral")
    if formality == "formal":
        adaptations.append("Maintain professional tone and formal language.")
    elif formality == "casual":
        adaptations.append("Use friendly, conversational tone.")

    length = preferences.get("length", "balanced")
    if length == "concise":
        adaptations.append("Provide concise, to-the-point responses.")
    elif length == "detailed":
        adaptations.append("Provide comprehensive, detailed explanations.")

    examples = preferences.get("examples", "balanced")
    if examples == "examples_first":
        adaptations.append("Lead with code examples, then explain concepts.")
    elif examples == "concepts_first":
        adaptations.append("Explain concepts first, then provide examples.")

    if adaptations:
        return base_instruction + "\n\n" + "\n".join(adaptations)
    return base_instruction
```

### 2. Expertise Level

**What to learn:**
- Technical proficiency (beginner/intermediate/expert)
- Domain knowledge
- Jargon tolerance
- Assumed background knowledge

**Detection Signals:**

```python
class ExpertiseLevelDetector:
    """Detect user's expertise level."""

    def __init__(self):
        self.beginner_signals = [
            "what is", "how to", "i'm new to", "just started",
            "basic", "simple", "eli5", "explain like"
        ]
        self.expert_signals = [
            "optimize", "performance", "architecture", "best practices",
            "edge case", "trade-offs", "implementation details"
        ]

    def analyze_question_type(self, user_input: str) -> str:
        """Analyze question complexity."""
        lower_input = user_input.lower()

        beginner_count = sum(
            1 for signal in self.beginner_signals
            if signal in lower_input
        )
        expert_count = sum(
            1 for signal in self.expert_signals
            if signal in lower_input
        )

        if beginner_count > expert_count:
            return "beginner"
        elif expert_count > beginner_count:
            return "expert"
        return "intermediate"

    def track_expertise_progression(
        self,
        user_id: str,
        topic: str,
        interaction_history: List[dict],
    ) -> dict:
        """Track expertise progression over time."""
        expertise_by_time = []

        for interaction in interaction_history:
            level = self.analyze_question_type(interaction["user_input"])
            expertise_by_time.append({
                "timestamp": interaction["timestamp"],
                "level": level,
                "topic": topic,
            })

        # Detect progression (beginner -> intermediate -> expert)
        if len(expertise_by_time) >= 3:
            levels = [e["level"] for e in expertise_by_time[-3:]]
            if levels == ["beginner", "intermediate", "expert"]:
                return {"status": "progressing", "current": "expert"}

        # Return current level
        if expertise_by_time:
            return {"status": "stable", "current": expertise_by_time[-1]["level"]}

        return {"status": "unknown", "current": "intermediate"}
```

**Adaptation Example:**

```python
def adapt_expertise_level(base_instruction: str, level: str) -> str:
    """Adapt instruction based on expertise level."""
    if level == "beginner":
        return base_instruction + """

For beginner users:
- Avoid jargon and technical terms
- Explain concepts step-by-step
- Provide analogies and simple examples
- Check understanding before advancing
"""
    elif level == "expert":
        return base_instruction + """

For expert users:
- Use precise technical terminology
- Focus on advanced concepts and edge cases
- Discuss trade-offs and performance implications
- Skip basic explanations
"""
    else:  # intermediate
        return base_instruction + """

For intermediate users:
- Balance technical accuracy with clarity
- Explain complex concepts when needed
- Provide both overview and details
- Mention advanced topics for further learning
"""
```

### 3. Topic Interests

**What to learn:**
- Frequently discussed topics
- Areas of deep interest
- Topics to avoid
- Related interests

**Detection Signals:**

```python
from collections import Counter

class TopicInterestTracker:
    """Track user's topic interests."""

    def __init__(self):
        self.topic_mentions = Counter()
        self.topic_engagement = {}  # topic -> engagement score

    def extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        # In production, use NLP topic modeling
        # Simple keyword extraction for demo
        common_topics = {
            "python": ["python", "py", "django", "flask"],
            "javascript": ["javascript", "js", "node", "react"],
            "machine_learning": ["ml", "machine learning", "neural", "model"],
            "databases": ["database", "sql", "postgres", "mongodb"],
            "devops": ["docker", "kubernetes", "ci/cd", "deployment"],
        }

        found_topics = []
        text_lower = text.lower()

        for topic, keywords in common_topics.items():
            if any(kw in text_lower for kw in keywords):
                found_topics.append(topic)

        return found_topics

    def record_interaction(
        self,
        user_input: str,
        agent_response: str,
        user_feedback: Optional[int] = None,
    ):
        """Record topic mentions and engagement."""
        topics = self.extract_topics(user_input + " " + agent_response)

        for topic in topics:
            self.topic_mentions[topic] += 1

            # Calculate engagement score
            if topic not in self.topic_engagement:
                self.topic_engagement[topic] = {
                    "total_interactions": 0,
                    "positive_feedback": 0,
                    "negative_feedback": 0,
                }

            self.topic_engagement[topic]["total_interactions"] += 1

            if user_feedback:
                if user_feedback >= 4:
                    self.topic_engagement[topic]["positive_feedback"] += 1
                elif user_feedback <= 2:
                    self.topic_engagement[topic]["negative_feedback"] += 1

    def get_top_interests(self, limit: int = 5) -> List[tuple]:
        """Get top topic interests."""
        return self.topic_mentions.most_common(limit)

    def get_engagement_score(self, topic: str) -> float:
        """Calculate engagement score for topic."""
        if topic not in self.topic_engagement:
            return 0.0

        data = self.topic_engagement[topic]
        total = data["total_interactions"]

        if total == 0:
            return 0.0

        positive_rate = data["positive_feedback"] / total
        negative_rate = data["negative_feedback"] / total

        # Score: frequency * (positive rate - negative rate)
        return self.topic_mentions[topic] * (positive_rate - negative_rate)

    def suggest_related_topics(self, current_topic: str) -> List[str]:
        """Suggest related topics based on user interests."""
        # Topic relationships (in production, use knowledge graph)
        related = {
            "python": ["django", "flask", "fastapi", "data_science"],
            "javascript": ["typescript", "react", "node", "frontend"],
            "machine_learning": ["python", "tensorflow", "pytorch", "data_science"],
            "databases": ["sql", "nosql", "data_modeling", "performance"],
        }

        return related.get(current_topic, [])
```

### 4. Time Preferences

**What to learn:**
- Preference for quick answers vs thorough exploration
- Patience for multi-step processes
- Willingness to iterate
- Response to follow-up questions

**Detection Signals:**

```python
class TimePreferenceDetector:
    """Detect user's time preferences."""

    def analyze_urgency(self, user_input: str) -> str:
        """Detect urgency level."""
        urgent_indicators = ["quick", "fast", "asap", "urgent", "immediately"]
        patient_indicators = ["when you can", "no rush", "detailed", "thorough"]

        lower_input = user_input.lower()

        if any(ind in lower_input for ind in urgent_indicators):
            return "urgent"
        elif any(ind in lower_input for ind in patient_indicators):
            return "patient"
        return "normal"

    def track_iteration_tolerance(
        self,
        interaction_history: List[dict],
    ) -> dict:
        """Track user's tolerance for iterative refinement."""
        if len(interaction_history) < 3:
            return {"tolerance": "unknown", "confidence": 0.0}

        # Count refinement interactions
        refinements = 0
        for i in range(1, len(interaction_history)):
            prev = interaction_history[i-1]["user_input"].lower()
            curr = interaction_history[i]["user_input"].lower()

            # Detect refinement signals
            if any(signal in curr for signal in ["more", "also", "what about", "additionally"]):
                refinements += 1

        refinement_rate = refinements / len(interaction_history)

        if refinement_rate > 0.5:
            return {"tolerance": "high", "confidence": 0.8}
        elif refinement_rate < 0.2:
            return {"tolerance": "low", "confidence": 0.6}
        return {"tolerance": "medium", "confidence": 0.5}
```

### 5. Learning Patterns

**What to learn:**
- Preferred learning modality (visual, code, text)
- Depth-first vs breadth-first learning
- Preference for theory vs practice
- Self-directed vs guided learning

**Detection Signals:**

```python
class LearningPatternDetector:
    """Detect user's learning patterns."""

    def analyze_learning_modality(self, user_input: str) -> List[str]:
        """Detect preferred learning modalities."""
        modalities = []

        if any(word in user_input.lower() for word in ["show", "example", "code"]):
            modalities.append("code_examples")

        if any(word in user_input.lower() for word in ["diagram", "visual", "chart"]):
            modalities.append("visual")

        if any(word in user_input.lower() for word in ["explain", "why", "how"]):
            modalities.append("conceptual")

        return modalities if modalities else ["balanced"]

    def analyze_learning_depth(
        self,
        interaction_history: List[dict],
    ) -> str:
        """Determine depth-first vs breadth-first learning."""
        if len(interaction_history) < 5:
            return "unknown"

        # Track topic diversity vs depth
        topics = []
        for interaction in interaction_history:
            topics.extend(self.extract_topics(interaction["user_input"]))

        unique_topics = len(set(topics))
        total_questions = len(interaction_history)

        diversity_ratio = unique_topics / total_questions

        if diversity_ratio > 0.7:
            return "breadth_first"  # Explores many topics
        elif diversity_ratio < 0.3:
            return "depth_first"  # Deep dives into few topics
        return "balanced"
```

## Preference Confidence Scoring

### Confidence Calculation

```python
class PreferenceConfidenceCalculator:
    """Calculate confidence scores for learned preferences."""

    def calculate_confidence(
        self,
        observations: List[str],
        confirmations: int,
        contradictions: int,
        days_since_learned: int,
    ) -> float:
        """Calculate confidence score (0.0 to 1.0)."""

        # Base confidence from observations
        base_confidence = min(0.5, len(observations) * 0.1)

        # Boost from confirmations
        confirmation_boost = min(0.4, confirmations * 0.05)

        # Penalty from contradictions
        contradiction_penalty = min(0.3, contradictions * 0.1)

        # Time decay (lose 0.01 per week)
        time_decay = min(0.2, (days_since_learned / 7) * 0.01)

        confidence = base_confidence + confirmation_boost - contradiction_penalty - time_decay

        return max(0.0, min(1.0, confidence))

    def should_apply_preference(self, confidence: float, threshold: float = 0.5) -> bool:
        """Determine if preference confidence is high enough to apply."""
        return confidence >= threshold

    def rank_preferences(
        self,
        preferences: List[UserPreference],
    ) -> List[UserPreference]:
        """Rank preferences by confidence and recency."""
        return sorted(
            preferences,
            key=lambda p: (p.confidence, p.last_confirmed.timestamp()),
            reverse=True,
        )
```

## Preference Conflicts

### Conflict Resolution

```python
class PreferenceConflictResolver:
    """Resolve conflicts between learned preferences."""

    def detect_conflicts(
        self,
        preferences: Dict[str, UserPreference],
    ) -> List[tuple]:
        """Detect conflicting preferences."""
        conflicts = []

        # Example conflicts
        conflict_pairs = [
            ("concise_responses", "detailed_explanations"),
            ("beginner_level", "expert_terminology"),
            ("quick_answers", "thorough_exploration"),
        ]

        for pref1_key, pref2_key in conflict_pairs:
            if pref1_key in preferences and pref2_key in preferences:
                pref1 = preferences[pref1_key]
                pref2 = preferences[pref2_key]

                # Both have high confidence - conflict
                if pref1.confidence > 0.5 and pref2.confidence > 0.5:
                    conflicts.append((pref1, pref2))

        return conflicts

    def resolve_conflict(
        self,
        pref1: UserPreference,
        pref2: UserPreference,
        context: Optional[str] = None,
    ) -> UserPreference:
        """Resolve conflict between two preferences."""

        # Use recency as tiebreaker
        if pref1.last_confirmed > pref2.last_confirmed:
            return pref1

        # Use confidence if recency similar
        if pref1.confidence > pref2.confidence:
            return pref1

        # Context-based resolution
        if context:
            # If context matches preference category, favor it
            if pref1.category.lower() in context.lower():
                return pref1
            if pref2.category.lower() in context.lower():
                return pref2

        # Default to more recent
        return pref1
```

## Privacy and Ethics

### Privacy-Preserving Preference Learning

```python
class PrivacyAwarePreferenceLearning:
    """Learn preferences while respecting privacy."""

    def __init__(self, retention_days: int = 90):
        self.retention_days = retention_days
        self.sensitive_categories = {
            "personal_info",
            "health",
            "financial",
            "location",
        }

    def should_learn_preference(
        self,
        category: str,
        observation: str,
    ) -> bool:
        """Determine if preference should be learned."""

        # Never learn sensitive personal information
        if category in self.sensitive_categories:
            return False

        # Don't learn from PII
        if self.contains_pii(observation):
            return False

        return True

    def contains_pii(self, text: str) -> bool:
        """Check if text contains personally identifiable information."""
        # Simple PII detection (use NER in production)
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{16}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        ]

        import re
        for pattern in pii_patterns:
            if re.search(pattern, text):
                return True

        return False

    def anonymize_preference(self, preference: UserPreference) -> UserPreference:
        """Anonymize preference before storage."""
        # Remove PII from evidence
        clean_evidence = [
            self.remove_pii(obs) for obs in preference.evidence
        ]

        preference.evidence = clean_evidence
        return preference

    def remove_pii(self, text: str) -> str:
        """Remove PII from text."""
        # Replace emails
        import re
        text = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL]',
            text,
        )

        # Replace phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)

        return text
```

## Testing Preference Learning

```python
import pytest

@pytest.mark.asyncio
async def test_communication_style_learning():
    """Test learning communication style preferences."""
    detector = CommunicationStyleDetector()

    # Test formal detection
    formal_input = "Could you please explain this concept? Thank you kindly."
    assert detector.analyze_formality(formal_input) == "formal"

    # Test casual detection
    casual_input = "Hey, can you help me out? Thanks!"
    assert detector.analyze_formality(casual_input) == "casual"

def test_expertise_progression():
    """Test tracking expertise progression."""
    detector = ExpertiseLevelDetector()

    interactions = [
        {"user_input": "What is Python?", "timestamp": datetime.now()},
        {"user_input": "How do I use list comprehensions?", "timestamp": datetime.now()},
        {"user_input": "What are the performance implications of generators vs lists?", "timestamp": datetime.now()},
    ]

    result = detector.track_expertise_progression("user_123", "python", interactions)
    assert result["status"] == "progressing"

def test_preference_confidence():
    """Test preference confidence calculation."""
    calculator = PreferenceConfidenceCalculator()

    confidence = calculator.calculate_confidence(
        observations=["concise response preferred"] * 5,
        confirmations=3,
        contradictions=0,
        days_since_learned=7,
    )

    assert confidence > 0.5
    assert calculator.should_apply_preference(confidence)
```

## Best Practices

1. **Start with low confidence** - Begin at 0.3-0.5, increase with evidence
2. **Require multiple observations** - Don't jump to conclusions from single interaction
3. **Track contradictions** - User preferences can be context-dependent
4. **Implement decay** - Preferences change over time
5. **Resolve conflicts contextually** - Use current context to choose between conflicting preferences
6. **Respect privacy** - Never store sensitive personal information
7. **Allow user control** - Provide way for users to view/edit learned preferences
8. **Test thoroughly** - Verify preference learning across diverse user patterns
