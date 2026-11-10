# ADK 2.14 architecture (Context7)

Reviewed against the google/adk-python v2.14.0 tag and an isolated google-adk==2.14.0 install; this is selected API coverage, not full skill-pack validation. ADK moves cross-cutting concerns toward App: register plugins there and pass App to Runner. LlmAgent.global_instruction is deprecated in favor of GlobalInstructionPlugin. Keep agent-local instructions on agents and global policy in the App plugin.

Sources: https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/runners.py ; https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/agents/llm_agent.py
