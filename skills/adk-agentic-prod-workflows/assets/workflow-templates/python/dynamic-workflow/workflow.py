"""Dynamic workflow template.

Pattern: Imperative control flow with async/await.
No graph DSL — Python drives the execution order.
"""

from google.adk import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import InProcessRunner
from pydantic import BaseModel, Field
import structlog
import uuid
import time

from .agents import fetcher_agent, transformer_agent, enricher_agent
from .tools import fetch_data, transform_data, enrich_data

logger = structlog.get_logger(__name__)


class WorkflowState:
    """Mutable state bag propagated across workflow nodes."""

    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self.data: dict = {}
        self.errors: list[dict] = []
        self.node_results: dict = {}

    def add_error(self, node: str, error: str) -> None:
        self.errors.append({"node": node, "error": error, "correlation_id": self.correlation_id})


class DynamicWorkflow:
    """Workflow with imperative execution order.

    Each step calls a specific agent via the runner.
    State flows explicitly between steps.
    """

    def __init__(self):
        self.runner = InProcessRunner(agent=None)  # Agent set per call

    async def run(self, query: str) -> dict:
        correlation_id = f"wf_{uuid.uuid4().hex[:12]}"
        state = WorkflowState(correlation_id)
        start = time.monotonic()

        logger.info("workflow_start", correlation_id=correlation_id, query=query)

        try:
            # Step 1: Fetch
            fetch_result = await self._run_agent(fetcher_agent, query, state)
            if not fetch_result.get("ok"):
                return self._error_response(state, "Fetch step failed")
            state.data["raw"] = fetch_result.get("data", [])

            # Step 2: Transform
            transform_result = await self._run_agent(
                transformer_agent,
                f"Transform {len(state.data['raw'])} records",
                state,
            )
            if not transform_result.get("ok"):
                return self._error_response(state, "Transform step failed")
            state.data["transformed"] = transform_result.get("data", [])

            # Step 3: Enrich (conditional)
            if state.data["transformed"]:
                enrich_result = await self._run_agent(
                    enricher_agent,
                    f"Enrich {len(state.data['transformed'])} records",
                    state,
                )
                state.data["enriched"] = enrich_result.get("data", [])

            elapsed = (time.monotonic() - start) * 1000
            logger.info("workflow_complete", correlation_id=correlation_id, latency_ms=elapsed)

            return {
                "status": "ok",
                "correlation_id": correlation_id,
                "data": state.data.get("enriched", state.data.get("transformed", [])),
                "latency_ms": elapsed,
            }

        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            logger.error("workflow_error", correlation_id=correlation_id, error=str(e), latency_ms=elapsed)
            return self._error_response(state, str(e))

    async def _run_agent(self, agent: Agent, query: str, state: WorkflowState) -> dict:
        node_start = time.monotonic()
        try:
            result = await self.runner.run(agent=agent, query=query)
            elapsed = (time.monotonic() - node_start) * 1000
            logger.info("node_complete", node=agent.name, latency_ms=elapsed, correlation_id=state.correlation_id)
            return result
        except Exception as e:
            elapsed = (time.monotonic() - node_start) * 1000
            logger.error("node_error", node=agent.name, error=str(e), latency_ms=elapsed, correlation_id=state.correlation_id)
            state.add_error(agent.name, str(e))
            return {"ok": False, "error": str(e)}

    def _error_response(self, state: WorkflowState, message: str) -> dict:
        return {
            "status": "error",
            "correlation_id": state.correlation_id,
            "message": message,
            "errors": state.errors,
        }


dynamic_workflow = DynamicWorkflow()


if __name__ == "__main__":
    import asyncio

    async def main():
        result = await dynamic_workflow.run("Fetch and process Q3 sales data")
        print(f"Result: {result}")

    asyncio.run(main())
