# ADK Agent Types Overview

## Agent Categories

The ADK enables building several classes of agents, each suited for different scenarios. Understanding the landscape helps choose the right starting point.

### 1. Simple Agents (Pre-Built Templates)

**Best for:** Quick starts, learning, common use cases

**Characteristics:**
- Pre-configured agent personalities and capabilities
- Single-agent systems (one agent handling requests)
- Fixed tools and instruction sets
- Minimal configuration needed
- Ready to test in minutes

**Examples:**
- Fitness Coach - Provides personalized fitness advice
- Researcher - Conducts web research and summarization
- Teaching Assistant - Explains concepts and answers questions
- Domain Expert - Specialized knowledge in specific fields
- Customer Service Agent - Handles customer inquiries
- Data Analyst - Analyzes data and generates insights

**Best when:** You want quick results and are new to agent development

**Triggers:** "Build a fitness coach", "Create a researcher", "Make a teaching assistant"

---

### 2. Custom Agents (From Scratch)

**Best for:** Specific use cases, unique requirements, production systems

**Characteristics:**
- Build agents tailored to your exact needs
- Define custom instructions and behaviors
- Choose specific tools and capabilities
- Full control over agent personality
- Single-agent or foundation for multi-agent

**Architecture Decisions:**
- **Instruction Design** - How to guide the agent's reasoning
- **Tool Selection** - Which tools the agent can access
- **Memory** - Should the agent remember context?
- **Error Handling** - How to handle failures gracefully
- **Output Format** - What should the agent produce?

**Best when:** You have specific requirements or learning goals

**Triggers:** "Build a custom agent", "Design an agent from scratch", "I need [complex scenario]"

---

### 3. Multi-Agent Workflows (Orchestration)

**Best for:** Complex tasks, team-based reasoning, specialized subtasks

**Characteristics:**
- Multiple agents working together
- Each agent has specialized role
- Orchestration layer coordinates work
- Agents can be custom or template-based
- State management and memory sharing

**Orchestration Patterns:**

**Supervisor Pattern**
- One supervisor agent delegates to specialists
- Supervisor: Routes requests to best specialist
- Specialists: Handle specific domains
- Use case: Customer service, support systems

**Hierarchical Pattern**
- Tree structure of agents
- Each level handles increasing complexity
- Parent agents oversee child agents
- Use case: Enterprise systems, complex workflows

**Conditional Routing Pattern**
- Route based on request properties
- Different paths for different scenarios
- LangGraph-based workflows
- Use case: Decision trees, complex logic

**Debate Pattern**
- Multiple agents argue different perspectives
- Observer evaluates positions
- Consensus or ranked output
- Use case: Decision support, analysis

**Tool Use Routing Pattern**
- Agents specialized by tool set
- Each agent masters specific tools
- Router selects best agent for task
- Use case: Multi-domain operations

**Best when:** Tasks are complex and need multiple perspectives

**Triggers:** "Multi-agent system", "Agent coordination", "Agent team", "LangGraph"

---

### 4. Knowledge & Memory Systems (RAG)

**Best for:** Information-heavy applications, learning from documents, context preservation

**Characteristics:**
- Vector embeddings for semantic search
- Pinecone for scalable vector storage
- Retrieval-augmented generation (RAG)
- Agent memory systems
- Document ingestion pipelines

**Memory Types:**
- **Working Memory** - Short-term, current context
- **Shared Memory** - Cross-agent coordination
- **Persistent Memory** - Long-term storage in Pinecone

**RAG Capabilities:**
- Text retrieval from documents
- Multimodal retrieval (text + images)
- Semantic search with embeddings
- Context injection into agent instructions
- Knowledge base building

**Best when:** Agents need to learn from or remember information

**Triggers:** "Build RAG", "Vector search", "Agent memory", "Knowledge base"

---

### 5. Real-Time & Voice Agents

**Best for:** Live interaction, audio processing, conversational AI

**Characteristics:**
- Native audio processing with gemini-live-2.5-flash-native-audio
- Bidirectional WebSocket streaming
- Real-time event handling
- Voice input/output
- Multimodal (text, audio, video)

**Use Cases:**
- Voice assistants with natural conversation
- Live meeting transcription and analysis
- Real-time customer service
- Interactive media production
- Accessibility applications

**Best when:** Users need live, interactive experiences

**Triggers:** "Voice agent", "Real-time streaming", "Multimodal agent", "Live session"

---

### 6. Integration-Heavy Agents

**Best for:** Connecting external systems, data sources, services

**Characteristics:**
- MCP (Model Context Protocol) server integration
- Multiple external data sources
- Complex tool ecosystems
- Automation workflows
- Enterprise integrations

**Supported Integrations:**
- **Pinecone** - Vector search
- **SQLite/PostgreSQL** - Database access
- **Brave Search** - Web search
- **GitHub/GitLab** - Code repositories
- **Notion** - Document management
- **Slack** - Team communication

**Best when:** Agents need to work with external systems

**Triggers:** "MCP integration", "Connect external tools", "External service integration"

---

### 7. Production Agents (Deployed)

**Best for:** Live services, scalable systems, team deployments

**Characteristics:**
- Containerized with Docker
- Deployed to Cloud Run, Vertex AI, or GKE
- Monitoring and logging
- Scalability and reliability
- Team collaboration

**Deployment Targets:**
- **Cloud Run** - Serverless, managed
- **Vertex AI Agent Engine** - Managed agent platform
- **GKE** - Kubernetes orchestration

**Best when:** Ready to deploy to production

**Triggers:** "Deploy agent", "Production deployment", "Cloud Run", "Vertex AI"

---

## Decision Matrix

| Scenario | Best Type | Why |
|----------|-----------|-----|
| Want to learn ADK | Simple Agent | Templates are fast and educational |
| Need something specific | Custom Agent | Full control over behavior |
| Complex problem | Multi-Agent | Multiple perspectives help |
| Information retrieval | RAG System | Vector search is ideal |
| Real-time interaction | Voice Agent | Built for live use |
| External integrations | Integration-Heavy | MCP enables connections |
| Go live | Production | Deployment infrastructure ready |

---

## Getting Started

**If you're new to ADK:**
→ Start with **Simple Agents** (Quick Start skill)

**If you have specific needs:**
→ Move to **Custom Agents** (Custom Agent Builder skill)

**If tasks are complex:**
→ Progress to **Multi-Agent Workflows** (Multi-Agent Orchestrator skill)

**If you need external data:**
→ Add **Knowledge Systems** (Knowledge & Memory skill)

**If you need real-time:**
→ Integrate **Voice/Real-Time** (Real-Time Agents skill)

**If you need external services:**
→ Add **Integrations** (Integration Tools skill)

**If you're production-ready:**
→ Use **Production Deployment** (Production Deployment skill)

---

## What ADK Provides

The Google ADK (Agent Development Kit) handles:
- Agent lifecycle management
- Tool/function calling infrastructure
- Streaming and async support
- State management
- Error handling and retries
- Integration with Google's AI models (Gemini, Vertex AI)

**What you provide:**
- Agent instructions and personality
- Tool definitions and behaviors
- Custom orchestration logic
- Domain-specific knowledge
- Deployment configuration

---

## Next Steps

1. **Identify your use case** in the categories above
2. **Run the ADK Quick Start questionnaire** for personalized guidance
3. **Navigate to the recommended skill** for deep dive
4. **Start building!** Skills include templates, examples, and references
5. **Test locally** with `/adk:test` command
6. **Deploy when ready** using production deployment guidance
