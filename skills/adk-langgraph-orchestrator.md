---
name: adk-langgraph-orchestrator
description: Build stateful multi-agent workflows using LangGraph with ADK tools. Patterns include supervisor (agent routing), sequential (pipeline with state), conditional (LLM-powered routing), RAG workflow (vector DB integration), custom graphs, conditional branching (complex decision trees), human-in-the-loop (approval workflows), checkpointing (state persistence and recovery), and streaming integration (real-time LangGraph). Supports state persistence (memory/SQLite/Postgres) and complex state machines.
version: 2.0.0
trigger_keywords:
  - langgraph orchestration
  - stateful workflows
  - conditional branching
  - human-in-the-loop
  - state checkpointing
  - streaming workflows
  - graph-based agents
examples:
  - Complex decision trees
  - Approval workflows
  - State persistence
  - Real-time streaming
references:
  - advanced-patterns.md
templates: []
---

# adk-langgraph-orchestrator

**LangGraph Multi-Agent Orchestration for Google ADK**

Build sophisticated stateful agent workflows using LangGraph with ADK tools. Create complex multi-agent graphs, state machines, and conditional workflows with LLM-powered decision making.

## When to Use

Use this skill when:
- Building stateful multi-step workflows
- Complex conditional agent routing
- Human-in-the-loop approval workflows
- Agent pipelines with state persistence
- Combining LangGraph orchestration with ADK tools

## Quick Start

```bash
# Create LangGraph workflow with ADK
/adk-langgraph-orchestrator --pattern "supervisor" --agents "researcher,writer,reviewer"

# Sequential pipeline with state
/adk-langgraph-orchestrator --pattern "sequential" --steps "intake,process,validate,output"

# Conditional routing graph
/adk-langgraph-orchestrator --pattern "conditional" --router "intent_classifier"

# With Pinecone RAG integration
/adk-langgraph-orchestrator --pattern "rag_workflow" --vector_db "pinecone"
```

## Parameters

```bash
--pattern "supervisor|sequential|conditional|rag_workflow|custom"  # Required
--agents "[agent1, agent2]"           # For supervisor pattern
--steps "[step1, step2]"              # For sequential pattern
--router "router_name"                # For conditional routing
--vector_db "pinecone|qdrant|vertex"  # Vector database integration
--checkpointer "memory|sqlite|postgres"  # State persistence
--human_in_loop true|false            # Enable approval workflows
```

## LangGraph Patterns

### 1. Supervisor Pattern with ADK Tools

Coordinator routes tasks to specialized ADK agents.

```bash
/adk-langgraph-orchestrator --pattern "supervisor" \
  --agents "researcher,analyst,writer" \
  --router "task_router"
```

**Generated Code:**
```python
from typing import Annotated, TypedDict
from typing_extensions import TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# Define workflow state
class WorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    current_agent: str
    task_status: str
    research_data: dict
    analysis_results: dict
    final_output: str

# ADK Researcher Agent
@tool
def research_tool(query: str) -> str:
    """Research information using ADK agent."""
    researcher = Agent(
        name="researcher",
        model="gemini-2.5-flash",
        instruction="Research and gather comprehensive information.",
    )
    # Execute ADK agent
    result = researcher.execute(query)
    return result.content

# ADK Analyst Agent
@tool
def analysis_tool(data: str) -> str:
    """Analyze data using ADK agent."""
    analyst = Agent(
        name="analyst",
        model="gemini-2.5-pro",
        instruction="Analyze data and extract key insights.",
    )
    result = analyst.execute(data)
    return result.content

# ADK Writer Agent
@tool
def writer_tool(content: str, style: str = "professional") -> str:
    """Write content using ADK agent."""
    writer = Agent(
        name="writer",
        model="gemini-2.5-flash",
        instruction=f"Write clear, {style} content.",
    )
    result = writer.execute(content)
    return result.content

# Router function
def route_task(state: WorkflowState) -> str:
    """Route to appropriate agent based on task status."""
    status = state.get("task_status", "research")
    if status == "research":
        return "researcher"
    elif status == "analysis":
        return "analyst"
    elif status == "writing":
        return "writer"
    return END

# Node functions
def researcher_node(state: WorkflowState) -> dict:
    query = state["messages"][-1].content if state["messages"] else ""
    result = research_tool.invoke({"query": query})
    return {
        "research_data": {"findings": result},
        "task_status": "analysis",
        "messages": [AIMessage(content=f"Research complete: {result[:200]}...")]
    }

def analyst_node(state: WorkflowState) -> dict:
    data = str(state.get("research_data", {}))
    result = analysis_tool.invoke({"data": data})
    return {
        "analysis_results": {"insights": result},
        "task_status": "writing",
        "messages": [AIMessage(content=f"Analysis complete: {result[:200]}...")]
    }

def writer_node(state: WorkflowState) -> dict:
    insights = str(state.get("analysis_results", {}))
    result = writer_tool.invoke({"content": insights})
    return {
        "final_output": result,
        "task_status": "complete",
        "messages": [AIMessage(content=f"Final report:\n{result}")]
    }

# Build the graph
builder = StateGraph(WorkflowState)

# Add nodes
builder.add_node("researcher", researcher_node)
builder.add_node("analyst", analyst_node)
builder.add_node("writer", writer_node)

# Add edges with conditional routing
builder.add_edge(START, "researcher")
builder.add_edge("researcher", "analyst")
builder.add_edge("analyst", "writer")
builder.add_edge("writer", END)

# Compile graph
graph = builder.compile()

# Execute workflow
result = graph.invoke({
    "messages": [HumanMessage(content="Research AI agent frameworks")],
    "task_status": "research",
    "research_data": {},
    "analysis_results": {},
    "final_output": "",
    "current_agent": ""
})
```

