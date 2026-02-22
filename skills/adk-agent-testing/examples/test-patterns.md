# ADK Agent Testing Patterns

Complete examples demonstrating testing patterns for Google ADK agents.

## ADK Testing Commands Overview

The ADK provides three primary testing commands for local development:

### 1. adk run - Local Agent Execution

Run your agent directly from the command line:

```bash
# Basic execution
adk run

# With specific input
adk run --input "What is the weather today?"

# Custom configuration
adk run --config config/dev.yaml

# Verbose mode
adk run --verbose
```

**Use cases:**
- Quick smoke tests during development
- Testing agent behavior with specific inputs
- Debugging tool integrations
- Validating configuration changes

**Example workflow:**
```bash
# Make changes to agent
vim agent.py

# Test immediately
adk run --input "Test my new feature"

# Check logs
adk run --verbose --input "Debug this issue"
```

### 2. adk web - Interactive Web UI Testing

Launch a web interface for interactive testing:

```bash
# Start web UI (default: http://localhost:8000)
adk web

# Custom port
adk web --port 3000

# With hot reload
adk web --reload

# Production mode
adk web --no-debug
```

**Features:**
- Multi-turn conversation testing
- Visual tool execution tracking
- Response time monitoring
- Conversation history export

**Best for:**
- Manual QA sessions
- Demonstrating agent capabilities
- Testing complex multi-turn interactions
- Collecting test cases from real conversations

**Example session:**
1. Start: `adk web`
2. Open browser to http://localhost:8000
3. Test conversation flows interactively
4. Export successful conversations as test cases
5. Use exported data in automated tests

### 3. adk api_server - REST API Testing Endpoint

Run agent as REST API for integration testing:

```bash
# Start API server
adk api_server

# Custom configuration
adk api_server --host 0.0.0.0 --port 8080

# With OpenAPI docs
adk api_server --docs
```

**API Endpoints:**

```bash
# Health check
curl http://localhost:8080/health

# Send message
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can you do?",
    "session_id": "test-session-1"
  }'

# Get conversation history
curl http://localhost:8080/history/test-session-1

# OpenAPI documentation
open http://localhost:8080/docs
```

**Integration testing example:**

```python
import requests
import pytest

API_BASE = "http://localhost:8080"

@pytest.fixture(scope="module")
def api_server():
    """Start API server for tests."""
    import subprocess
    proc = subprocess.Popen(["adk", "api_server"])
    time.sleep(2)  # Wait for startup
    yield
    proc.terminate()

def test_api_health(api_server):
    """Test API health endpoint."""
    response = requests.get(f"{API_BASE}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_chat(api_server):
    """Test chat endpoint."""
    response = requests.post(
        f"{API_BASE}/chat",
        json={
            "message": "Hello",
            "session_id": "test-1"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 0

def test_api_streaming(api_server):
    """Test streaming responses."""
    response = requests.post(
        f"{API_BASE}/chat/stream",
        json={"message": "Tell me a story"},
        stream=True
    )
    chunks = []
    for line in response.iter_lines():
        if line:
            chunks.append(line.decode())
    assert len(chunks) > 0
```

## Unit Testing with InMemoryRunner

The ADK's InMemoryRunner allows fast, deterministic unit tests:

```python
from adk.testing import InMemoryRunner
from my_agent import create_agent

def test_agent_with_inmemory_runner():
    """Test agent using InMemoryRunner."""

    # Create agent
    agent = create_agent()

    # Create in-memory runner (no API calls)
    runner = InMemoryRunner(
        agent=agent,
        mock_responses={
            "What is 2+2?": "The answer is 4.",
            "search:.*": "Here are the search results...",
        }
    )

    # Test basic interaction
    response = runner.run("What is 2+2?")
    assert "4" in response.text

    # Test with regex pattern matching
    response = runner.run("search for Python")
    assert "search results" in response.text

    # Verify no external API calls were made
    assert runner.api_calls_made == 0
```

**Advanced InMemoryRunner usage:**

