---
name: template-sequential-python
description: Linear pipeline using SequentialAgent. Python. Use for fixed-order processing chains.
---

# Sequential Template (Python)

Linear pipeline where each sub-agent processes output from the previous. Uses `SequentialAgent` from ADK.

## When to Use

- Fixed-order processing chains
- ETL pipelines (extract → transform → load)
- Validation → Enrichment → Approval flows
- Any workflow where step N+1 always follows step N
