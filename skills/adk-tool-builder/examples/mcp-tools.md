# MCP Tool Integration Examples

Complete examples for integrating MCP (Model Context Protocol) servers with ADK agents.

## Example 1: Filesystem MCP Server

```python
from google.adk.tools import MCPToolset
from google.adk.agents import LlmAgent

# Connect to filesystem MCP server
filesystem_tools = MCPToolset(
    server_url="stdio://mcp-server-filesystem",
    name="filesystem",
    config={
        "allowed_directories": ["/home/user/documents", "/tmp"],
        "max_file_size": 10485760,  # 10MB
    },
)

# Create agent with filesystem capabilities
file_agent = LlmAgent(
    name="file_assistant",
    model="gemini-2.0-flash-exp",
    tools=[filesystem_tools],
    system_instruction="""You are a file management assistant.
    You can read, write, list, and search files.
    Always confirm before deleting or modifying files.
    Respect directory restrictions.""",
)

# The agent now has access to all tools from the MCP server:
# - read_file
# - write_file
# - list_directory
# - search_files
# - delete_file
# - get_file_info

# Example conversation
if __name__ == "__main__":
    # User: "List all Python files in /home/user/documents"
    # Agent: Uses list_directory tool with filter
    response = file_agent.send_message("List all Python files in /home/user/documents")
    print(response.text)
```

## Example 2: Database MCP Server

```python
from google.adk.tools import MCPToolset
from google.adk.agents import LlmAgent
import os

# Connect to PostgreSQL MCP server
db_tools = MCPToolset(
    server_url="stdio://mcp-server-postgres",
    name="database",
    config={
        "connection_string": os.environ["DATABASE_URL"],
        "read_only": False,
        "max_query_time": 30,  # seconds
        "allowed_operations": ["SELECT", "INSERT", "UPDATE"],  # No DELETE
    },
)

# Create database agent
db_agent = LlmAgent(
    name="database_assistant",
    model="gemini-2.0-flash-exp",
    tools=[db_tools],
    system_instruction="""You are a database assistant.
    You can query and modify the database safely.
    Always use parameterized queries to prevent SQL injection.
    Confirm with user before UPDATE operations.
    DELETE operations are not allowed.""",
)

# Available tools from MCP server:
# - execute_query
# - get_schema
# - list_tables
# - describe_table
# - get_table_data
# - insert_record
# - update_record

# Example usage
if __name__ == "__main__":
    # User: "Show me the schema for the users table"
    response = db_agent.send_message("Show me the schema for the users table")
    print(response.text)

    # User: "Find all active users in the US"
    response = db_agent.send_message("Find all active users in the US")
    print(response.text)
```

## Example 3: Web Browser Automation MCP

```python
from google.adk.tools import MCPToolset
from google.adk.agents import LlmAgent

# Connect to Puppeteer MCP server for browser automation
browser_tools = MCPToolset(
    server_url="stdio://mcp-server-puppeteer",
    name="browser",
    config={
        "headless": True,
        "timeout": 60000,  # 60 seconds
        "viewport": {"width": 1920, "height": 1080},
    },
)

# Create web automation agent
browser_agent = LlmAgent(
    name="web_scraper",
    model="gemini-2.0-flash-exp",
    tools=[browser_tools],
    system_instruction="""You are a web automation assistant.
    You can navigate websites, extract data, and interact with pages.
    Always respect robots.txt and rate limits.
    Close browser sessions when done.""",
)

# Available MCP tools:
# - navigate_to_url
# - click_element
# - type_text
# - extract_text
# - get_screenshot
# - wait_for_element
# - execute_javascript

# Example scraping task
if __name__ == "__main__":
    response = browser_agent.send_message(
        "Go to example.com and extract the main heading"
    )
    print(response.text)
```

## Example 4: Multiple MCP Servers

```python
from google.adk.tools import MCPToolset
from google.adk.agents import LlmAgent

# Filesystem access
fs_tools = MCPToolset(
    server_url="stdio://mcp-server-filesystem",
    name="filesystem",
)

# Git operations
git_tools = MCPToolset(
    server_url="stdio://mcp-server-git",
    name="git",
    config={
        "allowed_repos": ["/home/user/projects"],
    },
)

# Slack integration
slack_tools = MCPToolset(
    server_url="stdio://mcp-server-slack",
    name="slack",
    config={
        "token": os.environ["SLACK_BOT_TOKEN"],
        "allowed_channels": ["#engineering", "#alerts"],
    },
)

# Create powerful automation agent
automation_agent = LlmAgent(
    name="automation_assistant",
    model="gemini-2.0-flash-exp",
    tools=[fs_tools, git_tools, slack_tools],
    system_instruction="""You are an automation assistant.
    You can manage files, interact with Git, and send Slack messages.
    Coordinate multi-step automation tasks efficiently.""",
)

# Example: Automated deployment notification
if __name__ == "__main__":
    response = automation_agent.send_message("""
        Check the status of the main branch in /home/user/projects/myapp,
        create a deployment summary file,
        and send it to #engineering on Slack.
    """)
    print(response.text)
```