### 2. Conditional Routing Graph

Route to different agents based on intent classification.

```bash
/adk-langgraph-orchestrator --pattern "conditional" \
  --router "intent_classifier" \
  --agents "support,sales,technical"
```

**Generated Code:**
```python
from typing import Annotated, Literal
from typing_extensions import TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from google.adk.agents import Agent

class RouterState(TypedDict):
    messages: Annotated[list, operator.add]
    intent: str
    response: str

# Intent classifier using ADK
def classify_intent(state: RouterState) -> dict:
    """Classify user intent using Gemini."""
    classifier = Agent(
        name="intent_classifier",
        model="gemini-2.5-flash",
        instruction="""Classify the user intent into one of:
        - support: Customer support issues
        - sales: Sales inquiries, pricing
        - technical: Technical questions, bugs

        Respond with ONLY the category name."""
    )

    user_message = state["messages"][-1].content if state["messages"] else ""
    result = classifier.execute(user_message)
    intent = result.content.strip().lower()

    return {"intent": intent}

# Route based on classified intent
def route_by_intent(state: RouterState) -> Literal["support", "sales", "technical", "fallback"]:
    intent = state.get("intent", "")
    if "support" in intent:
        return "support"
    elif "sales" in intent:
        return "sales"
    elif "technical" in intent:
        return "technical"
    return "fallback"

# Specialized agent nodes
def support_agent(state: RouterState) -> dict:
    agent = Agent(
        name="support_agent",
        model="gemini-2.5-flash",
        instruction="You are a helpful customer support agent. Be empathetic and solution-focused.",
    )
    result = agent.execute(state["messages"][-1].content)
    return {"response": result.content, "messages": [AIMessage(content=result.content)]}

def sales_agent(state: RouterState) -> dict:
    agent = Agent(
        name="sales_agent",
        model="gemini-2.5-flash",
        instruction="You are a friendly sales agent. Focus on value and benefits.",
    )
    result = agent.execute(state["messages"][-1].content)
    return {"response": result.content, "messages": [AIMessage(content=result.content)]}

def technical_agent(state: RouterState) -> dict:
    agent = Agent(
        name="technical_agent",
        model="gemini-2.5-pro",  # More capable model for technical queries
        instruction="You are a technical support engineer. Provide detailed, accurate solutions.",
    )
    result = agent.execute(state["messages"][-1].content)
    return {"response": result.content, "messages": [AIMessage(content=result.content)]}

def fallback_agent(state: RouterState) -> dict:
    return {
        "response": "I'll connect you with the right team. Please hold.",
        "messages": [AIMessage(content="Transferring to appropriate department...")]
    }

# Build conditional graph
builder = StateGraph(RouterState)

# Add nodes
builder.add_node("classifier", classify_intent)
builder.add_node("support", support_agent)
builder.add_node("sales", sales_agent)
builder.add_node("technical", technical_agent)
builder.add_node("fallback", fallback_agent)

# Add edges
builder.add_edge(START, "classifier")
builder.add_conditional_edges(
    "classifier",
    route_by_intent,
    {
        "support": "support",
        "sales": "sales",
        "technical": "technical",
        "fallback": "fallback"
    }
)
builder.add_edge("support", END)
builder.add_edge("sales", END)
builder.add_edge("technical", END)
builder.add_edge("fallback", END)

# Compile
graph = builder.compile()

# Usage
result = graph.invoke({
    "messages": [HumanMessage(content="I'm having trouble logging into my account")],
    "intent": "",
    "response": ""
})
print(result["response"])
```

### 3. RAG Workflow with Pinecone

Integrate Pinecone vector database with LangGraph for RAG pipelines.

```bash
/adk-langgraph-orchestrator --pattern "rag_workflow" \
  --vector_db "pinecone" \
  --embedding_model "multilingual-e5-large"
```

