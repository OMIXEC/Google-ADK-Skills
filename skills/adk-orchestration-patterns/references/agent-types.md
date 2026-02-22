# ADK Agent Types Reference

## SequentialAgent

### Overview
Executes sub-agents in a predetermined order. Each agent receives the output of the previous agent as input.

### API

```python
from google.adk.agents import SequentialAgent

sequential = SequentialAgent(
    name: str,                    # Agent identifier
    sub_agents: List[Agent],      # Ordered list of agents to execute
    description: str = None,      # Optional description
)
```

### Execution Flow

```
Input → Agent1 → Output1 → Agent2 → Output2 → Agent3 → Final Output
```

### Parameters

- **name**: Unique identifier for the agent
- **sub_agents**: List of agents to execute in order
- **description**: Optional description for clarity

### Behavior

- Executes agents sequentially in the order provided
- Each agent receives the output of the previous agent
- If any agent fails, the sequence stops
- Final output is the result of the last agent

### Use Cases

1. **Multi-stage processing**: Data transformation pipelines
2. **Sequential validation**: Check → Sanitize → Validate
3. **Workflow chains**: Research → Draft → Review → Publish
4. **Dependency chains**: When step N+1 requires output of step N

### Example: Content Creation Pipeline

```python
from google.adk.agents import SequentialAgent, LlmAgent

researcher = LlmAgent(
    name="researcher",
    model="gemini-2.5-flash",
    instruction="""
    Research the given topic thoroughly.
    Output: JSON with sources, key facts, and insights.
    """
)

writer = LlmAgent(
    name="writer",
    model="gemini-2.5-flash",
    instruction="""
    Write a comprehensive article based on the research.
    Use the facts and insights provided.
    Output: Draft article with introduction, body, conclusion.
    """
)

editor = LlmAgent(
    name="editor",
    model="gemini-2.5-flash",
    instruction="""
    Edit the article for clarity, grammar, and style.
    Ensure proper structure and flow.
    Output: Polished final article.
    """
)

pipeline = SequentialAgent(
    name="content_pipeline",
    sub_agents=[researcher, writer, editor],
    description="End-to-end content creation from research to publication"
)

result = pipeline.run("Write about quantum computing trends in 2026")
```

### Best Practices

- Keep sequence short (3-5 agents max)
- Each agent should have clear output format
- Use descriptive names for agents
- Handle errors at each stage if possible

---

## ParallelAgent

### Overview
Executes multiple sub-agents concurrently. All agents receive the same input, and their results are aggregated.

### API

```python
from google.adk.agents import ParallelAgent

parallel = ParallelAgent(
    name: str,                    # Agent identifier
    sub_agents: List[Agent],      # List of agents to execute in parallel
    description: str = None,      # Optional description
)
```

### Execution Flow

```
           ┌→ Agent1 → Output1 ┐
Input ────→├→ Agent2 → Output2 ├→ Aggregated Output
           └→ Agent3 → Output3 ┘
```

### Parameters

- **name**: Unique identifier for the agent
- **sub_agents**: List of agents to execute concurrently
- **description**: Optional description for clarity

### Behavior

- Executes all agents concurrently (when possible)
- All agents receive the same input
- Results are aggregated into a single output
- Faster than sequential for independent tasks

### Use Cases

1. **Multiple perspectives**: Technical + Business + Risk analysis
2. **Concurrent processing**: Process multiple data sources
3. **Validation from multiple angles**: Security + Performance + Usability checks
4. **Comparative analysis**: Multiple models or approaches

### Example: Comprehensive Analysis

```python
from google.adk.agents import ParallelAgent, LlmAgent

technical_analyst = LlmAgent(
    name="technical_analyst",
    model="gemini-2.5-flash",
    instruction="""
    Analyze from technical perspective:
    - Feasibility
    - Technical risks
    - Implementation complexity
    - Technology stack requirements
    """
)

business_analyst = LlmAgent(
    name="business_analyst",
    model="gemini-2.5-flash",
    instruction="""
    Analyze from business perspective:
    - Cost implications
    - ROI potential
    - Market fit
    - Business risks
    """
)

legal_analyst = LlmAgent(
    name="legal_analyst",
    model="gemini-2.5-flash",
    instruction="""
    Analyze from legal/compliance perspective:
    - Regulatory requirements
    - Compliance risks
    - Data privacy concerns
    - Legal obligations
    """
)

analysis_team = ParallelAgent(
    name="comprehensive_analysis",
    sub_agents=[technical_analyst, business_analyst, legal_analyst],
    description="Multi-perspective analysis for decision making"
)

result = analysis_team.run("Should we implement facial recognition in our app?")
```

