"""Parallel fan-out template.

Pattern: Multiple workers run concurrently on independent inputs.
Uses ParallelAgent — all sub-agents execute in parallel.
"""

from google.adk import Agent
from google.adk.agents import ParallelAgent
from .agents import worker_a, worker_b, worker_c

fan_out = ParallelAgent(
    name="parallel_workers",
    description="Fan-out: 3 workers process data chunks concurrently",
    sub_agents=[worker_a, worker_b, worker_c],
)


if __name__ == "__main__":
    import asyncio

    from google.adk.runners import InMemoryRunner
    from google.genai import types

    async def main():
        runner = InMemoryRunner(agent=fan_out, app_name="fan-out")
        session = await runner.session_service.create_session(
            app_name="fan-out", user_id="local"
        )
        message = types.Content(role="user", parts=[types.Part(text="Process all data chunks in parallel")])
        async for event in runner.run_async(
            user_id="local", session_id=session.id, new_message=message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text)

    asyncio.run(main())
