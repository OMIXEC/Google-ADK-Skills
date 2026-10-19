# Changelog

Semantic versioning applies to the **skill library**, not to ADK. A rename or a
removal is a breaking change for anyone who routes on skill names or installs a
subset with `--skills`.

Format based on Keep a Changelog. Dates are UTC.

## Versioning policy

- **Major** — a skill is renamed or removed; a skill's contract changes in a
  way that invalidates existing installs or routing tables.
- **Minor** — a skill is added; a skill gains coverage without changing its
  trigger surface.
- **Patch** — content corrections, link fixes, description wording, and
  documentation that does not move a trigger.

The library's version is recorded in `.claude-plugin/plugin.json` and the
marketplace entry. It is deliberately independent of every ADK version.

---

## [1.1.0] — 2026-10-19

Adds one skill and closes the deferred-name backlog. The other eight names from
the original map are answered by existing skills rather than duplicated, so
the product count moves 26 → 27, not 35.

### Added

- **`adk-performance-scaling`** — latency decomposition, concurrent
  invocations, `max_llm_calls` and tool-thread caps, 429/5xx retry policy,
  context caching, event compaction, token accounting, and deployment sizing.
  Four references plus its own 2.x baseline.
- `skills/adk-agents` gains a custom-`BaseAgent` example and a routing section,
  absorbing `adk-router` and `adk-custom-agents`.
- `adk-agent-architecture` gains explicit context-window coverage, absorbing
  `adk-context-management`.
- `adk-deploy-production` states that evaluation, testing, observability, and
  guardrails are answered there, absorbing those four deferred names.

### Changed

- The five large references that carried invented APIs were corrected against
  the pinned source (see `SOURCES.md` § correctness sweep). Highlights:
  - `InProcessRunner` did not exist; every runnable example now uses
    `InMemoryRunner` with explicit session creation.
  - `StreamingMode` and `RunConfig` import from `google.adk.agents.run_config`,
    not `google.adk.runners`.
  - `EventsCompactionConfig` imports from `google.adk.apps.app`.
  - `RemoteA2aAgent` replaces `RemoteA2AAgent`; the server is `to_a2a`, not
    `A2AServer`; `AgentCard` comes from `a2a.types`.
  - Firestore and Redis services moved to `google.adk.integrations.*`;
    `SpannerSessionService` does not exist.
  - `CalendarToolset` replaces `calendar_tool_set`.
  - `maybe_set_otel_providers` replaces the non-existent `setup_telemetry`.
  - Testing examples used a non-existent `AgentContext` and
    `agent.run(ctx, query=...)`; they now drive `run_async`.
  - The eval section described a bespoke YAML harness. It now documents the
    native `EvalSet` / `test_config.json` / `AgentEvaluator` path.
  - `adk api_server` / `adk web` take the agents directory positionally; the
    documented `--app-dir` flag does not exist.
- `SequentialAgent`, `ParallelAgent`, and `LoopAgent` are documented as
  deprecated in 2.12 (they still run and warn). `LoopAgent` termination is
  `exit_loop`, not a `stop_condition` argument.
- The model-ID baseline in every skill now states that `gemini-3.5-flash`
  redirects to 3.6 and `gemini-3.7-flash` to 3.8; the previous text wrongly
  claimed `gemini-3.8-flash` was a redirect.
- `skills.sh.json`, `CLAUDE.md`, `README.md`, `agents/workflow-builder.md`, and
  `agents/workflow-designer.md` route to the new skill.

### Not added

- `adk-accessibility-agents` is parked: no source-backed ADK material exists
  behind it. The one real slice — Live audio transcription — is already in
  `adk-bidi-live`.

---

## [1.0.2] — 2026-10-19

Patch release.

### Fixed

- `install.sh --ref <tag>` now works on the tarball fallback. The URL used
  `archive/refs/heads/<ref>`, which only resolves branches, so a tag install
  failed on machines without git. It now uses `archive/<ref>`, verified against
  `v1.0.1` and `main`.

---

## [1.0.1] — 2026-10-19

Model-catalog refresh. Content-only; no skill was renamed or removed.

### Changed

- `adk-model-routing` now reflects the catalog verified on 2026-10-19:
  `gemini-4-argon` (GA 2026-10-13) as the frontier tier, `gemini-3.8-flash` as
  the default, `gemini-3.6-flash` as the previous Flash, `gemini-3.5-flash-lite`
  as the cost tier, and `gemini-3.8-live` /
  `gemini-3.8-live-extended-thinking` on the Live API.
- `gemini-3.5-flash` and `gemini-3.7-flash` are documented as redirecting
  endpoints (to 3.6 and 3.8), not as current models.
- `adk-bidi-live` and every `references/adk-2x-baseline.md` now name
  `gemini-3.8-live` instead of the retiring
  `gemini-3.1-flash-live-preview` (shutdown 2026-11-17).
