"""Model validation and routing tools for ADK agents.

These tools enforce anti-deprecation rules and complexity-based model selection.
Data source: scripts/fetch_models.py → references/model-cache.json
"""

import json
from enum import Enum
from pathlib import Path
from typing import Optional

from google.adk.tools import FunctionTool

# Hard-blocked models — must NEVER be used
HARD_BLOCKED: set[str] = {
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

# Known deprecated models with shutdown dates
DEPRECATED_MODELS: dict[str, str] = {
    "gemini-2.5-pro": "2026-10-16",
    "gemini-2.5-flash": "2026-10-16",
    "gemini-2.5-flash-lite": "2026-10-16",
    "gemini-embedding-001": "2026-07-14",
    "imagen-4.0-generate-001": "2026-06-24",
    "imagen-4.0-ultra-generate-001": "2026-06-24",
    "imagen-4.0-fast-generate-001": "2026-06-24",
}

CACHE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "references" / "model-cache.json"


class TaskComplexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


COMPLEXITY_MODEL_MAP: dict[TaskComplexity, str] = {
    TaskComplexity.LOW: "gemini-2.5-flash-lite",
    TaskComplexity.MEDIUM: "gemini-2.5-flash",
    TaskComplexity.HIGH: "gemini-2.5-pro",
}

TASK_MODEL_MAP: dict[str, str] = {
    "code_generation": "gemini-2.5-pro",
    "code_review": "gemini-2.5-pro",
    "architecture_design": "gemini-2.5-pro",
    "orchestration": "gemini-2.5-pro",
    "content_generation": "gemini-2.5-flash",
    "tool_calling": "gemini-2.5-flash",
    "rag": "gemini-2.5-flash",
    "multi_step_reasoning": "gemini-2.5-flash",
    "classification": "gemini-2.5-flash-lite",
    "triage": "gemini-2.5-flash-lite",
    "formatting": "gemini-2.5-flash-lite",
    "real_time_audio": "gemini-2.5-flash-live",
    "tts": "chirp-3-hd-charon",
    "stt": "chirp-3-hd-charon",
    "image_gen": "imagen-4.0-fast-generate-001",
    "video_gen": "veo-3.0-generate-preview",
    "embedding": "gemini-embedding-002",
    "music_gen": "lyria-3.0-generate",
}


def model_validate(model_id: str) -> dict:
    """Validate a model ID against the blocklist and deprecation list.

    Returns:
        dict with keys: valid (bool), status (str), reason (str), suggested (str|None)
    """
    if model_id in HARD_BLOCKED:
        return {
            "valid": False,
            "status": "blocked",
            "reason": f"{model_id} is HARD-BLOCKED and must never be used.",
            "suggested": _find_replacement(model_id),
        }
    if model_id in DEPRECATED_MODELS:
        shutdown = DEPRECATED_MODELS[model_id]
        return {
            "valid": False,
            "status": "deprecated",
            "reason": f"{model_id} is deprecated. Shutdown date: {shutdown}.",
            "suggested": _find_replacement(model_id),
        }
    # Check cache for additional deprecation info
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text())
        for m in cache.get("deprecated_models", []):
            if m["id"] == model_id:
                return {
                    "valid": False,
                    "status": "deprecated",
                    "reason": f"{model_id} is deprecated per live catalog.",
                    "suggested": _find_replacement(model_id),
                }
    return {"valid": True, "status": "stable", "reason": "", "suggested": None}


