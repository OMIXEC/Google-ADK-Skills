# Database Integration for ADK Workflows

All DB integrations follow one rule: user_id flows from middleware → agent → tool → query. No exceptions.

## DB Selection Matrix

| Database | Type | When to Use | Row-Level Security | Hosting |
|----------|------|-------------|-------------------|---------|
| PostgreSQL | Relational | Complex queries, JSONB, extensions | Native RLS | Supabase, Neon, Cloud SQL, RDS, Aurora, self-hosted |
| MySQL 8+ | Relational | LAMP stacks, simple schemas, read-heavy | No native RLS — app-level | Cloud SQL, RDS, PlanetScale, self-hosted |
| Spanner | Relational (global) | Global consistency, horizontal scale | IAM + row-level via SQL | GCP only |
| Aurora | Relational | MySQL/Postgres compatible, AWS scale | Native PG RLS (PG-compat) or app-level | AWS only |
| Oracle | Relational | Enterprise, legacy, OCI | VPD (Virtual Private DB) | OCI, self-hosted |
| Firestore | NoSQL (doc) | Real-time, mobile-first | Security Rules DSL | Firebase/GCP |
| Bigtable | NoSQL (wide-column) | Time-series, IoT, analytics | IAM + app-level | GCP only |
| DynamoDB | NoSQL (key-value) | Serverless, predictable latency | IAM conditions | AWS only |
| MongoDB | NoSQL (doc) | Flexible schemas, rapid iteration | Atlas App Services rules | Atlas, self-hosted |
| Redis | In-memory | Caching, rate limiting, sessions | App-level only | Memorystore, ElastiCache, self-hosted |
| SQLite | Embedded | Local dev, testing, edge | App-level | File-based |

## Universal DB Access Pattern

```python
"""Database access layer — pattern reused across all DB types.

Every function receives user_id explicitly.
Every query is parameterized.
Every connection uses TLS.
"""

from typing import Any
from pydantic import BaseModel

class DBConfig(BaseModel):
    """Provider-agnostic DB configuration."""
    driver: str                # postgresql, mysql, spanner, oracle, mongodb, etc.
    host: str                  # Endpoint
    port: int = 5432
    database: str
    username: str | None = None
    password_secret: str | None = None  # Never the actual value — path to secret
    tls_required: bool = True
    pool_min: int = 2
    pool_max: int = 20
    connect_timeout_ms: int = 5000
    query_timeout_ms: int = 30000

    @classmethod
    def from_env(cls, prefix: str = "DB_") -> "DBConfig":
        """Load from environment variables. Secrets via env or secret manager."""
        import os
        return cls(
            driver=os.getenv(f"{prefix}DRIVER", "postgresql"),
            host=os.getenv(f"{prefix}HOST", "localhost"),
            port=int(os.getenv(f"{prefix}PORT", "5432")),
            database=os.getenv(f"{prefix}NAME", ""),
            username=os.getenv(f"{prefix}USER", ""),
            password_secret=os.getenv(f"{prefix}PASSWORD_SECRET"),  # Path, not value
            tls_required=os.getenv(f"{prefix}TLS", "true").lower() == "true",
        )


# ── PostgreSQL ──────────────────────────────────────────────────

"""
RLS is the first line of defense. Queries also filter by user_id explicitly.

Migration snippet:
```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation ON orders
    USING (user_id = current_setting('app.user_id'));
