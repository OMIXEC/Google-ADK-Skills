# Multi-Agent Team Patterns Reference

## Overview

This reference covers advanced team collaboration patterns for multi-agent systems. These patterns enable agents to work together effectively on complex tasks requiring diverse expertise, consensus, debate, or sequential refinement.

---

## Pattern 1: Debate Pattern

### Concept

Multiple agents argue different perspectives to thoroughly explore a topic. A moderator synthesizes the debate into balanced conclusions.

### When to Use

- **Decision-making requiring multiple viewpoints**: Major strategic decisions
- **Exploring pros and cons**: Investment decisions, technology choices
- **Critical analysis**: Policy evaluation, risk assessment
- **Controversial topics**: Ethical dilemmas, trade-off decisions

### Structure

```
Topic → Debater A (Pro) ⇄ Debater B (Con) → Moderator → Synthesized Conclusion
```

### Implementation

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Perspective 1: Optimist/Proponent
proponent = LlmAgent(
    name="proponent",
    model="gemini-2.5-flash",
    instruction="""
    Argue in favor of the proposition:

    **Responsibilities:**
    - Present strongest arguments FOR
    - Highlight benefits and opportunities
    - Counter opposing arguments
    - Use evidence and examples

    **Tone:**
    - Constructive and persuasive
    - Fact-based, not emotional
    - Acknowledge valid concerns while maintaining position
    """
)

# Perspective 2: Skeptic/Opponent
opponent = LlmAgent(
    name="opponent",
    model="gemini-2.5-flash",
    instruction="""
    Argue against the proposition:

    **Responsibilities:**
    - Present strongest arguments AGAINST
    - Highlight risks and downsides
    - Counter supporting arguments
    - Use evidence and examples

    **Tone:**
    - Critical but fair
    - Fact-based, not dismissive
    - Acknowledge valid points while maintaining skepticism
    """
)

# Moderator synthesizes
moderator = LlmAgent(
    name="moderator",
    model="gemini-2.5-pro",
    description="Moderates debate and produces balanced analysis",
    instruction="""
    Facilitate debate and synthesize conclusions:

    **Debate Process:**
    1. Present topic to both debaters
    2. Collect initial arguments from proponent
    3. Collect counter-arguments from opponent
    4. Allow proponent to respond to concerns
    5. Allow opponent to respond to rebuttals

    **Synthesis:**
    1. Summarize both perspectives fairly
    2. Identify points of agreement
    3. Highlight key points of disagreement
    4. Evaluate strength of each argument
    5. Provide balanced recommendation

    **Output Format:**
    # Debate Summary

    ## Proposition
    [Topic being debated]

    ## Arguments For
    [Proponent's strongest points]

    ## Arguments Against
    [Opponent's strongest points]

    ## Analysis
    [Balanced evaluation]

    ## Recommendation
    [Nuanced conclusion with conditions]
    """,
    tools=[
        AgentTool(agent=proponent),
        AgentTool(agent=opponent),
    ],
)
```

### Variations

**Multi-Perspective Debate:**
More than two perspectives (e.g., technical, business, legal).

```python
technical_perspective = LlmAgent(instruction="Argue from technical viewpoint")
business_perspective = LlmAgent(instruction="Argue from business viewpoint")
legal_perspective = LlmAgent(instruction="Argue from legal viewpoint")

moderator = LlmAgent(
    tools=[
        AgentTool(agent=technical_perspective),
        AgentTool(agent=business_perspective),
        AgentTool(agent=legal_perspective),
    ]
)
```

**Socratic Debate:**
One agent asks probing questions, the other defends their position.

```python
questioner = LlmAgent(instruction="Ask challenging questions to test reasoning")
defender = LlmAgent(instruction="Defend position against questions")
```

### Example Use Cases

1. **Should we migrate to microservices?**
   - Proponent: Scalability, maintainability, team autonomy
   - Opponent: Complexity, operational overhead, distributed system challenges

2. **Should we use AI for hiring decisions?**
   - Proponent: Efficiency, bias reduction, data-driven
   - Opponent: Privacy concerns, algorithmic bias, legal risks

3. **Should we open-source our core product?**
   - Proponent: Community contribution, transparency, ecosystem
   - Opponent: Competitive advantage, IP concerns, support burden

---

## Pattern 2: Consensus Pattern

### Concept

Multiple agents independently evaluate a proposal and vote. A consensus builder tallies votes, analyzes reasoning, and determines collective decision.

### When to Use

- **Democratic decision-making**: Committee decisions, board approvals
- **Quality assessment**: Code review, design review
- **Ensemble predictions**: Multiple models voting on classification
- **Risk evaluation**: Independent risk assessments

### Structure

```
Proposal → Voter 1 ↘
         → Voter 2 → Consensus Builder → Decision + Rationale
         → Voter 3 ↗
