# MCP Server Catalog for Google ADK

Complete catalog of MCP servers optimized for Google ADK agent integration. Includes configuration examples, environment variables, and best practices.

## Quick Reference

| Category | Server | Use Case |
|----------|--------|----------|
| **Vector DB** | Pinecone | Multimodal RAG (text, image, audio, video) |
| **Database** | SQLite | Local structured data |
| **Database** | PostgreSQL | Production databases |
| **Search** | Brave Search | Web search |
| **Code** | GitHub | Repository access |
| **Code** | GitLab | GitLab repositories |
| **Productivity** | Notion | Notes and databases |
| **Communication** | Slack | Team messaging |
| **Storage** | Filesystem | Local file access |

---

## Vector Database Servers

### Pinecone (Recommended for Multimodal RAG)

Pinecone provides multimodal vector search supporting text, images, audio, and video embeddings.

**Installation:**
```bash
pip install pinecone
```

**Configuration:**
```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from pinecone import Pinecone, EmbedModel
import os

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

# Multimodal embedding functions
def embed_text(text: str) -> list[float]:
    return pc.inference.embed(
        model=EmbedModel.Multilingual_E5_Large,
        inputs=[text],
        parameters={"input_type": "passage"}
    ).data[0].values

def embed_image(image_base64: str) -> list[float]:
    return pc.inference.embed(
        model="pinecone-clip-vit-base-patch32",
        inputs=[{"image": image_base64}]
    ).data[0].values

def embed_audio(audio_base64: str) -> list[float]:
    transcription = pc.inference.transcribe(
        model="openai-whisper-large-v3",
        audio=audio_base64
    )
    return embed_text(transcription.text)

def multimodal_search(query: str = None, image: str = None, audio: str = None, top_k: int = 5) -> list[dict]:
    """Search with text, image, or audio query."""
    if query:
        embedding = embed_text(query)
    elif image:
        embedding = embed_image(image)
    elif audio:
        embedding = embed_audio(audio)
    else:
        return []

    results = index.query(vector=embedding, top_k=top_k, include_metadata=True)
    return [{"text": m.metadata.get("text", ""), "score": m.score} for m in results.matches]

# Agent with multimodal search
multimodal_agent = Agent(
    name="multimodal_kb",
    model="gemini-2.5-pro",
    instruction="Search the multimodal knowledge base for relevant information.",
    tools=[FunctionTool(multimodal_search)],
)
```

**Environment Variables:**
```bash
PINECONE_API_KEY=your_api_key
PINECONE_INDEX_HOST=your_index_host
```

**Supported Modalities:**
- Text: `EmbedModel.Multilingual_E5_Large`
- Images: `pinecone-clip-vit-base-patch32`
- Audio: Whisper transcription + text embedding
- Video: Frame extraction + image embedding

---

## Database Servers

### SQLite

Local database access via MCP.

**Configuration:**
```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

sqlite_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='uvx',
            args=["mcp-server-sqlite", "--db-path", "data/app.db"],
        ),
        timeout=30,
    ),
)
```

**Installation:**
```bash
uvx mcp-server-sqlite --help
```

### PostgreSQL

Production database access.

**Configuration:**
```python
postgres_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@modelcontextprotocol/server-postgres",
                  "postgresql://user:pass@localhost/mydb"],
        ),
        timeout=30,
    ),
)
```

**Environment Variables:**
```bash
DATABASE_URL=postgresql://user:pass@localhost/mydb
```

---

## Search Servers

### Brave Search

Web search capabilities.

**Configuration:**
```python
brave_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@anthropic/mcp-server-brave-search"],
            env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")},
        ),
        timeout=30,
    ),
)
```

**Environment Variables:**
```bash
BRAVE_API_KEY=your_brave_api_key
```

---

## Code & Development Servers

### GitHub

GitHub repository access.

**Configuration:**
```python
github_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")},
        ),
        timeout=30,
    ),
)
```

**Environment Variables:**
```bash
GITHUB_TOKEN=your_github_token
```

### GitLab

GitLab repository access with OAuth.

