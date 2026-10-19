# Compatibility

What this library supports, and what it deliberately does not.

## Version matrix

The library floor is **`google-adk>=2.9.2,<3`**. Every skill declares that range
in `compatibility`.

| ADK Python | Released | `requires_python` | Supported here | Notes |
|---|---|---|---|---|
| 2.9.2 | 2026-09-18 | `>=3.10` | **floor** | Telemetry-only change from 2.9.1 |
| 2.10.0 | 2026-09-25 | `>=3.10` | Yes | Skills lifecycle (EPHEMERAL, unload, max active), MongoDB toolset, eval metrics |
| 2.11.0 | 2026-10-02 | `>=3.10` | Yes | |
| 2.12.0 | 2026-10-13 | `>=3.11` | **validated target** | Python 3.10 dropped; constraints files cover 3.11–3.15 |
| 1.39.1 | 2026-08-27 | — | **migration source only** | 1.x still ships in parallel |

### Python

| ADK | Python 3.10 | 3.11 | 3.12 | 3.13 | 3.14 | 3.15 |
|---|---|---|---|---|---|---|
| 2.9.2 – 2.11.0 | Yes | Yes | Yes | Yes | Yes | Yes |
| 2.12.0 | **No** | Yes | Yes | Yes | Yes | Yes |

Do not run 2.12.0 on Python 3.10; the package refuses to install.

CI runs the matrix in `.github/workflows/adk-skills-ci.yml`.

## Non-Python runtimes

`adk-typescript-go-parity` carries templates for the independent runtime lines.
Their version numbers do **not** track the Python one.

| Runtime | Package | Current | Meaning |
|---|---|---|---|
| Python | `google-adk` | 2.12.0 | Primary target of this library |
| TypeScript | `@google/adk` | 2.3.0 | Templates only; verify signatures against the installed package |
| Go | `google.golang.org/adk` | v1.9.0 | Templates only; verify signatures against the installed package |

## 1.x in parallel

ADK 1.x is still shipping (1.39.1). This library's guidance targets 2.x, and
the only 1.x material it carries is the migration path.

- Sessions written by 2.x are readable by 1.28+ with extra fields ignored.
- Sessions from older 1.x are **not** readable by 2.x.
- Do not reuse persisted 1.x session or state data after upgrading.
- `adk-migration` is the entry point; it covers the breaking API changes
  through 2.12.0.

## Deprecation table

### APIs and parameters

| Retired | Replacement | Skill |
|---|---|---|
| `GraphAgent` and pre-2.x graph imports | `Workflow` (or a verified compatibility API) | `adk-migration` |
| `MCPToolset` | `McpToolset` | `adk-migration`, `adk-mcp` |
| `ctx.resume_data` | `ctx.resume_inputs` | `adk-migration`, `adk-architecture` |
| Standalone `Task` class | task mode plus task request/result concepts | `adk-migration` |
| `thinking_budget` | `thinking_level` (`minimal` / `low` / `medium` / `high`) | `adk-model-routing` |
| `temperature` / `top_p` / `top_k` / `candidate_count` on Gemini 3.x | Omit; control via `thinking_level` | `adk-model-routing` |

### Models

| Retired | Use instead |
|---|---|
| `gemini-2.0-flash`, `-001`, `-lite`, `-lite-001` | `gemini-3.6-flash` or `gemini-3.1-flash-lite` |
| `gemini-3-pro-preview` | `gemini-3.1-pro-preview` |
| `gemini-3.1-flash-lite-preview` | `gemini-3.1-flash-lite` |
| `gemini-2.0-flash-live-001`, `gemini-3.1-flash-live-preview`, `gemini-2.5-flash-native-audio-preview-12-2025` | `gemini-3.8-live` |
| `gemini-3.1-flash-tts-preview`, `gemini-2.5-*-preview-tts` | `gemini-3.8-flash-tts` |
| `text-embedding-004`, `embedding-001`, `gemini-embedding-001` | `gemini-embedding-2` |
| `imagen-4.0-*` | `gemini-nano-banana-2.1` |
| `veo-3.1-*-preview` | `gemini-omni-1.1-flash` |

Redirecting endpoints still answer but do not run the model you named:
`gemini-3.5-flash` → `gemini-3.6-flash`, `gemini-3.7-flash` →
`gemini-3.8-flash`.

Shutdown dates that are close enough to plan around: Live and TTS previews
**2026-11-17**, Veo 3.1 previews **2026-10-22**, `gemini-3.1-flash-lite`
**2027-05-07**.

Retired IDs are rejected by the repository tests
(`TestV23MigrationGuards.test_no_blocked_model_ids_in_assignments`).

### Harness fields that ADK ignores

| Field | Reality |
|---|---|
| `disable-model-invocation` | Claude Code field. ADK parses unknown frontmatter keys and ignores this one. |
| `compatibility` | Parsed, capped at 500 chars, and **inert** at runtime. It documents; it does not gate. |

## What this library does not support

- ADK 2.8.x and earlier.
- Python 3.9 and earlier.
- 1.x as a target for new work. Migration guidance only.
- Vendoring `google-adk` or any runtime SDK into this repository.

## Reporting a compatibility problem

Open an issue with the ADK version, the Python or runtime version, the skill
name, and the exact error. If a claim in a skill disagrees with the pinned
source in [`SOURCES.md`](SOURCES.md), the source wins.
