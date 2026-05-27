# Output Validation & Quality Gates for ADK Workflows

Agent output is unreliable by nature. Validate before it propagates to the next agent or reaches the user. This reference covers validation at every stage.

## Validation Layers

```
┌──────────────────────────────────────────────┐
│ Layer 1: output_schema (Pydantic)            │
│   - Structural validation: types, required   │
│   - Enforced by LlmAgent automatically       │
├──────────────────────────────────────────────┤
│ Layer 2: Guard middleware (after_agent)      │
│   - Content safety, PII, format checks       │
│   - Runs after model response, before next   │
├──────────────────────────────────────────────┤
│ Layer 3: Quality gates (scoring function)    │
│   - Completeness, correctness, confidence    │
│   - Decides: pass to next or retry           │
├──────────────────────────────────────────────┤
│ Layer 4: Cross-agent contract (schema match) │
│   - Agent A output = Agent B input           │
│   - Validated at workflow composition time   │
└──────────────────────────────────────────────┘
```

## Layer 1: `output_schema` (Pydantic)

```python
from pydantic import BaseModel, Field, field_validator
from google.adk.agents import LlmAgent

class AnalysisOutput(BaseModel):
    summary: str = Field(description="One-paragraph summary", min_length=50, max_length=500)
    key_points: list[str] = Field(description="3-5 key takeaways", min_items=3, max_items=5)
    sentiment: str = Field(description="positive, negative, or neutral")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")

    @field_validator("sentiment")
    @classmethod
    def sentiment_must_be_valid(cls, v):
        allowed = {"positive", "negative", "neutral"}
        if v.lower() not in allowed:
            raise ValueError(f"Sentiment must be one of {allowed}")
        return v.lower()

analysis_agent = LlmAgent(
    name="analyzer",
    model="gemini-2.5-flash",
    instruction="Analyze the input text and return structured output.",
    output_schema=AnalysisOutput,  # ADK enforces this schema
    output_key="analysis",
)
```

### When `output_schema` is set, the agent CANNOT use tools

This is a critical constraint: `output_schema` forces the model into structured output mode, which disables tool calling. For agents that need both tools AND structured output, use Layer 2 (guard middleware) instead.

```python
# WRONG — agent won't call tools when output_schema is set
agent = LlmAgent(
    tools=[search_tool],
    output_schema=SearchResult,  # ← tools disabled!
)

# RIGHT — use after_agent_callback for validation when tools are needed
agent = LlmAgent(
    tools=[search_tool],
    after_agent_callback=validate_search_output,
)
```

## Layer 2: Guard Middleware

```python
"""Validate output structure, content safety, and format after agent runs."""

import re
from pydantic import BaseModel, ValidationError

class OutputGuard:
    def __init__(self):
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        }

    async def validate(self, output_text: str, schema: type[BaseModel] | None = None) -> dict:
        """Run all guard checks on agent output."""
        results = {
            "passed": True,
            "checks": {},
        }

        # PII check
        pii_found = self._check_pii(output_text)
        results["checks"]["pii"] = {"passed": not pii_found, "found": pii_found}

        # Content safety (basic — use LLM-based check for production)
        safety_issues = self._check_safety(output_text)
        results["checks"]["safety"] = {"passed": not safety_issues, "issues": safety_issues}

        # Schema validation (if provided)
        if schema:
            try:
                parsed = schema.model_validate_json(output_text)
                results["checks"]["schema"] = {"passed": True, "parsed": parsed.model_dump()}
            except (ValidationError, ValueError) as e:
                results["checks"]["schema"] = {"passed": False, "error": str(e)}
                results["passed"] = False

        # Empty output check
        results["checks"]["non_empty"] = {"passed": bool(output_text and output_text.strip())}
        if not output_text or not output_text.strip():
            results["passed"] = False

        return results

    def _check_pii(self, text: str) -> list[str]:
        found = []
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found.append(pii_type)
        return found

    def _check_safety(self, text: str) -> list[str]:
        issues = []
        banned_terms = ["execute arbitrary code", "dump all passwords", "bypass authentication"]
        for term in banned_terms:
            if term.lower() in text.lower():
                issues.append(f"Banned content pattern: '{term}'")
        return issues

# Wire as after_agent_callback
async def guard_output(callback_context):
    guard = OutputGuard()
    last_event = callback_context.session.events[-1] if callback_context.session.events else None
    if last_event and last_event.content:
        text = last_event.content.parts[0].text if last_event.content.parts else ""
        result = await guard.validate(text)
        if not result["passed"]:
            # Block output propagation
            callback_context.state["output_blocked"] = True
            callback_context.state["block_reason"] = result["checks"]
```

