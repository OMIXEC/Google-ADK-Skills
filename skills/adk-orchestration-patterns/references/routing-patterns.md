# Routing Patterns Reference

## Overview

Routing patterns determine how requests are directed to agents in a multi-agent system. This reference covers four fundamental routing patterns and their variations.

---

## 1. Static Routing

### Definition
Predetermined agent sequence defined at design time. The routing path is fixed and doesn't change based on input.

### Characteristics
- **Fixed path**: Same sequence for all inputs
- **Predictable**: Easy to reason about and debug
- **Deterministic**: Same input always follows same path
- **Fast**: No routing decision overhead

### When to Use
- Workflows with clear, unchanging steps
- Processing pipelines with fixed stages
- When all inputs need the same treatment
- Regulatory compliance requiring audit trails

### Implementation

```python
from google.adk.agents import SequentialAgent, LlmAgent

# Static three-stage pipeline
validator = LlmAgent(name="validator", instruction="Validate input")
processor = LlmAgent(name="processor", instruction="Process data")
formatter = LlmAgent(name="formatter", instruction="Format output")

static_pipeline = SequentialAgent(
    name="static_workflow",
    sub_agents=[validator, processor, formatter],
)
```

### Variations

**Linear Pipeline:**
```
Input → A → B → C → Output
```

**Parallel Processing:**
```
        ┌→ A ┐
Input →├→ B ├→ Aggregator → Output
        └→ C ┘
```

**Nested Static Routing:**
```python
stage1 = ParallelAgent(sub_agents=[a, b, c])
stage2 = LlmAgent(name="aggregator", instruction="Combine results")
stage3 = LlmAgent(name="finalizer", instruction="Finalize output")

workflow = SequentialAgent(sub_agents=[stage1, stage2, stage3])
```

### Pros & Cons

**Pros:**
- Simple to understand and maintain
- Predictable execution path
- Easy to test and debug
- No routing logic errors

**Cons:**
- Inflexible to input variations
- May execute unnecessary steps
- Cannot adapt to context
- All inputs treated identically

---

## 2. Dynamic Routing

### Definition
An LLM analyzes the input and decides which agent(s) to invoke. The routing path is determined at runtime based on the request.

### Characteristics
- **Adaptive**: Different paths for different inputs
- **Intelligent**: LLM understands intent and context
- **Flexible**: Can handle unexpected input types
- **Context-aware**: Routing based on content, not just structure

### When to Use
- Customer service with multiple departments
- Task delegation based on complexity or domain
- When input types vary significantly
- Intelligent request classification needed

### Implementation

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Specialist agents
billing_specialist = LlmAgent(
    name="billing",
    instruction="Handle billing and payment questions"
)

technical_specialist = LlmAgent(
    name="technical",
    instruction="Handle technical support questions"
)

sales_specialist = LlmAgent(
    name="sales",
    instruction="Handle product and sales questions"
)

# Dynamic router
router = LlmAgent(
    name="smart_router",
    model="gemini-2.5-flash",
    tools=[
        AgentTool(agent=billing_specialist),
        AgentTool(agent=technical_specialist),
        AgentTool(agent=sales_specialist),
    ],
    instruction="""
    Analyze the customer request and route to the appropriate specialist:
    - Billing specialist: payments, invoices, subscriptions
    - Technical specialist: bugs, errors, how-to questions
    - Sales specialist: features, pricing, purchase questions

    You can consult multiple specialists if needed.
    """
)

