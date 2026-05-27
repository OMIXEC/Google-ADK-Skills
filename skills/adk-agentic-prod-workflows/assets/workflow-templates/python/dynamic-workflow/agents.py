"""Agent definitions for dynamic workflow."""

from google.adk import Agent
from google.adk.tools import FunctionTool
from .tools import fetch_data, transform_data, enrich_data

fetcher_agent = Agent(
    name="fetcher",
    model="gemini-2.5-flash",
    instruction="""You are a data fetcher.
    Call fetch_data to retrieve data from the specified source.
    Return structured results with record count.""",
    tools=[FunctionTool(fetch_data)],
)

transformer_agent = Agent(
    name="transformer",
    model="gemini-2.5-flash",
    instruction="""You are a data transformer.
    Call transform_data to apply transformations to the fetched data.
    Validate the output before returning.""",
    tools=[FunctionTool(transform_data)],
)

enricher_agent = Agent(
    name="enricher",
    model="gemini-2.5-flash",
    instruction="""You are a data enricher.
    Call enrich_data to add contextual information to transformed records.
    Only enrich when records exist; skip empty datasets.""",
    tools=[FunctionTool(enrich_data)],
)
