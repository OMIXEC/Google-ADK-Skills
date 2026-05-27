"""Loop workflow: agent definitions."""

import os
from google.adk.agents import LlmAgent

MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash")


def build_generator(exit_tool) -> LlmAgent:
    """Agent that generates the initial output."""
    return LlmAgent(
        name="generator",
        model=MODEL,
        description="Generates content based on requirements. Uses exit_loop tool when output meets quality bar.",
        instruction="""You are a content generator. Your task is to produce output based on the requirements.

1. If this is your first run, generate initial output based on the user's requirements.
2. If feedback is available in session.state['feedback'], use it to improve your output.
3. Store your output in session.state['content'].
4. If you believe the output meets all requirements, call the exit_loop() tool to signal completion.
5. Be thorough and precise. Quality > speed.""",
        tools=[exit_tool],
        output_key="content",
    )


def build_critic(exit_tool) -> LlmAgent:
    """Agent that critiques output and signals when quality is good enough."""
    return LlmAgent(
        name="critic",
        model=MODEL,
        description="Reviews generated content and provides feedback. Signals loop exit when quality meets bar.",
        instruction="""You are a quality reviewer. Your task is to evaluate content and provide actionable feedback.

1. Read the content from session.state['content'].
2. Evaluate against these quality dimensions:
   - Completeness: Does it fully address the requirements?
   - Correctness: Is the information accurate?
   - Clarity: Is it well-structured and easy to understand?
3. If quality is sufficient (no major issues), call exit_loop() to signal completion.
4. Otherwise, provide specific, actionable feedback in session.state['feedback'].
   - Be specific: "The introduction lacks context about X" not "It could be better".
   - Prioritize: list the most critical improvement first.

Do NOT rewrite the content yourself. Your job is to evaluate and guide.""",
        tools=[exit_tool],
        output_key="feedback",
    )


def build_quality_scorer() -> LlmAgent:
    """Optional: dedicated quality scoring agent for quantitative evaluation."""
    return LlmAgent(
        name="quality_scorer",
        model=MODEL,
        description="Scores content on quality dimensions and decides pass/fail.",
        instruction="""You are a quality scoring agent. Evaluate the content from session.state['content'].

Score each dimension 0.0-1.0:
- completeness: 0.X (all requirements addressed?)
- correctness: 0.X (factually accurate?)
- clarity: 0.X (well-structured and readable?)

Return JSON: {"completeness": 0.X, "correctness": 0.X, "clarity": 0.X, "overall": 0.X}

Store the score in session.state['quality_score']. Call exit_loop() if overall >= 0.8.""",
        output_key="quality_score",
    )
