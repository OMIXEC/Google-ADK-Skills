#!/usr/bin/env python3
"""Compose agents and tools into a complete workflow definition.

Reads a workflow composition file (YAML/JSON) and generates the full
workflow code, wiring agents, tools, edges, and conditions together.

Usage:
    python compose_workflow.py --config workflow.yaml --output app/workflow.py
    python compose_workflow.py --config workflow.json --lang go --output main.go

Config format (YAML):
```yaml
name: order_processing
type: graph
language: python

agents:
  - name: validator
    model: gemini-2.5-flash
    instruction: Validate incoming orders
    tools: [validate_order, check_inventory]

  - name: processor
    model: gemini-2.5-flash
    instruction: Process validated orders
    tools: [fulfill_order, send_confirmation]

tools:
  - name: validate_order
    description: Check order data for completeness
    side_effect: false
    params:
      order_id: {type: str, description: "Order identifier"}

  - name: fulfill_order
    description: Execute order fulfillment
    side_effect: true
    params:
      order_id: {type: str, description: "Order identifier"}
      action: {type: str, description: "Fulfillment action"}

edges:
  - source: validator
    target: processor
    condition: "state['is_valid'] == True"

  - source: validator
    target: error_handler
    condition: "state['is_valid'] == False"

entry_point: validator
```
"""

import argparse
import json
import re
import sys
from pathlib import Path
from textwrap import dedent, indent

try:
    import yaml
except ImportError:
    yaml = None

# Safe subset of expressions allowed in edge conditions.
# Condition expressions only access state dict keys, compare them to
# literals, and combine with boolean operators. No function calls,
# attribute access, imports, or string escapes that could enable injection.
_CONDITION_SAFE_RE = re.compile(
    r"^state\["
    r"'[a-zA-Z_][a-zA-Z0-9_]*'"
    r"\]"
    r"("
    r"\s*(==|!=|is|is not|and|or|not|in|not in|True|False|None|null|undefined)\s*"
    r"("
    r"state\['[a-zA-Z_][a-zA-Z0-9_]*'\]"  # another state access
    r"|True|False|None|null|undefined"      # boolean/null literals
    r"|'[^'\\\\]*'"                           # single-quoted string (no escapes)
    r'|"[^"\\\\]*"'                           # double-quoted string (no escapes)
    r"|[0-9]+\.?[0-9]*"                      # numeric literal
    r")"
    r")*$"
)

_IDENT_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _sanitize_identifier(name: str) -> str:
    """Validate that a node/agent name is a safe identifier.

    Rejects names containing anything other than alphanumeric + underscore,
    which prevents injection of quotes, newlines, or code.

    Raises ValueError if the name is not a valid identifier.
    """
    stripped = name.strip()
    if not stripped:
        raise ValueError("Node/agent name must not be empty")
    if not _IDENT_RE.match(stripped):
        raise ValueError(
            f"Invalid node/agent name '{stripped}'. "
            f"Must match pattern: a-z, A-Z, 0-9, underscore."
        )
    return stripped


_BLOCKED_PATTERNS = [
    "__", "import", "exec", "eval", "compile", "open", "subprocess",
    "os.", "sys.", "shutil", "pathlib", "globals", "locals", "getattr",
    "setattr", "delattr", "base64", "decode", "encode", "\\x", "\\u",
    "require(", "require (", "fetch(", "import(", "process.",
]


def _sanitize_condition(condition: str) -> str:
    """Validate and sanitize an edge condition expression.

    Rejects conditions containing dangerous patterns (imports, code execution,
    attribute traversal). Only allows safe state-dict access with comparison
    operators and boolean logic.

    Raises ValueError if condition is unsafe.
    """
    stripped = condition.strip()

    # Blocklist check — reject anything with dangerous patterns
    lower = stripped.lower()
    for pattern in _BLOCKED_PATTERNS:
        if pattern in lower:
            raise ValueError(
                f"Unsafe condition pattern '{pattern}' found. "
                f"Conditions may only access state['key'] with simple comparisons."
            )

    # Allowlist check — match against safe expression pattern
    if not _CONDITION_SAFE_RE.match(stripped):
        raise ValueError(
            f"Condition expression does not match safe pattern. "
            f"Only state['key'] access, comparison operators (==, !=, is, in), "
            f"and boolean logic (and, or, not) are allowed. "
            f"Got: {stripped[:80]}"
        )

    return stripped


