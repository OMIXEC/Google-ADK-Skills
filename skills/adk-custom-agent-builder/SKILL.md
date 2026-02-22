---
name: ADK Custom Agent Builder
description: This skill should be used when the user asks to "build a custom agent", "design an agent from scratch", "create a specialized agent", "agent architecture", or "adaptive agent builder". Provides comprehensive guidance for designing and implementing agents tailored to specific requirements with full control over behavior, tools, and instructions.
version: 1.0.0
---

# ADK Custom Agent Builder

The ADK Custom Agent Builder skill enables creating fully customized agents for specific use cases. Unlike templates, custom agents give complete control over instructions, tools, architecture, and behavior patterns.

## Agent Design Process

Building a custom agent follows this workflow:

**Step 1: Define Agent Purpose**
Articulate the agent's primary role and responsibilities in a single sentence.

Example: "This agent autonomously researches market trends and creates competitive analysis reports"

**Step 2: Choose Agent Architecture**
Decide if the agent will be:
- **Single-Agent**: One agent handles all requests (simpler, faster)
- **Multi-Agent Foundation**: Foundation agent that coordinates with specialists (extensible)

For most custom agents, start single-agent. See adk-multi-agent-workflows skill if you need orchestration.

**Step 3: Select Tools and Capabilities**
Identify what tools the agent needs:
- Web search (Brave API)
- Document processing
- Database access
- API calls
- File operations
- Custom business logic

Only include tools the agent will actually use.

**Step 4: Design System Instructions**
Create a system prompt that guides the agent's reasoning. Best prompts:
- Define the agent's role and expertise
- Explain how to approach problems
- Set constraints and boundaries
- Specify output format expectations
- Include examples of good behavior

**Step 5: Test and Iterate**
Build the agent in Python, test locally with `/adk:test`, refine based on results.

**Step 6: Add Advanced Features**
As needed, layer in:
- Knowledge bases (RAG)
- Persistent memory
- Real-time streaming
- External integrations

## Core Agent Components

### System Prompt

The system prompt is the foundation of agent behavior. Effective prompts:

```python
SYSTEM_PROMPT = """
You are an expert Market Research Analyst specializing in competitive analysis.

Your role:
- Systematically research competitors in assigned markets
- Identify strategic differentiators and vulnerabilities
- Create comprehensive competitive analysis reports
- Track market trends and emerging threats

How to approach tasks:
1. Clarify the scope: Which competitors? Which markets? What timeframe?
2. Research systematically: Use web search to gather data on each competitor
3. Organize findings: Group by business model, products, pricing, positioning
4. Synthesize insights: Identify patterns and strategic implications
5. Present professionally: Create clear, actionable reports

Constraints:
- Focus on public information only
- Cite sources for claims
- Avoid speculation without evidence
- Present balanced view of strengths and weaknesses

Output format:
- Executive summary (1-2 paragraphs)
- Competitor profiles (for each competitor)
- Market trends and patterns
- Strategic recommendations
"""
```

Good system prompts:
- Define expertise and role clearly
- Explain step-by-step approach
- Set boundaries and constraints
- Specify output format
- Include behavioral examples

### Tools

Tools extend what agents can do. Define tools with:
- Clear name and description
- Input parameters with types
- Return value description

```python
from adk_bidi.core import Tool

web_search = Tool(
    name="web_search",
    description="Search the web for information using Brave Search",
    parameters={
        "query": "Search query string",
        "limit": "Number of results (default 10)"
    }
)

agent.add_tool(web_search)
```

Start with minimal tools. Add more as needed.

### Memory Systems

Agents can maintain memory across conversations:

**Working Memory** (current request)
- Loaded automatically from context
- Always available
- Limited to current interaction

**Persistent Memory** (across sessions)
```python
from adk_bidi.memory import PersistentMemory

memory = PersistentMemory(
    storage="pinecone",
    api_key=os.getenv("PINECONE_API_KEY")
)
agent.memory = memory
```

See adk-knowledge-systems skill for detailed memory and RAG guidance.

### Output Format

Design what the agent should produce:

```python
# Structured output
output_schema = {
    "summary": "Executive summary",
    "findings": [
        {
            "category": "Product Strategy",
            "insight": "Specific finding",
            "evidence": "Supporting data"
        }
    ],
    "recommendations": ["Action 1", "Action 2"]
}

# Or plain text
# Or formatted markdown
# Or JSON API response
```

Specify format clearly in system prompt.

## Building a Custom Agent: Step-by-Step

### Step 1: Create Agent Class

```python
from adk_bidi.agents import Agent
from adk_bidi.core import Tool
import os

class MarketAnalystAgent(Agent):
    def __init__(self):
        self.name = "Market Research Analyst"
        self.model = "gemini-2.5-flash"
        self.temperature = 0.7

        # Define system prompt
        self.system_prompt = """
        You are an expert Market Research Analyst...
        """

        # Add tools
        self._setup_tools()

    def _setup_tools(self):
        # Add web search
        from adk_bidi.tools import BraveSearchTool
        self.add_tool(BraveSearchTool(
            api_key=os.getenv("BRAVE_API_KEY")
        ))
```

### Step 2: Implement Agent Logic

