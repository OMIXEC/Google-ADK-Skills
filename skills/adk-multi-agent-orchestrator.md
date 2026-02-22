---
name: adk-multi-agent-orchestrator
description: Create multi-agent systems with supervisor-specialist hierarchies, sequential pipelines, or parallel execution. Uses AgentTool delegation for coordination. Patterns include supervisor (coordinator delegates to specialists), sequential (step-by-step pipeline), parallel (concurrent execution), hierarchical teams, debate (multiple perspectives argue), consensus (agents vote), specialist teams (domain experts collaborate), and review chains (sequential review). Use when tasks require specialized agents, coordination, or complex workflows.
version: 2.0.0
trigger_keywords:
  - multi-agent orchestration
  - agent collaboration
  - debate pattern
  - consensus voting
  - specialist teams
  - review chain
  - agent coordination
examples:
  - Multi-perspective debate
  - Consensus-based decision
  - Expert team collaboration
  - Sequential review process
references:
  - team-patterns.md
templates: []
---

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

## Advanced Multi-Agent Patterns

### 4. Debate Pattern

Multiple agents argue different perspectives to explore a topic thoroughly.

**Use Cases:**
- Decision-making requiring multiple viewpoints
- Exploring pros and cons
- Critical analysis
- Controversial topics

**Example:**
```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Debater: Optimistic perspective
optimist = LlmAgent(
    name="optimist",
    model="gemini-2.5-flash",
    instruction="""
    You are an optimistic debater.
    - Argue the positive aspects and opportunities
    - Highlight benefits and potential gains
    - Be enthusiastic but fact-based
    - Counter pessimistic arguments constructively
    """
)

# Debater: Pessimistic perspective
pessimist = LlmAgent(
    name="pessimist",
    model="gemini-2.5-flash",
    instruction="""
    You are a critical debater.
    - Argue the risks and downsides
    - Identify potential problems
    - Be skeptical but fair
    - Counter optimistic arguments with concerns
    """
)

# Moderator synthesizes both perspectives
moderator = LlmAgent(
    name="moderator",
    model="gemini-2.5-pro",
    description="Moderates debate and synthesizes conclusions",
    instruction="""
    You moderate the debate between optimist and pessimist.

    **Process:**
    1. Present the topic to both debaters
    2. Collect optimistic perspective
    3. Collect pessimistic perspective
    4. Have each respond to the other's arguments
    5. Synthesize balanced conclusion

    **Output:**
    - Summary of both perspectives
    - Key points of agreement and disagreement
    - Balanced recommendation
    - Conditions for success or failure
    """,
    tools=[
        AgentTool(agent=optimist),
        AgentTool(agent=pessimist),
    ],
)

root_agent = moderator
```

### 5. Consensus Pattern

Multiple agents vote or reach consensus on decisions.

**Use Cases:**
- Democratic decision-making
- Quality assessment
- Ensemble predictions
- Risk evaluation

**Example:**
```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Voter agents with different expertise
security_expert = LlmAgent(
    name="security_expert",
    instruction="""
    Evaluate from security perspective.
    Vote: APPROVE, REJECT, or ABSTAIN
    Provide justification for your vote.
    """
)

performance_expert = LlmAgent(
    name="performance_expert",
    instruction="""
    Evaluate from performance perspective.
    Vote: APPROVE, REJECT, or ABSTAIN
    Provide justification for your vote.
    """
)

usability_expert = LlmAgent(
    name="usability_expert",
    instruction="""
    Evaluate from usability perspective.
    Vote: APPROVE, REJECT, or ABSTAIN
    Provide justification for your vote.
    """
)

# Vote counter and consensus builder
consensus_builder = LlmAgent(
    name="consensus_builder",
    model="gemini-2.5-flash",
    description="Collects votes and builds consensus",
    instruction="""
    Collect votes from all experts and determine consensus.

    **Process:**
    1. Present proposal to each expert
    2. Collect votes and justifications
    3. Tally results
    4. Determine consensus or majority
    5. Identify dissenting opinions

    **Consensus Rules:**
    - Unanimous APPROVE → APPROVED
    - Majority APPROVE → APPROVED (note dissent)
    - Majority REJECT → REJECTED
    - Tie or all ABSTAIN → NEEDS_REVISION

    **Output:**
    - Vote tally
    - Consensus decision
    - Summary of all perspectives
    - Action items based on feedback
    """,
    tools=[
        AgentTool(agent=security_expert),
        AgentTool(agent=performance_expert),
        AgentTool(agent=usability_expert),
    ],
)

root_agent = consensus_builder
```