def _sanitize_condition_bool(condition: str) -> str:
    """Return True if condition is safe, False otherwise (no exception)."""
    try:
        _sanitize_condition(condition)
        return True
    except ValueError:
        return False


def load_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"Error: Config file '{path}' not found")
        sys.exit(1)

    with open(p) as f:
        if p.suffix in (".yaml", ".yml"):
            if yaml is None:
                print("Error: PyYAML required for YAML configs. Install with: pip install pyyaml")
                sys.exit(1)
            return yaml.safe_load(f)
        elif p.suffix == ".json":
            return json.load(f)
        else:
            print(f"Error: Unsupported config format '{p.suffix}'. Use .yaml, .yml, or .json")
            sys.exit(1)


def generate_python_agent(name: str, cfg: dict) -> str:
    model = cfg.get("model", "gemini-2.5-flash")
    instruction = cfg.get("instruction", f"Agent: {name}")
    tools = cfg.get("tools", [])
    tool_refs = ", ".join(tools) if tools else ""

    return f"""agent_{name} = Agent(
    name="{name}",
    model="{model}",
    instruction="""{instruction}""",
    tools=[{tool_refs}],
)"""


def generate_python_tool(name: str, cfg: dict) -> str:
    description = cfg.get("description", f"Tool: {name}")
    params = cfg.get("params", {})
    side_effect = cfg.get("side_effect", False)

    param_fields = []
    param_args = []
    for pname, pinfo in params.items():
        ptype = pinfo.get("type", "str")
        pdesc = pinfo.get("description", "")
        default = pinfo.get("default")
        if default is not None:
            param_fields.append(f"    {pname}: {ptype} = Field(default={repr(default)}, description=\"{pdesc}\")")
        else:
            param_fields.append(f"    {pname}: {ptype} = Field(description=\"{pdesc}\")")
        param_args.append(f"params.{pname}")

    fields_str = "\n".join(param_fields) if param_fields else "    pass"

    return f"""class {name.title()}Params(BaseModel):
{fields_str}

def {name}(params: {name.title()}Params) -> dict:
    \"\"\"{description}\"\"\"
    logger.info("tool_call", tool="{name}", side_effect={side_effect})
    try:
        # TODO: Implement tool logic
        return {{"status": "ok"}}
    except Exception as e:
        logger.error("tool_error", tool="{name}", error=str(e))
        return {{"status": "error", "error": str(e)}}

{name}_tool = FunctionTool({name})"""


def generate_python_edges(edges: list) -> str:
    if not edges:
        return "    edges=[],"

    edge_strs = []
    for edge in edges:
        source = _sanitize_identifier(edge["source"])
        target = _sanitize_identifier(edge["target"])
        condition = edge.get("condition")
        if condition:
            condition = _sanitize_condition(condition)
            edge_strs.append(
                f"        Edge(source=\"{source}\", target=\"{target}\", "
                f"condition=Condition(lambda state: {condition})),"
            )
        else:
            edge_strs.append(f"        Edge(source=\"{source}\", target=\"{target}\"),")

    return "    edges=[\n" + "\n".join(edge_strs) + "\n    ],"


