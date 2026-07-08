---
description: Scan the repo for lingering ADK v1 patterns and v2.3 API-name drift
allowed-tools: Read, Bash, Grep
---

Scan this repository for leftover ADK v1 references and known v2.3 API-name drift, then report every offender with `file:line`.

Use Context7 `/google/adk-docs` and the official ADK docs/API reference as the canonical source. `adk-python-v2.3/` may exist as a gitignored local source mirror; `adk-python-v1/` is legacy helper tooling. New code must import from `google.adk.*` (installed via `google-adk>=2.3.0,<3`) and must not path-import either local folder.

Run the deterministic scan (exclude local ADK source/helper trees themselves):

```bash
EXCL='--exclude-dir=adk-python-v2.3 --exclude-dir=adk-python-v1 --exclude-dir=.git --exclude-dir=node_modules'

echo "== bare adk-python/ path refs (should be adk-python-v1/ or adk-python-v2.3/) =="
grep -rn $EXCL -E 'adk-python/([^v]|$)' . || echo "  clean"

echo "== deprecated v2.3 names =="
grep -rn $EXCL -E 'ctx\.resume_data|@edge\b|from +langgraph +import' . || echo "  clean"

echo "== non-google.adk ADK imports in runtime code =="
grep -rn $EXCL -E 'from +adk[_-]python|import +adk[_-]python' agents adk-runtime adk_bidi skills 2>/dev/null || echo "  clean"

echo "== standalone Task class misuse (2.3 uses mode='task' + TaskRequest/TaskResult/FinishTaskTool) =="
grep -rn $EXCL -E 'import +Task\b|[^a-zA-Z_]Task\(' skills commands docs 2>/dev/null | grep -vE 'TaskRequest|TaskResult|FinishTask|task_' || echo "  clean"

echo "== python version drift (2.3 requires 3.10+) =="
grep -rn $EXCL -E 'Python 3\.11|>=3\.11|3\.11\+' . || echo "  clean"
```

For each hit: quote the line, say which v2.3 symbol/path it should become (see `CLAUDE.md` → "v2.3 Core Concepts"), and whether Context7 or the local source mirror confirms the fix. Anything unverifiable → flag `NEEDS VERIFICATION`, do not guess.
