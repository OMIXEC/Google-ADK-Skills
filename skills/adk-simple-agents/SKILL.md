---
name: ADK Simple Agents
description: This skill should be used when the user asks to "build a fitness coach", "create a researcher", "make a teaching assistant", "simple agent template", "pre-built agent", or "domain expert agent". Provides ready-to-use agent templates for common use cases, enabling rapid prototyping and learning through working examples.
version: 1.0.0
---

# ADK Simple Agents - Pre-Built Templates

The ADK Simple Agents skill provides six production-ready agent templates covering common use cases. Templates accelerate development by providing working code that can be used immediately or customized for specific requirements.

## Template Overview

Six templates are available, each specialized for a specific use case:

| Template | Best For | Key Strength |
|----------|----------|--------------|
| **Fitness Coach** | Fitness app, personal training | Motivational, personalized guidance |
| **Researcher** | Web research, information gathering | Systematic research methodology |
| **Teaching Assistant** | Education, tutoring, training | Pedagogical approach, learner-focused |
| **Domain Expert** | Professional consulting, expertise | Deep specialized knowledge |
| **Customer Service** | Support systems, help desk | Empathy, issue resolution |
| **Data Analyst** | Business intelligence, insights | Statistical reasoning, visualization |

## Getting Started with Templates

### Step 1: Choose a Template

Identify which template matches your use case. See `references/template-guide.md` for detailed descriptions of each template and selection guidance.

### Step 2: Load and Customize

Load a template in Python:

```python
from adk_bidi.agents import SimpleAgent

# Load a pre-configured template
coach = SimpleAgent.load_template("fitness-coach")

# Customize personality or specialization (optional)
coach.personality = "motivational"  # Options: motivational, educational, strict
```

### Step 3: Test Locally

Test the agent before integrating:

```bash
# Use CLI command to test template
/adk:test templates/fitness-coach-example.py

# Or test programmatically
response = coach.ask("Create a Monday workout for beginners")
print(response)
```

### Step 4: Integrate or Extend

Use the template as-is for quick prototypes, or extend with additional capabilities:

```python
# Add tools
coach.add_tool("wearable_api_integration")

# Add knowledge base
coach.knowledge_base = load_rag_system("fitness_docs")

# Add persistent memory
coach.memory = PersistentMemory(storage="pinecone")
```

### Step 5: Deploy

Once satisfied with the agent, deploy using the production deployment skill.

## Template Details

### Fitness Coach
**Specializations**: General, Yoga, Bodybuilding, Running, CrossFit, Pilates, Strength

Provides personalized fitness advice, workout recommendations, and motivational coaching.

```python
coach = SimpleAgent.load_template("fitness-coach")
coach.specialization = "yoga"
response = coach.ask("What's a good beginner yoga routine?")
```

### Researcher
**Specializations**: Academic, Industry, General, Market Research

Conducts systematic web research, organizes findings, and provides comprehensive summaries.

```python
researcher = SimpleAgent.load_template("researcher")
researcher.depth = "comprehensive"
findings = researcher.research("Latest advances in quantum computing")
```

### Teaching Assistant
**Specializations**: Mathematics, Science, Programming, Language, General

Explains concepts pedagogically, adapts to learner level, and provides interactive guidance.

```python
tutor = SimpleAgent.load_template("teaching-assistant")
tutor.level = "high-school"
explanation = tutor.explain("How do photosynthesis works?")
```

### Domain Expert
**Specializations**: Medical, Legal, Finance, Engineering, Technology, General

Provides expert guidance with deep domain knowledge and professional standards.

```python
expert = SimpleAgent.load_template("domain-expert")
expert.domain = "medical"
expert.specialty = "cardiology"
advice = expert.provide_guidance("Heart disease prevention")
```

### Customer Service
**Specializations**: Software, Retail, Hospitality, Finance, Technology

Handles inquiries with empathy, resolves issues, and provides professional support.

```python
support = SimpleAgent.load_template("customer-service")
support.industry = "software"
response = support.handle_inquiry("How do I reset my password?")
```

### Data Analyst
**Specializations**: Financial, Operational, Marketing, Sales, General

Analyzes data, identifies trends, and generates actionable insights.

```python
analyst = SimpleAgent.load_template("data-analyst")
analyst.audience = "executive"
insights = analyst.analyze(dataframe)
```

## Common Customizations

### Change Personality

```python
# Available for most templates
agent.personality = "motivational"  # or "educational", "strict"
```

### Add Web Search

```python
from adk_bidi.tools import WebSearchTool

agent.add_tool(WebSearchTool(api_key=os.getenv("BRAVE_API_KEY")))
```

### Add Knowledge Base (RAG)

```python
from adk_bidi.memory import RAGSystem

rag = RAGSystem(documents_path="path/to/documents")
agent.knowledge_base = rag
```

### Add Persistent Memory

```python
from adk_bidi.memory import PersistentMemory

memory = PersistentMemory(
    storage="pinecone",
    index_name="agent_memory",
    api_key=os.getenv("PINECONE_API_KEY")
)
agent.memory = memory
```

### Add Custom Tools

```python
from adk_bidi.core import Tool

tool = Tool(
    name="my_custom_tool",
    description="Description of what tool does",
    parameters={"param1": "description"}
)
agent.add_tool(tool)
```

### Modify System Instructions