**Configuration:**
```python
GITLAB_INSTANCE_URL = "gitlab.com"  # Or self-hosted URL

gitlab_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "mcp-remote",
                f"https://{GITLAB_INSTANCE_URL}/api/v4/mcp",
                "--static-oauth-client-metadata",
                '{"scope": "mcp"}',
            ],
        ),
        timeout=30,
    ),
)
```

### Filesystem

Local file system access.

**Configuration:**
```python
filesystem_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"],
        ),
        timeout=30,
    ),
)
```

---

## Productivity Servers

### Notion

Notion workspace access.

**Configuration:**
```python
notion_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@notionhq/notion-mcp-server"],
            env={"NOTION_TOKEN": os.getenv("NOTION_TOKEN")},
        ),
        timeout=30,
    ),
)
```

**Environment Variables:**
```bash
NOTION_TOKEN=your_notion_integration_token
```

### Slack

Team messaging.

**Configuration:**
```python
slack_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@modelcontextprotocol/server-slack"],
            env={"SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN")},
        ),
        timeout=30,
    ),
)
```

**Environment Variables:**
```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
```

---

## Multi-Server Agent Configuration

Combine multiple MCP servers with Pinecone multimodal for a comprehensive agent.

```python
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools import FunctionTool
from mcp import StdioServerParameters
from pinecone import Pinecone, EmbedModel
import os

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

def multimodal_search(query: str = None, image: str = None, top_k: int = 5) -> str:
    if query:
        embedding = pc.inference.embed(
            model=EmbedModel.Multilingual_E5_Large,
            inputs=[query],
            parameters={"input_type": "query"}
        ).data[0].values
    elif image:
        embedding = pc.inference.embed(
            model="pinecone-clip-vit-base-patch32",
            inputs=[{"image": image}]
        ).data[0].values
    else:
        return "Provide query or image"

    results = index.query(vector=embedding, top_k=top_k, include_metadata=True)
    return "\n".join([f"- {m.metadata.get('text', '')[:200]}" for m in results.matches])

# MCP servers
sqlite_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='uvx',
            args=["mcp-server-sqlite", "--db-path", "data.db"],
        ),
    ),
)

brave_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@anthropic/mcp-server-brave-search"],
            env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")},
        ),
    ),
)

github_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")},
        ),
    ),
)

# Full-stack agent
full_stack_agent = Agent(
    name="full_stack_assistant",
    model="gemini-2.5-pro",
    instruction="""You have access to multiple tools:

**Knowledge Base (Pinecone):**
- Multimodal search: text, images, audio
- Use for semantic queries and visual similarity

**Databases (SQLite):**
- Structured data queries
- Use for specific data lookups

**Web Search (Brave):**
- Real-time web information
- Use for current events and external data

**Code (GitHub):**
- Repository access
- Use for code-related queries

Choose the appropriate tool based on the query type.""",
    tools=[
        FunctionTool(multimodal_search),
        sqlite_tools,
        brave_tools,
        github_tools,
    ],
)

root_agent = full_stack_agent
```

---

## Environment Variables Summary

```bash
# Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_HOST=your_index_host

# Search
BRAVE_API_KEY=your_brave_api_key

# Code
GITHUB_TOKEN=your_github_token

# Productivity
NOTION_TOKEN=your_notion_token
SLACK_BOT_TOKEN=xoxb-your-token

# Databases
DATABASE_URL=postgresql://user:pass@host/db
```

---

## Best Practices

1. **Use Pinecone for multimodal**: Best support for text, image, audio, video embeddings
2. **Timeout configuration**: Always set appropriate timeouts (30s default)
3. **Environment variables**: Never hardcode API keys
4. **Error handling**: Wrap MCP calls in try-except
5. **Tool selection**: Let the agent decide which tool to use based on query type

---

## LangGraph Integration

All MCP servers can be integrated with LangGraph for stateful workflows. See `adk-langgraph-orchestrator` skill for examples.

---

## More Information

- Google ADK MCP docs: https://google.github.io/adk-docs/tools-custom/mcp-tools
- Pinecone docs: https://docs.pinecone.io/
- MCP specification: https://modelcontextprotocol.io/
- LangGraph docs: https://langchain-ai.github.io/langgraph/
