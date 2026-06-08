🗺️ Integrating and Deploying MCP Tools with the ADK

This guide provides a step-by-step workflow for integrating a Managed Computing Platform (MCP) server, specifically the Google Maps server, as a tool within an ADK agent, and how to prepare the final agent system for deployment on a platform like Cloud Run.

I. Prerequisites and Setup

Before you begin, ensure you have the following installed and configured:

Python Environment: Python 3.9+ and a virtual environment.

ADK Installation:

pip install google-adk


Node/NPM/npx: The Google Maps MCP tool is often distributed as a Node.js package, requiring npx (which comes with npm) to run the server component.

Google Maps API Key:

Obtain an API key from Google Cloud Console.

Ensure APIs like Directions API are enabled for this key.

Environment File (.env): Create or update your .env file to securely store your keys.

# .env
# Your Gemini API Key for the LLM
GEMINI_API_KEY="AIzaSy...your...key"

# Your Google Maps API Key for the MCP Toolset
GOOGLE_MAPS_API_KEY="AIzaSy...your...maps...key"








import os
from google.adk.agents import LlmAgent
# Import MCP tooling classes
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# 1. Retrieve the API Key from the environment
google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY")

if not google_maps_api_key:
    print("FATAL: GOOGLE_MAPS_API_KEY environment variable is not set.")
    # In a real app, you might raise an error here.

# 2. Define the MCP Toolset Client
# This setup tells the ADK agent how to launch and connect to the Maps MCP server.
maps_tool_set = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            # The command is 'npx' which runs the Maps MCP server package
            command='npx',
            args=[
                "-y",
                "@google/mcp-maps-server",
                # Crucially, pass the Maps API key to the server as an environment variable
                f"GOOGLE_MAPS_API_KEY={google_maps_api_key}"
            ],
            # Optional: Define working directory, timeout, etc.
        ),
    ),
    # Optional: Filter the specific tools you want to expose (e.g., ['get_directions', 'find_place'])
    # tool_filter=['get_directions']
)

# 3. Define the Agent that uses the tool
navigation_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='MapsAssistantAgent',
    instruction=(
        'You are a Navigation Specialist. Use the tools provided by the MCP Toolset to answer '
        'questions about distances, routes, and directions between locations. When providing directions, '
        'always use the "get_directions" tool.'
    ),
    tools=[maps_tool_set] # Provide the configured McpToolset
)

# 4. Define the Root Agent (for ADK Web UI)
root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='RootAgent',
    instruction='Delegate to the MapsAssistantAgent for any questions about navigation or maps.',
    sub_agents=[navigation_agent]
)
```

### 2. Local Testing

To test the integration locally, ensure your environment variables are loaded and run the ADK web interface:

1.  **Set Environment Variables:**
    ```bash
    source .env
    ```
2.  **Run ADK Web:**
    ```bash
    adk web