## Layer 3: Quality Gates

```python
"""Score agent output quality. Gate: pass to next agent or retry."""

class QualityGate:
    def __init__(self, min_score: float = 0.7):
        self.min_score = min_score

    async def evaluate(self, output: str, criteria: list[str]) -> dict:
        """
        Evaluate output against quality criteria.
        Returns score and pass/fail decision.

        In production, use a dedicated evaluator LLM for this.
        For templates, use heuristic checks.
        """
        scores = {}
        for criterion in criteria:
            scores[criterion] = await self._score_criterion(output, criterion)

        total = sum(scores.values()) / len(scores) if scores else 0.0
        return {
            "score": round(total, 2),
            "passed": total >= self.min_score,
            "criteria_scores": scores,
        }

    async def _score_criterion(self, output: str, criterion: str) -> float:
        """Heuristic scoring. Replace with LLM-based eval in production."""
        if criterion == "completeness":
            # Output has substance (not too short)
            return min(1.0, len(output.split()) / 50.0)
        elif criterion == "relevance":
            # Output contains expected keywords (pass via quality gate config)
            return 0.8  # Placeholder — use LLM eval
        elif criterion == "format":
            # Output is well-structured
            has_paragraphs = "\n\n" in output
            has_list = "- " in output or "1. " in output
            return 0.9 if has_paragraphs or has_list else 0.5
        return 0.5

# Usage in LoopAgent
quality_ok = False
max_iterations = 3
for i in range(max_iterations):
    output = await run_agent(generator)
    gate = QualityGate(min_score=0.7)
    result = await gate.evaluate(output, ["completeness", "relevance", "format"])
    if result["passed"]:
        quality_ok = True
        break
    # Feedback into next iteration
    feedback = f"Quality score {result['score']}. Improve: {result['criteria_scores']}"
```

### LLM-based quality evaluator

```python
"""Use a dedicated LLM call to evaluate output quality."""

class LLMQualityEvaluator:
    def __init__(self, model="gemini-2.5-flash"):
        self.model = model

    async def evaluate(self, output: str, expected_behavior: str) -> dict:
        """Ask an LLM to score the output."""
        prompt = f"""Evaluate this agent output against the expected behavior.

Expected behavior: {expected_behavior}

Agent output:
---
{output}
---

Score each dimension from 0.0 to 1.0:
1. completeness: Does it fully address the request?
2. correctness: Is the information accurate?
3. clarity: Is it well-written and easy to understand?
4. safety: Does it avoid harmful or inappropriate content?

Return JSON: {{"completeness": 0.X, "correctness": 0.X, "clarity": 0.X, "safety": 0.X, "overall_pass": true/false}}
Overall pass = all scores >= 0.7."""

        # Call LLM with JSON output
        response = await call_llm(prompt, response_format="json")
        return json.loads(response)
```

## Layer 4: Cross-Agent Contract Validation

