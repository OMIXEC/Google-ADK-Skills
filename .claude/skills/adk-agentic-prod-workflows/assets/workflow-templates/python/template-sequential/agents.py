"""Agent definitions for sequential pipeline."""

from google.adk import Agent
from google.adk.tools import FunctionTool
from .tools import extract_data, transform_data, load_data

extract_agent = Agent(
    name="extractor",
    model="gemini-2.5-flash",
    instruction="""You are a data extractor (step 1/3).
    Call extract_data to pull data from the source.
    Return raw data with record count and source metadata.""",
    tools=[FunctionTool(extract_data)],
)

transform_agent = Agent(
    name="transformer",
    model="gemini-2.5-flash",
    instruction="""You are a data transformer (step 2/3).
    Call transform_data on the extracted data.
    Apply cleaning, normalization, and business rules.
    Return transformed data with transformation stats.""",
    tools=[FunctionTool(transform_data)],
)

load_agent = Agent(
    name="loader",
    model="gemini-2.5-flash",
    instruction="""You are a data loader (step 3/3).
    Call load_data to write transformed data to the destination.
    Verify row counts match. Report load status.""",
    tools=[FunctionTool(load_data)],
)
