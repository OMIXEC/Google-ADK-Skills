# adk-adaptive-agent-generator

**Voice-Driven Custom ADK Agent Generator**

Build production-grade Google ADK agents by describing what you need. Fully autonomous operation with smart defaults - generates complete projects with approval workflow before deployment.

## When to Use

Use this skill when:
- User describes a custom agent requirement in natural language
- User says "build me an agent that...", "create an agent for...", "I need an agent to..."
- User wants a custom agent not covered by existing templates
- User needs to combine multiple capabilities (voice + vision + RAG + tools)

## Quick Start

```bash
# Simple agent
/adk-adaptive-agent-generator Build a customer service agent

# With specific capabilities
/adk-adaptive-agent-generator Create a research assistant with web search and RAG

# Complex multimodal
/adk-adaptive-agent-generator Build a fitness coach that analyzes exercise form with vision
```

## Autonomous Operation

**Maximum 2 questions before generating:**

1. **Question 1** (only if unclear): "What's the agent's primary purpose?"
2. **Question 2** (only if needed): "Deployment target?" (default: Cloud Run)

**Everything else is auto-detected:**
- API keys from environment
- Model selection based on capabilities
- Tool requirements from description
- RAG needs from domain keywords
- Deployment configuration

## Generation Flow

```
User Description
      |
      v
+-------------------------------------+
|     1. INTENT EXTRACTION            |
|  Parse description -> AgentIntent   |
|  - Domain (fitness, support, etc.)  |
|  - Capabilities (voice, vision...)  |
|  - Persona (coach, advisor, etc.)   |
|  - Tools needed                     |
|  - Knowledge requirements           |
+-------------------------------------+
      |
      v
+-------------------------------------+
|     2. CAPABILITY MAPPING           |
|  Map requirements -> ADK patterns   |
|  - Agent type (Agent, LlmAgent)     |
|  - Multi-agent (AgentTool, Seq.)    |
|  - MCP servers needed               |
|  - RAG corpus configuration         |
+-------------------------------------+
      |
      v
+-------------------------------------+
|     3. ARCHITECTURE DESIGN          |
|  Design complete agent system       |
|  - Agent hierarchy                  |
|  - Tool integrations                |
|  - Instruction templates            |
|  - Deployment strategy              |
+-------------------------------------+
      |
      v
+-------------------------------------+
|     4. CODE GENERATION              |
|  Apply Jinja2 templates             |
|  - agent.py (main agent)            |
|  - tools/*.py (function tools)      |
|  - config.py (smart config)         |
|  - main.py (FastAPI wrapper)        |
|  - Dockerfile, deployment           |
+-------------------------------------+
      |
      v
+-------------------------------------+
|     5. USER APPROVAL                |
|  Show architecture and code         |
|  Approve -> Generate project        |
|  Modify -> Adjust requirements      |
|  Cancel -> No code created          |
+-------------------------------------+
      |
      v
   Complete Project Generated
```

## Intent Extraction

### Supported Domains

| Domain | Keywords | Auto-Selected Tools |
|--------|----------|---------------------|
| Customer Service | support, help, service, tickets | search, database |
| Research | research, search, academic, papers | web_search, rag |
| Fitness | fitness, exercise, workout, form | vision, exercise_db |
| Healthcare | health, medical, symptoms | rag, safety_protocols |
| Education | teach, tutor, learn, explain | rag, quiz_generator |
| Coding | code, debug, review, programming | code_execution, github |
| Finance | finance, budget, investment | calculation, market_data |
| Creative | write, story, creative, content | text_generation |

### Capability Detection

| Capability | Keywords | ADK Pattern |
|------------|----------|-------------|
| Voice | voice, speak, conversation, talk | TTS/STT integration |
| Vision | see, look, image, camera, analyze | Vision model + tools |
| RAG | knowledge, documents, search | VertexAiRagRetrieval |
| Multi-Agent | team, specialists, coordinate | AgentTool delegation |
| Tools | search, database, api, calculate | MCPToolset / FunctionTool |
| Real-time | live, streaming, real-time | LiveRequestQueue |

### Persona Detection

| Persona | Keywords | Interaction Style |
|---------|----------|-------------------|
| Coach | coach, trainer, motivate | Encouraging, direct |
| Advisor | advisor, consultant, recommend | Professional, analytical |
| Tutor | tutor, teacher, explain | Patient, educational |
| Assistant | assistant, helper, support | Helpful, efficient |
| Expert | expert, specialist, professional | Authoritative, detailed |
| Companion | friend, buddy, chat | Casual, empathetic |

## Generated Project Structure