def generate_python(cfg: dict) -> str:
    name = cfg["name"]
    wf_type = cfg.get("type", "graph")

    sections = []

    # Imports
    sections.append("""from google.adk import Agent
from google.adk.agents.graph import GraphAgent, Node, Edge, Condition
from google.adk.tools import FunctionTool
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

""")

    # Tools
    tools_cfg = cfg.get("tools", [])
    tool_names = []
    if tools_cfg:
        for tool in tools_cfg:
            tname = tool.get("name", "unnamed_tool")
            tool_names.append(f"{tname}_tool")
            sections.append(generate_python_tool(tname, tool))
            sections.append("")
    else:
        sections.append("# No tools defined\n")

    sections.append("# ── Agents ──────────────────────────────────\n\n")

    # Agents
    agents_cfg = cfg.get("agents", [])
    agent_names = []
    for agent in agents_cfg:
        aname = agent.get("name", "unnamed_agent")
        agent_names.append(f"agent_{aname}")
        sections.append(generate_python_agent(aname, agent))
        sections.append("")

    # Nodes
    sections.append("# ── Workflow Graph ──────────────────────────\n\n")
    nodes = [f"        Node(id=\"{a['name']}\", agent=agent_{a['name']})," for a in agents_cfg]
    nodes_str = "    nodes=[\n" + "\n".join(nodes) + "\n    ],"

    edges_str = generate_python_edges(cfg.get("edges", []))
    entry = cfg.get("entry_point", agents_cfg[0]["name"] if agents_cfg else "entry")

    sections.append(f"""graph_agent = GraphAgent(
    name="{name}_graph",
{nodes_str}
{edges_str}
    entry_point="{entry}",
)

__all__ = ["graph_agent"] + {tool_names} + {agent_names}
""")

    # Entrypoint
    sections.append("""
if __name__ == "__main__":
    import asyncio
    from google.adk.runners import InProcessRunner

    async def main():
        runner = InProcessRunner(agent=graph_agent)
        result = await runner.run(query="Run the workflow")
        print(f"Result: {result}")

    asyncio.run(main())
""")

    return "\n".join(sections)


def generate_go_workflow(cfg: dict) -> str:
    name = cfg["name"]
    safe_name = name.replace("-", "_")
    wf_type = cfg.get("type", "graph")
    agents_cfg = cfg.get("agents", [])
    tools_cfg = cfg.get("tools", [])
    edges_cfg = cfg.get("edges", [])
    entry = cfg.get("entry_point", agents_cfg[0]["name"] if agents_cfg else "entry")

    lines = []
    lines.append(f"""// {name} — composed workflow
// Generated by adk-agentic-prod-workflows

package main

import (
    "context"
    "fmt"
    "log/slog"
    "os"
)

// ── Tool definitions ──────────────────────────────────────────────
""")

    if tools_cfg:
        for tool in tools_cfg:
            tname = tool.get("name", "unnamed")
            lines.append(f"""func {tname}(params map[string]any) (map[string]any, error) {{
    slog.Info("tool called", "tool", "{tname}")
    return map[string]any{{"status": "ok"}}, nil
}}
""")

    lines.append("// ── Agent definitions ─────────────────────────────────────────────\n")
    for agent in agents_cfg:
        aname = agent.get("name", "unnamed")
        model = agent.get("model", "gemini-2.5-flash")
        instruction = agent.get("instruction", f"Agent: {aname}")
        tools = agent.get("tools", [])
        tool_list = ", ".join(tools)

        lines.append(f"""type {safe_name}_{aname}Agent struct {{
    name string
}}

func New{safe_name}_{aname}Agent() *{safe_name}_{aname}Agent {{
    return &{safe_name}_{aname}Agent{{name: "{aname}"}}
}}

func (a *{safe_name}_{aname}Agent) Run(ctx context.Context, input string) (string, error) {{
    slog.Info("agent running", "agent", a.name, "model", "{model}")
    // Instruction: {instruction}
    // Tools: [{tool_list}]
    return fmt.Sprintf("[{aname}]: %s", input), nil
}}
""")

    lines.append(f"""// ── Workflow assembly ─────────────────────────────────────────────

type {safe_name}Workflow struct {{
    Nodes []struct {{
        ID    string
        Agent interface{{ Run(context.Context, string) (string, error) }}
    }}
    Edges      []struct{{ Source, Target string }}
    EntryPoint string
}}

func New{safe_name}Workflow() *{safe_name}Workflow {{
    wf := &{safe_name}Workflow{{
        EntryPoint: "{entry}",
    }}
""")
    for agent in agents_cfg:
        aname = agent.get("name", "unnamed")
        lines.append(f"""    wf.Nodes = append(wf.Nodes, struct {{
        ID    string
        Agent interface{{ Run(context.Context, string) (string, error) }}
    }}{{ID: "{aname}", Agent: New{safe_name}_{aname}Agent()}})
""")

    for edge in edges_cfg:
        src = _sanitize_identifier(edge["source"])
        tgt = _sanitize_identifier(edge["target"])
        lines.append(f"""    wf.Edges = append(wf.Edges, struct{{ Source, Target string }}{{Source: "{src}", Target: "{tgt}"}})
""")

    lines.append("""    return wf
}

func (w *""" + safe_name + """Workflow) Run(ctx context.Context, query string) error {
    slog.Info("workflow start", "correlation_id", fmt.Sprintf("wf_%p", w))
    currentNodeID := w.EntryPoint
    for currentNodeID != "" {
        var nodeAgent interface{ Run(context.Context, string) (string, error) }
        for _, n := range w.Nodes {
            if n.ID == currentNodeID {
                nodeAgent = n.Agent
                break
            }
        }
        if nodeAgent == nil {
            return fmt.Errorf("node not found: %s", currentNodeID)
        }
        result, err := nodeAgent.Run(ctx, query)
        if err != nil {
            return fmt.Errorf("node %s: %w", currentNodeID, err)
        }
        query = result
        currentNodeID = ""
        for _, e := range w.Edges {
            if e.Source == currentNodeID {
                currentNodeID = e.Target
                break
            }
        }
    }
    slog.Info("workflow complete")
    return nil
}

func main() {
    ctx := context.Background()
    wf := New""" + safe_name + """Workflow()
    if err := wf.Run(ctx, "Run the workflow"); err != nil {
        slog.Error("workflow failed", "error", err)
        os.Exit(1)
    }
    fmt.Println("Workflow completed successfully")
}
""")
    return "\n".join(lines)


