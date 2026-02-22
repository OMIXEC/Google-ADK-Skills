# ADK Simple Agent Templates Guide

## Available Templates

The ADK Simple Agents skill provides 6 pre-configured agent templates. Each template is production-ready and can be used as-is or customized for specific needs.

### Template 1: Fitness Coach Agent

**Purpose**: Provides personalized fitness advice, workout recommendations, and health guidance.

**Key Characteristics**:
- Conversational and motivational tone
- Knowledge of exercise physiology and fitness
- Personalization based on user profile (age, fitness level, goals)
- Tool access: fitness calculations, workout database

**Best For**:
- Fitness app integration
- Personal training assistance
- Health coaching services
- Wellness programs

**Customization Options**:
- Modify tone (strict vs. encouraging)
- Add specific fitness specializations (yoga, bodybuilding, etc.)
- Integrate with wearable APIs
- Add nutrition guidance

**Example Usage**:
```python
from adk_bidi.agents import SimpleAgent

coach = SimpleAgent.load_template("fitness-coach")
coach.personality = "motivational"  # or "strict", "educational"
response = coach.ask("Create a Monday workout for beginners")
```

---

### Template 2: Research Agent

**Purpose**: Conducts web research, summarizes findings, and organizes information.

**Key Characteristics**:
- Systematic research methodology
- Source verification and credibility assessment
- Structured summaries with citations
- Deep dive capability for complex topics

**Best For**:
- Academic research assistance
- Market research
- Competitive analysis
- Due diligence investigations

**Customization Options**:
- Focus area (academic, industry, general)
- Source types (academic papers, news, blogs)
- Output format (bullet points, essays, reports)
- Research depth (quick overview vs. comprehensive)

**Example Usage**:
```python
researcher = SimpleAgent.load_template("researcher")
researcher.focus = "academic"
findings = researcher.research("Latest advances in quantum computing")
```

---

### Template 3: Teaching Assistant Agent

**Purpose**: Explains concepts, answers questions, and supports learning.

**Key Characteristics**:
- Pedagogical approach (tailored to learner level)
- Multiple explanation styles (analogies, examples, visuals)
- Question generation for self-assessment
- Learning pathway guidance

**Best For**:
- Educational platforms
- Tutoring systems
- Corporate training
- Self-study support

**Customization Options**:
- Student level (elementary, high school, university, professional)
- Subject domain specialization
- Explanation style preference
- Assessment methods

**Example Usage**:
```python
tutor = SimpleAgent.load_template("teaching-assistant")
tutor.level = "high-school"
tutor.subject = "mathematics"
explanation = tutor.explain("quadratic equations")
```

---

### Template 4: Domain Expert Agent

**Purpose**: Provides specialized expertise in a specific domain.

**Key Characteristics**:
- Deep domain knowledge
- Expert reasoning patterns
- Best practices and standards knowledge
- Professional vocabulary and standards

**Best For**:
- Professional consulting
- Technical support
- Industry-specific applications
- Expert systems

**Customization Options**:
- Domain selection (legal, medical, engineering, finance, etc.)
- Expertise level (general vs. specialized subcategory)
- Communication style (formal vs. accessible)
- Regulatory awareness

**Example Usage**:
```python
expert = SimpleAgent.load_template("domain-expert")
expert.domain = "medical"
expert.specialty = "cardiology"
advice = expert.provide_guidance("Heart disease prevention strategies")
```

---

### Template 5: Customer Service Agent

**Purpose**: Handles customer inquiries, resolves issues, and provides support.

**Key Characteristics**:
- Empathetic and professional tone
- Issue classification and routing
- Escalation protocols
- Resolution tracking

**Best For**:
- Customer support systems
- Help desk automation
- Account management
- Complaint resolution

**Customization Options**:
- Industry (software, retail, hospitality, etc.)
- Support level (tier 1, tier 2, tier 3)
- Escalation rules
- Knowledge base integration

**Example Usage**:
```python
support = SimpleAgent.load_template("customer-service")
support.industry = "software"
support.tone = "friendly"
response = support.handle_inquiry("How do I reset my password?")
```

---

### Template 6: Data Analyst Agent

**Purpose**: Analyzes data and generates insights and visualizations.

**Key Characteristics**:
- Statistical reasoning
- Data interpretation
- Trend identification
- Actionable recommendations

