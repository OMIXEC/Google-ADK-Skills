# Parallel Workers Examples

## Example 1: Multi-Perspective Analysis

### Scenario
Analyze a business decision from technical, business, legal, and risk perspectives simultaneously.

### Architecture
```
                  ┌→ Technical Analyst ┐
                  ├→ Business Analyst  ├→ Aggregator → Final Report
Input Decision →├→ Legal Analyst     │
                  └→ Risk Analyst      ┘
```

### Implementation

```python
from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent

# Parallel analysts
technical_analyst = LlmAgent(
    name="technical_analyst",
    model="gemini-2.5-flash",
    instruction="""
    Analyze from technical perspective:

    **Assess:**
    1. Technical feasibility
    2. Implementation complexity
    3. Technology stack requirements
    4. Integration challenges
    5. Scalability considerations

    **Output:**
    - Feasibility score (1-10)
    - Key technical risks
    - Implementation timeline estimate
    - Required expertise
    """
)

business_analyst = LlmAgent(
    name="business_analyst",
    model="gemini-2.5-flash",
    instruction="""
    Analyze from business perspective:

    **Assess:**
    1. Cost-benefit analysis
    2. ROI potential
    3. Market fit
    4. Competitive advantage
    5. Resource requirements

    **Output:**
    - Business viability score (1-10)
    - Financial projections
    - Market opportunity size
    - Business risks
    """
)

legal_analyst = LlmAgent(
    name="legal_analyst",
    model="gemini-2.5-flash",
    instruction="""
    Analyze from legal/compliance perspective:

    **Assess:**
    1. Regulatory requirements
    2. Compliance risks
    3. Data privacy concerns (GDPR, CCPA)
    4. Intellectual property issues
    5. Contractual obligations

    **Output:**
    - Compliance score (1-10)
    - Legal risks and mitigation
    - Required certifications
    - Regulatory timeline
    """
)

risk_analyst = LlmAgent(
    name="risk_analyst",
    model="gemini-2.5-flash",
    instruction="""
    Analyze overall risks:

    **Assess:**
    1. Operational risks
    2. Financial risks
    3. Reputational risks
    4. Security risks
    5. Strategic risks

    **Output:**
    - Overall risk score (1-10)
    - Top 5 risks ranked by severity
    - Mitigation strategies
    - Fallback plans
    """
)

# Parallel analysis
analysis_team = ParallelAgent(
    name="multi_perspective_analysis",
    sub_agents=[technical_analyst, business_analyst, legal_analyst, risk_analyst],
)

# Aggregator to synthesize results
aggregator = LlmAgent(
    name="decision_synthesizer",
    model="gemini-2.5-flash",
    instruction="""
    Synthesize all perspectives into a comprehensive recommendation:

    1. Summary of each perspective
    2. Areas of agreement and concern
    3. Overall recommendation (GO / NO-GO / NEEDS REVISION)
    4. Key conditions for success
    5. Priority actions

    Format as executive summary with clear recommendation.
    """
)

# Complete workflow
decision_pipeline = SequentialAgent(
    name="decision_analysis_workflow",
    sub_agents=[analysis_team, aggregator],
)

# Execute
decision = """
Should we implement facial recognition for employee attendance tracking?
"""

result = decision_pipeline.run(decision)
```

---

## Example 2: Concurrent Data Gathering

### Scenario
Gather information from multiple sources simultaneously for comprehensive research.

### Architecture
```
               ┌→ Web Researcher      ┐
               ├→ Academic Researcher  ├→ Knowledge Synthesizer → Final Report
Query →     ├→ Database Analyst     │
               └→ Expert Interviewer   ┘
```

### Implementation

```python
from google.adk.agents import ParallelAgent, LlmAgent
from google.adk.tools import FunctionTool

# Tool definitions
def search_web(query):
    """Simulated web search"""
    return {"results": [...]}

def search_academic(query):
    """Simulated academic database search"""
    return {"papers": [...]}

def query_database(sql):
    """Simulated database query"""
    return {"data": [...]}

# Parallel researchers
web_researcher = LlmAgent(
    name="web_researcher",
    tools=[FunctionTool(func=search_web)],
    instruction="""
    Search the web for recent information:
    1. News articles and blog posts
    2. Industry reports
    3. Expert opinions
    4. Recent developments

    Use search_web tool and summarize findings.
    """
)

academic_researcher = LlmAgent(
    name="academic_researcher",
    tools=[FunctionTool(func=search_academic)],
    instruction="""
    Search academic sources:
    1. Peer-reviewed papers
    2. Research studies
    3. Meta-analyses
    4. Citation analysis

    Use search_academic tool and extract key findings.
    """
)

database_analyst = LlmAgent(
    name="database_analyst",
    tools=[FunctionTool(func=query_database)],
    instruction="""
    Query internal databases:
    1. Historical data
    2. Customer metrics
    3. Sales trends
    4. Operational data

    Use query_database tool and identify patterns.
    """
)

expert_interviewer = LlmAgent(
    name="expert_interviewer",
    instruction="""
    Synthesize expert opinions:
    1. Industry thought leaders
    2. Domain experts
    3. Practitioner insights
    4. Case studies

    Provide expert consensus and dissenting views.
    """
)

# Parallel gathering
data_gatherers = ParallelAgent(
    name="concurrent_research",
    sub_agents=[web_researcher, academic_researcher, database_analyst, expert_interviewer],
)

# Synthesizer
synthesizer = LlmAgent(
    name="knowledge_synthesizer",
    instruction="""
    Synthesize all research into comprehensive report:

    **Structure:**
    1. Executive Summary
    2. Key Findings (from all sources)
    3. Data Analysis
    4. Expert Insights
    5. Conclusions and Recommendations

    **Highlight:**
    - Consensus across sources
    - Contradictions or debates
    - Data-backed insights
    - Gaps in knowledge

    Format as structured markdown report.
    """
)

# Complete workflow
research_workflow = SequentialAgent(
    name="comprehensive_research",
    sub_agents=[data_gatherers, synthesizer],
)

# Execute
result = research_workflow.run("Impact of AI on software development productivity")
```