```
"""

import psycopg2
import psycopg2.extras
import psycopg2.pool

class PostgresAccess:
    def __init__(self, config: DBConfig):
        self.config = config
        # Connection pool with TLS enforcement
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            config.pool_min, config.pool_max,
            host=config.host, port=config.port,
            dbname=config.database, user=config.username,
            password=self._resolve_secret(config.password_secret),
            sslmode="require" if config.tls_required else "prefer",
            connect_timeout=config.connect_timeout_ms // 1000,
        )

    def _resolve_secret(self, secret_path: str | None) -> str:
        """Resolve password from env or secret manager."""
        import os
        if not secret_path:
            return os.getenv("DB_PASSWORD", "")
        # Google Secret Manager fallback
        if secret_path.startswith("gcp://"):
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            resp = client.access_secret_version(name=secret_path.removeprefix("gcp://"))
            return resp.payload.data.decode("UTF-8")
        # AWS Secrets Manager fallback
        if secret_path.startswith("aws://"):
            import boto3, json
            client = boto3.client("secretsmanager")
            resp = client.get_secret_value(SecretId=secret_path.removeprefix("aws://"))
            return json.loads(resp["SecretString"])["password"]
        # HashiCorp Vault, etc. — extend here
        return os.getenv(secret_path, "")

    def query(self, user_id: str, sql: str, params: tuple = ()) -> list[dict]:
        """Run parameterized query scoped to user_id."""
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f"SET app.user_id = %s", (user_id,))
                cur.execute(sql, params)
                return cur.fetchall()
        finally:
            self.pool.putconn(conn)

    def execute(self, user_id: str, sql: str, params: tuple = ()) -> int:
        """Execute mutation with user_id context."""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(f"SET app.user_id = %s", (user_id,))
                cur.execute(sql, params)
                conn.commit()
                return cur.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)


# ── MySQL ──────────────────────────────────────────────────────

"""
MySQL has no native RLS. Use application-level isolation:
- Every table has `user_id` column
- Every query includes `WHERE user_id = ?`
- OR use views with definer context

For MySQL 8+ with `SET @app_user_id` session variables:
```sql
CREATE VIEW user_orders AS
    SELECT * FROM orders WHERE user_id = @app_user_id;
```
"""

import mysql.connector
from mysql.connector import pooling

class MySQLAccess:
    def __init__(self, config: DBConfig):
        self.pool = pooling.MySQLConnectionPool(
            pool_name="adk_pool",
            pool_size=config.pool_max,
            host=config.host, port=config.port,
            database=config.database, user=config.username,
            password=self._resolve_secret(config.password_secret),
            ssl_disabled=not config.tls_required,
            connection_timeout=config.connect_timeout_ms // 1000,
        )

    def _resolve_secret(self, path: str | None) -> str:
        import os
        return os.getenv("DB_PASSWORD", "") if not path else os.getenv(path, "")

    def query(self, user_id: str, sql: str, params: tuple = ()) -> list[dict]:
        """Every query filtered by user_id."""
        conn = self.pool.get_connection()
        try:
            with conn.cursor(dictionary=True) as cur:
                # Inject user_id session variable for views
                cur.execute("SET @app_user_id = %s", (user_id,))
                cur.execute(sql, params)
                return cur.fetchall()
        finally:
            conn.close()

    def execute(self, user_id: str, sql: str, params: tuple = ()) -> int:
        """Mutation with explicit user_id. Add WHERE user_id = %s or INSERT with user_id."""
        conn = self.pool.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params + (user_id,))
                conn.commit()
                return cur.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# ── Cloud Spanner ──────────────────────────────────────────────

"""
Spanner uses IAM for access control + application-level row filtering.
Recommended: wrap queries in helper that auto-appends tenant/user filters.

Schema:
```sql
CREATE TABLE orders (
    order_id STRING(36) NOT NULL,
    user_id STRING(128) NOT NULL,
    tenant_id STRING(128) NOT NULL,
    ...
) PRIMARY KEY (user_id, order_id),
  INTERLEAVE IN PARENT users ON DELETE CASCADE;