## Example 5: Custom MCP Server

Build your own MCP server for domain-specific tools:

```python
# custom_mcp_server.py
from mcp.server import MCPServer, Tool
from mcp.types import TextContent
import asyncio

class CustomMCPServer(MCPServer):
    """Custom MCP server with domain-specific tools."""

    def __init__(self):
        super().__init__(name="custom-tools")
        self.register_tools()

    def register_tools(self):
        """Register custom tools."""

        @self.tool(
            name="calculate_shipping",
            description="Calculate shipping cost for an order",
            schema={
                "type": "object",
                "properties": {
                    "weight_kg": {"type": "number", "description": "Package weight in kg"},
                    "destination": {"type": "string", "description": "Destination country code"},
                    "service": {
                        "type": "string",
                        "enum": ["standard", "express", "overnight"],
                        "description": "Shipping service level"
                    }
                },
                "required": ["weight_kg", "destination", "service"]
            }
        )
        async def calculate_shipping(weight_kg: float, destination: str, service: str):
            """Calculate shipping cost."""
            # Implementation
            base_rate = {
                "standard": 5.0,
                "express": 15.0,
                "overnight": 30.0,
            }[service]

            weight_charge = weight_kg * 2.0

            international = 10.0 if destination != "US" else 0.0

            total = base_rate + weight_charge + international

            return {
                "cost": round(total, 2),
                "currency": "USD",
                "estimated_days": {
                    "standard": "5-7",
                    "express": "2-3",
                    "overnight": "1",
                }[service],
                "breakdown": {
                    "base_rate": base_rate,
                    "weight_charge": weight_charge,
                    "international_fee": international,
                }
            }

        @self.tool(
            name="check_inventory",
            description="Check product inventory",
            schema={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Product SKU"},
                    "warehouse": {"type": "string", "description": "Warehouse code"}
                },
                "required": ["product_id"]
            }
        )
        async def check_inventory(product_id: str, warehouse: str = "main"):
            """Check inventory levels."""
            # Mock implementation
            return {
                "product_id": product_id,
                "warehouse": warehouse,
                "quantity": 42,
                "reserved": 5,
                "available": 37,
                "reorder_point": 10,
                "needs_reorder": False,
            }

# Run the MCP server
if __name__ == "__main__":
    server = CustomMCPServer()
    asyncio.run(server.run())
```

Use the custom MCP server with ADK:

```python
# agent.py
from google.adk.tools import MCPToolset
from google.adk.agents import LlmAgent

# Connect to custom MCP server
custom_tools = MCPToolset(
    server_url="stdio://python custom_mcp_server.py",
    name="shipping_tools",
)

# Create agent
shipping_agent = LlmAgent(
    name="shipping_assistant",
    model="gemini-2.0-flash-exp",
    tools=[custom_tools],
    system_instruction="""You are a shipping assistant.
    You can calculate shipping costs and check inventory.
    Provide accurate cost estimates and inventory information.""",
)

# Test
if __name__ == "__main__":
    response = shipping_agent.send_message(
        "How much to ship a 2.5kg package to Canada via express?"
    )
    print(response.text)
```

## Example 6: MCP Server Discovery

```python
from google.adk.tools import MCPToolset
from google.adk.agents import LlmAgent
import json

# Connect to MCP server
toolset = MCPToolset(
    server_url="stdio://mcp-server-filesystem",
    name="filesystem",
)

# Discover available tools
print("Discovering tools from MCP server...")
tools_list = toolset.list_tools()

print(f"\nFound {len(tools_list)} tools:")
for tool in tools_list:
    print(f"\n  {tool['name']}")
    print(f"    Description: {tool['description']}")
    print(f"    Schema: {json.dumps(tool['schema'], indent=6)}")

# Output example:
# Found 6 tools:
#
#   read_file
#     Description: Read contents of a file
#     Schema: {
#       "type": "object",
#       "properties": {
#         "path": {"type": "string", "description": "File path"}
#       },
#       "required": ["path"]
#     }
#
#   write_file
#     Description: Write content to a file
#     ...
```

## Example 7: Error Handling with MCP

