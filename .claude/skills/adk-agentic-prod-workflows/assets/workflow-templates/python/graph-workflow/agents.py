"""Agent definitions for graph workflow."""

from google.adk import Agent
from google.adk.tools import FunctionTool
from .tools import validate_input, process_data

validator_agent = Agent(
    name="validator",
    model="gemini-2.5-flash",
    instruction="""You are a data validator.
    1. Call validate_input to check the incoming data.
    2. If validation passes, set state['is_valid'] = True.
    3. If validation fails, set state['is_valid'] = False and explain why.""",
    tools=[FunctionTool(validate_input)],
)

processor_agent = Agent(
    name="processor",
    model="gemini-2.5-flash",
    instruction="""You are a data processor.
    Call process_data on validated input and return structured results.
    Report any errors clearly.""",
    tools=[FunctionTool(process_data)],
)

fallback_agent = Agent(
    name="fallback",
    model="gemini-2.5-flash",
    instruction="""You are a fallback handler.
    The input failed validation. Tell the user what went wrong and
    suggest how to fix it. Be specific about the validation failure.""",
)
