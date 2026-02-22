# Advanced LangGraph Patterns Reference

## Overview

This reference covers advanced LangGraph patterns for building sophisticated stateful workflows with ADK agents. Patterns include complex conditional branching, human-in-the-loop approvals, state checkpointing, and streaming integration.

---

## Pattern 1: Conditional Branching

### Concept

Build complex decision trees with multiple conditional routing paths based on state analysis.

### When to Use

- **Multi-criteria routing**: Decisions based on multiple factors
- **Tiered service levels**: Different paths for different user tiers
- **Dynamic workflows**: Adapt flow based on intermediate results
- **Business rules**: Implement complex business logic

### Core Components

```python
from typing import Literal, TypedDict
from langgraph.graph import StateGraph, START, END

# 1. State definition with decision factors
class DecisionState(TypedDict):
    user_tier: str          # Decision factor 1
    request_urgency: str    # Decision factor 2
    estimated_cost: float   # Decision factor 3
    # ... other state

# 2. Routing functions with type hints
def route_by_tier(state: DecisionState) -> Literal["premium_path", "basic_path"]:
    """Type-safe routing function."""
    if state["user_tier"] in ["PREMIUM", "ENTERPRISE"]:
        return "premium_path"
    return "basic_path"

# 3. Nested conditional routing
def route_by_urgency(state: DecisionState) -> Literal["urgent", "normal", "low_priority"]:
    """Multi-way routing."""
    urgency = state["request_urgency"]
    if urgency == "CRITICAL":
        return "urgent"
    elif urgency == "HIGH":
        return "normal"
    return "low_priority"

# 4. Complex routing logic
def route_by_multiple_factors(state: DecisionState) -> Literal["path_a", "path_b", "path_c"]:
    """Route based on multiple factors."""
    tier = state["user_tier"]
    urgency = state["request_urgency"]
    cost = state["estimated_cost"]

    # Complex business logic
    if tier == "ENTERPRISE" and urgency == "CRITICAL":
        return "path_a"  # VIP fast track
    elif cost > 10000:
        return "path_b"  # Approval required
    else:
        return "path_c"  # Standard processing
```

### Example: Support Ticket Routing

