# Deployment Matrix — All Cloud Providers × All Targets

Every deployment follows the same pattern: Container → Registry → Target → Health Check. TLS everywhere. Secrets in secret manager, never in env.

## Provider × Target Compatibility

| Target | GCP | AWS | Azure | Local |
|--------|-----|-----|-------|-------|
| **Serverless Container** | Cloud Run | ECS Fargate / Lambda (Docker) | Container Apps | Docker Compose |
| **Managed Agent Runtime** | Agent Engine | SageMaker Inference | Foundry (Azure AI) | — |
| **Kubernetes** | GKE / Autopilot | EKS | AKS | k3s / minikube |
| **PaaS** | App Engine | Elastic Beanstalk | App Service | — |
| **AI Platform** | Vertex AI | SageMaker Endpoints | Azure ML Managed Online Endpoints | — |
| **Functions / Lightweight** | Cloud Functions | Lambda | Functions | — |
| **VM-based** | Compute Engine | EC2 | Azure VM | Docker (bare) |

## Universal Container Pattern

All targets share one Docker contract. Build once, deploy anywhere.

```dockerfile
# Dockerfile — multi-stage, non-root, health check
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
COPY evals/ ./evals/

ENV PATH=/root/.local/bin:$PATH
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## GCP Deployments

### Cloud Run (serverless container — default)

```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ${SERVICE_NAME}
  annotations:
    run.googleapis.com/ingress: all
    autoscaling.knative.dev/maxScale: "10"