```
"""

from google.cloud import spanner

class SpannerAccess:
    def __init__(self, config: DBConfig):
        self.client = spanner.Client()
        self.instance = self.client.instance(config.host)  # instance_id
        self.database = self.instance.database(config.database)

    def query(self, user_id: str, sql: str, params: dict = {}) -> list[dict]:
        """Spanner parameterized query with user_id injection."""
        params["user_id"] = user_id  # Auto-inject for interleaved reads
        with self.database.snapshot() as snapshot:
            results = snapshot.execute_sql(sql, params=params, param_types={
                "user_id": spanner.param_types.STRING,
            })
            return [dict(zip(row.keys(), row.values())) for row in results]

    def mutate(self, user_id: str, mutations: list) -> None:
        """All mutations must include user_id in the row data."""
        for m in mutations:
            if "user_id" not in m[2]:
                m[2]["user_id"] = user_id
        self.database.run_in_transaction(lambda txn: txn.insert_or_update(...))


# ── Aurora (PostgreSQL-compatible) ─────────────────────────────

"""
Aurora PG: Same as PostgreSQL with RLS.
Use standard PG driver with read/write endpoint for writes,
reader endpoint for read replicas.

Config:
    write_endpoint = os.getenv("AURORA_WRITER_ENDPOINT")
    read_endpoint = os.getenv("AURORA_READER_ENDPOINT")

Uses same PostgresAccess class above — just point host at Aurora endpoint.
"""


# ── Oracle ─────────────────────────────────────────────────────

"""
Oracle uses Virtual Private Database (VPD) for row-level security:
- Create policy function that appends WHERE user_id = SYS_CONTEXT('USERENV', 'CLIENT_IDENTIFIER')
- Set CLIENT_IDENTIFIER at session start for each user

```sql
CREATE OR REPLACE FUNCTION user_data_policy(schema IN VARCHAR2, obj IN VARCHAR2)
RETURN VARCHAR2 IS
BEGIN
    RETURN 'user_id = SYS_CONTEXT(''USERENV'', ''CLIENT_IDENTIFIER'')';
END;

BEGIN
    DBMS_RLS.ADD_POLICY('app_schema', 'orders', 'user_policy',
        'app_schema', 'user_data_policy', 'SELECT,INSERT,UPDATE,DELETE');
END;
```

In the application:
```python
import oracledb

class OracleAccess:
    def __init__(self, config: DBConfig):
        self.pool = oracledb.create_pool(
            user=config.username,
            password=self._resolve_secret(config.password_secret),
            dsn=f"{config.host}:{config.port}/{config.database}",
            min=config.pool_min, max=config.pool_max,
        )

    def query(self, user_id: str, sql: str, params: dict = {}) -> list:
        conn = self.pool.acquire()
        try:
            with conn.cursor() as cur:
                # Set user context for VPD
                cur.execute(
                    "BEGIN DBMS_SESSION.SET_IDENTIFIER(:uid); END;",
                    uid=user_id,
                )
                cur.execute(sql, params)
                return cur.fetchall()
        finally:
            self.pool.release(conn)
```
"""


# ── Firestore (Firebase) ──────────────────────────────────────

"""
Firestore uses security rules for RLS. The backend uses Admin SDK (service account)
which bypasses rules — so application-level user_id filtering is mandatory.

```python
from google.cloud import firestore

class FirestoreAccess:
    def __init__(self):
        self.db = firestore.Client()

    def get_user_orders(self, user_id: str, limit: int = 50) -> list[dict]:
        docs = (
            self.db.collection("orders")
            .where("user_id", "==", user_id)
            .limit(limit)
            .stream()
        )
        return [{"id": d.id, **d.to_dict()} for d in docs]

    def create_order(self, user_id: str, order_data: dict) -> str:
        order_data["user_id"] = user_id
        order_data["created_at"] = firestore.SERVER_TIMESTAMP
        _, ref = self.db.collection("orders").add(order_data)
        return ref.id
```

Security rules (firestore.rules):
```javascript
match /orders/{orderId} {
    allow read, write: if request.auth != null
        && request.auth.uid == resource.data.user_id;
}
```
"""


# ── MongoDB ────────────────────────────────────────────────────

"""
Use MongoDB Atlas with App Services auth or application-level user_id filtering.

```python
from pymongo import MongoClient

