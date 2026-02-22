# ADK Deployment Configurations

Comprehensive deployment configurations for Google ADK agents on Cloud Run, Vertex AI Agent Engine, and GKE.

## Cloud Run Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Cloud Run Service YAML

```yaml
# deployment/cloud_run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: adk-agent
  labels:
    app: adk-agent
    environment: production
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "10"
        autoscaling.knative.dev/target: "80"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
        - image: gcr.io/PROJECT_ID/adk-agent:latest
          ports:
            - name: http1
              containerPort: 8080
          env:
            - name: GOOGLE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: google-api-key
                  key: latest
            - name: ENVIRONMENT
              value: "production"
          resources:
            limits:
              memory: "2Gi"
              cpu: "2"
```

### Cloud Build Configuration

```yaml
# cloudbuild.yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/adk-agent:$COMMIT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/adk-agent:latest'
      - '.'

  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/adk-agent:$COMMIT_SHA'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'gcr.io/$PROJECT_ID/adk-agent:latest'

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'adk-agent'
      - '--image'
      - 'gcr.io/$PROJECT_ID/adk-agent:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-env-vars'
      - 'ENVIRONMENT=production'
      - '--set-secrets'
      - 'GOOGLE_API_KEY=google-api-key:latest'

images:
  - 'gcr.io/$PROJECT_ID/adk-agent:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/adk-agent:latest'

options:
  machineType: 'N1_HIGHCPU_8'
```

### Deploy Script

```bash
#!/bin/bash
# deploy-cloud-run.sh

PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="adk-agent"

# Build and push Docker image
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets GOOGLE_API_KEY=google-api-key:latest
```

## Vertex AI Agent Engine

### Agent Configuration

```python
# src/agent_engine_config.py
from google.cloud import aiplatform
from google.adk.agents import Agent

# Initialize Vertex AI
aiplatform.init(
    project="your-project-id",
    location="us-central1",
)

# Deploy agent to Agent Engine
def deploy_to_agent_engine(agent: Agent):
    """Deploy agent to Vertex AI Agent Engine."""
    from google.cloud.aiplatform import AgentEngine

    engine = AgentEngine.create(
        display_name="adk-agent",
        agent=agent,
        serving_config={
            "min_replica_count": 1,
            "max_replica_count": 10,
            "machine_type": "n1-standard-4",
        },
    )

    print(f"Agent deployed: {engine.resource_name}")
    return engine
```

### Agent Engine YAML

```yaml
# deployment/agent_engine.yaml
apiVersion: aiplatform.googleapis.com/v1
kind: AgentDeployment
metadata:
  name: adk-agent
  namespace: production
spec:
  agent:
    source:
      containerImage: gcr.io/PROJECT_ID/adk-agent:latest
  servingConfig:
    minReplicaCount: 1
    maxReplicaCount: 10
    machineType: n1-standard-4
    acceleratorType: NVIDIA_TESLA_T4
    acceleratorCount: 1
  environment:
    variables:
      - name: GOOGLE_API_KEY
        valueFrom:
          secretKeyRef:
            name: google-api-key
            key: latest
```

## GKE (Google Kubernetes Engine)

### Kubernetes Deployment

```yaml
# deployment/k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adk-agent
  namespace: production
  labels:
    app: adk-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: adk-agent
  template:
    metadata:
      labels:
        app: adk-agent
    spec:
      containers:
      - name: adk-agent
        image: gcr.io/PROJECT_ID/adk-agent:latest
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: google-api-key
              key: api-key
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: adk-agent-service
  namespace: production
spec:
  type: LoadBalancer
  selector:
    app: adk-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: adk-agent-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: adk-agent
  minReplicas: 2
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

### GKE Deploy Script

```bash
#!/bin/bash
# deploy-gke.sh

PROJECT_ID="your-project-id"
CLUSTER_NAME="adk-cluster"
REGION="us-central1"

# Create GKE cluster (if needed)
gcloud container clusters create $CLUSTER_NAME \
  --region $REGION \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10

# Get cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region $REGION

# Create namespace
kubectl create namespace production

# Create secret
kubectl create secret generic google-api-key \
  --from-literal=api-key=$GOOGLE_API_KEY \
  --namespace production

# Build and push image
docker build -t gcr.io/$PROJECT_ID/adk-agent:latest .
docker push gcr.io/$PROJECT_ID/adk-agent:latest

# Deploy to GKE
kubectl apply -f deployment/k8s-deployment.yaml

# Check deployment
kubectl get pods -n production
kubectl get services -n production
```

## Local Development

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  adk-agent:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - ENVIRONMENT=development
    volumes:
      - ./src:/app/src
    restart: unless-stopped

  # Optional: PostgreSQL for testing
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=adk_dev
      - POSTGRES_USER=dev
      - POSTGRES_PASSWORD=dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Local Run Script

```bash
#!/bin/bash
# run-local.sh

# Load environment variables
export $(cat .env | xargs)

# Run with uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

## Environment Configuration

### .env.example

```bash
# Google Cloud
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CLOUD_PROJECT=your-project-id

# Deployment
ENVIRONMENT=development
PORT=8080

# RAG (optional)
RAG_CORPUS_NAME=projects/123/locations/us-central1/corpora/456

# MCP Servers (optional)
BRAVE_API_KEY=your_brave_api_key
GITHUB_TOKEN=your_github_token
PINECONE_API_KEY=your_pinecone_api_key

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

### requirements.txt

```txt
# Core ADK
google-genai-adk>=0.1.0
google-cloud-aiplatform>=1.40.0

# Web framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Optional: RAG
vertexai>=1.40.0

# Optional: Pinecone
pinecone-client>=3.0.0

# Optional: MCP
mcp>=0.1.0

# Optional: LangGraph
langgraph>=0.1.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.0.0
requests>=2.31.0
```

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  SERVICE_NAME: adk-agent
  REGION: us-central1

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}

      - name: Configure Docker
        run: gcloud auth configure-docker

      - name: Build Docker image
        run: |
          docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA .
          docker tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

      - name: Push Docker image
        run: |
          docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA
          docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy $SERVICE_NAME \
            --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA \
            --region $REGION \
            --platform managed \
            --allow-unauthenticated \
            --memory 2Gi \
            --cpu 2 \
            --set-secrets GOOGLE_API_KEY=google-api-key:latest
```

## Monitoring & Logging

### Health Check Endpoint

```python
# src/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "adk-agent",
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check():
    # Check dependencies (database, APIs, etc.)
    return {"status": "ready"}
```

### Cloud Logging

```python
# src/logging_config.py
import logging
from google.cloud import logging as cloud_logging

# Set up Cloud Logging
client = cloud_logging.Client()
client.setup_logging()

# Use standard logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Log structured data
logger.info("Agent started", extra={
    "service": "adk-agent",
    "version": "1.0.0"
})
```

## Security Best Practices

### Secret Management

```bash
# Create secret in Google Secret Manager
gcloud secrets create google-api-key \
  --data-file=- <<< "$GOOGLE_API_KEY"

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding google-api-key \
  --member=serviceAccount:SERVICE_ACCOUNT_EMAIL \
  --role=roles/secretmanager.secretAccessor
```

### IAM Roles

```bash
# Service account for Cloud Run
gcloud iam service-accounts create adk-agent-sa \
  --display-name="ADK Agent Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:adk-agent-sa@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/aiplatform.user

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:adk-agent-sa@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

## Related Files

- @agent-patterns.md - Agent architecture patterns
- @tool-catalog.md - Tool integration patterns
- @streaming-patterns.md - Real-time streaming configurations
