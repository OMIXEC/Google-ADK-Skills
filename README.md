# CLAUDE-ADK-SKILLS

**Production-Grade Google ADK Agent Development Skills for Claude Code**

Build sophisticated AI agents using Google's Agent Development Kit (ADK) with voice-driven generation, expert personas, multimodal RAG pipelines, LangGraph orchestration, real-time bidirectional streaming, and production deployment.

## Features

- **Adaptive Agent Generation** - Describe what you need, get production-ready code
- **30+ Expert Personas** - Pre-built personas for any domain
- **Multimodal RAG** - Pinecone integration for text, image, audio, video
- **LangGraph Orchestration** - Stateful multi-agent workflows
- **MCP Integration** - External tools via Model Context Protocol
- **Real-Time Bidi Streaming** - Native audio, multi-agent coordination, autonomous agents
- **Production Deployment** - Cloud Run, Vertex AI Agent Engine, GKE

## Installation

### Quick Install (Recommended)

```bash
# With SSH (for developers with SSH keys configured)
curl -sSL https://raw.githubusercontent.com/OMIXEC/Claude-ADK-Skills/main/install.sh | bash -s -- --ssh

# With GitHub Personal Access Token
curl -sSL https://raw.githubusercontent.com/OMIXEC/Claude-ADK-Skills/main/install.sh | bash -s -- --token YOUR_GITHUB_PAT

# Interactive (prompts for authentication method)
curl -sSL https://raw.githubusercontent.com/OMIXEC/Claude-ADK-Skills/main/install.sh | bash
```

### Manual Installation

```bash
# Clone the repository
git clone [github.com:OMIXEC/Claude-ADK-Skills.git ~/.claude-adk-skills](https://github.com/OMIXEC/Claude-ADK-Skills.git)

# Install dependencies
cd ~/.claude-adk-skills
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Symlink skills to Claude Code
mkdir -p ~/.claude/skills
ln -sf ~/.claude-adk-skills/skills/*.md ~/.claude/skills/
```

### Prerequisites

- Python 3.11+
- Git
- Google Cloud credentials (`GOOGLE_API_KEY`)
- Optional: Pinecone API key (for RAG features)

### Standalone Orchestrator

After installation, run the multi-agent orchestrator:

```bash
# Text mode (default)
python -m adk_bidi

# Voice mode (native audio)
python -m adk_bidi --mode voice

# Multimodal (voice + vision)
python -m adk_bidi --mode multimodal

# With configuration file
python -m adk_bidi --config root_agent.yaml

# WebSocket server mode
python -m adk_bidi serve --port 8000
```

## Skills Overview

| Skill | Description |
|-------|-------------|
| `adk-skill-dispatcher` | **Auto-routing** - Automatically routes to the right ADK skill |
| `adk-adaptive-agent-generator` | Voice-driven custom agent creation |
| `adk-persona-builder` | 30+ pre-built expert personas |
| `adk-domain-expert-builder` | Custom domain expert agents |
| `adk-multi-agent-orchestrator` | Multi-agent coordination patterns |
| `adk-langgraph-orchestrator` | LangGraph stateful workflows |
| `adk-pinecone-rag` | Multimodal RAG with Pinecone |
| `adk-mcp-integration` | MCP external tool integration |
| `adk-rag-builder` | Vertex AI RAG integration |
| `adk-deployment-manager` | Production deployment |
| `adk-bidi-multi-agent` | Real-time multi-agent streaming |
| `adk-memory-manager` | Multi-agent memory systems |
| `adk-autonomous-agent` | Self-reasoning autonomous agents |

---

## Quick Start

### Create an Agent from Description

```bash
/adk-adaptive-agent-generator Build a customer service agent that handles support tickets and searches a knowledge base
```

### Use a Pre-built Persona

```bash
/adk-persona-builder --persona fitness_coach --specialization "strength training"
```

### Create Multimodal RAG Pipeline

