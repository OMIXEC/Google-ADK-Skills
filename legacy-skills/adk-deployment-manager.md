# adk-deployment-manager

**Production Deployment for Google ADK Agents**

Deploy ADK agents to Cloud Run, Vertex AI Agent Engine, or GKE. Generate Docker containers, deployment configurations, and CI/CD pipelines.

## When to Use

Use this skill when:
- Deploying agent to production
- Setting up CI/CD for agents
- Configuring Cloud Run, Agent Engine, or GKE
- Generating Dockerfiles and deployment configs

## Quick Start

```bash
# Deploy to Cloud Run
/adk-deployment-manager --target "cloud-run" --project "my-project"

# Deploy to Agent Engine
/adk-deployment-manager --target "agent-engine" --project "my-project"

# Deploy to GKE
/adk-deployment-manager --target "gke" --cluster "my-cluster"

# Generate deployment configs only
/adk-deployment-manager --target "cloud-run" --generate_only
```

## Parameters

```bash
--target "cloud-run|agent-engine|gke|local"  # Required
--project "gcp_project_id"                    # GCP project
--region "us-central1"                        # Region (default: us-central1)
--cluster "cluster_name"                      # For GKE
--memory "2Gi"                                # Memory limit
--cpu "2"                                     # CPU limit
--min_instances 0                             # Min instances
--max_instances 10                            # Max instances
--generate_only                               # Generate configs without deploying
```

## Deployment Targets

### 1. Cloud Run

Serverless containerized deployment.

```bash
/adk-deployment-manager --target "cloud-run" \
  --project "my-project" \
  --region "us-central1" \
  --memory "2Gi"
```

**Generated Files:**

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/ ./src/

# Environment
ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**cloudbuild.yaml:**
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}']

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - '${_SERVICE_NAME}'
      - '--image'
      - 'gcr.io/$PROJECT_ID/${_SERVICE_NAME}'
      - '--region'
      - '${_REGION}'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'

substitutions:
  _SERVICE_NAME: my-agent
  _REGION: us-central1
```

**cloud_run.yaml:**
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ${AGENT_NAME}
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containers:
        - image: gcr.io/${PROJECT_ID}/${AGENT_NAME}
          ports:
            - containerPort: 8080
          env:
            - name: GOOGLE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: google-api-key
                  key: latest
          resources:
            limits:
              memory: "2Gi"
              cpu: "2"
```

**Deploy Command:**
```bash
# Build and deploy
gcloud builds submit --config=cloudbuild.yaml

# Or direct deploy
gcloud run deploy my-agent \
  --source . \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated
```

### 2. Vertex AI Agent Engine

Managed agent hosting with built-in scaling.

```bash
/adk-deployment-manager --target "agent-engine" \
  --project "my-project" \
  --display_name "My Production Agent"
```

**Generated agent_engine.yaml:**
```yaml
displayName: "My Production Agent"
description: "Production ADK agent deployed to Agent Engine"

agentConfig:
  model: gemini-2.5-flash
  systemInstruction: |
    You are a helpful assistant.

deployment:
  minReplicas: 1
  maxReplicas: 10
  targetConcurrency: 10

resources:
  memory: 2Gi
  cpu: 2
```

**Deploy Script:**
```python
from vertexai.preview import reasoning_engines

# Deploy to Agent Engine
agent_engine = reasoning_engines.ReasoningEngine.create(
    reasoning_engine=root_agent,
    display_name="My Production Agent",
    description="Production ADK agent",
    requirements=[
        "google-adk>=1.0.0",
        "vertexai>=1.0.0",
    ],
)

print(f"Agent deployed: {agent_engine.resource_name}")
```

### 3. Google Kubernetes Engine (GKE)

Full control with Kubernetes orchestration.

```bash
/adk-deployment-manager --target "gke" \
  --cluster "my-cluster" \
  --namespace "agents"
```

**Generated k8s_deployment.yaml:**
```yaml
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
          image: gcr.io/${PROJECT_ID}/my-agent:latest
          ports:
            - containerPort: 8080
          env:
            - name: GOOGLE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: google-api-key
                  key: api-key
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
            initialDelaySeconds: 10
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
  name: my-agent-service
  namespace: agents
spec:
  selector:
    app: my-agent
  ports:
    - port: 80
      targetPort: 8080
  type: LoadBalancer
---
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
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

**Deploy Command:**
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s_deployment.yaml

# Check status
kubectl get pods -n agents
kubectl get services -n agents
```

### 4. Local Development

Run agent locally for development.

```bash
/adk-deployment-manager --target "local" --port 8080
```

**Generated run_local.sh:**
```bash
#!/bin/bash

# Set environment variables
export GOOGLE_API_KEY="${GOOGLE_API_KEY}"
export PORT=8080

# Run with hot reload
uvicorn src.main:app --host 0.0.0.0 --port $PORT --reload
```

## CI/CD Configuration

### GitHub Actions

```bash
/adk-deployment-manager --ci "github-actions" --target "cloud-run"
```

**Generated .github/workflows/deploy.yaml:**
```yaml
name: Deploy Agent

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy my-agent \
            --source . \
            --region us-central1 \
            --allow-unauthenticated
```

## Health Checks

All deployments include health check endpoint:

```python
# src/main.py
from google.adk.endpoints import get_fast_api_app
from agent import root_agent

app = get_fast_api_app(agent=root_agent)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent": root_agent.name,
        "model": root_agent.model,
    }
```

## Secrets Management

```bash
# Create secret in Secret Manager
gcloud secrets create google-api-key --data-file=api_key.txt

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding google-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

## Generated Project Structure

```
agent-deployment/
+-- src/
|   +-- agent.py
|   +-- main.py           # FastAPI wrapper with health check
|   +-- config.py
+-- deployment/
|   +-- Dockerfile
|   +-- cloudbuild.yaml   # Cloud Build
|   +-- cloud_run.yaml    # Cloud Run config
|   +-- agent_engine.yaml # Agent Engine config
|   +-- k8s/              # Kubernetes manifests
|   |   +-- deployment.yaml
|   |   +-- service.yaml
|   |   +-- hpa.yaml
+-- .github/
|   +-- workflows/
|       +-- deploy.yaml   # GitHub Actions
+-- scripts/
|   +-- deploy.sh
|   +-- run_local.sh
+-- requirements.txt
+-- README.md
```

## Examples

### Example 1: Cloud Run Deployment

```bash
$ /adk-deployment-manager --target "cloud-run" --project "my-project"

Deployment Configuration Generated

Target: Cloud Run
Region: us-central1
Memory: 2Gi
CPU: 2

Files:
- deployment/Dockerfile
- deployment/cloudbuild.yaml
- deployment/cloud_run.yaml

Deploy with:
  gcloud run deploy my-agent --source . --region us-central1
```

### Example 2: GKE with Auto-scaling

```bash
$ /adk-deployment-manager --target "gke" \
  --cluster "prod-cluster" \
  --min_instances 2 \
  --max_instances 20

GKE Deployment Configured

Cluster: prod-cluster
Namespace: agents
Replicas: 2-20
Auto-scaling: CPU 70%

Files:
- deployment/k8s/deployment.yaml
- deployment/k8s/service.yaml
- deployment/k8s/hpa.yaml

Deploy with:
  kubectl apply -f deployment/k8s/
```

## Related Skills

- **adk-adaptive-agent-generator** - Create agents to deploy
- **adk-mcp-integration** - Add tools before deployment
- **adk-rag-builder** - Add RAG before deployment

## More Information

See Cloud Run documentation for advanced configuration.
See GKE documentation for Kubernetes best practices.
