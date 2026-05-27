"""Agent definitions for collaborative workflow.

Pattern: Coordinator plans and delegates. Sub-agents execute.
Max delegation depth: 3. Errors isolated per sub-agent.
"""

from google.adk import Agent
from google.adk.tools import FunctionTool
from .tools import research_topic, write_code, review_code

researcher = Agent(
    name="researcher",
    model="gemini-2.5-flash",
    instruction="""You are a research specialist.
    Use research_topic to gather information on assigned topics.
    Return structured findings with sources.
    If information is unavailable, state what's missing clearly.""",
    tools=[FunctionTool(research_topic)],
)

coder = Agent(
    name="coder",
    model="gemini-2.5-pro",
    instruction="""You are a software engineer.
    Use write_code to implement features based on specifications.
    Write clean, tested, production-ready code.
    Include error handling and logging.""",
    tools=[FunctionTool(write_code)],
)

reviewer = Agent(
    name="reviewer",
    model="gemini-2.5-flash",
    instruction="""You are a code reviewer.
    Use review_code to check implementations for:
    - Correctness against the specification
    - Security issues (OWASP top 10)
    - Performance concerns
    - Missing error handling
    Approve or request changes with specific feedback.""",
    tools=[FunctionTool(review_code)],
)

coordinator = Agent(
    name="coordinator",
    model="gemini-2.5-pro",
    instruction="""You are a task coordinator. Your role is to plan and delegate — never execute tasks yourself.

    Workflow:
    1. Analyze the user's goal
    2. Break it into sequential steps
    3. Delegate each step to the appropriate sub-agent:
       - Research tasks → researcher
       - Implementation tasks → coder
       - Review tasks → reviewer
    4. Track progress in session.state['plan']
    5. After all steps complete, summarize results

    Rules:
    - Max delegation depth: 3 levels
    - If a sub-agent reports an error, decide: retry, skip, or escalate
    - Never answer questions that should be delegated""",
    sub_agents=[researcher, coder, reviewer],
)
