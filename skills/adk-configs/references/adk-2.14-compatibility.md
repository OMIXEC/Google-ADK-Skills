# ADK 2.14 configuration (Context7)

Reviewed against the google/adk-python v2.14.0 tag and an isolated google-adk==2.14.0 install; this is selected API coverage, not full skill-pack validation. Put cross-agent plugins on App(plugins=[...]) and pass app=app to Runner. Runner(plugins=...) is deprecated. Replace LlmAgent.global_instruction with GlobalInstructionPlugin on App; keep agent-specific instructions on each agent.

Sources: https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/runners.py ; https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/agents/llm_agent.py
