---
name: ADK Production Deployment
description: This skill should be used when the user asks to "deploy an agent", "production deployment", "cloud run deployment", "vertex AI deployment", or "containerize an agent". Provides comprehensive guidance for deploying agents to production environments including Cloud Run, Vertex AI, and Kubernetes.
version: 1.0.0
---

# ADK Production Deployment

Deploy built agents to production environments. This skill covers containerization, deployment to Cloud Run, Vertex AI Agent Engine, and Kubernetes orchestration.

## Deployment Targets

### Cloud Run (Recommended for Most Cases)

Serverless deployment, pay-per-use, automatic scaling:

**Pros:**
- No infrastructure management
- Automatic scaling
- Cost-effective
- Easy deployment

**Cons:**
- Cold start latency (mitigated with min instances)
- 60 minute timeout limit
- Not ideal for long-running tasks

### Vertex AI Agent Engine

Google's managed agent platform with full ADK integration:

**Pros:**
- Full ADK support
- Integrated monitoring
- Agent memory and tools
- Multi-agent orchestration

**Cons:**
- Google Cloud only
- More structured approach
- Higher cost for some use cases

### Kubernetes (GKE)

Full container orchestration for complex deployments:

**Pros:**
- Complete control
- Multi-region support
- Advanced orchestration
- Horizontal scaling

**Cons:**
- Higher operational complexity
- More infrastructure management
- Steeper learning curve

## Containerization with Docker

### Dockerfile for ADK Agent

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run agent
CMD ["python", "-m", "agent_service"]
```

### Build and Test Locally

```bash
# Build image
docker build -t my-agent:latest .

# Run locally
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  -e PINECONE_API_KEY=$PINECONE_API_KEY \
  my-agent:latest

# Test
curl http://localhost:8000/health
```

### Push to Container Registry

```bash
# Tag for registry
docker tag my-agent:latest gcr.io/my-project/my-agent:latest

# Push to Google Container Registry
docker push gcr.io/my-project/my-agent:latest
```

## Deploy to Cloud Run

### Using Cloud Console

1. Go to Cloud Run
2. Click "Create Service"
3. Select container image from registry
4. Configure memory and CPU
5. Set environment variables
6. Click "Create"

### Using gcloud CLI

```bash
gcloud run deploy my-agent \
  --image gcr.io/my-project/my-agent:latest \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars GOOGLE_API_KEY=$GOOGLE_API_KEY,PINECONE_API_KEY=$PINECONE_API_KEY \
  --allow-unauthenticated
```

### API Endpoint

```python
import requests

AGENT_URL = "https://my-agent-xxx.a.run.app"

response = requests.post(
    f"{AGENT_URL}/ask",
    json={"prompt": "Analyze market trends"}
)

print(response.json())
```

## Deploy to Vertex AI

### Create Agent in Vertex AI

```bash
# Initialize Vertex AI
gcloud init

# Deploy using ADK
python -m adk_bidi.deployment.vertex_ai \
  --agent-name my-agent \
  --agent-file my_agent.py \
  --project my-project \
  --region us-central1
```

### Configure Agent Tools

```python
from adk_bidi.deployment import VertexAIAgent

agent = VertexAIAgent(
    name="my-agent",
    description="My production agent",
    tools=[
        google_search_tool,
        database_query_tool,
        api_integration_tool
    ]
)

agent.deploy()
```

### Use Deployed Agent

```python
from google.cloud import aiplatform

# Get agent
agent = aiplatform.Agent.load("projects/my-project/locations/us-central1/agents/my-agent-id")

# Use agent
response = agent.query(input="Analyze sales data")
print(response)
```

## Deploy to Kubernetes (GKE)

### Create Kubernetes Deployment

```yaml
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
        image: gcr.io/my-project/my-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: google-api-key
        - name: PINECONE_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: pinecone-api-key
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
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: my-agent-service
spec:
  selector:
    app: my-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Deploy to GKE

```bash
# Create cluster
gcloud container clusters create my-cluster \
  --zone us-central1-a \
  --num-nodes 3

# Apply deployment
kubectl apply -f deployment.yaml

# Create secrets
kubectl create secret generic agent-secrets \
  --from-literal=google-api-key=$GOOGLE_API_KEY \
  --from-literal=pinecone-api-key=$PINECONE_API_KEY

# Check deployment
kubectl get pods
kubectl get services
```

## Monitoring & Logging

### Application Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_request(request):
    logger.info(f"Request received: {request}")
    try:
        result = agent.ask(request)
        logger.info(f"Request processed successfully")
        return result
    except Exception as e:
        logger.error(f"Request failed: {e}")
        raise
```

### Health Checks

```python
from fastapi import FastAPI

app = FastAPI()
agent = MyAgent()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    # Check if agent is ready
    return {"ready": agent.is_ready()}

@app.get("/metrics")
async def metrics():
    return {
        "requests_processed": agent.request_count,
        "errors": agent.error_count,
        "average_response_time": agent.avg_response_time
    }
```

### Cloud Logging

View logs in Cloud Console:

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Filter by severity
gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR"
```

## Scaling

### Automatic Scaling (Cloud Run)

Configured in deployment:
```bash
--max-instances 100
--min-instances 1
```

### Manual Scaling (Kubernetes)

```bash
# Scale deployment
kubectl scale deployment my-agent --replicas 5

# Or use HorizontalPodAutoscaler
kubectl autoscale deployment my-agent --min=2 --max=10 --cpu-percent=80
```

## Security Best Practices

**Do:**
- Use Cloud Secrets Manager for credentials
- Enable authentication/authorization
- Use HTTPS/TLS
- Implement rate limiting
- Log and monitor access
- Keep dependencies updated
- Use least privilege IAM roles

**Don't:**
- Store credentials in environment files
- Disable authentication for production
- Expose debug endpoints publicly
- Trust user input without validation
- Skip security updates
- Log sensitive data

## Deployment Checklist

Before deploying:

- [ ] Agent tested locally
- [ ] Dockerfile builds successfully
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Health checks implemented
- [ ] Error handling complete
- [ ] Logging configured
- [ ] Rate limiting setup
- [ ] Authentication configured
- [ ] Performance tested
- [ ] Rollback plan ready
- [ ] Monitoring setup

## Supporting Resources

### References
- **`references/cloud-run-guide.md`** - Cloud Run deployment details
- **`references/kubernetes-guide.md`** - Kubernetes deployment patterns
- **`references/vertex-ai-guide.md`** - Vertex AI Agent Engine setup

### Examples
- **`examples/cloudrun-deployment.sh`** - Cloud Run deployment script
- **`examples/kubernetes-manifest.yaml`** - K8s deployment manifest
- **`examples/agent-service.py`** - Production agent service

## Next Steps

1. **Choose deployment target** - Cloud Run, Vertex AI, or Kubernetes?
2. **Containerize agent** - Create Dockerfile
3. **Test container** - Run locally and verify
4. **Deploy** - Push to chosen platform
5. **Monitor** - Set up logging and alerts
6. **Iterate** - Update and redeploy as needed

See **adk-custom-agent-builder** skill for agent implementation.