```bash
/adk-pinecone-rag --action "setup" --index_name "knowledge_base"
/adk-pinecone-rag --action "ingest" --source "docs/" --namespace "product_docs"
/adk-pinecone-rag --action "create_agent"
```

### Deploy to Production

```bash
/adk-deployment-manager --target "cloud-run" --project "my-project"
```

---

## Adaptive Agent Generation

Describe what you need in natural language. The system extracts intent, designs architecture, and generates production-ready code.

```bash
/adk-adaptive-agent-generator Create a research assistant that searches the web, analyzes documents, and writes reports with citations
```

**What Happens:**
1. Intent extraction: domain, capabilities, tools needed
2. Architecture design: multi-agent vs single agent
3. Code generation: complete project structure
4. Approval: review and approve before deployment

**Generated Code:**
```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

research_agent = Agent(
    name="research_assistant",
    model="gemini-2.5-flash",
    instruction="""You are a research assistant.
    - Search the web for information
    - Analyze documents and extract key points
    - Write comprehensive reports with citations
    """,
    tools=[
        FunctionTool(web_search),
        FunctionTool(document_analyzer),
        FunctionTool(report_writer),
    ],
)
```

---

## Expert Personas

30+ pre-built personas across 5 categories:

### Expert Personas
- Historian, Scientist, Creative Writer
- Philosopher, Economist, Psychologist

### Professional Advisors
- Fitness Coach, Financial Advisor, Therapist
- Career Counselor, Nutritionist

### Language Tutors
- English, Spanish, Mandarin, French
- Conversational practice with pronunciation feedback

### Role-Playing
- Dungeon Master, Storyteller, Game Master
- Interactive fiction characters

### Domain Experts
- Coding Expert, Cooking Expert, Gardening Expert
- Mechanic, Photographer, Music Teacher

```bash
/adk-persona-builder --persona fitness_coach
```

**Generated Agent:**
```python
fitness_coach = Agent(
    name="fitness_coach",
    model="gemini-2.5-flash",
    instruction="""You are a certified fitness coach.

**Personality:** Motivational, encouraging, safety-focused
**Communication:** Direct, actionable, supportive

**Behavior:**
1. Prioritize safety - correct poor form immediately
2. Encourage progressive overload
3. Adapt to user's fitness level
4. Provide specific, measurable feedback
""",
)
```

---

## Multimodal RAG with Pinecone

Build knowledge bases with text, image, audio, and video search.

### Setup Pinecone Index

```bash
/adk-pinecone-rag --action "setup" --index_name "multimodal_kb"
```

### Ingest Multimodal Content

```python
from pinecone import Pinecone, EmbedModel

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

# Text embedding
text_embedding = pc.inference.embed(
    model=EmbedModel.Multilingual_E5_Large,
    inputs=["Your document text"],
    parameters={"input_type": "passage"}
).data[0].values

# Image embedding
image_embedding = pc.inference.embed(
    model="pinecone-clip-vit-base-patch32",
    inputs=[{"image": base64_image}]
).data[0].values

# Audio embedding (transcribe + embed)
transcription = pc.inference.transcribe(
    model="openai-whisper-large-v3",
    audio=base64_audio
)
audio_embedding = pc.inference.embed(
    model=EmbedModel.Multilingual_E5_Large,
    inputs=[transcription.text]
).data[0].values
```

### Cross-Modal Search

Search images with text, find text with images:

```python
def multimodal_search(query: str = None, image: str = None, audio: str = None) -> list:
    """Search with any modality."""
    if query:
        embedding = embed_text(query)
    elif image:
        embedding = embed_image(image)
    elif audio:
        embedding = embed_audio(audio)

    return index.query(vector=embedding, top_k=5, include_metadata=True)
```

---

## LangGraph Orchestration

Build stateful multi-agent workflows with LangGraph.

### Supervisor Pattern