```python
from typing import Annotated, TypedDict, Literal
import operator
from langgraph.graph import StateGraph, START, END
from google.adk.agents import Agent

class TicketState(TypedDict):
    messages: Annotated[list, operator.add]
    user_tier: str
    issue_type: str
    severity: str
    assigned_team: str
    resolution: str

# Classification nodes
def classify_user_tier(state: TicketState) -> dict:
    """Determine user tier."""
    classifier = Agent(
        name="tier_classifier",
        model="gemini-2.5-flash",
        instruction="Classify user as: FREE, BASIC, PREMIUM, or ENTERPRISE"
    )

    result = classifier.execute(state["messages"][-1].content)
    return {"user_tier": result.content.strip().upper()}

def classify_issue(state: TicketState) -> dict:
    """Classify issue type and severity."""
    classifier = Agent(
        name="issue_classifier",
        model="gemini-2.5-flash",
        instruction="""
        Classify the issue:
        Type: TECHNICAL, BILLING, ACCOUNT, FEATURE_REQUEST
        Severity: LOW, MEDIUM, HIGH, CRITICAL

        Output format: TYPE|SEVERITY
        """
    )

    result = classifier.execute(state["messages"][-1].content)
    issue_type, severity = result.content.strip().upper().split("|")

    return {
        "issue_type": issue_type,
        "severity": severity
    }

# Routing functions
def route_by_tier_and_severity(state: TicketState) -> Literal["vip_team", "standard_team", "basic_support", "self_service"]:
    """Route based on tier and severity."""
    tier = state["user_tier"]
    severity = state["severity"]

    # VIP treatment for enterprise critical issues
    if tier == "ENTERPRISE" and severity == "CRITICAL":
        return "vip_team"

    # Premium gets standard team for high severity
    if tier == "PREMIUM" and severity in ["HIGH", "CRITICAL"]:
        return "standard_team"

    # Basic tier gets standard support for critical only
    if tier == "BASIC" and severity == "CRITICAL":
        return "standard_team"

    # Free tier gets self-service
    if tier == "FREE":
        return "self_service"

    # Default to basic support
    return "basic_support"

# Team handler nodes
def vip_team_handler(state: TicketState) -> dict:
    """VIP team - immediate response."""
    return {
        "assigned_team": "VIP Team",
        "resolution": "Critical enterprise issue - immediate attention. ETA: 15 minutes.",
        "messages": [AIMessage(content="Escalated to VIP team")]
    }

def standard_team_handler(state: TicketState) -> dict:
    """Standard team - priority response."""
    return {
        "assigned_team": "Standard Team",
        "resolution": "Priority ticket queued. ETA: 1-2 hours.",
        "messages": [AIMessage(content="Assigned to standard team")]
    }

def basic_support_handler(state: TicketState) -> dict:
    """Basic support - automated assistance."""
    agent = Agent(
        name="support_agent",
        instruction="Provide automated support solutions."
    )

    result = agent.execute(state["messages"][-1].content)

    return {
        "assigned_team": "Automated Support",
        "resolution": result.content,
        "messages": [AIMessage(content=result.content)]
    }

def self_service_handler(state: TicketState) -> dict:
    """Self-service - knowledge base."""
    return {
        "assigned_team": "Self-Service",
        "resolution": "Please visit our knowledge base for solutions: help.example.com",
        "messages": [AIMessage(content="Redirected to self-service")]
    }

# Build decision tree
builder = StateGraph(TicketState)

builder.add_node("classify_tier", classify_user_tier)
builder.add_node("classify_issue", classify_issue)
builder.add_node("vip_team", vip_team_handler)
builder.add_node("standard_team", standard_team_handler)
builder.add_node("basic_support", basic_support_handler)
builder.add_node("self_service", self_service_handler)

# Build decision tree
builder.add_edge(START, "classify_tier")
builder.add_edge("classify_tier", "classify_issue")
builder.add_conditional_edges(
    "classify_issue",
    route_by_tier_and_severity,
    {
        "vip_team": "vip_team",
        "standard_team": "standard_team",
        "basic_support": "basic_support",
        "self_service": "self_service"
    }
)

# All paths end
for node in ["vip_team", "standard_team", "basic_support", "self_service"]:
    builder.add_edge(node, END)

ticket_router = builder.compile()
```

### Best Practices

1. **Use Type Hints:** `Literal["path_a", "path_b"]` for type safety
2. **Keep Routing Functions Pure:** No side effects, only decisions
3. **Document All Paths:** Clear comments for each routing branch
4. **Test Edge Cases:** Ensure all combinations are handled
5. **Limit Complexity:** Max 3-4 routing factors per function

---

## Pattern 2: Human-in-the-Loop

### Concept

Workflows that pause for human approval or input at critical checkpoints.

### When to Use

- **Approval workflows**: Budget approvals, content publication
- **Quality gates**: Manual verification before proceeding
- **Exception handling**: Human intervention for edge cases
- **Compliance**: Required human oversight

### Core Components

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 1. State with approval fields
class ApprovalState(TypedDict):
    content: str
    approval_needed: bool
    approved: bool
    approver_feedback: str
    status: str

# 2. Checkpoint configuration
memory = MemorySaver()
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["approval_checkpoint"]  # Pause here
)

# 3. Approval checkpoint node
def approval_checkpoint(state: ApprovalState) -> dict:
    """Graph pauses here for human input."""
    return {
        "status": "awaiting_approval",
        "messages": [AIMessage(content="Awaiting human approval...")]
    }