spec:
  template:
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      serviceAccountName: ${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com
      containers:
      - image: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:${VERSION}
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_CLOUD_PROJECT
          value: "${PROJECT_ID}"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
        startupProbe:
          httpGet:
            path: /health
          initialDelaySeconds: 5
        livenessProbe:
          httpGet:
            path: /health
```

Deploy:
```bash
gcloud run deploy ${SERVICE_NAME} \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:${VERSION} \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
```

### Agent Engine (managed ADK runtime)

```yaml
# agent-engine.yaml
agent_config:
  name: ${SERVICE_NAME}
  display_name: ${DISPLAY_NAME}
  runtime:
    type: python
    version: "3.11"
  entry_point: app.workflow:graph_agent
  scaling:
    min_instances: 0
    max_instances: 5
  observability:
    logging: true
    tracing: true
    metrics: true
```

Deploy:
```bash
adk deploy --project ${PROJECT_ID} --region ${REGION}
```

### Vertex AI (managed model + agent endpoint)

```python
# deploy_vertex.py
from google.cloud import aiplatform

aiplatform.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"), location=os.getenv("REGION"))

model = aiplatform.Model.upload(
    display_name=f"{name}-agent",
    serving_container_image_uri=f"{region}-docker.pkg.dev/{project_id}/{name}/{name}:latest",
    serving_container_ports=[8080],
    serving_container_health_route="/health",
    serving_container_predict_route="/run",
)

endpoint = model.deploy(
    machine_type="n1-standard-4",
    min_replica_count=1,
    max_replica_count=5,
    traffic_split={"0": 100},
)
```

### GKE (Kubernetes)

```yaml
# gke-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${SERVICE_NAME}
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: ${SERVICE_NAME}
  template:
    metadata:
      labels:
        app: ${SERVICE_NAME}
    spec:
      serviceAccountName: ${SERVICE_NAME}-sa
      containers:
      - name: ${SERVICE_NAME}
        image: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:${VERSION}
        ports:
        - containerPort: 8080
        env:
        - name: GOOGLE_CLOUD_PROJECT
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
          requests:
            cpu: "250m"
            memory: "256Mi"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: ${SERVICE_NAME}
spec:
  type: LoadBalancer
  selector:
    app: ${SERVICE_NAME}
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ${SERVICE_NAME}-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ${SERVICE_NAME}
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

### App Engine (PaaS)

```yaml
# app.yaml
runtime: python311
service: ${SERVICE_NAME}
entrypoint: uvicorn app.main:app --host 0.0.0.0 --port $PORT

instance_class: F2
automatic_scaling:
  min_instances: 0
  max_instances: 5
  target_cpu_utilization: 0.7

env_variables:
  GOOGLE_CLOUD_PROJECT: ${PROJECT_ID}
  LOG_LEVEL: INFO

handlers:
- url: /.*
  script: auto
  secure: always
```

Deploy:
```bash
gcloud app deploy app.yaml --project ${PROJECT_ID}
```

---

## AWS Deployments

### ECS Fargate (serverless container)

```json
{
  "family": "adk-workflow",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/adk-workflow-task-role",
  "containerDefinitions": [{
    "name": "adk-workflow",
    "image": "${ECR_REPO}:${VERSION}",
    "portMappings": [{"containerPort": 8080, "protocol": "tcp"}],
    "environment": [
      {"name": "AWS_REGION", "value": "${AWS_REGION}"},
      {"name": "LOG_LEVEL", "value": "INFO"}
    ],
    "secrets": [
      {"name": "DB_PASSWORD", "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:db-password"}
    ],
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
      "interval": 30,
      "timeout": 5,
      "retries": 3,
      "startPeriod": 10
    },
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/adk-workflow",
        "awslogs-region": "${AWS_REGION}",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]
}
```

Deploy via AWS CLI:
```bash
aws ecs register-task-definition --cli-input-json file://ecs-taskdef.json
aws ecs update-service --cluster adk-cluster --service adk-workflow --task-definition adk-workflow
```

### ECS with Terraform

```hcl
# terraform/aws-ecs.tf
resource "aws_ecs_cluster" "adk" {
  name = "adk-cluster"
}

resource "aws_ecs_task_definition" "workflow" {
  family                   = "adk-workflow"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "adk-workflow"
    image = "${aws_ecr_repository.workflow.repository_url}:latest"
    portMappings = [{ containerPort = 8080 }]
    environment = [
      { name = "AWS_REGION", value = var.region }
    ]
    secrets = [
      { name = "DB_PASSWORD", valueFrom = aws_secretsmanager_secret.db_password.arn }
    ]
  }])
}

resource "aws_ecs_service" "workflow" {
  name            = "adk-workflow"
  cluster         = aws_ecs_cluster.adk.id
  task_definition = aws_ecs_task_definition.workflow.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.workflow.arn
    container_name   = "adk-workflow"
    container_port   = 8080
  }
}
```

### EKS (Kubernetes)

```yaml
# eks-deployment.yaml — same structure as GKE, different auth/IAM
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${SERVICE_NAME}
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::${AWS_ACCOUNT_ID}:role/adk-workflow-role
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ${SERVICE_NAME}
  template:
    metadata:
      labels:
        app: ${SERVICE_NAME}
    spec:
      serviceAccountName: adk-workflow-sa
      containers:
      - name: ${SERVICE_NAME}
        image: ${ECR_REPO}:${VERSION}
        ports:
        - containerPort: 8080
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
```

### Lambda (Docker container)

```python
# lambda_handler.py
"""ADK workflow as Lambda function behind API Gateway."""
import asyncio
from app.workflow import graph_agent
from google.adk.runners import InProcessRunner

runner = InProcessRunner(agent=graph_agent)

def handler(event, context):
    """API Gateway proxy integration → ADK workflow."""
    body = json.loads(event.get("body", "{}"))
    query = body.get("query", "")
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(runner.run(query=query, user_id=user_id))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result),
    }
```

```hcl
# terraform/aws-lambda.tf
resource "aws_lambda_function" "workflow" {
  function_name = "adk-workflow"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.workflow.repository_url}:latest"
  timeout       = 300
  memory_size   = 1024

  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }
}
```

### SageMaker Endpoint

```python
# deploy_sagemaker.py
import sagemaker
from sagemaker.huggingface import HuggingFaceModel

# For ADK workflows: wrap as inference endpoint
model = HuggingFaceModel(
    entry_point="inference.py",
    source_dir="./app",
    role=sagemaker.get_execution_role(),
    image_uri=f"{account_id}.dkr.ecr.{region}.amazonaws.com/adk-workflow:latest",
)

predictor = model.deploy(
    initial_instance_count=1,
    instance_type="ml.g4dn.xlarge",
    endpoint_name=f"{name}-endpoint",
)
```

---

## Azure Deployments

### Container Apps (serverless container)

```yaml
# azure-container-app.yaml
kind: containerapp
location: ${AZURE_REGION}
name: ${SERVICE_NAME}
properties:
  configuration:
    ingress:
      external: true
      targetPort: 8080
    secrets:
    - name: db-password
      value: ${DB_PASSWORD}
  template:
    containers:
    - name: ${SERVICE_NAME}
      image: ${ACR_LOGIN_SERVER}/${SERVICE_NAME}:${VERSION}
      resources:
        cpu: 0.5
        memory: 1Gi
      env:
      - name: LOG_LEVEL
        value: INFO
      - name: DB_PASSWORD
        secretRef: db-password
      probes:
      - type: Liveness
        httpGet:
          path: /health
          port: 8080
        initialDelaySeconds: 30
      - type: Readiness
        httpGet:
          path: /health
          port: 8080
        initialDelaySeconds: 10
  scale:
    minReplicas: 1
    maxReplicas: 5
```

Deploy:
```bash
az containerapp up \
  --name ${SERVICE_NAME} \
  --resource-group ${RESOURCE_GROUP} \
  --environment ${CONTAINERAPPS_ENVIRONMENT} \
  --image ${ACR_LOGIN_SERVER}/${SERVICE_NAME}:${VERSION} \
  --target-port 8080 \
  --ingress external
```

### AKS (Kubernetes)

Same deployment YAML as GKE. Different auth — use Azure AD pod identity:

```yaml
# aks-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${SERVICE_NAME}
  labels:
    aadpodidbinding: adk-workflow-identity
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ${SERVICE_NAME}
  template:
    metadata:
      labels:
        app: ${SERVICE_NAME}
        aadpodidbinding: adk-workflow-identity
    spec:
      containers:
      - name: ${SERVICE_NAME}
        image: ${ACR_LOGIN_SERVER}/${SERVICE_NAME}:${VERSION}
        ports:
        - containerPort: 8080
        resources:
          limits:
            cpu: "1000m"
            memory: "512Mi"
```

```hcl
# terraform/azure-aks.tf
resource "azurerm_kubernetes_cluster" "adk" {
  name                = "adk-cluster"
  location            = var.location
  resource_group_name = azurerm_resource_group.adk.name
  dns_prefix          = "adk"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_D2s_v3"
  }

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_container_registry" "adk" {
  name                = "adkworkflowregistry"
  resource_group_name = azurerm_resource_group.adk.name
  location            = var.location
  sku                 = "Standard"
  admin_enabled       = false
}

resource "azurerm_role_assignment" "aks_acr" {
  scope                = azurerm_container_registry.adk.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.adk.kubelet_identity[0].object_id
}
```

### App Service (PaaS)

```bash
az webapp create \
  --resource-group ${RESOURCE_GROUP} \
  --plan ${APP_SERVICE_PLAN} \
  --name ${SERVICE_NAME} \
  --deployment-container-image-name ${ACR_LOGIN_SERVER}/${SERVICE_NAME}:${VERSION}

az webapp config set \
  --resource-group ${RESOURCE_GROUP} \
  --name ${SERVICE_NAME} \
  --startup-file "uvicorn app.main:app --host 0.0.0.0 --port 8080"
```

### Azure ML Managed Online Endpoint (AI Platform)

```yaml
# azure-ml-endpoint.yaml
$schema: https://azuremlschemas.azureedge.net/latest/managedOnlineEndpoint.schema.json
name: adk-workflow-endpoint
auth_mode: key
---
$schema: https://azuremlschemas.azureedge.net/latest/managedOnlineDeployment.schema.json
name: blue
endpoint_name: adk-workflow-endpoint
model:
  path: ./
  type: custom_model
instance_type: Standard_DS3_v2
instance_count: 1
environment:
  image: ${ACR_LOGIN_SERVER}/${SERVICE_NAME}:${VERSION}
  inference_config:
    scoring_route:
      port: 8080
      path: /run
    liveness_route:
      port: 8080
      path: /health
```

---

## Local / Dockerized

### Docker Compose

```yaml
# docker-compose.yml
version: "3.9"

services:
  workflow:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - LOG_LEVEL=DEBUG
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  # Optional: local DB for development
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: adk
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: adk_workflow
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  pgdata:
```

### Startup script — local dev

```bash
#!/bin/bash
# run-local.sh
# Set GOOGLE_API_KEY or other provider keys before running
export GOOGLE_API_KEY="${GOOGLE_API_KEY:?Set GOOGLE_API_KEY}"
export LOG_LEVEL=DEBUG

# Run via ADK CLI
adk api_server --app-dir app/ --port 8080

# Or run via uvicorn directly
# uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

---

## FastAPI Production Bootstrap

Production-ready FastAPI server with ADK workflow integration, security middleware, and health checks. Generated via `scripts/compose_workflow.py` when `--server fastapi` is specified.

### Application Factory

```python
"""app/main.py — Production FastAPI bootstrap for ADK workflows."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.workflow import graph_agent
from google.adk.runners import InProcessRunner
from middleware.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up runner on startup."""
    app.state.runner = InProcessRunner(agent=graph_agent)
    app.state.ready = True
    yield
    app.state.ready = False


def get_fast_api_app() -> FastAPI:
    """Factory: returns production-configured FastAPI app."""
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "api.example.com").split(",")
    cors_origins = os.getenv("CORS_ORIGINS", "https://app.example.com").split(",")

    app = FastAPI(
        title="ADK Workflow API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # ── Security middleware ──
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
    )

    return app


