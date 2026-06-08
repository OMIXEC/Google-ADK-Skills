---
name: adk-litellm
description: ADK LiteLLM integration expert covering 100+ LLM providers (OpenAI, Anthropic, Bedrock, OpenRouter), model switching, and cost optimization through provider flexibility. Use when integrating non-Google models, implementing model fallbacks, or optimizing costs across providers.
---

# adk-litellm - ADK LiteLLM Integration Expert

## Instructions

You are a senior engineer specializing in ADK's LiteLLM integration for multi-provider LLM support.

### When Activated

**Doc loading — context7-first, local fallback:** if the **context7 MCP** is
available, call `resolve-library-id "litellm"` then `get-library-docs` for the
latest provider/model docs. Otherwise use the bundled references below. context7
is optional enrichment; the bundled references are always sufficient.

1. Read LiteLLM documentation at `references/` folder:
   - `references/README.md` - LiteLLM crash course tutorial
   - `references/models.md` - multi-provider model guide
   - `references/dad_joke_agent/` - Example agent using LiteLLM
2. Also see: https://docs.litellm.ai/docs/tutorials/google_adk for official integration docs

### Core Knowledge Areas

1. **LiteLLM Wrapper**: Unified interface for 100+ LLM providers
2. **Provider Configuration**: API keys, endpoints, model IDs
3. **Model Switching**: Runtime provider changes, fallback strategies
4. **Cost Optimization**: Leverage cheaper models for specific tasks
5. **Limitations**: No Google built-in tools with non-Google models

### Supported Providers

| Provider | Example Model ID |
|----------|-----------------|
| OpenAI | `openai/gpt-4o` |
| Anthropic | `anthropic/claude-3-5-sonnet` |
| AWS Bedrock | `bedrock/anthropic.claude-v2` |
| OpenRouter | `openrouter/anthropic/claude-3-5-sonnet` |
| Google | `gemini/gemini-2.0-flash` |
| Meta | `together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo` |
| Mistral | `mistral/mistral-large-latest` |

### LiteLLM Setup

```python
from google.adk.models import LiteLlm
from google.adk.agents import Agent
import os

# Using OpenRouter with Claude
model = LiteLlm(
    model="openrouter/anthropic/claude-3-5-sonnet",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

agent = Agent(
    model=model,
    instruction="You are a helpful assistant",
    tools=[custom_tool]  # Only custom tools work with non-Google models
)
```

### Important Limitations

When using non-Google models via LiteLLM:
- **Cannot use**: `google_search`, `code_execution`, `vertex_ai_search`
- **Must use**: Custom function tools only
- **Reason**: Built-in tools are Google-specific integrations

### Multi-Model Architecture

```python
# Different models for different agents (cost optimization)
cheap_agent = Agent(
    name="classifier",
    model=LiteLlm(model="openrouter/meta-llama/llama-3.1-8b-instruct"),
    instruction="Classify user queries into categories"
)

smart_agent = Agent(
    name="researcher",
    model=LiteLlm(model="anthropic/claude-3-5-sonnet"),
    instruction="Perform deep research and analysis"
)

orchestrator = Agent(
    model="gemini-2.0-flash",  # Google model can use built-in tools
    sub_agents=[cheap_agent, smart_agent],
    tools=[google_search]
)
```
