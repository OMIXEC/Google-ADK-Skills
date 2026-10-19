"""Collaborative workflow template.

Pattern: Coordinator delegates to specialized sub-agents.
Coordinator does NOT execute tasks — only plans and routes.
"""

from google.adk import Agent
from .agents import coordinator, researcher, coder, reviewer

__all__ = ["coordinator", "researcher", "coder", "reviewer"]


if __name__ == "__main__":
    import asyncio

    from google.adk.runners import InMemoryRunner
    from google.genai import types

    async def main():
        runner = InMemoryRunner(agent=coordinator, app_name="coordinator")
        session = await runner.session_service.create_session(
            app_name="coordinator", user_id="local"
        )
        message = types.Content(role="user", parts=[types.Part(text="Build a REST API for user management")])
        async for event in runner.run_async(
            user_id="local", session_id=session.id, new_message=message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text)

    asyncio.run(main())
