# adk-mcp-integration

**MCP Toolset Integration for Google ADK**

Connect ADK agents to external tools via Model Context Protocol (MCP). Configure database access, web search, APIs, vector databases, and custom tool servers using the latest ADK patterns.

## When to Use

Use this skill when:
- Agent needs external tool access
- Connecting to databases (SQLite, PostgreSQL)
- Adding web search capabilities
- Integrating APIs (GitHub, GitLab, Notion, Slack)
- Multimodal vector database integration (Pinecone)
- Custom MCP server connections

## Quick Start

```bash
# Add database access
/adk-mcp-integration --server "sqlite" --db_path "data/app.db"

# Add Pinecone multimodal vector database
/adk-mcp-integration --server "pinecone" --index_name "multimodal_kb"

# Add web search
/adk-mcp-integration --server "brave_search"

# Add multiple servers
/adk-mcp-integration --servers "[sqlite,brave_search,github,pinecone]"

# Add Notion integration
/adk-mcp-integration --server "notion"

# Custom MCP server
/adk-mcp-integration --server "custom" --command "python my_server.py"
```

## Parameters

```bash
--server "server_type"             # Single server type
--servers "[server1, server2]"     # Multiple servers
--db_path "path/to/db"             # For database servers
--connection_string "url"          # For remote databases
--index_name "name"                # For Pinecone index
--api_key_env "ENV_VAR_NAME"       # API key environment variable
--command "command"                # For custom servers
--args "[arg1, arg2]"              # Server arguments
--timeout 30                       # Connection timeout (seconds)
```

## MCP Architecture Overview

ADK agents use `McpToolset` to establish connections with MCP servers. When an agent initializes with an McpToolset, it automatically discovers and loads available tools from the MCP server.

```python
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
```

## Supported MCP Servers

### Pinecone Multimodal Vector Database

#### Multimodal Embeddings (Text, Image, Audio, Video)

Pinecone supports multimodal embeddings for comprehensive knowledge retrieval across different content types.

```bash
/adk-mcp-integration --server "pinecone" --index_name "multimodal_kb"
```

**Generated Code for Multimodal Pinecone:**
```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from pinecone import Pinecone, EmbedModel
import base64
import os

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

# Multimodal embedding models
MULTIMODAL_MODELS = {
    "text": EmbedModel.Multilingual_E5_Large,
    "image": "pinecone-clip-vit-base-patch32",  # For images
    "audio": "openai-whisper-large-v3",  # Transcribe then embed
    "video": "pinecone-clip-vit-base-patch32",  # Frame extraction
}

def embed_text(text: str) -> list[float]:
    """Generate text embedding."""
    response = pc.inference.embed(
        model=EmbedModel.Multilingual_E5_Large,
        inputs=[text],
        parameters={"input_type": "passage", "truncate": "END"}
    )
    return response.data[0].values

def embed_image(image_base64: str) -> list[float]:
    """Generate image embedding using CLIP."""
    response = pc.inference.embed(
        model="pinecone-clip-vit-base-patch32",
        inputs=[{"image": image_base64}],
        parameters={"input_type": "image"}
    )
    return response.data[0].values

def embed_audio(audio_base64: str) -> list[float]:
    """Transcribe audio and generate text embedding."""
    # First transcribe using Whisper
    transcription = pc.inference.transcribe(
        model="openai-whisper-large-v3",
        audio=audio_base64
    )
    # Then embed the transcription
    return embed_text(transcription.text)

def embed_video_frames(frames: list[str]) -> list[list[float]]:
    """Generate embeddings for video frames."""
    embeddings = []
    for frame_base64 in frames:
        embedding = embed_image(frame_base64)
        embeddings.append(embedding)
    return embeddings

# Multimodal search tool
def multimodal_search(
    query: str = None,
    image: str = None,
    audio: str = None,
    top_k: int = 5,
    namespace: str = "default"
) -> list[dict]:
    """
    Search knowledge base with text, image, or audio query.

    Args:
        query: Text query
        image: Base64 encoded image
        audio: Base64 encoded audio
        top_k: Number of results
        namespace: Pinecone namespace

    Returns:
        List of relevant documents
    """
    # Generate query embedding based on input type
    if query:
        query_embedding = embed_text(query)
    elif image:
        query_embedding = embed_image(image)
    elif audio:
        query_embedding = embed_audio(audio)
    else:
        raise ValueError("Must provide query, image, or audio")

    # Search Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True
    )

    return [
        {
            "id": m.id,
            "text": m.metadata.get("text", ""),
            "content_type": m.metadata.get("content_type", "text"),
            "source": m.metadata.get("source", ""),
            "score": m.score
        }
        for m in results.matches
    ]

# Multimodal ingestion tool
def ingest_multimodal(
    content: str,
    content_type: str,  # "text", "image", "audio", "video"
    metadata: dict,
    namespace: str = "default"
) -> str:
    """
    Ingest multimodal content into Pinecone.

    Args:
        content: Text or base64 encoded media
        content_type: Type of content
        metadata: Additional metadata
        namespace: Pinecone namespace

    Returns:
        Ingestion status
    """
    import hashlib

    # Generate embedding based on content type
    if content_type == "text":
        embedding = embed_text(content)
    elif content_type == "image":
        embedding = embed_image(content)
    elif content_type == "audio":
        embedding = embed_audio(content)
    elif content_type == "video":
        # For video, extract key frames and average embeddings
        # This is simplified - production would use proper frame extraction
        embedding = embed_image(content)  # Assuming thumbnail
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

    # Generate unique ID
    doc_id = hashlib.md5(f"{content[:100]}_{content_type}".encode()).hexdigest()

    # Upsert to Pinecone
    index.upsert(
        vectors=[{
            "id": doc_id,
            "values": embedding,
            "metadata": {
                "content_type": content_type,
                "text": content if content_type == "text" else metadata.get("description", ""),
                **metadata
            }
        }],
        namespace=namespace
    )

    return f"Ingested {content_type} content with ID: {doc_id}"

# ADK Agent with multimodal Pinecone tools
multimodal_agent = Agent(
    name="multimodal_kb_agent",
    model="gemini-2.5-pro",
    instruction="""You are an intelligent assistant with access to a multimodal knowledge base.

**Capabilities:**
- Search by text, image, or audio query
- Ingest new content (text, images, audio, video)
- Cross-modal retrieval (search images with text, etc.)

**When searching:**
- Use text queries for general information
- Use image queries for visual similarity search
- Use audio queries for speech-based search

**When ingesting:**
- Add appropriate metadata for better retrieval
- Use descriptive text for non-text content
""",
    tools=[
        FunctionTool(multimodal_search),
        FunctionTool(ingest_multimodal),
    ],
)

root_agent = multimodal_agent
```

