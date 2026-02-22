---
name: ADK Quick Start
description: This skill should be used when the user asks "what can I build", "I want to create an agent", "tell me about ADK", "agent builder guide", "ADK quick start", or is exploring what's possible with agents. Provides foundational orientation and personalized routing to specialized ADK skills based on user goals and experience level.
version: 1.0.0
---

# ADK Quick Start Guide

The Google ADK (Agent Development Kit) is a comprehensive framework for building autonomous multi-agent systems with advanced capabilities like bidirectional streaming, multimodal input, memory management, knowledge retrieval, and production deployment.

This skill provides orientation for developers new to ADK or exploring what's possible. It answers "What can I build?" and guides toward the right specialized skill for your specific goals.

## Understanding Agent Capabilities

The ADK enables building agents that range from simple task-focused systems to complex multi-agent ecosystems. Understanding the spectrum helps identify the right starting point.

### The Agent Spectrum

**Simple Agents** (templates, quick start)
- Pre-configured personalities and capabilities
- Single agent handling requests
- Fixed tools and instruction sets
- Ready in minutes
- Best for: Learning, quick prototypes, common patterns

**Custom Agents** (tailored from scratch)
- Unique instructions and behaviors
- Specific tool selection
- Full control over personality
- Foundation for advanced features
- Best for: Specific requirements, production systems

**Multi-Agent Orchestration** (team-based reasoning)
- Multiple specialized agents
- Supervisor or hierarchical coordination
- State sharing and memory
- Complex workflow support
- Best for: Enterprise systems, complex reasoning

**Knowledge & Memory Systems** (information retrieval)
- Vector embeddings and semantic search
- Pinecone integration for scalable storage
- Persistent agent memory
- RAG (Retrieval-Augmented Generation)
- Best for: Information-heavy applications, learning from documents

**Real-Time & Voice Agents** (live interaction)
- Native audio with bidirectional streaming
- Multimodal input (text, audio, video)
- Event-based communication
- Conversational interfaces
- Best for: Voice assistants, live services, accessibility

**Integration-Heavy Systems** (external connections)
- MCP (Model Context Protocol) servers
- Database, API, and service connections
- Complex tool ecosystems
- Automation workflows
- Best for: Enterprise systems, multi-source data

**Production Deployments** (live services)
- Cloud Run, Vertex AI, or Kubernetes
- Scalability and reliability
- Monitoring and logging
- Team collaboration
- Best for: Live user services, team systems

## Quick Orientation

### What ADK Handles
- Agent lifecycle and execution
- Tool/function calling infrastructure
- Streaming and async support
- State management
- Integration with Gemini and Vertex AI models

### What You Provide
- Agent instructions and personality
- Tool definitions and behaviors
- Orchestration logic (if multi-agent)
- Domain-specific knowledge
- Deployment configuration

### Getting Started Journey

**Step 1: Understand Your Scenario**
Identify which agent type matches your goal. See `references/agent-types.md` for detailed descriptions of each category.

**Step 2: Answer Diagnostic Questions**
Use the questionnaire in `examples/questionnaire.md` to get personalized recommendations based on:
- Experience level (beginner, intermediate, expert)
- Primary goal (learn, prototype, production)
- Data needs (knowledge bases, external systems)
- Real-time requirements (voice, streaming)
- Deployment timeline

**Step 3: Navigate to Specialized Skill**
Based on your answers, move to the recommended skill:

| Your Goal | Recommended Skill |
|-----------|------------------|
| Learning or quick template | **adk-simple-agents** |
| Specific custom agent | **adk-custom-agent-builder** |
| Multiple coordinated agents | **adk-multi-agent-workflows** |
| Learning from documents | **adk-knowledge-systems** |
| Voice or real-time interaction | **adk-real-time-agents** |
| External system integration | **adk-integration-tools** |
| Production deployment | **adk-production-deployment** |

**Step 4: Build and Test**
Each specialized skill provides templates, examples, and guidance for building within that category.

**Step 5: Extend or Deploy**
As needs grow, layer in additional capabilities (add multi-agent coordination, integrate external systems, deploy to production).

## Common Questions

### Q: I'm brand new. Where do I start?
**A:** Start with **adk-simple-agents** skill. Templates let you explore ADK concepts quickly without worrying about implementation details. Try a template, test it with `/adk:test`, then move to custom agents once you understand the patterns.

### Q: I have a specific use case. What's my path?
**A:**
1. Describe your scenario
2. Use the questionnaire to identify the agent type
3. Navigate to the appropriate specialized skill
4. Build using templates and examples as guidance
5. Extend with additional features as needed

### Q: Can I build multi-agent systems?
**A:** Yes. The **adk-multi-agent-workflows** skill covers orchestration patterns like supervisor routing, hierarchical coordination, conditional routing, debate patterns, and more. Most use cases can be built as custom agents first, then extended to multi-agent systems.

### Q: How do I add knowledge/memory to my agent?
**A:** Use the **adk-knowledge-systems** skill. It covers working memory (short-term context), shared memory (cross-agent coordination), and persistent memory (long-term storage in Pinecone). RAG (Retrieval-Augmented Generation) enables learning from documents.

