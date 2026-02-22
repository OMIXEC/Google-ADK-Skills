# Enterprise Hierarchy Example

## Complete E-commerce Enterprise Agent System

This example demonstrates a full enterprise multi-agent hierarchy for an e-commerce platform with 50+ agents.

## Architecture Overview

```
Executive Coordinator (Gemini Pro)
├── Customer Operations (Gemini Flash)
│   ├── Sales Team (5 agents)
│   ├── Support Team (8 agents)
│   └── Success Team (4 agents)
├── Product Operations (Gemini Flash)
│   ├── Development Team (12 agents)
│   ├── QA Team (6 agents)
│   └── DevOps Team (5 agents)
└── Business Operations (Gemini Flash)
    ├── Finance Team (4 agents)
    ├── Analytics Team (6 agents)
    └── Compliance Team (3 agents)
```

## Full Implementation

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, List

# ============================================================================
# LEVEL 1: EXECUTIVE COORDINATOR
# ============================================================================

executive_coordinator = LlmAgent(
    name="executive_coordinator",
    model="gemini-2.5-pro",
    description="Enterprise AI coordinator for all business operations",
    instruction="""
    You are the executive AI coordinator for the e-commerce platform.

    Your responsibilities:
    1. Route requests to appropriate department supervisors
    2. Synthesize cross-department insights
    3. Handle escalations requiring executive decision-making
    4. Coordinate complex multi-department initiatives

    Department Supervisors:
    - Customer Operations: Sales, support, customer success
    - Product Operations: Development, QA, deployment
    - Business Operations: Finance, analytics, compliance

    Always explain your routing decisions and synthesize final responses.
    Escalate to humans for strategic decisions, legal issues, or high-value contracts.
    """,
)

# ============================================================================
# LEVEL 2: DEPARTMENT SUPERVISORS
# ============================================================================

customer_operations = LlmAgent(
    name="customer_operations_supervisor",
    model="gemini-2.5-flash",
    description="Coordinates customer-facing teams (sales, support, success)",
    instruction="""
    You supervise customer operations teams.

    Teams:
    - Sales: Lead qualification, pricing, contract generation
    - Support: Ticket resolution, troubleshooting, escalations
    - Success: Onboarding, adoption, renewals

    Route customer requests to the appropriate team.
    Coordinate cross-team initiatives (e.g., support escalation to sales).
    Monitor customer satisfaction metrics.
    """,
)

product_operations = LlmAgent(
    name="product_operations_supervisor",
    model="gemini-2.5-flash",
    description="Coordinates product development teams",
    instruction="""
    You supervise product operations teams.

    Teams:
    - Development: Feature implementation, bug fixes, architecture
    - QA: Testing, quality assurance, test automation
    - DevOps: Deployment, infrastructure, monitoring

    Route product requests to the appropriate team.
    Coordinate releases across development, QA, and DevOps.
    Monitor product quality metrics.
    """,
)

business_operations = LlmAgent(
    name="business_operations_supervisor",
    model="gemini-2.5-flash",
    description="Coordinates business function teams",
    instruction="""
    You supervise business operations teams.

    Teams:
    - Finance: Billing, payments, revenue tracking
    - Analytics: Metrics, reporting, business intelligence
    - Compliance: Security, privacy, regulatory requirements

    Route business requests to the appropriate team.
    Ensure compliance requirements are met across all operations.
    Monitor business health metrics.
    """,
)

# ============================================================================
# LEVEL 3: TEAM LEADS
# ============================================================================

# --- Customer Operations Team Leads ---

sales_team_lead = LlmAgent(
    name="sales_team_lead",
    model="gemini-2.5-flash",
    description="Manages sales specialist agents",
    instruction="Coordinate sales activities: lead qualification, pricing, proposals, contracts.",
)

support_team_lead = LlmAgent(
    name="support_team_lead",
    model="gemini-2.5-flash",
    description="Manages support specialist agents",
    instruction="Coordinate support activities: ticket triage, resolution, escalation.",
)

success_team_lead = LlmAgent(
    name="success_team_lead",
    model="gemini-2.5-flash",
    description="Manages customer success agents",
    instruction="Coordinate success activities: onboarding, adoption tracking, renewals.",
)

# --- Product Operations Team Leads ---

