# Session Service Types Reference

Complete reference for all ADK session service types and their specifications.

## Service Comparison Matrix

| Feature | InMemorySessionService | DatabaseSessionService | VertexAiSessionService |
|---------|----------------------|----------------------|----------------------|
| **Persistence** | None (RAM only) | Database (SQL) | Vertex AI managed |
| **Survives Restart** | No | Yes | Yes |
| **Scalability** | Single instance | Horizontal (with shared DB) | Fully managed |
| **Setup Complexity** | Zero config | Database required | GCP project required |
| **Cost** | Free | Database hosting | Vertex AI pricing |
| **Best For** | Development/Testing | Production (self-hosted) | Production (cloud) |
| **Concurrency** | Single process | Multi-process/container | Fully distributed |
| **Backup** | None | Database backups | Automatic |
| **Query Capability** | Limited | Full SQL | Managed API |

## InMemorySessionService

### API Reference

```python
from google.adk.sessions import InMemorySessionService

class InMemorySessionService:
    """In-memory session storage for development."""

    def __init__(self):
        """Initialize in-memory storage."""
        pass

    def create_session(
        self,
        session_id: str,
        app_name: str,
        agent_name: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a new session.

        Args:
            session_id: Unique session identifier
            app_name: Application name
            agent_name: Agent name
            metadata: Optional metadata dict

        Returns:
            Session object
        """
        pass

    def get_session(self, session_id: str) -> dict:
        """Retrieve session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data dict

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        pass

    def update_session(
        self,
        session_id: str,
        conversation_history: list,
    ) -> None:
        """Update session conversation history.

        Args:
            session_id: Session identifier
            conversation_history: Updated conversation turns
        """
        pass

    def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: Session identifier
        """
        pass

    def list_sessions(
        self,
        app_name: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> List[dict]:
        """List all sessions.

        Args:
            app_name: Filter by app name (optional)
            agent_name: Filter by agent name (optional)

        Returns:
            List of session dicts
        """
        pass
```

### Session Data Structure

```python
{
    "session_id": "user_123_session_1",
    "app_name": "my_app",
    "agent_name": "assistant",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "conversation_history": [
        {
            "role": "user",
            "content": "Hello",
            "timestamp": "2024-01-15T10:30:00Z",
        },
        {
            "role": "assistant",
            "content": "Hi! How can I help?",
            "timestamp": "2024-01-15T10:30:05Z",
            "tool_calls": [],
        },
    ],
    "metadata": {
        "user_id": "user_123",
        "device": "web",
    }
}
```

### Memory Limitations

```python
# Calculate approximate memory usage
import sys

def estimate_session_memory(session: dict) -> int:
    """Estimate memory usage in bytes."""
    # Rough calculation
    history_size = len(str(session["conversation_history"]))
    metadata_size = len(str(session.get("metadata", {})))

    return history_size + metadata_size + 1000  # +1KB overhead

# Example: 1000 sessions with 10 turns each
# ~10KB per session = 10MB total
# Manageable for development, not for production
```

### Best Practices

```python
# Good: Development and testing
service = InMemorySessionService()
runner = Runner(agent=agent, session_service=service)

# Bad: Production use (sessions lost on restart)
# Don't use InMemorySessionService in production!
```

## DatabaseSessionService

### API Reference

```python
from google.adk.sessions import DatabaseSessionService

class DatabaseSessionService:
    """Database-backed session storage."""

    def __init__(
        self,
        connection_string: str,
        table_name: str = "agent_sessions",
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        auto_create_table: bool = True,
    ):
        """Initialize database session service.

        Args:
            connection_string: SQLAlchemy connection string
                Examples:
                - PostgreSQL: "postgresql://user:pass@host:5432/dbname"
                - MySQL: "mysql://user:pass@host:3306/dbname"
                - SQLite: "sqlite:///path/to/database.db"
            table_name: Database table name for sessions
            pool_size: Connection pool size
            max_overflow: Max overflow connections beyond pool_size
            pool_timeout: Timeout for getting connection from pool (seconds)
            pool_recycle: Recycle connections after N seconds
            auto_create_table: Create table if not exists
        """
        pass
```

### Connection String Formats