```python
def test_tool_execution_with_runner():
    """Test tool execution flow."""

    agent = create_agent_with_tools()

    runner = InMemoryRunner(
        agent=agent,
        mock_tools={
            "search_database": lambda query: [
                {"id": 1, "title": f"Result for {query}"}
            ],
            "calculate": lambda expr: eval(expr),
        }
    )

    # Test tool invocation
    response = runner.run("Search for Python tutorials")

    # Verify tool was called
    assert runner.tools_called == ["search_database"]
    assert runner.tool_calls[0]["args"]["query"] == "Python tutorials"

    # Test calculation tool
    response = runner.run("Calculate 10 * 5")
    assert "50" in response.text
```

## Conversation Replay Testing

Test agent behavior by replaying recorded conversations:

```python
from adk.testing import ConversationReplay
import json

def test_conversation_replay():
    """Replay a recorded conversation for regression testing."""

    # Load recorded conversation
    with open("tests/fixtures/customer_support_conversation.json") as f:
        conversation = json.load(f)

    # conversation structure:
    # {
    #   "turns": [
    #     {"user": "I need help", "expected_contains": "how can I help"},
    #     {"user": "Reset password", "expected_contains": "reset link"},
    #   ]
    # }

    agent = create_agent()
    replay = ConversationReplay(agent=agent)

    # Replay conversation
    result = replay.run(conversation["turns"])

    # Check all turns passed
    assert result.all_passed
    assert result.failed_turns == []

    # Get detailed report
    for i, turn in enumerate(result.turns):
        print(f"Turn {i+1}: {'PASS' if turn.passed else 'FAIL'}")
        if not turn.passed:
            print(f"  Expected: {turn.expected}")
            print(f"  Got: {turn.actual}")
```

**Creating replay fixtures from live conversations:**

```python
from adk.testing import ConversationRecorder

def record_conversation_for_testing():
    """Record a conversation for later replay."""

    recorder = ConversationRecorder(
        agent=create_agent(),
        output_file="tests/fixtures/new_conversation.json"
    )

    # Have conversation
    recorder.user_says("Hello, I need help")
    recorder.user_says("What are your hours?")
    recorder.user_says("Thank you")

    # Save with assertions
    recorder.save(
        assertions=[
            {"turn": 1, "contains": "help you"},
            {"turn": 2, "contains": ["hours", "9", "5"]},
        ]
    )
```

## Tool Validation Testing

Ensure tools are properly defined and integrated:

```python
from adk.testing import ToolValidator

def test_tool_definitions():
    """Validate all tools are properly defined."""

    agent = create_agent()
    validator = ToolValidator(agent)

    # Check all tools have required fields
    report = validator.validate_all()

    assert report.all_valid
    assert len(report.errors) == 0

    # Detailed checks
    for tool_name, tool_report in report.tools.items():
        assert tool_report.has_name
        assert tool_report.has_description
        assert tool_report.has_parameters
        assert tool_report.description_length > 20  # Meaningful description

def test_tool_schema_compliance():
    """Test tool parameter schemas."""

    from my_agent.tools import search_database

    validator = ToolValidator.for_function(search_database)

    # Validate schema
    assert validator.has_valid_schema()

    # Check required parameters
    assert "query" in validator.required_params

    # Check parameter types
    assert validator.param_types["query"] == "string"

    # Test with valid inputs
    assert validator.validate_input({"query": "test"}) == True

    # Test with invalid inputs
    assert validator.validate_input({}) == False  # Missing required
    assert validator.validate_input({"query": 123}) == False  # Wrong type

def test_tool_execution():
    """Test actual tool execution."""

    from my_agent.tools import calculate_metrics

    # Test with valid data
    result = calculate_metrics([1, 2, 3, 4, 5])

    assert result["mean"] == 3.0
    assert result["sum"] == 15
    assert result["count"] == 5

    # Test edge cases
    assert calculate_metrics([]) == {"mean": 0, "sum": 0, "count": 0}
    assert calculate_metrics([42]) == {"mean": 42, "sum": 42, "count": 1}

    # Test error handling
    try:
        calculate_metrics("invalid")
        assert False, "Should have raised error"
    except TypeError:
        pass  # Expected
```

