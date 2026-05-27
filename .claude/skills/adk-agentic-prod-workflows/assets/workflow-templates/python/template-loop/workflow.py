"""Loop workflow: Generate → Critique → Improve → Repeat until quality gate passes.

Uses ADK LoopAgent with max_iterations and quality gate via exit_loop tool.
"""

import os
from google.adk.agents import LoopAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

from agents import build_generator, build_critic
from tools import build_exit_loop_tool


def build_workflow() -> LoopAgent:
    """Construct the iterative refinement workflow."""
    exit_loop_tool = build_exit_loop_tool()

    generator = build_generator(exit_tool=exit_loop_tool)
    critic = build_critic(exit_tool=exit_loop_tool)

    loop = LoopAgent(
        name="iterative_refinement",
        description="Generate → Critique → Improve → Repeat until quality gate passes",
        sub_agents=[generator, critic],
        max_iterations=int(os.getenv("LOOP_MAX_ITERATIONS", "5")),
    )
    return loop


def build_workflow_with_mcp(mcp_server_path: str) -> LoopAgent:
    """Construct workflow with MCP tools for external services."""
    exit_loop_tool = build_exit_loop_tool()

    generator = build_generator(exit_tool=exit_loop_tool)
    critic = build_critic(exit_tool=exit_loop_tool)

    # Optional MCP tools if external services needed
    mcp_tools = MCPToolset(
        connection_params=StdioServerParameters(
            command="python3",
            args=[mcp_server_path],
        ),
        tool_filter=os.getenv("MCP_TOOL_FILTER", "").split(",") if os.getenv("MCP_TOOL_FILTER") else None,
    )

    loop = LoopAgent(
        name="iterative_refinement_with_mcp",
        description="Generate → Critique → Improve with external tools",
        sub_agents=[generator, critic],
        max_iterations=int(os.getenv("LOOP_MAX_ITERATIONS", "5")),
    )
    return loop