```python
    def analyze_competitor(self, competitor_name: str, market: str) -> dict:
        """Analyze a specific competitor in a market."""

        prompt = f"""
        Research {competitor_name} in the {market} market.

        Find information about:
        - Business model and revenue streams
        - Products/services offered
        - Target customers
        - Pricing strategy
        - Market position and growth
        - Recent news and developments

        Create a structured competitive analysis.
        """

        response = self.ask(prompt)
        return self._parse_response(response)

    def _parse_response(self, response: str) -> dict:
        """Parse agent response into structured format."""
        # Implementation depends on output format
        return json.loads(response)
```

### Step 3: Test Locally

```python
# Test the agent
if __name__ == "__main__":
    analyst = MarketAnalystAgent()

    result = analyst.analyze_competitor(
        competitor_name="Company X",
        market="SaaS Cloud Storage"
    )

    print(json.dumps(result, indent=2))
```

### Step 4: Integrate into Application

Once tested:
1. Create project with `/adk:init`
2. Copy agent code to project
3. Implement your application logic
4. Deploy with adk-production-deployment skill

## Architecture Patterns

### Pattern 1: Information Retrieval Agent

For agents that find and synthesize information:

```python
class ResearchAgent(Agent):
    def research(self, topic: str) -> str:
        # 1. Search for information
        # 2. Gather sources
        # 3. Synthesize findings
        # 4. Cite sources
        return structured_report
```

Tools: web_search, document_processing, citation_management

### Pattern 2: Decision Support Agent

For agents that help make decisions:

```python
class DecisionAdvisor(Agent):
    def evaluate_options(self, options: list, criteria: dict) -> dict:
        # 1. Define decision criteria
        # 2. Score each option
        # 3. Identify tradeoffs
        # 4. Recommend action
        return recommendation
```

Tools: data_analysis, comparison_logic, risk_assessment

### Pattern 3: Code Generation Agent

For agents that produce code:

```python
class CodeGenerator(Agent):
    def generate_code(self, requirement: str) -> str:
        # 1. Understand requirement
        # 2. Design solution
        # 3. Generate code
        # 4. Add error handling
        # 5. Create tests
        return code_with_tests
```

Tools: code_linting, syntax_checking, test_generation

### Pattern 4: Automation Agent

For agents that automate workflows:

```python
class WorkflowAutomator(Agent):
    def automate_process(self, workflow: str) -> bool:
        # 1. Map process steps
        # 2. Execute each step
        # 3. Handle errors
        # 4. Log progress
        # 5. Report results
        return success
```

Tools: system_commands, database_access, notification_systems

## Advanced Customization

### Add Streaming

For real-time responses:

```python
response_stream = agent.ask_streaming(prompt)
for chunk in response_stream:
    print(chunk, end="", flush=True)
```

### Add Async Support

```python
async def analyze_async(self, data):
    return await self.ask_async(prompt)
```

### Add Custom Validators

```python
def validate_output(self, output: str) -> bool:
    # Check output meets requirements
    # Return True if valid, False otherwise
    pass

agent.add_validator(validate_output)
```

### Add Logging

```python
import logging

logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)

# Log all interactions
agent.log_interactions = True
```

## Decision Framework

### Single Agent or Multi-Agent?

**Use Single Agent When:**
- Single clear responsibility
- All tasks in same domain
- Simpler is better
- Faster response needed

**Use Multi-Agent When:**
- Multiple specializations needed
- Tasks require different expertise
- Coordination helps quality
- See adk-multi-agent-workflows skill

### Which Tools?

**Add Tools For:**
- External information (web search)
- Data processing (documents, databases)
- External systems (APIs, services)
- Specialized operations

**Skip Tools For:**
- Tasks pure reasoning handles
- Operations bloat complexity
- Edge case scenarios
- Uncertain requirements

Start minimal, add tools based on testing.

### Memory or No Memory?

**Add Memory When:**
- Agent needs context across sessions
- Learning from past interactions valuable
- Personalization important

**Skip Memory When:**
- Stateless requests acceptable
- No need for context
- Simplicity prioritized

See adk-knowledge-systems skill for memory guidance.

## Testing Custom Agents

### Local Testing

```bash
/adk:test my_agent.py

# Or programmatically
agent = MyAgent()
results = agent.test_suite([
    ("test prompt 1", expected_output_1),
    ("test prompt 2", expected_output_2)
])
```

### Validation Checklist

- [ ] Agent produces correct output format
- [ ] All tools are used appropriately
- [ ] Error handling is graceful
- [ ] Performance is acceptable
- [ ] No hallucination on out-of-domain queries
- [ ] Respects constraints and boundaries
- [ ] Citations/sources when required

## Supporting Resources

### Reference Files
- **`references/architecture-patterns.md`** - Detailed patterns and design decisions
- **`references/instruction-design.md`** - System prompt best practices
- **`references/tool-selection.md`** - Guide to choosing and implementing tools

### Examples
- **`examples/research-agent.py`** - Complete research agent
- **`examples/decision-agent.py`** - Decision support agent
- **`examples/code-generator.py`** - Code generation agent

## Next Steps

1. **Define agent purpose** - What will it do?
2. **Choose architecture** - Single or multi-agent?
3. **Select tools** - What capabilities needed?
4. **Design instructions** - System prompt
5. **Build in Python** - Implement agent class
6. **Test locally** - `/adk:test` your agent
7. **Deploy** - Use adk-production-deployment skill

For orchestrating multiple agents, see **adk-multi-agent-workflows** skill.

For adding knowledge and memory, see **adk-knowledge-systems** skill.

For real-time capabilities, see **adk-real-time-agents** skill.
