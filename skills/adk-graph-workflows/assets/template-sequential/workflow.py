"""Sequential pipeline template.

Pattern: Linear chain. Each agent processes output from previous.
Uses SequentialAgent — data flows step1 → step2 → step3.
"""

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools import FunctionTool
from .agents import extract_agent, transform_agent, load_agent

pipeline = SequentialAgent(
    name="etl_pipeline",
    description="Extract → Transform → Load pipeline",
    sub_agents=[extract_agent, transform_agent, load_agent],
)


if __name__ == "__main__":
    import asyncio
    from google.adk.runners import InProcessRunner

    async def main():
        runner = InProcessRunner(agent=pipeline)
        result = await runner.run(query="Run ETL pipeline for daily sales")
        print(f"Result: {result}")

    asyncio.run(main())
