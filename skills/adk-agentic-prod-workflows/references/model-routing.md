# Model Routing & Selection for ADK Workflows

## Anti-Pattern: Hardcoded Deprecated Models

**CRITICAL: Never use these models.** They have announced shutdown dates and will break your workflow.

### Blocked Models (DO NOT USE)

```
gemini-2.0-flash              → shutdown June 1, 2026
gemini-2.0-flash-001          → shutdown June 1, 2026
gemini-2.0-flash-lite         → shutdown June 1, 2026
gemini-2.0-flash-lite-001     → shutdown June 1, 2026
gemini-3-pro-preview          → shut down March 9, 2026
text-embedding-004            → shut down Jan 14, 2026
embedding-001                 → shut down Oct 30, 2025
imagen-3.0-generate-002       → shut down Nov 10, 2025
veo-2.0-generate-001          → shutdown coming soon
gemini-2.5-pro-preview-*      → shut down Dec 2, 2025
gemini-2.5-flash-preview-*    → shut down Nov 2025–Feb 2026
gemini-robotics-er-1.5-preview → shut down April 30, 2026
```

Always check: https://ai.google.dev/gemini-api/docs/models and https://ai.google.dev/gemini-api/docs/deprecations

## Model Catalog (Stable + Preview — May 2026)

### LLM Models — Text Generation & Reasoning

| Model | Tier | Best For | Status |
|-------|------|----------|--------|
| `gemini-3.5-flash` | Flash (high-end) | Agentic tasks, coding, sustained frontier performance | Stable |
| `gemini-3.1-pro-preview` | Pro | Complex reasoning, advanced problem-solving, vibe coding | Preview |
| `gemini-3.1-flash-lite` | Flash-Lite | Budget-friendly, high-volume, rivaling larger models | Stable |
| `gemini-2.5-pro` | Pro (previous gen) | Advanced reasoning, deep coding — **shutdown Oct 16, 2026** | Stable (migrating) |
| `gemini-2.5-flash` | Flash (previous gen) | Low-latency, high-volume, reasoning tasks — **shutdown Oct 16, 2026** | Stable (migrating) |
| `gemini-2.5-flash-lite` | Flash-Lite (prev) | Fastest budget model — **shutdown Oct 16, 2026** | Stable (migrating) |

### Complexity-Based Prompt Routing

Route tasks to the right model based on complexity. Saves cost, improves latency.

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class Complexity(str, Enum):
    LOW = "low"        # Simple classification, keyword extraction, yes/no
    MEDIUM = "medium"  # Summarization, Q&A, data extraction, translation
    HIGH = "high"      # Multi-step reasoning, code generation, planning

@dataclass
class ModelRoute:
    complexity: Complexity
    default_model: str
    fallback_model: str
    max_tokens: int
    temperature: float

MODEL_ROUTES: dict[Complexity, ModelRoute] = {
    Complexity.LOW: ModelRoute(
        complexity=Complexity.LOW,
        default_model="gemini-2.5-flash-lite",
        fallback_model="gemini-2.5-flash",
        max_tokens=1024,
        temperature=0.1,
    ),
    Complexity.MEDIUM: ModelRoute(
        complexity=Complexity.MEDIUM,
        default_model="gemini-2.5-flash",
        fallback_model="gemini-2.5-pro",
        max_tokens=4096,
        temperature=0.3,
    ),
    Complexity.HIGH: ModelRoute(
        complexity=Complexity.HIGH,
        default_model="gemini-2.5-pro",
        fallback_model="gemini-3.5-flash",
        max_tokens=8192,
        temperature=0.5,
    ),
}

def classify_complexity(query: str, tools_count: int = 0) -> Complexity:
    """Heuristic complexity classifier. Use LLM classifier for production."""
    query_len = len(query)
    if tools_count > 5 or query_len > 2000:
        return Complexity.HIGH
    if tools_count > 2 or query_len > 500:
        return Complexity.MEDIUM
    return Complexity.LOW