**Generated Code:**
```python
from typing import Annotated, TypedDict, List
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from pinecone import Pinecone, EmbedModel
from google.adk.agents import Agent

# Initialize Pinecone
pc = Pinecone(api_key="YOUR_PINECONE_API_KEY")
index = pc.Index(host="YOUR_INDEX_HOST")

class RAGState(TypedDict):
    messages: Annotated[list, operator.add]
    query: str
    retrieved_context: List[dict]
    response: str

def embed_query(state: RAGState) -> dict:
    """Generate embedding for the query."""
    query = state["messages"][-1].content if state["messages"] else ""

    # Use Pinecone's inference API for embeddings
    embeddings_response = pc.inference.embed(
        model=EmbedModel.Multilingual_E5_Large,
        inputs=[query],
        parameters={"input_type": "query", "truncate": "END"}
    )

    return {
        "query": query,
        "_embedding": embeddings_response.data[0].values
    }

def retrieve_context(state: RAGState) -> dict:
    """Retrieve relevant context from Pinecone."""
    embedding = state.get("_embedding", [])

    # Query Pinecone
    results = index.query(
        vector=embedding,
        top_k=5,
        namespace="documents",
        include_metadata=True
    )

    # Extract context
    contexts = []
    for match in results.matches:
        contexts.append({
            "text": match.metadata.get("text", ""),
            "source": match.metadata.get("source", "unknown"),
            "score": match.score
        })

    return {"retrieved_context": contexts}

def generate_response(state: RAGState) -> dict:
    """Generate response using ADK agent with retrieved context."""
    query = state["query"]
    contexts = state["retrieved_context"]

    # Format context for the agent
    context_text = "\n\n".join([
        f"Source: {ctx['source']}\nContent: {ctx['text']}"
        for ctx in contexts
    ])

    # ADK agent with RAG context
    rag_agent = Agent(
        name="rag_responder",
        model="gemini-2.5-flash",
        instruction=f"""Answer the user's question using the provided context.

Context:
{context_text}

Guidelines:
- Only use information from the provided context
- Cite sources when possible
- If the context doesn't contain relevant information, say so
- Be concise but comprehensive"""
    )

    result = rag_agent.execute(query)

    return {
        "response": result.content,
        "messages": [AIMessage(content=result.content)]
    }

# Build RAG workflow graph
builder = StateGraph(RAGState)

builder.add_node("embed", embed_query)
builder.add_node("retrieve", retrieve_context)
builder.add_node("generate", generate_response)

builder.add_edge(START, "embed")
builder.add_edge("embed", "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

rag_graph = builder.compile()

# Usage
result = rag_graph.invoke({
    "messages": [HumanMessage(content="How do I configure MCP tools in ADK?")],
    "query": "",
    "retrieved_context": [],
    "response": ""
})
print(result["response"])
```

### 4. Human-in-the-Loop Workflow

Workflows with approval checkpoints.

```bash
/adk-langgraph-orchestrator --pattern "supervisor" \
  --human_in_loop true \
  --approval_nodes "review,publish"
```

**Generated Code:**
```python
from typing import Annotated, TypedDict, Literal
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

class ApprovalState(TypedDict):
    messages: Annotated[list, operator.add]
    draft: str
    review_status: Literal["pending", "approved", "rejected"]
    feedback: str
    final_content: str

def generate_draft(state: ApprovalState) -> dict:
    """Generate initial draft using ADK agent."""
    from google.adk.agents import Agent

    writer = Agent(
        name="content_writer",
        model="gemini-2.5-flash",
        instruction="Write professional, engaging content."
    )

    topic = state["messages"][-1].content if state["messages"] else ""
    result = writer.execute(f"Write a draft about: {topic}")

    return {
        "draft": result.content,
        "review_status": "pending",
        "messages": [AIMessage(content=f"Draft ready for review:\n{result.content[:500]}...")]
    }

def human_review(state: ApprovalState) -> dict:
    """Human review checkpoint - graph pauses here for approval."""
    # This node represents where human input is required
    # In practice, the graph will interrupt here
    return state

def check_approval(state: ApprovalState) -> Literal["revise", "publish"]:
    """Route based on review status."""
    if state["review_status"] == "approved":
        return "publish"
    return "revise"

def revise_draft(state: ApprovalState) -> dict:
    """Revise draft based on feedback."""
    from google.adk.agents import Agent

    editor = Agent(
        name="editor",
        model="gemini-2.5-flash",
        instruction="Revise content based on feedback while maintaining quality."
    )

    revision_prompt = f"""
    Original draft: {state['draft']}

    Feedback: {state['feedback']}

    Please revise the draft addressing the feedback.
    """

    result = editor.execute(revision_prompt)

    return {
        "draft": result.content,
        "review_status": "pending",
        "messages": [AIMessage(content="Revision complete, ready for re-review.")]
    }

def publish_content(state: ApprovalState) -> dict:
    """Finalize and publish approved content."""
    return {
        "final_content": state["draft"],
        "messages": [AIMessage(content="Content published successfully!")]
    }

# Build graph with checkpointing
builder = StateGraph(ApprovalState)

builder.add_node("draft", generate_draft)
builder.add_node("review", human_review)
builder.add_node("revise", revise_draft)
builder.add_node("publish", publish_content)

builder.add_edge(START, "draft")
builder.add_edge("draft", "review")
builder.add_conditional_edges(
    "review",
    check_approval,
    {"revise": "revise", "publish": "publish"}
)
builder.add_edge("revise", "review")
builder.add_edge("publish", END)

# Compile with memory checkpointer for state persistence
memory = MemorySaver()
approval_graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["review"]  # Pause before human review
)

# Usage with thread management
config = {"configurable": {"thread_id": "content-123"}}

# Start workflow
result = approval_graph.invoke(
    {
        "messages": [HumanMessage(content="Write about AI agent frameworks")],
        "draft": "",
        "review_status": "pending",
        "feedback": "",
        "final_content": ""
    },
    config=config
)

# Later: Resume with approval
result = approval_graph.invoke(
    {"review_status": "approved"},
    config=config
)
```

