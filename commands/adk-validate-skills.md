---
description: Validate ADK skills, commands, agents, package metadata, and installer behavior
allowed-tools: Read, Bash, Grep
---

Validate this Google ADK skills repository before release or push.

Run the local deterministic checks:

```bash
bash -n install.sh
node -e "JSON.parse(require('fs').readFileSync('package.json','utf8')); JSON.parse(require('fs').readFileSync('skills.sh.json','utf8'))"
npm pack --dry-run --cache /private/tmp/google-adk-npm-cache
```

Then run a temporary install without mutating the user's real home directory:

```bash
HOME=/private/tmp/google-adk-validate-home bash install.sh --target codex --copy --install-dir /private/tmp/google-adk-validate-install --force --skills adk-tools
```

Report failures with exact command output and the file that needs correction.
