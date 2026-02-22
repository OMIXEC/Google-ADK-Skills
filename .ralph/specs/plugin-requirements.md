# Unified ADK Claude Plugin - Requirements Specification

## Project Overview

Create a comprehensive, unified Claude Code plugin for autonomous multi-agent development with Google's ADK. The plugin enables Claude Code users to build, orchestrate, deploy, and manage sophisticated AI agents through an interactive guided experience.

**Target Users**: Claude Code developers building production-ready AI agents
**Primary Use Case**: Interactive agent builder with guidance and best practices

---

## Core Plugin Architecture

### Plugin Manifest & Structure
- **Name**: `claude-adk-skills` (unified)
- **Version**: 2.0.0 (complete redesign)
- **Location**: `/home/omixec/Claude-ADK-Skills/` (base directory)
- **Structure**: Standard Claude Code plugin layout with auto-discovery

### Directory Organization
```
claude-adk-skills/
├── .claude-plugin/
│   └── plugin.json          # Manifest (requires careful configuration)
├── commands/                # 6 slash commands
├── agents/                  # 3 specialized agents
├── skills/                  # 8 beginner→advanced skills
├── hooks/                   # Event handlers
├── .mcp.json               # MCP server definitions
└── scripts/                # Helper utilities
```

---

## Component Specifications

### 1. SKILLS (8 Total - Beginner to Advanced Progression)

All skills MUST follow progressive disclosure pattern: brief description → focused guidance → actionable next steps.

#### Tier 1: Discovery & Basics

**Skill 1: adk-quick-start**
- **Location**: `skills/adk-quick-start/SKILL.md`
- **Purpose**: Entry point - route users to appropriate skill based on their goal
- **Triggers**: "What can I build?", "I want to create an agent", "Tell me about ADK"
- **Output**: Guided questionnaire with 4 questions → recommendation of next skill
- **Components**:
  - `SKILL.md`: Main guidance (800-1000 words)
  - `references/agent-types.md`: Overview of all agent types
  - `examples/quick-answers.md`: Common scenarios and answers

**Skill 2: adk-simple-agents**
- **Location**: `skills/adk-simple-agents/SKILL.md`
- **Purpose**: Pre-built agent templates (personas, specialists)
- **Triggers**: "Build a fitness coach", "Create a researcher", "Make a teaching assistant"
- **Templates**: Fitness Coach, Researcher, Domain Expert, Teaching Assistant, Customer Service, Analyst (6 templates)
- **Output**: Complete agent code, ready to test locally
- **Components**:
  - `SKILL.md`: Main skill (1000-1200 words)
  - `templates/`: 6 agent template files (Python + YAML)
  - `scripts/generate-agent.py`: Template expansion script
  - `examples/`: 3 working examples with test cases

#### Tier 2: Custom Building

**Skill 3: adk-custom-agent-builder**
- **Location**: `skills/adk-custom-agent-builder/SKILL.md`
- **Purpose**: Build agents from scratch with architecture guidance
- **Triggers**: "Build a custom agent", "Design an agent from scratch", "I need [complex scenario]"
- **Architecture Guidance**: Single vs multi-agent, tool choices, instruction design
- **Output**: Tailored agent code based on user needs
- **Components**:
  - `SKILL.md`: Main skill (1200-1500 words)
  - `references/`: Architecture patterns, instruction design
  - `scripts/agent-generator.py`: Code generation from user specs
  - `examples/`: Complex agent examples (research, analysis, coding)

**Skill 4: adk-multi-agent-workflows**
- **Location**: `skills/adk-multi-agent-workflows/SKILL.md`
- **Purpose**: Orchestration patterns (supervisor, hierarchical, conditional routing)
- **Triggers**: "Multi-agent system", "Agent coordination", "Agent team", "LangGraph"
- **Patterns Covered**: Supervisor, Hierarchical, Conditional Routing, Debate, Tool Use Routing
- **Output**: Orchestration code + agent definitions
- **Components**:
  - `SKILL.md`: Main skill (1200-1400 words)
  - `references/patterns.md`: Detailed pattern descriptions
  - `scripts/pattern-generator.py`: Generate orchestration code
  - `examples/`: 4 working orchestration examples

#### Tier 3: Enhancement

**Skill 5: adk-knowledge-systems**
- **Location**: `skills/adk-knowledge-systems/SKILL.md`
- **Purpose**: RAG pipelines, Pinecone integration, memory management
- **Triggers**: "Build RAG", "Vector search", "Agent memory", "Knowledge base"
- **Components**:
  - Working Memory (short-term, attention scoring)
  - Shared Memory (cross-agent coordination)
  - Persistent Memory (Pinecone vector storage)
  - RAG Pipelines (text, multimodal)
- **Output**: Memory system code + RAG setup
- **Components**:
  - `SKILL.md`: Main skill (1300-1500 words)
  - `references/`: Memory types, RAG patterns, Pinecone setup
  - `scripts/`: Memory initialization, RAG setup, Pinecone helpers
  - `examples/`: 3 memory + RAG examples

