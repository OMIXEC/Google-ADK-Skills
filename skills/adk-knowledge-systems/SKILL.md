---
name: ADK Knowledge & Memory Systems
description: This skill should be used when the user asks to "build RAG", "vector search", "agent memory", "knowledge base", "semantic search", or "pinecone integration". Provides comprehensive guidance for implementing memory systems, knowledge bases, and retrieval-augmented generation (RAG) for agents.
version: 1.0.0
---

# ADK Knowledge & Memory Systems

Agents need to remember information and learn from documents. This skill covers working memory, shared memory, persistent storage, and RAG (Retrieval-Augmented Generation).

## Memory Types

### Working Memory

Short-term context for the current request:
```python
# Automatic with context window
agent.working_memory = {
    "current_task": "Analyze market trends",
    "research_findings": [...],
    "interim_results": {...}
}
```

Always available, cleared between sessions.

### Shared Memory

Cross-agent coordination:
```python
from adk_bidi.memory import SharedMemory

shared = SharedMemory()

# Agent 1 stores finding
shared.store("market_analysis", research_data)

# Agent 2 retrieves
data = shared.retrieve("market_analysis")
```

Enables agents to build on each other's work.

### Persistent Memory

Long-term storage with Pinecone:
```python
from adk_bidi.memory import PersistentMemory

memory = PersistentMemory(
    storage="pinecone",
    api_key=os.getenv("PINECONE_API_KEY"),
    index_name="agent_memory"
)

# Store
memory.store(key="conversation_123", value=conversation_data)

# Retrieve
past_context = memory.retrieve(key="conversation_123")
```

Persists across sessions and agents.

## RAG (Retrieval-Augmented Generation)

RAG enables agents to learn from documents by searching and injecting relevant context:

### Basic RAG Pipeline

```python
from adk_bidi.memory import RAGSystem

# 1. Ingest documents
rag = RAGSystem(
    documents_path="path/to/documents",
    storage="pinecone",
    api_key=os.getenv("PINECONE_API_KEY")
)

# 2. Store embeddings
rag.ingest_documents()

# 3. Retrieve relevant context
query = "How do we handle customer refunds?"
relevant_docs = rag.search(query, limit=5)

# 4. Inject into prompt
context = "\n".join([doc.content for doc in relevant_docs])
prompt_with_context = f"""
Context from knowledge base:
{context}

User question: {user_query}
"""

# 5. Agent answers with context
response = agent.ask(prompt_with_context)
```

### Document Types

RAG supports multiple document types:

**Text Documents**
```python
rag.ingest_documents(
    format="text",
    file_patterns=["*.txt", "*.md"]
)
```

**PDFs**
```python
rag.ingest_documents(
    format="pdf",
    file_patterns=["*.pdf"]
)
```

**Code Files**
```python
rag.ingest_documents(
    format="code",
    file_patterns=["*.py", "*.js", "*.ts"]
)
```

**Structured Data**
```python
rag.ingest_documents(
    format="json",
    file_patterns=["*.json"]
)
```

### Multimodal RAG

Support images and other modalities:
```python
rag.ingest_documents(
    format="multimodal",
    file_patterns=["*.pdf", "*.txt", "*.png", "*.jpg"],
    enable_vision=True
)
```

## Integration with Agents

### Inject Knowledge into Agent

```python
class KnowledgeEnabledAgent(Agent):
    def __init__(self, rag_system):
        super().__init__()
        self.rag = rag_system
        self.knowledge_base = rag_system

    def ask_with_knowledge(self, question: str) -> str:
        # Search knowledge base
        relevant_docs = self.rag.search(question, limit=5)

        # Build context
        context = "\n".join([
            f"- {doc.source}: {doc.content[:500]}"
            for doc in relevant_docs
        ])

        # Ask with context
        enhanced_prompt = f"""
Context from knowledge base:
{context}

User question: {question}

Answer using the knowledge base context above.
"""

        return self.ask(enhanced_prompt)
```

### Add Memory to Agent

```python
agent = MyAgent()

# Add persistent memory
agent.memory = PersistentMemory(
    storage="pinecone",
    api_key=os.getenv("PINECONE_API_KEY")
)

# Agent automatically remembers past interactions
agent.remember_interaction(question, response)
```

## Pinecone Setup

### Create Index

```python
from pinecone import Pinecone

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create index
pc.create_index(
    name="agent-memory",
    dimension=1536,
    metric="cosine"
)
```

### Embed and Store Documents

```python
from langchain.embeddings import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings()

# Embed documents
vectors = [
    {
        "id": f"doc_{i}",
        "values": embeddings.embed_query(doc.content),
        "metadata": {"source": doc.source, "content": doc.content}
    }
    for i, doc in enumerate(documents)
]

# Store in Pinecone
index = pc.Index("agent-memory")
index.upsert(vectors=vectors)
```

### Search and Retrieve

```python
# Search vector database
query_vector = embeddings.embed_query(user_query)
results = index.query(
    vector=query_vector,
    top_k=5,
    include_metadata=True
)

# Extract documents
relevant_docs = [
    {
        "source": r["metadata"]["source"],
        "content": r["metadata"]["content"],
        "score": r["score"]
    }
    for r in results["matches"]
]
```

## Memory Management

### Store Information

```python
# Store to persistent memory
memory.store(
    key=f"conversation_{session_id}",
    value={
        "messages": conversation_history,
        "summary": conversation_summary,
        "topics": extracted_topics
    },
    metadata={"user_id": user_id, "date": datetime.now()}
)
```

### Retrieve Information

```python
# Retrieve from persistent memory
context = memory.retrieve(
    key=f"conversation_{session_id}",
    retrieve_metadata=True
)

past_topics = context.get("topics", [])
previous_messages = context.get("messages", [])
```

### Update Information

```python
# Update existing memory
memory.update(
    key=f"conversation_{session_id}",
    value={"messages": updated_messages},
    merge=True  # Merge with existing
)
```

### Clean Up

```python
# Remove old conversations
memory.delete(key=f"conversation_{old_session_id}")

# Bulk delete by metadata
memory.delete_by_metadata(
    metadata={"date_before": old_date}
)
```

## Best Practices

**Do:**
- Use relevant query for searches (specific vs generic)
- Limit search results to most relevant (top 5-10)
- Update memory after each interaction
- Version your documents for updates
- Monitor vector quality and recall

**Don't:**
- Store PII without encryption
- Forget to update embeddings after document changes
- Search with vague queries
- Overload context window with all documents
- Skip metadata for filtering

## Supporting Resources

### References
- **`references/memory-types.md`** - Detailed memory system descriptions
- **`references/rag-patterns.md`** - RAG implementation patterns
- **`references/pinecone-guide.md`** - Pinecone setup and operations

### Examples
- **`examples/rag-system.py`** - Complete RAG implementation
- **`examples/memory-agent.py`** - Agent with persistent memory
- **`examples/multimodal-rag.py`** - Multimodal RAG example

## Next Steps

1. **Choose memory type** - What do you need?
2. **Set up Pinecone** - Create index if using persistent memory
3. **Ingest documents** - Load your knowledge base
4. **Implement RAG** - Search and inject context
5. **Test** - Verify memory and retrieval work
6. **Deploy** - Use adk-production-deployment skill

See **adk-custom-agent-builder** skill for agent implementation.

See **adk-multi-agent-workflows** skill for sharing memory across agents.
