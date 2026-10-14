"""
ADK Bidi - Multi-Agent Real-Time Platform

Main entry point for running the standalone orchestrator.

Usage:
    python -m bidi_orchestrator                              # Interactive text mode
    python -m bidi_orchestrator --mode voice                 # Voice mode
    python -m bidi_orchestrator --mode multimodal            # Full multimodal
    python -m bidi_orchestrator --config root_agent.yaml     # With config file
    python -m bidi_orchestrator serve --port 8000            # WebSocket server mode
    python -m bidi_orchestrator list agents                  # List available components
    python -m bidi_orchestrator config generate --preset enterprise -o my_config.yaml

For more information:
    python -m bidi_orchestrator --help
"""

import sys
from bidi_orchestrator.cli import main

if __name__ == "__main__":
    sys.exit(main())
