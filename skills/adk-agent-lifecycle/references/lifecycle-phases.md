# ADK Agent Lifecycle Phases - Detailed Reference

Deep dive into each phase of the agent development lifecycle with patterns, examples, and best practices.

## Phase 1: Initialize - Project Scaffolding

### Goals

- Set up development environment
- Create project structure
- Configure dependencies
- Establish development workflow

### Project Templates

#### Basic Chat Agent

```bash
/adk:init --name chat-agent --template basic

# Creates:
chat-agent/
├── src/
│   └── agent.py              # Simple conversational agent
├── config/
│   └── config.yaml
├── tests/
│   └── test_basic.py
└── requirements.txt
```

**Use cases:** Simple Q&A, customer support, general assistance

#### RAG Agent

```bash
/adk:init --name rag-agent --template rag

# Creates:
rag-agent/
├── src/
│   ├── agent.py              # Agent with RAG
│   ├── tools/
│   │   ├── retrieval.py      # Document retrieval
│   │   └── embedding.py      # Embedding generation
│   └── knowledge/
│       └── loader.py         # Document loading
├── data/
│   └── documents/            # Knowledge base
└── config/
    ├── config.yaml
    └── rag_config.yaml       # RAG-specific settings
```

**Use cases:** Documentation Q&A, knowledge retrieval, research assistance

#### Multi-Agent System

```bash
/adk:init --name multi-agent --template multi-agent

# Creates:
multi-agent/
├── src/
│   ├── orchestrator.py       # Main orchestrator
│   ├── agents/
│   │   ├── researcher.py     # Research specialist
│   │   ├── analyst.py        # Analysis specialist
│   │   └── writer.py         # Writing specialist
│   └── coordination/
│       └── handoff.py        # Agent coordination
└── config/
    └── agents_config.yaml    # Per-agent configuration
```

**Use cases:** Complex workflows, specialized tasks, team collaboration

#### API Integration Agent

```bash
/adk:init --name api-agent --template api-integration

# Creates:
api-agent/
├── src/
│   ├── agent.py
│   ├── tools/
│   │   ├── api_client.py     # API wrapper
│   │   └── auth.py           # Authentication
│   └── schemas/
│       └── api_models.py     # API response models
└── config/
    └── api_config.yaml       # API endpoints and keys
```

**Use cases:** External service integration, data aggregation, workflow automation

### Environment Setup Patterns

#### Development Environment

```bash
# .env.development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
GOOGLE_API_KEY=dev-api-key
ENABLE_DEBUG_TOOLS=true

# Use faster, cheaper models for development
MODEL=gemini-1.5-flash
TEMPERATURE=0.7

# Local services
DATABASE_URL=sqlite:///dev.db
CACHE_BACKEND=memory
```

#### Staging Environment

```bash
# .env.staging
ENVIRONMENT=staging
LOG_LEVEL=INFO
GOOGLE_API_KEY=staging-api-key
ENABLE_DEBUG_TOOLS=false

# Production-like models
MODEL=gemini-1.5-pro
TEMPERATURE=0.5

# Staging services
DATABASE_URL=postgresql://staging-db
CACHE_BACKEND=redis://staging-redis
```

#### Production Environment

```bash
# .env.production
ENVIRONMENT=production
LOG_LEVEL=WARNING
GOOGLE_API_KEY=prod-api-key
ENABLE_DEBUG_TOOLS=false

# Production models
MODEL=gemini-1.5-pro
TEMPERATURE=0.3

# Production services
DATABASE_URL=postgresql://prod-db
CACHE_BACKEND=redis://prod-redis

# Monitoring
SENTRY_DSN=https://...
DATADOG_API_KEY=...
```

### Dependency Management

#### Core Dependencies

```txt
# requirements.txt - Core dependencies
google-adk>=0.1.0
python-dotenv>=1.0.0
pyyaml>=6.0
pydantic>=2.0.0
```

#### Development Dependencies

```txt
# requirements-dev.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
pre-commit>=3.0.0
```

#### Optional Dependencies

```txt
# requirements-optional.txt

# Vector databases
pinecone-client>=2.2.0
chromadb>=0.3.0
qdrant-client>=1.0.0

# Integrations
langchain>=0.1.0
llama-index>=0.9.0

# Monitoring
sentry-sdk>=1.40.0
datadog>=0.47.0
```

### Git Setup

```bash
# .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Environment
.env
.env.*
!.env.example

# Data
data/local/
*.db
*.sqlite

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp

# Testing
.coverage
htmlcov/
.pytest_cache/

# Build
dist/
build/
*.egg-info/
```