**Skill 6: adk-real-time-agents**
- **Location**: `skills/adk-real-time-agents/SKILL.md`
- **Purpose**: Bidirectional streaming, voice agents, multimodal
- **Triggers**: "Voice agent", "Real-time streaming", "Live session", "Multimodal"
- **Features**:
  - Native audio with gemini-live-2.5-flash-native-audio
  - Real-time streaming with WebSocket
  - Multimodal input (text, audio, video)
  - Event-based communication
- **Output**: Voice agent code + streaming setup
- **Components**:
  - `SKILL.md`: Main skill (1300-1500 words)
  - `references/`: Streaming architecture, event patterns
  - `scripts/`: WebSocket server, streaming config, audio handling
  - `examples/`: 3 real-time agent examples

#### Tier 4: Advanced

**Skill 7: adk-integration-tools**
- **Location**: `skills/adk-integration-tools/SKILL.md`
- **Purpose**: MCP server integration, external tools
- **Triggers**: "MCP integration", "Connect to external tools", "Add MCP server"
- **Supported Servers**: Pinecone, SQLite, PostgreSQL, Brave Search, GitHub, GitLab, Notion, Slack
- **Output**: MCP configuration + agent integration code
- **Components**:
  - `SKILL.md`: Main skill (1200-1400 words)
  - `references/mcp-servers.md`: Server catalog with setup
  - `scripts/`: MCP setup helpers, tool integrations
  - `examples/`: 3 MCP integration examples

**Skill 8: adk-production-deployment**
- **Location**: `skills/adk-production-deployment/SKILL.md`
- **Purpose**: Cloud Run, Vertex AI, GKE deployment
- **Triggers**: "Deploy agent", "Production deployment", "Cloud Run", "Vertex AI"
- **Targets**:
  - Cloud Run (containerized agents)
  - Vertex AI Agent Engine (managed agents)
  - GKE (Kubernetes orchestration)
- **Output**: Deployment configuration + Docker/K8s files
- **Components**:
  - `SKILL.md`: Main skill (1300-1500 words)
  - `references/`: Deployment guides per target
  - `scripts/`: Deployment automation, testing, monitoring
  - `examples/`: 3 deployment examples

---

### 2. COMMANDS (6 Total)

All commands should be concise, integrated with skills, and provide immediate value.

**Command 1: `/adk:init`**
- **Purpose**: Initialize new ADK project
- **Input**: Project name, agent type (simple/custom/multi)
- **Output**: Project structure with README, requirements.txt, examples
- **Implementation**: Bash script scaffolding

**Command 2: `/adk:test`**
- **Purpose**: Run local agent test/demo
- **Input**: Agent file path or inline code
- **Output**: Test results, agent behavior demo
- **Implementation**: Python test runner

**Command 3: `/adk:examples`**
- **Purpose**: Show project structure and examples
- **Input**: Optional: specific skill or agent type
- **Output**: File tree, key files, suggested next steps
- **Implementation**: Display formatted project structure

**Command 4: `/adk:docs`**
- **Purpose**: Quick access to ADK documentation
- **Input**: Optional: search term or skill name
- **Output**: Relevant docs, links, quick reference
- **Implementation**: Search + format docs

**Command 5: `/adk:config`**
- **Purpose**: Manage plugin settings (.env, API keys)
- **Input**: Setting key and value
- **Output**: Saved to `.claude/adk-skills.local.md`
- **Implementation**: Settings reader/writer

**Command 6: `/adk:status`**
- **Purpose**: Check dependencies and environment
- **Input**: None
- **Output**: Python version, ADK version, API key status, dependencies
- **Implementation**: Environment checker script

---

### 3. AGENTS (3 Total)

Autonomous agents for validation and assistance.

**Agent 1: adk-code-validator**
- **Description**: Validates generated agent code for best practices, security, and ADK conventions
- **Triggers**: After skill generates code, on request with `validate_agent_code`
- **Capabilities**:
  - Code review against ADK patterns
  - Security analysis
  - Performance checks
  - Convention compliance
- **Tools**: Read, Grep (code analysis)

**Agent 2: adk-code-improver**
- **Description**: Suggests improvements and optimizations for agent code
- **Triggers**: After validation, on request with `improve_agent_code`
- **Capabilities**:
  - Performance optimization
  - Error handling enhancement
  - Documentation improvements
  - Tool integration suggestions
- **Tools**: Read, Edit (code modification)

**Agent 3: adk-architecture-advisor**
- **Description**: Helps choose orchestration patterns and architecture
- **Triggers**: During multi-agent design phase, on request with `advise_architecture`
- **Capabilities**:
  - Pattern recommendation
  - Scalability analysis
  - Tool selection guidance
  - Implementation roadmap
- **Tools**: Read, Grep (pattern analysis)

---

### 4. HOOKS (2 Total)

Event-driven automation.