# 4. Conditional routing after approval
def check_approval(state: ApprovalState) -> Literal["approved_path", "rejected_path"]:
    if state.get("approved"):
        return "approved_path"
    return "rejected_path"
```

### Example: Content Publication Workflow

```python
from typing import Annotated, TypedDict, Literal
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

class PublicationState(TypedDict):
    messages: Annotated[list, operator.add]
    draft_content: str
    requires_legal_review: bool
    requires_exec_approval: bool
    legal_approved: bool
    exec_approved: bool
    legal_feedback: str
    exec_feedback: str
    final_content: str
    status: str

def generate_draft(state: PublicationState) -> dict:
    """Generate initial content draft."""
    from google.adk.agents import Agent

    writer = Agent(
        name="content_writer",
        model="gemini-2.5-flash",
        instruction="Write professional blog post."
    )

    topic = state["messages"][-1].content
    result = writer.execute(f"Write blog post about: {topic}")

    # Determine if legal/exec review needed
    requires_legal = "privacy" in topic.lower() or "compliance" in topic.lower()
    requires_exec = "strategy" in topic.lower() or "announcement" in topic.lower()

    return {
        "draft_content": result.content,
        "requires_legal_review": requires_legal,
        "requires_exec_approval": requires_exec,
        "status": "draft_complete",
        "messages": [AIMessage(content="Draft ready for review")]
    }

def legal_review_checkpoint(state: PublicationState) -> dict:
    """Pause for legal review."""
    return {
        "status": "awaiting_legal_review",
        "messages": [AIMessage(content="Awaiting legal review...")]
    }

def exec_approval_checkpoint(state: PublicationState) -> dict:
    """Pause for executive approval."""
    return {
        "status": "awaiting_exec_approval",
        "messages": [AIMessage(content="Awaiting executive approval...")]
    }

def incorporate_feedback(state: PublicationState) -> dict:
    """Revise content based on feedback."""
    from google.adk.agents import Agent

    editor = Agent(
        name="editor",
        model="gemini-2.5-flash",
        instruction="Revise content based on feedback."
    )

    feedback = []
    if state.get("legal_feedback"):
        feedback.append(f"Legal: {state['legal_feedback']}")
    if state.get("exec_feedback"):
        feedback.append(f"Executive: {state['exec_feedback']}")

    revision_prompt = f"""
    Original: {state['draft_content']}

    Feedback:
    {chr(10).join(feedback)}

    Please revise accordingly.
    """

    result = editor.execute(revision_prompt)

    return {
        "final_content": result.content,
        "status": "ready_to_publish",
        "messages": [AIMessage(content="Content revised")]
    }

def publish_content(state: PublicationState) -> dict:
    """Publish approved content."""
    return {
        "status": "published",
        "messages": [AIMessage(content=f"Content published:\n{state['final_content']}")]
    }

def handle_rejection(state: PublicationState) -> dict:
    """Handle rejected content."""
    reasons = []
    if not state.get("legal_approved"):
        reasons.append(f"Legal: {state.get('legal_feedback', 'Rejected')}")
    if not state.get("exec_approved"):
        reasons.append(f"Executive: {state.get('exec_feedback', 'Rejected')}")

    return {
        "status": "rejected",
        "messages": [AIMessage(content=f"Publication rejected:\n{chr(10).join(reasons)}")]
    }

# Routing functions
def route_after_draft(state: PublicationState) -> Literal["legal_review", "exec_approval", "publish"]:
    """Route based on review requirements."""
    if state["requires_legal_review"]:
        return "legal_review"
    elif state["requires_exec_approval"]:
        return "exec_approval"
    return "publish"

def route_after_legal(state: PublicationState) -> Literal["exec_approval", "reject", "incorporate"]:
    """Route after legal review."""
    if not state.get("legal_approved"):
        return "reject"
    elif state["requires_exec_approval"]:
        return "exec_approval"
    return "incorporate"