**Best For**:
- Business intelligence
- Data exploration
- Report generation
- Decision support

**Customization Options**:
- Data type specialization (financial, operational, marketing, etc.)
- Analysis depth (summary vs. detailed)
- Visualization preferences
- Audience level (technical vs. executive)

**Example Usage**:
```python
analyst = SimpleAgent.load_template("data-analyst")
analyst.data_type = "financial"
analyst.audience = "executive"
insights = analyst.analyze(dataframe)
```

---

## Using Templates

### Quick Start

1. **Load Template**:
```python
from adk_bidi.agents import SimpleAgent

agent = SimpleAgent.load_template("fitness-coach")
```

2. **Customize (Optional)**:
```python
agent.personality = "motivational"
agent.add_tool("wearable_api_integration")
```

3. **Test**:
```python
response = agent.ask("What's a good beginner workout?")
print(response)
```

4. **Deploy**:
Use `/adk:init` to scaffold a project with the template, then deploy with production deployment skill.

### Customization Patterns

**Change Tone**:
```python
agent.tone = "formal"  # or "casual", "technical", "friendly"
```

**Add Tools**:
```python
agent.add_tool("web_search")
agent.add_tool("document_processing")
```

**Modify Instructions**:
```python
agent.system_prompt = agent.system_prompt.replace(
    "current behavior",
    "new behavior"
)
```

**Integrate Data**:
```python
agent.knowledge_base = load_documents("path/to/docs")
agent.memory = load_persistent_memory()
```

---

## Template Selection Matrix

| Goal | Best Template | Why |
|------|---------------|-----|
| Fitness app | Fitness Coach | Pre-configured fitness knowledge |
| Research tool | Researcher | Systematic research methodology |
| Learning platform | Teaching Assistant | Pedagogical approach |
| Expert consulting | Domain Expert | Deep domain knowledge |
| Support system | Customer Service | Issue handling and empathy |
| Analytics dashboard | Data Analyst | Statistical reasoning |

---

## Extending Templates

Templates are starting points. Extend them by:

1. **Adding Tools**: Give agent access to new capabilities
2. **Integrating Knowledge**: Connect to RAG systems, databases
3. **Multi-Agent Coordination**: Template can become specialist in orchestration
4. **Real-Time Features**: Add streaming or voice interaction
5. **Custom Training**: Fine-tune with domain-specific examples

See specialized skills for detailed guidance:
- **adk-custom-agent-builder** for deep customization
- **adk-multi-agent-workflows** for orchestration
- **adk-knowledge-systems** for RAG integration
- **adk-real-time-agents** for streaming/voice
- **adk-integration-tools** for external connections

---

## Common Template Modifications

### Add Web Search to Any Template

```python
agent.add_tool("brave_search", api_key=os.getenv("BRAVE_API_KEY"))
```

### Add Document Processing to Any Template

```python
from adk_bidi.memory import RAGSystem

rag = RAGSystem(documents_path="path/to/docs")
agent.knowledge_base = rag
```

### Add Memory to Any Template

```python
from adk_bidi.memory import PersistentMemory

memory = PersistentMemory(
    storage="pinecone",
    api_key=os.getenv("PINECONE_API_KEY")
)
agent.memory = memory
```

### Convert Template to Multi-Agent

```python
# Create multiple specialized agents from templates
finance_expert = SimpleAgent.load_template("domain-expert")
finance_expert.domain = "finance"

hr_expert = SimpleAgent.load_template("domain-expert")
hr_expert.domain = "human_resources"

# Coordinate with orchestration (see adk-multi-agent-workflows)
coordinator = Orchestrator([finance_expert, hr_expert])
```

---

## Testing Templates

### Local Testing

```bash
# Test a template before customizing
python -c "
from adk_bidi.agents import SimpleAgent
agent = SimpleAgent.load_template('fitness-coach')
print(agent.ask('Beginner workout?'))
"

# Or use the CLI command
/adk:test templates/fitness-coach-example.py
```

### Integration Testing

Load template in your application and test with real scenarios.

---

## Next Steps

1. **Choose a template** that matches your use case
2. **Test it locally** with `/adk:test`
3. **Customize** as needed for your specific requirements
4. **Integrate** into your application or service
5. **Extend** with additional features (RAG, multi-agent, real-time)

For more detailed customization guidance, see the **adk-custom-agent-builder** skill.
