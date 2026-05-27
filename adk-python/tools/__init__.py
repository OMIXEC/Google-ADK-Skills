"""Tool discovery for ADK agents.

Exports all tool functions from model_tools and scaffold_tools for use
in agent.yaml tool lists via the ADK tool registry.
"""

from .model_tools import ALL_TOOLS as MODEL_TOOLS
from .scaffold_tools import ALL_TOOLS as SCAFFOLD_TOOLS

ALL_TOOLS = MODEL_TOOLS + SCAFFOLD_TOOLS
__all__ = ["ALL_TOOLS", "MODEL_TOOLS", "SCAFFOLD_TOOLS"]