#### Image-Text Cross-Modal Search

```python
def image_to_text_search(image_base64: str, top_k: int = 5) -> list[dict]:
    """Find text documents relevant to an image."""
    image_embedding = embed_image(image_base64)

    results = index.query(
        vector=image_embedding,
        top_k=top_k,
        namespace="text_documents",  # Search in text namespace
        include_metadata=True,
        filter={"content_type": {"$eq": "text"}}
    )

    return [
        {"text": m.metadata.get("text", ""), "score": m.score}
        for m in results.matches
    ]

def text_to_image_search(query: str, top_k: int = 5) -> list[dict]:
    """Find images relevant to a text query."""
    text_embedding = embed_text(query)

    results = index.query(
        vector=text_embedding,
        top_k=top_k,
        namespace="images",  # Search in image namespace
        include_metadata=True,
        filter={"content_type": {"$eq": "image"}}
    )

    return [
        {
            "image_url": m.metadata.get("url", ""),
            "description": m.metadata.get("description", ""),
            "score": m.score
        }
        for m in results.matches
    ]
```

#### Audio-Video Semantic Search

```python
def audio_semantic_search(audio_base64: str, top_k: int = 5) -> list[dict]:
    """Search knowledge base using audio query (speech)."""
    # Transcribe audio
    transcription = pc.inference.transcribe(
        model="openai-whisper-large-v3",
        audio=audio_base64
    )

    # Generate embedding from transcription
    text_embedding = embed_text(transcription.text)

    results = index.query(
        vector=text_embedding,
        top_k=top_k,
        namespace="all_content",
        include_metadata=True
    )

    return {
        "transcription": transcription.text,
        "results": [
            {
                "content": m.metadata.get("text", ""),
                "content_type": m.metadata.get("content_type", ""),
                "score": m.score
            }
            for m in results.matches
        ]
    }

def video_frame_search(frame_base64: str, top_k: int = 5) -> list[dict]:
    """Search for similar video content using a frame."""
    frame_embedding = embed_image(frame_base64)

    results = index.query(
        vector=frame_embedding,
        top_k=top_k,
        namespace="video_frames",
        include_metadata=True
    )

    return [
        {
            "video_id": m.metadata.get("video_id", ""),
            "timestamp": m.metadata.get("timestamp", 0),
            "description": m.metadata.get("description", ""),
            "score": m.score
        }
        for m in results.matches
    ]
```

