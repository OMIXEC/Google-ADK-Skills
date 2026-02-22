---
name: adk:test
description: Run local test of an agent or agent code to verify behavior before deployment
argument: file-path (path to agent Python file to test)
argument-hint: agent.py
---

# Test ADK Agent

Run local tests on an agent to verify behavior, output format, and error handling.

## Usage

```bash
/adk:test agent.py
/adk:test --verbose agent.py
/adk:test --scenarios agent.py
```

## Process

1. Load agent from specified file
2. Run test prompts against agent
3. Display responses and metrics
4. Report any errors or issues
5. Show performance statistics

## Options

- `--verbose` - Show detailed output
- `--scenarios` - Run pre-defined test scenarios
- `--limit N` - Limit test iterations to N

## Results

Output includes:
- Test prompts and responses
- Response times
- Error messages (if any)
- Token usage
- Quality metrics

Use results to refine agent instructions and tools before deployment.
