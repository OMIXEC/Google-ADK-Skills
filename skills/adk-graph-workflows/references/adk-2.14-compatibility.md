# ADK 2.14 workflows (Context7)

Reviewed against the google/adk-python v2.14.0 tag and an isolated google-adk==2.14.0 install; this is selected API coverage, not full skill-pack validation. SequentialAgent, ParallelAgent, and LoopAgent are deprecated for new compositions; prefer Workflow. Workflow cannot yet be used as an LlmAgent sub-agent. For human review, ADK documents structured RequestInput interrupts with Pydantic response_schema and typed input after resume.

Sources: https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/agents/sequential_agent.py ; https://github.com/google/adk-python/tree/main/contributing/samples/workflows/request_input_advanced