```
my-adk-agent/
+-- src/
|   +-- __init__.py
|   +-- agent.py                 # Main agent definition
|   +-- config.py                # Smart configuration
|   +-- prompts.py               # Agent instructions
|   +-- main.py                  # FastAPI wrapper
|   |
|   +-- tools/                   # Function tools
|   |   +-- __init__.py
|   |   +-- domain_tools.py      # Domain-specific tools
|   |   +-- mcp_config.py        # MCP server setup
|   |
|   +-- rag/                     # RAG configuration (if needed)
|       +-- __init__.py
|       +-- corpus_setup.py
|
+-- tests/
|   +-- __init__.py
|   +-- test_agent.py
|   +-- test_tools.py
|
+-- deployment/
|   +-- Dockerfile
|   +-- cloudbuild.yaml
|   +-- cloud_run.yaml
|   +-- agent_engine.yaml
|
+-- .env.example
+-- pyproject.toml
+-- README.md
+-- requirements.txt
```

## Generated Code Examples

### Simple Agent

**Input:** "Build a customer service agent"

**Generated agent.py:**
```python
# src/agent.py
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from tools.domain_tools import search_faq, create_ticket, get_order_status

instruction = """
You are a helpful customer service agent.

**Role:** Assist customers with inquiries, orders, and support tickets.

**Communication Style:** Professional, friendly, efficient.

**Behavior Guidelines:**
1. Greet customers warmly and identify their needs quickly
2. Search FAQs before escalating to human support
3. Create support tickets for complex issues
4. Provide order status when requested
5. Always confirm next steps before ending conversation

**Tools Available:**
- search_faq: Search knowledge base for answers
- create_ticket: Create support ticket for escalation
- get_order_status: Check order status by order ID
"""

customer_service_agent = Agent(
    name="customer_service_agent",
    model="gemini-2.5-flash",
    description="Customer service agent for support inquiries",
    instruction=instruction,
    tools=[
        FunctionTool(search_faq),
        FunctionTool(create_ticket),
        FunctionTool(get_order_status),
    ],
)

root_agent = customer_service_agent
```

### Multimodal Agent with Vision

**Input:** "Build a fitness coach that analyzes exercise form with vision"

**Generated agent.py:**
```python
# src/agent.py
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from tools.fitness_tools import analyze_form, suggest_exercise, track_workout
from tools.vision_tools import process_image, detect_pose

instruction = """
You are a certified fitness coach specializing in form analysis.

**Role:** Analyze exercise form from images/video and provide corrections.

**Personality:** Motivational, safety-focused, encouraging.

**Communication Style:** Direct, actionable, supportive.

**Behavior Guidelines:**
1. ALWAYS prioritize safety - correct poor form immediately
2. Use spatial language for corrections ("lower hips 2 inches", "widen stance")
3. Celebrate progress and good form
4. Suggest modifications for different fitness levels
5. Warn about injury risks with improper form

**Vision Analysis Protocol:**
When analyzing exercise form:
1. Identify the exercise being performed
2. Check joint angles and alignment
3. Assess balance and stability
4. Identify any form issues
5. Provide specific, actionable corrections

**Tools Available:**
- analyze_form: Detailed form analysis from image/description
- process_image: Process uploaded image for analysis
- detect_pose: Detect body pose and joint positions
- suggest_exercise: Recommend exercises for specific goals
- track_workout: Log workout progress
"""

fitness_coach_agent = Agent(
    name="fitness_coach",
    model="gemini-2.5-flash",
    description="Fitness coach with vision-based form analysis",
    instruction=instruction,
    tools=[
        FunctionTool(analyze_form),
        FunctionTool(process_image),
        FunctionTool(detect_pose),
        FunctionTool(suggest_exercise),
        FunctionTool(track_workout),
    ],
)

root_agent = fitness_coach_agent
```

### Multi-Agent Research System

**Input:** "Create a research assistant with web search, analysis, and synthesis"