## Evaluation Framework with Custom Metrics

Create custom evaluation metrics for your domain:

```python
from adk.evaluation import Evaluator, Metric
from typing import Dict, Any

class DomainSpecificEvaluator(Evaluator):
    """Custom evaluator for domain-specific metrics."""

    def __init__(self, agent):
        super().__init__(agent)
        self.register_metrics([
            AccuracyMetric(),
            ToneMetric(),
            CompletenessMetric(),
            ComplianceMetric(),
        ])

    async def evaluate_conversation(
        self,
        conversation: list[Dict[str, str]]
    ) -> Dict[str, float]:
        """Evaluate a complete conversation."""

        scores = {}

        for metric in self.metrics:
            score = await metric.score(conversation)
            scores[metric.name] = score

        # Compute weighted aggregate
        scores["overall"] = self._compute_weighted_score(scores)

        return scores

class AccuracyMetric(Metric):
    """Measure factual accuracy."""

    name = "accuracy"

    async def score(self, conversation: list) -> float:
        """Score accuracy of responses."""

        correct = 0
        total = 0

        for turn in conversation:
            if "ground_truth" in turn:
                total += 1
                response = turn["agent_response"]
                truth = turn["ground_truth"]

                # Use LLM-as-judge
                is_correct = await self.judge_accuracy(response, truth)
                if is_correct:
                    correct += 1

        return correct / total if total > 0 else 0.0

    async def judge_accuracy(self, response: str, truth: str) -> bool:
        """Use LLM to judge if response is accurate."""

        from adk.evaluation import LLMJudge

        judge = LLMJudge(model="gemini-1.5-pro")

        prompt = f"""
        Is this response factually accurate given the ground truth?

        Ground truth: {truth}
        Response: {response}

        Answer: Yes or No
        """

        result = await judge.judge(prompt)
        return "yes" in result.lower()

class ToneMetric(Metric):
    """Measure appropriateness of tone."""

    name = "tone"

    async def score(self, conversation: list) -> float:
        """Score tone appropriateness."""

        scores = []

        for turn in conversation:
            response = turn["agent_response"]
            expected_tone = turn.get("expected_tone", "professional")

            tone_score = await self.evaluate_tone(response, expected_tone)
            scores.append(tone_score)

        return sum(scores) / len(scores) if scores else 0.0

    async def evaluate_tone(self, text: str, expected: str) -> float:
        """Evaluate if tone matches expectation."""

        # Keywords for different tones
        tone_keywords = {
            "professional": ["please", "thank you", "assist", "help"],
            "friendly": ["hey", "great", "awesome", "happy"],
            "formal": ["kindly", "request", "appreciate", "regards"],
        }

        keywords = tone_keywords.get(expected, [])
        matches = sum(1 for kw in keywords if kw in text.lower())

        return min(matches / len(keywords), 1.0) if keywords else 0.5
```

## Benchmarking with Vertex AI Evaluation

Integrate with Google Vertex AI for comprehensive evaluation:

```python
from google.cloud import aiplatform
from adk.evaluation import VertexEvaluator

def evaluate_with_vertex_ai():
    """Run evaluation using Vertex AI."""

    # Initialize Vertex AI
    aiplatform.init(project="my-project", location="us-central1")

    # Create evaluator
    evaluator = VertexEvaluator(
        agent=create_agent(),
        metrics=[
            "bleu",
            "rouge",
            "coherence",
            "groundedness",
            "fluency",
        ]
    )

    # Load test dataset
    test_dataset = load_test_dataset("data/eval_dataset.jsonl")

    # Run evaluation
    results = evaluator.evaluate(
        dataset=test_dataset,
        batch_size=10,
    )

    # Generate report
    report = evaluator.generate_report(results)

    print(f"Overall Score: {report.overall_score}")
    print(f"BLEU: {report.metrics['bleu']}")
    print(f"Coherence: {report.metrics['coherence']}")

    # Save results
    report.save("evaluation_results.json")

    return report

def load_test_dataset(path: str):
    """Load test dataset in Vertex AI format."""

    import json

    dataset = []
    with open(path) as f:
        for line in f:
            item = json.loads(line)
            dataset.append({
                "input": item["prompt"],
                "reference": item["expected_response"],
                "context": item.get("context", ""),
            })

    return dataset
```