### 5. Nested Subgraphs

Compose complex workflows with nested graphs.

```bash
/adk-langgraph-orchestrator --pattern "nested" \
  --outer_graph "main_workflow" \
  --inner_graphs "research_subgraph,analysis_subgraph"
```

**Generated Code:**
```python
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END

# Inner graph: Research subgraph
class ResearchState(TypedDict):
    query: str
    findings: Annotated[list, operator.add]

def web_search(state: ResearchState) -> dict:
    """Search web for information."""
    from google.adk.agents import Agent

    searcher = Agent(
        name="web_searcher",
        model="gemini-2.5-flash",
        instruction="Search and summarize web information."
    )
    result = searcher.execute(state["query"])
    return {"findings": [f"Web: {result.content}"]}

def database_search(state: ResearchState) -> dict:
    """Search internal database."""
    from google.adk.agents import Agent

    db_agent = Agent(
        name="db_searcher",
        model="gemini-2.5-flash",
        instruction="Query internal knowledge base."
    )
    result = db_agent.execute(state["query"])
    return {"findings": [f"Database: {result.content}"]}

# Build research subgraph
research_builder = StateGraph(ResearchState)
research_builder.add_node("web", web_search)
research_builder.add_node("database", database_search)
research_builder.add_edge(START, "web")
research_builder.add_edge(START, "database")  # Parallel execution
research_builder.add_edge("web", END)
research_builder.add_edge("database", END)
research_subgraph = research_builder.compile()

# Inner graph: Analysis subgraph
class AnalysisState(TypedDict):
    data: str
    insights: Annotated[list, operator.add]

def quantitative_analysis(state: AnalysisState) -> dict:
    from google.adk.agents import Agent
    analyst = Agent(
        name="quant_analyst",
        model="gemini-2.5-pro",
        instruction="Perform quantitative analysis."
    )
    result = analyst.execute(state["data"])
    return {"insights": [f"Quantitative: {result.content}"]}

def qualitative_analysis(state: AnalysisState) -> dict:
    from google.adk.agents import Agent
    analyst = Agent(
        name="qual_analyst",
        model="gemini-2.5-pro",
        instruction="Perform qualitative analysis."
    )
    result = analyst.execute(state["data"])
    return {"insights": [f"Qualitative: {result.content}"]}

# Build analysis subgraph
analysis_builder = StateGraph(AnalysisState)
analysis_builder.add_node("quantitative", quantitative_analysis)
analysis_builder.add_node("qualitative", qualitative_analysis)
analysis_builder.add_edge(START, "quantitative")
analysis_builder.add_edge(START, "qualitative")
analysis_builder.add_edge("quantitative", END)
analysis_builder.add_edge("qualitative", END)
analysis_subgraph = analysis_builder.compile()

# Outer graph: Main workflow
class MainState(TypedDict):
    query: str
    research_findings: list
    analysis_insights: list
    final_report: str

def call_research_subgraph(state: MainState) -> dict:
    """Invoke research subgraph."""
    result = research_subgraph.invoke({
        "query": state["query"],
        "findings": []
    })
    return {"research_findings": result["findings"]}

def call_analysis_subgraph(state: MainState) -> dict:
    """Invoke analysis subgraph."""
    data = "\n".join(state["research_findings"])
    result = analysis_subgraph.invoke({
        "data": data,
        "insights": []
    })
    return {"analysis_insights": result["insights"]}

def synthesize_report(state: MainState) -> dict:
    """Create final report from all findings."""
    from google.adk.agents import Agent

    synthesizer = Agent(
        name="report_writer",
        model="gemini-2.5-flash",
        instruction="Synthesize research and analysis into a comprehensive report."
    )

    content = f"""
    Research Findings:
    {chr(10).join(state['research_findings'])}

    Analysis Insights:
    {chr(10).join(state['analysis_insights'])}
    """

    result = synthesizer.execute(f"Create a report from: {content}")
    return {"final_report": result.content}

# Build main workflow
main_builder = StateGraph(MainState)
main_builder.add_node("research", call_research_subgraph)
main_builder.add_node("analysis", call_analysis_subgraph)
main_builder.add_node("synthesize", synthesize_report)

main_builder.add_edge(START, "research")
main_builder.add_edge("research", "analysis")
main_builder.add_edge("analysis", "synthesize")
main_builder.add_edge("synthesize", END)

main_graph = main_builder.compile()

# Execute
result = main_graph.invoke({
    "query": "Impact of AI on software development",
    "research_findings": [],
    "analysis_insights": [],
    "final_report": ""
})
print(result["final_report"])
```

