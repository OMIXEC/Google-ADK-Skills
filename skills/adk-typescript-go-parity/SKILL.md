---
name: adk-typescript-go-parity
description: >-
  Provides reference templates and parity notes for building ADK agents in Go and
  TypeScript. Use when the target runtime is Go or TypeScript, when porting a Python
  workflow to either, or when checking whether a feature exists outside Python. Don't
  use for Python agent or workflow work (use adk-graph-workflows or
  adk-agent-architecture), or as a substitute for the current SDK reference when a
  signature matters.
compatibility: google-adk>=2.9.2,<3
---

# ADK TypeScript and Go Parity

Python is the primary target of this library. This skill exists so Go and
TypeScript work has a correct starting point instead of a translated guess.

## What parity means here

- **Shapes, not features.** A template shows how the pieces fit; it does not
  promise that every Python API exists.
- **Verify before trusting.** When a signature matters, read the installed
  package or the current SDK reference. Do not infer a Go or TS API from its
  Python counterpart.
- **No third stack.** Do not add per-language variants of a skill. Extend the
  templates here or leave the capability out.

## Templates

| Path | What it is |
|---|---|
| `assets/go/graph-workflow/` | Graph workflow in Go |
| `assets/go/dynamic-workflow/` | Dynamic workflow in Go |
| `assets/go/collaborative-workflow/` | Coordinator plus sub-agents in Go |
| `assets/go/template-sequential/` | Sequential template in Go |
| `assets/go/template-parallel/` | Parallel template in Go |
| `assets/ts/graph-workflow/` | Graph workflow in TypeScript |
| `assets/ts/agent-server/` | TypeScript agent server with tools |
| `assets/ts/workflow-client/` | TypeScript client for a running workflow |

Each directory carries its own `README.md`, `go.mod` or `package.json`, and a
runnable entry point. Copy the directory, then change it in place; do not edit
the template.

## Porting checklist

1. Fix the runtime and ADK package version in the manifest.
2. Map the Python workflow shape to the closest template in the table above.
3. Re-verify every API against the installed package. Names drift more across
   languages than within one.
4. Keep model IDs identical to the Python side; a runtime port is not a model
   change.
5. Re-run the parity templates' own build and test commands before claiming
   parity.

## Boundaries

- Python workflow design belongs to `adk-graph-workflows`.
- Python agent internals belong to `adk-agent-architecture`.
