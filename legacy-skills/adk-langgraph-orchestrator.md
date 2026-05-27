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

## Related Skills

- **adk-pinecone-rag** - Pinecone-specific RAG pipelines
- **adk-multi-agent-orchestrator** - Native ADK orchestration
- **adk-mcp-integration** - MCP tool configuration
- **adk-deployment-manager** - Deploy LangGraph workflows

## More Information

See LangGraph documentation: https://langchain-ai.github.io/langgraph/
See Google ADK documentation: https://google.github.io/adk-docs/