## MCP Integration with LangGraph

Combine LangGraph workflows with ADK MCP tools.

```python
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Create MCP-powered tools
@tool
async def query_database(query: str) -> str:
    """Query SQLite database via MCP."""
    mcp_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command='uvx',
                args=["mcp-server-sqlite", "--db-path", "data.db"],
            ),
        ),
    )
    # Use MCP tool
    result = await mcp_tools.call_tool("query", {"sql": query})
    return str(result)

@tool
async def search_web(query: str) -> str:
    """Search web via Brave MCP."""
    mcp_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command='npx',
                args=["-y", "@anthropic/mcp-server-brave-search"],
                env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")},
            ),
        ),
    )
    result = await mcp_tools.call_tool("search", {"query": query})
    return str(result)

# Use in LangGraph
class MCPWorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    db_results: str
    web_results: str

tool_node = ToolNode(tools=[query_database, search_web])

builder = StateGraph(MCPWorkflowState)
builder.add_node("tools", tool_node)
# ... rest of graph
```

## State Persistence Options

### SQLite Checkpointer (Production)

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Persistent state storage
checkpointer = SqliteSaver.from_conn_string("langgraph_state.db")

graph = builder.compile(checkpointer=checkpointer)

# Resume from any thread
config = {"configurable": {"thread_id": "workflow-abc-123"}}
result = graph.invoke(state, config=config)
```

### PostgreSQL Checkpointer (Scalable)

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost/langgraph"
)

graph = builder.compile(checkpointer=checkpointer)
```

## Generated Project Structure

```
langgraph-adk-workflow/
+-- src/
|   +-- graphs/
|   |   +-- __init__.py
|   |   +-- main_graph.py       # Main workflow graph
|   |   +-- subgraphs/          # Nested subgraphs
|   +-- agents/
|   |   +-- __init__.py
|   |   +-- researcher.py       # ADK agent definitions
|   |   +-- analyst.py
|   |   +-- writer.py
|   +-- tools/
|   |   +-- __init__.py
|   |   +-- mcp_tools.py        # MCP integrations
|   |   +-- rag_tools.py        # RAG tools
|   +-- state/
|   |   +-- __init__.py
|   |   +-- schemas.py          # TypedDict state schemas
|   +-- config.py
|   +-- main.py
+-- tests/
+-- deployment/
|   +-- Dockerfile
|   +-- cloud_run.yaml
+-- requirements.txt
+-- README.md
```

## Requirements

```
# requirements.txt
langgraph>=0.2.0
langchain-core>=0.3.0
google-adk>=1.0.0
pinecone>=5.0.0
```

## Examples

### Example 1: Research Workflow

```bash
$ /adk-langgraph-orchestrator --pattern "supervisor" \
  --agents "researcher,analyst,writer" \
  --checkpointer "sqlite"

LangGraph Workflow Created

Pattern: Supervisor with state persistence
Agents:
- researcher: Gathers information (ADK)
- analyst: Analyzes findings (ADK)
- writer: Creates reports (ADK)

State Management: SQLite persistence
Graph compiled with 4 nodes, 5 edges
```

### Example 2: RAG Pipeline

```bash
$ /adk-langgraph-orchestrator --pattern "rag_workflow" \
  --vector_db "pinecone" \
  --embedding_model "multilingual-e5-large"

RAG Workflow Created

Pipeline:
1. embed: Generate query embedding
2. retrieve: Search Pinecone (top_k=5)
3. generate: ADK agent response

Vector DB: Pinecone
Embedding: multilingual-e5-large
```

## Advanced LangGraph Patterns

### 6. Conditional Branching - Complex Decision Trees

Build sophisticated decision trees with multiple conditional paths.