## Phase 2: Develop - Agent Creation

### Tool Development Patterns

#### Simple Function Tool

```python
from adk.tools import tool

@tool(
    name="calculate",
    description="Perform basic arithmetic calculations"
)
def calculator(expression: str) -> float:
    """
    Evaluate a mathematical expression.

    Args:
        expression: Math expression like "2 + 2" or "10 * 5"

    Returns:
        Result of the calculation
    """
    try:
        # Safe evaluation (in production, use a proper math parser)
        result = eval(expression)
        return float(result)
    except Exception as e:
        return f"Error: {str(e)}"
```

#### API Integration Tool

```python
import requests
from typing import List, Dict
from adk.tools import tool

@tool(
    name="search_web",
    description="Search the web for current information"
)
def web_search(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Search the web using an external API.

    Args:
        query: Search query
        limit: Maximum results to return

    Returns:
        List of search results with title, url, snippet
    """
    api_key = os.getenv("SEARCH_API_KEY")

    try:
        response = requests.get(
            "https://api.search.com/search",
            params={"q": query, "limit": limit},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        response.raise_for_status()

        results = response.json()["results"]

        return [
            {
                "title": r["title"],
                "url": r["url"],
                "snippet": r["snippet"],
            }
            for r in results[:limit]
        ]

    except requests.RequestException as e:
        logger.error(f"Search API error: {e}")
        return []
```

#### Database Tool

```python
from typing import List, Dict, Optional
from adk.tools import tool
import sqlite3

@tool(
    name="query_database",
    description="Query the product database"
)
def query_products(
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
) -> List[Dict]:
    """
    Search products in the database.

    Args:
        category: Filter by category
        price_min: Minimum price
        price_max: Maximum price

    Returns:
        List of matching products
    """
    conn = sqlite3.connect("data/products.db")
    cursor = conn.cursor()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if price_min is not None:
        query += " AND price >= ?"
        params.append(price_min)

    if price_max is not None:
        query += " AND price <= ?"
        params.append(price_max)

    cursor.execute(query, params)

    results = [
        {
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "price": row[3],
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return results
```

### Prompt Engineering

#### System Prompt Template

```python
def build_system_prompt(
    role: str,
    capabilities: List[str],
    constraints: List[str],
    examples: Optional[List[str]] = None,
) -> str:
    """Build dynamic system prompt."""

    prompt = f"You are a {role}.\n\n"

    # Capabilities
    prompt += "Your capabilities include:\n"
    for cap in capabilities:
        prompt += f"- {cap}\n"

    prompt += "\n"

    # Constraints
    prompt += "Important constraints:\n"
    for constraint in constraints:
        prompt += f"- {constraint}\n"

    # Examples
    if examples:
        prompt += "\n"
        prompt += "Examples of good responses:\n"
        for example in examples:
            prompt += f"\n{example}\n"

    return prompt

# Usage
system_prompt = build_system_prompt(
    role="customer support specialist",
    capabilities=[
        "Answer product questions",
        "Process returns and refunds",
        "Escalate complex issues",
    ],
    constraints=[
        "Always be polite and professional",
        "Never share personal customer data",
        "Escalate billing issues to human agents",
    ],
    examples=[
        "User: 'Where is my order?'\nAssistant: 'I'll help you track your order. Could you provide your order number?'"
    ]
)
```

#### Context Injection

```python
def build_user_context(
    user_id: str,
    preferences: Dict[str, Any],
    history: List[str],
) -> str:
    """Build user-specific context."""

    context = f"User ID: {user_id}\n\n"

    # User preferences
    if preferences:
        context += "User preferences:\n"
        for key, value in preferences.items():
            context += f"- {key}: {value}\n"

    # Recent history
    if history:
        context += "\n"
        context += "Recent conversation:\n"
        for msg in history[-5:]:  # Last 5 messages
            context += f"{msg}\n"

    return context
```

### Memory Management

#### In-Memory Conversation History

```python
from typing import List, Dict
from collections import deque

class ConversationMemory:
    """Manage conversation history."""

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.history = deque(maxlen=max_turns * 2)  # user + assistant per turn

    def add_user_message(self, message: str):
        """Add user message to history."""
        self.history.append({
            "role": "user",
            "content": message,
        })

    def add_assistant_message(self, message: str):
        """Add assistant message to history."""
        self.history.append({
            "role": "assistant",
            "content": message,
        })

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return list(self.history)

    def clear(self):
        """Clear conversation history."""
        self.history.clear()
```

#### Persistent Memory with Database