```

### Implementation

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Voter 1: Security Expert
security_voter = LlmAgent(
    name="security_voter",
    model="gemini-2.5-flash",
    instruction="""
    Evaluate proposal from security perspective.

    **Assessment Criteria:**
    - Authentication and authorization
    - Data protection
    - Vulnerability risks
    - Compliance requirements

    **Vote:**
    - APPROVE: Security requirements met
    - REJECT: Security concerns unresolved
    - ABSTAIN: Insufficient information

    **Output Format:**
    {
        "voter": "security",
        "vote": "APPROVE|REJECT|ABSTAIN",
        "confidence": 0-100,
        "rationale": "Explanation of vote",
        "concerns": ["concern1", "concern2"],
        "conditions": ["condition1", "condition2"]
    }
    """
)

# Voter 2: Performance Expert
performance_voter = LlmAgent(
    name="performance_voter",
    model="gemini-2.5-flash",
    instruction="""
    Evaluate proposal from performance perspective.

    **Assessment Criteria:**
    - Response time impact
    - Scalability
    - Resource utilization
    - Throughput capacity

    **Vote:**
    - APPROVE: Performance acceptable
    - REJECT: Performance concerns
    - ABSTAIN: Needs performance testing

    [Same output format as security_voter]
    """
)

# Voter 3: Maintainability Expert
maintainability_voter = LlmAgent(
    name="maintainability_voter",
    model="gemini-2.5-flash",
    instruction="""
    Evaluate proposal from maintainability perspective.

    **Assessment Criteria:**
    - Code clarity
    - Documentation quality
    - Testing coverage
    - Long-term sustainability

    **Vote:**
    - APPROVE: Maintainable
    - REJECT: Technical debt concerns
    - ABSTAIN: Needs revision

    [Same output format]
    """
)

# Consensus Builder
consensus_builder = LlmAgent(
    name="consensus_builder",
    model="gemini-2.5-pro",
    description="Collects votes and determines consensus",
    instruction="""
    Collect votes from all experts and determine consensus.

    **Process:**
    1. Present proposal to each voter independently
    2. Collect votes and rationales
    3. Tally results
    4. Analyze voting patterns
    5. Determine outcome based on consensus rules

    **Consensus Rules:**
    - **Unanimous APPROVE** → APPROVED
    - **Supermajority APPROVE** (≥75%) → APPROVED_WITH_CONDITIONS
    - **Majority APPROVE** (>50%) → APPROVED_WITH_CONCERNS
    - **Majority REJECT** → REJECTED
    - **Tie or all ABSTAIN** → NEEDS_REVISION

    **Output:**
    {
        "decision": "APPROVED|APPROVED_WITH_CONDITIONS|APPROVED_WITH_CONCERNS|REJECTED|NEEDS_REVISION",
        "vote_tally": {
            "approve": N,
            "reject": M,
            "abstain": K
        },
        "voter_breakdown": [...],
        "common_concerns": [...],
        "required_conditions": [...],
        "action_items": [...]
    }
    """,
    tools=[
        AgentTool(agent=security_voter),
        AgentTool(agent=performance_voter),
        AgentTool(agent=maintainability_voter),
    ],
)
```

### Variations

**Weighted Voting:**
Some voters have more influence.

```python
instruction = """
Votes are weighted:
- Security expert: 40%
- Performance expert: 30%
- Maintainability expert: 30%

Calculate weighted score for final decision.
"""
```