### 6. Specialist Team Pattern

Domain experts collaborate on complex problems requiring deep expertise.

**Use Cases:**
- Cross-functional projects
- Complex problem-solving
- Technical design reviews
- Multidisciplinary research

**Example:**
```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Domain specialists
backend_specialist = LlmAgent(
    name="backend_specialist",
    model="gemini-2.5-flash",
    instruction="""
    Backend development expert.
    Provide: API design, database schema, business logic, scalability
    """
)

frontend_specialist = LlmAgent(
    name="frontend_specialist",
    model="gemini-2.5-flash",
    instruction="""
    Frontend development expert.
    Provide: UI/UX design, component architecture, state management
    """
)

devops_specialist = LlmAgent(
    name="devops_specialist",
    model="gemini-2.5-flash",
    instruction="""
    DevOps and infrastructure expert.
    Provide: Deployment strategy, CI/CD, monitoring, scaling
    """
)

security_specialist = LlmAgent(
    name="security_specialist",
    model="gemini-2.5-flash",
    instruction="""
    Security expert.
    Provide: Threat analysis, authentication, authorization, compliance
    """
)

# Team coordinator
tech_lead = LlmAgent(
    name="tech_lead",
    model="gemini-2.5-pro",
    description="Coordinates specialist team for technical solutions",
    instruction="""
    You are the technical lead coordinating a specialist team.

    **Team:**
    - backend_specialist: Backend and APIs
    - frontend_specialist: UI and UX
    - devops_specialist: Infrastructure and deployment
    - security_specialist: Security and compliance

    **Process:**
    1. Understand the project requirements
    2. Consult relevant specialists
    3. Ensure specialists collaborate on interfaces
    4. Synthesize into comprehensive technical design
    5. Identify dependencies and integration points

    **Output:**
    - Comprehensive technical design
    - Clear responsibilities for each area
    - Integration plan
    - Timeline and milestones
    """,
    tools=[
        AgentTool(agent=backend_specialist),
        AgentTool(agent=frontend_specialist),
        AgentTool(agent=devops_specialist),
        AgentTool(agent=security_specialist),
    ],
)

root_agent = tech_lead
```

### 7. Review Chain Pattern

Sequential review process where each reviewer builds on previous feedback.

**Use Cases:**
- Code review workflows
- Document editing
- Quality assurance
- Approval processes

**Example:**
```python
from google.adk.agents import SequentialAgent, LlmAgent

# Reviewer 1: Technical review
technical_reviewer = LlmAgent(
    name="technical_reviewer",
    model="gemini-2.5-flash",
    instruction="""
    Review for technical correctness:
    - Code quality and best practices
    - Logic errors and bugs
    - Performance issues
    - Technical debt

    Output: Technical review with issues and suggestions
    """
)

# Reviewer 2: Security review (receives tech review feedback)
security_reviewer = LlmAgent(
    name="security_reviewer",
    model="gemini-2.5-flash",
    instruction="""
    Review for security:
    - Vulnerabilities
    - Authentication/authorization
    - Data protection
    - Secure coding practices

    Build on previous technical review.
    Output: Security review with additional issues
    """
)

# Reviewer 3: Architecture review (receives both previous reviews)
architecture_reviewer = LlmAgent(
    name="architecture_reviewer",
    model="gemini-2.5-pro",
    instruction="""
    Review for architecture and design:
    - Design patterns
    - Scalability
    - Maintainability
    - Adherence to architecture

    Consider technical and security feedback.
    Output: Architecture review with recommendations
    """
)

# Final reviewer: Approval decision (receives all reviews)
approval_reviewer = LlmAgent(
    name="approval_reviewer",
    model="gemini-2.5-flash",
    instruction="""
    Final approval decision based on all reviews.

    Synthesize all feedback:
    - Technical issues
    - Security concerns
    - Architecture recommendations

    Decide: APPROVED, NEEDS_REVISION, or REJECTED
    Provide consolidated feedback and action items.
    """
)

# Sequential review chain
review_chain = SequentialAgent(
    name="code_review_chain",
    description="Sequential code review process",
    sub_agents=[
        technical_reviewer,
        security_reviewer,
        architecture_reviewer,
        approval_reviewer,
    ],
)

root_agent = review_chain
```

