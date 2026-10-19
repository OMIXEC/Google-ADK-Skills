---
name: adk-rag
description: >-
  Adds retrieval-augmented generation to ADK agents with Pinecone (self-managed) or
  Vertex AI RAG (managed corpora): ingestion, chunking, retrieval, and grounding. Use
  when the agent must answer from a document corpus or a knowledge base. Don't use for
  session or agent memory (use adk-memory), for raw vector-store plumbing and embedding
  storage (use adk-embeddings), or for prompt design (use adk-prompts).
compatibility: google-adk>=2.9.2,<3
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