dev_team_lead = LlmAgent(
    name="development_team_lead",
    model="gemini-2.5-flash",
    description="Manages development specialists",
    instruction="Coordinate development: feature work, bug fixes, code reviews.",
)

qa_team_lead = LlmAgent(
    name="qa_team_lead",
    model="gemini-2.5-flash",
    description="Manages QA specialists",
    instruction="Coordinate testing: test planning, execution, automation.",
)

devops_team_lead = LlmAgent(
    name="devops_team_lead",
    model="gemini-2.5-flash",
    description="Manages DevOps specialists",
    instruction="Coordinate deployments, infrastructure, monitoring.",
)

# --- Business Operations Team Leads ---

finance_team_lead = LlmAgent(
    name="finance_team_lead",
    model="gemini-2.5-flash",
    description="Manages finance specialists",
    instruction="Coordinate finance: billing, payments, revenue tracking.",
)

analytics_team_lead = LlmAgent(
    name="analytics_team_lead",
    model="gemini-2.5-flash",
    description="Manages analytics specialists",
    instruction="Coordinate analytics: metrics, dashboards, reports.",
)

# ============================================================================
# LEVEL 4: SPECIALIST AGENTS
# ============================================================================

# --- Sales Specialists ---

lead_qualifier = LlmAgent(
    name="lead_qualifier",
    model="gemini-2.5-flash",
    description="Qualifies sales leads using BANT criteria",
)

pricing_specialist = LlmAgent(
    name="pricing_specialist",
    model="gemini-2.5-flash",
    description="Generates pricing quotes based on product catalog",
)

proposal_writer = LlmAgent(
    name="proposal_writer",
    model="gemini-2.5-flash",
    description="Creates sales proposals and presentations",
)

contract_generator = LlmAgent(
    name="contract_generator",
    model="gemini-2.5-flash",
    description="Generates contract documents from templates",
)

demo_scheduler = LlmAgent(
    name="demo_scheduler",
    model="gemini-2.5-flash",
    description="Schedules product demos and follow-ups",
)

# --- Support Specialists ---

ticket_triager = LlmAgent(
    name="ticket_triager",
    model="gemini-2.5-flash",
    description="Triages support tickets by priority and category",
)

technical_support = LlmAgent(
    name="technical_support",
    model="gemini-2.5-flash",
    description="Resolves technical support issues",
)

billing_support = LlmAgent(
    name="billing_support",
    model="gemini-2.5-flash",
    description="Handles billing and payment inquiries",
)

account_support = LlmAgent(
    name="account_support",
    model="gemini-2.5-flash",
    description="Manages account-related requests",
)

escalation_handler = LlmAgent(
    name="escalation_handler",
    model="gemini-2.5-flash",
    description="Handles escalated support issues",
)

# --- Success Specialists ---

onboarding_specialist = LlmAgent(
    name="onboarding_specialist",
    model="gemini-2.5-flash",
    description="Manages customer onboarding process",
)

adoption_tracker = LlmAgent(
    name="adoption_tracker",
    model="gemini-2.5-flash",
    description="Tracks product adoption and usage",
)

renewal_specialist = LlmAgent(
    name="renewal_specialist",
    model="gemini-2.5-flash",
    description="Manages contract renewals",
)

health_monitor = LlmAgent(
    name="health_monitor",
    model="gemini-2.5-flash",
    description="Monitors customer health scores",
)

# --- Development Specialists ---

backend_developer = LlmAgent(
    name="backend_developer",
    model="gemini-2.5-flash",
    description="Implements backend features and APIs",
)

frontend_developer = LlmAgent(
    name="frontend_developer",
    model="gemini-2.5-flash",
    description="Implements frontend features and UI",
)

database_specialist = LlmAgent(
    name="database_specialist",
    model="gemini-2.5-flash",
    description="Manages database schema and queries",
)

api_architect = LlmAgent(
    name="api_architect",
    model="gemini-2.5-flash",
    description="Designs API architecture and contracts",
)

code_reviewer = LlmAgent(
    name="code_reviewer",
    model="gemini-2.5-flash",
    description="Reviews code for quality and best practices",
)

# --- QA Specialists ---

test_planner = LlmAgent(
    name="test_planner",
    model="gemini-2.5-flash",
    description="Creates test plans and strategies",
)

integration_tester = LlmAgent(
    name="integration_tester",
    model="gemini-2.5-flash",
    description="Performs integration testing",
)

