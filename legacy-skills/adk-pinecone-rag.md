# adk-pinecone-rag

**Pinecone Vector Database RAG Pipeline for Google ADK**

Build production-grade RAG (Retrieval-Augmented Generation) pipelines using Pinecone vector database with ADK agents. Ingest documents, generate embeddings, and create intelligent knowledge-powered agents.

## When to Use

Use this skill when:
- Building knowledge-based Q&A systems
- Creating documentation assistants
- Semantic search over large document collections
- Agent needs persistent long-term memory
- Hybrid search (semantic + keyword)
- Multi-tenant RAG applications

## Quick Start

```bash
# Create Pinecone index and RAG agent
/adk-pinecone-rag --action "setup" --index_name "knowledge_base"

# Ingest documents
/adk-pinecone-rag --action "ingest" --source "docs/" --namespace "product_docs"

# Create RAG-enabled agent
/adk-pinecone-rag --action "create_agent" --index_name "knowledge_base"

# Query the RAG system
/adk-pinecone-rag --action "query" --question "How do I configure MCP?"
```

## Parameters

```bash
--action "setup|ingest|create_agent|query"  # Required action
--index_name "name"                          # Pinecone index name
--namespace "namespace"                      # Logical partition
--source "path_or_url"                       # Document source
--embedding_model "multilingual-e5-large"    # Embedding model
--dimension 1024                             # Vector dimension
--top_k 10                                   # Results to retrieve
--hybrid_search true|false                   # Enable hybrid search
--reranker "cohere|none"                     # Optional reranker
```

## Pinecone Setup

### 1. Create Serverless Index

```bash
/adk-pinecone-rag --action "setup" \
  --index_name "my_knowledge_base" \
  --dimension 1024 \
  --metric "cosine"
```

**Generated Code:**
```python
from pinecone import (
    Pinecone,
    ServerlessSpec,
    CloudProvider,
    AwsRegion,
    VectorType
)
import os

# Initialize Pinecone client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create serverless index
index_config = pc.create_index(
    name="my_knowledge_base",
    dimension=1024,  # Match your embedding model
    spec=ServerlessSpec(
        cloud=CloudProvider.AWS,
        region=AwsRegion.US_EAST_1
    ),
    vector_type=VectorType.DENSE,
    metric="cosine"
)

print(f"Index created: {index_config.name}")
print(f"Host: {index_config.host}")

# Store host for later use
INDEX_HOST = index_config.host
```

### 2. Create Index for Specific Model

```bash
/adk-pinecone-rag --action "setup" \
  --index_name "e5_knowledge_base" \
  --embedding_model "multilingual-e5-large"
```

**Generated Code:**
```python
from pinecone import Pinecone, CloudProvider, AwsRegion, EmbedModel, IndexEmbed

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create index configured for specific embedding model
index_config = pc.create_index_for_model(
    name="e5_knowledge_base",
    cloud=CloudProvider.AWS,
    region=AwsRegion.US_EAST_1,
    embed=IndexEmbed(
        model=EmbedModel.Multilingual_E5_Large,
        field_map={"text": "content"}  # Map 'content' field to embeddings
    )
)

print(f"Index created with integrated embeddings: {index_config.name}")
INDEX_HOST = index_config.host
```

## Document Ingestion

### 3. Ingest Documents with Pinecone Inference

```bash
/adk-pinecone-rag --action "ingest" \
  --index_name "knowledge_base" \
  --source "docs/" \
  --namespace "product_docs"
```

