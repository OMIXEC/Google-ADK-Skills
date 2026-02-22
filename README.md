# Claude ADK Skills - Unified Agent Builder Plugin

A comprehensive Claude Code plugin for building, orchestrating, and deploying advanced AI agents using Google's ADK with multi-agent support, LangGraph, memory systems, and MCP integration.

## Features

✨ **8 Progressive Skills** - Beginner to advanced agent development
🎯 **6 Commands** - Quick operations for initialization, testing, docs, config
🤖 **3 Autonomous Agents** - Code validation, optimization, architecture guidance
🔄 **Multi-Agent Orchestration** - LangGraph-based workflow patterns
💾 **Knowledge & Memory** - RAG with Pinecone vector search
🎤 **Real-Time & Voice** - Native audio and bidirectional streaming
🔌 **MCP Integration** - Connect external services and databases
🚀 **Production Deployment** - Cloud Run, Vertex AI, Kubernetes

## Quick Start

### 1. Initialize Project
```bash
/adk:init my-agent
```

### 2. Choose Your Path
- **New to ADK?** → "What can I build?" (adk-quick-start)
- **Quick Template?** → "Build a fitness coach" (adk-simple-agents)
- **Custom Agent?** → "Design a research agent" (adk-custom-agent-builder)
- **Multi-Agent?** → "Build a coordinated system" (adk-multi-agent-workflows)
- **With Memory?** → "Add knowledge systems" (adk-knowledge-systems)
- **Voice?** → "Create voice agent" (adk-real-time-agents)
- **External Services?** → "Integrate tools" (adk-integration-tools)
- **Production?** → "Deploy agent" (adk-production-deployment)

### 3. Test Locally
```bash
/adk:test agent.py
```

## 8 Skills (Beginner → Advanced)

| Skill | Purpose | Best For |
|-------|---------|----------|
| **adk-quick-start** | Orientation and routing | Getting started, exploring |
| **adk-simple-agents** | Pre-built templates | Learning, quick prototypes |
| **adk-custom-agent-builder** | Build from scratch | Specific requirements |
| **adk-multi-agent-workflows** | Orchestration patterns | Complex problems |
| **adk-knowledge-systems** | RAG and memory | Information retrieval |
| **adk-real-time-agents** | Voice and streaming | Live interaction |
| **adk-integration-tools** | MCP servers | External services |
| **adk-production-deployment** | Cloud deployment | Going live |

## 6 Commands

```bash
/adk:init PROJECT                # Initialize new project
/adk:test agent.py               # Test agent locally
/adk:examples [FILTER]           # View available examples
/adk:docs [SEARCH]              # Search documentation
/adk:config [ACTION] [KEY] [VAL] # Manage settings
/adk:status                       # Check environment
```

## 3 Autonomous Agents

- **code-validator** - Validates code for best practices and security
- **code-improver** - Suggests optimizations and improvements
- **architecture-advisor** - Helps choose orchestration patterns

## Configuration

### Required
```bash
GOOGLE_API_KEY=your_gemini_key
```

### Optional
```bash
PINECONE_API_KEY=your_key
GITHUB_TOKEN=your_token
# ... see plugin.json for full list
```

Use `/adk:config set KEY VALUE` to configure.

## Installation

### From Marketplace
1. Open Claude Code
2. Go to Plugins
3. Search "Claude ADK Skills"
4. Click Install

### From Local
```bash
git clone https://github.com/OMIXEC/Claude-ADK-Skills.git
cd Claude-ADK-Skills
cc --plugin-dir $(pwd)
```

## Support

- `/adk:docs [topic]` - Search documentation
- `/adk:examples` - View examples
- `/adk:status` - Check setup
- Ask Claude Code questions about ADK concepts

## License

MIT License - See LICENSE file

---

**Start Building**: Ask Claude Code "What can I build with ADK?" to begin!