def generate_ts_workflow(cfg: dict) -> str:
    name = cfg["name"]
    agents_cfg = cfg.get("agents", [])
    tools_cfg = cfg.get("tools", [])
    edges_cfg = cfg.get("edges", [])
    entry = cfg.get("entry_point", agents_cfg[0]["name"] if agents_cfg else "entry")

    lines = []
    lines.append(f"""// {name} — composed workflow
// Generated by adk-agentic-prod-workflows

import {{ Agent, GraphAgent, type Node, type Edge }} from '@google/adk';
import {{ FunctionTool }} from '@google/adk/tools';
import {{ z }} from 'zod';

// ── Tool definitions ──────────────────────────────────────────────
""")

    if tools_cfg:
        for tool in tools_cfg:
            tname = tool.get("name", "unnamed")
            tdesc = tool.get("description", f"Tool: {tname}")
            lines.append(f"""const {tname.title()}Input = z.object({{
  params: z.record(z.any()).describe('Tool parameters'),
}});

async function {tname}(params: z.infer<typeof {tname.title()}Input>) {{
  console.log('tool_call', {{ tool: '{tname}' }});
  return {{ status: 'ok' }};
}}

const {tname}Tool = new FunctionTool({tname}, {{ schema: {tname.title()}Input }});
""")

    lines.append("// ── Agent definitions ─────────────────────────────────────────────\n")
    agent_names = []
    for agent in agents_cfg:
        aname = agent.get("name", "unnamed")
        agent_names.append(f"agent_{aname}")
        model = agent.get("model", "gemini-2.5-flash")
        instruction = agent.get("instruction", f"Agent: {aname}")
        tools = agent.get("tools", [])
        tool_refs = ", ".join(f"{t}Tool" for t in tools) if tools else ""

        lines.append(f"""const agent_{aname} = new Agent({{
  name: '{aname}',
  model: '{model}',
  instruction: `{instruction}`,
  tools: [{tool_refs}],
}});
""")

    lines.append("// ── Workflow Graph ─────────────────────────────────────────────\n")
    nodes = [f"  {{ id: '{a['name']}', agent: agent_{a['name']} }}," for a in agents_cfg]
    lines.append("const nodes: Node[] = [\n" + "\n".join(nodes) + "\n];\n")

    edge_strs = []
    for edge in edges_cfg:
        src = _sanitize_identifier(edge["source"])
        tgt = _sanitize_identifier(edge["target"])
        condition = edge.get("condition")
        if condition:
            condition = _sanitize_condition(condition)
            edge_strs.append(f"  {{ source: '{src}', target: '{tgt}', condition: (state) => {condition} }},")
        else:
            edge_strs.append(f"  {{ source: '{src}', target: '{tgt}' }},")
    lines.append("const edges: Edge[] = [\n" + "\n".join(edge_strs) + "\n];\n" if edge_strs else "const edges: Edge[] = [];\n")

    lines.append(f"""const workflow = new GraphAgent({{
  name: '{name}_graph',
  nodes,
  edges,
  entryPoint: '{entry}',
}});

async function main() {{
  const result = await workflow.run({{ query: 'Run the workflow' }});
  console.log('Result:', result);
}}

main().catch(console.error);
""")
    return "\n".join(lines)