**Generated Code:**
```python
from pinecone import Pinecone, EmbedModel
from pathlib import Path
import hashlib

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def ingest_documents(source_path: str, namespace: str = "default"):
    """Ingest documents from a directory."""
    documents = []
    source = Path(source_path)

    # Read all documents
    for file_path in source.glob("**/*"):
        if file_path.suffix in [".txt", ".md", ".pdf"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Chunk the document
            chunks = chunk_text(content)
            for i, chunk in enumerate(chunks):
                doc_id = hashlib.md5(f"{file_path}_{i}".encode()).hexdigest()
                documents.append({
                    "id": doc_id,
                    "text": chunk,
                    "metadata": {
                        "source": str(file_path),
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                })

    print(f"Processing {len(documents)} chunks...")

    # Generate embeddings using Pinecone Inference API
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]

        # Generate embeddings
        embeddings_response = pc.inference.embed(
            model=EmbedModel.Multilingual_E5_Large,
            inputs=[doc["text"] for doc in batch],
            parameters={
                "input_type": "passage",
                "truncate": "END"
            }
        )

        # Prepare vectors for upsert
        vectors = []
        for j, doc in enumerate(batch):
            vectors.append({
                "id": doc["id"],
                "values": embeddings_response.data[j].values,
                "metadata": {
                    **doc["metadata"],
                    "text": doc["text"]
                }
            })

        # Upsert to Pinecone
        index.upsert(
            vectors=vectors,
            namespace=namespace
        )

        print(f"Upserted {i + len(batch)}/{len(documents)} vectors")

    print(f"Ingestion complete: {len(documents)} vectors in namespace '{namespace}'")

# Run ingestion
ingest_documents("docs/", namespace="product_docs")
```

### 4. Ingest with Automatic Embeddings

For indexes created with `create_index_for_model`:

```python
from pinecone import Pinecone

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

# Upsert records - embeddings generated automatically
index.upsert_records(
    namespace="product_docs",
    records=[
        {
            "_id": "doc1",
            "content": "Google ADK is a framework for building AI agents.",
            "source": "adk_intro.md",
            "category": "documentation"
        },
        {
            "_id": "doc2",
            "content": "MCP allows agents to connect to external tools.",
            "source": "mcp_guide.md",
            "category": "tools"
        },
        {
            "_id": "doc3",
            "content": "LangGraph enables stateful multi-agent workflows.",
            "source": "langgraph_intro.md",
            "category": "orchestration"
        }
    ]
)

print("Records upserted with automatic embedding generation")
```

## RAG Agent Creation

### 5. Create RAG-Enabled ADK Agent

```bash
/adk-pinecone-rag --action "create_agent" \
  --index_name "knowledge_base" \
  --top_k 5 \
  --similarity_threshold 0.7
```

**Generated Code:**
```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from pinecone import Pinecone, EmbedModel
import os

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

def search_knowledge_base(
    query: str,
    namespace: str = "default",
    top_k: int = 5,
    filter_metadata: dict = None
) -> list[dict]:
    """
    Search the knowledge base using semantic similarity.

    Args:
        query: The search query
        namespace: Pinecone namespace to search
        top_k: Number of results to return
        filter_metadata: Optional metadata filters

    Returns:
        List of relevant documents with scores
    """
    # Generate query embedding
    query_embedding = pc.inference.embed(
        model=EmbedModel.Multilingual_E5_Large,
        inputs=[query],
        parameters={"input_type": "query", "truncate": "END"}
    )

    # Search Pinecone
    results = index.query(
        vector=query_embedding.data[0].values,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
        filter=filter_metadata
    )

    # Format results
    documents = []
    for match in results.matches:
        if match.score >= 0.7:  # Similarity threshold
            documents.append({
                "text": match.metadata.get("text", ""),
                "source": match.metadata.get("source", "unknown"),
                "score": match.score
            })

    return documents

def format_context(documents: list[dict]) -> str:
    """Format retrieved documents as context for the agent."""
    if not documents:
        return "No relevant documents found."

    context_parts = []
    for i, doc in enumerate(documents, 1):
        context_parts.append(
            f"[Source {i}: {doc['source']} (relevance: {doc['score']:.2f})]\n"
            f"{doc['text']}"
        )

    return "\n\n---\n\n".join(context_parts)

# RAG tool for the agent
def rag_search(query: str, namespace: str = "product_docs") -> str:
    """
    Search the knowledge base and return relevant information.

    Args:
        query: What to search for
        namespace: Which knowledge base to search

    Returns:
        Relevant context from the knowledge base
    """
    documents = search_knowledge_base(query, namespace=namespace, top_k=5)
    return format_context(documents)

# Create RAG-enabled agent
rag_agent = Agent(
    name="knowledge_assistant",
    model="gemini-2.5-flash",
    description="AI assistant with access to product documentation",
    instruction="""You are a knowledgeable assistant with access to a comprehensive knowledge base.

**Behavior:**
1. ALWAYS search the knowledge base before answering questions
2. Use the rag_search tool to find relevant information
3. Base your answers on the retrieved context
4. Cite sources when providing information
5. If no relevant information is found, acknowledge the limitation

**Response Format:**
- Provide clear, accurate answers based on retrieved context
- Include source citations: [Source: filename]
- If information is partial, note what's missing
- Suggest related topics if helpful

**When searching:**
- Use specific, targeted queries
- Search multiple times if needed for comprehensive answers
- Consider different phrasings for better results
""",
    tools=[
        FunctionTool(rag_search),
    ],
)

root_agent = rag_agent
```