def get_model_for_task(query: str, tools_count: int = 0) -> str:
    """Route to the right model based on task complexity."""
    complexity = classify_complexity(query, tools_count)
    route = MODEL_ROUTES[complexity]
    return route.default_model

# Usage in agent creation
agent = Agent(
    name="adaptive_agent",
    model=get_model_for_task(user_query, len(tools)),
    instruction="...",
    tools=tools,
)
```

**LLM-as-classifier routing (production):**

```python
classifier = Agent(
    name="complexity_classifier",
    model="gemini-2.5-flash-lite",  # Cheap model for classification
    instruction="""Classify the following task into LOW, MEDIUM, or HIGH complexity.
    LOW: simple classification, greeting, single tool call, yes/no
    MEDIUM: Q&A, summarization, data extraction, 2-4 tool calls
    HIGH: multi-step reasoning, code generation, planning, 5+ tool calls
    Return only the word: LOW, MEDIUM, or HIGH.""",
)

def route_by_llm(query: str) -> str:
    result = classifier.run(query=query)
    complexity = Complexity(result.text.strip().upper())
    return MODEL_ROUTES[complexity].default_model
```

### Live / Audio Models — Real-time Bidirectional Streaming

| Model | Type | Best For | Status |
|-------|------|----------|--------|
| `gemini-3.1-flash-live-preview` | Live Audio | Real-time dialogue, voice-first AI, sub-second latency | Preview |
| `gemini-2.5-flash-native-audio-preview-12-2025` | Live Audio | Conversational agents with native audio streaming | Preview |

```python
from google.adk import Agent
from google.adk.agents import LiveRequestQueue
from google.adk.run_config import RunConfig, StreamingMode

live_agent = Agent(
    name="voice_assistant",
    model="gemini-3.1-flash-live-preview",
    instruction="Respond conversationally. Keep answers brief.",
    tools=[weather_tool, search_tool],
)

queue = LiveRequestQueue()
runner.run_async(
    agent=live_agent,
    live_request_queue=queue,
    run_config=RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO", "TEXT"],
    ),
)
```

### TTS Models — Text-to-Speech

| Model | Type | Best For | Status |
|-------|------|----------|--------|
| `gemini-3.1-flash-tts-preview` | TTS | Low-latency speech generation | Preview |
| `gemini-2.5-pro-preview-tts` | TTS (high quality) | Podcasts, audiobooks, structured workflows | Preview |
| `gemini-2.5-flash-preview-tts` | TTS (fast) | Controllable style and pacing — migrating to 3.1 | Preview |

### Image Generation Models

| Model | Type | Best For | Status |
|-------|------|----------|--------|
| `gemini-2.5-flash-image` (Nano Banana) | Native multimodal | Fast creative image gen/editing | Stable |
| `gemini-3.1-flash-image-preview` (Nano Banana 2) | Native multimodal | High-efficiency, high-volume image gen | Preview |
| `gemini-3-pro-image-preview` (Nano Banana Pro) | Native multimodal | State-of-art contextual image creation | Preview |
| `imagen-4.0-generate-001` | Text-to-image | High quality up to 2K — **shutdown June 24, 2026** | Stable (migrating) |

```python
# Image generation via agent instruction
image_agent = Agent(
    name="image_creator",
    model="gemini-2.5-flash-image",
    instruction="Generate images based on user descriptions. "
                "Describe what you want in detail for best results.",
)
```

### Video Generation Models

| Model | Type | Best For | Status |
|-------|------|----------|--------|
| `veo-3.1-generate-preview` (Veo 3.1) | Video gen | Cinematic video with synced audio | Preview |
| `veo-3.1-lite-generate-preview` (Veo 3.1 Lite) | Video gen | Developer-first, low-cost video gen | Preview |

### Embedding Models — Memory & Retrieval

| Model | Type | Best For | Status |
|-------|------|----------|--------|
| `gemini-embedding-2` | Multimodal embedding | Text, images, video, audio, PDF → unified embeddings | Stable |
| `gemini-embedding-001` | Text embedding | Semantic search, RAG, classification — **shutdown July 14, 2026** | Stable (migrating) |

```python
# Embedding usage for RAG
from google import genai