### Q: Can my agent use voice or real-time input?
**A:** Yes. The **adk-real-time-agents** skill covers voice agents with native audio using gemini-live-2.5-flash-native-audio, bidirectional streaming for live interaction, and multimodal input (text, audio, video).

### Q: How do I connect external systems?
**A:** Use the **adk-integration-tools** skill. It covers MCP (Model Context Protocol) servers for integrations with databases, APIs, and services like Pinecone, SQLite, PostgreSQL, Brave Search, GitHub, Notion, Slack, and more.

### Q: How do I deploy to production?
**A:** Build your agent first using any of the specialized skills, then use the **adk-production-deployment** skill to containerize with Docker and deploy to Cloud Run, Vertex AI, or Kubernetes.

### Q: Can I combine features?
**A:** Absolutely. Start with a custom agent, add multi-agent coordination, integrate external systems, add real-time capabilities, and deploy to production. The skills build on each other. Start simple, extend as needed.

## Key Concepts

### Agents
Autonomous systems that take instructions, use tools, and produce outputs. Agents reason about goals and decide which tools to use.

### Tools
Functions agents can call to interact with systems. Tools are defined with names, descriptions, and input schemas so agents understand what they do.

### Orchestration
The pattern for coordinating multiple agents. Common patterns: supervisor (one agent routes to specialists), hierarchical (tree of agents), conditional (route based on logic), debate (multiple agents argue perspectives).

### Memory Systems
- **Working Memory**: Short-term context for current request
- **Shared Memory**: Cross-agent coordination and state
- **Persistent Memory**: Long-term storage in Pinecone vector database

### RAG (Retrieval-Augmented Generation)
Process where agents search a knowledge base before answering. Enables agents to learn from documents, maintain context across conversations, and provide accurate information.

### MCP (Model Context Protocol)
Standard protocol for integrating external services. Allows agents to connect to databases, APIs, and services seamlessly.

### Streaming
Real-time communication where agent responses are generated and sent incrementally, enabling live interaction and fast perceived response times.

## Decision Framework

Use this framework to identify your starting point:

**If you're exploring and learning:**
→ Start with **Simple Agents** skill
→ Use templates to understand ADK patterns
→ Experiment with `/adk:test` command

**If you need a specific agent:**
→ Use questionnaire to identify agent type
→ Navigate to specialized skill
→ Build using guidance and examples

**If you need multiple agents:**
→ Start with **Custom Agent Builder**
→ Then progress to **Multi-Agent Workflows**
→ Coordinate with orchestration patterns

**If you need to learn from data:**
→ Build base agent with **Custom Agent Builder**
→ Extend with **Knowledge & Memory Systems**
→ Use RAG for semantic search and context

**If you need real-time interaction:**
→ Use **Real-Time Agents** skill
→ Build voice or streaming interface
→ Deploy with **Production Deployment**

**If you need to go live:**
→ Build your agent with appropriate skill
→ Use **Production Deployment** skill to containerize
→ Deploy to Cloud Run, Vertex AI, or Kubernetes

## Supporting Resources

### Reference Files
- **`references/agent-types.md`** - Detailed descriptions of all agent categories, decision matrix, and example scenarios

### Examples
- **`examples/questionnaire.md`** - Interactive questionnaire to discover your best starting skill

## Next Steps

1. **Understand your goal**: What do you want to build?
2. **Run the questionnaire**: `examples/questionnaire.md` provides personalized routing
3. **Navigate to specialized skill**: Based on questionnaire results
4. **Build your agent**: Use templates and examples from specialized skill
5. **Test locally**: `/adk:test` command lets you test agents before deployment
6. **Deploy when ready**: `/adk:status` checks dependencies, then use production deployment

## Skills in This Plugin

The Claude ADK Skills plugin provides comprehensive guidance across agent development:

| Skill | Focus | Best For |
|-------|-------|----------|
| **adk-quick-start** (you are here) | Orientation & routing | Getting started, discovering paths |
| **adk-simple-agents** | Templates & quick start | Learning, rapid prototypes |
| **adk-custom-agent-builder** | Build from scratch | Specific requirements |
| **adk-multi-agent-workflows** | Orchestration patterns | Complex systems, team reasoning |
| **adk-knowledge-systems** | RAG & memory | Information retrieval, learning |
| **adk-real-time-agents** | Voice & streaming | Live interaction, accessibility |
| **adk-integration-tools** | External system connections | MCP servers, databases, APIs |
| **adk-production-deployment** | Cloud deployment | Launching live services |

Each skill provides detailed guidance, working examples, and templates for its focus area.

## Getting Help

- **Commands**: Use `/adk:init` to scaffold projects, `/adk:test` to test agents, `/adk:config` to manage settings
- **Examples**: Each skill includes working examples you can copy and adapt
- **Docs**: `/adk:docs` provides quick reference access to documentation
- **Status**: `/adk:status` checks environment and dependencies

---

**Ready to build?** Answer the questionnaire in `examples/questionnaire.md` to discover your best starting skill!
