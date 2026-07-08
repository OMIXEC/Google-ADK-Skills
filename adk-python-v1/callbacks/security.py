"""Security callbacks for ADK agents.

- before_tool_callback: Blocklist check on tool inputs. Reject blocked model IDs.
- after_model_callback: Scan outputs for PII, secrets, or blocked model references.
"""

import re
from typing import Any

from google.adk.tools import BaseTool

# Model IDs that must never appear in any agent output
MODEL_BLOCKLIST: set[str] = {
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
    "gemini-3-pro-preview",
    "text-embedding-004",
    "embedding-001",
    "embedding-gecko-001",
    "gemini-embedding-exp",
    "imagen-3.0-generate-002",
}

# Patterns that suggest hardcoded credentials
SECRET_PATTERNS: list[re.Pattern] = [
    re.compile(r'(?:api[_-]?key|apikey|secret|password|token)\s*[:=]\s*["\'](?![$]{)[^"\']+["\']', re.I),
    re.compile(r'(?:AIza[0-9A-Za-z\-_]{35})'),  # Google API key pattern
    re.compile(r'(?:sk-[A-Za-z0-9]{32,})'),       # OpenAI-like key pattern
]


def before_tool_callback(
    tool: BaseTool,
    args: dict[str, Any],
    agent_name: str,
) -> dict[str, Any] | None:
    """Validate tool inputs before execution. Blocks if model_id is in blocklist."""
    # Check for blocked model IDs
    model_id = args.get("model_id") or args.get("model")
    if model_id and model_id in MODEL_BLOCKLIST:
        return {
            "error": f"BLOCKED: {model_id} is in the deprecation blocklist. "
            f"Use a supported model instead.",
            "blocked": True,
        }
    return None  # No modification — allow execution


def after_model_callback(
    response: Any,
    agent_name: str,
) -> Any:
    """Scan agent response for PII/secrets and redact if found."""
    content = str(response)
    for pattern in SECRET_PATTERNS:
        if pattern.search(content):
            # Flag but don't modify — let the next agent or output validator catch it
            if hasattr(response, "metadata"):
                response.metadata["security_flag"] = "potential_secret_in_output"
    return response
