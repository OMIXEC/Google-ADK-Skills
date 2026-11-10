# ADK 2.14 agent (Context7)

Reviewed against the google/adk-python v2.14.0 tag and an isolated google-adk==2.14.0 install; this is selected API coverage, not full skill-pack validation. LlmAgent.global_instruction is deprecated; put global instructions in GlobalInstructionPlugin on the enclosing App. Pass that App to Runner(app=...). The legacy runner constructor remains for compatibility but has looser validation.

Sources: https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/agents/llm_agent.py ; https://github.com/google/adk-python/blob/v2.14.0/src/google/adk/runners.py
