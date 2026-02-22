---
wave: 4
depends_on: [04-PLAN.md, 07-PLAN.md]
files_modified:
  - skills/adk-multimodal-rag/SKILL.md
  - skills/adk-pinecone-rag.md
  - skills/adk-vertexai-rag/SKILL.md
autonomous: false
requirements: [multimodal-rag, pinecone, vertexai, enterprise-knowledge]
---

# Plan 08: Enterprise Multimodal RAG with Pinecone and Vertex AI

## Objective
Create comprehensive multimodal RAG systems combining Pinecone vector search, Vertex AI RAG Engine, and multimodal models for enterprise knowledge retrieval across text, images, audio, and video.

## must_haves
- [ ] Multimodal embedding pipelines (text, image, audio, video)
- [ ] Pinecone hybrid search (dense + sparse)
- [ ] Vertex AI RAG Engine integration
- [ ] Cross-modal retrieval patterns
- [ ] Enterprise-scale knowledge management

## Tasks

<task id="8.1" type="create">
<title>Create Multimodal RAG Architecture Skill</title>
<description>
Enterprise multimodal RAG combining all modalities:

**Multimodal Embedding Pipeline:**
```python
from pinecone import Pinecone, EmbedModel
from google.cloud import aiplatform
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from dataclasses import dataclass
from typing import Union, List, Optional
import base64

@dataclass
class MultimodalDocument:
    \"\"\"Document that can contain multiple modalities.\"\"\"
    id: str
    text: Optional[str] = None
    image_base64: Optional[str] = None
    audio_base64: Optional[str] = None
    video_url: Optional[str] = None
    metadata: dict = None

class MultimodalRAGPipeline:
    \"\"\"Enterprise multimodal RAG pipeline.\"\"\"

    def __init__(self, pinecone_index: str, project_id: str):
        self.pc = Pinecone()
        self.index = self.pc.Index(pinecone_index)
        self.project_id = project_id

    async def embed_text(self, text: str) -> List[float]:
        \"\"\"Embed text using multilingual model.\"\"\"
        result = self.pc.inference.embed(
            model=EmbedModel.Multilingual_E5_Large,
            inputs=[text],
            parameters={"input_type": "passage"}
        )
        return result.data[0].values

    async def embed_image(self, image_base64: str) -> List[float]:
        \"\"\"Embed image using CLIP model.\"\"\"
        result = self.pc.inference.embed(
            model="pinecone-clip-vit-base-patch32",
            inputs=[{"image": image_base64}]
        )
        return result.data[0].values

    async def embed_audio(self, audio_base64: str) -> List[float]:
        \"\"\"Transcribe and embed audio.\"\"\"
        # Transcribe with Whisper
        transcription = self.pc.inference.transcribe(
            model="openai-whisper-large-v3",
            audio=audio_base64
        )
        # Embed transcription
        return await self.embed_text(transcription.text)

    async def ingest_document(self, doc: MultimodalDocument):
        \"\"\"Ingest multimodal document into Pinecone.\"\"\"
        vectors = []

        if doc.text:
            text_embedding = await self.embed_text(doc.text)
            vectors.append({
                "id": f"{doc.id}_text",
                "values": text_embedding,
                "metadata": {
                    **doc.metadata,
                    "modality": "text",
                    "content": doc.text[:1000],
                }
            })

        if doc.image_base64:
            image_embedding = await self.embed_image(doc.image_base64)
            vectors.append({
                "id": f"{doc.id}_image",
                "values": image_embedding,
                "metadata": {
                    **doc.metadata,
                    "modality": "image",
                    "image_ref": doc.id,
                }
            })

        if doc.audio_base64:
            audio_embedding = await self.embed_audio(doc.audio_base64)
            vectors.append({
                "id": f"{doc.id}_audio",
                "values": audio_embedding,
                "metadata": {
                    **doc.metadata,
                    "modality": "audio",
                    "audio_ref": doc.id,
                }
            })

        if vectors:
            self.index.upsert(vectors=vectors)

    async def cross_modal_search(
        self,
        query: str = None,
        image: str = None,
        modalities: List[str] = ["text", "image", "audio"],
        top_k: int = 10,
        rerank: bool = True,
    ) -> List[dict]:
        \"\"\"Search across modalities with optional reranking.\"\"\"
        # Embed query
        if query:
            query_embedding = await self.embed_text(query)
        elif image:
            query_embedding = await self.embed_image(image)
        else:
            raise ValueError("Must provide query or image")

        # Search with modality filter
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k * 2 if rerank else top_k,
            filter={"modality": {"$in": modalities}},
            include_metadata=True,
        )

        if rerank:
            # Rerank with Pinecone reranker
            documents = [r.metadata.get("content", "") for r in results.matches]
            reranked = self.pc.inference.rerank(
                model="pinecone-rerank-v0",
                query=query,
                documents=documents,
                top_n=top_k,
            )
            return [results.matches[r.index] for r in reranked.data]

        return results.matches
```

**Cross-Modal Use Cases:**
1. **Text-to-Image Search** - Find images matching text description
2. **Image-to-Text Search** - Find documents about an image
3. **Audio-to-Text Search** - Search docs by voice query
4. **Unified Multimodal Search** - Search all modalities at once
</description>
<files>
- skills/adk-multimodal-rag/SKILL.md
- skills/adk-multimodal-rag/references/embedding-models.md
- skills/adk-multimodal-rag/references/cross-modal-search.md
- skills/adk-multimodal-rag/examples/multimodal-pipeline.md
- skills/adk-multimodal-rag/examples/enterprise-knowledge-base.md
</files>
</task>

