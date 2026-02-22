"""
Basic Agent Testing Demo

Demonstrates how to set up and run tests for an ADK agent.
Run with: pytest examples/basic_testing_demo.py -v
"""

import asyncio
import pytest
from typing import Any
from dataclasses import dataclass


# ============================================================================
# Mock Classes (replace with actual ADK imports in real usage)
# ============================================================================

@dataclass
class AgentResponse:
    """Mock agent response."""
    text: str
    success: bool = True
    tools_used: list = None
    turn_count: int = 1

    def __post_init__(self):
        if self.tools_used is None:
            self.tools_used = []


class MockAgent:
    """Mock agent for demonstration."""

    def __init__(self, name: str, tools: list = None):
        self.name = name
        self.tools = tools or []
        self.conversation_history = []

    async def ask(self, question: str) -> AgentResponse:
        """Simulate agent response."""
        self.conversation_history.append(question)

        # Simple mock responses for demo
        if "name" in question.lower() and len(self.conversation_history) > 1:
            # Check for name in history
            for msg in self.conversation_history:
                if "my name is" in msg.lower():
                    name = msg.split("is")[-1].strip().rstrip(".")
                    return AgentResponse(
                        text=f"Your name is {name}.",
                        turn_count=len(self.conversation_history)
                    )

        if "2 + 2" in question or "2+2" in question:
            return AgentResponse(text="The answer is 4.")

        if "search" in question.lower():
            return AgentResponse(
                text="Here are the search results...",
                tools_used=["web_search"]
            )

        return AgentResponse(
            text="I understand. How can I help you?",
            turn_count=len(self.conversation_history)
        )


class AgentTestHarness:
    """Test harness for running agent tests."""

    def __init__(self, timeout: int = 30, max_turns: int = 10):
        self.timeout = timeout
        self.max_turns = max_turns

    async def ask(self, agent: MockAgent, question: str) -> AgentResponse:
        """Send a question to the agent."""
        return await asyncio.wait_for(
            agent.ask(question),
            timeout=self.timeout
        )


class Conversation:
    """Manage multi-turn conversations."""

    def __init__(self, agent: MockAgent):
        self.agent = agent
        self.turn_count = 0
        self.history = []

    async def say(self, message: str) -> AgentResponse:
        """Send a message in the conversation."""
        self.turn_count += 1
        self.history.append({"role": "user", "content": message})
        response = await self.agent.ask(message)
        self.history.append({"role": "assistant", "content": response.text})
        return response


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_agent():
    """Create a test agent."""
    return MockAgent(
        name="test_agent",
        tools=["web_search", "calculator"]
    )


@pytest.fixture
def test_harness():
    """Create a test harness."""
    return AgentTestHarness(timeout=30, max_turns=10)


# ============================================================================
# Unit Tests - Tool Functions
# ============================================================================

class TestToolFunctions:
    """Test individual tool functions."""

    def test_calculator_addition(self):
        """Test basic addition."""
        # In real usage, this would test your actual tool
        result = 2 + 2
        assert result == 4

    def test_calculator_handles_zero(self):
        """Test edge case with zero."""
        result = 0 + 0
        assert result == 0

    @pytest.mark.parametrize("a,b,expected", [
        (1, 2, 3),
        (10, 20, 30),
        (-1, 1, 0),
        (0, 0, 0),
    ])
    def test_calculator_parameterized(self, a, b, expected):
        """Test multiple input combinations."""
        result = a + b
        assert result == expected


# ============================================================================
# Integration Tests - Agent Conversations
# ============================================================================

class TestAgentConversations:
    """Test agent conversation capabilities."""

    @pytest.mark.asyncio
    async def test_agent_answers_question(self, test_agent, test_harness):
        """Test agent can answer a basic question."""
        response = await test_harness.ask(
            agent=test_agent,
            question="What is 2 + 2?"
        )

        assert response.success
        assert "4" in response.text

    @pytest.mark.asyncio
    async def test_agent_uses_tools(self, test_agent, test_harness):
        """Test agent invokes tools appropriately."""
        response = await test_harness.ask(
            agent=test_agent,
            question="Search for Python tutorials."
        )

        assert response.success
        assert "web_search" in response.tools_used

    @pytest.mark.asyncio
    async def test_multi_turn_context(self, test_agent):
        """Test agent maintains context across turns."""
        conv = Conversation(agent=test_agent)

        # Turn 1: Introduce information
        r1 = await conv.say("My name is Alice.")
        assert r1.success

        # Turn 2: Reference previous context
        r2 = await conv.say("What is my name?")
        assert "Alice" in r2.text

        # Verify turn count
        assert conv.turn_count == 2


# ============================================================================
# Evaluation Tests - Quality Metrics
# ============================================================================

class TestQualityMetrics:
    """Test quality and evaluation metrics."""

    @pytest.mark.asyncio
    async def test_response_not_empty(self, test_agent, test_harness):
        """Responses should never be empty."""
        questions = [
            "Hello",
            "What can you do?",
            "Help me with something.",
        ]

        for q in questions:
            response = await test_harness.ask(test_agent, q)
            assert len(response.text) > 0, f"Empty response for: {q}"

    @pytest.mark.asyncio
    async def test_response_latency(self, test_agent, test_harness):
        """Responses should be fast."""
        import time

        start = time.time()
        await test_harness.ask(test_agent, "Quick question")
        latency = time.time() - start

        # Should respond within timeout
        assert latency < test_harness.timeout


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])