## Advanced RAG Patterns

### 6. Hybrid Search (Semantic + Keyword)

```bash
/adk-pinecone-rag --action "create_agent" \
  --hybrid_search true \
  --alpha 0.5
```

**Generated Code:**
```python
from pinecone import Pinecone, EmbedModel
from pinecone.grpc import PineconeGRPC

# For hybrid search, use sparse-dense index
pc = PineconeGRPC(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

def hybrid_search(
    query: str,
    namespace: str = "default",
    top_k: int = 10,
    alpha: float = 0.5  # Balance between semantic (1.0) and keyword (0.0)
) -> list[dict]:
    """
    Perform hybrid search combining semantic and keyword matching.

    Args:
        query: Search query
        namespace: Pinecone namespace
        top_k: Number of results
        alpha: Weight for semantic vs keyword (0-1)

    Returns:
        Combined search results
    """
    # Generate dense embedding for semantic search
    dense_embedding = pc.inference.embed(
        model=EmbedModel.Multilingual_E5_Large,
        inputs=[query],
        parameters={"input_type": "query"}
    )

    # Generate sparse embedding for keyword search (BM25-style)
    sparse_embedding = pc.inference.embed(
        model="pinecone-sparse-english-v0",
        inputs=[query],
        parameters={"input_type": "query"}
    )

    # Hybrid query
    results = index.query(
        vector=dense_embedding.data[0].values,
        sparse_vector=sparse_embedding.data[0],
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
        alpha=alpha  # Hybrid weighting
    )

    return [
        {
            "text": m.metadata.get("text", ""),
            "source": m.metadata.get("source", ""),
            "score": m.score
        }
        for m in results.matches
    ]
```

### 7. Multi-Namespace RAG

Search across multiple knowledge domains.

```python
def multi_namespace_search(
    query: str,
    namespaces: list[str],
    top_k_per_namespace: int = 3
) -> dict[str, list[dict]]:
    """Search across multiple namespaces and combine results."""

    # Generate embedding once
    query_embedding = pc.inference.embed(
        model=EmbedModel.Multilingual_E5_Large,
        inputs=[query],
        parameters={"input_type": "query"}
    )

    all_results = {}

    for namespace in namespaces:
        results = index.query(
            vector=query_embedding.data[0].values,
            top_k=top_k_per_namespace,
            namespace=namespace,
            include_metadata=True
        )

        all_results[namespace] = [
            {
                "text": m.metadata.get("text", ""),
                "source": m.metadata.get("source", ""),
                "score": m.score
            }
            for m in results.matches
        ]

    return all_results

# Multi-domain RAG agent
def search_all_knowledge(query: str) -> str:
    """Search across all knowledge domains."""
    namespaces = ["product_docs", "api_reference", "tutorials", "faq"]
    results = multi_namespace_search(query, namespaces)

    context_parts = []
    for namespace, docs in results.items():
        if docs:
            context_parts.append(f"### {namespace.replace('_', ' ').title()}")
            for doc in docs:
                context_parts.append(f"- {doc['text'][:200]}... [Score: {doc['score']:.2f}]")

    return "\n".join(context_parts)
```

### 8. RAG with Metadata Filtering

```python
def filtered_search(
    query: str,
    category: str = None,
    date_after: str = None,
    language: str = "en"
) -> list[dict]:
    """Search with metadata filters."""

    query_embedding = pc.inference.embed(
        model=EmbedModel.Multilingual_E5_Large,
        inputs=[query],
        parameters={"input_type": "query"}
    )

    # Build filter
    metadata_filter = {}

    if category:
        metadata_filter["category"] = {"$eq": category}

    if date_after:
        metadata_filter["created_date"] = {"$gte": date_after}

    if language:
        metadata_filter["language"] = {"$eq": language}

    results = index.query(
        vector=query_embedding.data[0].values,
        top_k=10,
        namespace="documents",
        include_metadata=True,
        filter=metadata_filter if metadata_filter else None
    )

    return [
        {
            "text": m.metadata.get("text", ""),
            "category": m.metadata.get("category", ""),
            "source": m.metadata.get("source", ""),
            "score": m.score
        }
        for m in results.matches
    ]

# Filtered search tool
def search_docs_by_category(query: str, category: str) -> str:
    """
    Search documentation filtered by category.

    Args:
        query: What to search for
        category: Filter by category (api, guide, tutorial, reference)

    Returns:
        Relevant documents from the specified category
    """
    results = filtered_search(query, category=category)
    return format_context(results)
```

