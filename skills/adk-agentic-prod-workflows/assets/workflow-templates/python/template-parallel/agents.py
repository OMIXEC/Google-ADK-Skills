"""Agent definitions for parallel fan-out."""

from google.adk import Agent
from google.adk.tools import FunctionTool
from .tools import process_chunk

worker_a = Agent(
    name="worker_a",
    model="gemini-2.5-flash",
    instruction="""You are Worker A in a parallel processing pool.
    Call process_chunk with worker_id='A' for assigned data chunks.
    Process independently — no coordination with other workers needed.""",
    tools=[FunctionTool(process_chunk)],
)

worker_b = Agent(
    name="worker_b",
    model="gemini-2.5-flash",
    instruction="""You are Worker B in a parallel processing pool.
    Call process_chunk with worker_id='B' for assigned data chunks.
    Process independently — no coordination with other workers needed.""",
    tools=[FunctionTool(process_chunk)],
)

worker_c = Agent(
    name="worker_c",
    model="gemini-2.5-flash",
    instruction="""You are Worker C in a parallel processing pool.
    Call process_chunk with worker_id='C' for assigned data chunks.
    Process independently — no coordination with other workers needed.""",
    tools=[FunctionTool(process_chunk)],
)