<task id="8.2" type="enhance">
<title>Enhance Pinecone RAG Skill for Enterprise</title>
<description>
Upgrade Pinecone RAG with enterprise features:

**Hybrid Search (Dense + Sparse):**
```python
from pinecone import Pinecone, EmbedModel

class HybridSearchPipeline:
    \"\"\"Hybrid search combining semantic and keyword matching.\"\"\"

    def __init__(self, index_name: str):
        self.pc = Pinecone()
        self.index = self.pc.Index(index_name)

    async def hybrid_embed(self, text: str) -> dict:
        \"\"\"Create both dense and sparse embeddings.\"\"\"
        # Dense embedding for semantic search
        dense = self.pc.inference.embed(
            model=EmbedModel.Multilingual_E5_Large,
            inputs=[text],
        ).data[0].values

        # Sparse embedding for keyword matching
        sparse = self.pc.inference.embed(
            model="pinecone-sparse-english-v0",
            inputs=[text],
        ).data[0]

        return {
            "dense": dense,
            "sparse": {
                "indices": sparse.indices,
                "values": sparse.values,
            }
        }

    async def hybrid_search(
        self,
        query: str,
        alpha: float = 0.5,  # Balance: 0=sparse, 1=dense
        top_k: int = 10,
        filter: dict = None,
    ) -> List[dict]:
        \"\"\"Hybrid search with configurable dense/sparse balance.\"\"\"
        embeddings = await self.hybrid_embed(query)

        results = self.index.query(
            vector=embeddings["dense"],
            sparse_vector=embeddings["sparse"],
            top_k=top_k,
            filter=filter,
            include_metadata=True,
        )
        return results.matches
```

**Enterprise Features:**
- Namespace isolation for multi-tenancy
- Access control integration
- Metadata filtering for compliance
- Batch ingestion for large datasets
- Index optimization for performance
</description>
<files>
- skills/adk-pinecone-rag.md
- skills/adk-pinecone-rag/references/hybrid-search.md
- skills/adk-pinecone-rag/references/enterprise-features.md
- skills/adk-pinecone-rag/examples/multi-tenant-rag.md
</files>
</task>

<task id="8.3" type="create">
<title>Create Vertex AI RAG Integration Skill</title>
<description>
Vertex AI RAG Engine for managed enterprise RAG:

**Vertex AI RAG Engine:**
```python
from google.adk.agents import Agent
from google.adk.tools.retrieval import VertexAiRagRetrieval
from vertexai import rag
from google.cloud import aiplatform

class VertexRAGPipeline:
    \"\"\"Managed RAG with Vertex AI.\"\"\"

    def __init__(self, project_id: str, location: str = "us-central1"):
        aiplatform.init(project=project_id, location=location)
        self.project_id = project_id
        self.location = location

    async def create_corpus(
        self,
        display_name: str,
        description: str = "",
    ) -> rag.RagCorpus:
        \"\"\"Create a new RAG corpus.\"\"\"
        corpus = rag.create_corpus(
            display_name=display_name,
            description=description,
        )
        return corpus

    async def import_files(
        self,
        corpus_name: str,
        gcs_uri: str,
        chunk_size: int = 512,
        chunk_overlap: int = 100,
    ):
        \"\"\"Import files from GCS into corpus.\"\"\"
        rag.import_files(
            corpus_name=corpus_name,
            paths=[gcs_uri],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def create_rag_tool(
        self,
        corpus_name: str,
        similarity_top_k: int = 10,
        vector_distance_threshold: float = 0.3,
    ) -> VertexAiRagRetrieval:
        \"\"\"Create RAG retrieval tool for agent.\"\"\"
        return VertexAiRagRetrieval(
            name="search_knowledge",
            description="Search enterprise knowledge base",
            rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
            similarity_top_k=similarity_top_k,
            vector_distance_threshold=vector_distance_threshold,
        )

# Create RAG-powered agent
def create_rag_agent(corpus_name: str) -> Agent:
    pipeline = VertexRAGPipeline(project_id="my-project")
    rag_tool = pipeline.create_rag_tool(corpus_name)

    return Agent(
        name="knowledge_agent",
        model="gemini-2.5-flash",
        instruction=\"\"\"
        You are a knowledge assistant with access to enterprise documentation.

        **Behavior:**
        1. ALWAYS search the knowledge base before answering
        2. Cite specific sources with page/section references
        3. Acknowledge when information is not in the knowledge base
        4. Suggest related topics for further exploration
        \"\"\",
        tools=[rag_tool],
    )
```

**Memory Bank Integration:**
```python
from google.adk.memory import VertexAiMemoryBankService

# Long-term memory with Vertex AI Memory Bank
memory_service = VertexAiMemoryBankService(
    project="my-project",
    location="us-central1",
    agent_engine_id="my-agent-engine",
)

# Store conversation memories
await memory_service.add_session_to_memory(session_events)

# Search memories
memories = await memory_service.search_memory(query="user preferences")
```
</description>
<files>
- skills/adk-vertexai-rag/SKILL.md
- skills/adk-vertexai-rag/references/corpus-management.md
- skills/adk-vertexai-rag/references/memory-bank.md
- skills/adk-vertexai-rag/examples/managed-rag-agent.md
- skills/adk-vertexai-rag/examples/memory-integration.md
</files>
</task>

## Verification Criteria
- [ ] Multimodal RAG supports text, image, audio, video
- [ ] Hybrid search combines dense and sparse
- [ ] Vertex AI RAG integration complete
- [ ] Cross-modal search patterns work
- [ ] Enterprise scalability demonstrated

## Acceptance
Enterprise multimodal RAG enables comprehensive knowledge retrieval.
