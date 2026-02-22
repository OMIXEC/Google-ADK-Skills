# Hierarchical Routing Examples

## Example 1: Corporate Organization Structure

### Scenario
Company-wide request routing through a hierarchical organization with executives, department heads, and individual contributors.

### Architecture
```
                                    CEO
                                     │
                ┌────────────────────┼────────────────────┐
                │                    │                    │
               CTO                  CFO                  COO
                │                    │                    │
        ┌───────┼───────┐    ┌──────┼──────┐    ┌───────┼───────┐
   Eng Lead  Prod Lead   Sales Lead  Finance   Ops Lead  Support
        │         │           │         │           │         │
    Backend   Designer    AE       Analyst    Logistics   CS Rep
    Frontend  PM          SDR      Controller  Warehouse   Tech Support
```

### Implementation

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# ============= Level 3: Individual Contributors =============

# Engineering team
backend_engineer = LlmAgent(
    name="backend_engineer",
    instruction="""
    Handle backend development tasks:
    - API development
    - Database design
    - Server-side logic
    - Integration development
    """
)

frontend_engineer = LlmAgent(
    name="frontend_engineer",
    instruction="""
    Handle frontend development tasks:
    - UI implementation
    - Client-side logic
    - Component development
    - User experience
    """
)

# Product team
designer = LlmAgent(
    name="designer",
    instruction="""
    Handle design tasks:
    - UI/UX design
    - Design systems
    - User research
    - Prototyping
    """
)

product_manager = LlmAgent(
    name="product_manager",
    instruction="""
    Handle product management tasks:
    - Feature planning
    - Requirements gathering
    - Roadmap planning
    - Stakeholder coordination
    """
)

# Sales team
account_executive = LlmAgent(
    name="account_executive",
    instruction="""
    Handle sales tasks:
    - Customer demos
    - Proposal creation
    - Deal negotiation
    - Account management
    """
)

sales_dev_rep = LlmAgent(
    name="sales_dev_rep",
    instruction="""
    Handle sales development:
    - Lead qualification
    - Outreach campaigns
    - Demo scheduling
    - Prospect research
    """
)

# Finance team
financial_analyst = LlmAgent(
    name="financial_analyst",
    instruction="""
    Handle financial analysis:
    - Financial modeling
    - Budget analysis
    - Revenue forecasting
    - Cost optimization
    """
)

controller = LlmAgent(
    name="controller",
    instruction="""
    Handle accounting:
    - Books management
    - Financial reporting
    - Compliance
    - Audit preparation
    """
)

# Operations team
logistics_manager = LlmAgent(
    name="logistics_manager",
    instruction="""
    Handle logistics:
    - Supply chain management
    - Vendor coordination
    - Inventory management
    - Shipping coordination
    """
)

warehouse_manager = LlmAgent(
    name="warehouse_manager",
    instruction="""
    Handle warehouse operations:
    - Inventory tracking
    - Order fulfillment
    - Storage optimization
    - Quality control
    """
)

# Customer success team
customer_success_rep = LlmAgent(
    name="customer_success_rep",
    instruction="""
    Handle customer success:
    - Onboarding
    - Customer training
    - Relationship management
    - Renewal management
    """
)

technical_support = LlmAgent(
    name="technical_support",
    instruction="""
    Handle technical support:
    - Troubleshooting
    - Bug investigation
    - Customer education
    - Escalation management
    """
)

# ============= Level 2: Department Heads =============

engineering_lead = LlmAgent(
    name="engineering_lead",
    model="gemini-2.5-flash",
    description="Manages engineering team",
    tools=[
        AgentTool(agent=backend_engineer),
        AgentTool(agent=frontend_engineer),
    ],
    instruction="""
    Delegate engineering work:
    - Backend tasks → backend_engineer
    - Frontend tasks → frontend_engineer

    For full-stack tasks, coordinate both engineers.
    """
)

product_lead = LlmAgent(
    name="product_lead",
    model="gemini-2.5-flash",
    description="Manages product team",
    tools=[
        AgentTool(agent=designer),
        AgentTool(agent=product_manager),
    ],
    instruction="""
    Delegate product work:
    - Design tasks → designer
    - Product planning → product_manager

    For feature development, coordinate both.
    """
)

sales_lead = LlmAgent(
    name="sales_lead",
    model="gemini-2.5-flash",
    description="Manages sales team",
    tools=[
        AgentTool(agent=account_executive),
        AgentTool(agent=sales_dev_rep),
    ],
    instruction="""
    Delegate sales work:
    - Active deals → account_executive
    - New lead generation → sales_dev_rep

    For large accounts, coordinate both.
    """
)

