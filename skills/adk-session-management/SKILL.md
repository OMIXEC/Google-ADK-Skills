---
name: ADK Session Management
description: This skill should be used when the user asks to "add session persistence", "implement conversation memory", "save agent state", "multi-turn conversations", "remember user context", "agent memory management", "database session storage", or "Vertex AI session service". Provides comprehensive patterns for session and memory management in ADK agents.
version: 1.0.0
---

# ADK Session Management

Session and memory services enable agents to maintain state across conversations, remember user preferences, and provide personalized experiences. The ADK provides multiple storage backends for different use cases.

## Session vs Memory

| Concept | Purpose | Scope | Storage |
|---------|---------|-------|---------|
| **Session** | Conversation state, turn history | Single conversation | Session service |
| **Memory** | Long-term facts, user preferences | Cross-conversation | Memory service |

**Session** = "What did we just talk about?"
**Memory** = "What do I know about this user?"

## Session Services

### Service Types

| Service | Use Case | Persistence | Setup |
|---------|----------|-------------|-------|
| **InMemorySessionService** | Development, testing | None (in-memory) | No config needed |
| **DatabaseSessionService** | Production | Database (PostgreSQL, MySQL) | Requires DB connection |
| **VertexAiSessionService** | Cloud production | Vertex AI managed | Requires GCP project |

## InMemorySessionService

For development and testing - sessions lost on restart.

```python
from google.adk.sessions import InMemorySessionService
from google.adk.agents import LlmAgent
from google.adk.runners import Runner

# Create session service
session_service = InMemorySessionService()

# Create agent
agent = LlmAgent(
    name="my_agent",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool],
)

# Create runner with session service
runner = Runner(
    agent=agent,
    app_name="my_app",
    session_service=session_service,
)

# Start conversation
session_id = "user_123_session_1"

response1 = runner.run(
    user_input="My name is Alice",
    session_id=session_id,
)
print(response1.text)  # "Nice to meet you, Alice!"

response2 = runner.run(
    user_input="What's my name?",
    session_id=session_id,
)
print(response2.text)  # "Your name is Alice!"
```

**Characteristics:**
- Zero configuration
- Fast (no I/O)
- Sessions lost on restart
- Suitable for development only

## DatabaseSessionService

For production - persistent sessions in relational database.

### PostgreSQL Setup

```python
from google.adk.sessions import DatabaseSessionService
from google.adk.agents import LlmAgent
from google.adk.runners import Runner

# Create database session service
session_service = DatabaseSessionService(
    connection_string="postgresql://user:password@localhost:5432/agent_db",
    table_name="agent_sessions",  # Optional custom table name
)

# Create runner
runner = Runner(
    agent=agent,
    app_name="production_app",
    session_service=session_service,
)

# Sessions automatically persisted to database
session_id = "user_123_session_1"
response = runner.run(
    user_input="Hello",
    session_id=session_id,
)
```

### Database Schema

The DatabaseSessionService creates this table automatically:

```sql
CREATE TABLE agent_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    app_name VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conversation_history JSONB NOT NULL,
    metadata JSONB,
    INDEX idx_app_agent (app_name, agent_name),
    INDEX idx_updated (updated_at)
);
```

### MySQL Setup

```python
session_service = DatabaseSessionService(
    connection_string="mysql://user:password@localhost:3306/agent_db",
    table_name="agent_sessions",
)
```

### SQLite Setup (for small deployments)

```python
session_service = DatabaseSessionService(
    connection_string="sqlite:///agent_sessions.db",
)
```

### Configuration Options

```python
session_service = DatabaseSessionService(
    connection_string="postgresql://...",
    table_name="custom_sessions",
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Max overflow connections
    pool_timeout=30,  # Connection timeout (seconds)
    auto_create_table=True,  # Create table if not exists (default)
)
```

## VertexAiSessionService

For cloud production - fully managed by Google Cloud.

```python
from google.adk.sessions import VertexAiSessionService
from google.adk.agents import LlmAgent
from google.adk.runners import Runner

# Create Vertex AI session service
session_service = VertexAiSessionService(
    project_id="my-gcp-project",
    location="us-central1",
)

# Create runner
runner = Runner(
    agent=agent,
    app_name="cloud_app",
    session_service=session_service,
)

# Sessions stored in Vertex AI
session_id = "user_123_session_1"
response = runner.run(
    user_input="Hello",
    session_id=session_id,
)
```