```bash
/adk-langgraph-orchestrator --pattern "supervisor" \
  --agents "researcher,analyst,writer"
```

```python
from langgraph.graph import StateGraph, START, END

class WorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    research_data: dict
    analysis_results: dict
    final_output: str

builder = StateGraph(WorkflowState)
builder.add_node("researcher", researcher_node)
builder.add_node("analyst", analyst_node)
builder.add_node("writer", writer_node)

builder.add_edge(START, "researcher")
builder.add_edge("researcher", "analyst")
builder.add_edge("analyst", "writer")
builder.add_edge("writer", END)

graph = builder.compile()
```

### Conditional Routing

```bash
/adk-langgraph-orchestrator --pattern "conditional" \
  --router "intent_classifier"
```

### RAG Pipeline with LangGraph

```bash
/adk-langgraph-orchestrator --pattern "rag_workflow" \
  --vector_db "pinecone"
```

---

## MCP Integration

Connect to external tools via Model Context Protocol.

### Supported Servers

| Server | Use Case |
|--------|----------|
| Pinecone | Multimodal vector search |
| SQLite | Local database |
| PostgreSQL | Production database |
| Brave Search | Web search |
| GitHub | Repository access |
| GitLab | GitLab repositories |
| Notion | Notes and databases |
| Slack | Team messaging |

### Configuration

```bash
/adk-mcp-integration --servers "[pinecone,sqlite,brave_search,github]"
```

```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

sqlite_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='uvx',
            args=["mcp-server-sqlite", "--db-path", "data.db"],
        ),
    ),
)

agent = Agent(
    name="db_agent",
    model="gemini-2.5-flash",
    tools=[sqlite_tools],
)
```

---

## Production Deployment

### Cloud Run

```bash
/adk-deployment-manager --target "cloud-run" --project "my-project"
```

**Generated Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
ENV PYTHONPATH=/app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Vertex AI Agent Engine

```bash
/adk-deployment-manager --target "agent-engine" --project "my-project"
```

### GKE (Kubernetes)

```bash
/adk-deployment-manager --target "gke" --cluster "my-cluster"
```

---

## Real-Time Bidirectional Streaming (adk_bidi)

Build production-ready real-time agents with native audio, multi-agent coordination, and autonomous behavior.

### Voice Assistant

```bash
/adk-bidi-multi-agent --type "voice" --personality "friendly"
```

```python
from adk_bidi import VoiceAgent
from adk_bidi.agents.voice_agent import VoicePersonality

agent = VoiceAgent(
    name="voice_assistant",
    instruction="You are a helpful voice assistant.",
    personality=VoicePersonality.FRIENDLY,
)
# Uses gemini-live-2.5-flash-native-audio
```

### Multi-Agent Real-Time Coordination

```bash
/adk-bidi-multi-agent --type "supervisor" --agents "researcher,analyst,writer"
```

```python
from adk_bidi import MultiAgentSupervisor, SharedMemory
from google.adk.agents import Agent

# Create specialist agents
researcher = Agent(name="researcher", model="gemini-live-2.5-flash-native-audio", ...)
analyst = Agent(name="analyst", model="gemini-live-2.5-flash-native-audio", ...)

# Coordinate with supervisor
supervisor = MultiAgentSupervisor(
    agents=[researcher, analyst],
    shared_memory=SharedMemory(),
)
```

### Autonomous Agent

```bash
/adk-autonomous-agent --type "research" --goal "Find and summarize AI research papers"
```

```python
from adk_bidi import AutonomousAgent

agent = AutonomousAgent(
    name="researcher",
    goal="Research and synthesize information about AI trends",
    enable_proactivity=True,
)
# Agent reasons autonomously: OBSERVE -> THINK -> PLAN -> ACT -> REFLECT
```

### Memory Systems

```bash
/adk-memory-manager --type "shared" --conflict-strategy "last-write-wins"
```