finance_lead = LlmAgent(
    name="finance_lead",
    model="gemini-2.5-flash",
    description="Chief Financial Officer",
    tools=[
        AgentTool(agent=financial_analyst),
        AgentTool(agent=controller),
    ],
    instruction="""
    Delegate finance work:
    - Analysis and planning → financial_analyst
    - Accounting and reporting → controller

    For financial planning, coordinate both.
    """
)

operations_lead = LlmAgent(
    name="operations_lead",
    model="gemini-2.5-flash",
    description="Manages operations",
    tools=[
        AgentTool(agent=logistics_manager),
        AgentTool(agent=warehouse_manager),
    ],
    instruction="""
    Delegate operations work:
    - Supply chain and vendors → logistics_manager
    - Warehouse and fulfillment → warehouse_manager

    For end-to-end fulfillment, coordinate both.
    """
)

customer_success_lead = LlmAgent(
    name="customer_success_lead",
    model="gemini-2.5-flash",
    description="Manages customer success",
    tools=[
        AgentTool(agent=customer_success_rep),
        AgentTool(agent=technical_support),
    ],
    instruction="""
    Delegate customer work:
    - Account management → customer_success_rep
    - Technical issues → technical_support

    For escalations, coordinate both.
    """
)

# ============= Level 1: C-Level Executives =============

cto = LlmAgent(
    name="cto",
    model="gemini-2.5-flash",
    description="Chief Technology Officer",
    tools=[
        AgentTool(agent=engineering_lead),
        AgentTool(agent=product_lead),
    ],
    instruction="""
    Lead technology organization:
    - Engineering tasks → engineering_lead
    - Product tasks → product_lead

    Coordinate engineering and product for features.
    Provide technical leadership and strategy.
    """
)

cfo = LlmAgent(
    name="cfo",
    model="gemini-2.5-flash",
    description="Chief Financial Officer",
    tools=[
        AgentTool(agent=finance_lead),
        AgentTool(agent=sales_lead),
    ],
    instruction="""
    Lead revenue and finance:
    - Financial matters → finance_lead
    - Sales matters → sales_lead

    Coordinate finance and sales for revenue planning.
    Provide financial leadership and strategy.
    """
)

coo = LlmAgent(
    name="coo",
    model="gemini-2.5-flash",
    description="Chief Operating Officer",
    tools=[
        AgentTool(agent=operations_lead),
        AgentTool(agent=customer_success_lead),
    ],
    instruction="""
    Lead operations and customer success:
    - Operations tasks → operations_lead
    - Customer tasks → customer_success_lead

    Coordinate ops and CS for customer experience.
    Provide operational leadership and strategy.
    """
)

# ============= Level 0: CEO =============

ceo = LlmAgent(
    name="ceo",
    model="gemini-2.5-flash",
    description="Chief Executive Officer - routes to appropriate executive",
    tools=[
        AgentTool(agent=cto),
        AgentTool(agent=cfo),
        AgentTool(agent=coo),
    ],
    instruction="""
    You are the CEO routing company-wide requests.

    Delegate to executives:

    **CTO (Technology):**
    - Product development
    - Engineering work
    - Technical architecture
    - Technology strategy

    **CFO (Finance & Sales):**
    - Financial planning
    - Sales and revenue
    - Budget questions
    - Pricing strategy

    **COO (Operations & Customers):**
    - Operations and logistics
    - Customer success
    - Customer support
    - Process improvement

    For cross-functional initiatives, coordinate multiple executives.
    Provide executive-level guidance and decision-making.
    """
)

# ============= Usage =============

# Example: Product feature request
result = ceo.run("We need to build a new dashboard feature for enterprise customers")
# CEO → CTO → Engineering Lead + Product Lead → Backend Engineer + Designer

# Example: Financial planning
result = ceo.run("What's our revenue forecast for next quarter?")
# CEO → CFO → Finance Lead → Financial Analyst

# Example: Customer escalation
result = ceo.run("Enterprise customer is having technical issues with billing")
# CEO → COO + CFO → Customer Success Lead + Finance Lead → Technical Support + Controller
```

---

## Example 2: Healthcare System

### Scenario
Hospital management system with clinical, administrative, and billing departments.

### Architecture
```
                            Hospital Director
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
        Clinical Director   Administrative Dir    Billing Director
                │                   │                   │
        ┌───────┼───────┐   ┌──────┼──────┐    ┌──────┼──────┐
    Doctor   Nurse    Pharm  HR   Scheduling  Insurance  Claims