---

## Example 3: Parallel Code Generation

### Scenario
Generate multiple implementation approaches simultaneously, then select the best.

### Architecture
```
                    ┌→ Optimized for Performance ┐
                    ├→ Optimized for Readability  ├→ Evaluator → Best Implementation
Requirements →   ├→ Optimized for Simplicity   │
                    └→ Optimized for Security     ┘
```

### Implementation

```python
from google.adk.agents import ParallelAgent, LlmAgent

# Parallel code generators (different optimization goals)
performance_optimizer = LlmAgent(
    name="performance_optimizer",
    model="gemini-2.5-flash",
    instruction="""
    Generate code optimized for performance:
    1. Minimize time complexity
    2. Efficient memory usage
    3. Leverage caching
    4. Use optimal data structures
    5. Parallel processing where possible

    Explain performance characteristics.
    """
)

readability_optimizer = LlmAgent(
    name="readability_optimizer",
    model="gemini-2.5-flash",
    instruction="""
    Generate code optimized for readability:
    1. Clear variable names
    2. Well-documented
    3. Intuitive structure
    4. Minimal complexity
    5. Self-explanatory logic

    Prioritize maintainability over micro-optimizations.
    """
)

simplicity_optimizer = LlmAgent(
    name="simplicity_optimizer",
    model="gemini-2.5-flash",
    instruction="""
    Generate the simplest possible implementation:
    1. Minimal lines of code
    2. Fewest dependencies
    3. Straightforward logic
    4. No premature optimization
    5. YAGNI principle

    Elegance through simplicity.
    """
)

security_optimizer = LlmAgent(
    name="security_optimizer",
    model="gemini-2.5-flash",
    instruction="""
    Generate code optimized for security:
    1. Input validation and sanitization
    2. Parameterized queries
    3. Proper authentication/authorization
    4. Secure data handling
    5. Defense against common vulnerabilities

    Document security considerations.
    """
)

# Parallel generation
code_generators = ParallelAgent(
    name="parallel_implementations",
    sub_agents=[
        performance_optimizer,
        readability_optimizer,
        simplicity_optimizer,
        security_optimizer
    ],
)

# Evaluator
evaluator = LlmAgent(
    name="implementation_evaluator",
    model="gemini-2.5-flash",
    instruction="""
    Evaluate all implementations:

    **Score each on (1-10):**
    - Performance
    - Readability
    - Simplicity
    - Security
    - Maintainability

    **Provide:**
    1. Comparison table
    2. Strengths of each approach
    3. Trade-offs
    4. Recommendation based on context

    **Select best implementation** considering:
    - Project requirements
    - Team expertise
    - Long-term maintenance
    """
)

# Complete workflow
code_generation_workflow = SequentialAgent(
    name="multi_approach_generation",
    sub_agents=[code_generators, evaluator],
)

# Execute
requirements = """
Implement a user authentication system that:
- Validates email and password
- Stores credentials securely
- Handles session management
- Prevents brute force attacks
"""

result = code_generation_workflow.run(requirements)
```

---

## Example 4: Parallel Validation

### Scenario
Validate a system design against multiple quality attributes concurrently.

### Architecture
```
                  ┌→ Performance Validator ┐
                  ├→ Security Validator    ├→ Aggregator → Validation Report
Design →       ├→ Scalability Validator  │
                  └→ Usability Validator   ┘
```

### Implementation