### Best Practices

- Use for independent tasks only
- Limit to 3-5 parallel agents for manageability
- Ensure agents have consistent output formats
- Aggregate results meaningfully in downstream processing

---

## LoopAgent

### Overview
Executes sub-agents iteratively until a condition is met or max iterations reached.

### API

```python
from google.adk.agents import LoopAgent

loop = LoopAgent(
    name: str,                    # Agent identifier
    sub_agents: List[Agent],      # Agents to execute in each iteration
    max_iterations: int = 10,     # Maximum number of iterations
    description: str = None,      # Optional description
)
```

### Execution Flow

```
Input → Agent(s) → Output1 → Check condition
         ↑                      ↓
         └── Output2 ←─ Agent(s) (if not done)
         ↑                      ↓
         └── OutputN ←─ Agent(s) (until max iterations or done)
```

### Parameters

- **name**: Unique identifier for the agent
- **sub_agents**: List of agents to execute in each iteration
- **max_iterations**: Maximum number of loop iterations (default: 10)
- **description**: Optional description for clarity

### Behavior

- Executes agents repeatedly
- Each iteration can refine or build upon previous output
- Stops when max_iterations reached
- Useful for convergence and refinement

### Use Cases

1. **Iterative refinement**: Code improvement, text polishing
2. **Quality improvement loops**: Check → Fix → Recheck
3. **Convergence algorithms**: Refine until acceptable
4. **Retry with intelligence**: Learn from previous attempts

### Example: Code Quality Improvement

```python
from google.adk.agents import LoopAgent, LlmAgent

analyzer = LlmAgent(
    name="code_analyzer",
    model="gemini-2.5-flash",
    instruction="""
    Analyze the code for:
    - Code smells
    - Performance issues
    - Readability problems
    - Best practice violations

    Output issues found as JSON.
    """
)

improver = LlmAgent(
    name="code_improver",
    model="gemini-2.5-flash",
    instruction="""
    Fix the issues identified in the analysis.
    Improve code quality while maintaining functionality.
    Output improved code.
    """
)

quality_loop = LoopAgent(
    name="quality_improvement",
    sub_agents=[analyzer, improver],
    max_iterations=3,
    description="Iterative code quality improvement"
)

result = quality_loop.run("""
def calc(x,y):
    return x+y
""")
```

### Example: Iterative Problem Solving

```python
from google.adk.agents import LoopAgent, LlmAgent

solver = LlmAgent(
    name="solver",
    instruction="""
    Attempt to solve the problem.
    If solution is incomplete or incorrect, identify what's missing.
    Refine approach in next iteration.
    """
)

refinement_loop = LoopAgent(
    name="problem_solver",
    sub_agents=[solver],
    max_iterations=5,
)

result = refinement_loop.run("Find the optimal route for visiting these 10 cities")
```

### Best Practices

- Set reasonable max_iterations (3-5 for most cases)
- Design agents to show improvement each iteration
- Log iteration number for debugging
- Consider convergence criteria in agent instructions

---

## LlmAgent (with AgentTool for Dynamic Routing)

### Overview
An LLM-powered agent that can dynamically invoke other agents using AgentTool. The LLM decides which agent(s) to use based on the input.

### API

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

