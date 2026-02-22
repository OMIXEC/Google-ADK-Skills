---
name: adk-skill-dispatcher
description: Intelligent router analyzing user intent to automatically dispatch ADK development tasks to specialized skills. Auto-activates on agent/ADK/build/deploy keywords. Routes voice/streaming to bidi-multi-agent, deployment to deployment-manager, RAG to rag-builder, multi-agent to orchestrator, and more based on keyword detection. Acts as intelligent entry point for all ADK workflows.
version: 1.0.0
---

# adk-skill-dispatcher

**Intelligent ADK Skill Router - Automatic Intent-Based Dispatch**

The master router skill that analyzes user intent and automatically dispatches to the appropriate ADK skill. This skill should be invoked first for any ADK-related development task.

## When to Use

**AUTO-ACTIVATE** on any of these conditions:

- User mentions: "agent", "ADK", "Google ADK", "build agent", "create agent"
- User asks about: "voice", "realtime", "streaming", "multi-agent", "RAG", "deployment"
- User wants to: build, create, deploy, configure, orchestrate agents
- Any Google ADK development task
- User says: "I need an agent that...", "Help me build...", "Create a..."

This skill acts as the **intelligent entry point** for all ADK development workflows.

## Intent-to-Skill Mapping

| Priority | Keywords | Target Skill | Confidence |
|----------|----------|--------------|------------|
| HIGH | realtime, live, streaming, voice, audio, bidi, native audio | `adk-bidi-multi-agent` | 0.95 |
| HIGH | deploy, production, cloud run, vertex ai, gke, kubernetes | `adk-deployment-manager` | 0.95 |
| HIGH | memory, context, remember, shared state, persistent | `adk-memory-manager` | 0.90 |
| HIGH | autonomous, self-reasoning, proactive, OODA, goal-driven | `adk-autonomous-agent` | 0.90 |
| HIGH | multi-agent, team, supervisor, coordinate, delegate | `adk-multi-agent-orchestrator` | 0.90 |
| HIGH | langgraph, workflow, state machine, graph, conditional | `adk-langgraph-orchestrator` | 0.90 |
| HIGH | pinecone, vector, embedding, multimodal rag, semantic search | `adk-pinecone-rag` | 0.90 |
| HIGH | MCP, tools, database, search, github, external tools | `adk-mcp-integration` | 0.85 |
| MEDIUM | RAG, retrieval, vertex ai rag, knowledge base | `adk-rag-builder` | 0.80 |
| MEDIUM | persona, personality, character, expert template | `adk-persona-builder` | 0.75 |
| MEDIUM | domain expert, specialist, industry expert | `adk-domain-expert-builder` | 0.75 |
| DEFAULT | build agent, create agent, custom agent, new agent | `adk-adaptive-agent-generator` | 0.70 |

## Routing Logic

```
FUNCTION route_to_skill(user_request):
    # Extract keywords and intent
    keywords = extract_keywords(user_request)

    # Priority 1: Real-time / Voice
    IF contains_any(keywords, ["realtime", "real-time", "live", "streaming",
                               "voice", "audio", "speech", "bidi", "native audio"]):
        RETURN "adk-bidi-multi-agent"

    # Priority 2: Deployment
    IF contains_any(keywords, ["deploy", "production", "cloud run", "vertex ai",
                               "gke", "kubernetes", "docker", "container"]):
        RETURN "adk-deployment-manager"

    # Priority 3: Memory
    IF contains_any(keywords, ["memory", "context", "remember", "shared",
                               "persistent", "working memory"]):
        RETURN "adk-memory-manager"

    # Priority 4: Autonomous
    IF contains_any(keywords, ["autonomous", "self-reasoning", "proactive",
                               "OODA", "goal-driven", "self-directed"]):
        RETURN "adk-autonomous-agent"

    # Priority 5: Multi-Agent
    IF contains_any(keywords, ["multi-agent", "team", "supervisor", "coordinate",
                               "delegate", "swarm", "parallel agents"]):
        RETURN "adk-multi-agent-orchestrator"

    # Priority 6: LangGraph
    IF contains_any(keywords, ["langgraph", "workflow", "state machine",
                               "graph", "conditional", "state"]):
        RETURN "adk-langgraph-orchestrator"

    # Priority 7: Pinecone RAG
    IF contains_any(keywords, ["pinecone", "vector", "embedding",
                               "multimodal rag", "semantic search"]):
        RETURN "adk-pinecone-rag"

    # Priority 8: MCP Tools
    IF contains_any(keywords, ["MCP", "tools", "database", "search",
                               "github", "external"]):
        RETURN "adk-mcp-integration"

    # Priority 9: Vertex AI RAG
    IF contains_any(keywords, ["rag", "retrieval", "vertex ai rag",
                               "knowledge base", "document"]):
        RETURN "adk-rag-builder"

    # Priority 10: Persona
    IF contains_any(keywords, ["persona", "personality", "character",
                               "expert template", "coach", "tutor"]):
        RETURN "adk-persona-builder"

    # Priority 11: Domain Expert
    IF contains_any(keywords, ["domain expert", "specialist", "industry",
                               "professional", "expert"]):
        RETURN "adk-domain-expert-builder"

    # Default: Adaptive Agent Generator
    RETURN "adk-adaptive-agent-generator"
```

