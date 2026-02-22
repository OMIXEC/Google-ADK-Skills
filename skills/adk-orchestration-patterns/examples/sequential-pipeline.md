# Sequential Pipeline Examples

## Example 1: Content Creation Pipeline

### Scenario
Create high-quality blog posts from topic ideas through research, writing, and editing.

### Architecture
```
Topic → Researcher → Writer → Editor → SEO Optimizer → Final Article
```

### Implementation

```python
from google.adk.agents import SequentialAgent, LlmAgent

# Stage 1: Research
researcher = LlmAgent(
    name="researcher",
    model="gemini-2.5-flash",
    instruction="""
    Research the given topic thoroughly:
    1. Key concepts and definitions
    2. Recent trends and developments
    3. Expert opinions and insights
    4. Relevant statistics and data

    Output as structured JSON:
    {
        "topic": "...",
        "key_points": [...],
        "sources": [...],
        "statistics": [...],
        "trends": [...]
    }
    """
)

# Stage 2: Writing
writer = LlmAgent(
    name="writer",
    model="gemini-2.5-flash",
    instruction="""
    Write a comprehensive blog post using the research:
    1. Engaging introduction with hook
    2. Well-structured body with headings
    3. Include statistics and expert quotes
    4. Actionable conclusion

    Tone: Professional yet accessible
    Length: 1200-1500 words
    """
)

# Stage 3: Editing
editor = LlmAgent(
    name="editor",
    model="gemini-2.5-flash",
    instruction="""
    Edit the article for:
    1. Grammar and spelling
    2. Clarity and flow
    3. Consistency in tone
    4. Removal of redundancy

    Maintain the author's voice while improving quality.
    """
)

# Stage 4: SEO Optimization
seo_optimizer = LlmAgent(
    name="seo_optimizer",
    model="gemini-2.5-flash",
    instruction="""
    Optimize the article for SEO:
    1. Suggest meta title and description
    2. Recommend keyword placement
    3. Add internal linking suggestions
    4. Suggest alt text for images
    5. Create a URL slug

    Output the optimized article with SEO metadata.
    """
)

# Complete pipeline
content_pipeline = SequentialAgent(
    name="content_creation_pipeline",
    sub_agents=[researcher, writer, editor, seo_optimizer],
)

# Execute
result = content_pipeline.run("The future of quantum computing in healthcare")
```

---

## Example 2: Data Processing Pipeline

### Scenario
Process raw customer data through validation, enrichment, transformation, and storage.

### Architecture
```
Raw Data → Validator → Enricher → Transformer → Storage Formatter → Output
```

### Implementation

```python
from google.adk.agents import SequentialAgent, LlmAgent
from google.adk.tools import FunctionTool

# Stage 1: Validation
def validate_data(data):
    """Programmatic validation logic"""
    # Check required fields, data types, etc.
    return {"valid": True, "errors": []}

validator = LlmAgent(
    name="validator",
    tools=[FunctionTool(func=validate_data)],
    instruction="""
    Validate the input data:
    1. Check for required fields
    2. Verify data types and formats
    3. Detect anomalies or outliers
    4. Flag suspicious entries

    Use the validate_data tool for programmatic checks.
    Output: VALID or list of validation errors
    """
)

# Stage 2: Enrichment
enricher = LlmAgent(
    name="enricher",
    instruction="""
    Enrich customer data:
    1. Standardize addresses
    2. Add geographic coordinates
    3. Append demographic data
    4. Calculate customer segment

    Output enriched data in same format as input.
    """
)

# Stage 3: Transformation
transformer = LlmAgent(
    name="transformer",
    instruction="""
    Transform data to target schema:
    1. Map fields to target structure
    2. Convert data types as needed
    3. Calculate derived fields
    4. Apply business rules

    Output data in target schema format.
    """
)

# Stage 4: Storage Formatting
storage_formatter = LlmAgent(
    name="storage_formatter",
    instruction="""
    Format data for database storage:
    1. Generate unique IDs
    2. Add timestamps
    3. Create foreign key references
    4. Format for SQL insertion

    Output SQL INSERT statements or JSON for NoSQL.
    """
)

# Pipeline
data_pipeline = SequentialAgent(
    name="data_processing_pipeline",
    sub_agents=[validator, enricher, transformer, storage_formatter],
)

# Execute
raw_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "purchase_amount": 149.99
}

result = data_pipeline.run(str(raw_data))
```

---

## Example 3: Code Review Pipeline

### Scenario
Automated code review with security, performance, style, and testing checks.

### Architecture
```
Code → Security Scanner → Performance Analyzer → Style Checker → Test Validator → Review Report
```

### Implementation