```python
from typing import Annotated, TypedDict, Literal
import operator
from langgraph.graph import StateGraph, START, END

class DecisionState(TypedDict):
    messages: Annotated[list, operator.add]
    user_type: str
    issue_severity: str
    requires_expert: bool
    resolution: str

def classify_user(state: DecisionState) -> dict:
    """Classify user type."""
    from google.adk.agents import Agent

    classifier = Agent(
        name="user_classifier",
        model="gemini-2.5-flash",
        instruction="Classify user as: FREE, PREMIUM, or ENTERPRISE"
    )

    result = classifier.execute(state["messages"][-1].content)
    return {"user_type": result.content.strip().upper()}

def assess_severity(state: DecisionState) -> dict:
    """Assess issue severity."""
    from google.adk.agents import Agent

    assessor = Agent(
        name="severity_assessor",
        model="gemini-2.5-flash",
        instruction="Classify severity as: LOW, MEDIUM, HIGH, or CRITICAL"
    )

    result = assessor.execute(state["messages"][-1].content)
    severity = result.content.strip().upper()

    return {
        "issue_severity": severity,
        "requires_expert": severity in ["HIGH", "CRITICAL"]
    }

# Conditional routing functions
def route_by_user_type(state: DecisionState) -> Literal["assess_severity", "upgrade_prompt"]:
    """Route based on user type."""
    if state["user_type"] in ["PREMIUM", "ENTERPRISE"]:
        return "assess_severity"
    return "upgrade_prompt"

def route_by_severity(state: DecisionState) -> Literal["auto_resolve", "expert_queue", "escalate"]:
    """Route based on severity."""
    severity = state["issue_severity"]
    user_type = state["user_type"]

    if severity == "CRITICAL" and user_type == "ENTERPRISE":
        return "escalate"
    elif severity in ["HIGH", "CRITICAL"]:
        return "expert_queue"
    return "auto_resolve"

# Handler nodes
def upgrade_prompt_node(state: DecisionState) -> dict:
    """Prompt free users to upgrade."""
    return {
        "resolution": "Please upgrade to Premium for priority support.",
        "messages": [AIMessage(content="Upgrade required for this service.")]
    }

def auto_resolve_node(state: DecisionState) -> dict:
    """Auto-resolve low-severity issues."""
    from google.adk.agents import Agent

    agent = Agent(
        name="auto_resolver",
        instruction="Provide automated solution for common issues."
    )

    result = agent.execute(state["messages"][-1].content)
    return {
        "resolution": result.content,
        "messages": [AIMessage(content=result.content)]
    }

def expert_queue_node(state: DecisionState) -> dict:
    """Queue for expert review."""
    return {
        "resolution": "Queued for expert review. ETA: 1-2 hours.",
        "messages": [AIMessage(content="Expert will review your case shortly.")]
    }

def escalate_node(state: DecisionState) -> dict:
    """Escalate critical enterprise issues."""
    return {
        "resolution": "CRITICAL - Escalated to senior team. Contact within 15 minutes.",
        "messages": [AIMessage(content="Priority escalation initiated.")]
    }

# Build complex decision tree
builder = StateGraph(DecisionState)

builder.add_node("classify_user", classify_user)
builder.add_node("assess_severity", assess_severity)
builder.add_node("upgrade_prompt", upgrade_prompt_node)
builder.add_node("auto_resolve", auto_resolve_node)
builder.add_node("expert_queue", expert_queue_node)
builder.add_node("escalate", escalate_node)

# Decision tree edges
builder.add_edge(START, "classify_user")
builder.add_conditional_edges(
    "classify_user",
    route_by_user_type,
    {
        "assess_severity": "assess_severity",
        "upgrade_prompt": "upgrade_prompt"
    }
)
builder.add_conditional_edges(
    "assess_severity",
    route_by_severity,
    {
        "auto_resolve": "auto_resolve",
        "expert_queue": "expert_queue",
        "escalate": "escalate"
    }
)

# All paths end
builder.add_edge("upgrade_prompt", END)
builder.add_edge("auto_resolve", END)
builder.add_edge("expert_queue", END)
builder.add_edge("escalate", END)

decision_tree = builder.compile()
```

### 7. Human-in-the-Loop - Approval Workflows

Advanced approval workflows with conditional interrupts.

