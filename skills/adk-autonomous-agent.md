---
name: adk-autonomous-agent
description: Build self-reasoning autonomous agents with goal-directed execution using OODA loop (Observe, Orient, Decide, Act). Types include research (multi-step queries), task (success-criteria-driven), and custom (proactive behavior). Agents reason about actions, plan multi-step workflows, and adapt based on results. Configure goal, success-criteria, proactivity, max-thoughts.
version: 1.0.0
---

# adk-autonomous-agent

**Self-Reasoning Autonomous Agents for Google ADK**

Build autonomous agents with self-reasoning capabilities, proactive behavior, and goal-directed execution. Implements the OODA loop (Observe, Orient, Decide, Act) with explicit reasoning and planning.

## When to Use

Use this skill when:
- Agent needs self-directed behavior
- Goal-oriented task execution is required
- Agent should reason about its actions
- Proactive behavior without prompts is needed
- Complex multi-step planning is required
- Agent needs to learn and adapt

## Quick Start

```bash
# Research agent with goal
/adk-autonomous-agent --type "research" \
  --goal "Find and summarize latest AI research papers"

# Task execution agent
/adk-autonomous-agent --type "task" \
  --goal "Refactor authentication module" \
  --success-criteria "All tests pass,No security vulnerabilities"

# Custom autonomous agent
/adk-autonomous-agent --type "custom" \
  --goal "Monitor system health and alert on anomalies" \
  --enable-proactivity "true"
```

## Parameters

```bash
--type "research|task|custom"                # Agent type
--goal "Agent's primary goal"                # Required
--success-criteria "[criterion1,criterion2]" # For task type
--enable-proactivity "true|false"            # Proactive behavior
--max-thoughts "50"                          # Reasoning history limit
--model "gemini-live-2.5-flash-native-audio" # Live model
```

## Autonomous Reasoning Loop

The OODA Loop (Observe-Orient-Decide-Act) adapted for AI agents:

```
┌────────────────────────────────────────────────────────┐
│                    OBSERVE                             │
│  - Process all available information                   │
│  - What inputs have been received?                     │
│  - What is the current state?                          │
│  - What do we know from memory?                        │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│                     THINK                              │
│  - Reason about the situation                          │
│  - How does this relate to the goal?                   │
│  - What are the key insights?                          │
│  - What are the constraints?                           │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│                     PLAN                               │
│  - Create or update action plan                        │
│  - What steps move toward the goal?                    │
│  - What is the next logical action?                    │
│  - How to measure progress?                            │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│                      ACT                               │
│  - Execute the plan                                    │
│  - Use available tools                                 │
│  - Delegate to other agents                            │
│  - Record results                                      │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│                    REFLECT                             │
│  - Evaluate outcomes                                   │
│  - Did the action succeed?                             │
│  - What was learned?                                   │
│  - Should approach be adjusted?                        │
└───────────────────────┴────────────────────────────────┘
                        │
                        └──────────────► Loop back to OBSERVE
```

## Core Components

### 1. Autonomous Agent

Base autonomous agent with reasoning capabilities.

```bash
/adk-autonomous-agent --type "custom" \
  --goal "Complete user requests efficiently" \
  --enable-proactivity "true"
```

**Generated Code:**
```python
from adk_bidi import AutonomousAgent
from adk_bidi.memory.persistent_store import InMemoryPersistentStore

# Create autonomous agent
agent = AutonomousAgent(
    name="autonomous_assistant",
    goal="Help users complete their tasks efficiently",
    instruction="Be proactive and explain your reasoning.",
    model="gemini-live-2.5-flash-native-audio",
    max_thoughts=50,
    enable_proactivity=True,
    persistent_memory=InMemoryPersistentStore(),  # Optional long-term memory
)

# Agent has built-in reasoning tools:
# - think(observation, reasoning) -> Records thought
# - create_plan(goal, steps) -> Creates action plan
# - get_current_plan() -> Shows current plan
# - complete_step(result) -> Marks step complete
# - update_progress(progress, notes) -> Updates goal progress
# - recall_long_term(query) -> Recalls from persistent memory
# - store_long_term(content, importance) -> Stores to persistent memory
# - get_reasoning_summary() -> Summarizes recent reasoning
```

### 2. Research Agent

Specialized for information gathering and synthesis.

```bash
/adk-autonomous-agent --type "research" \
  --goal "Find and summarize latest AI research papers"
```