| Database | Format | Example |
|----------|--------|---------|
| **PostgreSQL** | `postgresql://user:pass@host:port/db` | `postgresql://admin:secret@db.example.com:5432/agents` |
| **MySQL** | `mysql://user:pass@host:port/db` | `mysql://root:pass@localhost:3306/agentdb` |
| **SQLite** | `sqlite:///path/to/file.db` | `sqlite:///./sessions.db` |
| **PostgreSQL (async)** | `postgresql+asyncpg://...` | `postgresql+asyncpg://user:pass@host/db` |

### Database Schema

```sql
-- PostgreSQL schema
CREATE TABLE agent_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    app_name VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    conversation_history JSONB NOT NULL,
    metadata JSONB,

    INDEX idx_app_agent (app_name, agent_name),
    INDEX idx_updated (updated_at),
    INDEX idx_created (created_at)
);

-- MySQL schema
CREATE TABLE agent_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    app_name VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    conversation_history JSON NOT NULL,
    metadata JSON,

    INDEX idx_app_agent (app_name, agent_name),
    INDEX idx_updated (updated_at),
    INDEX idx_created (created_at)
);

-- SQLite schema
CREATE TABLE agent_sessions (
    session_id TEXT PRIMARY KEY,
    app_name TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    conversation_history TEXT NOT NULL,  -- JSON string
    metadata TEXT  -- JSON string
);

CREATE INDEX idx_app_agent ON agent_sessions(app_name, agent_name);
CREATE INDEX idx_updated ON agent_sessions(updated_at);
CREATE INDEX idx_created ON agent_sessions(created_at);
```

### Connection Pool Configuration

```python
# Development (low traffic)
service = DatabaseSessionService(
    connection_string="postgresql://...",
    pool_size=5,
    max_overflow=10,
)

# Production (high traffic)
service = DatabaseSessionService(
    connection_string="postgresql://...",
    pool_size=20,  # Larger pool
    max_overflow=40,
    pool_timeout=60,
    pool_recycle=1800,  # 30 minutes
)

# Connection pool monitoring
print(f"Pool size: {service.engine.pool.size()}")
print(f"Checked out: {service.engine.pool.checkedout()}")
```

### Query Examples

```python
# List recent sessions
recent_sessions = service.list_sessions(
    app_name="my_app",
    limit=10,
    order_by="updated_at DESC",
)

# Find sessions by metadata
premium_sessions = service.list_sessions(
    app_name="my_app",
    metadata_filter={"user_tier": "premium"},
)

# Delete old sessions
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=30)
old_sessions = service.list_sessions(
    app_name="my_app",
    before_date=cutoff,
)

for session in old_sessions:
    service.delete_session(session["session_id"])
```

### Migration Scripts

```python
# Migrate from InMemory to Database
def migrate_to_database(
    in_memory_service: InMemorySessionService,
    db_service: DatabaseSessionService,
):
    """Migrate sessions from in-memory to database."""
    sessions = in_memory_service.list_sessions()

    for session in sessions:
        db_service.create_session(
            session_id=session["session_id"],
            app_name=session["app_name"],
            agent_name=session["agent_name"],
            metadata=session.get("metadata"),
        )

        db_service.update_session(
            session_id=session["session_id"],
            conversation_history=session["conversation_history"],
        )

    print(f"Migrated {len(sessions)} sessions")
```

## VertexAiSessionService

### API Reference

```python
from google.adk.sessions import VertexAiSessionService

class VertexAiSessionService:
    """Vertex AI managed session storage."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        credentials: Optional[Any] = None,
    ):
        """Initialize Vertex AI session service.

        Args:
            project_id: GCP project ID
            location: GCP region (e.g., "us-central1", "europe-west1")
            credentials: Optional GCP credentials (uses default if None)
        """
        pass
```

### Setup Requirements

1. **Enable Vertex AI API:**

```bash
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
```

2. **Create Service Account:**

```bash
gcloud iam service-accounts create agent-sessions \
    --display-name="Agent Session Service"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:agent-sessions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

3. **Download Credentials:**

```bash
gcloud iam service-accounts keys create credentials.json \
    --iam-account=agent-sessions@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