```python
from typing import Annotated, TypedDict, Literal
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

class ApprovalWorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    proposal: str
    estimated_cost: float
    approval_needed: bool
    approved: bool
    approver_feedback: str
    status: str

def create_proposal(state: ApprovalWorkflowState) -> dict:
    """Generate proposal."""
    from google.adk.agents import Agent

    planner = Agent(
        name="proposal_generator",
        model="gemini-2.5-flash",
        instruction="Create detailed project proposal with cost estimate."
    )

    result = planner.execute(state["messages"][-1].content)

    # Extract cost (simplified)
    cost = 5000.0  # In practice, parse from result

    return {
        "proposal": result.content,
        "estimated_cost": cost,
        "approval_needed": cost > 1000,
        "messages": [AIMessage(content=f"Proposal created. Cost: ${cost}")]
    }

def check_approval_needed(state: ApprovalWorkflowState) -> Literal["wait_approval", "execute"]:
    """Check if approval is needed."""
    if state["approval_needed"] and not state["approved"]:
        return "wait_approval"
    return "execute"

def wait_for_approval(state: ApprovalWorkflowState) -> dict:
    """Human approval checkpoint - graph interrupts here."""
    # Graph pauses here for human input
    return {
        "messages": [AIMessage(content="Awaiting approval...")]
    }

def execute_proposal(state: ApprovalWorkflowState) -> dict:
    """Execute approved proposal."""
    from google.adk.agents import Agent

    executor = Agent(
        name="executor",
        instruction="Execute the approved proposal."
    )

    if state.get("approver_feedback"):
        prompt = f"Execute with feedback: {state['approver_feedback']}\n\nProposal: {state['proposal']}"
    else:
        prompt = f"Execute: {state['proposal']}"

    result = executor.execute(prompt)

    return {
        "status": "completed",
        "messages": [AIMessage(content=f"Execution complete: {result.content}")]
    }

def handle_rejection(state: ApprovalWorkflowState) -> dict:
    """Handle rejected proposals."""
    return {
        "status": "rejected",
        "messages": [AIMessage(content=f"Proposal rejected: {state.get('approver_feedback', 'No feedback provided')}")]
    }

# Build approval workflow
builder = StateGraph(ApprovalWorkflowState)

builder.add_node("create_proposal", create_proposal)
builder.add_node("wait_approval", wait_for_approval)
builder.add_node("execute", execute_proposal)
builder.add_node("reject", handle_rejection)

builder.add_edge(START, "create_proposal")
builder.add_conditional_edges(
    "create_proposal",
    check_approval_needed,
    {
        "wait_approval": "wait_approval",
        "execute": "execute"
    }
)

# After approval, check if approved or rejected
def check_approval_status(state: ApprovalWorkflowState) -> Literal["execute", "reject"]:
    return "execute" if state.get("approved") else "reject"

builder.add_conditional_edges(
    "wait_approval",
    check_approval_status,
    {
        "execute": "execute",
        "reject": "reject"
    }
)

builder.add_edge("execute", END)
builder.add_edge("reject", END)

# Compile with checkpointing and interrupt
memory = MemorySaver()
approval_workflow = builder.compile(
    checkpointer=memory,
    interrupt_before=["wait_approval"]  # Pause for human input
)

# Usage
config = {"configurable": {"thread_id": "project-456"}}

# Step 1: Start workflow
result = approval_workflow.invoke(
    {
        "messages": [HumanMessage(content="Plan a website redesign")],
        "proposal": "",
        "estimated_cost": 0.0,
        "approval_needed": False,
        "approved": False,
        "approver_feedback": "",
        "status": "pending"
    },
    config=config
)

# Workflow pauses at wait_approval

# Step 2: Human approves (later)
result = approval_workflow.invoke(
    {
        "approved": True,
        "approver_feedback": "Approved - prioritize mobile-first design"
    },
    config=config
)

# Workflow continues and completes
```

### 8. Checkpointing - State Persistence and Recovery

Robust state persistence with recovery capabilities.

```python
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

class RobustState(TypedDict):
    messages: Annotated[list, operator.add]
    step_completed: Annotated[list, operator.add]
    current_step: str
    data: dict
    errors: Annotated[list, operator.add]

def step_1(state: RobustState) -> dict:
    """First processing step."""
    try:
        # Simulate processing
        result = {"step1_data": "processed"}

        return {
            "step_completed": ["step_1"],
            "current_step": "step_2",
            "data": {**state.get("data", {}), **result},
            "messages": [AIMessage(content="Step 1 complete")]
        }
    except Exception as e:
        return {
            "errors": [f"Step 1 failed: {str(e)}"],
            "current_step": "error_handler"
        }

def step_2(state: RobustState) -> dict:
    """Second processing step."""
    try:
        result = {"step2_data": "processed"}

        return {
            "step_completed": ["step_2"],
            "current_step": "step_3",
            "data": {**state.get("data", {}), **result},
            "messages": [AIMessage(content="Step 2 complete")]
        }
    except Exception as e:
        return {
            "errors": [f"Step 2 failed: {str(e)}"],
            "current_step": "error_handler"
        }

def step_3(state: RobustState) -> dict:
    """Final processing step."""
    try:
        result = {"step3_data": "processed"}

        return {
            "step_completed": ["step_3"],
            "current_step": "complete",
            "data": {**state.get("data", {}), **result},
            "messages": [AIMessage(content="All steps complete")]
        }
    except Exception as e:
        return {
            "errors": [f"Step 3 failed: {str(e)}"],
            "current_step": "error_handler"
        }

def error_handler(state: RobustState) -> dict:
    """Handle errors and determine recovery."""
    completed_steps = state.get("step_completed", [])
    errors = state.get("errors", [])

    return {
        "messages": [
            AIMessage(content=f"Errors occurred: {errors}")
        ],
        "current_step": "failed"
    }

# Build graph with checkpointing
builder = StateGraph(RobustState)

builder.add_node("step_1", step_1)
builder.add_node("step_2", step_2)
builder.add_node("step_3", step_3)
builder.add_node("error_handler", error_handler)

builder.add_edge(START, "step_1")
builder.add_edge("step_1", "step_2")
builder.add_edge("step_2", "step_3")
builder.add_edge("step_3", END)
builder.add_edge("error_handler", END)

# SQLite checkpointer for persistence
checkpointer = SqliteSaver.from_conn_string("workflow_state.db")

robust_workflow = builder.compile(checkpointer=checkpointer)

# Usage with recovery
config = {"configurable": {"thread_id": "robust-workflow-123"}}

# Initial execution
try:
    result = robust_workflow.invoke(
        {
            "messages": [],
            "step_completed": [],
            "current_step": "step_1",
            "data": {},
            "errors": []
        },
        config=config
    )
except Exception as e:
    print(f"Workflow failed: {e}")

# Later: Resume from last checkpoint
# State is automatically recovered from SQLite
result = robust_workflow.invoke(None, config=config)
```