def generate_mcp_agent_config(cfg: dict) -> str:
    """Generate MCP agent configuration from YAML/JSON config."""
    name = cfg["name"]
    mcp_config = cfg.get("mcp", {})
    servers = mcp_config.get("servers", [])

    lines = []
    lines.append("""# MCP Agent Configuration
# Generated by compose_workflow.py with MCP support

from google.adk import Agent
from google.adk.tools import MCPToolset
from google.adk.tools.mcp import StdioServerParameters, SseServerParams

""")

    mcp_tool_vars = []
    for i, server in enumerate(servers):
        var_name = f"mcp_tools_{i}"
        mcp_tool_vars.append(var_name)
        transport = server.get("transport", "stdio")
        server_name = server.get("name", f"mcp_server_{i}")

        if transport == "stdio":
            command = server.get("command", "python3")
            args = server.get("args", [f"mcp_servers/{server_name}.py"])
            env = server.get("env", {})
            env_str = ", ".join(f'"{k}": "{v}"' for k, v in env.items()) if env else ""

            lines.append(f"""# MCP Server: {server_name} (stdio transport)
{var_name} = MCPToolset(
    connection_params=StdioServerParameters(
        command="{command}",
        args={args},
        env={{{env_str}}},
    ),
)
""")
        elif transport in ("sse", "http"):
            url = server.get("url", f"https://{server_name}.example.com/sse")
            headers = server.get("headers", {})
            headers_str = ", ".join(f'"{k}": "{v}"' for k, v in headers.items()) if headers else ""

            lines.append(f"""# MCP Server: {server_name} (SSE transport)
{var_name} = MCPToolset(
    connection_params=SseServerParams(
        url="{url}",
        headers={{{headers_str}}},
    ),
)
""")

    tool_filter = mcp_config.get("tool_filter", [])
    if tool_filter:
        lines.append(f"# Tool filter (allowlist)\n")
        lines.append(f"for mcp in [{', '.join(mcp_tool_vars)}]:")
        lines.append(f"    # mcp.tool_filter = {tool_filter}  # Uncomment to enable allowlisting\n")
        lines.append("")

    lines.append(f"""# ── Agent with MCP tools ──────────────────────────────────────

agent = Agent(
    name="{name}_mcp_agent",
    model="gemini-2.5-flash",
    instruction="Use MCP tools to complete tasks. Each MCPToolset gives access to specific external capabilities.",
    tools=[{', '.join(mcp_tool_vars)}],
)
""")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compose agents and tools into a complete ADK workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", required=True, help="Workflow composition config (YAML/JSON)")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--lang", default="python", choices=["python", "go", "ts", "mcp"],
                        help="Target language or output type (default: python)")

    args = parser.parse_args()

    cfg = load_config(args.config)

    required = ["name"]
    missing = [k for k in required if k not in cfg]
    if missing:
        print(f"Error: Config missing required fields: {missing}")
        sys.exit(1)

    if args.lang == "python":
        code = generate_python(cfg)
    elif args.lang == "go":
        code = generate_go_workflow(cfg)
    elif args.lang == "ts":
        code = generate_ts_workflow(cfg)
    elif args.lang == "mcp":
        code = generate_mcp_agent_config(cfg)
    else:
        print(f"Error: Language '{args.lang}' not yet supported")
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code)

    print(f"Workflow composed: {output_path}")
    print(f"  Language: {args.lang}")
    print(f"  Agents: {len(cfg.get('agents', []))}")
    print(f"  Tools: {len(cfg.get('tools', []))}")
    if cfg.get("edges"):
        print(f"  Edges: {len(cfg.get('edges', []))}")
    if cfg.get("mcp"):
        print(f"  MCP servers: {len(cfg['mcp'].get('servers', []))}")


if __name__ == "__main__":
    main()
