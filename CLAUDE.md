# ADK Skills — Routing Rules

This repo provides 8 Claude Code skills for building Google ADK (Agent Development Kit) agents. All skills live in `skills/` with standard SKILL.md format.

## Skill Routing

When a user request matches a trigger below, invoke the corresponding skill.

| # | Skill | Triggers |
|---|-------|----------|
| 1 | `adk-agentic-prod-workflows` | "build a workflow", "design multi-agent system", "scaffold agent project", "deploy ADK agent", "production workflow", "graph agent", "parallel agent", "sequential agent", "loop agent", "A2A agent", "MCP integration", "CI/CD for agents" |
| 2 | `adk-agent-builder` | "create an agent", "build agent", "add agent node", "configure agent mode", "task mode", "single-turn agent", "graph-based workflow" |
| 3 | `adk-architecture` | "how does ADK work", "ADK architecture", "event flow", "resumption", "checkpoint", "BaseNode", "NodeRunner", "runner roles", "LLM context orchestration" |
| 4 | `adk-debug` | "debug agent", "inspect session", "test agent behavior", "troubleshoot tool call", "event flow issue", "model problem" |
| 5 | `adk-git` | "commit", "push", "pull", "rebase", "branch", "PR", "cherry-pick", "git operation" |
| 6 | `adk-sample-creator` | "create a sample", "add example", "demonstrate agent pattern", "fan-out example", "dynamic node sample" |
| 7 | `adk-setup` | "set up ADK", "install ADK", "configure environment", "get started with ADK", "prepare for contributing" |
| 8 | `adk-style` | "code style", "format code", "naming convention", "lint", "nit", "imports", "typing", "Pydantic pattern", "testing rules" |

## Agent Definitions

Agent definitions for ADK runtime are in `agents/` — these are `.agent.yaml` files that can be loaded by the ADK Python runtime. Python tools and callbacks supporting these agents are in `adk-python/`.

## Legacy Skills

`legacy-skills/` contains 13 older skill files (raw markdown, not SKILL.md format). These need conversion to SKILL.md format before use.

## IDE Support

Run `install.sh` to install skills into your IDE:
- `--target claude-code` (default)
- `--target gemini-cli`
- `--target opencode`
- `--target cursor`
- `--target all`