def route_after_exec(state: PublicationState) -> Literal["incorporate", "reject"]:
    """Route after executive approval."""
    if state.get("exec_approved"):
        return "incorporate"
    return "reject"

# Build workflow
builder = StateGraph(PublicationState)

builder.add_node("draft", generate_draft)
builder.add_node("legal_review", legal_review_checkpoint)
builder.add_node("exec_approval", exec_approval_checkpoint)
builder.add_node("incorporate", incorporate_feedback)
builder.add_node("publish", publish_content)
builder.add_node("reject", handle_rejection)

builder.add_edge(START, "draft")
builder.add_conditional_edges(
    "draft",
    route_after_draft,
    {
        "legal_review": "legal_review",
        "exec_approval": "exec_approval",
        "publish": "publish"
    }
)
builder.add_conditional_edges(
    "legal_review",
    route_after_legal,
    {
        "exec_approval": "exec_approval",
        "reject": "reject",
        "incorporate": "incorporate"
    }
)
builder.add_conditional_edges(
    "exec_approval",
    route_after_exec,
    {
        "incorporate": "incorporate",
        "reject": "reject"
    }
)
builder.add_edge("incorporate", "publish")
builder.add_edge("publish", END)
builder.add_edge("reject", END)

# Compile with checkpointing and interrupts
checkpointer = SqliteSaver.from_conn_string("publication_workflow.db")
publication_workflow = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["legal_review", "exec_approval"]  # Pause at both checkpoints
)

# Usage
config = {"configurable": {"thread_id": "article-2024-001"}}

# Step 1: Start workflow
result = publication_workflow.invoke(
    {
        "messages": [HumanMessage(content="AI privacy and compliance best practices")],
        "draft_content": "",
        "requires_legal_review": False,
        "requires_exec_approval": False,
        "legal_approved": False,
        "exec_approved": False,
        "legal_feedback": "",
        "exec_feedback": "",
        "final_content": "",
        "status": "initiated"
    },
    config=config
)

# Workflow pauses at legal_review

# Step 2: Legal approves (later)
result = publication_workflow.invoke(
    {
        "legal_approved": True,
        "legal_feedback": "Add GDPR reference in section 2"
    },
    config=config
)

# Workflow pauses at exec_approval

# Step 3: Executive approves (later)
result = publication_workflow.invoke(
    {
        "exec_approved": True,
        "exec_feedback": "Emphasize our competitive advantage"
    },
    config=config
)

# Workflow completes
```

### Best Practices

1. **Use Persistent Checkpointers:** SQLite or Postgres in production
2. **Clear Checkpoint Messages:** Tell approvers what they're approving
3. **Timeout Handling:** Auto-escalate stalled approvals
4. **Audit Trail:** Log all approval decisions
5. **Graceful Rejection:** Handle rejections with clear feedback

---

## Pattern 3: State Checkpointing

### Concept

Robust state persistence enabling workflow recovery from failures.

### When to Use

- **Long-running workflows**: Multi-hour or multi-day processes
- **Failure recovery**: Resume from last successful checkpoint
- **Multi-session workflows**: Pause and resume across sessions
- **Production systems**: Ensure reliability and fault tolerance

### Core Components

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver

# 1. Checkpointer setup
checkpointer = SqliteSaver.from_conn_string("workflow.db")

# 2. Thread ID for workflow instances
config = {"configurable": {"thread_id": "unique-workflow-id"}}

# 3. Compile with checkpointer
graph = builder.compile(checkpointer=checkpointer)

# 4. Resume from last checkpoint
result = graph.invoke(None, config=config)  # None = resume from state
```

### Example: Multi-Stage Data Pipeline