performance_tester = LlmAgent(
    name="performance_tester",
    model="gemini-2.5-flash",
    description="Conducts performance and load testing",
)

automation_engineer = LlmAgent(
    name="automation_engineer",
    model="gemini-2.5-flash",
    description="Develops test automation",
)

# --- DevOps Specialists ---

deployment_engineer = LlmAgent(
    name="deployment_engineer",
    model="gemini-2.5-flash",
    description="Manages deployments and releases",
)

infrastructure_engineer = LlmAgent(
    name="infrastructure_engineer",
    model="gemini-2.5-flash",
    description="Manages cloud infrastructure",
)

monitoring_specialist = LlmAgent(
    name="monitoring_specialist",
    model="gemini-2.5-flash",
    description="Sets up monitoring and alerting",
)

# --- Finance Specialists ---

billing_analyst = LlmAgent(
    name="billing_analyst",
    model="gemini-2.5-flash",
    description="Analyzes billing and revenue data",
)

payment_processor = LlmAgent(
    name="payment_processor",
    model="gemini-2.5-flash",
    description="Processes payments and refunds",
)

revenue_tracker = LlmAgent(
    name="revenue_tracker",
    model="gemini-2.5-flash",
    description="Tracks revenue metrics and forecasts",
)

# --- Analytics Specialists ---

metrics_analyst = LlmAgent(
    name="metrics_analyst",
    model="gemini-2.5-flash",
    description="Analyzes business metrics",
)

dashboard_builder = LlmAgent(
    name="dashboard_builder",
    model="gemini-2.5-flash",
    description="Creates dashboards and visualizations",
)

report_generator = LlmAgent(
    name="report_generator",
    model="gemini-2.5-flash",
    description="Generates business reports",
)

# ============================================================================
# WIRE HIERARCHY
# ============================================================================

# Wire specialists to team leads
sales_team_lead.tools = [
    AgentTool(agent=lead_qualifier),
    AgentTool(agent=pricing_specialist),
    AgentTool(agent=proposal_writer),
    AgentTool(agent=contract_generator),
    AgentTool(agent=demo_scheduler),
]

support_team_lead.tools = [
    AgentTool(agent=ticket_triager),
    AgentTool(agent=technical_support),
    AgentTool(agent=billing_support),
    AgentTool(agent=account_support),
    AgentTool(agent=escalation_handler),
]

success_team_lead.tools = [
    AgentTool(agent=onboarding_specialist),
    AgentTool(agent=adoption_tracker),
    AgentTool(agent=renewal_specialist),
    AgentTool(agent=health_monitor),
]

dev_team_lead.tools = [
    AgentTool(agent=backend_developer),
    AgentTool(agent=frontend_developer),
    AgentTool(agent=database_specialist),
    AgentTool(agent=api_architect),
    AgentTool(agent=code_reviewer),
]

qa_team_lead.tools = [
    AgentTool(agent=test_planner),
    AgentTool(agent=integration_tester),
    AgentTool(agent=performance_tester),
    AgentTool(agent=automation_engineer),
]

devops_team_lead.tools = [
    AgentTool(agent=deployment_engineer),
    AgentTool(agent=infrastructure_engineer),
    AgentTool(agent=monitoring_specialist),
]

finance_team_lead.tools = [
    AgentTool(agent=billing_analyst),
    AgentTool(agent=payment_processor),
    AgentTool(agent=revenue_tracker),
]

analytics_team_lead.tools = [
    AgentTool(agent=metrics_analyst),
    AgentTool(agent=dashboard_builder),
    AgentTool(agent=report_generator),
]

# Wire team leads to supervisors
customer_operations.tools = [
    AgentTool(agent=sales_team_lead),
    AgentTool(agent=support_team_lead),
    AgentTool(agent=success_team_lead),
]

product_operations.tools = [
    AgentTool(agent=dev_team_lead),
    AgentTool(agent=qa_team_lead),
    AgentTool(agent=devops_team_lead),
]

business_operations.tools = [
    AgentTool(agent=finance_team_lead),
    AgentTool(agent=analytics_team_lead),
]