app = get_fast_api_app()


class RunRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    user_id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    session_id: str | None = None


class RunResponse(BaseModel):
    status: str
    result: dict | None = None
    error: str | None = None


@app.get("/health")
async def health():
    """Basic liveness — always returns 200 if process alive."""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness — returns 200 when runner is warmed up."""
    if app.state.ready:
        return {"status": "ready"}
    return {"status": "not_ready"}, 503


@app.post("/run", response_model=RunResponse)
async def run_workflow(req: RunRequest, request: Request):
    """Execute the ADK workflow."""
    try:
        result = await app.state.runner.run(
            query=req.query,
            user_id=req.user_id,
            session_id=req.session_id,
        )
        return RunResponse(status="ok", result=result)
    except Exception as e:
        logger.exception("Workflow run failed")
        return RunResponse(status="error", error=str(e))
```

### Security-Hardened Dockerfile (Gunicorn + Uvicorn)

```dockerfile
# Dockerfile — multi-stage, non-root, gunicorn + uvicorn workers
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app

# Install gunicorn for production serving
RUN pip install --no-cache-dir gunicorn uvicorn[standard]

COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
COPY evals/ ./evals/

ENV PATH=/root/.local/bin:$PATH
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Non-root user
RUN groupadd --system app && useradd --system --no-create-home --gid app app \
    && chown -R app:app /app
USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Gunicorn with uvicorn workers — production-grade ASGI
# --worker-connections: 1000 per worker (tune to container memory)
# --keep-alive: 5s connection keepalive
# --timeout: 300s to allow long-running workflow steps
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", \
     "--keep-alive", "5", \
     "--timeout", "300", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

### Cloud Run Config Table

| Setting | Value | Reason |
|---------|-------|--------|
| `--memory` | 512Mi | ADK runner + agent state fits in 512Mi for most workflows |
| `--cpu` | 1 (1000m) | One vCPU per instance; gunicorn workers share |
| `--max-instances` | 10 | Production cap; increase based on load testing |
| `--concurrency` | 80 | gunicorn 4 workers × 20 connections each ≈ 80 |
| `--timeout` | 300s | Matches gunicorn timeout; long enough for multi-step workflows |
| `--cpu-boost` | Enabled | Faster cold starts for agent workloads |
| `--cpu-throttling` | Disabled | Agents need consistent CPU for LLM call processing |
| `--min-instances` | 1 | Avoid cold start latency for production |
| `--vpc-connector` | Required | If agents call VPC-only services (DBs, internal APIs) |
| `--service-account` | Dedicated SA | Never use default compute SA in production |
| `--ingress` | internal-and-cloud-load-balancing | Restrict direct internet access if behind API Gateway |

Deploy command:
```bash
gcloud run deploy ${SERVICE_NAME} \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:${VERSION} \
  --region=${REGION} \
  --memory=512Mi --cpu=1 --max-instances=10 --concurrency=80 --timeout=300 \
  --cpu-boost --no-cpu-throttling --min-instances=1 \
  --service-account=${SERVICE_NAME}-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},LOG_LEVEL=INFO"
```

---

## Infrastructure-as-Code — Multi-Cloud

### GCP with Terraform

```hcl
# terraform/gcp-cloudrun.tf
resource "google_cloud_run_v2_service" "workflow" {
  name     = var.service_name
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}/${var.service_name}:latest"
      ports { container_port = 8080 }
      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
      }}
      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 5
      }
      liveness_probe {
        http_get {
          path = "/health"
        }
      }
    }
    service_account = google_service_account.workflow.email
  }

  ingress = "INGRESS_TRAFFIC_ALL"
}

resource "google_service_account" "workflow" {
  account_id   = "${var.service_name}-sa"
  display_name = "${var.service_name} Service Account"
}

resource "google_artifact_registry_repository" "workflow" {
  repository_id = var.service_name
  location      = var.region
  format        = "DOCKER"
}
```

### Multi-Cloud CI/CD — Provider-Agnostic

```yaml
# .github/workflows/deploy-multicloud.yml
name: Multi-Cloud Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t workflow:${{ github.sha }} .

  deploy-gcp:
    needs: build
    if: vars.GCP_ENABLED == 'true'
    # Pin to commit SHA in production: google-github-actions/auth@<COMMIT_SHA>
    uses: ./.github/workflows/deploy-gcp.yml
    secrets:
      GCP_SA_KEY: ${{ secrets.GCP_SA_KEY }}

  deploy-aws:
    needs: build
    if: vars.AWS_ENABLED == 'true'
    # Pin to commit SHA in production: aws-actions/configure-aws-credentials@<COMMIT_SHA>
    uses: ./.github/workflows/deploy-aws.yml
    secrets:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

  deploy-azure:
    needs: build
    if: vars.AZURE_ENABLED == 'true'
    # Pin to commit SHA in production: azure/login@<COMMIT_SHA>
    uses: ./.github/workflows/deploy-azure.yml
    secrets:
      AZURE_CREDENTIALS: ${{ secrets.AZURE_CREDENTIALS }}
```

---

## Deployment Selection Guide

Decision flowchart:

```
User requirement → constraints lead to target:

"serverless, zero config"     → Cloud Run / Container Apps / ECS Fargate
"managed ADK runtime"         → Agent Engine
"Kubernetes ecosystem"        → GKE / EKS / AKS
"GPU / model inference"       → Vertex AI / SageMaker / Azure ML
"PaaS, no Dockerfile needed"  → App Engine / App Service
"event-driven, bursty"        → Cloud Functions / Lambda
"hybrid / on-prem"            → GKE on-prem / AKS hybrid / k3s
"local dev / testing"         → Docker Compose / minikube / k3s
```

---

## Deployment Checklist

- [ ] Non-root user in Dockerfile (`USER app`)
- [ ] Health check endpoint (`/health`) returns 200
- [ ] TLS enforced at ingress, not app-level
- [ ] Secrets in secret manager (Secret Manager / Secrets Manager / Key Vault)
- [ ] IAM role / service account scoped to minimum permissions
- [ ] Resource limits set (CPU, memory, max scale)
- [ ] Startup probe configured (grace period for model loading)
- [ ] Liveness probe configured
- [ ] Readiness probe configured (for K8s)
- [ ] Container image scanned (Container Scanning / ECR Scan / Defender)
- [ ] Image tag is content-addressable (git SHA, not `latest` in prod)
- [ ] Multi-region failover configured if >99.9% SLA required
- [ ] Logs shipped to central observability (Cloud Logging / CloudWatch / Log Analytics)
- [ ] Traces + metrics enabled
