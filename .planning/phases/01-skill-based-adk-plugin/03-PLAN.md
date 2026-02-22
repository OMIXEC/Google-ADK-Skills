---
wave: 2
depends_on: [01-PLAN.md]
files_modified:
  - skills/adk-tool-builder/SKILL.md
  - skills/adk-callback-patterns/SKILL.md
  - skills/adk-session-management/SKILL.md
autonomous: false
requirements: [adk-tools, adk-callbacks, adk-sessions]
---

# Plan 03: Create Advanced ADK Component Skills

## Objective
Add skills for advanced ADK components: custom tool creation, callback patterns, and session management based on Context7 ADK documentation.

## must_haves
- [ ] FunctionTool creation patterns (Python, TypeScript, Java)
- [ ] Callback system for agent behavior customization
- [ ] Session and memory service patterns
- [ ] AgentTool for agent composition

## Tasks

<task id="3.1" type="create">
<title>Create Tool Builder Skill</title>
<description>
Comprehensive skill for creating ADK tools:

**Tool Types:**
1. **FunctionTool** - Wrap Python/TS/Java functions
2. **LongRunningFunctionTool** - Async background tasks
3. **AgentTool** - Agent composition and delegation
4. **MCPToolset** - External MCP server integration
5. **GoogleSearchTool** - Built-in web search
6. **VertexAiRagRetrieval** - RAG retrieval tool

**Schema Patterns:**
- Type hints for automatic schema generation
- @Schema annotations (Java)
- Zod schema validation (TypeScript)
- Return type requirements (must return dict/Map/object)

**Code Examples:**
```python
from google.adk.tools import FunctionTool

def get_weather(city: str) -> dict:
    """Get weather for a city.

    Args:
        city: The city name to get weather for.

    Returns:
        Weather information dictionary.
    """
    return {"city": city, "temp": 72, "condition": "sunny"}

weather_tool = FunctionTool(get_weather)
```
</description>
<files>
- skills/adk-tool-builder/SKILL.md
- skills/adk-tool-builder/references/tool-types.md
- skills/adk-tool-builder/examples/function-tools.md
- skills/adk-tool-builder/examples/mcp-tools.md
</files>
</task>

<task id="3.2" type="create">
<title>Create Callback Patterns Skill</title>
<description>
Skill for ADK callback system:

**Callback Types:**
1. **before_model_callback** - Pre-LLM processing
2. **after_model_callback** - Post-LLM processing
3. **before_tool_callback** - Pre-tool execution
4. **after_tool_callback** - Post-tool execution

**Use Cases:**
- Logging and monitoring
- Input/output transformation
- Safety guardrails
- Cost tracking
- Custom routing logic

**Code Example:**
```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

def log_callback(ctx: CallbackContext, request: types.GenerateContentRequest):
    print(f"Request to model: {request}")
    return None  # Continue normal flow

agent = LlmAgent(
    name="agent_with_callbacks",
    model="gemini-2.5-flash",
    before_model_callback=log_callback,
)
```
</description>
<files>
- skills/adk-callback-patterns/SKILL.md
- skills/adk-callback-patterns/references/callback-types.md
- skills/adk-callback-patterns/examples/logging-callbacks.md
- skills/adk-callback-patterns/examples/guardrail-callbacks.md
</files>
</task>

<task id="3.3" type="create">
<title>Create Session Management Skill</title>
<description>
Skill for ADK session and memory services:

**Session Services:**
1. **InMemorySessionService** - Development/testing
2. **DatabaseSessionService** - Production persistence
3. **VertexAiSessionService** - Vertex AI managed

**Memory Services:**
1. **InMemoryMemoryService** - Short-term memory
2. **VertexAiMemoryBankService** - Managed long-term memory

**State Management:**
- Session state persistence
- Cross-turn context
- Multi-agent shared state
- Memory search and retrieval

**Code Example:**
```python
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner

session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

runner = Runner(
    agent=my_agent,
    app_name="my_app",
    session_service=session_service,
    memory_service=memory_service,
)
```
</description>
<files>
- skills/adk-session-management/SKILL.md
- skills/adk-session-management/references/session-types.md
- skills/adk-session-management/references/memory-services.md
- skills/adk-session-management/examples/persistent-sessions.md
</files>
</task>

## Verification Criteria
- [ ] Tool builder skill covers all ADK tool types
- [ ] Callback patterns match ADK documentation
- [ ] Session management includes all service types
- [ ] Examples are correct and follow ADK patterns

## Acceptance
Advanced component skills enable sophisticated agent customization.
