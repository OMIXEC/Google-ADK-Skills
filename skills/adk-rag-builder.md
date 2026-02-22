---
name: adk-rag-builder
description: Add knowledge bases to ADK agents using Vertex AI RAG. Actions include create (corpus setup), ingest (documents from GCS/local), integrate (add VertexAiRagRetrieval to agent), and query (test retrieval). Configure chunk size, overlap, similarity_top_k, distance threshold. Use for Q&A systems, documentation assistants, and long-term agent memory.
version: 1.0.0
---

# adk-rag-builder

**Vertex AI RAG Integration for Google ADK**

Add knowledge bases to ADK agents using Vertex AI RAG. Create corpora, ingest documents, and configure retrieval for intelligent knowledge-powered agents.

## When to Use

Use this skill when:
- Agent needs domain knowledge
- Ingesting documents (PDF, text, web)
- Building Q&A systems
- Creating documentation assistants
- Adding long-term memory to agents

## Quick Start

```bash
# Create RAG corpus
/adk-rag-builder --action "create" --corpus_name "product_docs"

# Ingest documents
/adk-rag-builder --action "ingest" --corpus_name "product_docs" --source "gs://bucket/docs/"

# Add RAG to agent
/adk-rag-builder --action "integrate" --corpus_name "product_docs" --agent "support_agent"
```

## Parameters

```bash
--action "create|ingest|integrate|query"  # Required action
--corpus_name "name"                       # Corpus identifier
--source "path_or_url"                     # Document source
--chunk_size 512                           # Chunk size (default: 512)
--chunk_overlap 50                         # Overlap (default: 50)
--similarity_top_k 10                      # Results to return
--distance_threshold 0.3                   # Similarity threshold
```

## RAG Workflow

### 1. Create Corpus

```bash
/adk-rag-builder --action "create" \
  --corpus_name "product_documentation" \
  --description "Product docs and guides"
```

**Generated Code:**
```python
from vertexai import rag
import vertexai

# Initialize Vertex AI
vertexai.init(project="your-project", location="us-central1")

# Create RAG corpus
corpus = rag.create_corpus(
    display_name="product_documentation",
    description="Product docs and guides",
)

print(f"Corpus created: {corpus.name}")
CORPUS_NAME = corpus.name
```

### 2. Ingest Documents

```bash
# From Google Cloud Storage
/adk-rag-builder --action "ingest" \
  --corpus_name "product_documentation" \
  --source "gs://my-bucket/docs/"
```

**Generated Code:**
```python
from vertexai import rag

# Import files from GCS
response = rag.import_files(
    corpus.name,
    paths=["gs://my-bucket/docs/"],
    chunk_size=512,
    chunk_overlap=50,
)

print(f"Imported {response.imported_rag_files_count} files")
```

### 3. Integrate with Agent

```bash
/adk-rag-builder --action "integrate" \
  --corpus_name "product_documentation" \
  --agent "support_agent"
```

**Generated Code:**
```python
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai import rag

RAG_CORPUS = "projects/your-project/locations/us-central1/ragCorpora/your-corpus-id"

support_agent = Agent(
    name="support_agent",
    model="gemini-2.5-flash",
    description="Support agent with product knowledge",
    instruction="""
    You are a support agent with access to product documentation.
    Always search the knowledge base before answering.
    Cite specific documentation sections.
    """,
    tools=[
        VertexAiRagRetrieval(
            name="search_docs",
            description="Search product documentation",
            rag_resources=[
                rag.RagResource(rag_corpus=RAG_CORPUS)
            ],
            similarity_top_k=10,
            vector_distance_threshold=0.3,
        ),
    ],
)

root_agent = support_agent
```

## RAG Configuration Options

### Chunking Strategies

```python
# Small chunks for precise retrieval
rag.import_files(
    corpus.name,
    paths=paths,
    chunk_size=256,
    chunk_overlap=25,
)

# Large chunks for more context
rag.import_files(
    corpus.name,
    paths=paths,
    chunk_size=1024,
    chunk_overlap=100,
)
```

### Retrieval Tuning

```python
VertexAiRagRetrieval(
    name="search_docs",
    rag_resources=[rag.RagResource(rag_corpus=CORPUS)],
    similarity_top_k=10,         # Number of results
    vector_distance_threshold=0.3,  # Minimum similarity
)
```

## Supported File Types

| Type | Extensions | Notes |
|------|------------|-------|
| Text | .txt, .md | Plain text |
| PDF | .pdf | Text extraction |
| HTML | .html | Web pages |
| Word | .docx | Microsoft Word |

## Generated Project Structure

```
rag-enabled-agent/
+-- src/
|   +-- agent.py           # Agent with RAG
|   +-- rag_setup.py       # Corpus management
|   +-- config.py
+-- scripts/
|   +-- create_corpus.py
|   +-- ingest_docs.py
+-- deployment/
+-- README.md
```

## Examples

### Example 1: Documentation Assistant

```bash
$ /adk-rag-builder --action "create" --corpus_name "api_docs"
$ /adk-rag-builder --action "ingest" --corpus_name "api_docs" --source "gs://docs/api/"
$ /adk-rag-builder --action "integrate" --corpus_name "api_docs" --agent "api_assistant"

RAG Integration Complete
Corpus: api_docs (150 files)
Agent: api_assistant
```

## Best Practices

- Use smaller chunks (256-512) for precise Q&A
- Use larger chunks (1024+) for narrative context
- Start with top_k=10, adjust based on quality

## Related Skills

- **adk-adaptive-agent-generator** - Create agents with RAG
- **adk-mcp-integration** - Add MCP tools alongside RAG
- **adk-deployment-manager** - Deploy RAG-enabled agents