result = router.run("I want to upgrade my plan but I'm having login issues")
# Router might call both technical_specialist and sales_specialist
```

### Variations

**Single-Target Routing:**
LLM selects exactly one agent to handle the request.

```python
instruction = "Choose the SINGLE best specialist for this request."
```

**Multi-Target Routing:**
LLM can invoke multiple agents as needed.

```python
instruction = "Use as many specialists as needed to fully answer the request."
```

**Sequential Dynamic Routing:**
LLM routes to one agent, then routes the result to another based on outcome.

```python
coordinator = LlmAgent(
    name="coordinator",
    instruction="""
    1. First, determine the primary specialist needed
    2. After getting their response, determine if a secondary specialist is needed
    3. Combine insights from all consulted specialists
    """
)
```

### Advanced Example: Multi-Step Dynamic Routing

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Research specialists
web_researcher = LlmAgent(name="web", instruction="Search web for recent info")
academic_researcher = LlmAgent(name="academic", instruction="Search academic sources")
data_analyst = LlmAgent(name="data", instruction="Analyze datasets")

# Writing specialists
technical_writer = LlmAgent(name="tech_writer", instruction="Write technical content")
creative_writer = LlmAgent(name="creative_writer", instruction="Write engaging content")

# Two-stage coordinator
coordinator = LlmAgent(
    name="content_coordinator",
    model="gemini-2.5-flash",
    tools=[
        AgentTool(agent=web_researcher),
        AgentTool(agent=academic_researcher),
        AgentTool(agent=data_analyst),
        AgentTool(agent=technical_writer),
        AgentTool(agent=creative_writer),
    ],
    instruction="""
    Two-phase process:

    PHASE 1 - Research:
    - For recent trends: use web_researcher
    - For scientific topics: use academic_researcher
    - For data analysis: use data_analyst

    PHASE 2 - Writing:
    - For technical audience: use technical_writer
    - For general audience: use creative_writer

    Gather research first, then produce the content.
    """
)
```

### Pros & Cons

**Pros:**
- Highly flexible and adaptive
- Handles diverse input types
- Can route based on nuanced understanding
- Reduces unnecessary processing

**Cons:**
- Less predictable execution paths
- Routing logic can be opaque
- Requires clear routing instructions
- Additional LLM call overhead

---

## 3. Conditional Routing

### Definition
Rule-based branching where routing decisions are made programmatically based on agent outputs, state, or explicit conditions.

### Characteristics
- **Rule-based**: Explicit if/then logic
- **Programmatic**: Controlled by code, not LLM
- **Deterministic**: Same state = same route
- **Transparent**: Easy to audit and debug

### When to Use
- Business rules and compliance requirements
- Error handling and retry logic
- State-based workflows
- When routing logic must be explicit and auditable

### Implementation Pattern

```python
from google.adk.agents import LlmAgent

classifier = LlmAgent(name="classifier", instruction="Classify input as urgent or normal")
urgent_handler = LlmAgent(name="urgent", instruction="Handle urgent requests")
normal_handler = LlmAgent(name="normal", instruction="Handle normal requests")

# Get classification
classification = classifier.run(user_input)

# Conditional routing in application logic
if "urgent" in classification.lower():
    result = urgent_handler.run(user_input)
else:
    result = normal_handler.run(user_input)
```

### Advanced Example: Multi-Stage Conditional Routing

```python
from google.adk.agents import LlmAgent

# Stage 1: Input validation
validator = LlmAgent(
    name="validator",
    instruction="Check if input is valid. Output: VALID or INVALID with reason."
)

validation_result = validator.run(user_input)

if "INVALID" in validation_result:
    # Route to error handler
    error_handler = LlmAgent(name="error", instruction="Explain validation error")
    final_result = error_handler.run(validation_result)
else:
    # Stage 2: Complexity assessment
    assessor = LlmAgent(
        name="assessor",
        instruction="Assess complexity: SIMPLE, MEDIUM, or COMPLEX"
    )
    complexity = assessor.run(user_input)

    # Route based on complexity
    if "SIMPLE" in complexity:
        processor = LlmAgent(name="simple", instruction="Quick processing")
        final_result = processor.run(user_input)
    elif "MEDIUM" in complexity:
        processor = LlmAgent(name="medium", instruction="Standard processing")
        final_result = processor.run(user_input)
    else:  # COMPLEX
        processor = LlmAgent(name="complex", instruction="Deep analysis")
        final_result = processor.run(user_input)
```

### State-Based Conditional Routing

```python
class WorkflowState:
    def __init__(self):
        self.stage = "initial"
        self.attempts = 0
        self.errors = []

state = WorkflowState()

while state.stage != "complete":
    if state.stage == "initial":
        result = initial_processor.run(input)
        if "error" in result.lower():
            state.stage = "error_handling"
            state.errors.append(result)
        else:
            state.stage = "validation"

    elif state.stage == "validation":
        result = validator.run(result)
        if "valid" in result.lower():
            state.stage = "complete"
        else:
            state.attempts += 1
            if state.attempts >= 3:
                state.stage = "failed"
            else:
                state.stage = "retry"

    elif state.stage == "error_handling":
        result = error_handler.run(state.errors[-1])
        state.stage = "validation"

    elif state.stage == "retry":
        result = retrier.run(result)
        state.stage = "validation"

    elif state.stage == "failed":
        result = failure_handler.run(state.errors)
        break
```