```python
import sqlite3
from datetime import datetime

class PersistentMemory:
    """Store conversation in database."""

    def __init__(self, db_path: str = "data/conversations.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def save_message(self, session_id: str, role: str, content: str):
        """Save message to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )

        conn.commit()
        conn.close()

    def get_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve conversation history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role, content, timestamp
            FROM conversations
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (session_id, limit)
        )

        history = [
            {
                "role": row[0],
                "content": row[1],
                "timestamp": row[2],
            }
            for row in cursor.fetchall()
        ]

        conn.close()
        return list(reversed(history))  # Chronological order
```

## Phase 3: Test - Quality Assurance

See **adk-agent-testing** skill for comprehensive patterns.

### Quick Testing Workflow

```bash
# 1. Quick smoke test
adk run --input "test query"

# 2. Interactive multi-turn testing
adk web

# 3. Run unit tests
pytest tests/unit/ -v

# 4. Run integration tests
pytest tests/integration/ -v

# 5. Run evaluation
python -m evaluation.run_benchmark
```

## Phase 4: Deploy - Production Release

### Deployment Checklist

```markdown
## Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Configuration validated
- [ ] Secrets properly managed (never in code)
- [ ] Environment variables set
- [ ] Health checks implemented
- [ ] Logging configured
- [ ] Monitoring set up
- [ ] Rollback plan documented
- [ ] Load testing completed (if high traffic expected)

## Deployment Steps

1. [ ] Build container image
2. [ ] Push to container registry
3. [ ] Deploy to staging
4. [ ] Run smoke tests on staging
5. [ ] Deploy to production (canary if possible)
6. [ ] Monitor for errors
7. [ ] Verify health checks
8. [ ] Check metrics dashboard
9. [ ] Update documentation
10. [ ] Notify team of deployment
```

### Cloud Run Deployment (Detailed)

```bash
#!/bin/bash
# deploy-cloudrun.sh

set -e

PROJECT_ID="your-project-id"
SERVICE_NAME="my-agent"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Building container image..."
docker build -t ${IMAGE_NAME}:latest .

echo "Pushing to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets GOOGLE_API_KEY=google-api-key:latest

echo "Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --format 'value(status.url)')

echo "Service deployed at: ${SERVICE_URL}"

echo "Running health check..."
curl ${SERVICE_URL}/health

echo "Deployment complete!"
```

### Kubernetes Deployment (Detailed)

```yaml
# k8s/complete-deployment.yaml
---
# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: agents

---
# Secret
apiVersion: v1
kind: Secret
metadata:
  name: agent-secrets
  namespace: agents
type: Opaque
stringData:
  google-api-key: YOUR_API_KEY_HERE

---
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: agent-config
  namespace: agents
data:
  config.yaml: |
    agent:
      name: my-agent
      model: gemini-1.5-pro
      temperature: 0.5

---
# Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-agent
  namespace: agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-agent
  template:
    metadata:
      labels:
        app: my-agent
    spec:
      containers:
      - name: agent
        image: gcr.io/PROJECT_ID/my-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: google-api-key
        volumeMounts:
        - name: config
          mountPath: /app/config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: agent-config

---
# Service
apiVersion: v1
kind: Service
metadata:
  name: my-agent-service
  namespace: agents
spec:
  selector:
    app: my-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer

---
# HorizontalPodAutoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-agent-hpa
  namespace: agents
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-agent
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Phase 5: Monitor - Performance Tracking

### Monitoring Stack Setup

#### Prometheus Metrics

```python
# src/metrics_prometheus.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
request_count = Counter(
    'agent_requests_total',
    'Total agent requests',
    ['status', 'endpoint']
)

request_duration = Histogram(
    'agent_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint']
)

active_sessions = Gauge(
    'agent_active_sessions',
    'Number of active sessions'
)

token_usage = Counter(
    'agent_tokens_total',
    'Total tokens used',
    ['type']  # input/output
)

# Usage in agent
def handle_request(request):
    start_time = time.time()

    try:
        response = agent.process(request)
        request_count.labels(status='success', endpoint='/chat').inc()
        token_usage.labels(type='input').inc(response.input_tokens)
        token_usage.labels(type='output').inc(response.output_tokens)
        return response

    except Exception as e:
        request_count.labels(status='error', endpoint='/chat').inc()
        raise

    finally:
        duration = time.time() - start_time
        request_duration.labels(endpoint='/chat').observe(duration)
