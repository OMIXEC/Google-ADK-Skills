---
wave: 1
depends_on: []
files_modified:
  - skills/adk-quick-start/SKILL.md
  - skills/adk-simple-agents/SKILL.md
  - skills/adk-custom-agent-builder/SKILL.md
  - plugin.json
autonomous: false
requirements: [skill-architecture, adk-patterns]
---

# Plan 01: Refactor Skill Architecture Using Skill-Builder Patterns

## Objective
Restructure existing ADK skills to follow skill-builder best practices with proper YAML frontmatter, gerund naming, progressive disclosure, and intention-revealing file organization.

## must_haves
- [ ] All skills have proper YAML frontmatter (name, description, version)
- [ ] Description field optimized for Claude invocation triggers
- [ ] Skills organized with supporting reference files
- [ ] No single skill exceeds 500 lines
- [ ] CLI-focused tooling (no Python scripts for skill execution)

## Tasks

<task id="1.1" type="refactor">
<title>Update YAML Frontmatter for All Skills</title>
<description>
Add proper skill-builder compliant frontmatter to all 12+ ADK skills:
- name: kebab-case skill name
- description: Trigger-optimized description (max 1024 chars) answering "when would Claude invoke this?"
- version: SemVer version number
</description>
<files>
- skills/adk-skill-dispatcher.md
- skills/adk-adaptive-agent-generator.md
- skills/adk-persona-builder.md
- skills/adk-domain-expert-builder.md
- skills/adk-multi-agent-orchestrator.md
- skills/adk-langgraph-orchestrator.md
- skills/adk-pinecone-rag.md
- skills/adk-mcp-integration.md
- skills/adk-rag-builder.md
- skills/adk-deployment-manager.md
- skills/adk-bidi-multi-agent.md
- skills/adk-memory-manager.md
- skills/adk-autonomous-agent.md
</files>
</task>

<task id="1.2" type="create">
<title>Create Progressive Disclosure Reference Files</title>
<description>
Extract detailed content from large skills into supporting reference files:
- references/agent-patterns.md - ADK agent architecture patterns
- references/tool-catalog.md - All FunctionTool and MCPToolset patterns
- references/deployment-configs.md - Cloud Run, Vertex AI, GKE configs
- references/streaming-patterns.md - LiveRequestQueue, bidi patterns
</description>
<files>
- skills/references/agent-patterns.md
- skills/references/tool-catalog.md
- skills/references/deployment-configs.md
- skills/references/streaming-patterns.md
</files>
</task>

<task id="1.3" type="create">
<title>Create Templates Directory</title>
<description>
Add Jinja2/template files for code generation:
- templates/agent-basic.py.j2
- templates/agent-multiagent.py.j2
- templates/agent-rag.py.j2
- templates/dockerfile.j2
- templates/cloud-run.yaml.j2
</description>
<files>
- skills/templates/agent-basic.py.j2
- skills/templates/agent-multiagent.py.j2
- skills/templates/agent-rag.py.j2
- skills/templates/dockerfile.j2
- skills/templates/cloud-run.yaml.j2
</files>
</task>

## Verification Criteria
- [ ] `grep -l "^---" skills/*.md` shows all skills have frontmatter
- [ ] No skill file exceeds 500 lines: `wc -l skills/*.md | sort -n`
- [ ] Reference files exist and are properly linked
- [ ] Templates directory created with working templates

## Acceptance
Plans achieve refactored skill architecture following skill-builder patterns.