# Wire supervisors to executive
executive_coordinator.tools = [
    AgentTool(agent=customer_operations),
    AgentTool(agent=product_operations),
    AgentTool(agent=business_operations),
]

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def main():
    # Example 1: Customer inquiry
    result = await executive_coordinator.invoke(
        "Customer wants pricing for 500 user licenses of our enterprise plan"
    )
    # Routes: executive → customer_ops → sales_team_lead → pricing_specialist

    # Example 2: Support ticket
    result = await executive_coordinator.invoke(
        "Customer reporting payment failure on credit card ending in 4242"
    )
    # Routes: executive → customer_ops → support_team_lead → billing_support

    # Example 3: Feature request
    result = await executive_coordinator.invoke(
        "We need to add SSO authentication support for enterprise customers"
    )
    # Routes: executive → product_ops → dev_team_lead → backend_developer

    # Example 4: Cross-department coordination
    result = await executive_coordinator.invoke(
        "Customer wants to upgrade from 100 to 500 licenses. Need pricing, contract update, and billing changes."
    )
    # Routes to: sales (pricing), finance (billing), success (account management)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Agent Count Summary

| Level | Count | Total |
|-------|-------|-------|
| L1: Executive | 1 | 1 |
| L2: Supervisors | 3 | 4 |
| L3: Team Leads | 8 | 12 |
| L4: Specialists | 41 | 53 |

## Delegation Patterns

### Pattern 1: Direct Delegation

```
Customer inquiry → Executive → Customer Ops → Sales Lead → Pricing Specialist
```

**Total hops:** 4
**Latency:** ~1.5-2s

### Pattern 2: Parallel Delegation

```
Complex request → Executive → [Customer Ops, Product Ops, Business Ops] (parallel)
```

**Total hops:** 2 (parallel)
**Latency:** ~1-1.5s

### Pattern 3: Cross-Department

```
Upgrade request → Executive → Customer Ops → Sales Lead
                           ↓
                       Business Ops → Finance Lead
```

**Coordination at:** Executive level
**Total hops:** 4 (2 branches)

## Monitoring

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class HierarchyMetrics:
    """Track enterprise hierarchy metrics."""
    total_invocations: int = 0
    invocations_by_level: Dict[int, int] = field(default_factory=dict)
    invocations_by_agent: Dict[str, int] = field(default_factory=dict)
    avg_delegation_depth: float = 0.0

metrics = HierarchyMetrics()

def track_invocation(agent_name: str, level: int):
    metrics.total_invocations += 1
    metrics.invocations_by_level[level] = metrics.invocations_by_level.get(level, 0) + 1
    metrics.invocations_by_agent[agent_name] = metrics.invocations_by_agent.get(agent_name, 0) + 1

# After 1000 requests
print(f"Total invocations: {metrics.total_invocations}")
print(f"L1 (Executive): {metrics.invocations_by_level[1]}")  # 1000 (all requests)
print(f"L2 (Supervisors): {metrics.invocations_by_level[2]}")  # ~900
print(f"L3 (Team Leads): {metrics.invocations_by_level[3]}")  # ~800
print(f"L4 (Specialists): {metrics.invocations_by_level[4]}")  # ~750
```

## Cost Optimization

```python
# Model distribution
models = {
    "gemini-2.5-pro": 1,    # Executive only
    "gemini-2.5-flash": 52,  # Everyone else
}

# Cost per 1M tokens (input/output)
costs = {
    "pro": {"input": 1.25, "output": 5.00},
    "flash": {"input": 0.075, "output": 0.30},
}

# Assuming 1000 requests/day, avg 500 tokens input, 200 tokens output
daily_tokens = {
    "executive": {"input": 500_000, "output": 200_000},  # 1000 requests
    "supervisors": {"input": 450_000, "output": 180_000},  # ~900 requests
    "specialists": {"input": 375_000, "output": 150_000},  # ~750 requests
}

# Daily cost calculation
executive_cost = (500_000/1_000_000 * 1.25) + (200_000/1_000_000 * 5.00)
# = $0.625 + $1.00 = $1.625

supervisors_cost = (450_000/1_000_000 * 0.075) + (180_000/1_000_000 * 0.30)
# = $0.034 + $0.054 = $0.088 per supervisor × 3 = $0.264

specialists_cost = (375_000/1_000_000 * 0.075) + (150_000/1_000_000 * 0.30)
# = $0.028 + $0.045 = $0.073 per specialist × 41 = $2.993

# Total daily cost: ~$4.88
# Monthly cost (30 days): ~$146.40
```