**Hook 1: PreToolUse (Write)**
- **Event**: Before Write tool executes
- **Matcher**: Files matching `*agent*.py`, `*orchestrator*.py`
- **Action**: Run code validator on generated code
- **Implementation**: Bash script with validation logic

**Hook 2: SessionStart**
- **Event**: When Claude Code session starts with plugin enabled
- **Action**: Check ADK dependencies, offer setup if missing
- **Implementation**: Bash script with dependency check

---

### 5. MCP INTEGRATION (1 Server)

**Pinecone MCP Server**
- **Purpose**: Vector search and multimodal RAG operations
- **Configuration**: `.mcp.json` with server params
- **Tools**: embed, upsert, query, delete
- **Integration**: Used by knowledge-systems skill

---

### 6. SETTINGS (Plugin Configuration)

**File**: `.claude/adk-skills.local.md`

**Fields**:
- `GOOGLE_API_KEY` (required) - Gemini API key
- `PINECONE_API_KEY` (optional) - Pinecone API key
- `PINECONE_INDEX_HOST` (optional) - Pinecone index host
- `DEFAULT_MODEL` (optional, default: gemini-2.5-flash)
- `DEPLOYMENT_PROJECT` (optional) - Google Cloud project ID
- `DEPLOYMENT_REGION` (optional, default: us-central1)

---

## Quality Requirements

### Skill Quality Standards
- ✅ Progressive disclosure (overview → guidance → examples)
- ✅ Third-person descriptions
- ✅ Specific trigger phrases (not generic)
- ✅ 800-1500 words per skill body
- ✅ Working examples for every major feature
- ✅ Clear next steps and navigation

### Code Generation Quality
- ✅ Production-ready code
- ✅ Proper error handling
- ✅ Type hints (Python 3.11+)
- ✅ Docstrings for complex functions
- ✅ Follows Google ADK conventions

### Plugin Structure Quality
- ✅ Manifest validation passes
- ✅ All paths use `/home/omixec/.claude/plugins/cache/claude-plugins-official/plugin-dev/e30768372b41`
- ✅ Components auto-discover correctly
- ✅ README comprehensive and tested

### Testing
- ✅ Each command works and produces output
- ✅ Each skill triggers on specified phrases
- ✅ Agents function autonomously
- ✅ Hooks execute without errors
- ✅ MCP server integrates with agents

---

## Integration with Existing Code

### Reuse Existing Skills
The plugin should integrate existing skills where possible:
- Consolidate logic from existing 13 skills into 8 new skills
- Reference existing templates, patterns, and utilities
- Maintain backward compatibility where feasible

### Consolidation Approach
- **adk-simple-agents**: Consolidates persona-builder, domain-expert-builder
- **adk-custom-agent-builder**: Consolidates adaptive-agent-generator
- **adk-multi-agent-workflows**: Consolidates langgraph-orchestrator, multi-agent-orchestrator, bidi-multi-agent
- **adk-knowledge-systems**: Consolidates pinecone-rag, rag-builder, memory-manager
- **adk-real-time-agents**: Extracts voice/multimodal from bidi-multi-agent
- **adk-integration-tools**: Consolidates mcp-integration
- **adk-production-deployment**: Consolidates deployment-manager

### Python Package Integration
- Leverage existing `adk_bidi` package
- Use existing classes and utilities
- Maintain CLI entry points
- Ensure skills reference correct package versions

---

## Success Criteria

1. ✅ All 8 skills created with progressive disclosure
2. ✅ All 6 commands functional and integrated
3. ✅ All 3 agents autonomous and effective
4. ✅ Plugin structure valid and complete
5. ✅ All paths portable (no hardcoded absolute paths)
6. ✅ Comprehensive README with setup instructions
7. ✅ Can be tested in Claude Code without errors
8. ✅ Agents can auto-generate working code
9. ✅ All components follow naming conventions
10. ✅ Documentation complete and examples working

---

## Technical Constraints

- **Python Version**: 3.11+
- **Framework**: Google ADK, LangGraph, LiteLLM
- **Base Path**: `/home/omixec/.claude/plugins/cache/claude-plugins-official/plugin-dev/e30768372b41`
- **Plugin Root**: `/home/omixec/Claude-ADK-Skills/`
- **No external dependencies** beyond what's in requirements.txt

---

## File Statistics Target

- **Skills**: 8 (with supporting files = ~40 files total)
- **Commands**: 6 (markdown files)
- **Agents**: 3 (markdown files)
- **Configuration**: 3 (plugin.json, hooks.json, .mcp.json)
- **Scripts**: 8-10 (helper utilities)
- **Examples**: 10-15 (working demonstrations)
- **Documentation**: 1 comprehensive README + inline docs

---

## Delivery Artifacts

1. Complete `/home/omixec/Claude-ADK-Skills/.claude-plugin/` structure
2. All 8 skills with SKILL.md and supporting files
3. All 6 commands as `.md` files
4. All 3 agents as `.md` files
5. hooks.json and hook scripts
6. .mcp.json with Pinecone config
7. Comprehensive README
8. Example configurations and projects
9. This specification and implementation plan