```

#### Structured Logging

```python
# src/structured_logging.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    """JSON structured logging for better querying."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_request(
        self,
        session_id: str,
        message: str,
        response: str,
        latency: float,
        tokens: int,
        success: bool,
    ):
        """Log structured request data."""

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "agent_request",
            "session_id": session_id,
            "message_length": len(message),
            "response_length": len(response),
            "latency_ms": latency * 1000,
            "tokens": tokens,
            "success": success,
        }

        self.logger.info(json.dumps(log_entry))

    def log_error(
        self,
        error_type: str,
        error_message: str,
        session_id: str = None,
        context: dict = None,
    ):
        """Log structured error data."""

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "error",
            "error_type": error_type,
            "error_message": error_message,
            "session_id": session_id,
            "context": context or {},
        }

        self.logger.error(json.dumps(log_entry))
```

## Phase 6: Iterate - Continuous Improvement

### Feedback Loop

```python
# src/feedback_loop.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

@dataclass
class ImprovementOpportunity:
    """Identified improvement opportunity."""

    category: str  # accuracy, speed, user_satisfaction
    description: str
    evidence: List[str]  # Supporting data
    priority: str  # high, medium, low
    suggested_fix: Optional[str] = None

class FeedbackAnalyzer:
    """Analyze feedback to identify improvements."""

    def analyze_period(self, days: int = 7) -> List[ImprovementOpportunity]:
        """Analyze feedback from last N days."""

        opportunities = []

        # Load feedback
        feedback = self.load_feedback(days=days)
        metrics = self.load_metrics(days=days)

        # Accuracy issues
        low_ratings = [f for f in feedback if f.rating <= 2]
        if len(low_ratings) / len(feedback) > 0.1:  # >10% low ratings
            opportunities.append(ImprovementOpportunity(
                category="accuracy",
                description="High rate of low user ratings",
                evidence=[f.comment for f in low_ratings if f.comment],
                priority="high",
                suggested_fix="Review low-rated responses, improve prompt or add tools"
            ))

        # Speed issues
        p95_latency = metrics['p95_latency']
        if p95_latency > 3.0:  # >3 seconds
            opportunities.append(ImprovementOpportunity(
                category="speed",
                description=f"P95 latency high: {p95_latency:.2f}s",
                evidence=["Latency metrics above threshold"],
                priority="medium",
                suggested_fix="Consider using faster model or caching"
            ))

        # Error rate
        error_rate = metrics['error_rate']
        if error_rate > 0.05:  # >5% errors
            opportunities.append(ImprovementOpportunity(
                category="reliability",
                description=f"Error rate high: {error_rate:.1%}",
                evidence=metrics.get('top_errors', []),
                priority="high",
                suggested_fix="Investigate and fix top error causes"
            ))

        return opportunities
```

### Version Management

```python
# src/version.py
from dataclasses import dataclass
from typing import Dict, Any
import json

@dataclass
class AgentVersion:
    """Agent version metadata."""

    version: str
    model: str
    config: Dict[str, Any]
    deployed_at: str
    metrics: Dict[str, float]

class VersionManager:
    """Manage agent versions."""

    def __init__(self, versions_file: str = "data/versions.json"):
        self.versions_file = versions_file
        self.versions = self.load_versions()

    def load_versions(self) -> List[AgentVersion]:
        """Load version history."""
        try:
            with open(self.versions_file) as f:
                data = json.load(f)
                return [AgentVersion(**v) for v in data]
        except FileNotFoundError:
            return []

    def register_version(self, version: AgentVersion):
        """Register new version."""
        self.versions.append(version)
        self.save_versions()

    def compare_versions(self, v1: str, v2: str) -> Dict[str, Any]:
        """Compare two versions."""

        version_1 = next(v for v in self.versions if v.version == v1)
        version_2 = next(v for v in self.versions if v.version == v2)

        return {
            "model_change": version_1.model != version_2.model,
            "config_changes": self.diff_configs(version_1.config, version_2.config),
            "metric_improvements": {
                metric: version_2.metrics.get(metric, 0) - version_1.metrics.get(metric, 0)
                for metric in version_1.metrics.keys()
            }
        }
```

## Best Practices Summary

### DO

- Start with simple templates
- Test locally before deploying
- Use environment-specific configs
- Implement comprehensive logging
- Monitor metrics from day 1
- Collect and act on feedback
- Version all changes
- Document as you go

### DON'T

- Hardcode secrets in code
- Skip testing phases
- Deploy without health checks
- Ignore monitoring alerts
- Make untracked changes
- Deploy directly to production
- Neglect documentation
- Forget to version configs

## Related Resources

- **ADK Documentation**: https://cloud.google.com/adk/docs
- **Google Cloud Run**: https://cloud.google.com/run/docs
- **Kubernetes**: https://kubernetes.io/docs
- **Docker**: https://docs.docker.com
