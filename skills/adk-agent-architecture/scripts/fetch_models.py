#!/usr/bin/env python3
"""Fetch the current Gemini model catalog from Google's docs.

Sources:
    https://ai.google.dev/gemini-api/docs/models
    https://ai.google.dev/gemini-api/docs/deprecations

The models page is card-based: each model is an
``<a class="gemini-card-centered">`` with an ``<h3 data-text>`` name and a
``<p class="status-subtext">`` status. The deprecations page is a set of
tables with one row per model: id, release date, shutdown date, replacement.

Usage:
    python fetch_models.py                     # write references/model-cache.json
    python fetch_models.py --output cache.json
    python fetch_models.py --check-only        # exit 1 if the catalog changed
    python fetch_models.py --check-only --json # machine-readable diff

Exit codes:
    0  success (or no changes under --check-only)
    1  changes detected under --check-only
    2  fetch or parse failure (the cache is not rewritten)
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODELS_URL = "https://ai.google.dev/gemini-api/docs/models"
DEPRECATIONS_URL = "https://ai.google.dev/gemini-api/docs/deprecations"

CARD_RE = re.compile(
    r'<a href="/gemini-api/docs/models/(?P<id>[^"]+)" class="gemini-card-centered">'
    r"(?P<body>.*?)</a>",
    re.DOTALL,
)
NAME_RE = re.compile(r'<h3[^>]*data-text="(?P<name>[^"]+)"', re.DOTALL)
STATUS_RE = re.compile(r'<p class="status-subtext">(?P<status>.*?)</p>', re.DOTALL)

TABLE_ROW_RE = re.compile(r"<tr>(?P<body>.*?)</tr>", re.DOTALL)
ENDPOINT_RE = re.compile(r"<pre[^>]*>(?P<endpoint>[^<]+)</pre>", re.DOTALL)
LINK_ID_RE = re.compile(r'href="/gemini-api/docs/models/(?P<slug>[^"]+)"')

DEP_ROW_RE = re.compile(
    r"<tr>\s*"
    r"<td><code[^>]*>(?P<id>[^<]+)</code></td>\s*"
    r"<td>(?P<release>.*?)</td>\s*"
    r"<td>(?P<shutdown>.*?)</td>\s*"
    r"<td>(?P<replacement>.*?)</td>\s*"
    r"</tr>",
    re.DOTALL,
)

TAG_RE = re.compile(r"<[^>]+>")
DATE_RE = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")

TYPE_ORDER = [
    "llm_pro",
    "llm_flash",
    "llm_flash_lite",
    "live_audio",
    "tts",
    "transcribe",
    "image_gen",
    "video_gen",
    "music_gen",
    "embedding",
    "tool_agent",
]


def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "adk-model-fetcher/2.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def _text(raw: str) -> str:
    return " ".join(html.unescape(TAG_RE.sub(" ", raw)).split())


def _parse_date(raw: str) -> str | None:
    match = DATE_RE.search(_text(raw))
    if not match:
        return None
    parsed = datetime.strptime(match.group(1), "%B %d, %Y").date()
    return parsed.isoformat()


def parse_cards(html: str) -> dict[str, dict[str, str]]:
    """Return id -> {name, status} for every model card on the models page."""
    cards: dict[str, dict[str, str]] = {}
    for match in CARD_RE.finditer(html):
        model_id = match.group("id")
        body = match.group("body")
        name = NAME_RE.search(body)
        status = STATUS_RE.search(body)
        cards[model_id] = {
            "name": _text(name.group("name")) if name else model_id,
            "status": _text(status.group("status")).lower() if status else "",
        }
    return cards


def parse_table_rows(html: str) -> tuple[dict[str, dict[str, str]], set[str]]:
    """Return (endpoint id -> {name, status}, page slugs seen in table links).

    The models page renders every non-text family (TTS, image, video, music,
    embeddings, agents) as a table row whose last cell holds one or more
    ``<pre>`` endpoint IDs. Some rows link to an overview page rather than a
    model page, so the link is used for the name only.
    """
    rows: dict[str, dict[str, str]] = {}
    slugs: set[str] = set()
    for match in TABLE_ROW_RE.finditer(html):
        body = match.group("body")
        endpoints = [e.strip() for e in ENDPOINT_RE.findall(body)]
        if not endpoints:
            continue
        link = LINK_ID_RE.search(body)
        if link:
            slugs.add(link.group("slug"))
        row_text = _text(body).lower()
        if "shut down" in row_text:
            status = "shut down"
        elif "preview" in row_text:
            status = "preview"
        else:
            status = "stable"
        name_match = re.search(r">([^<>]+)</a>", body)
        name = _text(name_match.group(1)) if name_match else ""
        for endpoint in endpoints:
            for model_id in endpoint.split():
                if re.match(r"^[a-z0-9][a-z0-9.\-]+$", model_id):
                    rows.setdefault(model_id, {"name": name or model_id, "status": status})
    return rows, slugs


def parse_deprecations(html: str) -> dict[str, dict[str, str | None]]:
    """Return id -> {release, shutdown, replacement} from the deprecation tables."""
    rows: dict[str, dict[str, str | None]] = {}
    for match in DEP_ROW_RE.finditer(html):
        model_id = _text(match.group("id"))
        if not model_id:
            continue
        rows[model_id] = {
            "release": _parse_date(match.group("release")),
            "shutdown": _parse_date(match.group("shutdown")),
            "shutdown_text": _text(match.group("shutdown")),
            "replacement": _text(match.group("replacement")) or None,
        }
    return rows


def classify(model_id: str) -> str:
    if model_id == "gemini-4-argon":
        return "llm_pro"
    if "transcribe" in model_id:
        return "transcribe"
    if "live" in model_id or "native-audio" in model_id:
        return "live_audio"
    if "tts" in model_id:
        return "tts"
    if "embedding" in model_id:
        return "embedding"
    if model_id.startswith(("imagen", "veo")):
        return "image_gen" if model_id.startswith("imagen") else "video_gen"
    if "nano-banana" in model_id or model_id.endswith(("-image", "-image-preview")):
        return "image_gen"
    if model_id.startswith("lyria"):
        return "music_gen"
    if model_id.startswith("gemini-omni"):
        return "video_gen"
    if any(k in model_id for k in ("computer-use", "deep-research", "antigravity", "robotics")):
        return "tool_agent"
    if "pro" in model_id:
        return "llm_pro"
    if "flash-lite" in model_id:
        return "llm_flash_lite"
    if "flash" in model_id:
        return "llm_flash"
    return "llm_unknown"


def status_for(
    model_id: str,
    card: dict[str, str] | None,
    dep: dict[str, Any] | None,
    today: str,
) -> tuple[str, str | None]:
    """Return (status, shutdown_date).

    Precedence: a shutdown date in the past wins, then a scheduled shutdown or
    an explicit redirect, then the card's own stable/preview label.
    """
    shutdown = dep.get("shutdown") if dep else None
    if shutdown and shutdown <= today:
        return "blocked", shutdown

    label = (card or {}).get("status", "")
    if "shut down" in label:
        return "blocked", shutdown

    if shutdown and shutdown > today:
        return "deprecated", shutdown

    # "N/A" shutdown plus a replacement means the endpoint redirects, not dies.
    if dep and dep.get("shutdown_text") == "N/A" and dep.get("replacement"):
        return "deprecated", None

    if "preview" in model_id or "preview" in label:
        return "preview", None
    if "experimental" in label or model_id.endswith("-exp") or model_id.endswith("-exp-03-07"):
        return "experimental", None

    # An announced release with no shutdown date, or a live card, is supported.
    if dep and dep.get("shutdown_text", "").startswith("No shutdown"):
        return "stable", None
    if card:
        return "stable", None
    if dep:
        return "deprecated", None
    return "unknown", None


def build_cache(
    cards: dict[str, dict[str, str]],
    deprecations: dict[str, dict[str, Any]],
    today: str,
) -> dict[str, Any]:
    entries = []
    for model_id in sorted(set(cards) | set(deprecations)):
        entry = deprecations.get(model_id)
        status, shutdown = status_for(model_id, cards.get(model_id), entry, today)
        entries.append(
            {
                "id": model_id,
                "name": (cards.get(model_id) or {}).get("name", model_id),
                "type": classify(model_id),
                "status": status,
                "release_date": (entry or {}).get("release"),
                "shutdown_date": shutdown,
                "replacement": (entry or {}).get("replacement"),
            }
        )

    active = [m for m in entries if m["status"] in ("stable", "preview", "experimental")]
    deprecated = [m for m in entries if m["status"] == "deprecated"]
    blocked = [m for m in entries if m["status"] == "blocked"]

    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources": [MODELS_URL, DEPRECATIONS_URL],
        "summary": {
            "total": len(entries),
            "active": len(active),
            "deprecated": len(deprecated),
            "blocked": len(blocked),
        },
        "models_by_type": {
            kind: [m for m in entries if m["type"] == kind] for kind in TYPE_ORDER
        },
        "active_models": active,
        "deprecated_models": deprecated,
        "blocked_models": blocked,
    }


def diff_cache(new: dict[str, Any], old_path: Path) -> list[str]:
    if not old_path.exists():
        return ["no existing cache — first run"]
    old = json.loads(old_path.read_text())

    def flat(cache: dict[str, Any]) -> dict[str, str]:
        found: dict[str, str] = {}
        for models in cache.get("models_by_type", {}).values():
            for model in models:
                found[model["id"]] = model["status"]
        return found

    before, after = flat(old), flat(new)
    changes = []
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(i for i in set(before) & set(after) if before[i] != after[i])

    if added:
        changes.append("NEW MODELS: " + ", ".join(added))
    if removed:
        changes.append("REMOVED MODELS: " + ", ".join(removed))
    if changed:
        details = ", ".join(f"{i} ({before[i]} -> {after[i]})" for i in changed)
        changes.append("STATUS CHANGES: " + details)
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the Gemini model catalog")
    parser.add_argument("--output", default=None, help="output path")
    parser.add_argument("--check-only", action="store_true", help="do not write; exit 1 on change")
    parser.add_argument("--json", action="store_true", help="JSON diff output")
    parser.add_argument("--today", default=None, help="override today's date (YYYY-MM-DD)")
    args = parser.parse_args()

    output_path = (
        Path(args.output)
        if args.output
        else Path(__file__).resolve().parent.parent / "references" / "model-cache.json"
    )
    today = args.today or datetime.now(timezone.utc).date().isoformat()

    try:
        models_html = fetch_page(MODELS_URL)
        deprecations_html = fetch_page(DEPRECATIONS_URL)
    except Exception as exc:  # noqa: BLE001 - network boundary
        print(f"error fetching docs: {exc}", file=sys.stderr)
        return 2

    cards = parse_cards(models_html)
    table_rows, slugs = parse_table_rows(models_html)
    # A card whose link is a doc slug, not an endpoint, is not a callable model.
    for model_id in [i for i in cards if i in slugs and i not in table_rows]:
        cards.pop(model_id)
    for model_id, row in table_rows.items():
        cards.setdefault(model_id, row)
    deprecations = parse_deprecations(deprecations_html)
    if not cards:
        print("error: no model cards parsed; the page structure changed", file=sys.stderr)
        return 2

    cache = build_cache(cards, deprecations, today)

    if args.check_only:
        changes = diff_cache(cache, output_path)
        if args.json:
            print(json.dumps({"changes": changes}, indent=2))
        elif changes:
            print("\n".join(changes))
        else:
            print("No changes detected")
        return 1 if changes else 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cache, indent=2) + "\n")
    print(f"Saved model cache to {output_path}")
    print(f"  total: {cache['summary']['total']}")
    print(f"  active: {cache['summary']['active']}")
    print(f"  deprecated: {cache['summary']['deprecated']}")
    print(f"  blocked: {cache['summary']['blocked']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
