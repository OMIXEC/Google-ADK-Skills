#!/usr/bin/env python3
"""Fetch latest Gemini models from Google AI docs.

Keeps the model catalog current by scraping ai.google.dev.
Run weekly via cron or CI to detect deprecations and new models.

Usage:
    python fetch_models.py
    python fetch_models.py --output model-cache.json
    python fetch_models.py --check-only  # Exit 1 if new deprecations found

Sources:
    https://ai.google.dev/gemini-api/docs/models
    https://ai.google.dev/gemini-api/docs/deprecations
"""

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

MODELS_URL = "https://ai.google.dev/gemini-api/docs/models"
DEPRECATIONS_URL = "https://ai.google.dev/gemini-api/docs/deprecations"

# Hard-blocked models — shut down or imminent shutdown
HARD_BLOCKED = {
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

# Known deprecated with shutdown dates
KNOWN_DEPRECATED = {
    "gemini-2.5-pro": "2026-10-16",
    "gemini-2.5-flash": "2026-10-16",
    "gemini-2.5-flash-lite": "2026-10-16",
    "gemini-2.0-flash": "2026-06-01",
    "gemini-2.0-flash-001": "2026-06-01",
    "gemini-2.0-flash-lite": "2026-06-01",
    "gemini-2.0-flash-lite-001": "2026-06-01",
    "gemini-embedding-001": "2026-07-14",
    "imagen-4.0-generate-001": "2026-06-24",
    "imagen-4.0-ultra-generate-001": "2026-06-24",
    "imagen-4.0-fast-generate-001": "2026-06-24",
    "gemini-robotics-er-1.5-preview": "2026-04-30",
}


def fetch_page(url: str) -> str:
    """Fetch a URL and return decoded text."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "adk-model-fetcher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode()


def parse_model_ids(html: str) -> set[str]:
    """Extract Gemini model identifiers from HTML."""
    pattern = r'(?:gemini|imagen|veo|lyria|embedding|text-embedding|computer-use|antigravity)[\w\-\.]+'
    seen: set[str] = set()
    for match in re.finditer(pattern, html, re.IGNORECASE):
        model_id = match.group(0).rstrip(".-")
        # Filter out false positives (URLs, paths, code identifiers)
        if len(model_id) > 5 and not model_id.endswith((".js", ".css", ".html")):
            seen.add(model_id)
    return seen


def classify_model(model_id: str) -> str:
    """Classify model by type."""
    if "live" in model_id or "native-audio" in model_id:
        return "live_audio"
    if "tts" in model_id:
        return "tts"
    if "embedding" in model_id or "text-embedding" in model_id:
        return "embedding"
    if model_id.startswith("imagen"):
        return "image_gen"
    if model_id.startswith("veo"):
        return "video_gen"
    if model_id.startswith("lyria"):
        return "music_gen"
    if "computer-use" in model_id:
        return "tool_agent"
    if "deep-research" in model_id:
        return "tool_agent"
    if "antigravity" in model_id:
        return "tool_agent"
    if "robotics" in model_id:
        return "tool_agent"
    if "pro" in model_id:
        return "llm_pro"
    if "flash-lite" in model_id or "flash_lite" in model_id:
        return "llm_flash_lite"
    if "flash" in model_id:
        return "llm_flash"
    return "llm_unknown"


def determine_status(model_id: str) -> str:
    """Determine model status."""
    if model_id in HARD_BLOCKED:
        return "blocked"
    if model_id in KNOWN_DEPRECATED:
        return "deprecated"
    if "preview" in model_id:
        return "preview"
    if "exp" in model_id and not model_id.startswith("gemini-embedding"):
        return "experimental"
    return "stable"


def build_cache(models_html: str, deprecations_html: str) -> dict:
    """Build the model cache from scraped HTML."""
    all_models = parse_model_ids(models_html)
    dep_models = parse_model_ids(deprecations_html)

    model_entries = []
    for model_id in sorted(all_models):
        status = determine_status(model_id)
        if model_id in dep_models and status == "stable":
            status = "deprecated"

        model_entries.append({
            "id": model_id,
            "type": classify_model(model_id),
            "status": status,
            "shutdown_date": KNOWN_DEPRECATED.get(model_id),
        })

    active = [m for m in model_entries if m["status"] not in ("deprecated", "blocked")]
    deprecated_list = [m for m in model_entries if m["status"] == "deprecated"]
    blocked_list = [m for m in model_entries if m["status"] == "blocked"]

    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources": [MODELS_URL, DEPRECATIONS_URL],
        "summary": {
            "total": len(model_entries),
            "active": len(active),
            "deprecated": len(deprecated_list),
            "blocked": len(blocked_list),
        },
        "models_by_type": {
            "llm_pro": [m for m in model_entries if m["type"] == "llm_pro"],
            "llm_flash": [m for m in model_entries if m["type"] == "llm_flash"],
            "llm_flash_lite": [m for m in model_entries if m["type"] == "llm_flash_lite"],
            "live_audio": [m for m in model_entries if m["type"] == "live_audio"],
            "tts": [m for m in model_entries if m["type"] == "tts"],
            "image_gen": [m for m in model_entries if m["type"] == "image_gen"],
            "video_gen": [m for m in model_entries if m["type"] == "video_gen"],
            "embedding": [m for m in model_entries if m["type"] == "embedding"],
            "music_gen": [m for m in model_entries if m["type"] == "music_gen"],
            "tool_agent": [m for m in model_entries if m["type"] == "tool_agent"],
        },
        "deprecated_models": deprecated_list,
        "blocked_models": blocked_list,
    }


def check_for_changes(new_cache: dict, old_path: Path) -> Optional[list[str]]:
    """Compare new cache with existing. Return list of changes."""
    if not old_path.exists():
        return ["No existing cache — first run"]

    old = json.loads(old_path.read_text())
    changes = []

    old_deprecated = {m["id"] for m in old.get("deprecated_models", [])}
    new_deprecated = {m["id"] for m in new_cache.get("deprecated_models", [])}
    new_deps = new_deprecated - old_deprecated

    old_active = {m["id"] for m in old.get("models_by_type", {}).get("llm_flash", []) +
                  old.get("models_by_type", {}).get("llm_pro", [])}
    new_ids = {m["id"] for m in new_cache["models_by_type"]["llm_flash"] +
               new_cache["models_by_type"]["llm_pro"]}
    new_models = new_ids - old_active

    if new_deps:
        changes.append(f"NEW DEPRECATIONS: {', '.join(sorted(new_deps))}")
    if new_models:
        changes.append(f"NEW MODELS: {', '.join(sorted(new_models))}")

    return changes if changes else None


def main():
    parser = argparse.ArgumentParser(
        description="Fetch latest Gemini models from Google AI docs",
    )
    parser.add_argument("--output", default=None,
                        help="Output file path (default: references/model-cache.json)")
    parser.add_argument("--check-only", action="store_true",
                        help="Only check for changes, don't write output")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else (
        Path(__file__).resolve().parent.parent / "references" / "model-cache.json"
    )

    print("Fetching Gemini models from Google AI docs...")

    try:
        models_html = fetch_page(MODELS_URL)
        deprecations_html = fetch_page(DEPRECATIONS_URL)
    except Exception as e:
        print(f"Error fetching docs: {e}", file=sys.stderr)
        print("Using fallback: hardcoded model data", file=sys.stderr)
        models_html = ""
        deprecations_html = ""

    cache = build_cache(models_html, deprecations_html)

    if args.check_only:
        changes = check_for_changes(cache, output_path)
        if changes:
            print("\n".join(changes))
            sys.exit(1)  # Signal that updates are needed
        print("No changes detected")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cache, indent=2))
    print(f"Saved model cache to {output_path}")
    print(f"  Total: {cache['summary']['total']}")
    print(f"  Active: {cache['summary']['active']}")
    print(f"  Deprecated: {cache['summary']['deprecated']}")
    print(f"  Blocked: {cache['summary']['blocked']}")

    # Print by type
    for type_name, models in cache["models_by_type"].items():
        if models:
            active_count = sum(1 for m in models if m["status"] in ("stable", "preview"))
            print(f"  {type_name}: {len(models)} models ({active_count} usable)")


if __name__ == "__main__":
    main()