**Generated agent.py:**
```python
# src/agent.py
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from tools.search_tools import web_search, academic_search
from tools.analysis_tools import summarize_content, extract_key_points

# Specialist: Research Agent
research_agent = Agent(
    name="researcher",
    model="gemini-2.5-flash",
    description="Searches and gathers information from multiple sources",
    instruction="""
    You are a research specialist. Your job is to:
    1. Search web and academic sources for relevant information
    2. Gather comprehensive data on the topic
    3. Identify credible sources and note citations
    4. Return raw findings for analysis
    """,
    tools=[
        FunctionTool(web_search),
        FunctionTool(academic_search),
    ],
)

# Specialist: Analysis Agent
analysis_agent = Agent(
    name="analyst",
    model="gemini-2.5-pro",  # Better reasoning for analysis
    description="Analyzes research findings and extracts insights",
    instruction="""
    You are an analysis specialist. Your job is to:
    1. Review research findings critically
    2. Identify patterns, themes, and key insights
    3. Source credibility assessment
    4. Highlight contradictions or gaps
    5. Organize findings logically
    """,
    tools=[
        FunctionTool(summarize_content),
        FunctionTool(extract_key_points),
    ],
)

# Specialist: Synthesis Agent
synthesis_agent = Agent(
    name="synthesizer",
    model="gemini-2.5-flash",
    description="Synthesizes analysis into coherent response",
    instruction="""
    You are a synthesis specialist. Your job is to:
    1. Combine analyzed findings into a coherent narrative
    2. Write clear, well-structured responses
    3. Include proper citations
    4. Highlight key takeaways
    5. Suggest areas for further research
    """,
)

# Coordinator using AgentTool delegation
coordinator = Agent(
    name="research_coordinator",
    model="gemini-2.5-flash",
    description="Coordinates research team for comprehensive answers",
    instruction="""
    You are a research coordinator managing a team of specialists.

    **Team Members:**
    - researcher: Gathers information from web and academic sources
    - analyst: Analyzes findings and extracts insights
    - synthesizer: Creates coherent, well-cited responses

    **Workflow:**
    1. For research queries, delegate to researcher first
    2. Pass findings to analyst for critical review
    3. Have synthesizer create final response
    4. Review and deliver to user

    Always use the full team for comprehensive research.
    For simple questions, answer directly.
    """,
    tools=[
        AgentTool(agent=research_agent),
        AgentTool(agent=analysis_agent),
        AgentTool(agent=synthesis_agent),
    ],
)

root_agent = coordinator
```

### Agent with RAG

**Input:** "Build a documentation assistant for our product docs"

**Generated agent.py:**
```python
# src/agent.py
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai import rag
from config import RAG_CORPUS_NAME

instruction = """
You are a documentation assistant for our product.

**Role:** Help users find answers in our documentation.

**Behavior Guidelines:**
1. Always search the knowledge base before answering
2. Cite specific documentation sections
3. Provide step-by-step instructions when helpful
4. Suggest related documentation for further reading
5. Admit when information is not in the docs

**Response Format:**
- Start with a direct answer
- Include relevant code examples
- Link to full documentation
- Suggest related topics
"""

docs_assistant = Agent(
    name="docs_assistant",
    model="gemini-2.5-flash",
    description="Documentation assistant with RAG knowledge base",
    instruction=instruction,
    tools=[
        VertexAiRagRetrieval(
            name="search_docs",
            description="Search product documentation",
            rag_resources=[
                rag.RagResource(rag_corpus=RAG_CORPUS_NAME)
            ],
            similarity_top_k=10,
            vector_distance_threshold=0.3,
        ),
    ],
)

root_agent = docs_assistant
```

### Agent with MCP Tools

**Input:** "Create an agent that can search the web and access databases"

**Generated agent.py:**
```python
# src/agent.py
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Web Search MCP
search_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@anthropic/mcp-server-brave-search"],
            env={"BRAVE_API_KEY": "${BRAVE_API_KEY}"},
        ),
    ),
)

# Database MCP
database_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='uvx',
            args=["mcp-server-sqlite", "--db-path", "data/app.db"],
        ),
    ),
)

instruction = """
You are a data analyst assistant with access to web search and database.

**Capabilities:**
- Search the web for current information
- Query the database for stored data
- Combine external and internal data for insights

**Behavior Guidelines:**
1. Use web search for current events and external data
2. Use database for historical and internal data
3. Cross-reference sources when possible
4. Clearly distinguish between web and database sources
"""

data_analyst = Agent(
    name="data_analyst",
    model="gemini-2.5-flash",
    description="Data analyst with web search and database access",
    instruction=instruction,
    tools=[search_toolset, database_toolset],
)

root_agent = data_analyst
```

## Generated Configuration

### config.py (Smart Defaults)

```python
# src/config.py
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AgentConfig:
    """Smart configuration with environment auto-detection."""

    # Model Configuration
    model: str = "gemini-2.5-flash"
    reasoning_model: str = "gemini-2.5-pro"

    # API Keys (auto-detected from environment)
    google_api_key: Optional[str] = None

    # RAG Configuration
    rag_corpus_name: Optional[str] = None
    rag_similarity_top_k: int = 10

    # Deployment
    deployment_target: str = "cloud-run"  # cloud-run, agent-engine, gke, local
    port: int = 8080

    # Logging
    log_level: str = "INFO"

    def __post_init__(self):
        # Auto-detect API keys
        self.google_api_key = self.google_api_key or os.getenv("GOOGLE_API_KEY")

        # Auto-detect RAG corpus
        self.rag_corpus_name = self.rag_corpus_name or os.getenv("RAG_CORPUS_NAME")

        # Validate required keys
        if not self.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY required. Set via environment or config."
            )

def get_config() -> AgentConfig:
    """Get configuration with smart defaults."""
    return AgentConfig()

# Export commonly used values
config = get_config()
MODEL = config.model
REASONING_MODEL = config.reasoning_model
RAG_CORPUS_NAME = config.rag_corpus_name
```