```python
agent.system_prompt = """
Custom system prompt here.
Override default instructions while keeping agent structure.
"""
```

## Template Examples

Working examples for each template are provided in `examples/` directory:

| Template | Example File |
|----------|--------------|
| Fitness Coach | `examples/fitness-coach-demo.py` |
| Researcher | `examples/researcher-demo.py` |
| Teaching Assistant | `examples/tutor-demo.py` |
| Domain Expert | `examples/domain-expert-demo.py` |
| Customer Service | `examples/support-agent-demo.py` |
| Data Analyst | `examples/analyst-demo.py` |

Run examples to see templates in action:

```bash
python examples/fitness-coach-demo.py
python examples/researcher-demo.py
# etc...
```

## Usage Patterns

### Pattern 1: Quick Prototype

Load template, customize minimally, test:

```python
agent = SimpleAgent.load_template("fitness-coach")
response = agent.ask("Workout plan for Monday")
```

**Time**: 5 minutes
**Effort**: Minimal
**Result**: Working prototype

### Pattern 2: Specialized Agent

Load template, add specialization, customize system prompt:

```python
coach = SimpleAgent.load_template("fitness-coach")
coach.specialization = "yoga"
coach.system_prompt = coach.system_prompt.replace(
    "General fitness training",
    "Yoga-focused instruction"
)
```

**Time**: 15 minutes
**Effort**: Moderate
**Result**: Specialized agent

### Pattern 3: Enhanced Agent

Load template, add tools, add knowledge base, add memory:

```python
analyst = SimpleAgent.load_template("data-analyst")
analyst.add_tool(DatabaseTool())
analyst.knowledge_base = RAGSystem("company_docs")
analyst.memory = PersistentMemory()
```

**Time**: 30 minutes
**Effort**: Moderate-High
**Result**: Feature-rich agent

### Pattern 4: Multi-Agent System

Load multiple templates, coordinate with orchestrator:

```python
finance_expert = SimpleAgent.load_template("domain-expert")
finance_expert.domain = "finance"

hr_expert = SimpleAgent.load_template("domain-expert")
hr_expert.domain = "human_resources"

orchestrator = Orchestrator([finance_expert, hr_expert])
```

**Time**: 45 minutes
**Effort**: High
**Result**: Coordinated multi-agent system

## Testing Templates

### Local Testing

Test before integration:

```bash
# Test with CLI
/adk:test templates/fitness-coach-template.py

# Or programmatically
agent = SimpleAgent.load_template("fitness-coach")
test_questions = [
    "What should I do Monday?",
    "I'm a beginner",
    "How many calories?"
]

for q in test_questions:
    print(f"Q: {q}")
    print(f"A: {agent.ask(q)}\n")
```

### Integration Testing

Test in your application context:

```python
# Test with real application data
agent = SimpleAgent.load_template("data-analyst")
results = agent.analyze(your_dataframe)
assert isinstance(results, dict)  # Basic validation
```

## When to Use Templates vs. Custom Agents

**Use Templates When**:
- You want quick results
- Your use case matches a template
- You're learning ADK concepts
- You want working code immediately
- You need a solid foundation to customize

**Use Custom Agents When**:
- Your use case is unique
- You need full control over instructions
- You're building specialized agents
- You have specific requirements
- You want to optimize for your domain

See **adk-custom-agent-builder** skill for building custom agents from scratch.

## Extending Beyond Templates

Templates can be layered with additional features:

**Add Complexity Progressively**:
1. Start with template
2. Test and validate locally
3. Add tools (web search, databases)
4. Integrate knowledge base (RAG)
5. Add persistent memory
6. Deploy to production

See specialized skills for detailed guidance:
- **adk-custom-agent-builder** - Deep customization
- **adk-multi-agent-workflows** - Orchestration
- **adk-knowledge-systems** - RAG integration
- **adk-real-time-agents** - Streaming/voice
- **adk-integration-tools** - External connections
- **adk-production-deployment** - Cloud deployment

## Supporting Resources

### Reference Files
- **`references/template-guide.md`** - Detailed template descriptions, selection matrix, customization examples

### Examples
- **`examples/fitness-coach-demo.py`** - Fitness Coach template usage
- **`examples/researcher-demo.py`** - Research Agent example
- **`examples/tutor-demo.py`** - Teaching Assistant example
- **`examples/domain-expert-demo.py`** - Domain Expert customization
- **`examples/support-agent-demo.py`** - Customer Service setup
- **`examples/analyst-demo.py`** - Data Analyst integration

### Templates
- **`templates/fitness-coach-template.py`** - Full Fitness Coach template code
- **`templates/researcher-template.py`** - Research Agent template
- **`templates/teaching-assistant-template.py`** - Teaching Assistant template
- **`templates/domain-expert-template.py`** - Domain Expert template
- **`templates/customer-service-template.py`** - Customer Service template
- **`templates/data-analyst-template.py`** - Data Analyst template

## Quick Start Command

Initialize a new project with a template:

```bash
/adk:init --template fitness-coach --project-name my-coach
cd my-coach
/adk:test agent.py
```

## Next Steps

1. **Choose a template** from the six available options
2. **Review reference guide** for detailed template descriptions
3. **Load the template** in Python or via CLI
4. **Test locally** with `/adk:test`
5. **Customize** as needed for your use case
6. **Deploy** when ready using production deployment skill

For building entirely custom agents, see **adk-custom-agent-builder** skill.
