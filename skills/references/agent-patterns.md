# ADK Agent Architecture Patterns

Comprehensive reference for Google ADK agent architecture patterns, capabilities, and implementation strategies.

## Agent Types

### 1. Agent (Basic Agent)

Simple single-agent pattern for focused tasks.

```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

agent = Agent(
    name="agent_name",
    model="gemini-2.5-flash",
    description="Agent description for routing",
    instruction="Detailed agent instructions...",
    tools=[FunctionTool(function_name)],
)
```

**Use when:**
- Single domain expertise needed
- Simple tool coordination required
- No multi-step reasoning across specialists

### 2. Multi-Agent with AgentTool Delegation

Supervisor coordinates specialist agents using AgentTool.

```python
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

# Specialist agents
specialist_1 = Agent(name="specialist_1", ...)
specialist_2 = Agent(name="specialist_2", ...)

# Supervisor agent
supervisor = Agent(
    name="supervisor",
    model="gemini-2.5-flash",
    description="Coordinates specialist agents",
    instruction="Delegate tasks to specialists based on requirements",
    tools=[
        AgentTool(agent=specialist_1),
        AgentTool(agent=specialist_2),
    ],
)
```

**Use when:**
- Task requires multiple specialized capabilities
- Clear delegation boundaries exist
- Specialists can work independently

### 3. Sequential Multi-Agent Pipeline

Chain agents for step-by-step processing.

```python
from google.adk.agents import SequentialAgent

pipeline = SequentialAgent(
    agents=[intake_agent, process_agent, validate_agent, output_agent],
    name="pipeline",
)
```

**Use when:**
- Linear workflow with distinct stages
- Each stage produces input for the next
- Order matters (intake → process → validate → output)

### 4. LangGraph Stateful Workflows

Complex workflows with state management and conditional routing.

```python
from langgraph.graph import StateGraph
from google.adk.agents import Agent

workflow = StateGraph(state_schema)
workflow.add_node("researcher", researcher_agent)
workflow.add_node("analyst", analyst_agent)
workflow.add_conditional_edges("researcher", route_function)
workflow.compile()
```

**Use when:**
- Complex conditional logic required
- State persistence needed across steps
- Human-in-the-loop approvals
- Parallel execution with merge points

## Capability Patterns

### Voice/Audio Integration

```python
# Native audio model
agent = Agent(
    name="voice_agent",
    model="gemini-live-2.5-flash-native-audio",
    description="Voice-enabled agent",
    instruction="Respond naturally in conversation...",
)
```

### Vision Integration

```python
# Vision-enabled agent
agent = Agent(
    name="vision_agent",
    model="gemini-2.5-flash",  # Vision-enabled by default
    description="Analyzes images and visual content",
    instruction="When analyzing images, describe spatial relationships...",
    tools=[FunctionTool(process_image), FunctionTool(detect_objects)],
)
```

### RAG (Retrieval-Augmented Generation)

#### Vertex AI RAG

```python
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai import rag

agent = Agent(
    name="rag_agent",
    model="gemini-2.5-flash",
    description="Knowledge-powered agent with RAG",
    instruction="Always search knowledge base before answering...",
    tools=[
        VertexAiRagRetrieval(
            name="search_knowledge",
            description="Search knowledge base",
            rag_resources=[
                rag.RagResource(rag_corpus="projects/123/corpora/456")
            ],
            similarity_top_k=10,
            vector_distance_threshold=0.3,
        ),
    ],
)
```

#### Pinecone RAG

```python
from pinecone import Pinecone
from google.adk.tools import FunctionTool

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("knowledge-base")

def search_knowledge(query: str, top_k: int = 10) -> list:
    """Search knowledge base using Pinecone."""
    # Generate query embedding
    embedding = generate_embedding(query)

    # Search Pinecone
    results = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True,
    )
    return results['matches']

agent = Agent(
    name="pinecone_rag_agent",
    model="gemini-2.5-flash",
    tools=[FunctionTool(search_knowledge)],
)
```

### MCP Tool Integration

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Database MCP
database_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='uvx',
            args=["mcp-server-sqlite", "--db-path", "data/app.db"],
        ),
    ),
)

# Web Search MCP
search_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@anthropic/mcp-server-brave-search"],
            env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")},
        ),
    ),
)