**Generated Code:**
```python
from adk_bidi.agents.autonomous_agent import ResearchAgent

# Create research agent
agent = ResearchAgent(
    name="ai_researcher",
    research_topic="Latest advances in large language models",
    tools=[web_search_tool, arxiv_tool],  # Custom research tools
)

# Agent automatically follows research methodology:
# 1. Define key questions to answer
# 2. Gather information from sources
# 3. Cross-reference and verify facts
# 4. Synthesize findings
# 5. Identify gaps needing more research
```

### 3. Task Agent

Specialized for executing specific tasks with success criteria.

```bash
/adk-autonomous-agent --type "task" \
  --goal "Refactor authentication module" \
  --success-criteria "All tests pass,No security vulnerabilities,Code coverage > 80%"
```

**Generated Code:**
```python
from adk_bidi.agents.autonomous_agent import TaskAgent

# Create task agent with success criteria
agent = TaskAgent(
    name="refactoring_agent",
    task_description="Refactor the authentication module",
    success_criteria=[
        "All tests pass",
        "No security vulnerabilities",
        "Code coverage exceeds 80%",
    ],
    tools=[code_edit_tool, test_runner_tool, security_scanner_tool],
)

# Agent automatically:
# - Breaks task into actionable steps
# - Verifies each step before proceeding
# - Handles errors gracefully
# - Confirms completion against success criteria
```

## Reasoning Tools

### Think Tool

Record reasoning process for transparency.

```python
# Agent uses think() to record observations and reasoning
agent.think(
    observation="User asked about AI trends",
    reasoning="I should search for recent AI news and research papers first, "
              "then synthesize the findings into key trends."
)

# Thoughts are stored in working memory and can be retrieved
summary = agent.get_reasoning_summary()
```

### Planning Tools

Create and manage action plans.

```python
# Create a plan
agent.create_plan(
    goal="Research AI trends and write a report",
    steps=[
        "Search for recent AI news",
        "Find academic papers on key topics",
        "Analyze and identify trends",
        "Write summary report",
        "Review and refine",
    ]
)

# Check current plan status
plan = agent.get_current_plan()
# Output:
# Goal: Research AI trends and write a report
# Status: in_progress
# Progress: 2/5
#   ✓ 1. Search for recent AI news
#   ✓ 2. Find academic papers on key topics
#   ○ 3. Analyze and identify trends
#   · 4. Write summary report
#   · 5. Review and refine

# Mark step complete
agent.complete_step(result="Found 15 relevant papers")

# Update overall progress
agent.update_progress(progress=0.4, notes="Research phase complete")
```

### Memory Tools

Long-term memory for learning.

```python
# Store important information for later
agent.store_long_term(
    content="User prefers detailed technical explanations",
    importance="high",
)

# Recall relevant memories
memories = agent.recall_long_term(
    query="user preferences",
    top_k=5,
)
```

## Full Example: Autonomous Research Assistant

```python
"""Complete autonomous research assistant."""
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.tools import FunctionTool
from adk_bidi import AutonomousAgent
from adk_bidi.memory.persistent_store import PersistentMemoryStore

# Define research tools
def web_search(query: str) -> str:
    """Search the web for information."""
    # Implementation here
    return f"Search results for: {query}"

def summarize_text(text: str, max_length: int = 200) -> str:
    """Summarize long text."""
    return text[:max_length] + "..."

# Create autonomous research agent
researcher = AutonomousAgent(
    name="research_assistant",
    goal="Research topics thoroughly and provide comprehensive summaries",
    instruction="""
    You are an autonomous research assistant.

    When given a research topic:
    1. OBSERVE: Understand what the user wants to learn
    2. THINK: Plan your research approach
    3. PLAN: Create a structured research plan
    4. ACT: Execute searches and gather information
    5. REFLECT: Evaluate findings and identify gaps

    Always explain your reasoning and cite sources.
    """,
    tools=[
        FunctionTool(web_search),
        FunctionTool(summarize_text),
    ],
    persistent_memory=PersistentMemoryStore(namespace="research"),
    max_thoughts=100,
    enable_proactivity=True,
)

# Run the agent
async def run_research(topic: str):
    runner = Runner(
        agent=researcher.adk_agent,
        app_name="research_app",
    )

    # Start research
    print(f"Starting research on: {topic}")

    # The agent will autonomously:
    # 1. Think about the topic
    # 2. Create a research plan
    # 3. Execute searches
    # 4. Synthesize findings
    # 5. Store learnings for future use

    async for event in runner.run_async(
        user_id="user_123",
        session_id="session_456",
        new_message=types.Content(
            parts=[types.Part(text=f"Research: {topic}")]
        ),
    ):
        # Process events
        pass

    # Get reasoning summary
    summary = researcher.get_reasoning_summary()
    print(summary)

    # Get stats
    stats = researcher.get_autonomous_stats()
    print(f"Actions taken: {stats['action_count']}")
    print(f"Progress: {stats['goal_progress']:.0%}")

asyncio.run(run_research("Recent advances in multimodal AI"))
```

