# Prototype — `adk-recipes` and the four-way merge

Throwaway artifact for [#4](https://github.com/OMIXEC/Google-ADK-Skills/issues/4). **Never merged.** Delete when the shape is settled.

Candidates: `adk-persona` + `adk-domain-expert` + `adk-autonomous-agent` + `adk-langgraph` → one `adk-recipes`.

Ticket's test: *can a reader tell from the frontmatter description alone when to load it, and is there one coherent job — or is this actually two skills, or none?*

---

## Attempt 1 — the literal four-way merge (what the plan asks for)

```yaml
name: adk-recipes
description: >-
  Ready-made ADK agent recipes: instantiate a stock persona, generate a bespoke
  domain expert, build an autonomous OODA-loop agent, or orchestrate a LangGraph
  state machine. Use when you want a pre-built agent shape rather than a
  from-scratch build.
```

```
# adk-recipes
## Choose a recipe          ← 4-row routing table
## Route A — stock persona            → references/persona-templates.md          (830 lines)
## Route B — bespoke domain expert    → references/domain-expert-generator.md   (593 lines)
## Route C — autonomous OODA agent    → references/autonomous-agents.md         (482 lines)
## Route D — LangGraph state machine  → references/langgraph-orchestration.md   (905 lines)
## NEVER                   ← union of four NEVER lists
```

### Verdict: **fails the test.** Three independent reasons

1. **The description is a disjunction of four unrelated triggers.** It cannot state *when* to load, because the honest answer is "when you want any of four unrelated things". Compare the originals — each names a **situation**:

   | Skill | Trigger it actually owns |
   |---|---|
   | `adk-persona` | "a ready-made character/role agent (e.g. tutor, coach, analyst, support rep)" |
   | `adk-domain-expert` | "a bespoke specialist with **no matching persona template**" |
   | `adk-autonomous-agent` | "runs **without per-step human follow-up**, plans its own steps" |
   | `adk-langgraph` | "mentions **LangGraph**" |

   No two of these overlap. A merged description must either enumerate them (à la above — unreadable) or abstract them into something that helps nobody.

2. **`recipes` is a name for a grab-bag.** It makes the merge *legible* rather than *testing* it. A name that fits any four things describes none of them.

3. **It defeats the L1/L2 split it is supposed to exploit.** L1 frontmatter is the only thing seen every turn; L2 body loads on trigger. One name covering four jobs forces the L1 description to summarize four jobs — the one thing it cannot do — and once triggered on any single axis, **3/4 of the L2 body is irrelevant**. That is exactly the L2 token waste the destination's *lean* leg exists to prevent.

**False friend:** all four originals end with "validate the model (`adk-litellm`)". A shared *tail* is evidence of copy-paste, not of shared purpose.

---

## Attempt 2 — find the real seam

Two of the four already serve one question **and already cross-reference each other by name**:

| Pair | The one question they share | Evidence in source |
|---|---|---|
| `adk-persona` + `adk-domain-expert` | **Who is the agent?** Give it a specialist identity. | `adk-persona`: *"If no template fits, hand off to the `adk-domain-expert` skill instead."* `adk-domain-expert`: *"If the need maps to a stock template, defer to `adk-persona`."* Identical output shape — instruction + tools + interaction style — reached two ways: **catalogue or generate**. |
| `adk-autonomous-agent` + `adk-langgraph` | **How does it run over time?** Control flow past the standard agent types. | `adk-langgraph`: *"For simple linear/parallel/loop pipelines, prefer native ADK … don't add LangGraph weight."* Both answer *"my flow is not linear."* |

**Across the seam there is no shared question.** Identity is not control flow. So the four-way merge is two distinct questions wearing one label — and the label seats them at the same table only because a meta-prompt listed them together.

### Proposed shape

#### `adk-agent-personas` — persona + domain-expert

```yaml
name: adk-agent-personas
description: >-
  Give an ADK agent a specialist identity: instantiate one of 30+ stock persona
  templates (tutor, coach, analyst, support rep, creative role) or generate a
  bespoke domain expert when no template fits — scope, expertise depth,
  interaction style, and knowledge sources included. Use when the question is who
  the agent should be, not how it is built. For multi-agent composition use
  adk-agents; for orchestration topology use adk-agent-orchestration.
```

```
# adk-agent-personas
## Process   1. match the request against the catalogue
             2. no match → generate bespoke (same output contract)
             3. customise instruction / tools / interaction style
             4. wire knowledge via adk-rag if a corpus is involved
## NEVER     no blocked models · never strip a persona's scope guardrails
```
`references/`: `persona-templates.md` (830) + `domain-expert-generator.md` (593) — **one decision, two branches**.

#### `adk-agent-orchestration` — autonomous + langgraph

```yaml
name: adk-agent-orchestration
description: >-
  Choose and implement an ADK agent's control flow when a plain
  sequential/parallel/loop pipeline is not enough: a self-directed OODA loop with
  planning, progress, and stop conditions, or an explicit LangGraph state machine
  with conditional edges driving ADK tools as nodes. Use when the flow is cyclic,
  branching, or goal-directed. For simple pipelines use adk-agents.
```

```
# adk-agent-orchestration
## Pick the topology    self-directed loop  vs  inspectable state machine
## Route A — self-directed (OODA)   → references/autonomous-agents.md       (482)
## Route B — explicit state machine → references/langgraph-orchestration.md (905)
## NEVER    no unbounded loop (always max-iterations + stop condition) ·
            no graph without a terminal edge · no irreversible external action
            without an approval gate
```
`references/`: `autonomous-agents.md` (482) + `langgraph-orchestration.md` (905).

> **Carry over, do not lose:** `adk-langgraph` is the only skill here with an **external doc dependency** — context7-first, bundled reference as fallback. That is a real discipline (LangGraph moves fast), not decoration. It must survive the merge.

---

## Honest alternative — do not merge at all

The seam above is real, but it is also **mild**, and one fact cuts against merging:

> **These four are already lean.** SKILL.md bodies are 22–43 lines. The destination's *lean* leg targets the **L2 token budget**, and these are nowhere near it — unlike the 840K monster, which is the actual leanness problem.

So merging buys **only** what coherence buys. That is enough for the persona/domain-expert pair (they are one job already, with explicit hand-offs). It is weaker for autonomous/langgraph, which are *adjacent* rather than *the same*: one is an in-ADK pattern, the other is third-party framework interop.

**Minimum-risk variant:** merge only `adk-persona` + `adk-domain-expert`; leave `adk-autonomous-agent` and `adk-langgraph` alone.

### Ledger

| Shape | SKILL.md lines | reference lines | refs |
|---|---|---|---|
| four separate (today) | 112 total | 2810 | 4 |
| `adk-recipes` (four-way) | ~60 | 2810 | 4 |
| **`adk-agent-personas` + `adk-agent-orchestration`** | ~35 + ~45 | 1423 + 1387 | 2 + 2 |
| `adk-agent-personas` only (minimum-risk) | ~35 | 1423 | 2 |

---

## What to decide

1. **Two-skill split (recommended)** — `adk-agent-personas` + `adk-agent-orchestration`.
2. **Minimum-risk** — merge only persona + domain-expert → `adk-agent-personas`; keep `adk-autonomous-agent` and `adk-langgraph` as they are (3 skills, not 1).
3. **Keep all four** — drop the `adk-recipes` merge from the taxonomy entirely.
4. Something else.

**Whatever wins, the name `adk-recipes` dies.** It is the name the merge was invented for, and it is the tell that it was invented.