def _find_replacement(model_id: str) -> Optional[str]:
    """Suggest a replacement for a blocked/deprecated model."""
    replacements = {
        "gemini-2.0-flash": "gemini-2.5-flash",
        "gemini-2.0-flash-001": "gemini-2.5-flash",
        "gemini-2.0-flash-lite": "gemini-2.5-flash-lite",
        "gemini-2.0-flash-lite-001": "gemini-2.5-flash-lite",
        "gemini-3-pro-preview": "gemini-2.5-pro",
        "text-embedding-004": "gemini-embedding-002",
        "embedding-001": "gemini-embedding-002",
        "embedding-gecko-001": "gemini-embedding-002",
        "gemini-embedding-exp": "gemini-embedding-002",
        "imagen-3.0-generate-002": "imagen-4.0-fast-generate-001",
        "imagen-4.0-generate-001": "imagen-4.0-fast-generate-001",
        "imagen-4.0-ultra-generate-001": "imagen-4.0-ultra-generate-001",
        "imagen-4.0-fast-generate-001": "imagen-4.0-fast-generate-001",
    }
    return replacements.get(model_id)


def classify_complexity(task_description: str) -> dict:
    """Classify task complexity (LOW/MEDIUM/HIGH) from description.

    Heuristic-based. For production, replace with LLM-as-classifier pattern.
    """
    desc_lower = task_description.lower()

    high_keywords = [
        "architecture", "design system", "complex", "multi-agent",
        "code generation", "refactor", "planning", "orchestrate",
        "security audit", "optimize", "production",
    ]
    medium_keywords = [
        "tool calling", "reasoning", "analyze", "summarize",
        "rag", "retrieval", "multi-step", "review", "translate",
    ]

    high_hits = sum(1 for kw in high_keywords if kw in desc_lower)
    medium_hits = sum(1 for kw in medium_keywords if kw in desc_lower)

    if high_hits >= 2:
        complexity = TaskComplexity.HIGH
    elif high_hits >= 1 or medium_hits >= 2:
        complexity = TaskComplexity.MEDIUM
    else:
        complexity = TaskComplexity.LOW

    return {
        "complexity": complexity.value,
        "recommended_model": COMPLEXITY_MODEL_MAP[complexity],
        "high_hits": high_hits,
        "medium_hits": medium_hits,
    }


def fetch_model_cache() -> dict:
    """Load the current model cache. Returns summary with counts by type/status."""
    if not CACHE_PATH.exists():
        return {"error": "model-cache.json not found. Run scripts/fetch_models.py first."}
    cache = json.loads(CACHE_PATH.read_text())
    return {
        "fetched_at": cache.get("fetched_at"),
        "summary": cache.get("summary", {}),
        "types": {
            t: len(models) for t, models in cache.get("models_by_type", {}).items()
        },
        "deprecated_count": len(cache.get("deprecated_models", [])),
        "blocked_count": len(cache.get("blocked_models", [])),
    }


def get_model_for_task(task_type: str, complexity: str = "medium") -> dict:
    """Get the recommended model for a task type and complexity level.

    Args:
        task_type: One of the known task types (code_generation, rag, etc.)
        complexity: low, medium, or high

    Returns:
        dict with model_id and validation result
    """
    # For LLM tasks, complexity overrides the task map
    llm_tasks = {
        "code_generation", "code_review", "architecture_design",
        "orchestration", "content_generation", "tool_calling",
        "rag", "multi_step_reasoning", "classification",
        "triage", "formatting",
    }
    if task_type in llm_tasks:
        try:
            tc = TaskComplexity(complexity)
        except ValueError:
            tc = TaskComplexity.MEDIUM
        model_id = COMPLEXITY_MODEL_MAP[tc]
    elif task_type in TASK_MODEL_MAP:
        model_id = TASK_MODEL_MAP[task_type]
    else:
        model_id = "gemini-2.5-flash"

    validation = model_validate(model_id)
    return {"task_type": task_type, "complexity": complexity,
            "model_id": model_id, "validation": validation}


# Export as ADK FunctionTools
model_validate_tool = FunctionTool(func=model_validate)
classify_complexity_tool = FunctionTool(func=classify_complexity)
fetch_model_cache_tool = FunctionTool(func=fetch_model_cache)
get_model_for_task_tool = FunctionTool(func=get_model_for_task)

ALL_TOOLS = [
    model_validate_tool,
    classify_complexity_tool,
    fetch_model_cache_tool,
    get_model_for_task_tool,
]