```python
from google.adk.agents import ParallelAgent, LlmAgent

# Parallel validators
performance_validator = LlmAgent(
    name="performance_validator",
    instruction="""
    Validate performance aspects:

    **Check:**
    1. Response time requirements
    2. Throughput capacity
    3. Resource utilization
    4. Caching strategy
    5. Database query efficiency

    **Output:**
    - PASS/FAIL for each criterion
    - Performance bottlenecks
    - Optimization recommendations
    """
)

security_validator = LlmAgent(
    name="security_validator",
    instruction="""
    Validate security design:

    **Check:**
    1. Authentication mechanism
    2. Authorization model
    3. Data encryption (at rest and in transit)
    4. API security
    5. Vulnerability mitigation

    **Output:**
    - PASS/FAIL for each criterion
    - Security gaps
    - Remediation steps
    """
)

scalability_validator = LlmAgent(
    name="scalability_validator",
    instruction="""
    Validate scalability:

    **Check:**
    1. Horizontal scaling capability
    2. Database sharding strategy
    3. Load balancing approach
    4. Stateless design
    5. Auto-scaling configuration

    **Output:**
    - PASS/FAIL for each criterion
    - Scalability limits
    - Scaling recommendations
    """
)

usability_validator = LlmAgent(
    name="usability_validator",
    instruction="""
    Validate usability:

    **Check:**
    1. User interface clarity
    2. Error handling and messaging
    3. Accessibility compliance
    4. Mobile responsiveness
    5. User flow efficiency

    **Output:**
    - PASS/FAIL for each criterion
    - UX issues
    - Improvement suggestions
    """
)

# Parallel validation
validators = ParallelAgent(
    name="parallel_validation",
    sub_agents=[
        performance_validator,
        security_validator,
        scalability_validator,
        usability_validator
    ],
)

# Aggregator
validation_aggregator = LlmAgent(
    name="validation_aggregator",
    instruction="""
    Aggregate validation results:

    **Produce:**
    1. Overall validation status (APPROVED / NEEDS REVISION / REJECTED)
    2. Summary of each validator's findings
    3. Critical issues (must fix)
    4. Recommended improvements (nice to have)
    5. Priority action items

    Format as validation report with clear sections.
    """
)

# Complete workflow
validation_workflow = SequentialAgent(
    name="design_validation",
    sub_agents=[validators, validation_aggregator],
)

# Execute
design_doc = """
E-commerce platform design:
- Microservices architecture
- PostgreSQL for transactions
- Redis for caching
- JWT authentication
- REST APIs
- React frontend
"""

result = validation_workflow.run(design_doc)
```

---

## Best Practices for Parallel Workers

### 1. Ensure Independence
Parallel agents should not depend on each other's results.

**Good:** Each analyst analyzes the same input independently

**Bad:** Analyst B needs Analyst A's output to proceed

### 2. Consistent Output Format
All parallel agents should produce similarly structured outputs.

```python
# Standard output format
{
    "analyst": "technical",
    "score": 8,
    "findings": [...],
    "recommendations": [...]
}
```

### 3. Limit Concurrency
Don't run too many agents in parallel (3-5 is ideal for LLM-based agents).

**Why:** Rate limits, memory constraints, and diminishing returns

### 4. Aggregate Intelligently
Design aggregator to synthesize results, not just concatenate.

```python
aggregator = LlmAgent(
    instruction="""
    Synthesize results by:
    1. Identifying common themes across perspectives
    2. Highlighting contradictions
    3. Weighing different viewpoints
    4. Drawing conclusions from the collective analysis
    """
)
```

### 5. Timeout Handling
Parallel execution may complete at different times.

```python
# Set appropriate timeouts
# Handle cases where one agent takes longer than others
```

---

## Performance Considerations

### Sequential vs Parallel Timing

**Sequential Execution:**
```
Agent A: 5s
Agent B: 5s
Agent C: 5s
Total: 15s
```

**Parallel Execution:**
```
Agent A: 5s ┐
Agent B: 5s ├→ All complete at 5s
Agent C: 5s ┘
Total: ~5s
```

**When to Use Parallel:**
- Tasks are independent
- Tasks are I/O bound
- Need to save time
- Want multiple perspectives

**When to Use Sequential:**
- Tasks have dependencies
- Need ordered processing
- Tasks build on each other
- Resource constraints

---

## Common Patterns

### Pattern 1: Analyze-Then-Synthesize
Parallel analysis followed by synthesis.

```python
workflow = SequentialAgent(
    sub_agents=[
        ParallelAgent(sub_agents=[analyst_a, analyst_b, analyst_c]),
        synthesizer
    ]
)
```

### Pattern 2: Generate-Then-Select
Parallel generation followed by selection.

```python
workflow = SequentialAgent(
    sub_agents=[
        ParallelAgent(sub_agents=[generator_a, generator_b, generator_c]),
        selector
    ]
)
```

### Pattern 3: Validate-Then-Aggregate
Parallel validation followed by aggregation.

```python
workflow = SequentialAgent(
    sub_agents=[
        ParallelAgent(sub_agents=[validator_a, validator_b, validator_c]),
        aggregator
    ]
)
```

---

## Testing Parallel Agents

### Test Individual Agents First

```python
# Test each agent independently
result_a = technical_analyst.run(test_input)
result_b = business_analyst.run(test_input)

# Then test parallel execution
parallel_result = analysis_team.run(test_input)
```

### Verify All Agents Execute

```python
# Ensure all agents contribute to result
assert "technical_analyst" in result
assert "business_analyst" in result
assert "legal_analyst" in result
```

### Test Aggregation Logic

```python
# Test that aggregator handles all inputs
aggregator_result = aggregator.run(parallel_result)
assert "recommendation" in aggregator_result
```