### Pros & Cons

**Pros:**
- Explicit, auditable logic
- Full programmatic control
- Deterministic behavior
- Easy to test each path

**Cons:**
- Requires predefined rules
- Less flexible than dynamic routing
- More code to maintain
- Rules may become complex

---

## 4. Hierarchical Routing

### Definition
Tree structure of supervisor agents that delegate to sub-teams or specialist agents. Multi-level delegation with clear reporting structure.

### Characteristics
- **Layered**: Multiple levels of delegation
- **Organized**: Clear responsibility boundaries
- **Scalable**: Add teams without affecting structure
- **Modular**: Each level is independent

### When to Use
- Large organizations with multiple departments
- Complex domains requiring deep specialization
- When scaling beyond 5-7 top-level agents
- Clear delegation chains are needed

### Implementation

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Level 3: Individual specialists
backend_dev = LlmAgent(name="backend", instruction="Backend development")
frontend_dev = LlmAgent(name="frontend", instruction="Frontend development")
devops = LlmAgent(name="devops", instruction="DevOps and infrastructure")

designer = LlmAgent(name="designer", instruction="UI/UX design")
researcher = LlmAgent(name="researcher", instruction="User research")

sales_rep = LlmAgent(name="sales", instruction="Sales questions")
support_rep = LlmAgent(name="support", instruction="Customer support")

# Level 2: Team leads
engineering_lead = LlmAgent(
    name="engineering_lead",
    tools=[
        AgentTool(agent=backend_dev),
        AgentTool(agent=frontend_dev),
        AgentTool(agent=devops),
    ],
    instruction="Delegate engineering tasks to backend, frontend, or devops."
)

product_lead = LlmAgent(
    name="product_lead",
    tools=[
        AgentTool(agent=designer),
        AgentTool(agent=researcher),
    ],
    instruction="Delegate product tasks to designers or researchers."
)

customer_lead = LlmAgent(
    name="customer_lead",
    tools=[
        AgentTool(agent=sales_rep),
        AgentTool(agent=support_rep),
    ],
    instruction="Delegate customer requests to sales or support."
)

# Level 1: Executive
cto = LlmAgent(
    name="cto",
    model="gemini-2.5-flash",
    tools=[
        AgentTool(agent=engineering_lead),
        AgentTool(agent=product_lead),
        AgentTool(agent=customer_lead),
    ],
    instruction="""
    You are the CTO coordinating all company functions.
    Delegate to the appropriate department:
    - Engineering lead: technical implementation, infrastructure, code
    - Product lead: design, user experience, research
    - Customer lead: sales, support, customer success

    The leads will further delegate to their team members.
    """
)

result = cto.run("We need to redesign the checkout page to improve conversion")
# CTO → Product Lead → Designer + Researcher
# CTO → Engineering Lead → Frontend Dev
```

### Variations

**Strict Hierarchy (No Cross-Level):**
Each level only communicates with adjacent levels.

```python
# CTO can only talk to leads, not individual specialists
# Leads can only talk to their direct reports
```

**Flexible Hierarchy (Skip Levels):**
Higher levels can directly access lower levels when needed.

```python
cto = LlmAgent(
    name="cto",
    tools=[
        # Level 2: Leads
        AgentTool(agent=engineering_lead),
        AgentTool(agent=product_lead),
        # Level 3: Can also access specialists directly
        AgentTool(agent=backend_dev),
        AgentTool(agent=designer),
    ],
    instruction="Typically use leads, but can access specialists for urgent matters."
)
```

**Domain-Based Hierarchy:**
Organization by domain expertise rather than function.

```python
# Healthcare domain
clinical_supervisor = LlmAgent(
    tools=[AgentTool(agent=doctor), AgentTool(agent=nurse)]
)

# Billing domain
billing_supervisor = LlmAgent(
    tools=[AgentTool(agent=insurance), AgentTool(agent=payments)]
)

# Admin domain
admin_supervisor = LlmAgent(
    tools=[AgentTool(agent=scheduling), AgentTool(agent=records)]
)

