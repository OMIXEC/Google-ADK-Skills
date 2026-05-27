---
name: template-loop-python
description: Iterative refinement using LoopAgent. Python. Generate → critique → improve → repeat until quality gate passes.
---

# Loop Template (Python)

Iterative refinement workflow where sub-agents loop until a quality gate passes or max iterations reached. Uses `LoopAgent` from ADK.

## When to Use

- Content generation with quality improvement
- Code generation with test-driven refinement
- RAG with query refinement loops
- Any workflow where output quality improves through iteration
