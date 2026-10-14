"""
PersistentMemoryStore - Long-term memory persistence with Pinecone.

Provides vector-based semantic memory storage using Pinecone
for multimodal embeddings and retrieval.
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

try:
    from pinecone import Pinecone, EmbedModel
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False


@dataclass
class MemoryRecord:
    """A record in persistent memory."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    importance: float = 0.5
    agent_id: str = ""
    modality: str = "text"  # text, image, audio, video


class PersistentMemoryStore:
    """
    Long-term memory persistence with Pinecone.

    Provides vector-based storage for semantic memory that persists
    across sessions. Supports multimodal content through different
    embedding models.

    Example:
        store = PersistentMemoryStore(index_name="agent-memory")
        store.store_memory("mem1", "Important fact about Python", {"topic": "programming"})
        results = store.recall("What is Python?", top_k=5)
    """

    # Embedding model mappings
    EMBED_MODELS = {
        "text": "multilingual-e5-large",
        "image": "pinecone-clip-vit-base-patch32",
    }

    def __init__(
        self,
        index_name: str = "agent-memory",
        api_key: Optional[str] = None,
        index_host: Optional[str] = None,
        namespace: str = "default",
    ):
        """
        Initialize persistent memory store.

        Args:
            index_name: Name of the Pinecone index
            api_key: Pinecone API key (defaults to PINECONE_API_KEY env var)
            index_host: Pinecone index host (defaults to PINECONE_INDEX_HOST env var)
            namespace: Namespace for organizing memories
        """
        if not PINECONE_AVAILABLE:
            raise ImportError(
                "Pinecone is required for PersistentMemoryStore. "
                "Install with: pip install pinecone"
            )

        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.index_host = index_host or os.getenv("PINECONE_INDEX_HOST")
        self.namespace = namespace

        if not self.api_key:
            raise ValueError("Pinecone API key is required")
        if not self.index_host:
            raise ValueError("Pinecone index host is required")

        self.pc = Pinecone(api_key=self.api_key)
        self.index = self.pc.Index(host=self.index_host)

    def embed_text(self, text: str, input_type: str = "passage") -> List[float]:
        """
        Generate text embedding.

        Args:
            text: Text to embed
            input_type: "passage" for storage, "query" for retrieval

        Returns:
            Embedding vector
        """
        result = self.pc.inference.embed(
            model=EmbedModel.Multilingual_E5_Large,
            inputs=[text],
            parameters={"input_type": input_type, "truncate": "END"}
        )
        return result.data[0].values

    def embed_image(self, image_base64: str) -> List[float]:
        """
        Generate image embedding.

        Args:
            image_base64: Base64-encoded image data

        Returns:
            Embedding vector
        """
        result = self.pc.inference.embed(
            model="pinecone-clip-vit-base-patch32",
            inputs=[{"image": image_base64}],
            parameters={"input_type": "image"}
        )
        return result.data[0].values

    def embed_audio(self, audio_base64: str) -> List[float]:
        """
        Generate audio embedding via transcription.

        Args:
            audio_base64: Base64-encoded audio data

        Returns:
            Embedding vector (from transcribed text)
        """
        # Transcribe audio first
        transcription = self.pc.inference.transcribe(
            model="openai-whisper-large-v3",
            audio=audio_base64
        )
        # Then embed the transcription
        return self.embed_text(transcription.text)

    def store_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
        agent_id: str = "",
        modality: str = "text",
    ) -> bool:
        """
        Store a memory in persistent storage.

        Args:
            memory_id: Unique identifier for the memory
            content: The content to store
            metadata: Additional metadata
            importance: Importance score (0.0 to 1.0)
            agent_id: ID of the storing agent
            modality: Content type ("text", "image", "audio")

        Returns:
            True if storage succeeded
        """
        try:
            # Generate embedding based on modality
            if modality == "text":
                embedding = self.embed_text(content)
            elif modality == "image":
                embedding = self.embed_image(content)
            elif modality == "audio":
                embedding = self.embed_audio(content)
            else:
                embedding = self.embed_text(content)

            # Prepare metadata
            full_metadata = {
                "content": content[:1000] if len(content) > 1000 else content,  # Truncate for metadata
                "importance": importance,
                "agent_id": agent_id,
                "modality": modality,
                "created_at": datetime.now().isoformat(),
                **(metadata or {}),
            }

            # Upsert to Pinecone
            self.index.upsert(
                vectors=[{
                    "id": memory_id,
                    "values": embedding,
                    "metadata": full_metadata,
                }],
                namespace=self.namespace,
            )

            return True

        except Exception as e:
            print(f"Error storing memory {memory_id}: {e}")
            return False

    def recall(
        self,
        query: str,
        top_k: int = 5,
        agent_id: Optional[str] = None,
        modality: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Recall memories similar to a query.

        Args:
            query: Text query or embedding
            top_k: Number of results to return
            agent_id: Filter by agent ID
            modality: Filter by content modality
            min_score: Minimum similarity score

        Returns:
            List of matching memories with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embed_text(query, input_type="query")

            # Build filter
            filter_dict = {}
            if agent_id:
                filter_dict["agent_id"] = agent_id
            if modality:
                filter_dict["modality"] = modality

            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=self.namespace,
                filter=filter_dict if filter_dict else None,
            )

            # Format results
            memories = []
            for match in results.matches:
                if match.score >= min_score:
                    memories.append({
                        "id": match.id,
                        "content": match.metadata.get("content", ""),
                        "score": match.score,
                        "importance": match.metadata.get("importance", 0.5),
                        "agent_id": match.metadata.get("agent_id", ""),
                        "modality": match.metadata.get("modality", "text"),
                        "created_at": match.metadata.get("created_at", ""),
                        "metadata": {
                            k: v for k, v in match.metadata.items()
                            if k not in ("content", "importance", "agent_id", "modality", "created_at")
                        },
                    })

            return memories

        except Exception as e:
            print(f"Error recalling memories: {e}")
            return []

    def recall_multimodal(
        self,
        text_query: Optional[str] = None,
        image_query: Optional[str] = None,
        audio_query: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Recall memories using multimodal query.

        Supports cross-modal search (e.g., find images with text query).

        Args:
            text_query: Optional text query
            image_query: Optional base64 image query
            audio_query: Optional base64 audio query
            top_k: Number of results

        Returns:
            List of matching memories
        """
        if text_query:
            query_embedding = self.embed_text(text_query, input_type="query")
        elif image_query:
            query_embedding = self.embed_image(image_query)
        elif audio_query:
            query_embedding = self.embed_audio(audio_query)
        else:
            return []

        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=self.namespace,
            )

            return [
                {
                    "id": match.id,
                    "content": match.metadata.get("content", ""),
                    "score": match.score,
                    "modality": match.metadata.get("modality", "text"),
                }
                for match in results.matches
            ]

        except Exception as e:
            print(f"Error in multimodal recall: {e}")
            return []

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        try:
            self.index.delete(ids=[memory_id], namespace=self.namespace)
            return True
        except Exception as e:
            print(f"Error deleting memory {memory_id}: {e}")
            return False

    def delete_by_agent(self, agent_id: str) -> bool:
        """Delete all memories from a specific agent."""
        try:
            self.index.delete(
                filter={"agent_id": agent_id},
                namespace=self.namespace,
            )
            return True
        except Exception as e:
            print(f"Error deleting memories for agent {agent_id}: {e}")
            return False

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by ID."""
        try:
            result = self.index.fetch(ids=[memory_id], namespace=self.namespace)
            if memory_id in result.vectors:
                vec = result.vectors[memory_id]
                return {
                    "id": memory_id,
                    "content": vec.metadata.get("content", ""),
                    "metadata": vec.metadata,
                }
            return None
        except Exception as e:
            print(f"Error fetching memory {memory_id}: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "namespaces": {
                    ns: data.vector_count
                    for ns, data in stats.namespaces.items()
                },
                "dimension": stats.dimension,
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}


