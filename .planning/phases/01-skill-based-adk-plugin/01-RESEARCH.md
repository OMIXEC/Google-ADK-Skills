# Research: Skill-Based ADK Plugin Architecture

## Sources Consulted

### 1. Skill-Builder (metaskills/skill-builder)
- **Repository:** https://github.com/metaskills/skill-builder
- **Key Patterns:**
  - YAML frontmatter: `name`, `description`, `version`
  - Description field optimized for Claude invocation triggers
  - Gerund naming convention (e.g., `processing-pdfs`)
  - Progressive disclosure with supporting reference files
  - Max 500 lines per skill file
  - CLI/Node.js focus (no Python for skill execution)
  - Templates directory for code generation

### 2. Google ADK Documentation (Context7)
- **Library ID:** `/google/adk-docs`
- **Key Components:**
  - **Agent Types:** Agent, LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
  - **Tools:** FunctionTool, AgentTool, MCPToolset, GoogleSearchTool, VertexAiRagRetrieval
  - **Streaming:** LiveRequestQueue, RunConfig, Voice Activity Detection
  - **Memory:** InMemoryMemoryService, VertexAiMemoryBankService
  - **Sessions:** InMemorySessionService, DatabaseSessionService, VertexAiSessionService

### 3. Existing Claude-ADK-Skills Structure
- **Current Skills (12+):**
  - adk-skill-dispatcher (router)
  - adk-adaptive-agent-generator
  - adk-persona-builder
  - adk-domain-expert-builder
  - adk-multi-agent-orchestrator
  - adk-langgraph-orchestrator
  - adk-pinecone-rag
  - adk-mcp-integration
  - adk-rag-builder
  - adk-deployment-manager
  - adk-bidi-multi-agent
  - adk-memory-manager
  - adk-autonomous-agent

## Architecture Decisions

### 1. Skill Organization
**Decision:** Organize skills into hierarchical structure with SKILL.md + references + examples
**Rationale:** Enables progressive disclosure while keeping main skill files concise

### 2. Enterprise Multi-Agent Hierarchy
**Decision:** Support 3+ tier hierarchies (Executive → Department → Specialist)
**Rationale:** Enterprise deployments require scalable agent architectures with 100+ agents

### 3. Adaptive Memory System
**Decision:** Implement 4-layer memory (Working, Episodic, Semantic, Procedural)
**Rationale:** Enables agents to learn and adapt to user preferences over time

### 4. Multimodal RAG
**Decision:** Combine Pinecone (dense + sparse) with Vertex AI RAG Engine
**Rationale:** Enterprise needs both managed and self-hosted RAG options

### 5. Real-World Scenarios
**Decision:** Focus on vision, tutoring, support, interpretation
**Rationale:** These represent highest-value enterprise use cases

## Technical Requirements

### Models
- `gemini-2.5-flash` - Standard agent model
- `gemini-2.5-pro` - Reasoning-heavy tasks
- `gemini-live-2.5-flash-native-audio` - Voice/streaming
- `gemini-2.0-flash-live-001` - Legacy live model

### Infrastructure
- Pinecone for vector search
- Vertex AI for managed RAG
- Cloud Run for serverless deployment
- GKE for Kubernetes deployment
- Vertex AI Agent Engine for managed agents

### Dependencies
- google-adk>=1.0.0
- pinecone>=5.0.0
- langgraph>=0.2.0
- langchain-core>=0.3.0
- vertexai>=1.0.0
- fastapi>=0.100.0
- uvicorn>=0.20.0

## Gap Analysis

### Missing from Current Plugin:
1. **Tool Builder Skill** - Custom FunctionTool creation patterns
2. **Callback Patterns Skill** - Agent behavior customization
3. **Session Management Skill** - Session/memory service patterns
4. **Grounding Patterns Skill** - RAG and search grounding
5. **Safety Guardrails Skill** - Content filtering and security
6. **Orchestration Patterns Skill** - Sequential/Parallel/Loop agents
7. **Streaming Agents Skill** - LiveRequestQueue patterns
8. **Vision Agents Skill** - Real-world visual understanding
9. **Tutoring Agents Skill** - Adaptive learning
10. **Support Agents Skill** - Enterprise helpdesk
11. **Monitoring Skill** - Observability and metrics

### Enhancement Needed:
1. YAML frontmatter on all existing skills
2. Reference file organization
3. Template directory for code generation
4. Enterprise deployment patterns
5. Plugin.json with full skill registration
