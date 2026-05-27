# adk-multi-agent-orchestrator

**Multi-Agent System Builder for Google ADK**

Create sophisticated multi-agent systems using ADK patterns. Build supervisor-specialist hierarchies, sequential pipelines, parallel execution, and complex agent teams.

## When to Use

Use this skill when:
- Task requires multiple specialized agents
- User needs agent coordination/orchestration
- Complex workflows with delegation
- Parallel processing of subtasks
- Hierarchical agent teams

## Quick Start

```bash
# Supervisor with specialists
/adk-multi-agent-orchestrator --pattern "supervisor" \
  --specialists "researcher,analyst,writer"

# Sequential pipeline
/adk-multi-agent-orchestrator --pattern "sequential" \
  --steps "intake,process,validate,output"

# Parallel execution
/adk-multi-agent-orchestrator --pattern "parallel" \
  --agents "search_agent,rag_agent,calculator_agent"
```

## Parameters

```bash
--pattern "supervisor|sequential|parallel|hierarchical"  # Required
--specialists "[agent1, agent2]"       # For supervisor pattern
--steps "[step1, step2]"               # For sequential pattern
--agents "[agent1, agent2]"            # For parallel pattern
--coordinator "coordinator_name"       # Optional: custom coordinator
```

## Multi-Agent Patterns

### 1. Supervisor Pattern (AgentTool Delegation)

Coordinator delegates to specialists based on task requirements.

```bash
/adk-multi-agent-orchestrator --pattern "supervisor" \
  --specialists "researcher,analyst,synthesizer" \
  --coordinator "research_lead"
```

**Generated Code:**
```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool

# Specialist: Researcher
researcher = Agent(
    name="researcher",
    model="gemini-2.5-flash",
    description="Gathers information from multiple sources",
    instruction="""
    You are a research specialist.
    - Search web and databases for relevant information
    - Gather comprehensive data on topics
    - Cite sources and assess credibility
    - Return structured findings
    """,
    tools=[FunctionTool(web_search), FunctionTool(database_query)],
)

# Specialist: Analyst
analyst = Agent(
    name="analyst",
    model="gemini-2.5-pro",  # Better reasoning
    description="Analyzes data and extracts insights",
    instruction="""
    You are an analysis specialist.
    - Review research findings critically
    - Identify patterns and insights
    - Assess data quality
    - Provide structured analysis
    """,
)

# Specialist: Synthesizer
synthesizer = Agent(
    name="synthesizer",
    model="gemini-2.5-flash",
    description="Creates coherent summaries and reports",
    instruction="""
    You are a synthesis specialist.
    - Combine analysis into coherent narrative
    - Write clear, structured reports
    - Highlight key findings
    """,
)

# Supervisor/Coordinator
research_lead = Agent(
    name="research_lead",
    model="gemini-2.5-flash",
    description="Coordinates research team",
    instruction="""
    You are the research team coordinator.

    **Team:**
    - researcher: Gathers information
    - analyst: Analyzes findings
    - synthesizer: Creates reports

    **Workflow:**
    1. Understand user request
    2. Delegate research to researcher
    3. Send findings to analyst
    4. Have synthesizer create final report
    """,
    tools=[
        AgentTool(agent=researcher),
        AgentTool(agent=analyst),
        AgentTool(agent=synthesizer),
    ],
)

root_agent = research_lead
```

### 2. Sequential Pattern (SequentialAgent)

Agents execute in order, each passing results to next.

```bash
/adk-multi-agent-orchestrator --pattern "sequential" \
  --steps "intake,classify,process,respond"
```

**Generated Code:**
```python
from google.adk.agents import Agent, SequentialAgent

# Step 1: Intake
intake_agent = Agent(
    name="intake",
    model="gemini-2.5-flash",
    description="Receives and validates input",
    instruction="Receive user request and extract key information.",
)

# Step 2: Classify
classify_agent = Agent(
    name="classify",
    model="gemini-2.5-flash",
    description="Classifies request type",
    instruction="Analyze and classify the request type.",
)

# Step 3: Process
process_agent = Agent(
    name="process",
    model="gemini-2.5-pro",
    description="Processes the request",
    instruction="Handle the classified request and generate response.",
)

# Step 4: Respond
respond_agent = Agent(
    name="respond",
    model="gemini-2.5-flash",
    description="Formats final response",
    instruction="Format processed data for user delivery.",
)

# Sequential Pipeline
pipeline = SequentialAgent(
    name="request_pipeline",
    description="Sequential request processing pipeline",
    sub_agents=[intake_agent, classify_agent, process_agent, respond_agent],
)

root_agent = pipeline
```

### 3. Parallel Pattern (Multiple AgentTools)

Multiple agents work simultaneously, results aggregated.

```bash
/adk-multi-agent-orchestrator --pattern "parallel" \
  --agents "web_searcher,rag_searcher,calculator" \
  --aggregator "result_combiner"
```

**Generated Code:**
```python
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

# Parallel Agent 1: Web Search
web_searcher = Agent(
    name="web_searcher",
    model="gemini-2.5-flash",
    description="Searches the web for information",
    instruction="Search the web and return relevant results.",
)

# Parallel Agent 2: RAG Search
rag_searcher = Agent(
    name="rag_searcher",
    model="gemini-2.5-flash",
    description="Searches internal knowledge base",
    instruction="Search the knowledge base for relevant information.",
)

# Parallel Agent 3: Calculator
calculator = Agent(
    name="calculator",
    model="gemini-2.5-flash",
    description="Performs calculations",
    instruction="Perform numerical calculations as needed.",
)

# Aggregator/Coordinator
result_combiner = Agent(
    name="result_combiner",
    model="gemini-2.5-flash",
    description="Combines results from parallel agents",
    instruction="""
    Coordinate parallel information gathering.
    Call multiple agents for comprehensive answers.
    Combine results into coherent response.
    """,
    tools=[
        AgentTool(agent=web_searcher),
        AgentTool(agent=rag_searcher),
        AgentTool(agent=calculator),
    ],
)

root_agent = result_combiner
```

## Generated Project Structure

```
multi-agent-system/
+-- src/
|   +-- agents/
|   |   +-- __init__.py
|   |   +-- coordinator.py      # Main coordinator
|   |   +-- specialists/        # Specialist agents
|   +-- config.py
|   +-- main.py
+-- tests/
+-- deployment/
+-- README.md
```

## Examples

### Example 1: Research Team

```bash
$ /adk-multi-agent-orchestrator --pattern "supervisor" \
  --specialists "web_researcher,academic_researcher,fact_checker"

Multi-Agent System Created

Pattern: Supervisor with AgentTool delegation
Specialists:
- web_researcher: Web search
- academic_researcher: Academic papers
- fact_checker: Verify claims
```

### Example 2: Support Pipeline

```bash
$ /adk-multi-agent-orchestrator --pattern "sequential" \
  --steps "classifier,router,handler,responder"

Sequential Pipeline Created

Steps:
1. classifier: Categorize request
2. router: Route to queue
3. handler: Process request
4. responder: Send response
```

## Related Skills

- **adk-adaptive-agent-generator** - Create individual agents
- **adk-persona-builder** - Create specialist personas
- **adk-mcp-integration** - Add tools to agents

## More Information

See CLAUDE.md for multi-agent architecture patterns.