class InMemoryPersistentStore:
    """
    In-memory implementation for testing without Pinecone.

    Provides the same interface as PersistentMemoryStore but stores
    everything in memory. Useful for development and testing.
    """

    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self.memories: Dict[str, MemoryRecord] = {}

    def store_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
        agent_id: str = "",
        modality: str = "text",
    ) -> bool:
        self.memories[memory_id] = MemoryRecord(
            id=memory_id,
            content=content,
            metadata=metadata or {},
            importance=importance,
            agent_id=agent_id,
            modality=modality,
        )
        return True

    def recall(
        self,
        query: str,
        top_k: int = 5,
        agent_id: Optional[str] = None,
        modality: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        # Simple keyword matching for testing
        query_lower = query.lower()
        results = []

        for memory in self.memories.values():
            if agent_id and memory.agent_id != agent_id:
                continue
            if modality and memory.modality != modality:
                continue

            # Simple relevance score based on keyword overlap
            content_lower = memory.content.lower()
            words = query_lower.split()
            matches = sum(1 for w in words if w in content_lower)
            score = matches / len(words) if words else 0

            if score >= min_score:
                results.append({
                    "id": memory.id,
                    "content": memory.content,
                    "score": score,
                    "importance": memory.importance,
                    "agent_id": memory.agent_id,
                    "modality": memory.modality,
                    "metadata": memory.metadata,
                })

        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_memory(self, memory_id: str) -> bool:
        if memory_id in self.memories:
            del self.memories[memory_id]
            return True
        return False

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        if memory_id in self.memories:
            mem = self.memories[memory_id]
            return {
                "id": mem.id,
                "content": mem.content,
                "metadata": mem.metadata,
            }
        return None

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_vectors": len(self.memories),
            "namespaces": {self.namespace: len(self.memories)},
        }