4. **Use in Code:**

```python
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

service = VertexAiSessionService(
    project_id="your-project-id",
    location="us-central1",
)
```

### Pricing

Vertex AI Session Service pricing (example rates):

| Operation | Cost |
|-----------|------|
| **Session storage** | $0.01 per GB-month |
| **Read operations** | $0.0001 per request |
| **Write operations** | $0.0002 per request |

Estimate: 10,000 active sessions, 100KB each, 1M requests/month:
- Storage: 1GB × $0.01 = $0.01/month
- Requests: 1M × $0.00015 avg = $150/month

### Regional Availability

Available regions:
- `us-central1` (Iowa)
- `us-east1` (South Carolina)
- `us-west1` (Oregon)
- `europe-west1` (Belgium)
- `europe-west4` (Netherlands)
- `asia-east1` (Taiwan)
- `asia-northeast1` (Tokyo)

Choose region closest to users for lower latency.

## Session Service Selection Guide

### Choose InMemorySessionService if:
- ✅ Development or testing only
- ✅ Short-lived sessions acceptable
- ✅ Single-instance deployment
- ❌ NOT for production

### Choose DatabaseSessionService if:
- ✅ Production use
- ✅ Self-hosted infrastructure preferred
- ✅ Existing database infrastructure
- ✅ Full control over data
- ✅ Cost-sensitive (database already paid for)

### Choose VertexAiSessionService if:
- ✅ Production use
- ✅ Cloud-native deployment
- ✅ Want fully managed service
- ✅ Don't want database maintenance
- ✅ Need automatic scaling
- ❌ Higher cost vs self-hosted

## Performance Benchmarks

| Service | Read Latency | Write Latency | Throughput |
|---------|--------------|---------------|------------|
| InMemory | <1ms | <1ms | 10,000+ ops/sec |
| Database (local) | 2-5ms | 5-10ms | 1,000+ ops/sec |
| Database (remote) | 10-50ms | 20-100ms | 500+ ops/sec |
| VertexAI | 50-200ms | 100-300ms | Unlimited (scales) |

*Note: Latencies approximate, vary by configuration and network*

## Session Lifecycle

```
┌─────────────┐
│   Created   │  session_service.create_session()
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Active    │  runner.run() → auto-updates session
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Idle      │  No activity for period
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Archived   │  Moved to cold storage (optional)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Deleted   │  session_service.delete_session()
└─────────────┘
```

## Advanced Patterns

### Session Sharding

For very high scale, shard sessions across multiple databases:

```python
import hashlib

class ShardedSessionService:
    """Session service with database sharding."""

    def __init__(self, shard_count: int = 4):
        self.shards = [
            DatabaseSessionService(
                connection_string=f"postgresql://...db{i}"
            )
            for i in range(shard_count)
        ]

    def _get_shard(self, session_id: str) -> DatabaseSessionService:
        """Determine shard for session ID."""
        shard_index = int(hashlib.md5(session_id.encode()).hexdigest(), 16) % len(self.shards)
        return self.shards[shard_index]

    def get_session(self, session_id: str):
        """Get session from correct shard."""
        shard = self._get_shard(session_id)
        return shard.get_session(session_id)

    # Implement other methods similarly
```

### Session Replication

Replicate sessions across regions for disaster recovery:

```python
class ReplicatedSessionService:
    """Session service with cross-region replication."""

    def __init__(self):
        self.primary = DatabaseSessionService(
            connection_string="postgresql://us-east-db/..."
        )
        self.replica = DatabaseSessionService(
            connection_string="postgresql://eu-west-db/..."
        )

    def create_session(self, **kwargs):
        """Create session in primary and replica."""
        session = self.primary.create_session(**kwargs)

        # Async replicate to backup region
        import threading
        threading.Thread(
            target=self.replica.create_session,
            kwargs=kwargs,
        ).start()

        return session
```

## Related Documentation

- SQLAlchemy Connection Strings: https://docs.sqlalchemy.org/en/20/core/engines.html
- Vertex AI Sessions API: https://cloud.google.com/vertex-ai/docs
- PostgreSQL JSON Functions: https://www.postgresql.org/docs/current/functions-json.html