**Iterative Consensus:**
If no consensus, iterate with more information.

```python
instruction = """
If no consensus:
1. Identify information gaps
2. Request clarification
3. Re-vote with new information
Maximum 3 iterations.
"""
```

### Example Use Cases

1. **Code Review Approval**
   - Voters: Technical reviewer, security reviewer, architecture reviewer
   - Decision: Merge, Request changes, Reject

2. **Design Proposal Evaluation**
   - Voters: UX expert, accessibility expert, brand expert
   - Decision: Approve, Revise, Reject

3. **Feature Prioritization**
   - Voters: Product manager, engineering lead, customer success
   - Decision: High priority, Medium, Low, Deferred

---

## Pattern 3: Specialist Team Pattern

### Concept

Domain experts collaborate on complex problems requiring deep, diverse expertise. A team lead coordinates specialists and synthesizes their contributions.

### When to Use

- **Cross-functional projects**: Features spanning multiple domains
- **Complex problem-solving**: Requires multiple areas of expertise
- **Technical design reviews**: Architecture spanning front/back/infra
- **Multidisciplinary research**: Combining different fields

### Structure

```
                      Team Lead
                          ↓
        ┌─────────┬───────┼───────┬─────────┐
   Specialist A  Spec B  Spec C  Spec D  Spec E
```

### Implementation

```python
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

# Specialist 1: Backend
backend_specialist = LlmAgent(
    name="backend_specialist",
    model="gemini-2.5-flash",
    instruction="""
    Backend development expert.

    **Expertise:**
    - API design (REST, GraphQL, gRPC)
    - Database schema and queries
    - Business logic and domain models
    - Scalability and performance
    - Integration patterns

    **Deliverables:**
    - API specifications
    - Database schema
    - Service architecture
    - Performance requirements
    """
)

# Specialist 2: Frontend
frontend_specialist = LlmAgent(
    name="frontend_specialist",
    model="gemini-2.5-flash",
    instruction="""
    Frontend development expert.

    **Expertise:**
    - UI/UX implementation
    - Component architecture
    - State management
    - Performance optimization
    - Accessibility

    **Deliverables:**
    - Component structure
    - State management approach
    - UI specifications
    - User flow diagrams
    """
)

# Specialist 3: DevOps
devops_specialist = LlmAgent(
    name="devops_specialist",
    model="gemini-2.5-flash",
    instruction="""
    DevOps and infrastructure expert.

    **Expertise:**
    - CI/CD pipelines
    - Container orchestration
    - Cloud infrastructure
    - Monitoring and observability
    - Disaster recovery

    **Deliverables:**
    - Deployment architecture
    - CI/CD workflow
    - Monitoring strategy
    - Scaling approach
    """
)

# Specialist 4: Security
security_specialist = LlmAgent(
    name="security_specialist",
    model="gemini-2.5-flash",
    instruction="""
    Security and compliance expert.

    **Expertise:**
    - Threat modeling
    - Authentication/authorization
    - Data protection
    - Compliance (GDPR, SOC2, etc.)
    - Secure coding practices

    **Deliverables:**
    - Threat model
    - Security architecture
    - Compliance requirements
    - Security testing plan
    """
)

# Specialist 5: Data
data_specialist = LlmAgent(
    name="data_specialist",
    model="gemini-2.5-flash",
    instruction="""
    Data and analytics expert.

    **Expertise:**
    - Data modeling
    - ETL pipelines
    - Analytics and reporting
    - Data governance
    - ML/AI integration

    **Deliverables:**
    - Data model
    - Analytics requirements
    - Reporting dashboards
    - Data pipeline architecture
    """
)

# Team Lead coordinates specialists
tech_lead = LlmAgent(
    name="tech_lead",
    model="gemini-2.5-pro",
    description="Coordinates specialist team for comprehensive technical solutions",
    instruction="""
    You are the technical lead coordinating a specialist team.

    **Team:**
    - backend_specialist: APIs, business logic, databases
    - frontend_specialist: UI/UX, components, state
    - devops_specialist: Infrastructure, deployment, monitoring
    - security_specialist: Security, compliance, threat modeling
    - data_specialist: Data modeling, analytics, pipelines

    **Coordination Process:**
    1. **Requirement Analysis**: Understand project scope and constraints
    2. **Specialist Consultation**: Engage relevant specialists
    3. **Cross-Domain Integration**: Ensure specialists align on interfaces
    4. **Dependency Management**: Identify and resolve dependencies
    5. **Synthesis**: Combine specialist inputs into cohesive design

    **Key Responsibilities:**
    - Ensure specialists communicate on shared concerns
    - Resolve conflicts between specialist recommendations
    - Identify gaps in coverage
    - Maintain architectural consistency
    - Balance trade-offs across domains

    **Deliverable:**
    Comprehensive technical design document with:
    - Executive summary
    - Architecture overview
    - Specialist contributions (each domain)
    - Integration points and dependencies
    - Implementation timeline
    - Risk assessment
    """,
    tools=[
        AgentTool(agent=backend_specialist),
        AgentTool(agent=frontend_specialist),
        AgentTool(agent=devops_specialist),
        AgentTool(agent=security_specialist),
        AgentTool(agent=data_specialist),
    ],
)
```

