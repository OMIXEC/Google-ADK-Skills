---
name: template-parallel-python
description: Fan-out parallelism using ParallelAgent. Python. Use for independent task batches that can run concurrently.
---

# Parallel Template (Python)

Fan-out pattern where multiple sub-agents run concurrently. Uses `ParallelAgent` from ADK.

## When to Use

- Batch processing (N chunks → N workers)
- Independent sub-tasks (no data dependencies)
- Multi-source data fetching
- Load-balanced worker pools