```python
from google.adk.tools import MCPToolset
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

# Create MCP toolset
fs_tools = MCPToolset(
    server_url="stdio://mcp-server-filesystem",
    name="filesystem",
    timeout=30,  # 30 second timeout
)

# Error handling callback
def handle_tool_errors(ctx: CallbackContext, result):
    """Log and handle MCP tool errors."""
    if not result.get("success"):
        error = result.get("error", "Unknown error")
        print(f"MCP Tool Error: {error}")

        # Return user-friendly message
        return {
            "success": False,
            "error": f"File operation failed: {error}",
            "suggestion": "Please check the file path and permissions.",
        }

    return None  # Continue normal flow

# Create agent with error handling
file_agent = LlmAgent(
    name="file_assistant",
    model="gemini-2.0-flash-exp",
    tools=[fs_tools],
    after_tool_callback=handle_tool_errors,
    system_instruction="""You are a file assistant.
    If a file operation fails, explain the error clearly and suggest alternatives.""",
)
```

## MCP Server URLs

| Transport | URL Format | Example |
|-----------|------------|---------|
| **Stdio** | `stdio://command [args]` | `stdio://mcp-server-filesystem` |
| **Stdio with path** | `stdio:///path/to/server` | `stdio:///usr/local/bin/mcp-server` |
| **HTTP** | `http://host:port` | `http://localhost:3000` |
| **HTTPS** | `https://host:port` | `https://api.example.com` |

## Installing MCP Servers

```bash
# Official MCP servers
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-postgres
npm install -g @modelcontextprotocol/server-puppeteer
npm install -g @modelcontextprotocol/server-git
npm install -g @modelcontextprotocol/server-slack

# Python MCP servers
pip install mcp-server-sqlite
pip install mcp-server-github

# Verify installation
which mcp-server-filesystem
mcp-server-filesystem --version
```

## Configuration Best Practices

### 1. Use Environment Variables for Secrets

```python
import os

db_tools = MCPToolset(
    server_url="stdio://mcp-server-postgres",
    name="database",
    config={
        "connection_string": os.environ["DATABASE_URL"],
        "api_key": os.environ.get("DB_API_KEY"),
    },
)
```

### 2. Set Appropriate Timeouts

```python
# Fast operations
cache_tools = MCPToolset(
    server_url="stdio://mcp-server-redis",
    name="cache",
    timeout=5,  # 5 seconds
)

# Slow operations
video_tools = MCPToolset(
    server_url="stdio://mcp-server-ffmpeg",
    name="video",
    timeout=300,  # 5 minutes
)
```

### 3. Restrict Capabilities

```python
fs_tools = MCPToolset(
    server_url="stdio://mcp-server-filesystem",
    name="filesystem",
    config={
        "allowed_directories": ["/home/user/safe_dir"],
        "allowed_operations": ["read", "list"],  # No write/delete
        "max_file_size": 1048576,  # 1MB
    },
)
```

### 4. Handle Connection Failures

```python
try:
    tools = MCPToolset(
        server_url="stdio://mcp-server-custom",
        name="custom",
    )
    print("Connected to MCP server successfully")
except Exception as e:
    print(f"Failed to connect to MCP server: {e}")
    # Fall back to alternative tools
    tools = None
```

## Testing MCP Integration

```python
import pytest
from google.adk.tools import MCPToolset

@pytest.fixture
def mcp_toolset():
    """Create MCP toolset for testing."""
    return MCPToolset(
        server_url="stdio://mcp-server-filesystem",
        name="filesystem",
    )

def test_mcp_connection(mcp_toolset):
    """Test MCP server connection."""
    tools = mcp_toolset.list_tools()
    assert len(tools) > 0
    assert any(t["name"] == "read_file" for t in tools)

@pytest.mark.asyncio
async def test_mcp_tool_invocation(mcp_toolset):
    """Test invoking MCP tool."""
    result = await mcp_toolset.invoke_tool(
        tool_name="read_file",
        parameters={"path": "/tmp/test.txt"},
    )
    assert "content" in result or "error" in result

def test_mcp_with_agent():
    """Test MCP tools with agent."""
    toolset = MCPToolset(
        server_url="stdio://mcp-server-filesystem",
        name="filesystem",
    )

    agent = LlmAgent(
        name="test_agent",
        model="gemini-2.0-flash-exp",
        tools=[toolset],
    )

    assert len(agent.tools) > 0
```

## Related Resources

- MCP Protocol Specification: https://modelcontextprotocol.io
- Official MCP Servers: https://github.com/modelcontextprotocol/servers
- Build Custom MCP Servers: https://modelcontextprotocol.io/docs/building-servers
- ADK MCP Integration Skill: **adk-mcp-integration**