- `adk-bidi-live` gains `references/gemini-3.8-live.md`: 131k input / 65k
  output, audio-only response with transcription, no `thinking_level` or
  `thinking_config` (use `gemini-3.8-live-extended-thinking` instead),
  asynchronous function calling by default, `turn_complete=true` interrupts
  generation, proactive audio permanently on, affective dialogue removed, and
  all video frames sent by default.
- `adk-model-routing` states the same Live constraint instead of implying a
  thinking flag works in streaming.
- Example code across all skills pins `gemini-3.8-flash` instead of
  `gemini-3.5-flash`.
- `references/model-cache.json` regenerated: 54 models, 31 active, 15
  deprecated, 8 blocked.
- `COMPATIBILITY.md` replacement table extended with Live, TTS, Image, and Veo
  shutdowns and the two redirecting IDs.
- `SOURCES.md` records the models and deprecations pages as first-class sources.

### Fixed

- `fetch_models.py` rewritten. The previous version classified any model
  mentioned on the deprecations page as deprecated (marking `gemini-3.8-live`
  deprecated), missed Argon and the 3.8 family entirely, and emitted page slugs
  as model IDs. It now parses model cards, endpoint tables, and deprecation
  rows, and exits 2 instead of writing a cache when the page structure changes.

---

## [1.0.0] — 2026-10-19

The restructure release. The taxonomy changed, so routing tables, subsets, and
cached installs must be updated.

### Added

- `adk-skills-authoring` — the ADK skills subsystem: `Skill`, `Frontmatter`,
  `Resources`, `Script`, the loader, `SkillRegistry`, and `SkillToolset` with
  eager/lazy discovery and the two lifecycle switches.
- `adk-graph-workflows`, `adk-agent-architecture`, and `adk-deploy-production`
  — the three-way split of the former 844K `adk-agentic-prod-workflows`.
- `adk-typescript-go-parity` — the only Go/TypeScript surface, carrying the
  templates and parity notes.
- `adk-agent-personas` — `adk-persona` merged with `adk-domain-expert`.
- `adk-agent-orchestration` — `adk-autonomous-agent` merged with
  `adk-langgraph`, keeping LangGraph's context7-first documentation discipline.
- `contributing/` — 8 contributor-only skills ported from
  `google/adk-python@v2.12.0`, with provenance headers. Not installed by
  default; opt in with `install.sh --with-contributing`.
- `scripts/validate_skills.py` — the repo-owned contract validator, with 36
  tests. CI runs it with `--strict` over `skills/`.
- `SOURCES.md`, `COMPATIBILITY.md`, and this changelog.
- `compatibility: google-adk>=2.9.2,<3` on every skill.

### Changed

- Every description now carries a positive trigger and a negative trigger that
  names the sibling skill owning the excluded case.
- `skills.sh.json`, the `CLAUDE.md` router table, the README table, the
  subagents, and the commands all follow the new taxonomy. Tests fail if any of
  those surfaces drifts from the filesystem.
- `adk-agent-builder`, `adk-architecture`, and `adk-debug` were reconciled onto
  the upstream `v2.12.0` base. `adk-debug`'s long symptom catalogue moved into
  `references/`.
- The Claude plugin is a supported install channel, not experimental.
- `adk-migration` now targets the 2.12.0 range instead of 2.3.
- Every skill is self-contained: no skill reads `../../docs/`.

### Removed

- `adk-agentic-prod-workflows` — superseded by the three split skills plus the
  parity skill.
- `adk-persona`, `adk-domain-expert`, `adk-autonomous-agent`, `adk-langgraph` —
  merged into `adk-agent-personas` and `adk-agent-orchestration`.
- `adk-git`, `adk-setup`, `adk-style`, `adk-sample-creator` from `skills/` —
  moved to `contributing/`.
- `bin/cli.js` and `package.json` — the npm wrapper was never published under
  either name, and its documented command returned 404.
- 77 broken relative links and 3 dead image references that predated the
  restructure.

### Fixed

- `README.md` no longer calls the installer "the skills.sh CLI" and no longer
  claims an unverified skills.sh listing effect.
- The 14 removed or renamed skills no longer appear in routing tables,
  subagents, or commands.

---

## [0.1.0] — 2026-10-14

Baseline release, commit `5275610`.

### Changed

- Purged 196 MB of vendored and generated material; repository working tree
  370 MB → 4.5 MB, `.git` 171 MB → 1.7 MB.
- Retired vestigial formats and aligned the library on ADK 2.9.2–2.12.0.
- Rewrote CI with the ADK version × Python matrix.

### Known issues at this tag

- CI red: it required `compatibility` on every skill and no skill had it.
- 13 skills read `../../docs/python-adk-2.md`, so they could not be installed
  standalone.
- `adk-agentic-prod-workflows` was 92 files and ~90% of all skill bytes.
- The skills subsystem had no coverage at all.
