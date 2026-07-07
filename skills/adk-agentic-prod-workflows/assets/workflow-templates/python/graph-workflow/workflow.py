"""ADK 2.x workflow template.

Pattern: DAG with conditional branching.
Nodes = agents or functions, edges = execution routes.
"""

from google.adk import Workflow
from google.adk.workflow import START
from pydantic import BaseModel, Field
import structlog

from .agents import validator_agent, processor_agent, fallback_agent
from .tools import validate_input, process_data

logger = structlog.get_logger(__name__)


def route_after_validation(node_input: dict) -> str:
    """Return the route key consumed by the Workflow edge map."""
    return "process" if node_input.get("is_valid", False) else "fallback"


def build_workflow() -> Workflow:
    """Assemble the ADK 2.x workflow graph."""
    return Workflow(
        name="root_agent",
        edges=[
            (
                START,
                validator_agent,
                route_after_validation,
                {"process": processor_agent, "fallback": fallback_agent},
            ),
        ],
    )


root_agent = build_workflow()


if __name__ == "__main__":
    import asyncio
    from google.adk.runners import InProcessRunner

    async def main():
        runner = InProcessRunner(agent=root_agent)
        result = await runner.run(query="Process order #12345")
        print(f"Result: {result}")

    asyncio.run(main())