```

### Implementation

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Level 3: Specialists
doctor = LlmAgent(name="doctor", instruction="Handle medical diagnosis and treatment")
nurse = LlmAgent(name="nurse", instruction="Handle patient care and procedures")
pharmacist = LlmAgent(name="pharmacist", instruction="Handle medication management")

hr_specialist = LlmAgent(name="hr", instruction="Handle employee matters")
scheduler = LlmAgent(name="scheduler", instruction="Handle appointment scheduling")

insurance_specialist = LlmAgent(name="insurance", instruction="Handle insurance verification")
claims_specialist = LlmAgent(name="claims", instruction="Handle claims processing")

# Level 2: Department Directors
clinical_director = LlmAgent(
    name="clinical_director",
    tools=[
        AgentTool(agent=doctor),
        AgentTool(agent=nurse),
        AgentTool(agent=pharmacist),
    ],
    instruction="""
    Route clinical matters:
    - Medical diagnosis and treatment → doctor
    - Patient care and procedures → nurse
    - Medication questions → pharmacist

    Ensure patient safety and quality care.
    """
)

administrative_director = LlmAgent(
    name="administrative_director",
    tools=[
        AgentTool(agent=hr_specialist),
        AgentTool(agent=scheduler),
    ],
    instruction="""
    Route administrative matters:
    - Employee issues → hr
    - Appointment scheduling → scheduler

    Ensure efficient operations.
    """
)

billing_director = LlmAgent(
    name="billing_director",
    tools=[
        AgentTool(agent=insurance_specialist),
        AgentTool(agent=claims_specialist),
    ],
    instruction="""
    Route billing matters:
    - Insurance verification → insurance
    - Claims processing → claims

    Ensure accurate billing and reimbursement.
    """
)

# Level 1: Hospital Director
hospital_director = LlmAgent(
    name="hospital_director",
    tools=[
        AgentTool(agent=clinical_director),
        AgentTool(agent=administrative_director),
        AgentTool(agent=billing_director),
    ],
    instruction="""
    Route hospital matters to appropriate department:

    - Patient care, medical questions → clinical_director
    - Scheduling, HR, operations → administrative_director
    - Billing, insurance, claims → billing_director

    For patient admissions, coordinate clinical and administrative.
    For procedures, coordinate clinical and billing.
    """
)

# Usage
result = hospital_director.run("Patient needs surgery scheduled and insurance verified")
# Hospital Director → Clinical Director + Administrative Director + Billing Director
```

---

## Example 3: E-commerce Platform

### Scenario
Multi-department e-commerce organization handling customers, inventory, and marketing.

### Architecture
```
                        Platform Director
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
    Customer Service Dir   Inventory Dir      Marketing Dir
            │                   │                   │
        CS Rep             Warehouse Mgr        Content Creator
        Tech Support       Procurement         Ad Specialist
```

### Implementation

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Level 3: Specialists
cs_rep = LlmAgent(
    name="cs_rep",
    instruction="Handle customer inquiries, returns, and general questions"
)

tech_support = LlmAgent(
    name="tech_support",
    instruction="Handle technical issues, bugs, and troubleshooting"
)

warehouse_manager = LlmAgent(
    name="warehouse_manager",
    instruction="Handle inventory, fulfillment, and shipping"
)

procurement = LlmAgent(
    name="procurement",
    instruction="Handle vendor relations, purchasing, and stock replenishment"
)

content_creator = LlmAgent(
    name="content_creator",
    instruction="Handle product descriptions, blog posts, and content"
)

ad_specialist = LlmAgent(
    name="ad_specialist",
    instruction="Handle advertising campaigns, PPC, and promotions"
)

# Level 2: Directors
customer_service_director = LlmAgent(
    name="customer_service_director",
    tools=[
        AgentTool(agent=cs_rep),
        AgentTool(agent=tech_support),
    ],
    instruction="""
    Route customer matters:
    - General questions, returns, orders → cs_rep
    - Technical issues, bugs → tech_support

    Ensure excellent customer experience.
    """
)

inventory_director = LlmAgent(
    name="inventory_director",
    tools=[
        AgentTool(agent=warehouse_manager),
        AgentTool(agent=procurement),
    ],
    instruction="""
    Route inventory matters:
    - Warehouse, fulfillment, shipping → warehouse_manager
    - Purchasing, vendors, restocking → procurement

    Ensure optimal inventory levels and fulfillment.
    """
)

marketing_director = LlmAgent(
    name="marketing_director",
    tools=[
        AgentTool(agent=content_creator),
        AgentTool(agent=ad_specialist),
    ],
    instruction="""
    Route marketing matters:
    - Content, descriptions, blog → content_creator
    - Ads, campaigns, promotions → ad_specialist

    Ensure effective marketing and customer acquisition.
    """
)