### 9. RAG with Reranking

```python
from google.adk.agents import Agent

def search_with_reranking(
    query: str,
    namespace: str = "default",
    initial_k: int = 20,
    final_k: int = 5
) -> list[dict]:
    """Search and rerank results for better relevance."""

    # Initial retrieval
    query_embedding = pc.inference.embed(
        model=EmbedModel.Multilingual_E5_Large,
        inputs=[query],
        parameters={"input_type": "query"}
    )

    results = index.query(
        vector=query_embedding.data[0].values,
        top_k=initial_k,
        namespace=namespace,
        include_metadata=True
    )

    # Use Pinecone reranking
    documents = [m.metadata.get("text", "") for m in results.matches]

    reranked = pc.inference.rerank(
        model="bge-reranker-v2-m3",
        query=query,
        documents=documents,
        top_n=final_k,
        return_documents=True
    )

    return [
        {
            "text": doc.document.text,
            "score": doc.score,
            "source": results.matches[doc.index].metadata.get("source", "")
        }
        for doc in reranked.data
    ]
```

## LangGraph Integration

### 10. RAG Pipeline with LangGraph

```python
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from google.adk.agents import Agent
from pinecone import Pinecone, EmbedModel

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

class RAGPipelineState(TypedDict):
    messages: Annotated[list, operator.add]
    query: str
    query_embedding: list[float]
    retrieved_docs: list[dict]
    reranked_docs: list[dict]
    response: str

def generate_embedding(state: RAGPipelineState) -> dict:
    """Step 1: Generate query embedding."""
    query = state["messages"][-1].content if state["messages"] else ""

    embedding = pc.inference.embed(
        model=EmbedModel.Multilingual_E5_Large,
        inputs=[query],
        parameters={"input_type": "query"}
    )

    return {
        "query": query,
        "query_embedding": embedding.data[0].values
    }

def retrieve_documents(state: RAGPipelineState) -> dict:
    """Step 2: Retrieve from Pinecone."""
    results = index.query(
        vector=state["query_embedding"],
        top_k=20,
        namespace="documents",
        include_metadata=True
    )

    docs = [
        {
            "id": m.id,
            "text": m.metadata.get("text", ""),
            "source": m.metadata.get("source", ""),
            "score": m.score
        }
        for m in results.matches
    ]

    return {"retrieved_docs": docs}

def rerank_documents(state: RAGPipelineState) -> dict:
    """Step 3: Rerank for relevance."""
    docs = state["retrieved_docs"]
    texts = [d["text"] for d in docs]

    reranked = pc.inference.rerank(
        model="bge-reranker-v2-m3",
        query=state["query"],
        documents=texts,
        top_n=5
    )

    reranked_docs = [
        {
            **docs[r.index],
            "rerank_score": r.score
        }
        for r in reranked.data
    ]

    return {"reranked_docs": reranked_docs}

def generate_response(state: RAGPipelineState) -> dict:
    """Step 4: Generate response with ADK agent."""
    context = "\n\n".join([
        f"[{d['source']}]: {d['text']}"
        for d in state["reranked_docs"]
    ])

    agent = Agent(
        name="rag_responder",
        model="gemini-2.5-flash",
        instruction=f"""Answer based on this context:

{context}

Rules:
- Only use provided context
- Cite sources
- Say if info is missing"""
    )

    result = agent.execute(state["query"])

    return {
        "response": result.content,
        "messages": [AIMessage(content=result.content)]
    }

# Build RAG pipeline graph
builder = StateGraph(RAGPipelineState)

builder.add_node("embed", generate_embedding)
builder.add_node("retrieve", retrieve_documents)
builder.add_node("rerank", rerank_documents)
builder.add_node("generate", generate_response)

builder.add_edge(START, "embed")
builder.add_edge("embed", "retrieve")
builder.add_edge("retrieve", "rerank")
builder.add_edge("rerank", "generate")
builder.add_edge("generate", END)

rag_pipeline = builder.compile()

# Usage
result = rag_pipeline.invoke({
    "messages": [HumanMessage(content="How do I configure MCP in ADK?")],
    "query": "",
    "query_embedding": [],
    "retrieved_docs": [],
    "reranked_docs": [],
    "response": ""
})

print(result["response"])
```

