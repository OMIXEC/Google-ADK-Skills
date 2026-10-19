---
name: adk-graph-workflows
description: >-
  Designs and scaffolds ADK 2.x multi-agent workflows: graph, dynamic,
  collaborative, and template (sequential, parallel, loop) shapes, project
  layout, code generation, and extension of an existing workflow. Use when
  deciding how agents and deterministic steps connect, scaffolding a workflow
  project, routing conditionally, fanning out and joining, or adding nodes to a
  running graph. Don't use for the internals of one agent — models, tools,
  memory, MCP, A2A (use adk-agent-architecture); for CI/CD, containers, or
  cloud targets (use adk-deploy-production); for Go or TypeScript templates
  (use adk-typescript-go-parity); or for autonomous goal loops and LangGraph
  state machines (use adk-autonomous-agent or adk-langgraph).
compatibility: google-adk>=2.9.2,<3
---

# ADK Graph Workflows

Decide the shape of the flow, then generate it. This skill owns the edges:
which node runs, in what order, on which branch, with what state crossing the
boundary.

Read `references/adk-2x-baseline.md` before writing code. It carries the
version floor, Python matrix, and core imports.

## Choose the shape

| Shape | Use when | Shape of the code |
|---|---|---|
| **Graph** (`Workflow`) | Branching, merging, retries, fan-out/fan-in, human pauses | Nodes plus declared edges |
| **Dynamic** | The graph is decided at runtime from data or tool output | Nodes and edges created programmatically |
| **Collaborative** | One coordinator delegates to specialists that share state | Coordinator plus sub-agents |
| **Template: sequential** | Fixed linear pipeline | `SequentialAgent` |
| **Template: parallel** | Independent concurrent work, then aggregate | `ParallelAgent` |
| **Template: loop** | Iterate until a quality gate passes | `LoopAgent` with `max_iterations` |

Prefer `Workflow` for new complex orchestration. The three template agents
remain valid for genuinely linear, fan-out, or retry-until-good flows; do not
wrap a straight line in a graph for its own sake.

## Design pass

Translate the request into:

1. **Nodes** — LLM agents, deterministic functions, validators, retrievers.
2. **Edges** — sequence, conditional branches, fan-out, join.
3. **State** — what each node writes with `output_key` and what the next node
   reads.
4. **Pauses** — which nodes need human approval and therefore a resumable
   boundary.

Then check the seams:

- A node with `output_schema` must not also declare tools.
- Fan-out branches must not write the same state key.
- A loop needs a termination condition that does not depend on the model
  choosing to stop.
- A human-in-the-loop pause is a checkpoint; verify the workflow is resumable
  before promising it.

## Scaffold a project

```bash
python scripts/init_adk_workflow.py --type graph --lang python --name order-flow
```

Supported Python types: `graph`, `dynamic`, `collaborative`, `template-seq`,
`template-parallel`, `template-loop`. The script can also emit Go and TS
skeletons; the reference templates for those runtimes live in
`adk-typescript-go-parity`.

Generate or patch workflow code from a composition file:

```bash
python scripts/compose_workflow.py --config workflow.yaml --output app/workflow.py
```

Validate a workflow skill's structure before shipping it:

```bash
python scripts/quick_validate.py
```

Project layout produced by the scaffolder:

```text
<name>/
├── app/
│   ├── __init__.py
│   ├── workflow.py
│   ├── agents/
│   └── tools/
├── tests/
├── evals/
├── .env.example
└── requirements.txt
```

## Extend an existing workflow

1. Read the current nodes, edges, and state keys before editing.
2. Add the smallest new node or edge that satisfies the request.
3. Re-run `quick_validate.py`.
4. Update evals and CI only if the change alters observable behavior.

## References

| File | Load when |
|---|---|
| `references/adk-workflows.md` | Selecting or justifying a workflow shape |
| `references/multi-agent-patterns.md` | Choosing a coordination pattern |
| `references/adk-2x-baseline.md` | Version, imports, model IDs, migration cautions |

## Assets

`assets/<type>/` holds a runnable Python example per shape, each with its own
`README.md`: `graph-workflow`, `dynamic-workflow`, `collaborative-workflow`,
`template-sequential`, `template-parallel`, `template-loop`.

## Boundaries

- Agent internals — model choice, tools, MCP, A2A, memory — belong to
  `adk-agent-architecture`.
- Packaging, CI/CD, containers, and cloud targets belong to
  `adk-deploy-production`.
- Go and TypeScript templates belong to `adk-typescript-go-parity`.