```python
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import time

class PipelineState(TypedDict):
    messages: Annotated[list, operator.add]
    stages_completed: Annotated[list, operator.add]
    current_stage: str
    input_data: dict
    processed_data: dict
    errors: Annotated[list, operator.add]
    retry_count: int

def extract_stage(state: PipelineState) -> dict:
    """Extract data from source."""
    try:
        # Simulate data extraction
        time.sleep(2)  # Long-running operation

        extracted = {
            "records": 10000,
            "source": "database",
            "timestamp": time.time()
        }

        return {
            "stages_completed": ["extract"],
            "current_stage": "transform",
            "processed_data": {"extracted": extracted},
            "messages": [AIMessage(content="Extraction complete")]
        }
    except Exception as e:
        return {
            "errors": [f"Extract failed: {str(e)}"],
            "current_stage": "extract",
            "retry_count": state.get("retry_count", 0) + 1
        }

def transform_stage(state: PipelineState) -> dict:
    """Transform extracted data."""
    try:
        time.sleep(3)  # Long-running operation

        extracted_data = state["processed_data"]["extracted"]

        transformed = {
            "records_transformed": extracted_data["records"],
            "transformations": ["normalize", "deduplicate", "enrich"],
            "timestamp": time.time()
        }

        return {
            "stages_completed": ["transform"],
            "current_stage": "load",
            "processed_data": {
                **state["processed_data"],
                "transformed": transformed
            },
            "messages": [AIMessage(content="Transformation complete")]
        }
    except Exception as e:
        return {
            "errors": [f"Transform failed: {str(e)}"],
            "current_stage": "transform",
            "retry_count": state.get("retry_count", 0) + 1
        }

def load_stage(state: PipelineState) -> dict:
    """Load transformed data to destination."""
    try:
        time.sleep(2)  # Long-running operation

        transformed_data = state["processed_data"]["transformed"]

        loaded = {
            "records_loaded": transformed_data["records_transformed"],
            "destination": "data_warehouse",
            "timestamp": time.time()
        }

        return {
            "stages_completed": ["load"],
            "current_stage": "complete",
            "processed_data": {
                **state["processed_data"],
                "loaded": loaded
            },
            "messages": [AIMessage(content="Load complete - pipeline successful")]
        }
    except Exception as e:
        return {
            "errors": [f"Load failed: {str(e)}"],
            "current_stage": "load",
            "retry_count": state.get("retry_count", 0) + 1
        }

def check_retry(state: PipelineState) -> dict:
    """Check if stage should be retried."""
    retry_count = state.get("retry_count", 0)

    if retry_count >= 3:
        return {
            "current_stage": "failed",
            "messages": [AIMessage(content=f"Pipeline failed after {retry_count} retries")]
        }

    # Reset for retry
    return {
        "messages": [AIMessage(content=f"Retrying stage (attempt {retry_count + 1})")]
    }

# Routing
def route_by_stage(state: PipelineState) -> Literal["extract", "transform", "load", "check_retry", "end"]:
    """Route based on current stage."""
    stage = state["current_stage"]

    if state.get("errors"):
        return "check_retry"

    if stage == "extract":
        return "extract"
    elif stage == "transform":
        return "transform"
    elif stage == "load":
        return "load"
    elif stage in ["complete", "failed"]:
        return "end"

    return "end"

# Build pipeline
builder = StateGraph(PipelineState)

builder.add_node("extract", extract_stage)
builder.add_node("transform", transform_stage)
builder.add_node("load", load_stage)
builder.add_node("check_retry", check_retry)

builder.add_edge(START, "extract")

# Conditional routing after each stage
for stage in ["extract", "transform", "load"]:
    builder.add_conditional_edges(
        stage,
        route_by_stage,
        {
            "extract": "extract",
            "transform": "transform",
            "load": "load",
            "check_retry": "check_retry",
            "end": END
        }
    )

builder.add_conditional_edges(
    "check_retry",
    route_by_stage,
    {
        "extract": "extract",
        "transform": "transform",
        "load": "load",
        "end": END
    }
)

# Compile with SQLite checkpointing
checkpointer = SqliteSaver.from_conn_string("pipeline_state.db")
data_pipeline = builder.compile(checkpointer=checkpointer)

# Usage with recovery
config = {"configurable": {"thread_id": "daily-pipeline-2024-02-20"}}

try:
    # Initial run
    result = data_pipeline.invoke(
        {
            "messages": [],
            "stages_completed": [],
            "current_stage": "extract",
            "input_data": {},
            "processed_data": {},
            "errors": [],
            "retry_count": 0
        },
        config=config
    )
    print("Pipeline completed successfully")

except Exception as e:
    print(f"Pipeline failed: {e}")

    # Later: Resume from last checkpoint
    # State is automatically loaded from SQLite
    print("Resuming pipeline from last checkpoint...")
    result = data_pipeline.invoke(None, config=config)
```