**Benefits:**
- Fully managed (no database maintenance)
- Automatic scaling
- Built-in security and compliance
- Integration with other Vertex AI services

**Requirements:**
- GCP project with Vertex AI enabled
- Service account with appropriate permissions
- Project billing enabled

## Memory Services

Memory services store long-term information across sessions.

### Memory Service Types

| Service | Use Case | Persistence | Search |
|---------|----------|-------------|--------|
| **InMemoryMemoryService** | Development | None | Simple lookup |
| **VertexAiMemoryBankService** | Production | Vertex AI | Semantic search |

## InMemoryMemoryService

For development and testing.

```python
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner

# Create memory service
memory_service = InMemoryMemoryService()

# Create runner with memory
runner = Runner(
    agent=agent,
    app_name="my_app",
    session_service=session_service,
    memory_service=memory_service,
)

# Agent can now store and retrieve memories
# Example conversation:
# User: "My favorite color is blue"
# Agent stores this fact in memory

# Later session:
# User: "What's my favorite color?"
# Agent retrieves from memory: "Your favorite color is blue"
```

## VertexAiMemoryBankService

For production with semantic search capabilities.

```python
from google.adk.memory import VertexAiMemoryBankService
from google.adk.runners import Runner

# Create Vertex AI memory service
memory_service = VertexAiMemoryBankService(
    project_id="my-gcp-project",
    location="us-central1",
    memory_bank_id="user_preferences",
)

# Create runner
runner = Runner(
    agent=agent,
    app_name="my_app",
    session_service=session_service,
    memory_service=memory_service,
)

# Agent stores facts with semantic understanding
# User: "I love Italian food"
# Stored as semantic memory

# Later:
# User: "What kind of restaurants do I like?"
# Agent uses semantic search to find related memories
```

**Features:**
- Semantic search (finds related memories, not just exact matches)
- Automatic embedding generation
- Scalable storage
- Built-in deduplication

## Complete Setup Example

```python
from google.adk.agents import LlmAgent
from google.adk.sessions import DatabaseSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.adk.runners import Runner
from google.adk.tools import FunctionTool

# Create tools
def get_weather(city: str) -> dict:
    """Get weather for a city."""
    return {"city": city, "temp": 72, "condition": "sunny"}

weather_tool = FunctionTool(get_weather)

# Create agent
agent = LlmAgent(
    name="assistant",
    model="gemini-2.0-flash-exp",
    tools=[weather_tool],
    system_instruction="""You are a helpful assistant with memory.
    Remember user preferences and past conversations.
    Use stored memories to provide personalized responses.""",
)

# Configure session service (persistent)
session_service = DatabaseSessionService(
    connection_string="postgresql://user:pass@localhost/agentdb",
)

# Configure memory service (long-term)
memory_service = VertexAiMemoryBankService(
    project_id="my-gcp-project",
    location="us-central1",
    memory_bank_id="user_memories",
)

# Create runner with both services
runner = Runner(
    agent=agent,
    app_name="my_assistant",
    session_service=session_service,
    memory_service=memory_service,
)

# Use in application
def chat(user_id: str, message: str):
    """Handle chat message."""
    session_id = f"{user_id}_main_session"

    response = runner.run(
        user_input=message,
        session_id=session_id,
    )

    return response.text

# Example usage
print(chat("user_123", "My name is Alice and I love pizza"))
# Agent stores in memory: user_123 is named Alice, likes pizza

print(chat("user_123", "What do I like to eat?"))
# Agent retrieves from memory: "You love pizza!"
```

## Session Lifecycle Management

### Creating Sessions

```python
# Sessions created automatically on first message
session_id = "user_123_session_1"

response = runner.run(
    user_input="Hello",
    session_id=session_id,
)

# Session now exists and tracks conversation history
```

### Retrieving Sessions

```python
# Get session data
session_data = session_service.get_session(session_id)

print(session_data["conversation_history"])
print(session_data["created_at"])
print(session_data["updated_at"])
```

### Listing Sessions

```python
# List all sessions for an app
sessions = session_service.list_sessions(
    app_name="my_app",
    agent_name="assistant",
)

for session in sessions:
    print(f"Session: {session['session_id']}")
    print(f"Created: {session['created_at']}")
    print(f"Turns: {len(session['conversation_history'])}")
```

### Deleting Sessions