```python
"""Validate that Agent A's output matches Agent B's input expectations."""

from pydantic import BaseModel

class AgentContract:
    """Defines the data contract between two agents in a workflow."""
    def __init__(self, from_agent: str, to_agent: str, output_schema: type[BaseModel], input_schema: type[BaseModel]):
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.output_schema = output_schema
        self.input_schema = input_schema

    def validate(self, output_data: dict) -> bool:
        """Check that output_data conforms to the expected input schema."""
        try:
            self.input_schema.model_validate(output_data)
            return True
        except Exception:
            return False

    def missing_fields(self, output_data: dict) -> list[str]:
        """Return fields present in input_schema but missing from output."""
        output_keys = set(output_data.keys())
        input_keys = set(self.input_schema.model_fields.keys())
        return list(input_keys - output_keys)

# Example: Writer → Reviewer contract
class WriterOutput(BaseModel):
    draft: str
    word_count: int
    topic: str

class ReviewerInput(BaseModel):
    draft: str
    topic: str
    review_guidelines: str | None = None  # Optional, Reviewer can use defaults

contract = AgentContract(
    from_agent="writer",
    to_agent="reviewer",
    output_schema=WriterOutput,
    input_schema=ReviewerInput,
)

# After writer runs, validate before calling reviewer
writer_output = state["writer_output"]
if not contract.validate(writer_output):
    missing = contract.missing_fields(writer_output)
    raise ContractViolationError(
        f"Writer→Reviewer contract broken. Missing: {missing}"
    )
```

## Hallucination Detection

```python
"""Basic hallucination detection patterns."""

class HallucinationDetector:
    def __init__(self):
        self.hallucination_markers = [
            "as an AI language model",  # Self-reference hallucination
        ]

    async def check_factual_grounding(
        self,
        output: str,
        source_documents: list[str],
        model="gemini-2.5-flash",
    ) -> dict:
        """Check if claims in output are supported by source documents."""
        prompt = f"""You are a factuality checker. For each claim in the agent output, verify if it is supported by the source documents.

Source documents:
{chr(10).join(f'- {doc}' for doc in source_documents)}

Agent output:
---
{output}
---

Return JSON:
{{
    "claims": [
        {{"claim": "...", "supported": true/false, "source_index": 0, "explanation": "..."}}
    ],
    "hallucination_rate": 0.X,
    "unsubstantiated_claims": ["..."]
}}"""

        response = await call_llm(prompt, response_format="json")
        result = json.loads(response)
        return result

    def detect_self_reference(self, output: str) -> bool:
        """Check for self-referential hallucination patterns."""
        for marker in self.hallucination_markers:
            if marker.lower() in output.lower():
                return True
        return False

    def detect_placeholder(self, output: str) -> bool:
        """Check for placeholder text that should be replaced."""
        placeholders = ["TODO", "FIXME", "[insert", "[your", "Lorem ipsum"]
        for ph in placeholders:
            if ph in output:
                return True
        return False
```

## Output Sanitization

```python
"""Sanitize agent output before it reaches the user or next agent."""

def sanitize_output(text: str) -> str:
    """Remove or redact sensitive content."""
    import re

    # Redact PII
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL_REDACTED]',
        text,
    )
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]', text)

    # Strip markdown code blocks if they contain sensitive commands
    text = re.sub(r'```(?:bash|sh|shell)\n.*?rm -rf.*?\n```', '[CODE_REDACTED]', text, flags=re.DOTALL)

    return text

# Wire into after_agent_callback
async def sanitize_agent_output(callback_context):
    last_event = callback_context.session.events[-1] if callback_context.session.events else None
    if last_event and last_event.content and last_event.content.parts:
        for part in last_event.content.parts:
            if part.text:
                part.text = sanitize_output(part.text)
```

## Production Checklist

- [ ] `output_schema` used for agents that don't need tools + structured output
- [ ] Guard middleware (`after_agent_callback`) used for agents with tools
- [ ] PII detection and redaction enabled on all user-facing outputs
- [ ] Quality gates on iterative workflows (LoopAgent)
- [ ] Cross-agent contracts validated at composition time
- [ ] Hallucination detection for RAG/grounded workflows
- [ ] Empty output detection (prevents silent failures)
- [ ] Output sanitization before user display
- [ ] Blocked outputs logged to DLQ for review