hospital_coordinator = LlmAgent(
    tools=[
        AgentTool(agent=clinical_supervisor),
        AgentTool(agent=billing_supervisor),
        AgentTool(agent=admin_supervisor),
    ]
)
```

### Pros & Cons

**Pros:**
- Scalable to large organizations
- Clear responsibility boundaries
- Easy to add new specialists
- Modular and maintainable

**Cons:**
- More complex to set up
- Longer execution paths
- Potential for miscommunication
- Overhead from multiple delegation steps

---

## Pattern Comparison

| Pattern | Flexibility | Predictability | Complexity | Best For |
|---------|-------------|----------------|------------|----------|
| **Static** | Low | High | Low | Fixed workflows, compliance |
| **Dynamic** | High | Medium | Medium | Intent-based routing, variety |
| **Conditional** | Medium | High | Medium | Business rules, state-based |
| **Hierarchical** | High | Medium | High | Large orgs, deep specialization |

---

## Combining Patterns

Real-world systems often combine multiple patterns:

### Example: E-commerce Platform

```python
# Static pipeline for order processing
order_pipeline = SequentialAgent(
    sub_agents=[validate_order, charge_payment, create_shipment]
)

# Dynamic routing for customer service
customer_service = LlmAgent(
    tools=[
        AgentTool(agent=order_status),
        AgentTool(agent=returns),
        AgentTool(agent=product_info),
    ],
    instruction="Route customer questions to appropriate specialist"
)

# Conditional routing for fraud detection
fraud_score = fraud_detector.run(order)
if fraud_score > 0.8:
    result = fraud_review_team.run(order)
elif fraud_score > 0.5:
    result = automated_verification.run(order)
else:
    result = order_pipeline.run(order)

# Hierarchical routing for internal operations
ops_director = LlmAgent(
    tools=[
        AgentTool(agent=warehouse_manager),    # → warehouse staff
        AgentTool(agent=logistics_manager),    # → drivers, carriers
        AgentTool(agent=customer_service),     # → CS reps (dynamic router above)
    ]
)
```

---

## Best Practices

### Choosing the Right Pattern

1. **Start with static** if workflow is well-defined and unchanging
2. **Use dynamic** when inputs vary significantly or intent matters
3. **Use conditional** when business rules or state drive routing
4. **Use hierarchical** when you have >7 agents or clear org structure

### Designing Routing Instructions

**For Dynamic Routing:**
- Be specific about routing criteria
- Include examples in instructions
- Specify when to use multiple agents
- Define fallback behavior

```python
instruction = """
Route based on these rules:

1. Billing questions (keywords: payment, invoice, charge, subscription)
   → billing_specialist

2. Technical issues (keywords: error, bug, not working, crash)
   → technical_specialist

3. Product questions (keywords: feature, how to, pricing, upgrade)
   → sales_specialist

If question spans multiple areas, consult all relevant specialists.
If unclear, ask clarifying questions first.
"""
```

### Monitoring and Debugging

**Log Routing Decisions:**
```python
import logging

class RoutingLogger:
    def log_route(self, from_agent, to_agent, reason):
        logging.info(f"{from_agent} → {to_agent}: {reason}")
```

**Track Execution Paths:**
```python
class ExecutionTracker:
    def __init__(self):
        self.path = []

    def record(self, agent_name):
        self.path.append(agent_name)

    def get_path(self):
        return " → ".join(self.path)
```

---

## Anti-Patterns to Avoid

### 1. Over-Routing
Too many routing layers slow down execution.

**Bad:**
```
Input → Router1 → Router2 → Router3 → Specialist
```

**Better:**
```
Input → Smart Router → Specialist
```

### 2. Ambiguous Routing Logic
Unclear criteria lead to inconsistent routing.

**Bad:**
```python
instruction = "Route this to the right person"
```

**Better:**
```python
instruction = """
Route based on:
- Account questions → account_specialist
- Technical issues → tech_specialist
"""
```

### 3. No Fallback
Every routing pattern should handle unexpected inputs.

**Bad:**
```python
if condition_a:
    route_to_a()
elif condition_b:
    route_to_b()
# What if neither?
```

**Better:**
```python
if condition_a:
    route_to_a()
elif condition_b:
    route_to_b()
else:
    route_to_general_handler()
```

### 4. Circular Routing
Agents routing back and forth infinitely.

**Bad:**
```
Agent A → Agent B → Agent A → Agent B → ...
```

**Better:**
Add iteration limits or state tracking to prevent loops.
