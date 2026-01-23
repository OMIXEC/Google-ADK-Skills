"""
CLI interface for the ADK Bidi orchestrator.

Provides a command-line interface for running the unified orchestrator
in various modes with different configurations.

Usage:
    python -m adk_bidi                              # Interactive text mode
    python -m adk_bidi --mode voice                 # Voice mode
    python -m adk_bidi --mode multimodal            # Multimodal mode
    python -m adk_bidi --config root_agent.yaml     # With configuration
    python -m adk_bidi serve --port 8000            # WebSocket server
    python -m adk_bidi list agents                  # List components
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional, List

from adk_bidi.config import (
    OrchestratorConfig,
    OrchestratorMode,
    load_config,
    get_voice_preset,
    get_multimodal_preset,
    get_autonomous_preset,
    get_enterprise_preset,
)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="adk_bidi",
        description="ADK Multi-Agent Real-Time Platform",
        epilog="Documentation: https://github.com/OMIXEC/Claude-ADK-Skills",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command (default)
    run_parser = subparsers.add_parser(
        "run",
        help="Run interactive session (default command)",
    )
    _add_run_arguments(run_parser)

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start WebSocket server",
    )
    serve_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)",
    )
    serve_parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (YAML)",
    )

    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List available components",
    )
    list_parser.add_argument(
        "component",
        choices=["agents", "mcp-servers", "presets", "modes"],
        help="Component type to list",
    )

    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Configuration management",
    )
    config_subparsers = config_parser.add_subparsers(dest="config_command")

    generate_parser = config_subparsers.add_parser(
        "generate",
        help="Generate a configuration template",
    )
    generate_parser.add_argument(
        "--preset",
        choices=["voice", "multimodal", "autonomous", "enterprise", "minimal"],
        default="minimal",
        help="Preset to use for generation",
    )
    generate_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("root_agent.yaml"),
        help="Output file path",
    )

    validate_parser = config_subparsers.add_parser(
        "validate",
        help="Validate a configuration file",
    )
    validate_parser.add_argument(
        "file",
        type=Path,
        help="Configuration file to validate",
    )

    # Add run arguments to main parser for default behavior
    _add_run_arguments(parser)

    return parser


def _add_run_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments for run command."""
    parser.add_argument(
        "--mode",
        choices=["text", "voice", "multimodal", "autonomous"],
        default="text",
        help="Operating mode (default: text)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (YAML)",
    )
    parser.add_argument(
        "--preset",
        choices=["voice", "multimodal", "autonomous", "enterprise"],
        help="Use a preset configuration",
    )
    parser.add_argument(
        "--agents",
        nargs="+",
        help="Specialist agents to include",
    )
    parser.add_argument(
        "--mcp-servers",
        nargs="+",
        dest="mcp_servers",
        help="MCP servers to connect",
    )
    parser.add_argument(
        "--goal",
        type=str,
        help="Goal for autonomous mode",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Enable continuous live session",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Override the model to use",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )


def get_config(args: argparse.Namespace) -> OrchestratorConfig:
    """Build configuration from arguments."""
    # Start with config file if provided
    if hasattr(args, 'config') and args.config and args.config.exists():
        config = load_config(args.config)
    # Or use preset if provided
    elif hasattr(args, 'preset') and args.preset:
        if args.preset == "voice":
            config = get_voice_preset()
        elif args.preset == "multimodal":
            config = get_multimodal_preset()
        elif args.preset == "autonomous":
            goal = getattr(args, 'goal', None) or "Help users accomplish their tasks"
            config = get_autonomous_preset(goal)
        elif args.preset == "enterprise":
            config = get_enterprise_preset()
        else:
            config = OrchestratorConfig()
    else:
        config = OrchestratorConfig()

    # Apply CLI overrides
    if hasattr(args, 'mode') and args.mode:
        config.mode = OrchestratorMode(args.mode)

    if hasattr(args, 'model') and args.model:
        config.model = args.model

    if hasattr(args, 'goal') and args.goal:
        config.autonomous.goal = args.goal

    if hasattr(args, 'continuous') and args.continuous:
        config.continuous_session = True

    return config


async def run_interactive(config: OrchestratorConfig, verbose: bool = False) -> int:
    """Run interactive orchestrator session."""
    from adk_bidi.agent import UnifiedOrchestrator

    if verbose:
        print(f"Configuration:")
        print(f"  Mode: {config.mode.value}")
        print(f"  Model: {config.model}")
        print(f"  Agents: {len(config.agents)}")
        print(f"  MCP Servers: {len(config.mcp_servers)}")

    orchestrator = UnifiedOrchestrator(config)

    try:
        await orchestrator.initialize()
        await orchestrator.run_interactive()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    finally:
        await orchestrator.cleanup()

    return 0


