# Ralph Autonomous Development - ADK Claude Plugin

This directory contains all configuration for Ralph, an autonomous AI development agent building the unified ADK Claude Plugin.

## Files Overview

### 1. PROMPT.md (319 lines)
**Ralph Development Instructions**
- Core objectives and key principles
- Specific guidance for ADK plugin development
- Task execution workflow
- Status reporting requirements
- Exit scenarios and completion criteria

**For Ralph**: Read this first to understand the development philosophy and principles.

### 2. @fix_plan.md (415 lines)
**Prioritized Task List**
- 8 phases with 30+ specific tasks
- Task dependencies and blocking relationships
- Priority ordering (critical path first)
- Execution notes for Ralph
- Success metrics and checkpoints

**For Ralph**: This is your task list. Work through it sequentially, marking tasks complete as [x].

### 3. specs/plugin-requirements.md (379 lines)
**Detailed Requirements Specification**
- Complete plugin architecture description
- Component specifications (8 skills, 6 commands, 3 agents, etc.)
- Quality requirements and standards
- Integration guidelines with existing code
- Success criteria checklist

**For Ralph**: Read this to understand what each component should do.

### 4. @AGENT.md (591 lines)
**Build & Run Instructions**
- Project structure and directory layout
- Setup and development environment
- How to run Ralph
- Testing instructions (unit, integration, manual)
- Validation commands
- File modification rules
- Commit strategy
- Troubleshooting guide

**For Ralph**: Use this as reference for build commands, testing, and validation.

## Ralph Execution

### Start Autonomous Development

```bash
cd /home/omixec/Claude-ADK-Skills
python -m ralph --prompt .ralph/PROMPT.md --plan .ralph/@fix_plan.md
```

Ralph will:
1. Read PROMPT.md (development instructions)
2. Read @fix_plan.md (task list)
3. Execute first unchecked [ ] task
4. Mark completed tasks as [x]
5. Output status in RALPH_STATUS format
6. Loop until all tasks complete or EXIT_SIGNAL=true

### Monitor Progress

```bash
# Watch execution logs
tail -f .ralph/logs/latest.log

# Check task completion
grep "^\- \[x\]" .ralph/@fix_plan.md | wc -l

# View generated docs
ls .ralph/docs/generated/
```

## Key Points for Ralph

### What You're Building
A comprehensive Claude Code plugin that consolidates 13 existing ADK skills into 8 unified, beginner→advanced skills for interactive agent building.

### 8 Skills to Create
1. **adk-quick-start** - Entry point with questionnaire
2. **adk-simple-agents** - Pre-built templates (6 templates)
3. **adk-custom-agent-builder** - Build from scratch
4. **adk-multi-agent-workflows** - Orchestration patterns (5 patterns)
5. **adk-knowledge-systems** - RAG + memory systems
6. **adk-real-time-agents** - Voice + multimodal + streaming
7. **adk-integration-tools** - MCP servers (8 supported)
8. **adk-production-deployment** - Cloud Run + Vertex AI + GKE

### 6 Commands to Create
- `/adk:init` - Initialize project
- `/adk:test` - Run agent test
- `/adk:examples` - View examples
- `/adk:docs` - Quick docs access
- `/adk:config` - Manage settings
- `/adk:status` - Check environment

### 3 Agents to Create
- **code-validator** - Validate agent code
- **code-improver** - Suggest improvements
- **architecture-advisor** - Choose orchestration patterns

### Additional Components
- 2 Hooks (PreToolUse, SessionStart)
- 1 MCP Integration (Pinecone)
- Plugin Settings (.claude/adk-skills.local.md)
- Comprehensive README

### Critical Success Factors
✅ All paths use portable reference: `/home/omixec/.claude/plugins/cache/claude-plugins-official/plugin-dev/e30768372b41`
✅ Each skill has examples and progressive disclosure
✅ Commands are concise and integrated
✅ Agents are autonomous and effective
✅ Plugin structure passes validation
✅ All components work in Claude Code

## Status Tracking

### Current Progress
- [ ] Phase 1: Plugin structure (2 tasks)
- [ ] Phase 2: 8 skills (8 tasks)
- [ ] Phase 3: 6 commands (6 tasks)
- [ ] Phase 4: 3 agents (3 tasks)
- [ ] Phase 5: Hooks + MCP (2 tasks)
- [ ] Phase 6: Documentation (3 tasks)
- [ ] Phase 7: Validation (5 tasks)
- [ ] Phase 8: Final polish (4 tasks)

**Total Tasks**: 33
**Completed**: 0
**In Progress**: 0
**Remaining**: 33

## Questions Ralph Should Ask

If blocked, check:
1. **Specs**: Does `.ralph/specs/plugin-requirements.md` clarify the requirement?
2. **Plan**: Is there a dependent task not completed yet in `.ralph/@fix_plan.md`?
3. **Existing Code**: Can you reuse code from `/home/omixec/Claude-ADK-Skills/skills/` or `adk_bidi/`?
4. **Examples**: Are there examples in `.ralph/specs/` you can follow?
5. **Previous Loops**: Check `.ralph/logs/` for similar attempts

## Next Steps

1. **Ralph starts**: `python -m ralph --prompt .ralph/PROMPT.md --plan .ralph/@fix_plan.md`
2. **Ralph loops**: Executes one task per loop, outputs RALPH_STATUS
3. **Ralph completes**: When all tasks marked [x] and tests passing, EXIT_SIGNAL=true
4. **Manual testing**: After Ralph completes, manually test in Claude Code
5. **Deployment**: Push to GitHub, add to marketplace

---

Good luck, Ralph! You've got this. Build it right the first time. 🚀
