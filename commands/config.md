---
name: adk:config
description: Manage plugin settings and environment variables
argument: action (get, set, list)
argument-hint: set PINECONE_API_KEY xxx
---

# Configure ADK Plugin

Manage environment variables and plugin settings.

## Usage

```bash
/adk:config list
/adk:config get GOOGLE_API_KEY
/adk:config set PINECONE_API_KEY your_key
```

Settings stored in `.claude/adk-skills.local.md`

## Environment Variables

- `GOOGLE_API_KEY` (required) - Gemini API key
- `PINECONE_API_KEY` (optional) - Vector search
- `DEFAULT_MODEL` (optional) - Default model
- See each skill for additional variables
