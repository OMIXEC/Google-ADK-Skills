# ADK 2.14 composition (Context7)

Reviewed against the google/adk-python v2.14.0 tag and an isolated google-adk==2.14.0 install; this is selected API coverage, not full skill-pack validation. SequentialAgent, ParallelAgent, and LoopAgent are deprecated in favor of Workflow. Preserve existing compositions during migration but prefer Workflow for new orchestration. Workflow cannot yet be nested as an LlmAgent sub-agent.

Source: https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/agents/sequential_agent.py
