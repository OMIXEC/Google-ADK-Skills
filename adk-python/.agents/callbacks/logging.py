"""Structured logging callbacks for ADK agents.

Produces JSON-lines structured logs with correlation IDs for observability.
"""

import json
import logging
import time
import uuid
from typing import Any

logger = logging.getLogger("adk.agents")


def _format_event(
    event_type: str,
    agent_name: str,
    data: dict[str, Any] | None = None,
) -> str:
    return json.dumps({
        "timestamp": time.time(),
        "event": event_type,
        "agent": agent_name,
        "correlation_id": str(uuid.uuid4()),
        **(data or {}),
    })


def before_agent_callback(agent_name: str) -> None:
    """Log agent invocation start with correlation ID."""
    logger.info(_format_event("agent_invoke_start", agent_name))


def after_agent_callback(agent_name: str, latency_ms: float | None = None) -> None:
    """Log agent invocation completion with latency."""
    logger.info(_format_event("agent_invoke_end", agent_name, {
        "latency_ms": latency_ms,
    }))
