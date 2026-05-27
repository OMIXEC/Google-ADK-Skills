# ADK-SKILLS

Claude Code skills for Google's Agent Development Kit (ADK).

## Quick Start

### Download Skills (for developers)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ADK-SKILLS.git
cd ADK-SKILLS

# Option 1: Use skills directly from this repo
# Open your IDE in this directory - skills auto-activate

# Option 2: Install skills for your IDE
bash install.sh --target claude-code    # or: gemini-cli, opencode, cursor, windsurf, codex, all
```

# Contrubutars

# Fork and clone

git clone https://github.com/omixec/Claude-ADK-Skills
cd Claude-ADK-Skills

# Create new skill

mkdir -p skills/my-new-skill
cat > skills/my-new-skill/SKILL.md << 'EOF'

---

name: my-new-skill
description: Description of what the skill does and when to use it

---

# my-new-skill

## Instructions

1. Your instructions here
   EOF

# Add references (optional)

mkdir -p skills/my-new-skill/references

# Copy relevant documentation to references/

# Commit and push

git add .
git commit -m "Add my-new-skill"
git push origin main

# Create PR to upstream repository

```

## Available Skills (12)

| Skill | Focus Area |
|-------|------------|
| `adk-backend` | Runtime, sessions, state management |
| `adk-deployment` | Cloud Run, GKE, Vertex AI deployment (Vertex AI Agent Engine) |
| `adk-prompts` | Agent instructions, few-shot, cost optimization |
| `adk-tools` | Custom functions, built-in tools, OpenAPI |
| `adk-memory` | State, memory, persistence |
| `adk-mcp` | MCP integration, MCPToolset |
| `adk-a2a` | Agent-to-Agent protocol |
| `adk-agents` | Multi-agent patterns, orchestration |
| `adk-runtime` | Event loop, callbacks |
| `adk-configs` | YAML configs, environment variables |
| `adk-litellm` | 100+ LLM providers via LiteLLM |
| `adk-bidi-live` | Native audio, Live API streaming |

## Skill Structure

Each skill contains:
- `SKILL.md` - Skill definition with YAML frontmatter
- `references/` - Local copies of relevant documentation

## Usage

Skills auto-activate based on task context. Example triggers:
- "Help me build an ADK agent" → `adk-agents` skill
- "Deploy to Cloud Run" → `adk-deployment` skill
- "Add MCP tools" → `adk-mcp` skill

## Related Repositories

- **LIVEKIT-SKILLS** - LiveKit real-time voice/vision agent skills

## Documentation

See [CLAUDE.md](../CLAUDE.md) for detailed skill routing and agent definitions.

## Upcoming Enhancements

See [UPCOMING.md](../UPCOMING.md) for the curriculum alignment roadmap — cross-reference audit of `adk-agentic-prod-workflows` against `docs/adk-course/` production standards with prioritized gaps and recommended new files.
```
