# Session Backends — Cloud SQL, Postgres, Firestore, SQLite, Vertex

Choose a `SessionService` for durable conversation/state. All attach to the
`Runner` via `session_service=`. Verify with Context7 or the local mirror paths
`adk-python-v2.3/src/google/adk/sessions` and `.../integrations/firestore`.

## Install extras

```bash
pip install "google-adk>=2.3.0,<3"
# Database (Postgres/Cloud SQL/MySQL) — SQLAlchemy + an async driver:
pip install "sqlalchemy>=2,<3" asyncpg           # or pg8000 / aiomysql
# Cloud SQL (managed connector):
pip install "cloud-sql-python-connector[asyncpg]"
# Firestore:
pip install "google-cloud-firestore>=2.11,<3"
```

## SQLite (local file, dev/single-node)

```python
from google.adk.sessions import SqliteSessionService

session_service = SqliteSessionService(db_path="./sessions.db")
```

## Postgres

`DatabaseSessionService` is SQLAlchemy-based and async — use an **async** driver
in the URL. One class serves Postgres, MySQL, and SQLite.

```python
from google.adk.sessions import DatabaseSessionService

session_service = DatabaseSessionService(
    db_url="postgresql+asyncpg://user:password@host:5432/ion_sight",
)
```

`db_url` and `db_engine` are mutually exclusive — pass an existing
`sqlalchemy.ext.asyncio.AsyncEngine` via `db_engine=` when you manage pooling.

## Cloud SQL (Postgres) via the Python Connector

Use the Cloud SQL Connector to build an `AsyncEngine`, then hand it to
`DatabaseSessionService(db_engine=...)`:

```python
from google.cloud.sql.connector import Connector, create_async_connector
from sqlalchemy.ext.asyncio import create_async_engine
from google.adk.sessions import DatabaseSessionService

connector = await create_async_connector()

async def getconn():
    return await connector.connect_async(
        "project:region:instance",   # Cloud SQL instance connection name
        "asyncpg",
        user="ion",
        password="…",                # prefer IAM auth / Secret Manager
        db="ion_sight",
    )

engine = create_async_engine("postgresql+asyncpg://", async_creator=getconn)
session_service = DatabaseSessionService(db_engine=engine)
```

Prefer IAM database authentication and pull secrets from Secret Manager — never
hardcode credentials.

## MySQL / Cloud SQL for MySQL

```python
session_service = DatabaseSessionService(
    db_url="mysql+aiomysql://user:password@host:3306/ion_sight",
)
```

## Firestore (serverless, per-user isolation)

```python
from google.cloud import firestore
from google.adk.integrations.firestore import FirestoreSessionService

session_service = FirestoreSessionService(
    client=firestore.AsyncClient(project="ion-sight", database="(default)"),
    root_collection="adk-session",   # default; sessions nested per user
)
```

`FirestoreSessionService` takes an optional `firestore.AsyncClient` (one is
created if omitted) and a `root_collection`. It stores sessions under
`users/{user}/…` with separate app-state and user-state collections.

## Vertex managed sessions

```python
from google.adk.sessions import VertexAiSessionService

session_service = VertexAiSessionService(project="ion-sight", location="us-central1")
```

## Choosing

| Need | Backend |
|------|---------|
| Local dev, tests | `InMemorySessionService` / `SqliteSessionService` |
| Existing relational stack, transactions | `DatabaseSessionService` (Postgres / Cloud SQL) |
| Serverless, per-user isolation, GCP-native | `FirestoreSessionService` |
| Fully managed on Vertex | `VertexAiSessionService` |

Session state is short-lived operational state — long-term recall belongs in a
`MemoryService` (see `references/vector-stores.md`).
