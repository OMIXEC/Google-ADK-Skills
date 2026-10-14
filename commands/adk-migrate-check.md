---
description: Scan the repo for lingering ADK v1 patterns and stale 2.x API-name drift
allowed-tools: Read, Bash, Grep
---

Scan this repository for leftover ADK v1 references and known 2.x API-name drift, then report every offender with `file:line`.

Canonical sources are Context7 `/google/adk-docs`, the installed `google.adk` package, and `google/adk-python` at the matching tag. New code imports from `google.adk.*` (installed via `google-adk>=2.9.2,<3`) and must never path-import a vendored SDK checkout.

Run the deterministic scan:

```bash
EXCL='--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__'

echo "== vendored SDK path refs (should be none) =="
grep -rn $EXCL -E 'adk-python(-v?[0-9.]+)?/' . || echo "  clean"

echo "== stale / deprecated 2.x names =="
grep -rn $EXCL -E 'ctx\.resume_data|@edge\b|MCPToolset' . || echo "  clean"

echo "== non-google.adk ADK imports =="
grep -rn $EXCL -E 'from +adk[_-]python|import +adk[_-]python' agents examples skills 2>/dev/null || echo "  clean"

echo "== standalone Task class misuse (2.x uses mode='task' + TaskRequest/TaskResult/FinishTaskTool) =="
grep -rn $EXCL -E 'import +Task\b|[^a-zA-Z_]Task\(' skills commands docs 2>/dev/null | grep -vE 'TaskRequest|TaskResult|FinishTask|task_' || echo "  clean"

echo "== retired Gemini models assigned in examples =="
grep -rn $EXCL -E "(model\s*[:=]\s*|\.model\(\s*)['\"](gemini-2\.0-|gemini-1\.5-|gemini-1\.0-|gemini-3-pro-preview|gemini-2\.5-pro|gemini-2\.5-flash)" skills examples 2>/dev/null || echo "  clean"

echo "== python floor drift (2.9.2-2.11.0 need 3.10+; 2.12.0 needs 3.11+) =="
grep -rn $EXCL -E 'Python 3\.11\+|requires-python.*3\.1[12]' CLAUDE.md README.md MIGRATION.md .github 2>/dev/null || echo "  clean"
```

For each hit: quote the line, say which 2.x symbol/path it should become (see `CLAUDE.md` → "2.x Core Concepts"), and whether Context7 or the installed package confirms the fix. Anything unverifiable → flag `NEEDS VERIFICATION`, do not guess.
