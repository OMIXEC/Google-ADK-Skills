#!/usr/bin/env python3
"""Quick validation of ADK workflow files for schema and convention compliance.

Validates:
- SKILL.md frontmatter correctness
- Python workflow files: imports, agent definitions, tool signatures
- YAML/JSON config files: required fields, types
- Project structure: required files and directories

Usage:
    python quick_validate.py --file app/workflow.py
    python quick_validate.py --file workflow.yaml
    python quick_validate.py --file SKILL.md
    python quick_validate.py --project .
    python quick_validate.py --project . --strict
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class ValidationResult:
    file_path: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def print(self) -> None:
        status = "PASS" if self.is_valid else "FAIL"
        print(f"  [{status}] {self.file_path}")
        for e in self.errors:
            print(f"    ERROR: {e}")
        for w in self.warnings:
            print(f"    WARN: {w}")


def validate_skill_md(path: Path) -> ValidationResult:
    result = ValidationResult(str(path))

    content = path.read_text()

    # Check YAML frontmatter
    if not content.startswith("---"):
        result.errors.append("Missing YAML frontmatter (must start with ---)")
        return result

    try:
        end_idx = content.index("---", 3)
        frontmatter = content[3:end_idx].strip()
        fm = yaml.safe_load(frontmatter) if yaml else {}
    except (ValueError, Exception):
        result.errors.append("Invalid YAML frontmatter")
        return result

    required_fields = ["name", "description"]
    for field in required_fields:
        if field not in fm:
            result.errors.append(f"Missing required field: '{field}'")
        elif not fm[field]:
            result.errors.append(f"Empty required field: '{field}'")

    if "name" in fm:
        name = fm["name"]
        if not re.match(r"^[a-z0-9][a-z0-9-]*$", name):
            result.warnings.append(f"Name '{name}' should be kebab-case (lowercase, hyphens)")

    # Check description length
    if "description" in fm:
        desc = fm["description"]
        if len(desc) < 50:
            result.warnings.append(f"Description is short ({len(desc)} chars). Aim for 100+ chars for good agent routing.")

    # Check body has content
    body = content[end_idx + 3:].strip()
    if len(body) < 100:
        result.warnings.append(f"Body is short ({len(body)} chars). Skills need substantive prompt content.")

    # Check references section exists
    if "references/" not in body:
        result.warnings.append("No references/ mentioned in body. Consider adding reference docs.")

    return result


def validate_python_workflow(path: Path) -> ValidationResult:
    result = ValidationResult(str(path))

    try:
        tree = ast.parse(path.read_text())
    except SyntaxError as e:
        result.errors.append(f"Python syntax error: {e}")
        return result

    imports = set()
    agent_defs = []
    tool_funcs = []
    has_entrypoint = False

    for node in ast.walk(tree):
        # Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

        # Check Agent() calls
        agent_types = {"Agent", "GraphAgent", "SequentialAgent", "ParallelAgent", "LoopAgent", "CustomAgent"}
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in agent_types:
                agent_defs.append(node)
            # Check for MCPToolset usage
            if isinstance(node.func, ast.Name) and node.func.id == "MCPToolset":
                result.warnings.append(f"MCPToolset found — verify connection_params and tool_filter are configured")

        # Check FunctionTool() calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "FunctionTool":
                tool_funcs.append(node)

        # Check for entrypoint
        if isinstance(node, ast.If) and hasattr(node, "test"):
            if ast.unparse(node.test) == "__name__ == '__main__'":
                has_entrypoint = True

    # Required imports
    if "google.adk" not in imports:
        result.errors.append("Missing 'google.adk' import")
    if "pydantic" not in imports and "pydantic" not in str(imports):
        result.warnings.append("Missing 'pydantic' import (recommended for tool schemas)")

    # Agent definitions
    if not agent_defs:
        result.errors.append("No Agent() definition found")
    else:
        # Check each agent has name and model
        for agent_node in agent_defs:
            has_name = has_model = has_instruction = False
            for kw in agent_node.keywords:
                if kw.arg == "name":
                    has_name = True
                elif kw.arg == "model":
                    has_model = True
                elif kw.arg == "instruction":
                    has_instruction = True
            if not has_name:
                result.warnings.append("Agent defined without explicit 'name'")
            if not has_model:
                result.warnings.append("Agent defined without explicit 'model'")
            if not has_instruction:
                result.warnings.append("Agent defined without explicit 'instruction'")

    # Tools
    if tool_funcs:
        for tool_node in tool_funcs:
            if tool_node.args:
                func_name = ast.unparse(tool_node.args[0]) if hasattr(ast, 'unparse') else str(tool_node.args[0])
                # Check that the function exists and has Pydantic params
                result.warnings.append(f"Tool '{func_name}': verify function has Pydantic params schema")

    # Entrypoint
    if not has_entrypoint:
        result.warnings.append("No if __name__ == '__main__' entrypoint found")

    return result


def validate_yaml_config(path: Path) -> ValidationResult:
    result = ValidationResult(str(path))

    if yaml is None:
        result.errors.append("PyYAML required. Install: pip install pyyaml")
        return result

    try:
        cfg = yaml.safe_load(path.read_text())
    except Exception as e:
        result.errors.append(f"YAML parse error: {e}")
        return result

    if not isinstance(cfg, dict):
        result.errors.append("Config must be a mapping (dict)")
        return result

    # Check for workflow config
    if "name" not in cfg and "agents" not in cfg:
        result.warnings.append("No 'name' or 'agents' key — is this a workflow config?")

    if "agents" in cfg:
        if not isinstance(cfg["agents"], list):
            result.errors.append("'agents' must be a list")
        else:
            for i, agent in enumerate(cfg["agents"]):
                if not isinstance(agent, dict):
                    result.errors.append(f"agents[{i}] must be a mapping")
                elif "name" not in agent:
                    result.errors.append(f"agents[{i}] missing 'name'")

    if "tools" in cfg:
        if not isinstance(cfg["tools"], list):
            result.errors.append("'tools' must be a list")
        else:
            for i, tool in enumerate(cfg["tools"]):
                if not isinstance(tool, dict):
                    result.errors.append(f"tools[{i}] must be a mapping")
                elif "name" not in tool:
                    result.errors.append(f"tools[{i}] missing 'name'")

    if "edges" in cfg:
        if not isinstance(cfg["edges"], list):
            result.errors.append("'edges' must be a list")
        else:
            for i, edge in enumerate(cfg["edges"]):
                if not isinstance(edge, dict):
                    result.errors.append(f"edges[{i}] must be a mapping")
                else:
                    for field in ["source", "target"]:
                        if field not in edge:
                            result.errors.append(f"edges[{i}] missing '{field}'")

    return result


def validate_project_structure(path: Path, strict: bool = False) -> list[ValidationResult]:
    results = []

    required_files = ["SKILL.md"]
    if strict:
        required_files.extend(["requirements.txt", ".env.example"])

    for rf in required_files:
        fp = path / rf
        if not fp.exists():
            results.append(ValidationResult(str(fp), errors=[f"Missing required file: {rf}"]))

    recommended_dirs = {
        "app/": "Workflow source directory",
        "tests/": "Test directory",
        "evals/": "Evaluation directory",
        "references/": "Reference documentation directory",
    }

    for d, desc in recommended_dirs.items():
        dp = path / d
        if not dp.exists():
            if strict:
                results.append(ValidationResult(str(dp), errors=[f"Missing {desc}: {d}"]))
            else:
                results.append(ValidationResult(str(dp), warnings=[f"Missing {desc}: {d}"]))

    # Validate python files in app/
    app_dir = path / "app"
    if app_dir.exists():
        for py_file in app_dir.glob("*.py"):
            results.append(validate_python_workflow(py_file))

    # Validate SKILL.md
    skill_md = path / "SKILL.md"
    if skill_md.exists():
        results.append(validate_skill_md(skill_md))

    return results


def validate_go_workflow(path: Path) -> ValidationResult:
    result = ValidationResult(str(path))

    content = path.read_text()

    # Check required imports
    if "google.golang.org/adk" not in content:
        result.errors.append("Missing 'google.golang.org/adk' import")
    if "log/slog" not in content and '"log"' not in content:
        result.warnings.append("No structured logging import (slog recommended)")

    # Check for agent patterns
    has_agent = False
    agent_patterns = [
        r"agent\.New\(agent\.Config",
        r"agent\.New\(",
        r"parallelagent\.New\(",
        r"sequentialagent\.New\(",
        r"loopagent\.New\(",
        r"graphagent\.New\(",
        r"a2aagent\.New\(",
        r"Agent\s+struct",
    ]
    for pattern in agent_patterns:
        if re.search(pattern, content):
            has_agent = True
            break

    if not has_agent:
        result.warnings.append("No ADK agent definition found (agent.New, Agent struct, etc.)")

    # Check for entrypoint
    if "func main()" not in content:
        result.warnings.append("No main() function found")

    # Check for context propagation
    if "context.Context" not in content:
        result.warnings.append("No context.Context usage — tracing and cancellation will be missing")

    # Check go.mod
    mod_file = path.parent / "go.mod"
    if mod_file.exists():
        mod_content = mod_file.read_text()
        if "google.golang.org/adk" not in mod_content:
            result.errors.append("go.mod missing google.golang.org/adk dependency")

    return result


def validate_ts_workflow(path: Path) -> ValidationResult:
    result = ValidationResult(str(path))

    content = path.read_text()

    # Check required imports
    if "@google/adk" not in content:
        result.errors.append("Missing '@google/adk' import")

    # Check for agent patterns
    if not re.search(r"new\s+(Agent|GraphAgent|ParallelAgent|SequentialAgent|LoopAgent)\s*\(", content):
        result.warnings.append("No ADK agent instantiation found (new Agent(...))")

    # Check for type safety
    if "zod" not in content.lower() and "z." not in content:
        result.warnings.append("No Zod schema found — consider using Zod for runtime type validation")

    # Check for entrypoint
    if "main()" not in content and "server.listen" not in content and "app.listen" not in content:
        result.warnings.append("No entrypoint found (main(), server.listen, etc.)")

    # Check for error handling
    if ".catch(" not in content and "try {" not in content:
        result.warnings.append("No error handling found (.catch(), try/catch)")

    # Check package.json
    pkg_file = path.parent / "package.json"
    if pkg_file.exists():
        import json as j
        pkg = j.loads(pkg_file.read_text())
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "@google/adk" not in deps:
            result.errors.append("package.json missing @google/adk dependency")
        if "typescript" not in deps:
            result.warnings.append("package.json missing typescript devDependency")

    return result


def validate_file(path: Path) -> ValidationResult:
    suffix = path.suffix.lower()

    if path.name == "SKILL.md" or suffix == ".md":
        return validate_skill_md(path)
    elif suffix == ".py":
        return validate_python_workflow(path)
    elif suffix == ".go":
        return validate_go_workflow(path)
    elif suffix in (".ts", ".tsx"):
        return validate_ts_workflow(path)
    elif suffix in (".yaml", ".yml"):
        return validate_yaml_config(path)
    elif suffix == ".json":
        try:
            data = json.loads(path.read_text())
            if "package" in path.name.lower():
                return validate_ts_workflow(path)  # package.json checked by ts validator
            return ValidationResult(str(path))
        except json.JSONDecodeError as e:
            return ValidationResult(str(path), errors=[f"JSON parse error: {e}"])
    else:
        return ValidationResult(str(path), warnings=[f"No validator for '{suffix}' files"])


def main():
    parser = argparse.ArgumentParser(
        description="Validate ADK workflow files and project structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", help="Validate a single file")
    parser.add_argument("--project", help="Validate an entire project directory")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors for project validation")

    args = parser.parse_args()

    if not args.file and not args.project:
        parser.print_help()
        sys.exit(1)

    all_results = []
    if args.file:
        all_results = [validate_file(Path(args.file))]
    elif args.project:
        all_results = validate_project_structure(Path(args.project), strict=args.strict)

    total = len(all_results)
    passed = sum(1 for r in all_results if r.is_valid)
    errors = sum(len(r.errors) for r in all_results)
    warnings = sum(len(r.warnings) for r in all_results)

    print(f"\nValidating: {args.file or args.project}\n")

    for r in all_results:
        r.print()

    print(f"\n───")
    print(f"Files: {total} | Passed: {passed} | Failed: {total - passed}")
    print(f"Issues: {errors} errors, {warnings} warnings")

    if total - passed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