### Coordination Strategies

**Sequential Consultation:**
Lead consults specialists one by one.

**Parallel Consultation:**
Lead consults all specialists simultaneously.

**Iterative Refinement:**
Multiple rounds of consultation as design evolves.

**Cross-Specialist Collaboration:**
Specialists directly collaborate on interfaces.

### Example Use Cases

1. **E-commerce Platform Design**
   - Backend: Product catalog, order processing, payment
   - Frontend: Shopping cart, checkout flow, user dashboard
   - DevOps: Auto-scaling, CDN, database replication
   - Security: PCI compliance, user data protection
   - Data: Customer analytics, inventory forecasting

2. **Healthcare Application**
   - Backend: FHIR integration, clinical workflows
   - Frontend: Patient portal, clinician dashboard
   - DevOps: HIPAA-compliant infrastructure
   - Security: PHI protection, audit logging
   - Data: Clinical analytics, outcome reporting

---

## Pattern 4: Review Chain Pattern

### Concept

Sequential review process where each reviewer builds on previous feedback. Each reviewer has specific focus area and can see all prior reviews.

### When to Use

- **Code review workflows**: Multi-stage code approval
- **Document editing**: Progressive refinement
- **Quality assurance**: Multiple QA checks
- **Approval processes**: Hierarchical approvals

### Structure

```
Artifact → Reviewer 1 → Reviewer 2 → Reviewer 3 → Final Decision
             ↓            ↓            ↓              ↓
          Feedback 1   Feedback 2   Feedback 3   Consolidated
```

### Implementation