client = genai.Client()
result = client.models.embed_content(
    model="gemini-embedding-2",
    contents=["What is the capital of France?"],
)
embedding_vector = result.embeddings[0].values
```

### Music Generation Models

| Model | Type | Best For | Status |
|-------|------|----------|--------|
| `lyria-3-pro-preview` | Music gen | Full-length songs, complex structure | Preview |
| `lyria-3-clip-preview` | Music gen | Short clips, loops, previews (≤30s) | Preview |
| `lyria-realtime-exp` | Music gen (experimental) | Real-time streaming, granular control | Experimental |

### Tool & Agent Models

| Model | Type | Best For | Status |
|-------|------|----------|--------|
| `computer-use-preview` | Agent (screen) | UI automation — click, type, navigate | Preview |
| `gemini-deep-research-preview` | Agent (research) | Multi-step research across 100s of sources | Preview |
| `gemini-deep-research-max-preview` | Agent (research) | Maximum comprehensiveness | Preview |
| `antigravity-agent-preview` | Agent (sandbox) | Code execution, file management, web browsing in sandbox | Preview |
| `gemini-robotics-er-1.6-preview` | Agent (robotics) | Physical space understanding, multi-step task planning | Preview |

## Auto-Fetch: Keep Models Updated

Hardcoded model lists go stale. Implement auto-fetch from Google AI docs.

### Fetch Script

```python
#!/usr/bin/env python3
"""scripts/fetch_models.py — Fetch latest Gemini models from Google AI docs.
Run weekly via cron or CI to keep model lists current.
"""

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MODELS_URL = "https://ai.google.dev/gemini-api/docs/models"
DEPRECATIONS_URL = "https://ai.google.dev/gemini-api/docs/deprecations"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "references" / "model-cache.json"

def fetch_page(url: str) -> str:
    with urllib.request.urlopen(url) as resp:
        return resp.read().decode()

def parse_models(html: str) -> list[dict]:
    """Extract model names from page. Basic regex — use bs4 for production."""
    models = []
    # Match model identifiers like gemini-2.5-flash, veo-3.1-generate-preview
    model_pattern = r'(gemini|imagen|veo|lyria|embedding|text-embedding|computer-use|antigravity)[\w\-\.]+'
    seen = set()
    for match in re.finditer(model_pattern, html, re.IGNORECASE):
        model_id = match.group(0)
        if model_id not in seen:
            seen.add(model_id)
            models.append({"id": model_id, "last_seen": datetime.now(timezone.utc).isoformat()})
    return models

def parse_deprecations(html: str) -> list[dict]:
    """Extract deprecated model names."""
    deprecated = []
    # Match pattern: model name followed by shutdown date
    dep_pattern = r'(gemini|imagen|veo|lyria|embedding|text-embedding)[\w\-\.]+.*?(?:shutdown|deprecated|retired)'
    seen = set()
    for match in re.finditer(dep_pattern, html, re.IGNORECASE):
        model_id = match.group(0).split()[0]  # Take just the model ID
        if model_id not in seen:
            seen.add(model_id)
            deprecated.append({"id": model_id, "status": "deprecated"})
    return deprecated