```python
# Delete a specific session
session_service.delete_session(session_id)

# Delete old sessions (cleanup)
from datetime import datetime, timedelta

cutoff_date = datetime.now() - timedelta(days=30)

old_sessions = session_service.list_sessions(
    app_name="my_app",
    before_date=cutoff_date,
)

for session in old_sessions:
    session_service.delete_session(session["session_id"])
```

## Session Metadata

Store custom metadata with sessions.

```python
# Add metadata when creating session
response = runner.run(
    user_input="Hello",
    session_id=session_id,
    metadata={
        "user_id": "user_123",
        "user_tier": "premium",
        "source": "web_app",
        "language": "en",
    },
)

# Retrieve session with metadata
session = session_service.get_session(session_id)
print(session["metadata"]["user_tier"])  # "premium"

# Update metadata
session_service.update_session_metadata(
    session_id=session_id,
    metadata={
        "last_login": "2024-01-15T10:30:00Z",
        "feature_flags": ["new_ui", "advanced_tools"],
    },
)

# Query sessions by metadata
premium_sessions = session_service.list_sessions(
    app_name="my_app",
    metadata_filter={"user_tier": "premium"},
)
```

## Multi-Agent Session Sharing

Share session state across multiple agents.

```python
# Create multiple agents
researcher = LlmAgent(
    name="researcher",
    model="gemini-2.0-flash-exp",
    tools=[search_tool],
)

analyst = LlmAgent(
    name="analyst",
    model="gemini-2.0-flash-exp",
    tools=[calculate_tool],
)

# Share session service
shared_session_service = DatabaseSessionService(
    connection_string="postgresql://...",
)

# Create runners for each agent
researcher_runner = Runner(
    agent=researcher,
    app_name="research_app",
    session_service=shared_session_service,
)

analyst_runner = Runner(
    agent=analyst,
    app_name="research_app",
    session_service=shared_session_service,
)

# Both agents can access the same session
session_id = "shared_session_1"

# Researcher agent
response1 = researcher_runner.run(
    user_input="Find information about AI trends",
    session_id=session_id,
)

# Analyst agent (sees researcher's conversation)
response2 = analyst_runner.run(
    user_input="Analyze the trends that were found",
    session_id=session_id,
)
```

## Memory Management Patterns

### Storing Facts

```python
# Agent automatically extracts and stores facts during conversation
# User: "I work at Google and my role is Software Engineer"
# Agent stores:
# - user works at Google
# - user's role is Software Engineer

# Explicit memory storage (if needed)
from google.adk.memory import Memory

memory_service.store_memory(
    user_id="user_123",
    memory=Memory(
        content="User prefers dark mode",
        tags=["preference", "ui"],
        source="user_settings",
    ),
)
```

### Retrieving Memories

```python
# Agent automatically retrieves relevant memories
# User: "Where do I work?"
# Agent searches memories, finds "user works at Google"
# Responds: "You work at Google"

# Explicit memory retrieval
memories = memory_service.search_memories(
    user_id="user_123",
    query="What are the user's preferences?",
    limit=5,
)

for memory in memories:
    print(f"Memory: {memory.content}")
    print(f"Relevance: {memory.score}")
```

### Updating Memories

```python
# Memories automatically updated when user provides new information
# User: "I got promoted to Senior Engineer"
# Agent updates existing memory about role

# Explicit update
memory_service.update_memory(
    memory_id="mem_456",
    content="User is now Senior Engineer at Google",
)
```

### Deleting Memories

```python
# Delete specific memory
memory_service.delete_memory(memory_id="mem_456")

# Delete all memories for a user
memory_service.delete_user_memories(user_id="user_123")

# Delete by tag
memory_service.delete_memories_by_tag(
    user_id="user_123",
    tag="temporary",
)
```

## Session Configuration Best Practices

### 1. Choose Right Service for Environment

```python
import os

# Development
if os.getenv("ENVIRONMENT") == "development":
    session_service = InMemorySessionService()

# Staging/Production
elif os.getenv("ENVIRONMENT") in ["staging", "production"]:
    session_service = DatabaseSessionService(
        connection_string=os.getenv("DATABASE_URL"),
    )
```

### 2. Implement Session Cleanup