```python
from adk_bidi import WorkingMemory, SharedMemory, PersistentMemoryStore

# Working memory (short-term with attention scoring)
working = WorkingMemory(max_size=20)
working.add("user_name", "Alice", importance=0.8)

# Shared memory (cross-agent coordination)
shared = SharedMemory()
await shared.write("task", "research AI", "agent1")

# Persistent memory (Pinecone vector storage)
persistent = PersistentMemoryStore(namespace="knowledge")
persistent.store_memory("fact1", "Python is a programming language", importance=0.7)
```

### Example Applications

```bash
# Voice Assistant
python -m adk_bidi.examples.voice_assistant.main

# Multimodal Chat
python -m adk_bidi.examples.multimodal_chat.main

# Autonomous Researcher
python -m adk_bidi.examples.autonomous_researcher.main

# Multi-Agent Support Team
python -m adk_bidi.examples.multi_agent_support.main
```

---

## Project Structure

```
CLAUDE-ADK-SKILLS/
+-- .claude-plugin/
|   +-- plugin.json
|   +-- marketplace.json
+-- skills/
|   +-- adk-adaptive-agent-generator.md
|   +-- adk-persona-builder.md
|   +-- adk-domain-expert-builder.md
|   +-- adk-multi-agent-orchestrator.md
|   +-- adk-langgraph-orchestrator.md
|   +-- adk-pinecone-rag.md
|   +-- adk-mcp-integration.md
|   +-- adk-rag-builder.md
|   +-- adk-deployment-manager.md
|   +-- adk-bidi-multi-agent.md        # NEW
|   +-- adk-memory-manager.md          # NEW
|   +-- adk-autonomous-agent.md        # NEW
+-- adk_bidi/                          # NEW
|   +-- core/
|   |   +-- live_session.py            # LiveRequestQueue wrapper
|   |   +-- streaming_config.py        # Streaming presets
|   |   +-- websocket_server.py        # FastAPI WebSocket
|   +-- memory/
|   |   +-- working_memory.py          # Short-term memory
|   |   +-- semantic_memory.py         # Knowledge graph
|   |   +-- shared_memory.py           # Cross-agent state
|   |   +-- persistent_store.py        # Pinecone persistence
|   +-- agents/
|   |   +-- bidi_agent.py              # Base bidirectional agent
|   |   +-- voice_agent.py             # Native audio agent
|   |   +-- multimodal_agent.py        # Text + audio + video
|   |   +-- autonomous_agent.py        # Self-reasoning agent
|   +-- orchestration/
|   |   +-- supervisor.py              # Multi-agent supervisor
|   |   +-- router.py                  # Intent-based routing
|   |   +-- swarm.py                   # Parallel agent swarm
|   +-- examples/
|       +-- voice_assistant/
|       +-- multimodal_chat/
|       +-- autonomous_researcher/
|       +-- multi_agent_support/
+-- mcp_servers/
|   +-- CATALOG.md
+-- README.md
```

---

## Environment Variables

```bash
# Google AI
GOOGLE_API_KEY=your_gemini_api_key

# Pinecone (Multimodal RAG)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_HOST=your_index_host

# MCP Servers
BRAVE_API_KEY=your_brave_api_key
GITHUB_TOKEN=your_github_token
NOTION_TOKEN=your_notion_token
SLACK_BOT_TOKEN=your_slack_token

# GCP Deployment
GOOGLE_CLOUD_PROJECT=your_project_id
```

---

## Requirements

```
google-adk>=1.0.0
pinecone>=5.0.0
langgraph>=0.2.0
langchain-core>=0.3.0
vertexai>=1.0.0
fastapi>=0.100.0     # For WebSocket server
uvicorn>=0.20.0      # ASGI server
```

---

## Documentation

- [Google ADK Docs](https://google.github.io/adk-docs/)
- [Pinecone Docs](https://docs.pinecone.io/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [MCP Specification](https://modelcontextprotocol.io/)

---

## License

MIT License - See LICENSE file for details.