async def run_server(host: str, port: int, config: OrchestratorConfig) -> int:
    """Run WebSocket server mode."""
    try:
        import uvicorn
        from adk_bidi.core.websocket_server import create_websocket_app
    except ImportError:
        print("Error: Server mode requires uvicorn and fastapi packages")
        print("Install with: pip install uvicorn fastapi")
        return 1

    app = create_websocket_app(config)

    print(f"\nStarting WebSocket server on {host}:{port}")
    print(f"Mode: {config.mode.value}")
    print(f"Agents: {len(config.agents)}")
    print(f"MCP Servers: {len(config.mcp_servers)}")
    print("\nPress Ctrl+C to stop.\n")

    server_config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(server_config)

    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\nServer stopped.")

    return 0


def list_components(component: str) -> int:
    """List available components."""
    if component == "agents":
        print("\nAvailable Agent Types:")
        print("=" * 40)
        print("- BidiAgent         Base bidirectional streaming agent")
        print("- VoiceAgent        Voice-optimized with native audio")
        print("- MultimodalAgent   Text, audio, image, and video")
        print("- AutonomousAgent   Self-reasoning with OODA loop")
        print("\nOrchestration:")
        print("- MultiAgentSupervisor  Manages multiple agents")
        print("- IntentRouter          Routes by intent")
        print("- AgentSwarm            Parallel execution")

    elif component == "mcp-servers":
        print("\nSupported MCP Servers:")
        print("=" * 40)
        print("- sqlite          Local SQLite database")
        print("- postgresql      PostgreSQL database")
        print("- pinecone        Vector search")
        print("- brave_search    Web search")
        print("- github          GitHub API")
        print("- gitlab          GitLab API")
        print("- notion          Notion API")
        print("- slack           Slack API")
        print("\nSee mcp_servers/CATALOG.md for configuration details.")

    elif component == "presets":
        print("\nConfiguration Presets:")
        print("=" * 40)
        print("- voice       Voice-only mode with native audio")
        print("- multimodal  Voice + vision capabilities")
        print("- autonomous  Self-reasoning with OODA loop")
        print("- enterprise  Multi-agent team configuration")
        print("\nUsage: python -m adk_bidi --preset voice")

    elif component == "modes":
        print("\nOperating Modes:")
        print("=" * 40)
        print("- text        Text-only interaction (default)")
        print("- voice       Native audio streaming")
        print("- multimodal  Voice + vision capabilities")
        print("- autonomous  Self-reasoning with goals")
        print("\nUsage: python -m adk_bidi --mode voice")

    return 0


def generate_config(preset: str, output: Path) -> int:
    """Generate a configuration template."""
    from adk_bidi.config import save_config

    if preset == "voice":
        config = get_voice_preset()
    elif preset == "multimodal":
        config = get_multimodal_preset()
    elif preset == "autonomous":
        config = get_autonomous_preset("Help users accomplish their tasks")
    elif preset == "enterprise":
        config = get_enterprise_preset()
    else:  # minimal
        config = OrchestratorConfig()

    save_config(config, output)
    print(f"Configuration template saved to: {output}")
    return 0


def validate_config(file: Path) -> int:
    """Validate a configuration file."""
    if not file.exists():
        print(f"Error: File not found: {file}")
        return 1

    try:
        config = load_config(file)
        issues = config.validate()

        if issues:
            print(f"Configuration warnings:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        else:
            print(f"Configuration is valid: {file}")
            print(f"  Mode: {config.mode.value}")
            print(f"  Agents: {len(config.agents)}")
            print(f"  MCP Servers: {len(config.mcp_servers)}")
            return 0

    except Exception as e:
        print(f"Error parsing configuration: {e}")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Handle subcommands
    if args.command == "serve":
        config = get_config(args)
        return asyncio.run(run_server(args.host, args.port, config))

    elif args.command == "list":
        return list_components(args.component)

    elif args.command == "config":
        if args.config_command == "generate":
            return generate_config(args.preset, args.output)
        elif args.config_command == "validate":
            return validate_config(args.file)
        else:
            parser.parse_args(["config", "--help"])
            return 1

    else:
        # Default: run interactive session
        config = get_config(args)
        verbose = getattr(args, 'verbose', False)
        return asyncio.run(run_interactive(config, verbose))


if __name__ == "__main__":
    sys.exit(main())
