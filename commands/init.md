---
name: adk:init
description: Initialize a new ADK project with directory structure, requirements, and optional agent template
argument: project-name (optional, default: my-adk-agent)
argument-hint: my-project
---

# Initialize ADK Project

Initialize a new project directory with ADK structure, requirements file, and optional starter template.

## Usage

```bash
/adk:init my-project
/adk:init --template fitness-coach
```

## Process

1. Create project directory structure
2. Create virtual environment
3. Install dependencies from requirements.txt
4. Set up .env file
5. Optionally add template agent code

## Next Steps

Test with `/adk:test agent.py` and deploy with adk-production-deployment skill.
