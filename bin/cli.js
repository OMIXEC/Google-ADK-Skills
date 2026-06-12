#!/usr/bin/env node
// Thin shim: exec install.sh with any passed-through flags so `npx
// google-adk-skills [--target ...] [--copy] ...` works. Node is not a runtime
// dependency of the skills — this only shells out to the bash installer.

const { spawnSync } = require("node:child_process");
const path = require("node:path");
const fs = require("node:fs");

const repoRoot = path.resolve(__dirname, "..");
const installer = path.join(repoRoot, "install.sh");

if (!fs.existsSync(installer)) {
  console.error(`install.sh not found at ${installer}`);
  process.exit(1);
}

const args = process.argv.slice(2);
const result = spawnSync("bash", [installer, ...args], {
  stdio: "inherit",
  cwd: repoRoot,
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}
process.exit(result.status === null ? 1 : result.status);
