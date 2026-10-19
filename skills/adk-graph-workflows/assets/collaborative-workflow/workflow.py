"""Collaborative workflow template.

Pattern: Coordinator delegates to specialized sub-agents.
Coordinator does NOT execute tasks — only plans and routes.
"""

from google.adk import Agent
from .agents import coordinator, researcher, coder, reviewer

__all__ = ["coordinator", "researcher", "coder", "reviewer"]


if __name__ == "__main__":
    import asyncio
    from google.adk.runners import InProcessRunner

    async def main():
        runner = InProcessRunner(agent=coordinator)
        result = await runner.run(query="Build a REST API for user management")
        print(f"Result: {result}")

    asyncio.run(main())
