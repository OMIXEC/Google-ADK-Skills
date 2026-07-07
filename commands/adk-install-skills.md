---
description: Install Google ADK skills into supported agent tools
argument-hint: [target or flags]
allowed-tools: Read, Bash, Grep
---

Help install this Google ADK skill collection using the safest available path.

Prefer the public skills.sh installer:

```bash
npx skills add OMIXEC/Google-ADK-Skills
```

If the user needs custom target paths, selective installs, runtime helpers, user/global scope, or local checkout installation, use this repository's installer:

```bash
bash install.sh --interactive
```

When installing from this repo, explain the available targets: `codex`, `opencode`, `claude`, `cline`, `cursor`, `gemini-cli`, `windsurf`, `.agents`, `all`, `auto`, and custom `--skills-dir`.
Use `--copy` when symlinks are undesirable, `--skills` for selected skills, and `--scope global` only when the user has admin permissions.