## Quick Start

This skill auto-activates. You can also invoke it explicitly:

```bash
# Explicit invocation
/adk-skill-dispatcher Build a realtime voice agent with RAG capabilities

# The router will analyze and dispatch to:
# 1. adk-bidi-multi-agent (primary - realtime/voice)
# 2. May suggest adk-pinecone-rag as follow-up (RAG capabilities)
```

## Multi-Skill Chaining

When a request spans multiple capabilities, the router identifies the **primary skill** and suggests **follow-up skills**:

| Request Example | Primary Skill | Follow-up Skills |
|-----------------|---------------|------------------|
| "Voice agent with RAG" | `adk-bidi-multi-agent` | `adk-pinecone-rag` |
| "Deploy multi-agent system" | `adk-deployment-manager` | `adk-multi-agent-orchestrator` |
| "Autonomous researcher with memory" | `adk-autonomous-agent` | `adk-memory-manager` |
| "LangGraph workflow with MCP tools" | `adk-langgraph-orchestrator` | `adk-mcp-integration` |

## Parameters

```bash
--analyze-only          # Only show routing decision, don't dispatch
--force-skill SKILL     # Force dispatch to specific skill
--show-confidence       # Display confidence scores for all skills
--chain                 # Enable automatic multi-skill chaining
```

## Usage Patterns

### Pattern 1: Natural Language Request

User says: "I want to build a customer support agent that can handle voice calls and search our knowledge base"

**Router Analysis:**
- Detected: "voice calls" -> `adk-bidi-multi-agent` (HIGH)
- Detected: "knowledge base" -> `adk-pinecone-rag` (HIGH)
- Detected: "customer support" -> Could use persona templates

**Router Action:**
1. Dispatch to `adk-bidi-multi-agent` for voice setup
2. Suggest `adk-pinecone-rag` for knowledge base integration
3. Optionally suggest `adk-persona-builder` for customer service persona

### Pattern 2: Specific Technology Request

User says: "Set up LangGraph workflow for my research team"

**Router Analysis:**
- Detected: "LangGraph" -> `adk-langgraph-orchestrator` (EXACT MATCH)

**Router Action:**
1. Direct dispatch to `adk-langgraph-orchestrator`

### Pattern 3: Deployment Request

User says: "Deploy my agent to Cloud Run"

**Router Analysis:**
- Detected: "Deploy", "Cloud Run" -> `adk-deployment-manager` (EXACT MATCH)

**Router Action:**
1. Direct dispatch to `adk-deployment-manager`

## Skill Dependency Graph

```
                    adk-skill-dispatcher
                           |
           +---------------+---------------+
           |               |               |
    Agent Creation    Orchestration    Infrastructure
           |               |               |
    +------+------+   +----+----+    +-----+-----+
    |      |      |   |    |    |    |     |     |
  adapt  persona domain multi lang  mcp   rag   deploy
    |      |      |   agent graph   |     |     |
    +------+------+   +----+----+   +-----+-----+
           |               |               |
           +-------+-------+-------+-------+
                   |
              adk-bidi-multi-agent
              (real-time streaming)
                   |
              adk-memory-manager
              adk-autonomous-agent
```

## Output Format

When the router dispatches, it:

1. **Announces the routing decision:**
   ```
   Routing to: adk-bidi-multi-agent
   Reason: Detected voice/streaming keywords
   Confidence: 0.95
   ```

2. **Passes full context to target skill:**
   - Original user request
   - Extracted intent and keywords
   - Suggested follow-up skills

3. **Monitors for follow-up needs:**
   - If target skill completes, suggests next skill if applicable

## Related Skills

All ADK skills are accessible through this router:

- **adk-adaptive-agent-generator** - Custom agent creation
- **adk-persona-builder** - Pre-built persona templates
- **adk-domain-expert-builder** - Domain specialist agents
- **adk-multi-agent-orchestrator** - Multi-agent coordination
- **adk-langgraph-orchestrator** - LangGraph workflows
- **adk-pinecone-rag** - Multimodal RAG with Pinecone
- **adk-mcp-integration** - MCP tool integration
- **adk-rag-builder** - Vertex AI RAG
- **adk-deployment-manager** - Production deployment
- **adk-bidi-multi-agent** - Real-time streaming agents
- **adk-memory-manager** - Multi-agent memory systems
- **adk-autonomous-agent** - Self-reasoning agents

## More Information

See the [Claude-ADK-Skills README](../README.md) for complete documentation.