```python
import schedule
import time
from datetime import datetime, timedelta

def cleanup_old_sessions():
    """Delete sessions older than 30 days."""
    cutoff = datetime.now() - timedelta(days=30)

    old_sessions = session_service.list_sessions(
        app_name="my_app",
        before_date=cutoff,
    )

    for session in old_sessions:
        session_service.delete_session(session["session_id"])

    print(f"Deleted {len(old_sessions)} old sessions")

# Schedule cleanup daily
schedule.every().day.at("02:00").do(cleanup_old_sessions)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(3600)
```

### 3. Handle Session Errors

```python
def safe_run(user_input: str, session_id: str):
    """Run with error handling."""
    try:
        response = runner.run(
            user_input=user_input,
            session_id=session_id,
        )
        return response.text

    except SessionNotFoundError:
        # Session expired or deleted - create new one
        logger.warning(f"Session {session_id} not found, creating new session")
        response = runner.run(
            user_input=user_input,
            session_id=session_id,  # Will create new session
        )
        return response.text

    except DatabaseError as e:
        # Database connection issue
        logger.error(f"Database error: {e}")
        return "I'm having trouble accessing your conversation history. Please try again."
```

### 4. Use Session Metadata Effectively

```python
def chat_with_context(user_id: str, message: str, **context):
    """Chat with rich context metadata."""
    session_id = f"{user_id}_session"

    response = runner.run(
        user_input=message,
        session_id=session_id,
        metadata={
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "device": context.get("device", "unknown"),
            "location": context.get("location"),
            "session_start": context.get("session_start"),
            "feature_flags": context.get("feature_flags", []),
        },
    )

    return response.text
```

## Testing Session Management

```python
import pytest
from google.adk.sessions import InMemorySessionService

@pytest.fixture
def session_service():
    """Create session service for testing."""
    return InMemorySessionService()

@pytest.fixture
def runner(session_service):
    """Create runner with session service."""
    agent = LlmAgent(
        name="test_agent",
        model="gemini-2.0-flash-exp",
    )

    return Runner(
        agent=agent,
        app_name="test_app",
        session_service=session_service,
    )

def test_session_persistence(runner):
    """Test that session persists across turns."""
    session_id = "test_session"

    # Turn 1
    response1 = runner.run(
        user_input="My name is Alice",
        session_id=session_id,
    )

    # Turn 2 - agent should remember
    response2 = runner.run(
        user_input="What's my name?",
        session_id=session_id,
    )

    assert "Alice" in response2.text

def test_multiple_sessions(runner):
    """Test isolation between sessions."""
    # Session 1
    runner.run(
        user_input="My favorite color is blue",
        session_id="session_1",
    )

    # Session 2
    response = runner.run(
        user_input="What's my favorite color?",
        session_id="session_2",  # Different session
    )

    # Should not know from different session
    assert "blue" not in response.text.lower()

def test_session_metadata(session_service, runner):
    """Test session metadata storage."""
    session_id = "metadata_test"

    runner.run(
        user_input="Hello",
        session_id=session_id,
        metadata={"user_tier": "premium"},
    )

    session = session_service.get_session(session_id)
    assert session["metadata"]["user_tier"] == "premium"
```

## Performance Optimization

### Connection Pooling

```python
# Configure connection pool for database sessions
session_service = DatabaseSessionService(
    connection_string="postgresql://...",
    pool_size=20,  # Increase for high traffic
    max_overflow=40,
    pool_recycle=3600,  # Recycle connections hourly
)
```

### Session Caching

```python
from functools import lru_cache

class CachedSessionService:
    """Session service with caching layer."""

    def __init__(self, backend_service):
        self.backend = backend_service

    @lru_cache(maxsize=1000)
    def get_session(self, session_id: str):
        """Get session with caching."""
        return self.backend.get_session(session_id)

    def save_session(self, session_id: str, data: dict):
        """Save and invalidate cache."""
        self.get_session.cache_clear()  # Invalidate
        return self.backend.save_session(session_id, data)

# Use cached service
cached_service = CachedSessionService(
    backend_service=DatabaseSessionService(...)
)
```

## Related Skills

- **adk-callback-patterns** - Intercept session operations
- **adk-agent-testing** - Test session persistence
- **adk-multi-agent-orchestrator** - Share sessions across agents
- **adk-memory-manager** - Advanced memory patterns

## Next Steps

1. **Choose session service** - InMemory (dev) or Database (prod)
2. **Add memory service** - For long-term facts
3. **Configure cleanup** - Remove old sessions
4. **Add metadata** - Track context and analytics
5. **Test thoroughly** - Verify persistence works
6. **Monitor performance** - Track database load