### Database Servers

#### SQLite

```bash
/adk-mcp-integration --server "sqlite" --db_path "data/app.db"
```

**Generated Code:**
```python
from google.adk.agents import Agent
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

agent = Agent(
    name="db_agent",
    model="gemini-2.5-flash",
    instruction="You have access to a SQLite database. Use SQL queries to answer questions.",
    tools=[sqlite_tools],
)
```

#### PostgreSQL

```bash
/adk-mcp-integration --server "postgres" --connection_string "postgresql://user:pass@localhost/mydb"
```

**Generated Code:**
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

### Search Servers

#### Brave Search

```bash
/adk-mcp-integration --server "brave_search"
```

**Generated Code:**
```python
import os

brave_search_tools = McpToolset(
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

### Code & Development

#### GitHub

```bash
/adk-mcp-integration --server "github"
```

**Generated Code:**
```python
import os

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

#### GitLab (from ADK docs)

```bash
/adk-mcp-integration --server "gitlab"
```

**Generated Code (from ADK docs):**
```python
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

GITLAB_INSTANCE_URL = "gitlab.com"

root_agent = Agent(
    model="gemini-2.5-pro",
    name="gitlab_agent",
    instruction="Help users get information from GitLab",
    tools=[
        McpToolset(
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
    ],
)
```

### Productivity & Communication

#### Notion (from ADK docs)

```bash
/adk-mcp-integration --server "notion"
```

**Generated Code (from ADK docs):**
```python
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

NOTION_TOKEN = "YOUR_NOTION_TOKEN"

root_agent = Agent(
    model="gemini-2.5-pro",
    name="notion_agent",
    instruction="Help users get information from Notion",
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "@notionhq/notion-mcp-server"],
                    env={"NOTION_TOKEN": NOTION_TOKEN}
                ),
                timeout=30,
            ),
        )
    ],
)
```

#### Slack

```bash
/adk-mcp-integration --server "slack"
```

**Generated Code:**
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

## Multi-Server Configuration with Pinecone Multimodal

```bash
/adk-mcp-integration --servers "[sqlite,brave_search,github,pinecone]"
```

**Generated Code:**
```python
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools import FunctionTool
from mcp import StdioServerParameters
from pinecone import Pinecone, EmbedModel
import os

# Initialize Pinecone for multimodal
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

# Multimodal search function
def multimodal_search(query: str = None, image: str = None, top_k: int = 5) -> str:
    """Search with text or image query."""
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
        return "Provide either query or image"

    results = index.query(vector=embedding, top_k=top_k, include_metadata=True)
    return "\n".join([f"- {m.metadata.get('text', '')[:200]}" for m in results.matches])

# MCP tools
sqlite_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='uvx',
            args=["mcp-server-sqlite", "--db-path", "data/app.db"],
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

# Agent with all tools
agent = Agent(
    name="multi_tool_agent",
    model="gemini-2.5-pro",
    instruction="""You have access to multiple tools:

**Database:** SQLite for structured data queries
**Search:** Brave Search for web information
**Code:** GitHub for repository access
**Knowledge Base:** Pinecone multimodal search (text, images, audio)

Choose the right tool based on the query type.""",
    tools=[
        sqlite_tools,
        brave_tools,
        github_tools,
        FunctionTool(multimodal_search),
    ],
)

root_agent = agent
```

## LangGraph Integration with Pinecone Multimodal

