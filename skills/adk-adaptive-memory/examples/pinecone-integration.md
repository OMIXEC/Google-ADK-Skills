# Pinecone Integration for Long-term Memory

## Overview

This example demonstrates using Pinecone vector database for scalable, semantic long-term memory storage.

## Complete Implementation

```python
from pinecone import Pinecone, ServerlessSpec
from google.adk.agents import LlmAgent
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from datetime import datetime
import json

# ============================================================================
# PINECONE MEMORY STORE
# ============================================================================

class PineconeMemoryStore:
    """Long-term memory storage using Pinecone."""

    def __init__(
        self,
        api_key: str,
        index_name: str = "user-memories",
        dimension: int = 768,
        metric: str = "cosine",
    ):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.dimension = dimension

        # Create index if doesn't exist
        if index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1",
                ),
            )

        self.index = self.pc.Index(index_name)

    async def store_preference(
        self,
        user_id: str,
        preference: "UserPreference",
    ):
        """Store user preference with semantic embedding."""

        # Create text representation
        text = f"{preference.category}: {preference.preference}"

        # Generate embedding using Pinecone inference API
        embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[text],
            parameters={"input_type": "passage"},
        ).data[0].values

        # Prepare metadata
        metadata = {
            "user_id": user_id,
            "type": "preference",
            "category": preference.category,
            "preference": preference.preference,
            "confidence": preference.confidence,
            "learned_at": preference.learned_at.isoformat(),
            "last_confirmed": preference.last_confirmed.isoformat(),
            "confirmation_count": preference.confirmation_count,
        }

        # Store in Pinecone
        self.index.upsert(vectors=[{
            "id": f"{user_id}_pref_{preference.category}",
            "values": embedding,
            "metadata": metadata,
        }])

    async def recall_preferences(
        self,
        user_id: str,
        context: str,
        top_k: int = 5,
        min_score: float = 0.7,
    ) -> List["UserPreference"]:
        """Recall preferences relevant to context using semantic search."""

        # Generate query embedding
        query_embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[context],
            parameters={"input_type": "query"},
        ).data[0].values

        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            filter={
                "user_id": user_id,
                "type": "preference",
            },
            top_k=top_k,
            include_metadata=True,
        )

        # Convert matches to UserPreference objects
        from skills.adk_adaptive_memory.memory_models import UserPreference

        preferences = []
        for match in results.matches:
            if match.score >= min_score:
                meta = match.metadata
                pref = UserPreference(
                    category=meta["category"],
                    preference=meta["preference"],
                    confidence=meta["confidence"],
                    evidence=[],  # Not stored in vector DB
                    learned_at=datetime.fromisoformat(meta["learned_at"]),
                    last_confirmed=datetime.fromisoformat(meta["last_confirmed"]),
                    confirmation_count=meta.get("confirmation_count", 0),
                )
                preferences.append(pref)

        return preferences

    async def store_episode(
        self,
        user_id: str,
        episode: "Episode",
    ):
        """Store interaction episode."""

        # Create text representation
        text = f"User: {episode.summary}\nOutcome: {episode.outcome}"

        # Generate embedding
        embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[text],
            parameters={"input_type": "passage"},
        ).data[0].values

        # Prepare metadata
        metadata = {
            "user_id": user_id,
            "type": "episode",
            "summary": episode.summary[:500],  # Limit metadata size
            "outcome": episode.outcome[:500],
            "timestamp": episode.timestamp.isoformat(),
            "sentiment": episode.sentiment or "neutral",
        }

        # Store in Pinecone
        self.index.upsert(vectors=[{
            "id": episode.episode_id,
            "values": embedding,
            "metadata": metadata,
        }])

    async def recall_episodes(
        self,
        user_id: str,
        context: str,
        top_k: int = 5,
        min_score: float = 0.6,
    ) -> List["Episode"]:
        """Recall similar past episodes using semantic search."""

        # Generate query embedding
        query_embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[context],
            parameters={"input_type": "query"},
        ).data[0].values

        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            filter={
                "user_id": user_id,
                "type": "episode",
            },
            top_k=top_k,
            include_metadata=True,
        )

        # Convert matches to Episode objects
        from skills.adk_adaptive_memory.memory_models import Episode

        episodes = []
        for match in results.matches:
            if match.score >= min_score:
                meta = match.metadata
                episode = Episode(
                    episode_id=match.id,
                    user_id=user_id,
                    timestamp=datetime.fromisoformat(meta["timestamp"]),
                    summary=meta["summary"],
                    context={},  # Full context not stored in metadata
                    outcome=meta["outcome"],
                    sentiment=meta.get("sentiment"),
                )
                episodes.append(episode)

        return episodes

    async def store_fact(
        self,
        user_id: str,
        fact: "SemanticFact",
    ):
        """Store semantic fact."""

        text = f"{fact.category}: {fact.fact}"

        embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[text],
            parameters={"input_type": "passage"},
        ).data[0].values

        metadata = {
            "user_id": user_id,
            "type": "fact",
            "category": fact.category,
            "fact": fact.fact[:500],
            "confidence": fact.confidence,
            "learned_at": fact.learned_at.isoformat(),
            "last_accessed": fact.last_accessed.isoformat(),
            "access_count": fact.access_count,
        }

        self.index.upsert(vectors=[{
            "id": fact.fact_id,
            "values": embedding,
            "metadata": metadata,
        }])

    async def recall_facts(
        self,
        user_id: str,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
    ) -> List["SemanticFact"]:
        """Recall facts using semantic search."""

        query_embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={"input_type": "query"},
        ).data[0].values

        filter_dict = {
            "user_id": user_id,
            "type": "fact",
        }
        if category:
            filter_dict["category"] = category

        results = self.index.query(
            vector=query_embedding,
            filter=filter_dict,
            top_k=top_k,
            include_metadata=True,
        )

        from skills.adk_adaptive_memory.memory_models import SemanticFact

        facts = []
        for match in results.matches:
            meta = match.metadata
            fact = SemanticFact(
                fact_id=match.id,
                user_id=user_id,
                category=meta["category"],
                fact=meta["fact"],
                confidence=meta["confidence"],
                learned_at=datetime.fromisoformat(meta["learned_at"]),
                last_accessed=datetime.fromisoformat(meta["last_accessed"]),
                access_count=meta.get("access_count", 0),
            )
            facts.append(fact)

        return facts

    def delete_user_memories(self, user_id: str):
        """Delete all memories for a user (GDPR compliance)."""
        # Delete all vectors with user_id metadata
        self.index.delete(filter={"user_id": user_id})

    def get_memory_stats(self, user_id: str) -> dict:
        """Get statistics about stored memories."""
        # Query counts by type
        stats = {}

        for memory_type in ["preference", "episode", "fact"]:
            results = self.index.query(
                vector=[0.0] * self.dimension,  # Dummy vector
                filter={
                    "user_id": user_id,
                    "type": memory_type,
                },
                top_k=10000,  # Get all
                include_metadata=False,
            )
            stats[f"{memory_type}_count"] = len(results.matches)

        return stats

# ============================================================================
# PINECONE-BACKED ADAPTIVE AGENT
# ============================================================================

class PineconeAdaptiveAgent:
    """Adaptive agent using Pinecone for long-term memory."""

    def __init__(
        self,
        user_id: str,
        base_instruction: str,
        pinecone_api_key: str,
        model: str = "gemini-2.5-flash",
    ):
        self.user_id = user_id
        self.base_instruction = base_instruction
        self.model = model

        # Initialize Pinecone store
        self.memory_store = PineconeMemoryStore(
            api_key=pinecone_api_key,
            index_name="adaptive-agent-memories",
        )

        # Local working memory
        self.working_memory = []

        # Create agent
        self.agent = LlmAgent(
            name=f"pinecone_agent_{user_id}",
            model=model,
            instruction=base_instruction,
        )

    async def invoke(self, user_input: str) -> str:
        """Invoke with memory retrieval and storage."""

        # 1. Recall relevant preferences from Pinecone
        relevant_prefs = await self.memory_store.recall_preferences(
            user_id=self.user_id,
            context=user_input,
            top_k=5,
        )

        # 2. Recall similar past episodes
        similar_episodes = await self.memory_store.recall_episodes(
            user_id=self.user_id,
            context=user_input,
            top_k=3,
        )

        # 3. Build enhanced context
        enhanced_instruction = self.base_instruction

        if relevant_prefs:
            enhanced_instruction += "\n\n## User Preferences"
            for pref in relevant_prefs:
                enhanced_instruction += (
                    f"\n- {pref.category}: {pref.preference} "
                    f"(confidence: {pref.confidence:.2f})"
                )

        if similar_episodes:
            enhanced_instruction += "\n\n## Similar Past Interactions"
            for ep in similar_episodes:
                enhanced_instruction += (
                    f"\n- {ep.timestamp.strftime('%Y-%m-%d')}: {ep.summary[:50]}..."
                )

        # 4. Create temporary agent with enhanced context
        temp_agent = LlmAgent(
            name=f"enhanced_{self.user_id}",
            model=self.model,
            instruction=enhanced_instruction,
        )

        # 5. Invoke agent
        response = await temp_agent.invoke(user_input)

        # 6. Store episode
        from skills.adk_adaptive_memory.memory_models import Episode

        episode = Episode(
            episode_id=f"ep_{self.user_id}_{datetime.now().timestamp()}",
            user_id=self.user_id,
            timestamp=datetime.now(),
            summary=user_input,
            context={"input_length": len(user_input)},
            outcome=response,
        )
        await self.memory_store.store_episode(self.user_id, episode)

        # 7. Learn preferences (simple example)
        await self._learn_from_interaction(user_input, response)

        return response

    async def _learn_from_interaction(self, user_input: str, response: str):
        """Extract and store learnings from interaction."""
        from skills.adk_adaptive_memory.memory_models import UserPreference

        # Detect communication style preference
        if len(user_input.split()) < 15:
            pref = UserPreference(
                category="response_length",
                preference="User prefers concise responses",
                confidence=0.4,
                evidence=[user_input],
                learned_at=datetime.now(),
                last_confirmed=datetime.now(),
            )
            await self.memory_store.store_preference(self.user_id, pref)

    async def provide_feedback(self, rating: int):
        """Update preferences based on feedback."""
        # Retrieve recent preferences
        recent_prefs = await self.memory_store.recall_preferences(
            user_id=self.user_id,
            context="recent interaction",
            top_k=5,
        )

        # Adjust confidence based on feedback
        for pref in recent_prefs:
            if rating >= 4:
                pref.confidence = min(1.0, pref.confidence + 0.1)
            elif rating <= 2:
                pref.confidence = max(0.0, pref.confidence - 0.2)

            pref.confirmation_count += 1
            pref.last_confirmed = datetime.now()

            # Update in Pinecone
            await self.memory_store.store_preference(self.user_id, pref)

    async def export_memories(self) -> dict:
        """Export all memories for user."""
        stats = self.memory_store.get_memory_stats(self.user_id)

        # Retrieve all memories
        all_prefs = await self.memory_store.recall_preferences(
            user_id=self.user_id,
            context="all preferences",
            top_k=100,
            min_score=0.0,
        )

        all_episodes = await self.memory_store.recall_episodes(
            user_id=self.user_id,
            context="all episodes",
            top_k=100,
            min_score=0.0,
        )

        return {
            "user_id": self.user_id,
            "stats": stats,
            "preferences": [asdict(p) for p in all_prefs],
            "episodes": [asdict(e) for e in all_episodes],
        }

    async def delete_all_memories(self):
        """Delete all user memories (GDPR right to be forgotten)."""
        self.memory_store.delete_user_memories(self.user_id)

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_basic_usage():
    """Basic usage with Pinecone memory."""

    agent = PineconeAdaptiveAgent(
        user_id="user_001",
        base_instruction="You are a helpful coding assistant.",
        pinecone_api_key="your-api-key-here",
    )

    # First interaction
    response1 = await agent.invoke("Quick: explain list comprehensions")
    print(f"Response 1: {response1}\n")

    # Second interaction - similar topic
    response2 = await agent.invoke("Show me dictionary comprehension example")
    # Agent recalls similar past episode about list comprehensions
    print(f"Response 2: {response2}\n")

    # Provide feedback
    await agent.provide_feedback(rating=5)

    # Third interaction
    response3 = await agent.invoke("What about generator expressions?")
    # Agent applies learned preference for concise, example-based responses
    print(f"Response 3: {response3}\n")

async def example_multi_session():
    """Multiple sessions with persistent memory."""

    # Session 1
    print("=== SESSION 1 ===")
    agent1 = PineconeAdaptiveAgent(
        user_id="user_002",
        base_instruction="You are a Python tutor.",
        pinecone_api_key="your-api-key-here",
    )

    await agent1.invoke("I'm learning Python. What are classes?")
    await agent1.invoke("Give me a simple example")

    # Session 2 (next day) - same user_id
    print("\n=== SESSION 2 ===")
    agent2 = PineconeAdaptiveAgent(
        user_id="user_002",  # Same user
        base_instruction="You are a Python tutor.",
        pinecone_api_key="your-api-key-here",
    )

    # Agent automatically recalls preferences and past context
    await agent2.invoke("Tell me about inheritance")
    # Remembers user is beginner, prefers simple examples

async def example_semantic_search():
    """Demonstrate semantic memory retrieval."""

    agent = PineconeAdaptiveAgent(
        user_id="user_003",
        base_instruction="You are a helpful assistant.",
        pinecone_api_key="your-api-key-here",
    )

    # Store varied interactions
    await agent.invoke("How do I deploy a Flask app?")
    await agent.invoke("What's the best way to structure a Django project?")
    await agent.invoke("Explain Docker containers")
    await agent.invoke("Help with Kubernetes deployment")

    # Later query - semantically similar to multiple past interactions
    await agent.invoke("I need to deploy my Python web application")
    # Recalls relevant episodes about Flask, Django, Docker, Kubernetes

async def example_gdpr_compliance():
    """GDPR-compliant memory management."""

    agent = PineconeAdaptiveAgent(
        user_id="user_004",
        base_instruction="You are helpful.",
        pinecone_api_key="your-api-key-here",
    )

    # User interactions
    await agent.invoke("Help me with Python")
    await agent.invoke("Show me examples")

    # User requests data export
    exported_data = await agent.export_memories()
    print(f"Exported data: {json.dumps(exported_data, indent=2, default=str)}")

    # User exercises right to be forgotten
    await agent.delete_all_memories()
    print("All memories deleted")

    # Verify deletion
    stats = agent.memory_store.get_memory_stats("user_004")
    print(f"Stats after deletion: {stats}")
    # Should show 0 for all counts

# ============================================================================
# TESTING
# ============================================================================

import pytest

@pytest.mark.asyncio
async def test_preference_storage_retrieval():
    """Test storing and retrieving preferences."""
    from skills.adk_adaptive_memory.memory_models import UserPreference

    store = PineconeMemoryStore(api_key="test-key")

    # Store preference
    pref = UserPreference(
        category="test",
        preference="Test preference",
        confidence=0.8,
        evidence=["test"],
        learned_at=datetime.now(),
        last_confirmed=datetime.now(),
    )

    await store.store_preference("test_user", pref)

    # Retrieve
    retrieved = await store.recall_preferences(
        user_id="test_user",
        context="test preference",
        top_k=1,
    )

    assert len(retrieved) > 0
    assert retrieved[0].category == "test"

@pytest.mark.asyncio
async def test_semantic_episode_search():
    """Test semantic search for episodes."""
    from skills.adk_adaptive_memory.memory_models import Episode

    store = PineconeMemoryStore(api_key="test-key")

    # Store episodes
    ep1 = Episode(
        episode_id="ep1",
        user_id="test_user",
        timestamp=datetime.now(),
        summary="How to deploy Flask application",
        context={},
        outcome="Explained deployment process",
    )

    await store.store_episode("test_user", ep1)

    # Search with semantically similar query
    results = await store.recall_episodes(
        user_id="test_user",
        context="deploying Python web app",  # Similar but different words
        top_k=5,
    )

    assert len(results) > 0

# ============================================================================
# RUN EXAMPLES
# ============================================================================

if __name__ == "__main__":
    import asyncio

    print("Example 1: Basic Usage")
    print("=" * 50)
    asyncio.run(example_basic_usage())

    print("\n\nExample 2: Multi-Session")
    print("=" * 50)
    asyncio.run(example_multi_session())

    print("\n\nExample 3: Semantic Search")
    print("=" * 50)
    asyncio.run(example_semantic_search())

    print("\n\nExample 4: GDPR Compliance")
    print("=" * 50)
    asyncio.run(example_gdpr_compliance())
```

## Production Configuration

### Index Configuration

```python
# Production Pinecone configuration
PINECONE_CONFIG = {
    "development": {
        "index_name": "dev-user-memories",
        "dimension": 768,
        "metric": "cosine",
        "spec": ServerlessSpec(cloud="aws", region="us-east-1"),
    },
    "production": {
        "index_name": "prod-user-memories",
        "dimension": 768,
        "metric": "cosine",
        "spec": ServerlessSpec(cloud="aws", region="us-west-2"),
        "deletion_protection": "enabled",
    },
}
```

### Monitoring

```python
class MonitoredPineconeStore(PineconeMemoryStore):
    """Pinecone store with monitoring."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_count = 0
        self.upsert_count = 0

    async def recall_preferences(self, *args, **kwargs):
        self.query_count += 1
        return await super().recall_preferences(*args, **kwargs)

    async def store_preference(self, *args, **kwargs):
        self.upsert_count += 1
        return await super().store_preference(*args, **kwargs)

    def get_metrics(self) -> dict:
        return {
            "queries": self.query_count,
            "upserts": self.upsert_count,
            "qps": self.query_count / 3600,  # Assuming hourly reset
        }
```
