"""
ADK Bidi - Multi-Agent Real-Time Platform

Main entry point for running the standalone orchestrator.

Usage:
    python -m adk_bidi                              # Interactive text mode
    python -m adk_bidi --mode voice                 # Voice mode
    python -m adk_bidi --mode multimodal            # Full multimodal
    python -m adk_bidi --config root_agent.yaml     # With config file
    python -m adk_bidi serve --port 8000            # WebSocket server mode
    python -m adk_bidi list agents                  # List available components
    python -m adk_bidi config generate --preset enterprise -o my_config.yaml

For more information:
    python -m adk_bidi --help
"""

import sys
from adk_bidi.cli import main

if __name__ == "__main__":
    sys.exit(main())
