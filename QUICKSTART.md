# Claude ADK Skills - Quick Start Guide

## Installation (60 seconds)

### Option 1: From GitHub (Recommended)
```bash
git clone https://github.com/OMIXEC/Claude-ADK-Skills.git
cd Claude-ADK-Skills
cc --plugin-dir $(pwd)
```

### Option 2: Using Install Script
```bash
curl https://raw.githubusercontent.com/OMIXEC/Claude-ADK-Skills/main/install.sh | bash
```

### Option 3: From Claude Code Marketplace
1. Open Claude Code
2. Go to Plugins
3. Search "Claude ADK Skills"
4. Click Install

## First Steps (2 minutes)

### 1. Check Environment
```bash
/adk:status
```

### 2. Configure API Keys
```bash
/adk:config set GOOGLE_API_KEY your_gemini_api_key
```

### 3. Initialize Project
```bash
/adk:init my-first-agent
cd my-first-agent
```

### 4. Test Locally
```bash
/adk:test agent.py
```

## Common Tasks

### Build Quick Agent
Ask Claude Code: **"Build a fitness coach"**
→ Uses adk-simple-agents skill with pre-built template

### Design Custom Agent
Ask Claude Code: **"Design a research agent"**
→ Uses adk-custom-agent-builder skill with guidance

### Build Multi-Agent System
Ask Claude Code: **"Build a coordinated agent system"**
→ Uses adk-multi-agent-workflows skill

### Add Memory & Knowledge
Ask Claude Code: **"Add RAG system to my agent"**
→ Uses adk-knowledge-systems skill

### Deploy to Production
Ask Claude Code: **"Deploy my agent to Cloud Run"**
→ Uses adk-production-deployment skill

## Commands Reference

```bash
/adk:init PROJECT_NAME          # Create new project
/adk:test agent.py               # Test locally
/adk:examples [FILTER]           # View examples
/adk:docs [SEARCH_TERM]         # Search docs
/adk:config [ACTION] KEY VALUE  # Manage settings
/adk:status                       # Check setup
```

## Get Help

- **View Examples**: `/adk:examples`
- **Search Docs**: `/adk:docs memory` or `/adk:docs deployment`
- **Check Setup**: `/adk:status`
- **Ask Claude**: "Tell me about [skill name]"

## Required Environment Variables

```bash
GOOGLE_API_KEY=your_gemini_api_key
```

## Optional Environment Variables

```bash
PINECONE_API_KEY=your_key
GITHUB_TOKEN=your_token
SLACK_BOT_TOKEN=your_token
# See README.md for complete list
```

## 8 Skills Available

1. **adk-quick-start** - Get oriented and explore
2. **adk-simple-agents** - Use pre-built templates
3. **adk-custom-agent-builder** - Build from scratch
4. **adk-multi-agent-workflows** - Coordinate agents
5. **adk-knowledge-systems** - Add memory & RAG
6. **adk-real-time-agents** - Voice & streaming
7. **adk-integration-tools** - Connect services
8. **adk-production-deployment** - Deploy agents

## Learning Path

### Beginner (30 min)
1. `/adk:status` - Verify setup
2. Ask "What can I build?" - Get oriented
3. Try a template - "Build a fitness coach"
4. Test locally - `/adk:test`

### Intermediate (2 hours)
1. Design custom agent - "Design a research agent"
2. Add tools and capabilities
3. Test thoroughly
4. Customize instructions

### Advanced (depends)
1. Build multi-agent system
2. Add knowledge systems (RAG)
3. Integrate external services
4. Deploy to production

## Troubleshooting

### "No API key configured"
```bash
/adk:config set GOOGLE_API_KEY your_key
```

### "Python 3.11+ required"
Check: `python3 --version`

### "Plugin not loading"
Verify: `cc --plugin-dir /path/to/plugin`

### "Agent test failing"
```bash
/adk:test --verbose agent.py
```

## Support

- 📖 Read documentation: `/adk:docs`
- 💡 View examples: `/adk:examples`
- 🔍 Search help: `/adk:docs [topic]`
- ❓ Ask Claude: Just type your question

## Next Steps

1. **Try it out**: `/adk:init my-project`
2. **Explore skills**: Ask Claude about any skill
3. **Build an agent**: Follow guided skill workflow
4. **Deploy**: Use production deployment skill when ready

---

**Ready to build?** Start with: `/adk:init my-first-agent`