## Proactive Behavior

Enable agents to take initiative without explicit prompts.

```python
from adk_bidi import AutonomousAgent
from adk_bidi import StreamingPresets

# Create proactive agent
agent = AutonomousAgent(
    name="proactive_assistant",
    goal="Help users efficiently, anticipating their needs",
    enable_proactivity=True,
)

# Use with proactive streaming config
run_config = StreamingPresets.autonomous_proactive()
# Enables:
# - proactive_audio: Agent can speak first
# - enable_affective_dialog: Emotional awareness
# - session_resumption: Maintain context across sessions
```

## Multi-Agent Autonomous Systems

Combine autonomous agents with supervisors.

```python
from adk_bidi import AutonomousAgent, MultiAgentSupervisor, SharedMemory
from adk_bidi.agents.autonomous_agent import ResearchAgent, TaskAgent

# Create autonomous specialists
researcher = ResearchAgent(
    name="researcher",
    research_topic="Market analysis",
)

analyst = AutonomousAgent(
    name="analyst",
    goal="Analyze research findings and provide insights",
)

writer = TaskAgent(
    name="writer",
    task_description="Create comprehensive reports",
    success_criteria=["Clear structure", "Actionable insights"],
)

# Coordinate with supervisor
shared_memory = SharedMemory()
team = MultiAgentSupervisor(
    agents=[researcher.adk_agent, analyst.adk_agent, writer.adk_agent],
    shared_memory=shared_memory,
    instruction="""
    Coordinate the research team:
    1. Researcher gathers information
    2. Analyst interprets findings
    3. Writer creates the final report

    Each agent reasons autonomously about their task.
    """,
)
```

## Reasoning Phase Management

Track and manage reasoning phases.

```python
from adk_bidi.agents.autonomous_agent import ReasoningPhase

# Check current phase
print(f"Current phase: {agent.current_phase}")  # ReasoningPhase.OBSERVE

# Advance to next phase
next_phase = agent.advance_phase()
print(f"Now in: {next_phase}")  # ReasoningPhase.THINK

# Available phases
# ReasoningPhase.OBSERVE - Processing inputs
# ReasoningPhase.THINK - Reasoning about situation
# ReasoningPhase.PLAN - Creating action plan
# ReasoningPhase.ACT - Executing actions
# ReasoningPhase.REFLECT - Evaluating outcomes
```

## Statistics and Monitoring

Track autonomous agent behavior.

```python
# Get comprehensive stats
stats = agent.get_autonomous_stats()

print(f"Goal: {stats['goal']}")
print(f"Progress: {stats['goal_progress']:.0%}")
print(f"Current phase: {stats['current_phase']}")
print(f"Thoughts recorded: {stats['thoughts_count']}")
print(f"Actions taken: {stats['action_count']}")
print(f"Has active plan: {stats['has_plan']}")
print(f"Plan status: {stats['plan_status']}")
```

## Environment Variables

```bash
# Google AI
GOOGLE_API_KEY=your_gemini_api_key

# For persistent memory (optional)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_HOST=your_index_host
```

## Best Practices

1. **Clear Goals**: Define specific, measurable goals
2. **Success Criteria**: For task agents, define explicit success criteria
3. **Memory Integration**: Use persistent memory for learning across sessions
4. **Reasoning Transparency**: Review reasoning summaries to understand agent behavior
5. **Incremental Progress**: Use update_progress() to track goal completion
6. **Error Handling**: Agents should reflect and adapt when actions fail

## Related Skills

- **adk-bidi-multi-agent**: Real-time multi-agent streaming
- **adk-memory-manager**: Memory systems for agents
- **adk-multi-agent-orchestrator**: Agent team coordination
