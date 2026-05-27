"""Project scaffolding tools — wrappers around the skill scripts.

These tools wrap scripts/init_adk_workflow.py, scripts/compose_workflow.py,
scripts/package_workflow.py, scripts/quick_validate.py, and
scripts/fetch_models.py as callable ADK FunctionTools.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

from google.adk.tools import FunctionTool

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"


def _run_script(script_name: str, *args: str) -> dict:
    """Run a script from the scripts/ directory and return structured output."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return {"success": False, "error": f"Script not found: {script_path}"}

    cmd = [sys.executable, str(script_path), *args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Script timed out after 120s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def init_adk_workflow(
    name: str,
    workflow_type: str = "graph",
    lang: str = "python",
    output_dir: Optional[str] = None,
    with_mcp: bool = False,
    with_memory: bool = False,
) -> dict:
    """Scaffold a new ADK workflow project.

    Args:
        name: Project name (kebab-case)
        workflow_type: graph, dynamic, collaborative, template-seq, template-parallel, template-loop
        lang: python, go, ts
        output_dir: Target directory (defaults to current dir)
        with_mcp: Include MCP server scaffolding
        with_memory: Include SessionService configuration
    """
    args = [
        "--type", workflow_type,
        "--lang", lang,
        "--name", name,
    ]
    if output_dir:
        args.extend(["--output", output_dir])
    if with_mcp:
        args.append("--with-mcp")
    if with_memory:
        args.append("--with-memory")
    return _run_script("init_adk_workflow.py", *args)


def compose_workflow(config_file: str, lang: str = "python") -> dict:
    """Generate workflow code from a YAML/JSON config file.

    Args:
        config_file: Path to YAML or JSON config defining agents and tools
        lang: Target language (python, go, ts, mcp)
    """
    return _run_script("compose_workflow.py", "--config", config_file, "--lang", lang)


def package_workflow(project_dir: str, target: str = "cloud-run") -> dict:
    """Package a workflow for deployment.

    Args:
        project_dir: Path to the workflow project
        target: Deployment target (cloud-run, agent-engine, gke, ecs, eks, lambda,
                container-apps, aks, docker)
    """
    return _run_script("package_workflow.py", "--dir", project_dir, "--target", target)


def quick_validate(target: str) -> dict:
    """Validate ADK workflow files for schema and convention compliance.

    Args:
        target: File path or project directory to validate
    """
    return _run_script("quick_validate.py", "--project", target)


def fetch_models(output_path: Optional[str] = None, check_only: bool = False) -> dict:
    """Fetch latest Gemini models from Google AI docs.

    Args:
        output_path: Custom output path for model-cache.json
        check_only: If True, exit 1 if new deprecations found (for CI)
    """
    args = []
    if output_path:
        args.extend(["--output", output_path])
    if check_only:
        args.append("--check-only")
    return _run_script("fetch_models.py", *args)


# Export as FunctionTools
init_adk_workflow_tool = FunctionTool(func=init_adk_workflow)
compose_workflow_tool = FunctionTool(func=compose_workflow)
package_workflow_tool = FunctionTool(func=package_workflow)
quick_validate_tool = FunctionTool(func=quick_validate)
fetch_models_tool = FunctionTool(func=fetch_models)

ALL_TOOLS = [
    init_adk_workflow_tool,
    compose_workflow_tool,
    package_workflow_tool,
    quick_validate_tool,
    fetch_models_tool,
]