### Best Practices

1. **Unique Thread IDs:** Use meaningful IDs (timestamp, job ID)
2. **Granular Checkpoints:** Save state after each significant step
3. **Error Tracking:** Log errors in state for debugging
4. **Retry Logic:** Implement intelligent retry with backoff
5. **State Cleanup:** Periodically purge old workflow states

---

## Pattern 4: Streaming Integration

### Concept

Stream intermediate results for real-time monitoring and progressive output.

### When to Use

- **Long-running workflows**: Provide progress updates
- **User-facing applications**: Show incremental results
- **Monitoring dashboards**: Real-time workflow status
- **Content generation**: Stream text as it's generated

### Core Components

```python
# 1. Async streaming
async for event in graph.astream(initial_state, config=config):
    print(f"Event: {event}")

# 2. Stream with updates
async for event in graph.astream_events(initial_state, config=config):
    if event["event"] == "on_chain_stream":
        print(f"Progress: {event['data']}")
```

### Example: Real-Time Report Generation

```python
from typing import Annotated, TypedDict, AsyncIterator
import operator
from langgraph.graph import StateGraph, START, END
import asyncio

class ReportState(TypedDict):
    messages: Annotated[list, operator.add]
    progress: int
    current_section: str
    sections_complete: Annotated[list, operator.add]
    report_content: dict

async def research_section(state: ReportState) -> dict:
    """Research section with streaming."""
    from google.adk.agents import Agent

    researcher = Agent(
        name="researcher",
        model="gemini-2.5-flash",
        stream=True
    )

    chunks = []
    async for chunk in researcher.stream("Research market trends"):
        chunks.append(chunk)
        # Each chunk is available in real-time

    content = "".join(chunks)

    return {
        "progress": 25,
        "current_section": "analysis",
        "sections_complete": ["research"],
        "report_content": {"research": content},
        "messages": [AIMessage(content="Research section complete")]
    }

async def analysis_section(state: ReportState) -> dict:
    """Analysis section."""
    from google.adk.agents import Agent

    analyst = Agent(
        name="analyst",
        model="gemini-2.5-pro",
        stream=True
    )

    research = state["report_content"].get("research", "")

    chunks = []
    async for chunk in analyst.stream(f"Analyze: {research}"):
        chunks.append(chunk)

    content = "".join(chunks)

    return {
        "progress": 50,
        "current_section": "recommendations",
        "sections_complete": ["analysis"],
        "report_content": {
            **state["report_content"],
            "analysis": content
        },
        "messages": [AIMessage(content="Analysis section complete")]
    }

async def recommendations_section(state: ReportState) -> dict:
    """Recommendations section."""
    from google.adk.agents import Agent

    strategist = Agent(
        name="strategist",
        model="gemini-2.5-flash",
        stream=True
    )

    analysis = state["report_content"].get("analysis", "")

    chunks = []
    async for chunk in strategist.stream(f"Create recommendations from: {analysis}"):
        chunks.append(chunk)

    content = "".join(chunks)

    return {
        "progress": 75,
        "current_section": "executive_summary",
        "sections_complete": ["recommendations"],
        "report_content": {
            **state["report_content"],
            "recommendations": content
        },
        "messages": [AIMessage(content="Recommendations section complete")]
    }

async def executive_summary(state: ReportState) -> dict:
    """Final executive summary."""
    from google.adk.agents import Agent

    summarizer = Agent(
        name="summarizer",
        model="gemini-2.5-flash",
        stream=True
    )

    full_report = "\n\n".join([
        state["report_content"].get("research", ""),
        state["report_content"].get("analysis", ""),
        state["report_content"].get("recommendations", "")
    ])

    chunks = []
    async for chunk in summarizer.stream(f"Create executive summary: {full_report}"):
        chunks.append(chunk)

    content = "".join(chunks)

    return {
        "progress": 100,
        "current_section": "complete",
        "sections_complete": ["executive_summary"],
        "report_content": {
            **state["report_content"],
            "executive_summary": content
        },
        "messages": [AIMessage(content="Report complete")]
    }

# Build streaming workflow
builder = StateGraph(ReportState)

builder.add_node("research", research_section)
builder.add_node("analysis", analysis_section)
builder.add_node("recommendations", recommendations_section)
builder.add_node("executive_summary", executive_summary)

builder.add_edge(START, "research")
builder.add_edge("research", "analysis")
builder.add_edge("analysis", "recommendations")
builder.add_edge("recommendations", "executive_summary")
builder.add_edge("executive_summary", END)

report_generator = builder.compile()

# Usage with real-time streaming
async def generate_report_with_progress():
    """Generate report with real-time progress."""
    config = {"configurable": {"thread_id": "report-2024-02-20"}}

    initial_state = {
        "messages": [],
        "progress": 0,
        "current_section": "research",
        "sections_complete": [],
        "report_content": {}
    }

    # Stream the entire workflow
    async for event in report_generator.astream(initial_state, config=config):
        # Real-time updates
        if isinstance(event, dict):
            if "progress" in event:
                print(f"📊 Progress: {event['progress']}%")
            if "current_section" in event:
                print(f"📝 Current section: {event['current_section']}")
            if "sections_complete" in event:
                print(f"✅ Completed: {event['sections_complete']}")

# Run
asyncio.run(generate_report_with_progress())
```

