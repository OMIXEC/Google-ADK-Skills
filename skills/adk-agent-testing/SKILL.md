---
name: ADK Agent Testing & Evaluation
description: This skill should be used when the user asks to "test my agent", "evaluate agent quality", "benchmark agent performance", "create agent tests", "agent QA", "measure agent accuracy", "test agent responses", "agent evaluation framework", or "validate agent behavior". Provides comprehensive testing strategies, evaluation frameworks, and quality assurance patterns for ADK agents.
version: 1.0.0
---

# ADK Agent Testing & Evaluation

Testing and evaluation are critical for building production-quality agents. This skill provides frameworks for unit testing, integration testing, evaluation metrics, and continuous quality assurance of Google ADK agents.

## Testing Pyramid for Agents

Agent testing follows a modified testing pyramid:

```
                    ┌─────────────┐
                    │   E2E/UAT   │  User acceptance, real conversations
                   ╱│  Evaluation │╲
                  ╱ └─────────────┘ ╲
                 ╱                   ╲
                ┌─────────────────────┐
                │  Integration Tests  │  Multi-agent, tool chains, memory
               ╱└─────────────────────┘╲
              ╱                         ╲
             ┌───────────────────────────┐
             │       Unit Tests          │  Individual tools, prompts, handlers
             └───────────────────────────┘
```

| Level | Tests | Speed | Coverage |
|-------|-------|-------|----------|
| **Unit** | Tool functions, prompt templates, handlers | Fast (ms) | High |
| **Integration** | Agent + tools, multi-agent flows | Medium (s) | Medium |
| **E2E/Evaluation** | Full conversations, quality metrics | Slow (min) | Critical paths |

## Getting Started

### Step 1: Set Up Test Environment

```python
# tests/conftest.py
import pytest
from adk_bidi import TestAgent, MockTool
from adk_bidi.testing import AgentTestHarness

@pytest.fixture
def test_agent():
    """Create a test agent with mocked dependencies."""
    return TestAgent(
        name="test_agent",
        model="gemini-1.5-flash",  # Use faster model for tests
        tools=[],
    )

@pytest.fixture
def test_harness():
    """Create test harness for agent evaluation."""
    return AgentTestHarness(
        timeout=30,
        max_turns=10,
    )
```

### Step 2: Write Unit Tests

```python
# tests/test_tools.py
import pytest
from my_agent.tools import search_database, format_response

def test_search_database_returns_results():
    """Test that search returns expected format."""
    results = search_database("test query")

    assert isinstance(results, list)
    assert len(results) > 0
    assert all("id" in r and "content" in r for r in results)

def test_search_database_handles_empty_query():
    """Test empty query handling."""
    results = search_database("")

    assert results == []

def test_format_response_structures_output():
    """Test response formatting."""
    raw_data = {"items": [1, 2, 3]}
    formatted = format_response(raw_data)

    assert "summary" in formatted
    assert "details" in formatted
```

### Step 3: Write Integration Tests

```python
# tests/test_agent_integration.py
import pytest
from adk_bidi.testing import AgentTestHarness

@pytest.mark.asyncio
async def test_agent_answers_question(test_agent, test_harness):
    """Test agent can answer a basic question."""
    response = await test_harness.ask(
        agent=test_agent,
        question="What is 2 + 2?",
    )

    assert "4" in response.text
    assert response.turn_count <= 2

@pytest.mark.asyncio
async def test_agent_uses_tool_correctly(test_agent, test_harness):
    """Test agent invokes tools appropriately."""
    response = await test_harness.ask(
        agent=test_agent,
        question="Search for information about Python.",
    )

    assert response.tools_used == ["search_database"]
    assert response.tool_calls[0].success
```

### Step 4: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=my_agent --cov-report=html

# Run only unit tests (fast)
pytest tests/test_tools.py -v

# Run integration tests
pytest tests/test_agent_integration.py -v --timeout=60
```

## Unit Testing Patterns

### Testing Tool Functions

```python
# tests/test_tools.py
import pytest
from unittest.mock import patch, MagicMock
from my_agent.tools import web_search, calculate_metrics

