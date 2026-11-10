# ADK 2.14 tools (Context7)

Reviewed against the google/adk-python v2.14.0 tag and an isolated google-adk==2.14.0 install; this is selected API coverage, not full skill-pack validation. ADK documents LongRunningFunctionTool for work that remains pending during human approval; enforce approval at the application dispatch/tool boundary, not in model instructions alone. Use before_tool_callback for argument-sensitive allowlisting when a tool filter cannot inspect call arguments.

Sources: https://github.com/google/adk-python/tree/main/docs/guides/tools/long_running_tool ; https://github.com/google/adk-python/tree/main/docs/guides/integrations/mongodb/mongodb_toolset