### 9. Streaming Integration - Real-time LangGraph

Stream intermediate results and enable real-time monitoring.

```python
from typing import Annotated, TypedDict, AsyncIterator
import operator
from langgraph.graph import StateGraph, START, END
import asyncio

class StreamingState(TypedDict):
    messages: Annotated[list, operator.add]
    progress: int
    current_task: str
    results: Annotated[list, operator.add]

async def research_step(state: StreamingState) -> dict:
    """Research step with progress updates."""
    from google.adk.agents import Agent

    researcher = Agent(
        name="researcher",
        model="gemini-2.5-flash",
        instruction="Research the topic thoroughly.",
        stream=True  # Enable streaming
    )

    # Simulate streaming research
    chunks = []
    async for chunk in researcher.stream("Research AI agents"):
        chunks.append(chunk)
        # Progress can be monitored in real-time

    result = "".join(chunks)

    return {
        "progress": 33,
        "current_task": "analysis",
        "results": [f"Research: {result}"],
        "messages": [AIMessage(content=f"Research complete")]
    }

async def analysis_step(state: StreamingState) -> dict:
    """Analysis step."""
    from google.adk.agents import Agent

    analyst = Agent(
        name="analyst",
        model="gemini-2.5-pro",
        instruction="Analyze the research findings.",
        stream=True
    )

    chunks = []
    research = state["results"][0] if state["results"] else ""
    async for chunk in analyst.stream(f"Analyze: {research}"):
        chunks.append(chunk)

    result = "".join(chunks)

    return {
        "progress": 66,
        "current_task": "writing",
        "results": [f"Analysis: {result}"],
        "messages": [AIMessage(content="Analysis complete")]
    }

async def writing_step(state: StreamingState) -> dict:
    """Writing step."""
    from google.adk.agents import Agent

    writer = Agent(
        name="writer",
        model="gemini-2.5-flash",
        instruction="Write a comprehensive report.",
        stream=True
    )

    chunks = []
    analysis = state["results"][-1] if state["results"] else ""
    async for chunk in writer.stream(f"Write report from: {analysis}"):
        chunks.append(chunk)

    result = "".join(chunks)

    return {
        "progress": 100,
        "current_task": "complete",
        "results": [f"Report: {result}"],
        "messages": [AIMessage(content="Report complete")]
    }

# Build streaming workflow
builder = StateGraph(StreamingState)

builder.add_node("research", research_step)
builder.add_node("analysis", analysis_step)
builder.add_node("writing", writing_step)

builder.add_edge(START, "research")
builder.add_edge("research", "analysis")
builder.add_edge("analysis", "writing")
builder.add_edge("writing", END)

streaming_workflow = builder.compile()

# Usage with streaming
async def run_with_progress():
    config = {"configurable": {"thread_id": "streaming-789"}}

    # Stream the workflow execution
    async for event in streaming_workflow.astream(
        {
            "messages": [],
            "progress": 0,
            "current_task": "research",
            "results": []
        },
        config=config
    ):
        # Real-time progress updates
        if "progress" in event:
            print(f"Progress: {event['progress']}%")
        if "current_task" in event:
            print(f"Current task: {event['current_task']}")

# Run
asyncio.run(run_with_progress())
```

## Best Practices for Advanced Patterns

### 1. Conditional Branching

- Keep decision logic simple and testable
- Use type hints for routing functions
- Document all possible paths
- Test edge cases thoroughly

### 2. Human-in-the-Loop

- Use `interrupt_before` for approval nodes
- Provide clear context for approvers
- Implement timeout handling
- Support both approval and rejection paths

### 3. Checkpointing

- Always use persistent checkpointers in production (SQLite/Postgres)
- Use unique thread IDs for each workflow instance
- Implement error handling at each node
- Test recovery scenarios

### 4. Streaming

- Use streaming for long-running operations
- Provide progress updates
- Handle streaming errors gracefully
- Test with slow networks

## Related Skills

- **adk-orchestration-patterns** - Fundamental orchestration patterns
- **adk-multi-agent-orchestrator** - Native ADK orchestration
- **adk-mcp-integration** - MCP tool configuration
- **adk-deployment-manager** - Deploy LangGraph workflows

## Reference Documentation

- @advanced-patterns - Advanced LangGraph patterns and examples

## More Information

See LangGraph documentation: https://langchain-ai.github.io/langgraph/
See Google ADK documentation: https://google.github.io/adk-docs/