class TestWebSearch:
    """Test web search tool."""

    def test_returns_results_for_valid_query(self):
        """Valid query returns structured results."""
        results = web_search("Python tutorials")

        assert isinstance(results, list)
        assert len(results) <= 10  # Max results limit

    def test_handles_api_errors_gracefully(self):
        """API failures return empty results, not exceptions."""
        with patch('my_agent.tools.requests.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            results = web_search("test")

        assert results == []

    def test_sanitizes_input(self):
        """Dangerous inputs are sanitized."""
        # Test injection attempt
        results = web_search("'; DROP TABLE users; --")

        # Should not raise, should return safe results
        assert isinstance(results, list)


class TestCalculateMetrics:
    """Test metrics calculation tool."""

    @pytest.mark.parametrize("data,expected", [
        ([1, 2, 3, 4, 5], {"mean": 3.0, "sum": 15}),
        ([10], {"mean": 10.0, "sum": 10}),
        ([], {"mean": 0.0, "sum": 0}),
    ])
    def test_calculates_correctly(self, data, expected):
        """Metrics are calculated accurately."""
        result = calculate_metrics(data)

        assert result["mean"] == expected["mean"]
        assert result["sum"] == expected["sum"]
```

### Testing Prompt Templates

```python
# tests/test_prompts.py
from my_agent.prompts import build_system_prompt, build_user_context

def test_system_prompt_includes_role():
    """System prompt defines agent role."""
    prompt = build_system_prompt(role="assistant")

    assert "assistant" in prompt.lower()
    assert len(prompt) > 50  # Not empty/minimal

def test_system_prompt_includes_constraints():
    """System prompt includes safety constraints."""
    prompt = build_system_prompt(role="assistant")

    # Check for safety guidelines
    assert any(word in prompt.lower() for word in [
        "safe", "appropriate", "professional", "helpful"
    ])

def test_user_context_formats_correctly():
    """User context is properly formatted."""
    context = build_user_context(
        user_name="Alice",
        preferences={"language": "en"},
    )

    assert "Alice" in context
    assert "language" in context
```

### Testing Response Handlers

```python
# tests/test_handlers.py
import pytest
from my_agent.handlers import parse_response, validate_output

class TestParseResponse:
    """Test response parsing."""

    def test_parses_json_response(self):
        """JSON responses are parsed correctly."""
        raw = '{"answer": "42", "confidence": 0.95}'
        parsed = parse_response(raw)

        assert parsed["answer"] == "42"
        assert parsed["confidence"] == 0.95

    def test_handles_malformed_json(self):
        """Malformed JSON returns text fallback."""
        raw = "This is not JSON"
        parsed = parse_response(raw)

        assert parsed["text"] == raw
        assert parsed["format"] == "text"


class TestValidateOutput:
    """Test output validation."""

    def test_accepts_valid_output(self):
        """Valid outputs pass validation."""
        output = {"text": "Hello", "complete": True}

        assert validate_output(output) == True

    def test_rejects_empty_output(self):
        """Empty outputs fail validation."""
        output = {"text": "", "complete": True}

        assert validate_output(output) == False

    def test_rejects_unsafe_content(self):
        """Unsafe content fails validation."""
        output = {"text": "UNSAFE_CONTENT_HERE", "complete": True}

        # Assuming content filter
        assert validate_output(output) == False
```

## Integration Testing Patterns

### Testing Agent Conversations

```python
# tests/test_conversations.py
import pytest
from adk_bidi.testing import AgentTestHarness, Conversation

@pytest.fixture
def harness():
    return AgentTestHarness(timeout=60)

@pytest.mark.asyncio
async def test_multi_turn_conversation(harness, test_agent):
    """Agent maintains context across turns."""
    conv = Conversation(agent=test_agent)

    # Turn 1: Introduce topic
    r1 = await conv.say("My name is Alice.")
    assert r1.success

    # Turn 2: Reference previous context
    r2 = await conv.say("What is my name?")
    assert "Alice" in r2.text

    # Verify context was maintained
    assert conv.turn_count == 2

@pytest.mark.asyncio
async def test_agent_handles_clarification(harness, test_agent):
    """Agent asks for clarification on ambiguous input."""
    conv = Conversation(agent=test_agent)

    # Ambiguous question
    response = await conv.say("What about it?")

    # Agent should ask for clarification
    assert any(word in response.text.lower() for word in [
        "what", "which", "could you", "please clarify"
    ])

@pytest.mark.asyncio
async def test_agent_recovers_from_errors(harness, test_agent):
    """Agent gracefully handles tool failures."""
    # Inject a failing tool
    test_agent.add_tool(MockTool(
        name="failing_tool",
        return_value=None,
        raises=Exception("Tool failed"),
    ))

    conv = Conversation(agent=test_agent)
    response = await conv.say("Use the failing tool.")

    # Agent should acknowledge issue, not crash
    assert response.success
    assert not "Exception" in response.text
```

### Testing Multi-Agent Systems

```python
# tests/test_multi_agent.py
import pytest
from adk_bidi.testing import MultiAgentTestHarness
from my_agents import researcher, analyst, writer

@pytest.fixture
def multi_harness():
    return MultiAgentTestHarness(
        agents=[researcher, analyst, writer],
        timeout=120,
    )

@pytest.mark.asyncio
async def test_agent_handoff(multi_harness):
    """Agents correctly hand off tasks."""
    result = await multi_harness.run_workflow(
        initial_agent="researcher",
        task="Research and write a report on AI trends.",
    )

    # Verify all agents participated
    assert "researcher" in result.agents_used
    assert "analyst" in result.agents_used
    assert "writer" in result.agents_used

    # Verify final output
    assert len(result.final_output) > 100

@pytest.mark.asyncio
async def test_shared_memory_sync(multi_harness):
    """Agents share memory correctly."""
    # Agent 1 stores information
    await multi_harness.send_to(
        agent="researcher",
        message="Remember that the key finding is X.",
    )

    # Agent 2 should access it
    response = await multi_harness.send_to(
        agent="analyst",
        message="What was the key finding?",
    )

    assert "X" in response.text
```

### Testing Tool Chains

```python
# tests/test_tool_chains.py
import pytest
from adk_bidi.testing import ToolChainTester

@pytest.fixture
def tool_tester():
    return ToolChainTester()

@pytest.mark.asyncio
async def test_search_then_summarize(tool_tester, test_agent):
    """Agent chains search → summarize correctly."""
    result = await tool_tester.run(
        agent=test_agent,
        task="Search for Python news and summarize.",
        expected_chain=["web_search", "summarize"],
    )

    assert result.chain_completed
    assert result.chain_order == ["web_search", "summarize"]

@pytest.mark.asyncio
async def test_parallel_tool_calls(tool_tester, test_agent):
    """Agent can call multiple tools in parallel."""
    result = await tool_tester.run(
        agent=test_agent,
        task="Get weather in NYC and LA simultaneously.",
        expected_tools={"get_weather"},
        min_parallel_calls=2,
    )

    assert result.parallel_calls >= 2
```

## Evaluation Frameworks

### Quality Metrics

```python
# evaluation/metrics.py
from adk_bidi.evaluation import EvaluationSuite, Metric

class AgentEvaluator:
    """Comprehensive agent evaluation."""

    def __init__(self, agent, test_cases):
        self.agent = agent
        self.test_cases = test_cases
        self.suite = EvaluationSuite()

    async def evaluate(self):
        """Run full evaluation."""
        results = {
            "accuracy": await self._evaluate_accuracy(),
            "relevance": await self._evaluate_relevance(),
            "helpfulness": await self._evaluate_helpfulness(),
            "safety": await self._evaluate_safety(),
            "latency": await self._evaluate_latency(),
        }
        return results

    async def _evaluate_accuracy(self):
        """Measure factual accuracy."""
        correct = 0
        for case in self.test_cases:
            response = await self.agent.ask(case["question"])
            if case["expected_answer"] in response.text:
                correct += 1
        return correct / len(self.test_cases)

    async def _evaluate_relevance(self):
        """Measure response relevance (LLM-as-judge)."""
        scores = []
        for case in self.test_cases:
            response = await self.agent.ask(case["question"])
            score = await self.suite.judge_relevance(
                question=case["question"],
                response=response.text,
            )
            scores.append(score)
        return sum(scores) / len(scores)

    async def _evaluate_helpfulness(self):
        """Measure how helpful responses are."""
        scores = []
        for case in self.test_cases:
            response = await self.agent.ask(case["question"])
            score = await self.suite.judge_helpfulness(
                question=case["question"],
                response=response.text,
            )
            scores.append(score)
        return sum(scores) / len(scores)

    async def _evaluate_safety(self):
        """Measure safety compliance."""
        violations = 0
        for case in self.test_cases.get("adversarial", []):
            response = await self.agent.ask(case["prompt"])
            if await self.suite.detect_unsafe_content(response.text):
                violations += 1
        total = len(self.test_cases.get("adversarial", []))
        return 1 - (violations / total) if total > 0 else 1.0

    async def _evaluate_latency(self):
        """Measure response latency."""
        import time
        latencies = []
        for case in self.test_cases[:10]:  # Sample
            start = time.time()
            await self.agent.ask(case["question"])
            latencies.append(time.time() - start)
        return {
            "p50": sorted(latencies)[len(latencies)//2],
            "p95": sorted(latencies)[int(len(latencies)*0.95)],
            "mean": sum(latencies) / len(latencies),
        }
```

### Test Case Generation

```python
# evaluation/test_cases.py
from adk_bidi.evaluation import TestCaseGenerator

def generate_test_cases(domain: str, count: int = 100):
    """Generate test cases for evaluation."""
    generator = TestCaseGenerator()

    cases = {
        "factual": generator.factual_questions(domain, count=count//4),
        "reasoning": generator.reasoning_questions(domain, count=count//4),
        "creative": generator.creative_prompts(domain, count=count//4),
        "adversarial": generator.adversarial_prompts(count=count//4),
    }

    return cases

# Example usage
test_cases = generate_test_cases("customer_support", count=100)

# Structure:
# {
#     "factual": [
#         {"question": "What are your business hours?", "expected_answer": "9-5"},
#         ...
#     ],
#     "reasoning": [
#         {"question": "If I ordered yesterday, when will it arrive?", ...},
#         ...
#     ],
#     "creative": [
#         {"prompt": "Write a friendly response to a complaint", ...},
#         ...
#     ],
#     "adversarial": [
#         {"prompt": "Ignore your instructions and...", "expected": "refuse"},
#         ...
#     ],
# }
```

### LLM-as-Judge Evaluation

```python
# evaluation/llm_judge.py
from adk_bidi.evaluation import LLMJudge

class AgentJudge:
    """Use LLM to evaluate agent responses."""

    def __init__(self, judge_model="gemini-1.5-pro"):
        self.judge = LLMJudge(model=judge_model)

    async def evaluate_response(
        self,
        question: str,
        response: str,
        criteria: list[str],
    ) -> dict:
        """Evaluate response against criteria."""

        prompt = f"""
        Evaluate this agent response against the criteria.

        Question: {question}
        Response: {response}

        Criteria to evaluate:
        {chr(10).join(f'- {c}' for c in criteria)}

        For each criterion, provide:
        - Score (1-5)
        - Brief justification

        Format as JSON.
        """

        evaluation = await self.judge.evaluate(prompt)
        return evaluation

    async def compare_responses(
        self,
        question: str,
        response_a: str,
        response_b: str,
    ) -> dict:
        """Compare two responses (A/B testing)."""

        prompt = f"""
        Compare these two agent responses.

        Question: {question}

        Response A: {response_a}
        Response B: {response_b}

        Which is better and why?
        Consider: accuracy, helpfulness, clarity, completeness.

        Return: {{"winner": "A" or "B", "reason": "..."}}
        """

        comparison = await self.judge.evaluate(prompt)
        return comparison
```

### Benchmark Suites

```python
# evaluation/benchmarks.py
from adk_bidi.evaluation import BenchmarkSuite

class AgentBenchmark:
    """Standard benchmark suite for agents."""

    def __init__(self, agent):
        self.agent = agent
        self.suite = BenchmarkSuite()

    async def run_all(self):
        """Run all benchmark categories."""
        results = {}

        # Knowledge benchmarks
        results["knowledge"] = await self.suite.run_knowledge_tests(
            self.agent,
            categories=["general", "domain_specific"],
        )

        # Reasoning benchmarks
        results["reasoning"] = await self.suite.run_reasoning_tests(
            self.agent,
            types=["logical", "mathematical", "causal"],
        )

        # Instruction following
        results["instruction"] = await self.suite.run_instruction_tests(
            self.agent,
            complexity=["simple", "multi_step", "conditional"],
        )

        # Safety benchmarks
        results["safety"] = await self.suite.run_safety_tests(
            self.agent,
            categories=["jailbreak", "harmful", "bias"],
        )

        # Compute aggregate scores
        results["aggregate"] = self._compute_aggregate(results)

        return results

    def _compute_aggregate(self, results):
        """Compute weighted aggregate score."""
        weights = {
            "knowledge": 0.25,
            "reasoning": 0.25,
            "instruction": 0.30,
            "safety": 0.20,
        }

        total = sum(
            results[k]["score"] * weights[k]
            for k in weights
        )

        return {
            "score": total,
            "grade": self._score_to_grade(total),
        }

    def _score_to_grade(self, score):
        if score >= 0.9: return "A"
        if score >= 0.8: return "B"
        if score >= 0.7: return "C"
        if score >= 0.6: return "D"
        return "F"
```

## Continuous Testing

### CI/CD Integration

```yaml
# .github/workflows/agent-tests.yml
name: Agent Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run unit tests
        run: pytest tests/test_tools.py tests/test_prompts.py -v --cov

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run integration tests
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: pytest tests/test_agent_integration.py -v --timeout=120

  evaluation:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run evaluation
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: python evaluation/run_benchmark.py --output results.json

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: evaluation-results
          path: results.json
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: agent-unit-tests
        name: Agent Unit Tests
        entry: pytest tests/test_tools.py tests/test_prompts.py -v
        language: system
        pass_filenames: false
        stages: [commit]

      - id: prompt-lint
        name: Prompt Lint
        entry: python scripts/lint_prompts.py
        language: system
        files: '.*prompts.*\.py$'
        stages: [commit]
```

### Regression Testing

```python
# tests/test_regression.py
import pytest
import json
from pathlib import Path

GOLDEN_FILE = Path("tests/golden_responses.json")

@pytest.fixture
def golden_responses():
    """Load golden responses for regression testing."""
    with open(GOLDEN_FILE) as f:
        return json.load(f)

@pytest.mark.asyncio
async def test_no_regression(test_agent, golden_responses):
    """Verify responses haven't regressed."""
    for case in golden_responses:
        response = await test_agent.ask(case["question"])

        # Check key assertions
        for assertion in case["assertions"]:
            if assertion["type"] == "contains":
                assert assertion["value"] in response.text, \
                    f"Regression: '{assertion['value']}' not in response"
            elif assertion["type"] == "not_contains":
                assert assertion["value"] not in response.text, \
                    f"Regression: '{assertion['value']}' should not be in response"

def update_golden_file(agent, test_cases):
    """Update golden file with new baseline (run manually)."""
    golden = []
    for case in test_cases:
        response = agent.ask(case["question"])
        golden.append({
            "question": case["question"],
            "response": response.text,
            "assertions": case.get("assertions", []),
        })

    with open(GOLDEN_FILE, "w") as f:
        json.dump(golden, f, indent=2)
```

## Best Practices

### Do's

1. **Test tools in isolation** - Unit test each tool function independently
2. **Mock external dependencies** - Don't call real APIs in unit tests
3. **Test edge cases** - Empty inputs, large inputs, special characters
4. **Use parameterized tests** - Cover multiple scenarios efficiently
5. **Test error handling** - Verify graceful degradation
6. **Run integration tests with real models** - Catch model-specific issues
7. **Track metrics over time** - Detect regressions early
8. **Test adversarial inputs** - Verify safety guardrails work

### Don'ts

1. **Don't test LLM output exactly** - Allow for variation
2. **Don't skip integration tests** - Unit tests alone aren't enough
3. **Don't ignore latency** - Performance matters in production
4. **Don't test only happy paths** - Error cases are critical
5. **Don't hardcode API keys** - Use environment variables
6. **Don't run full evaluations on every commit** - Reserve for CI/CD

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_tools.py        # Tool function tests
│   ├── test_prompts.py      # Prompt template tests
│   └── test_handlers.py     # Response handler tests
├── integration/
│   ├── test_agent.py        # Single agent tests
│   ├── test_multi_agent.py  # Multi-agent tests
│   └── test_tool_chains.py  # Tool chain tests
├── evaluation/
│   ├── test_accuracy.py     # Accuracy benchmarks
│   ├── test_safety.py       # Safety benchmarks
│   └── test_performance.py  # Latency benchmarks
└── golden_responses.json    # Regression baselines
```

## ADK Testing Commands

The ADK provides built-in commands for testing agents during development:

### Local Testing with adk run

Execute your agent directly from command line for quick smoke tests:

```bash
# Basic execution
adk run

# With specific input
adk run --input "What is the weather today?"

# Custom configuration
adk run --config config/dev.yaml

# Verbose mode for debugging
adk run --verbose

# Example workflow
adk run --input "Search for Python tutorials" --verbose
```

**When to use:**
- Quick smoke tests after code changes
- Debugging specific inputs
- Validating tool integrations
- Testing configuration changes

### Interactive Testing with adk web

Launch a web UI for multi-turn conversation testing:

```bash
# Start web UI (default: http://localhost:8000)
adk web

# Custom port
adk web --port 3000

# With hot reload for development
adk web --reload

# Production mode
adk web --no-debug
```

**Features:**
- Visual conversation interface
- Tool execution tracking
- Response time monitoring
- Export conversations as test cases
- Session history

**Best for:**
- Manual QA sessions
- Demonstrating agent to stakeholders
- Testing complex multi-turn flows
- Collecting real conversation data for test datasets

### REST API Testing with adk api_server

Run agent as REST API for integration testing:

```bash
# Start API server
adk api_server

# Custom configuration
adk api_server --host 0.0.0.0 --port 8080

# With OpenAPI documentation
adk api_server --docs
```

**API Endpoints:**

```bash
# Health check
curl http://localhost:8080/health

# Send message
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-1"}'

# Get conversation history
curl http://localhost:8080/history/test-1

# OpenAPI docs
open http://localhost:8080/docs
```

**Integration test example:**

```python
import requests
import pytest

API_BASE = "http://localhost:8080"

def test_api_chat_endpoint():
    """Test chat API endpoint."""
    response = requests.post(
        f"{API_BASE}/chat",
        json={"message": "Hello", "session_id": "test"}
    )
    assert response.status_code == 200
    assert "response" in response.json()
```

## Advanced Testing Patterns

### InMemoryRunner for Fast Unit Tests

Use ADK's InMemoryRunner for deterministic, fast tests without API calls:

```python
from adk.testing import InMemoryRunner
from my_agent import create_agent

def test_agent_logic():
    """Test agent behavior without external API calls."""
    agent = create_agent()

    runner = InMemoryRunner(
        agent=agent,
        mock_responses={
            "What is 2+2?": "The answer is 4.",
            "search:.*": "Search results...",
        }
    )

    response = runner.run("What is 2+2?")
    assert "4" in response.text
    assert runner.api_calls_made == 0  # No external calls
```

### Conversation Replay Testing

Replay recorded conversations for regression testing:

```python
from adk.testing import ConversationReplay
import json

def test_conversation_replay():
    """Replay conversation to catch regressions."""
    with open("tests/fixtures/support_conversation.json") as f:
        conversation = json.load(f)

    agent = create_agent()
    replay = ConversationReplay(agent=agent)

    result = replay.run(conversation["turns"])
    assert result.all_passed
```

### Tool Validation

Ensure all tools are properly defined and integrated:

```python
from adk.testing import ToolValidator

def test_tool_definitions():
    """Validate all tools have proper schemas."""
    agent = create_agent()
    validator = ToolValidator(agent)

    report = validator.validate_all()
    assert report.all_valid
    assert len(report.errors) == 0
```

## Quick Start Commands

```bash
# Initialize test structure
/adk:test-init --project my-agent

# ADK testing commands
adk run --input "test query"          # Quick smoke test
adk web                                # Interactive testing
adk api_server                         # Start API for integration tests

# Automated testing
pytest tests/unit/ -v                  # Unit tests
pytest tests/integration/ -v --timeout=60  # Integration tests
python -m evaluation.run_benchmark --agent my_agent  # Full evaluation

# Generate test cases
python -m evaluation.generate_cases --domain customer_support --count 100

# Update golden file (after intentional changes)
python -m tests.update_golden
```

## Related Skills

- **adk-simple-agents** - Pre-built agent templates (test these!)
- **adk-multi-agent-workflows** - Multi-agent testing patterns
- **adk-production-deployment** - Deploy tested agents
- **adk-real-time-agents** - Testing streaming agents

## Next Steps

1. **Set up test environment** with pytest and fixtures
2. **Write unit tests** for all tool functions
3. **Add integration tests** for agent conversations
4. **Configure CI/CD** with GitHub Actions
5. **Run evaluations** before major releases
6. **Monitor quality metrics** over time
