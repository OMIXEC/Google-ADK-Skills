---
name: ADK Agent Lifecycle Management
description: This skill should be used when the user asks to "create new agent project", "deploy agent", "manage agent lifecycle", "agent development workflow", "initialize ADK project", "configure agent", "monitor agent performance", "debug agent", or "agent DevOps". Provides complete agent development lifecycle from initialization to production deployment and monitoring.
version: 1.0.0
---

# ADK Agent Lifecycle Management

Complete guide to the agent development lifecycle: from project initialization through development, testing, deployment, and ongoing monitoring and iteration.

## Lifecycle Overview

The agent development lifecycle follows six key phases:

```
┌──────────┐     ┌─────────┐     ┌──────┐     ┌────────┐     ┌─────────┐     ┌─────────┐
│   Init   │────▶│ Develop │────▶│ Test │────▶│ Deploy │────▶│ Monitor │────▶│ Iterate │
└──────────┘     └─────────┘     └──────┘     └────────┘     └─────────┘     └─────────┘
     │                                                                              │
     └──────────────────────────────────────────────────────────────────────────────┘
```

| Phase | Focus | Duration | Key Activities |
|-------|-------|----------|----------------|
| **Init** | Project setup | Hours | Scaffolding, dependencies, configuration |
| **Develop** | Agent creation | Days-Weeks | Tools, prompts, integrations |
| **Test** | Quality assurance | Days | Unit, integration, evaluation |
| **Deploy** | Production release | Hours-Days | Containerization, cloud deployment |
| **Monitor** | Performance tracking | Ongoing | Logs, metrics, alerts |
| **Iterate** | Continuous improvement | Ongoing | Feedback, refinement, updates |

## Phase 1: Initialize

Set up a new ADK agent project from scratch.

### Quick Start

```bash
# Create new project
/adk:init --name my-agent --type basic

# Or use specific template
/adk:init --name customer-support --template chat-agent
/adk:init --name research-assistant --template rag-agent
/adk:init --name workflow-agent --template multi-agent
```

### Manual Project Setup

If you prefer manual setup:

```bash
# Create project directory
mkdir my-agent && cd my-agent

# Initialize Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install ADK
pip install google-adk

# Create basic structure
mkdir -p {src,tests,config,data}
touch src/agent.py
touch config/config.yaml
touch requirements.txt
```

### Project Structure

After initialization, your project should look like:

```
my-agent/
├── src/
│   ├── agent.py           # Main agent definition
│   ├── tools/             # Custom tools
│   │   ├── __init__.py
│   │   └── search.py
│   ├── prompts/           # Prompt templates
│   │   └── system.py
│   └── handlers/          # Response handlers
│       └── parser.py
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Test fixtures
├── config/
│   ├── config.yaml        # Main configuration
│   ├── dev.yaml           # Development config
│   └── prod.yaml          # Production config
├── data/                  # Data files (if needed)
├── .env.example           # Environment template
├── .gitignore
├── requirements.txt       # Python dependencies
└── README.md
```

### Configuration Setup

Create `config/config.yaml`:

```yaml
agent:
  name: my-agent
  model: gemini-1.5-flash
  temperature: 0.7
  max_tokens: 2048

tools:
  enabled:
    - search
    - calculator
    - file_reader

memory:
  type: in_memory
  max_history: 10

safety:
  enable_guardrails: true
  content_filtering: strict
```

### Environment Variables

Create `.env` (never commit this!):

```bash
# Google Cloud
GOOGLE_API_KEY=your-api-key-here
GOOGLE_PROJECT_ID=your-project-id

# Optional integrations
PINECONE_API_KEY=your-pinecone-key
OPENAI_API_KEY=your-openai-key

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Dependencies

Create `requirements.txt`:

```txt
# Core
google-adk>=0.1.0
python-dotenv>=1.0.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Optional integrations
pinecone-client>=2.2.0
langchain>=0.1.0
```

### Commands

```bash
# Initialize new project
/adk:init --name <project-name> [--template <template>] [--type <type>]

# Check environment status
/adk:status

# Install dependencies
/adk:setup
```

## Phase 2: Develop

Build your agent with tools, prompts, and integrations.

### Create Basic Agent

```python
# src/agent.py
from adk import Agent
from src.tools import search_tool, calculator_tool
from src.prompts import get_system_prompt

