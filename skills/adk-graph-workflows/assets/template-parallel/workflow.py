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
    from google.adk.runners import InProcessRunner

    async def main():
        runner = InProcessRunner(agent=fan_out)
        result = await runner.run(query="Process all data chunks in parallel")
        print(f"Result: {result}")

    asyncio.run(main())