router = LlmAgent(
    name: str,
    model: str,
    tools: List[AgentTool],       # Other agents as tools
    instruction: str,              # Routing logic
    description: str = None,
)
```

### Execution Flow

```
Input → LLM Router → Analyzes input → Selects Agent(s) → Execute → Output
```

### Parameters

- **name**: Unique identifier for the routing agent
- **model**: LLM model to use for routing decisions
- **tools**: List of AgentTool wrapping other agents
- **instruction**: How to route and when to use each agent
- **description**: Optional description for clarity

### Behavior

- LLM analyzes input and decides which agent(s) to invoke
- Can call multiple agents sequentially or based on results
- Fully dynamic routing based on context
- Most flexible but requires clear routing instructions

### Use Cases

1. **Customer service routing**: Route to specialists
2. **Intent-based delegation**: Different workflows for different intents
3. **Adaptive workflows**: Choose approach based on complexity
4. **Smart task distribution**: Delegate to best-suited agent

### Example: Customer Service Router

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

billing_agent = LlmAgent(
    name="billing_specialist",
    model="gemini-2.5-flash",
    instruction="""
    Handle billing questions:
    - Invoices and payments
    - Subscription management
    - Refunds and credits
    - Payment method updates
    """
)

support_agent = LlmAgent(
    name="support_specialist",
    model="gemini-2.5-flash",
    instruction="""
    Handle technical support:
    - Login issues
    - Feature usage
    - Troubleshooting
    - Bug reports
    """
)

sales_agent = LlmAgent(
    name="sales_specialist",
    model="gemini-2.5-flash",
    instruction="""
    Handle sales questions:
    - Product features
    - Pricing information
    - Upgrade options
    - Demo requests
    """
)

coordinator = LlmAgent(
    name="customer_service_coordinator",
    model="gemini-2.5-flash",
    description="Routes customer requests to appropriate specialists",
    tools=[
        AgentTool(agent=billing_agent),
        AgentTool(agent=support_agent),
        AgentTool(agent=sales_agent),
    ],
    instruction="""
    Analyze the customer request and route to the appropriate specialist:

    1. Billing specialist for:
       - Payment issues, invoices, subscriptions, refunds

    2. Support specialist for:
       - Technical problems, login issues, troubleshooting, features

    3. Sales specialist for:
       - Product questions, pricing, upgrades, demos

    You can call multiple specialists if needed.
    Provide a comprehensive response to the customer.
    """
)

result = coordinator.run("I can't log in and I think I was double-charged")
```

### Example: Research Task Router

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

web_researcher = LlmAgent(
    name="web_researcher",
    instruction="Search the web for recent information and trends."
)

academic_researcher = LlmAgent(
    name="academic_researcher",
    instruction="Search academic papers and scholarly sources."
)

data_analyst = LlmAgent(
    name="data_analyst",
    instruction="Analyze datasets and provide statistical insights."
)

research_coordinator = LlmAgent(
    name="research_coordinator",
    model="gemini-2.5-flash",
    tools=[
        AgentTool(agent=web_researcher),
        AgentTool(agent=academic_researcher),
        AgentTool(agent=data_analyst),
    ],
    instruction="""
    Based on the research query, determine the best approach:
    - Use web_researcher for recent trends, news, and general information
    - Use academic_researcher for scientific topics requiring peer-reviewed sources
    - Use data_analyst when the query involves data analysis or statistics

    You can use multiple researchers for comprehensive coverage.
    """
)

result = research_coordinator.run("What are the latest advances in quantum computing?")
```

### Best Practices

- Write clear routing instructions with specific criteria
- Use descriptive agent names and descriptions
- Keep the number of routable agents manageable (3-7)
- Test routing with various input types
- Log routing decisions for debugging

---

## Comparison Matrix

| Agent Type | Execution | Input Distribution | Use Case | Control |
|------------|-----------|-------------------|----------|---------|
| **Sequential** | One after another | Output of previous agent | Ordered workflows, dependencies | Static |
| **Parallel** | Concurrent | Same input to all | Independent tasks, multiple perspectives | Static |
| **Loop** | Iterative | Previous iteration output | Refinement, convergence | Static with max iterations |
| **LlmAgent + AgentTool** | Dynamic | LLM decides | Intent-based routing, adaptive workflows | Dynamic (LLM) |

---

## Combining Agent Types

You can compose these agents to create complex orchestration patterns:

### Sequential + Parallel

```python
# Stage 1: Gather data in parallel
data_gatherers = ParallelAgent(
    name="data_collection",
    sub_agents=[source_a, source_b, source_c]
)

# Stage 2: Process gathered data
processor = LlmAgent(name="processor", instruction="Process all gathered data")

# Sequential pipeline
pipeline = SequentialAgent(
    name="gather_and_process",
    sub_agents=[data_gatherers, processor]
)
```

### Loop + Sequential

```python
# Iterative refinement with multi-step process
refiner = SequentialAgent(
    name="refine_step",
    sub_agents=[analyzer, fixer, validator]
)

refinement_loop = LoopAgent(
    name="quality_loop",
    sub_agents=[refiner],
    max_iterations=3
)
```

### Router + Teams

```python
# Each team is a SequentialAgent or ParallelAgent
engineering_team = ParallelAgent(...)
product_team = ParallelAgent(...)

cto = LlmAgent(
    name="cto",
    tools=[AgentTool(agent=engineering_team), AgentTool(agent=product_team)],
    instruction="Delegate to appropriate team"
)
```