agent = Agent(
    name="mcp_agent",
    model="gemini-2.5-flash",
    tools=[database_toolset, search_toolset],
)
```

## Instruction Patterns

### Role-Based Instructions

```python
instruction = """
You are a [ROLE] specializing in [DOMAIN].

**Role:** [What you do]
**Expertise:** [Your capabilities]
**Communication Style:** [How you interact]

**Behavior Guidelines:**
1. [Guideline 1]
2. [Guideline 2]
3. [Guideline 3]

**Tool Usage:**
- [tool_name]: When to use
"""
```

### Domain Expert Instructions

```python
instruction = """
You are a domain expert in [DOMAIN].

**Expertise Level:** [beginner|intermediate|advanced|expert]

**Core Competencies:**
- [Competency 1]
- [Competency 2]

**Interaction Style:** [formal|casual|socratic|technical]

**Safety Protocols:**
[Domain-specific safety guidelines]

**Response Format:**
[Expected response structure]
"""
```

### Multi-Agent Coordinator Instructions

```python
instruction = """
You are a coordinator managing a team of specialist agents.

**Team Members:**
- specialist_1: [What they do]
- specialist_2: [What they do]

**Delegation Strategy:**
1. Analyze user request for required capabilities
2. Delegate to appropriate specialist(s)
3. Coordinate results if multiple specialists used
4. Synthesize final response

**When to delegate:**
- [Condition 1] → specialist_1
- [Condition 2] → specialist_2

For simple queries you can handle directly, answer without delegation.
"""
```

## Model Selection

| Model | Best For | Capabilities |
|-------|----------|-------------|
| `gemini-2.5-flash` | General purpose, fast responses | Text, vision, function calling |
| `gemini-2.5-pro` | Complex reasoning, deep analysis | Advanced reasoning, longer context |
| `gemini-live-2.5-flash-native-audio` | Real-time voice | Speech-to-speech, native audio |
| `gemini-2.0-flash-live-001` | Text + audio streaming | Multimodal streaming |

## Architecture Decision Tree

```
User Requirement
      |
      v
Single domain? ----YES----> Agent (Basic)
      |
      NO
      |
      v
Sequential stages? ----YES----> SequentialAgent
      |
      NO
      |
      v
Complex routing? ----YES----> LangGraph
      |
      NO
      |
      v
Multiple specialists? ----YES----> AgentTool Delegation
```

## Best Practices

### 1. Agent Naming

- Use descriptive snake_case names
- Reflect role/domain: `customer_service_agent`, `researcher`, `analyst`

### 2. Instructions

- Start with role definition
- Include behavior guidelines
- Document available tools
- Specify communication style
- Add safety protocols for regulated domains

### 3. Tool Selection

- Use FunctionTool for custom Python functions
- Use MCPToolset for external integrations
- Use VertexAiRagRetrieval for knowledge bases
- Limit to 5-10 tools per agent (avoid overwhelming the model)

### 4. Error Handling

```python
from google.adk.tools import FunctionTool

def safe_tool_function(param: str) -> dict:
    """Tool with proper error handling."""
    try:
        result = perform_operation(param)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

agent = Agent(
    name="agent",
    tools=[FunctionTool(safe_tool_function)],
)
```

### 5. Testing Agents

```python
# Test agent locally before deployment
from google.adk.runners import Runner

runner = Runner(agent=agent)
response = runner.run(prompt="Test query")
print(response)
```

## Common Patterns

### Pattern: Research + Analysis + Synthesis

```python
researcher = Agent(name="researcher", ...)
analyst = Agent(name="analyst", ...)
synthesizer = Agent(name="synthesizer", ...)

coordinator = Agent(
    name="coordinator",
    tools=[
        AgentTool(agent=researcher),
        AgentTool(agent=analyst),
        AgentTool(agent=synthesizer),
    ],
)
```

### Pattern: Intake + Process + Validate + Output

```python
pipeline = SequentialAgent(
    agents=[intake, process, validate, output],
    name="data_pipeline",
)
```

### Pattern: Voice Agent with Tools

```python
voice_agent = Agent(
    name="voice_assistant",
    model="gemini-live-2.5-flash-native-audio",
    tools=[
        FunctionTool(search_calendar),
        FunctionTool(create_reminder),
        FunctionTool(send_message),
    ],
)
```

## Related Files

- @tool-catalog.md - Function and MCP tool patterns
- @deployment-configs.md - Deployment configurations
- @streaming-patterns.md - Real-time and streaming patterns