## MCP Integration

### 11. Pinecone MCP Server

```python
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Use Pinecone via MCP server
pinecone_agent = Agent(
    model="gemini-2.5-flash",
    name="pinecone_mcp_agent",
    instruction="Search and manage the vector knowledge base",
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="uvx",
                    args=["mcp-server-pinecone"],
                    env={
                        "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
                        "PINECONE_INDEX_HOST": os.getenv("PINECONE_INDEX_HOST"),
                    }
                ),
                timeout=30,
            ),
        )
    ],
)
```

## Generated Project Structure

```
pinecone-rag-agent/
+-- src/
|   +-- agent.py              # RAG-enabled ADK agent
|   +-- rag/
|   |   +-- __init__.py
|   |   +-- embeddings.py     # Embedding generation
|   |   +-- retriever.py      # Pinecone search
|   |   +-- reranker.py       # Reranking logic
|   |   +-- pipeline.py       # LangGraph pipeline
|   +-- ingestion/
|   |   +-- __init__.py
|   |   +-- chunker.py        # Text chunking
|   |   +-- loader.py         # Document loading
|   |   +-- ingest.py         # Ingestion pipeline
|   +-- config.py
|   +-- main.py
+-- scripts/
|   +-- setup_index.py
|   +-- ingest_docs.py
+-- tests/
+-- deployment/
|   +-- Dockerfile
|   +-- cloud_run.yaml
+-- requirements.txt
+-- README.md
```

## Requirements

```
# requirements.txt
google-adk>=1.0.0
pinecone>=5.0.0
langgraph>=0.2.0
langchain-core>=0.3.0
```

## Environment Variables

```bash
# .env
PINECONE_API_KEY=your_api_key
PINECONE_INDEX_HOST=your_index_host
GOOGLE_API_KEY=your_gemini_api_key
```

## Examples

### Example 1: Documentation Assistant

```bash
$ /adk-pinecone-rag --action "setup" --index_name "docs_kb"
$ /adk-pinecone-rag --action "ingest" --source "documentation/" --namespace "api_docs"
$ /adk-pinecone-rag --action "create_agent"

RAG Agent Created

Index: docs_kb
Namespace: api_docs
Documents: 1,247 chunks ingested
Embedding: multilingual-e5-large
Agent: knowledge_assistant

Test query: "How do I configure authentication?"
Response: Based on the documentation [auth_guide.md], you can configure authentication by...
```

### Example 2: Multi-Domain Knowledge Base

```bash
$ /adk-pinecone-rag --action "ingest" --source "product/" --namespace "product_docs"
$ /adk-pinecone-rag --action "ingest" --source "api/" --namespace "api_reference"
$ /adk-pinecone-rag --action "ingest" --source "tutorials/" --namespace "tutorials"

Multi-Namespace Ingestion Complete

Namespaces:
- product_docs: 523 vectors
- api_reference: 1,892 vectors
- tutorials: 347 vectors

Total: 2,762 vectors indexed
```

## Best Practices

1. **Chunking**: Use 256-512 tokens with 50-100 token overlap
2. **Namespaces**: Organize by document type or domain
3. **Metadata**: Include source, date, category for filtering
4. **Reranking**: Use for better relevance on top results
5. **Hybrid Search**: Combine semantic + keyword for comprehensive results

## Related Skills

- **adk-langgraph-orchestrator** - LangGraph workflows with RAG
- **adk-rag-builder** - Vertex AI RAG alternative
- **adk-mcp-integration** - MCP tool configuration
- **adk-deployment-manager** - Deploy RAG agents

## More Information

See Pinecone documentation: https://docs.pinecone.io/
See Google ADK documentation: https://google.github.io/adk-docs/
