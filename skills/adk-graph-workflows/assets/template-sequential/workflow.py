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

    from google.adk.runners import InMemoryRunner
    from google.genai import types

    async def main():
        runner = InMemoryRunner(agent=pipeline, app_name="pipeline")
        session = await runner.session_service.create_session(
            app_name="pipeline", user_id="local"
        )
        message = types.Content(role="user", parts=[types.Part(text="Run ETL pipeline for daily sales")])
        async for event in runner.run_async(
            user_id="local", session_id=session.id, new_message=message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text)

    asyncio.run(main())