```python
from typing import Annotated, TypedDict, List
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from google.adk.agents import Agent
from pinecone import Pinecone, EmbedModel
import os

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(host=os.getenv("PINECONE_INDEX_HOST"))

class MultimodalRAGState(TypedDict):
    messages: Annotated[list, operator.add]
    query: str
    query_type: str  # "text", "image", "audio"
    query_content: str  # text or base64
    retrieved_docs: List[dict]
    response: str

def detect_query_type(state: MultimodalRAGState) -> dict:
    """Detect if query is text, image, or audio."""
    content = state["messages"][-1].content if state["messages"] else ""

    # Simple detection - in production, use proper detection
    if content.startswith("data:image"):
        return {"query_type": "image", "query_content": content}
    elif content.startswith("data:audio"):
        return {"query_type": "audio", "query_content": content}
    else:
        return {"query_type": "text", "query_content": content, "query": content}

def embed_and_retrieve(state: MultimodalRAGState) -> dict:
    """Generate embedding and retrieve from Pinecone."""
    query_type = state["query_type"]
    content = state["query_content"]

    if query_type == "text":
        embedding = pc.inference.embed(
            model=EmbedModel.Multilingual_E5_Large,
            inputs=[content],
            parameters={"input_type": "query"}
        ).data[0].values
    elif query_type == "image":
        embedding = pc.inference.embed(
            model="pinecone-clip-vit-base-patch32",
            inputs=[{"image": content}]
        ).data[0].values
    elif query_type == "audio":
        # Transcribe first
        transcription = pc.inference.transcribe(
            model="openai-whisper-large-v3",
            audio=content
        )
        embedding = pc.inference.embed(
            model=EmbedModel.Multilingual_E5_Large,
            inputs=[transcription.text],
            parameters={"input_type": "query"}
        ).data[0].values
    else:
        embedding = []

    results = index.query(
        vector=embedding,
        top_k=5,
        include_metadata=True
    )

    docs = [
        {
            "text": m.metadata.get("text", ""),
            "content_type": m.metadata.get("content_type", "text"),
            "score": m.score
        }
        for m in results.matches
    ]

    return {"retrieved_docs": docs}

def generate_response(state: MultimodalRAGState) -> dict:
    """Generate response using ADK agent."""
    context = "\n".join([
        f"[{d['content_type']}]: {d['text']}"
        for d in state["retrieved_docs"]
    ])

    agent = Agent(
        name="multimodal_responder",
        model="gemini-2.5-pro",
        instruction=f"""Answer based on the multimodal knowledge base context:

{context}

The user's query was: {state.get('query', state['query_content'][:100])}
Query type: {state['query_type']}

Provide a helpful, accurate response based on the retrieved information."""
    )

    result = agent.execute(state.get("query", "Describe the content"))

    return {
        "response": result.content,
        "messages": [AIMessage(content=result.content)]
    }

# Build multimodal RAG graph
builder = StateGraph(MultimodalRAGState)

builder.add_node("detect", detect_query_type)
builder.add_node("retrieve", embed_and_retrieve)
builder.add_node("generate", generate_response)

builder.add_edge(START, "detect")
builder.add_edge("detect", "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

multimodal_rag = builder.compile()

# Usage
result = multimodal_rag.invoke({
    "messages": [HumanMessage(content="What products look similar to this image?")],
    "query": "",
    "query_type": "",
    "query_content": "",
    "retrieved_docs": [],
    "response": ""
})
```

## Environment Variables

| Server | Environment Variables |
|--------|----------------------|
| pinecone | PINECONE_API_KEY, PINECONE_INDEX_HOST |
| brave_search | BRAVE_API_KEY |
| github | GITHUB_TOKEN |
| gitlab | (OAuth - first run authorization) |
| slack | SLACK_BOT_TOKEN |
| notion | NOTION_TOKEN |
| postgres | DATABASE_URL |

## Generated Project Structure

```
agent-with-mcp/
+-- src/
|   +-- agent.py           # Agent with MCP tools
|   +-- mcp_config.py      # MCP server setup
|   +-- pinecone_multimodal.py  # Multimodal Pinecone integration
|   +-- config.py
+-- mcp.json               # MCP configuration
+-- .env.example           # Required env vars
+-- deployment/
|   +-- Dockerfile
|   +-- cloud_run.yaml
+-- README.md
```

## Examples

### Example 1: Multimodal Knowledge Base Agent

```bash
$ /adk-mcp-integration --server "pinecone" --multimodal true

MCP + Pinecone Multimodal Integration Complete

Capabilities:
- Text semantic search
- Image similarity search
- Audio transcription + search
- Video frame search
- Cross-modal retrieval

Required ENV:
- PINECONE_API_KEY
- PINECONE_INDEX_HOST
```

### Example 2: Full-Stack Agent

```bash
$ /adk-mcp-integration --servers "[sqlite,brave_search,github,pinecone]"

Multi-Tool Integration Complete

Tools:
- SQLite: Structured data queries
- Brave Search: Web information
- GitHub: Code repositories
- Pinecone: Multimodal knowledge base

Agent ready for deployment.
```

## Related Skills

- **adk-pinecone-rag** - Pinecone RAG pipeline with LangGraph
- **adk-langgraph-orchestrator** - LangGraph workflows
- **adk-adaptive-agent-generator** - Create agents with MCP
- **adk-deployment-manager** - Deploy MCP-enabled agents

## MCP Server Catalog

See `/mcp_servers/CATALOG.md` for complete server list.

## More Information

- Google ADK MCP docs: https://google.github.io/adk-docs/tools-custom/mcp-tools
- Pinecone docs: https://docs.pinecone.io/
- MCP specification: https://modelcontextprotocol.io/