## State Management and Communication

### Shared Memory Across Agents

Agents can share context through:

1. **Passing State in Output:**
```python
agent_a = LlmAgent(
    instruction="Output findings as JSON: {findings: [...], metadata: {...}}"
)
agent_b = LlmAgent(
    instruction="Use the findings JSON from previous agent"
)
```

2. **External State Store:**
```python
# Shared context via tools
class SharedState:
    def __init__(self):
        self.context = {}

    def set(self, key, value):
        self.context[key] = value

    def get(self, key):
        return self.context.get(key)

shared_state = SharedState()

# Agents use tools to access shared state
def get_shared_context(key):
    return shared_state.get(key)

def set_shared_context(key, value):
    shared_state.set(key, value)
```

### Event-Driven Communication

Agents can communicate via events:

```python
from typing import List, Dict

class EventBus:
    def __init__(self):
        self.events: List[Dict] = []

    def publish(self, event_type: str, data: Dict):
        self.events.append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now()
        })

    def get_events(self, event_type: str = None):
        if event_type:
            return [e for e in self.events if e["type"] == event_type]
        return self.events

# Agents can publish and subscribe via tools
event_bus = EventBus()
```

### Artifact Passing

Agents pass structured artifacts:

```python
# Agent A outputs artifact
agent_a = LlmAgent(
    instruction="""
    Output structured artifact:
    {
        "artifact_type": "analysis",
        "data": {...},
        "metadata": {...}
    }
    """
)

# Agent B consumes artifact
agent_b = LlmAgent(
    instruction="""
    Receive artifact from previous agent.
    Validate artifact type and data.
    Process and enhance the artifact.
    """
)
```

## Best Practices for Team Patterns

### 1. Clear Roles and Responsibilities

Each agent should have a well-defined role:

```python
# Good: Specific role
security_expert = LlmAgent(
    name="security_expert",
    instruction="Focus exclusively on security aspects"
)

# Bad: Vague role
general_expert = LlmAgent(
    name="expert",
    instruction="Help with anything"
)
```

### 2. Structured Communication

Use consistent formats for agent outputs:

```python
instruction = """
Always output in this format:
{
    "agent": "your_name",
    "analysis": "your analysis",
    "recommendation": "your recommendation",
    "confidence": 0-100
}
"""
```

### 3. Conflict Resolution

Define how to handle disagreements:

```python
consensus_builder = LlmAgent(
    instruction="""
    When agents disagree:
    1. Identify points of disagreement
    2. Ask agents to elaborate
    3. Look for common ground
    4. Make informed decision
    5. Document dissent
    """
)
```

### 4. Team Composition

Keep teams focused and manageable:

- **Small teams (2-3 agents):** Faster, more focused
- **Medium teams (4-6 agents):** Comprehensive coverage
- **Large teams (7+ agents):** Use hierarchical structure

### 5. Coordination Overhead

Be aware of coordination costs:

```
2 agents: 1 interaction
3 agents: 3 interactions
4 agents: 6 interactions
5 agents: 10 interactions
```

Use hierarchical patterns for large teams.

## Related Skills

- **adk-adaptive-agent-generator** - Create individual agents
- **adk-orchestration-patterns** - Fundamental orchestration patterns
- **adk-langgraph-orchestrator** - Advanced graph-based orchestration
- **adk-callback-patterns** - Monitor multi-agent systems
- **adk-session-management** - Manage state across agents

## Reference Documentation

- @team-patterns - Advanced team collaboration patterns

## More Information

See CLAUDE.md for multi-agent architecture patterns.