```python
from google.adk.agents import SequentialAgent, LlmAgent

# Reviewer 1: Technical Correctness
technical_reviewer = LlmAgent(
    name="technical_reviewer",
    model="gemini-2.5-flash",
    instruction="""
    Review for technical correctness and quality.

    **Focus Areas:**
    - Code correctness and logic
    - Best practices adherence
    - Error handling
    - Edge cases
    - Code smells and anti-patterns

    **Output:**
    {
        "reviewer": "technical",
        "status": "PASS|NEEDS_WORK|FAIL",
        "issues": [
            {
                "severity": "critical|major|minor",
                "location": "file:line",
                "description": "...",
                "suggestion": "..."
            }
        ],
        "overall_feedback": "..."
    }
    """
)

# Reviewer 2: Security (sees technical review)
security_reviewer = LlmAgent(
    name="security_reviewer",
    model="gemini-2.5-flash",
    instruction="""
    Review for security vulnerabilities.

    **You receive:**
    - Original code
    - Technical reviewer's feedback

    **Focus Areas:**
    - SQL injection, XSS, CSRF
    - Authentication/authorization flaws
    - Insecure data handling
    - Dependency vulnerabilities
    - Secrets management

    **Build on technical review:**
    - Note if technical issues have security implications
    - Identify security issues not caught by technical review

    [Same output format as technical_reviewer]
    """
)

# Reviewer 3: Architecture (sees both previous reviews)
architecture_reviewer = LlmAgent(
    name="architecture_reviewer",
    model="gemini-2.5-pro",
    instruction="""
    Review for architectural alignment.

    **You receive:**
    - Original code
    - Technical reviewer's feedback
    - Security reviewer's feedback

    **Focus Areas:**
    - Design pattern adherence
    - Architectural principles
    - Scalability and maintainability
    - Separation of concerns
    - Technical debt

    **Build on previous reviews:**
    - Identify if issues stem from architectural problems
    - Recommend architectural improvements
    - Assess long-term impact

    [Same output format]
    """
)

# Reviewer 4: Final Approval (sees all reviews)
approval_reviewer = LlmAgent(
    name="approval_reviewer",
    model="gemini-2.5-flash",
    instruction="""
    Make final approval decision based on all reviews.

    **You receive:**
    - Original code
    - All previous reviews and feedback

    **Responsibilities:**
    1. Synthesize all feedback
    2. Categorize issues by severity
    3. Determine if blocking issues exist
    4. Make approval decision
    5. Create consolidated action items

    **Decision Criteria:**
    - No critical issues → APPROVED
    - Critical issues present → REJECTED
    - Only minor/major issues → NEEDS_REVISION

    **Output:**
    {
        "decision": "APPROVED|NEEDS_REVISION|REJECTED",
        "summary": "Executive summary of all reviews",
        "critical_issues": [...],
        "major_issues": [...],
        "minor_issues": [...],
        "action_items": [
            {
                "priority": "P0|P1|P2",
                "description": "...",
                "assigned_to": "author",
                "blocking": true|false
            }
        ],
        "approval_conditions": [...]
    }
    """
)

# Sequential review chain
review_chain = SequentialAgent(
    name="code_review_chain",
    description="Multi-stage code review process",
    sub_agents=[
        technical_reviewer,
        security_reviewer,
        architecture_reviewer,
        approval_reviewer,
    ],
)
```

### Variations

**Fast-Track Review:**
Skip later reviewers if early reviewer rejects.

```python
# Add conditional logic in application layer
technical_result = technical_reviewer.run(code)
if technical_result.status == "FAIL":
    return {"decision": "REJECTED", "reason": "Failed technical review"}
else:
    continue_to_security_review()
```

**Parallel Review with Synthesis:**
All reviewers review in parallel, final reviewer synthesizes.

```python
from google.adk.agents import ParallelAgent

parallel_reviewers = ParallelAgent(
    sub_agents=[technical_reviewer, security_reviewer, architecture_reviewer]
)

workflow = SequentialAgent(
    sub_agents=[parallel_reviewers, approval_reviewer]
)
```

### Example Use Cases

1. **Pull Request Review**
   - Technical review → Security review → Architecture review → Approval

2. **Document Publication**
   - Content review → Legal review → Editorial review → Publication approval

3. **Design Review**
   - Functionality review → Accessibility review → Brand review → Approval

---

## Best Practices

### 1. Clear Role Definition

Each agent should have a specific, non-overlapping role.

### 2. Structured Communication

Use consistent output formats for inter-agent communication.

### 3. Manage Coordination Overhead

More agents = more coordination. Use hierarchical patterns for large teams.

### 4. Handle Disagreements

Define conflict resolution mechanisms (voting, moderator decision, escalation).

### 5. Track Progress

Log agent interactions for debugging and auditing.

### 6. Test Team Dynamics

Test individual agents, then test team interactions.

---

## Comparison Matrix

| Pattern | Agents | Communication | Use Case | Output |
|---------|--------|---------------|----------|--------|
| **Debate** | 2+ debaters + moderator | Adversarial + synthesis | Explore perspectives | Balanced analysis |
| **Consensus** | 3+ voters + builder | Independent votes | Democratic decision | Vote + rationale |
| **Specialist Team** | 3+ specialists + lead | Collaborative | Complex design | Comprehensive plan |
| **Review Chain** | 3+ reviewers (sequential) | Sequential feedback | Quality assurance | Approval + feedback |