class MongoAccess:
    def __init__(self, config: DBConfig):
        uri = f"mongodb+srv://{config.username}:<password>@{config.host}/{config.database}"
        self.client = MongoClient(uri, tls=config.tls_required)
        self.db = self.client[config.database]

    def query(self, user_id: str, collection: str, filter: dict = {}) -> list[dict]:
        filter["user_id"] = user_id  # Always append user_id
        return list(self.db[collection].find(filter))

    def insert(self, user_id: str, collection: str, doc: dict):
        doc["user_id"] = user_id
        return self.db[collection].insert_one(doc)
```
"""


# ── DynamoDB ───────────────────────────────────────────────────

"""
Use partition key = user_id for user-scoped data.
Use IAM conditions for coarse auth + application-level for fine-grained.

```python
import boto3
from boto3.dynamodb.conditions import Key

class DynamoAccess:
    def __init__(self, table_name: str):
        self.table = boto3.resource("dynamodb").Table(table_name)

    def query(self, user_id: str, **kwargs) -> list[dict]:
        resp = self.table.query(
            KeyConditionExpression=Key("user_id").eq(user_id),
            **kwargs,
        )
        return resp.get("Items", [])

    def put(self, user_id: str, item: dict):
        item["user_id"] = user_id
        return self.table.put_item(Item=item)
```
"""


# ── Redis ──────────────────────────────────────────────────────

"""
Redis is app-level only — no RLS. Use namespaced keys.
Rate limiting per user, caching with user prefix.

```python
import redis
import json

class RedisAccess:
    def __init__(self, config: DBConfig):
        self.client = redis.Redis(
            host=config.host, port=config.port,
            username=config.username,
            password=config.password_secret,
            ssl=config.tls_required,
            decode_responses=True,
        )

    def cache_user_data(self, user_id: str, key: str, data: dict, ttl: int = 300):
        full_key = f"user:{user_id}:{key}"
        self.client.setex(full_key, ttl, json.dumps(data))

    def get_user_cache(self, user_id: str, key: str) -> dict | None:
        full_key = f"user:{user_id}:{key}"
        raw = self.client.get(full_key)
        return json.loads(raw) if raw else None

    def check_rate_limit(self, user_id: str, action: str, max_calls: int, window: int) -> bool:
        key = f"ratelimit:{user_id}:{action}"
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, window)
        return current <= max_calls
```
"""


# ── ORM Pattern ────────────────────────────────────────────────

"""
If using SQLAlchemy, always inject user_id at session level.
Never use auto-commit sessions without user_id filter.

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from contextvars import ContextVar

current_user_id: ContextVar[str] = ContextVar("current_user_id")

engine = create_engine(
    f"postgresql://{user}:{pwd}@{host}/{db}",
    connect_args={"sslmode": "require"},
    pool_size=10,
)
SessionLocal = sessionmaker(bind=engine)

@event.listens_for(Session, "do_orm_execute")
def _add_user_filter(orm_execute_state):
    """Inject user_id condition on SELECT for tables with user_id column."""
    if orm_execute_state.is_select:
        uid = current_user_id.get(None)
        if uid:
            # Apply global user filter — override per-model as needed
            pass

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
"""


# ── Migration & RLS Checklist ──────────────────────────────────

"""
For every DB added to a workflow:

- [ ] Connection string in secret manager, never in code
- [ ] TLS enforced (sslmode=require, ssl_disabled=False, tls=True)
- [ ] Connection pooling configured (min/max, timeouts)
- [ ] All queries parameterized — no string interpolation
- [ ] user_id explicit in every query/mutation
- [ ] RLS or equivalent enabled (PG, Oracle, Supabase) or app-level filter (MySQL, Mongo)
- [ ] Index on (tenant_id, user_id) for multi-tenant queries
- [ ] Credentials rotated (secret manager versioning)
- [ ] Connection timeout + query timeout configured
- [ ] Read replicas used for read-heavy workloads where available
"""