## A/B Testing Patterns

Compare different agent configurations:

```python
from adk.testing import ABTest
import asyncio

async def run_ab_test():
    """Run A/B test comparing two agent versions."""

    # Create two variants
    agent_a = create_agent(config="config_a.yaml")  # Current
    agent_b = create_agent(config="config_b.yaml")  # New

    # Load test cases
    test_cases = load_test_cases("tests/ab_test_cases.json")

    # Run A/B test
    ab_test = ABTest(
        variant_a=agent_a,
        variant_b=agent_b,
        test_cases=test_cases,
    )

    results = await ab_test.run()

    # Analyze results
    print(f"Variant A - Win Rate: {results.a_win_rate}")
    print(f"Variant B - Win Rate: {results.b_win_rate}")
    print(f"Statistical Significance: {results.p_value < 0.05}")

    # Detailed comparison
    for metric in ["accuracy", "latency", "user_satisfaction"]:
        print(f"\n{metric}:")
        print(f"  A: {results.a_metrics[metric]}")
        print(f"  B: {results.b_metrics[metric]}")
        print(f"  Improvement: {results.improvements[metric]}")

    return results

class ABTest:
    """A/B testing framework for agents."""

    def __init__(self, variant_a, variant_b, test_cases):
        self.variant_a = variant_a
        self.variant_b = variant_b
        self.test_cases = test_cases

    async def run(self):
        """Run A/B test on all test cases."""

        results_a = []
        results_b = []

        for case in self.test_cases:
            # Get responses from both variants
            response_a = await self.variant_a.ask(case["input"])
            response_b = await self.variant_b.ask(case["input"])

            # Judge which is better
            winner = await self.judge_winner(
                case["input"],
                response_a,
                response_b,
                case.get("criteria", [])
            )

            results_a.append({
                "case": case,
                "response": response_a,
                "won": winner == "a",
            })

            results_b.append({
                "case": case,
                "response": response_b,
                "won": winner == "b",
            })

        return self.compile_results(results_a, results_b)

    async def judge_winner(self, input, response_a, response_b, criteria):
        """Use LLM to judge which response is better."""

        from adk.evaluation import LLMJudge

        judge = LLMJudge(model="gemini-1.5-pro")

        prompt = f"""
        Compare these two agent responses and determine which is better.

        Input: {input}

        Response A: {response_a.text}
        Response B: {response_b.text}

        Criteria: {', '.join(criteria)}

        Which response is better? Answer: A, B, or Tie
        """

        result = await judge.judge(prompt)

        if "response a" in result.lower() and "response b" not in result.lower():
            return "a"
        elif "response b" in result.lower():
            return "b"
        else:
            return "tie"
```

## Best Practices Summary

### 1. Development Workflow
```bash
# Quick iteration
adk run --input "test feature"

# Interactive testing
adk web

# API integration tests
adk api_server  # In one terminal
pytest tests/test_api.py  # In another
```

### 2. Test Organization
```
tests/
├── unit/
│   ├── test_tools.py           # Fast, isolated
│   └── test_prompts.py
├── integration/
│   ├── test_inmemory.py        # InMemoryRunner tests
│   └── test_conversations.py   # Conversation replay
├── api/
│   └── test_api_server.py      # API endpoint tests
└── evaluation/
    ├── test_metrics.py         # Custom metrics
    └── test_benchmarks.py      # Vertex AI evaluation
```

### 3. CI/CD Pipeline
```yaml
# .github/workflows/test.yml
- Unit tests (always)
- Integration tests (on PR)
- API tests (on PR)
- Evaluation (on main)
- A/B tests (before release)
```

### 4. Testing Checklist
- [ ] Unit tests for all tools
- [ ] Integration tests for key flows
- [ ] Conversation replay for regressions
- [ ] Tool validation
- [ ] API endpoint tests
- [ ] Evaluation metrics tracked
- [ ] A/B tests for major changes