### Best Practices

1. **Async/Await:** Use async functions for streaming
2. **Chunk Size:** Balance between granularity and overhead
3. **Error Handling:** Handle streaming interruptions gracefully
4. **Progress Indicators:** Provide meaningful progress updates
5. **Buffering:** Buffer chunks for smoother UI updates

---

## Comparison Matrix

| Pattern | Use Case | Complexity | Recovery | Real-time |
|---------|----------|------------|----------|-----------|
| **Conditional Branching** | Complex routing | Medium | Via checkpoints | No |
| **Human-in-the-Loop** | Approvals | Medium | Built-in | No |
| **Checkpointing** | Fault tolerance | Low | Automatic | No |
| **Streaming** | Progress monitoring | High | Via checkpoints | Yes |

---

## Integration Example

Combine all patterns for production-ready workflow:

```python
# Production workflow with all advanced patterns
builder = StateGraph(ProductionState)

# Add all nodes
builder.add_node("classify", classification_node)
builder.add_node("process_tier_1", tier_1_handler)
builder.add_node("process_tier_2", tier_2_handler)
builder.add_node("approval_checkpoint", approval_node)
builder.add_node("finalize", finalization_node)

# Conditional branching
builder.add_conditional_edges("classify", route_by_tier, {...})

# Human-in-the-loop
builder.add_edge("process_tier_1", "approval_checkpoint")
builder.add_conditional_edges("approval_checkpoint", check_approval, {...})

# Checkpointing for recovery
checkpointer = PostgresSaver.from_conn_string(DB_URL)

# Compile with all features
production_workflow = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["approval_checkpoint"]
)

# Use with streaming
async for event in production_workflow.astream(state, config):
    monitor_progress(event)
```
