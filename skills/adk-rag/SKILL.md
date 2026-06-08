---
name: adk-rag
description: >-
  Add retrieval-augmented generation to ADK agents. Build knowledge-powered
  agents with either Pinecone (self-managed vector DB, embeddings, ingestion)
  or Vertex AI RAG (managed corpora). Use when a request mentions RAG, knowledge
  base, vector search, embeddings, document ingestion, or grounding an agent in
  a corpus.
---

# adk-rag — Retrieval-Augmented Generation for ADK

You build RAG pipelines that ground ADK agents in a document corpus.

## Choose the backend, then read its reference

| Need | Backend | Reference |
|------|---------|-----------|
| Self-managed vectors, custom embeddings, full control | Pinecone | `references/pinecone-rag.md` |
| Fully managed corpora on Google Cloud, least ops | Vertex AI RAG | `references/vertex-ai-rag.md` |

Read the matching reference **before** writing code — they contain the ingestion,
embedding, and retrieval-tool patterns end to end.

## Process
1. Clarify corpus source, size, update cadence, and latency/cost constraints
2. Pick the backend from the table above and read its reference
3. Scaffold: ingestion → embedding → index → a retrieval tool bound to the agent
4. Validate the model choice (load `adk-litellm`); never hardcode API keys

## NEVER
- Hardcode Pinecone/Vertex credentials — use `${PINECONE_API_KEY}` / ADC
- Use a deprecated embedding model — confirm against `adk-litellm`
- Skip chunking/metadata strategy for non-trivial corpora