def create_agent():
    """Create and configure the agent."""

    agent = Agent(
        name="my-agent",
        model="gemini-1.5-flash",
        system_prompt=get_system_prompt(),
        tools=[
            search_tool,
            calculator_tool,
        ],
        temperature=0.7,
    )

    return agent

if __name__ == "__main__":
    agent = create_agent()
    print(f"Agent '{agent.name}' created successfully!")
```

### Add Custom Tools

```python
# src/tools/search.py
from adk.tools import tool

@tool(
    name="search_database",
    description="Search the knowledge database for information"
)
def search_tool(query: str, limit: int = 5):
    """
    Search for information in the database.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of search results
    """
    # Implement your search logic
    results = perform_search(query, limit)
    return results
```

### Define System Prompts

```python
# src/prompts/system.py
def get_system_prompt(role: str = "assistant") -> str:
    """Generate system prompt for the agent."""

    return f"""
    You are a helpful AI {role} powered by Google's ADK.

    Your capabilities:
    - Search and retrieve information
    - Perform calculations
    - Provide clear, accurate responses

    Guidelines:
    - Be helpful and professional
    - Ask clarifying questions when needed
    - Cite sources when available
    - Acknowledge limitations

    Always prioritize user safety and provide accurate information.
    """
```

### Configuration Management

```python
# src/config.py
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Agent configuration manager."""

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self.load_config(config_path)

    def load_config(self, path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(path) as f:
            return yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

# Usage
config = Config()
model = config.get('agent.model', 'gemini-1.5-flash')
```

### Commands

```bash
# Configure agent settings
/adk:config --set agent.model=gemini-1.5-pro
/adk:config --get agent.temperature

# Add tool integration
/adk:add-tool --name search --type custom
/adk:add-tool --name weather --type api --url https://api.weather.com

# Generate boilerplate code
/adk:generate tool --name custom_tool
/adk:generate handler --name response_parser
```

## Phase 3: Test

Validate agent behavior and quality.

### Local Testing

```bash
# Quick test with adk run
adk run --input "What can you do?"

# Interactive testing
adk web

# Start API server for integration tests
adk api_server
```

### Automated Testing

```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v --timeout=60

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run evaluation
python -m evaluation.run_benchmark
```

### Test Examples

See **adk-agent-testing** skill for comprehensive testing patterns.

### Commands

```bash
# Run all tests
/adk:test

# Run specific test type
/adk:test --type unit
/adk:test --type integration
/adk:test --type evaluation

# Generate test coverage report
/adk:test --coverage
```

## Phase 4: Deploy

Deploy agent to production environment.

### Containerization

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Expose port
EXPOSE 8080

# Run agent
CMD ["python", "-m", "adk", "api_server", "--host", "0.0.0.0", "--port", "8080"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  agent:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - ENVIRONMENT=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Local Docker Testing

```bash
# Build image
docker build -t my-agent:latest .

# Run locally
docker run -p 8080:8080 \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  my-agent:latest

# Test health endpoint
curl http://localhost:8080/health

# Using docker-compose
docker-compose up -d
docker-compose logs -f
```

### Cloud Deployment

**Google Cloud Run:**

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/my-agent

# Deploy to Cloud Run
gcloud run deploy my-agent \
  --image gcr.io/PROJECT_ID/my-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY

# Get service URL
gcloud run services describe my-agent --region us-central1 --format 'value(status.url)'
```

**Kubernetes:**

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-agent
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
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: google-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Commands

```bash
# Build container
/adk:build --tag my-agent:latest

# Deploy to Cloud Run
/adk:deploy --platform cloudrun --project PROJECT_ID

# Deploy to Kubernetes
/adk:deploy --platform k8s --namespace production

# Check deployment status
/adk:deploy-status
```

## Phase 5: Monitor

Track performance and detect issues in production.

### Logging Setup

```python
# src/logging_config.py
import logging
import sys
from google.cloud import logging as cloud_logging

def setup_logging(environment: str = "development"):
    """Configure logging for the agent."""

    if environment == "production":
        # Use Cloud Logging
        client = cloud_logging.Client()
        client.setup_logging()
    else:
        # Use console logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('logs/agent.log'),
            ]
        )

    return logging.getLogger(__name__)

# Usage in agent
logger = setup_logging(os.getenv('ENVIRONMENT', 'development'))

def create_agent():
    logger.info("Creating agent...")
    agent = Agent(...)
    logger.info(f"Agent '{agent.name}' created successfully")
    return agent
```

### Metrics Tracking

```python
# src/metrics.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class AgentMetrics:
    """Track agent performance metrics."""

    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_latency: float = 0.0
    total_tokens: int = 0

    def record_request(
        self,
        success: bool,
        latency: float,
        tokens: int,
        error: Optional[str] = None
    ):
        """Record a single request."""
        self.request_count += 1

        if success:
            self.success_count += 1
        else:
            self.error_count += 1

        self.total_latency += latency
        self.total_tokens += tokens

        if error:
            logger.error(f"Request error: {error}")

    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            "total_requests": self.request_count,
            "success_rate": self.success_count / self.request_count if self.request_count > 0 else 0,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "avg_latency": self.total_latency / self.request_count if self.request_count > 0 else 0,
            "avg_tokens": self.total_tokens / self.request_count if self.request_count > 0 else 0,
        }
```

### Health Checks

```python
# src/health.py
from fastapi import FastAPI, Response
import time

app = FastAPI()
start_time = time.time()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    uptime = time.time() - start_time

    return {
        "status": "healthy",
        "uptime_seconds": uptime,
        "version": "1.0.0",
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # Check if agent is ready to serve requests
    try:
        agent = get_agent()
        if agent:
            return {"status": "ready"}
    except Exception as e:
        return Response(
            content={"status": "not ready", "error": str(e)},
            status_code=503
        )
```

### View Logs

```bash
# Local logs
tail -f logs/agent.log

# Cloud Logging
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=my-agent" --limit 50

# Kubernetes logs
kubectl logs -f deployment/my-agent -n production

# Docker logs
docker logs -f my-agent
```

### Commands

```bash
# View agent logs
/adk:logs --tail 100
/adk:logs --filter "level=ERROR" --since 1h

# Get performance metrics
/adk:metrics --period 24h

# View health status
/adk:health
```

## Phase 6: Iterate

Continuously improve based on feedback and monitoring.

### Feedback Collection

```python
# src/feedback.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class UserFeedback:
    """User feedback on agent response."""

    session_id: str
    message_id: str
    rating: int  # 1-5
    comment: Optional[str] = None
    category: Optional[str] = None  # helpful/unhelpful/incorrect/etc

def collect_feedback(feedback: UserFeedback):
    """Store user feedback for analysis."""
    # Store in database or analytics system
    logger.info(f"Feedback collected: {feedback.rating}/5 - {feedback.comment}")

    # Trigger alerts for low ratings
    if feedback.rating <= 2:
        alert_team(f"Low rating received: {feedback}")
```

### Performance Analysis

```python
# scripts/analyze_performance.py
import pandas as pd
from datetime import datetime, timedelta

def analyze_last_week():
    """Analyze agent performance over last week."""

    # Load logs/metrics
    df = load_metrics(days=7)

    analysis = {
        "total_requests": len(df),
        "success_rate": (df['success'] == True).mean(),
        "avg_latency": df['latency'].mean(),
        "p95_latency": df['latency'].quantile(0.95),
        "avg_tokens": df['tokens'].mean(),
        "peak_hour": df.groupby(df['timestamp'].dt.hour)['request_id'].count().idxmax(),
    }

    # Identify issues
    errors = df[df['success'] == False]
    if len(errors) > 0:
        analysis["top_errors"] = errors.groupby('error_type').size().nlargest(5).to_dict()

    # User satisfaction
    feedback = load_feedback(days=7)
    if len(feedback) > 0:
        analysis["avg_rating"] = feedback['rating'].mean()
        analysis["feedback_count"] = len(feedback)

    return analysis
```

### A/B Testing Updates

```python
# Test new configurations
def run_ab_test(variant_a_config, variant_b_config, sample_size=100):
    """Run A/B test on configuration changes."""

    from adk.testing import ABTest

    agent_a = create_agent(config=variant_a_config)
    agent_b = create_agent(config=variant_b_config)

    test = ABTest(
        variant_a=agent_a,
        variant_b=agent_b,
        test_cases=load_test_cases(sample_size),
    )

    results = test.run()

    if results.b_win_rate > results.a_win_rate and results.p_value < 0.05:
        logger.info("Variant B is significantly better - recommend deployment")
    else:
        logger.info("No significant improvement - keep current version")

    return results
```

### Gradual Rollout

```yaml
# k8s/canary-deployment.yaml
apiVersion: v1
kind: Service
metadata:
  name: my-agent
spec:
  selector:
    app: my-agent
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-agent-v1
spec:
  replicas: 9  # 90% of traffic
  selector:
    matchLabels:
      app: my-agent
      version: v1
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-agent-v2
spec:
  replicas: 1  # 10% of traffic (canary)
  selector:
    matchLabels:
      app: my-agent
      version: v2
```

### Commands

```bash
# Analyze performance
/adk:analyze --period 7d

# Collect feedback
/adk:feedback --export feedback.json

# Run A/B test
/adk:ab-test --variant-a config_a.yaml --variant-b config_b.yaml --sample 100

# Deploy canary
/adk:deploy --strategy canary --percentage 10
```

## Best Practices

### Development

1. **Use version control** - Commit early and often
2. **Follow project structure** - Keep code organized
3. **Document as you go** - Add docstrings and comments
4. **Test locally first** - Use `adk run` and `adk web` before deploying

### Configuration

1. **Never commit secrets** - Use `.env` files and environment variables
2. **Use config files** - Separate dev/staging/prod configurations
3. **Validate configs** - Check settings before deployment
4. **Document settings** - Explain what each config option does

### Testing

1. **Test at all levels** - Unit, integration, and evaluation tests
2. **Automate tests** - Run in CI/CD pipeline
3. **Track metrics** - Monitor test results over time
4. **Regression test** - Prevent quality degradation

### Deployment

1. **Use containers** - Docker for consistency across environments
2. **Implement health checks** - Enable automatic recovery
3. **Gradual rollout** - Start with canary deployments
4. **Have rollback plan** - Be able to revert quickly

### Monitoring

1. **Log everything** - Requests, errors, performance
2. **Set up alerts** - Get notified of issues immediately
3. **Track KPIs** - Success rate, latency, user satisfaction
4. **Review regularly** - Weekly/monthly performance reviews

### Iteration

1. **Collect feedback** - From users and monitoring
2. **Prioritize improvements** - Focus on high-impact changes
3. **Test changes** - A/B test before full deployment
4. **Measure impact** - Verify improvements with metrics

## Troubleshooting

### Common Issues

**Agent not responding:**
```bash
# Check status
/adk:status

# Check logs
/adk:logs --tail 50 --filter "level=ERROR"

# Verify configuration
/adk:config --validate
```

**Performance degradation:**
```bash
# Check metrics
/adk:metrics --period 24h

# Profile slow requests
/adk:profile --sample 100

# Check resource usage
kubectl top pods -n production  # For K8s
```

**Deployment failures:**
```bash
# Check build logs
docker build . 2>&1 | tee build.log

# Verify environment
/adk:status --deployment

# Check health endpoint
curl http://your-agent-url/health
```

## Related Skills

- **adk-agent-testing** - Comprehensive testing patterns
- **adk-production-deployment** - Advanced deployment strategies
- **adk-quick-start** - Quick start templates
- **adk-integration-tools** - Tool integration patterns

## Quick Reference

```bash
# Lifecycle commands
/adk:init --name <project>        # Initialize new project
/adk:config --set <key>=<value>   # Configure agent
/adk:test                         # Run tests
/adk:build                        # Build container
/adk:deploy                       # Deploy to production
/adk:logs                         # View logs
/adk:metrics                      # Get performance metrics
/adk:analyze                      # Analyze performance
/adk:status                       # Check status

# ADK commands
adk run                           # Quick local test
adk web                           # Interactive testing
adk api_server                    # Start API server
```

## Next Steps

1. **Initialize project** with `/adk:init`
2. **Develop agent** with tools and prompts
3. **Test locally** with `adk run` and `adk web`
4. **Write automated tests** following adk-agent-testing patterns
5. **Deploy to staging** for further testing
6. **Monitor performance** and collect feedback
7. **Iterate and improve** based on data