```python
from google.adk.agents import SequentialAgent, LlmAgent

# Stage 1: Security Analysis
security_scanner = LlmAgent(
    name="security_scanner",
    model="gemini-2.5-flash",
    instruction="""
    Scan code for security vulnerabilities:
    1. SQL injection risks
    2. XSS vulnerabilities
    3. Insecure authentication
    4. Hardcoded secrets
    5. Unsafe deserialization

    Output JSON with severity levels:
    {"critical": [...], "high": [...], "medium": [...], "low": [...]}
    """
)

# Stage 2: Performance Analysis
performance_analyzer = LlmAgent(
    name="performance_analyzer",
    model="gemini-2.5-flash",
    instruction="""
    Analyze code performance:
    1. Time complexity issues
    2. Memory leaks
    3. Inefficient queries
    4. Unnecessary loops
    5. Missing caching

    Output performance issues with suggestions for improvement.
    """
)

# Stage 3: Style Checking
style_checker = LlmAgent(
    name="style_checker",
    model="gemini-2.5-flash",
    instruction="""
    Check code style and best practices:
    1. Naming conventions
    2. Code organization
    3. Documentation quality
    4. DRY violations
    5. Error handling

    Output style violations with line numbers.
    """
)

# Stage 4: Test Validation
test_validator = LlmAgent(
    name="test_validator",
    model="gemini-2.5-flash",
    instruction="""
    Validate test coverage:
    1. Missing test cases
    2. Edge cases not covered
    3. Mock quality
    4. Test organization

    Output testing recommendations.
    """
)

# Stage 5: Report Generator
report_generator = LlmAgent(
    name="report_generator",
    model="gemini-2.5-flash",
    instruction="""
    Generate comprehensive code review report:
    1. Executive summary
    2. Security findings
    3. Performance issues
    4. Style violations
    5. Testing gaps
    6. Overall recommendation (approve/request changes/reject)

    Format as markdown with clear sections.
    """
)

# Pipeline
code_review_pipeline = SequentialAgent(
    name="code_review_pipeline",
    sub_agents=[
        security_scanner,
        performance_analyzer,
        style_checker,
        test_validator,
        report_generator
    ],
)

# Execute
code_to_review = """
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return result
"""

result = code_review_pipeline.run(code_to_review)
```

---

## Example 4: Customer Onboarding Pipeline

### Scenario
Multi-step customer onboarding with data collection, verification, setup, and welcome.

### Architecture
```
New User → Profile Builder → ID Verifier → Account Setup → Welcome Guide → Complete
```

### Implementation

```python
from google.adk.agents import SequentialAgent, LlmAgent

# Stage 1: Profile Building
profile_builder = LlmAgent(
    name="profile_builder",
    instruction="""
    Collect and structure customer information:
    1. Basic demographics
    2. Business details
    3. Use case and goals
    4. Team size and structure

    Ask clarifying questions if information is incomplete.
    Output structured customer profile.
    """
)

# Stage 2: Identity Verification
id_verifier = LlmAgent(
    name="id_verifier",
    instruction="""
    Guide identity verification process:
    1. Explain verification requirements
    2. List acceptable documents
    3. Provide upload instructions
    4. Validate submitted documents

    Output: VERIFIED or list of issues to resolve.
    """
)

# Stage 3: Account Setup
account_setup = LlmAgent(
    name="account_setup",
    instruction="""
    Set up customer account:
    1. Create user credentials
    2. Configure preferences
    3. Set up billing
    4. Assign subscription tier
    5. Create team workspace

    Output account details and access credentials.
    """
)

# Stage 4: Welcome Guide
welcome_guide = LlmAgent(
    name="welcome_guide",
    instruction="""
    Create personalized welcome guide:
    1. Getting started checklist
    2. Key features for their use case
    3. Tutorial recommendations
    4. Support resources
    5. Next steps

    Tailor recommendations to customer profile and goals.
    """
)

# Pipeline
onboarding_pipeline = SequentialAgent(
    name="customer_onboarding",
    sub_agents=[profile_builder, id_verifier, account_setup, welcome_guide],
)

# Execute
result = onboarding_pipeline.run("New customer signup: Acme Corp")
```

---

## Best Practices for Sequential Pipelines

### 1. Clear Stage Boundaries
Each agent should have a single, well-defined responsibility.

**Good:**
- Stage 1: Data collection
- Stage 2: Data validation
- Stage 3: Data transformation

**Bad:**
- Stage 1: Collect and validate data, plus some transformation

### 2. Consistent Output Formats
Each stage should output in a format the next stage expects.

```python
# Each stage outputs JSON with consistent structure
{
    "stage": "researcher",
    "status": "complete",
    "data": {...},
    "metadata": {...}
}
```

### 3. Error Handling
Each stage should handle errors gracefully.

```python
validator = LlmAgent(
    name="validator",
    instruction="""
    If validation fails:
    1. Output detailed error messages
    2. Suggest corrections
    3. Mark as INVALID to stop pipeline

    If validation passes:
    1. Output VALID
    2. Include validated data
    """
)
```

### 4. Progress Tracking
Log progress through the pipeline.

```python
class PipelineTracker:
    def __init__(self):
        self.completed_stages = []

    def track(self, stage_name):
        self.completed_stages.append({
            "stage": stage_name,
            "timestamp": datetime.now()
        })

tracker = PipelineTracker()
# After each stage: tracker.track("researcher")
```

### 5. Testing Each Stage
Test stages independently before testing the full pipeline.

```python
# Test individual stages
research_result = researcher.run("test topic")
assert "key_points" in research_result

write_result = writer.run(research_result)
assert len(write_result) > 1000

# Then test full pipeline
pipeline_result = pipeline.run("test topic")
```

---

## Common Pitfalls

### 1. Too Many Stages
Limit pipelines to 3-7 stages for maintainability.

**Problem:** 12-stage pipeline is hard to debug

**Solution:** Group related stages into sub-pipelines

### 2. Tight Coupling
Stages too dependent on each other's specific output formats.

**Problem:** Changing one stage breaks downstream stages

**Solution:** Use standard intermediate formats (JSON schema)

### 3. No Rollback
Pipeline stops midway with no way to recover.

**Problem:** Stage 4 fails, stages 1-3 are lost

**Solution:** Checkpoint state after each stage

### 4. Slow Sequential Processing
Sequential execution when parallelization is possible.

**Problem:** Waiting for each stage when some could run in parallel

**Solution:** Use ParallelAgent for independent stages