# Level 1: Platform Director
platform_director = LlmAgent(
    name="platform_director",
    model="gemini-2.5-flash",
    tools=[
        AgentTool(agent=customer_service_director),
        AgentTool(agent=inventory_director),
        AgentTool(agent=marketing_director),
    ],
    instruction="""
    Route platform matters to appropriate department:

    **Customer Service:**
    - Customer inquiries
    - Returns and refunds
    - Technical support
    - Order issues

    **Inventory:**
    - Stock levels
    - Fulfillment
    - Shipping
    - Vendor relations

    **Marketing:**
    - Product launches
    - Advertising campaigns
    - Content creation
    - Promotions

    For product launches: coordinate inventory and marketing
    For customer issues: coordinate customer service and inventory
    """
)

# Usage examples
result = platform_director.run("Customer says order hasn't shipped yet")
# Platform Director → Customer Service Director → CS Rep
# May also involve Inventory Director → Warehouse Manager

result = platform_director.run("Launch new product line next month")
# Platform Director → Inventory Director + Marketing Director
# → Procurement + Warehouse Manager + Content Creator + Ad Specialist
```

---

## Best Practices for Hierarchical Routing

### 1. Clear Responsibility Boundaries

Each level should have well-defined scope:

```python
# Good: Clear separation
level_1_instruction = "Route to departments: engineering, sales, or support"
level_2_instruction = "Route within department: to specific team or specialist"

# Bad: Overlapping responsibilities
level_1_instruction = "Route anywhere in the organization"
level_2_instruction = "Also route anywhere in the organization"
```

### 2. Limit Hierarchy Depth

Keep hierarchies to 2-4 levels maximum:

```
✓ Good: CEO → Director → Manager → Specialist (4 levels)
✗ Bad: CEO → VP → Director → Manager → Lead → Senior → Junior (7 levels)
```

### 3. Delegation Instructions

Each supervisor should have clear delegation logic:

```python
supervisor_instruction = """
Delegate based on request type:

TYPE A (keywords: x, y, z) → Specialist A
TYPE B (keywords: a, b, c) → Specialist B
TYPE C (complex cases) → Coordinate Specialist A + B

For cross-functional requests, delegate to multiple specialists.
"""
```

### 4. Escalation Paths

Define how to escalate beyond normal hierarchy:

```python
specialist_instruction = """
Handle routine requests directly.

Escalate to supervisor if:
- Requires policy decision
- Involves multiple departments
- Customer is VIP or escalated
- Request exceeds authority level
"""
```

### 5. Cross-Hierarchy Communication

Allow lateral communication when needed:

```python
# Option 1: Through shared supervisor
engineer = LlmAgent(tools=[AgentTool(agent=shared_supervisor)])

# Option 2: Direct peer access
engineer = LlmAgent(tools=[AgentTool(agent=designer)])  # Peer-to-peer
```

---

## Monitoring and Debugging

### Trace Delegation Paths

```python
class DelegationTracer:
    def __init__(self):
        self.path = []

    def trace(self, from_agent, to_agent, reason):
        self.path.append({
            "from": from_agent,
            "to": to_agent,
            "reason": reason,
            "timestamp": datetime.now()
        })

    def print_path(self):
        for step in self.path:
            print(f"{step['from']} → {step['to']}: {step['reason']}")

# Usage
tracer = DelegationTracer()
# After each delegation: tracer.trace("CEO", "CTO", "Engineering request")
```

### Measure Delegation Efficiency

```python
class DelegationMetrics:
    def __init__(self):
        self.delegations = []

    def record(self, levels_traversed, time_taken, request_type):
        self.delegations.append({
            "levels": levels_traversed,
            "time": time_taken,
            "type": request_type
        })

    def average_levels(self):
        return sum(d["levels"] for d in self.delegations) / len(self.delegations)

    def average_time(self):
        return sum(d["time"] for d in self.delegations) / len(self.delegations)
```

---

## Common Patterns

### Pattern 1: Strict Hierarchy
Each level only communicates with adjacent levels.

### Pattern 2: Skip-Level Access
Higher levels can access lower levels directly for urgent matters.

### Pattern 3: Matrix Organization
Agents report to multiple supervisors (functional + project).

### Pattern 4: Flat with Specialists
One supervisor with many specialized agents (2-level hierarchy).

---

## Anti-Patterns to Avoid

### 1. Too Deep
More than 4-5 levels makes routing slow and error-prone.

### 2. Unclear Delegation
Supervisors without clear criteria for delegation.

### 3. No Lateral Communication
Forcing all communication through hierarchy creates bottlenecks.

### 4. Single Point of Failure
One supervisor handling too many subordinates (>7 agents).