### main.py (FastAPI Wrapper)

```python
# src/main.py
from google.adk.endpoints import get_fast_api_app
from agent import root_agent
from config import config
import uvicorn

# Create FastAPI app with ADK wrapper
app = get_fast_api_app(agent=root_agent)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": root_agent.name}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.port,
        reload=True,
    )
```

## Deployment Templates

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Cloud Run Deployment

```yaml
# deployment/cloud_run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ${AGENT_NAME}
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containers:
        - image: gcr.io/${PROJECT_ID}/${AGENT_NAME}
          ports:
            - containerPort: 8080
          env:
            - name: GOOGLE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: google-api-key
                  key: latest
          resources:
            limits:
              memory: "2Gi"
              cpu: "2"
```

## Approval Workflow

After generating the architecture and code, present to user:

```
=== ADK Agent Generation Complete ===

Agent: fitness_coach
Domain: Fitness / Exercise Form Analysis
Capabilities: Vision, Voice, RAG

Architecture:
+-------------------------------------+
|         fitness_coach               |
|    (gemini-2.5-flash)               |
+-------------------------------------+
| Tools:                              |
|  - analyze_form (vision)            |
|  - detect_pose (vision)             |
|  - suggest_exercise (domain)        |
|  - track_workout (domain)           |
+-------------------------------------+
| Knowledge: Exercise library (RAG)   |
| Deployment: Cloud Run               |
+-------------------------------------+

Generated Files:
+-- src/agent.py (145 lines)
+-- src/config.py (52 lines)
+-- src/main.py (28 lines)
+-- src/tools/fitness_tools.py (89 lines)
+-- src/tools/vision_tools.py (67 lines)
+-- deployment/Dockerfile
+-- deployment/cloud_run.yaml
+-- README.md

**What Happens Next:**
[Approve] Full project generated to ./fitness-coach-agent/
[Modify] Adjust capabilities, tools, or deployment
[Cancel] No code created

Approve? [Yes/Modify/Cancel]
```

## Examples

### Example 1: Simple Customer Support

```bash
$ /adk-adaptive-agent-generator Build a customer support chatbot

Intent Detected:
- Domain: Customer Service
- Capabilities: Text chat
- Persona: Support Assistant
- Tools: FAQ search, ticket creation

Generating agent...

Agent Generated: customer_support_agent
- Model: gemini-2.5-flash
- Tools: search_faq, create_ticket, get_order_status
- Deployment: Cloud Run ready
```

### Example 2: Research Assistant with RAG

```bash
$ /adk-adaptive-agent-generator Create a research assistant that searches academic papers and synthesizes findings

Intent Detected:
- Domain: Research
- Capabilities: RAG, Multi-agent
- Persona: Research Expert
- Tools: Academic search, web search, synthesis

Generating multi-agent system...

Multi-Agent System Generated:
- Coordinator: research_coordinator (gemini-2.5-flash)
- Specialist: researcher (gemini-2.5-flash + search tools)
- Specialist: analyst (gemini-2.5-pro + analysis tools)
- Specialist: synthesizer (gemini-2.5-flash)
- Pattern: AgentTool delegation
```

### Example 3: Vision-Enabled Quality Inspector

```bash
$ /adk-adaptive-agent-generator Build an agent that inspects product images for defects

Intent Detected:
- Domain: Quality Control
- Capabilities: Vision, Analysis
- Persona: Quality Expert
- Tools: Image analysis, defect detection

Generating vision agent...

Agent Generated: quality_inspector
- Model: gemini-2.5-flash (vision-enabled)
- Tools: analyze_image, detect_defects, classify_severity
- Vision Protocol: Defect detection workflow
```

## Related Skills

- **adk-persona-builder** - Use pre-built persona templates
- **adk-domain-expert-builder** - Create specialized domain experts
- **adk-multi-agent-orchestrator** - Build complex multi-agent systems
- **adk-mcp-integration** - Add MCP tool integrations
- **adk-rag-builder** - Configure Vertex AI RAG
- **adk-deployment-manager** - Deploy to production

## More Information

See CLAUDE.md for ADK architecture patterns and best practices.
See MCP Server Catalog for available tool integrations.
