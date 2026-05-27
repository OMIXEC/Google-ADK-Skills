"""Graph-based workflow template.

Pattern: DAG with conditional branching.
Nodes = agents, Edges = transitions, Conditions = routing logic.
"""

from google.adk import Agent
from google.adk.agents.graph import GraphAgent, Node, Edge, Condition
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field
import structlog

from .agents import validator_agent, processor_agent, fallback_agent
from .tools import validate_input, process_data

logger = structlog.get_logger(__name__)


def build_graph() -> GraphAgent:
    """Assemble the workflow graph."""
    return GraphAgent(
        name="graph_workflow",
        description="DAG workflow with validation gate and conditional routing",
        nodes=[
            Node(id="validate", agent=validator_agent),
            Node(id="process", agent=processor_agent),
            Node(id="fallback", agent=fallback_agent),
        ],
        edges=[
            Edge(
                source="validate",
                target="process",
                condition=Condition(lambda state: state.get("is_valid", False)),
            ),
            Edge(
                source="validate",
                target="fallback",
                condition=Condition(lambda state: not state.get("is_valid", False)),
            ),
        ],
        entry_point="validate",
    )


graph_agent = build_graph()


if __name__ == "__main__":
    import asyncio
    from google.adk.runners import InProcessRunner

    async def main():
        runner = InProcessRunner(agent=graph_agent)
        result = await runner.run(query="Process order #12345")
        print(f"Result: {result}")

    asyncio.run(main())