def main():
    print("Fetching latest Gemini models...")
    models_html = fetch_page(MODELS_URL)
    deprecations_html = fetch_page(DEPRECATIONS_URL)

    models = parse_models(models_html)
    deprecated = {d["id"] for d in parse_deprecations(deprecations_html)}

    cache = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources": [MODELS_URL, DEPRECATIONS_URL],
        "models": models,
        "deprecated_models": sorted(deprecated),
        "active_models": [m for m in models if m["id"] not in deprecated],
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(cache, indent=2))
    print(f"Saved {len(models)} models to {OUTPUT_FILE}")
    print(f"  Active: {len(cache['active_models'])}")
    print(f"  Deprecated: {len(deprecated)}")

if __name__ == "__main__":
    main()
```

### CI Integration

```yaml
# GitHub Actions: weekly model refresh
name: Refresh Model Catalog
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9am
  workflow_dispatch:

jobs:
  refresh-models:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Fetch latest models
        run: python scripts/fetch_models.py
      - name: Create PR if changes
        uses: peter-evans/create-pull-request@v7
        with:
          title: 'chore: update model catalog from Google AI docs'
          branch: auto/update-model-catalog
          commit-message: 'chore: refresh model catalog'
          body: 'Automated model list refresh from ai.google.dev'
```

### Runtime Model Validation

```python
"""Validate model name at agent creation time."""
import json
from pathlib import Path

_MODEL_CACHE: dict | None = None

def _load_cache() -> dict:
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        cache_file = Path(__file__).parent / "model-cache.json"
        if cache_file.exists():
            _MODEL_CACHE = json.loads(cache_file.read_text())
        else:
            _MODEL_CACHE = {"deprecated_models": [], "active_models": []}
    return _MODEL_CACHE

def validate_model(model: str) -> None:
    """Warn if model is deprecated. Raise if hard-blocked."""
    cache = _load_cache()
    deprecated = set(cache.get("deprecated_models", []))

    # Hard-block list (models with imminent shutdown)
    HARD_BLOCK = {
        "gemini-2.0-flash", "gemini-2.0-flash-001",
        "gemini-2.0-flash-lite", "gemini-2.0-flash-lite-001",
        "gemini-3-pro-preview",
        "text-embedding-004", "embedding-001",
        "imagen-3.0-generate-002",
    }

    if model in HARD_BLOCK:
        raise ValueError(
            f"Model '{model}' is BLOCKED (shut down or imminent shutdown). "
            f"See https://ai.google.dev/gemini-api/docs/deprecations"
        )

    if model in deprecated:
        import warnings
        warnings.warn(
            f"Model '{model}' is deprecated. Check for replacement at "
            f"https://ai.google.dev/gemini-api/docs/deprecations",
            DeprecationWarning,
            stacklevel=2,
        )

# Usage at agent creation
validate_model("gemini-2.5-flash")     # Warns (shutdown Oct 2026)
validate_model("gemini-2.0-flash")     # Raises ValueError
```

## Model-to-Task Mapping

| Task Type | Primary Model | Fallback | Why |
|-----------|--------------|----------|-----|
| Greeting / simple Q&A | `gemini-2.5-flash-lite` | `gemini-2.5-flash` | Cheapest, fastest |
| Classification / routing | `gemini-2.5-flash-lite` | `gemini-2.5-flash` | Low complexity |
| Summarization | `gemini-2.5-flash` | `gemini-2.5-pro` | Medium complexity |
| Q&A with context | `gemini-2.5-flash` | `gemini-2.5-pro` | Medium complexity |
| Data extraction | `gemini-2.5-flash` | `gemini-2.5-pro` | Medium complexity |
| Multi-step reasoning | `gemini-2.5-pro` | `gemini-3.5-flash` | High complexity |
| Code generation (simple) | `gemini-2.5-flash` | `gemini-2.5-pro` | Medium complexity |
| Code generation (complex) | `gemini-2.5-pro` | `gemini-3.5-flash` | High complexity |
| Planning / orchestration | `gemini-2.5-pro` | `gemini-3.1-pro-preview` | Highest reasoning |
| Real-time voice | `gemini-3.1-flash-live-preview` | `gemini-2.5-flash-native-audio-preview-12-2025` | Live audio |
| TTS / speech generation | `gemini-3.1-flash-tts-preview` | `gemini-2.5-flash-preview-tts` | TTS |
| Image generation | `gemini-2.5-flash-image` | `gemini-3-pro-image-preview` | Native multimodal |
| Video generation | `veo-3.1-generate-preview` | `veo-3.1-lite-generate-preview` | Video |
| Embeddings / RAG | `gemini-embedding-2` | `gemini-embedding-001` | Multimodal emb |
| Music generation | `lyria-3-pro-preview` | `lyria-3-clip-preview` | Music |
| Agent / tool use (simple) | `gemini-2.5-flash` | `gemini-2.5-flash-lite` | Flash balances speed+reasoning |
| Agent / tool use (complex) | `gemini-3.5-flash` | `gemini-2.5-pro` | Frontier agentic perf |
| Deep research | `gemini-deep-research-preview` | `gemini-2.5-pro` | Multi-source analysis |
| Screen automation | `computer-use-preview` | — | UI agent |
| Robotics | `gemini-robotics-er-1.6-preview` | — | Embodied reasoning |

## Model Selection in Agent Definitions

```python
from google.adk import Agent

# SIMPLE agent — flash-lite for speed/cost
greeter = Agent(
    name="greeter",
    model="gemini-2.5-flash-lite",
    instruction="Greet users warmly.",
)

# STANDARD agent — flash for general tasks
support = Agent(
    name="support_agent",
    model="gemini-2.5-flash",
    instruction="Handle customer inquiries with tools.",
    tools=[lookup_order, check_status],
)

# COMPLEX agent — pro for reasoning/planning
planner = Agent(
    name="planner",
    model="gemini-2.5-pro",
    instruction="Plan multi-step tasks and delegate to sub-agents.",
    sub_agents=[researcher, coder, reviewer],
)

# LIVE agent — live model for real-time audio
voice_agent = Agent(
    name="voice_assistant",
    model="gemini-3.1-flash-live-preview",
    instruction="Respond conversationally. Keep answers under 30 seconds.",
)
```

## Version Stability Strategy

```
ALWAYS use specific stable versions:
  ✅ gemini-2.5-flash
  ✅ gemini-2.5-pro
  
PREFER latest alias with auto-update pipeline:
  ⚠️ gemini-flash-latest  (auto-swaps — have monitoring)
  
AVOID preview models in production without migration plan:
  ⚠️ gemini-3.1-pro-preview  (2-week deprecation notice)
  
NEVER use experimental models in production:
  ❌ lyria-realtime-exp
```

**Migration strategy:**
1. Pin specific stable versions in production config
2. Run CI job weekly to fetch latest model list (see above)
3. When a deprecation is announced, migrate to replacement in staging first
4. Set `GOOGLE_API_KEY` and model name via environment variables (not hardcoded)
5. Monitor shutdown dates — set calendar reminders 2 weeks before

## Environment Configuration

```bash
# .env — model configuration
# LLM Models (complexity-based routing)
MODEL_LOW_COMPLEXITY=gemini-2.5-flash-lite
MODEL_MEDIUM_COMPLEXITY=gemini-2.5-flash
MODEL_HIGH_COMPLEXITY=gemini-2.5-pro

# Specialized Models
MODEL_LIVE_AUDIO=gemini-3.1-flash-live-preview
MODEL_TTS=gemini-3.1-flash-tts-preview
MODEL_IMAGE_GEN=gemini-2.5-flash-image
MODEL_VIDEO_GEN=veo-3.1-generate-preview
MODEL_EMBEDDING=gemini-embedding-2
MODEL_MUSIC=lyria-3-pro-preview

# Tool/Agent Models
MODEL_COMPUTER_USE=computer-use-preview
MODEL_DEEP_RESEARCH=gemini-deep-research-preview
```
