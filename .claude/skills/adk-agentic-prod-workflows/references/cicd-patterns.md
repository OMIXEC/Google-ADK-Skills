# CI/CD Patterns for ADK Workflows

## Pipeline Stages

```
[Push] → [Install Deps] → [Lint] → [Unit Tests] → [Evals] → [Build Image] → [Deploy]
```

## 1. GitHub Actions

```yaml
name: ADK Workflow CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1
  SERVICE_NAME: my-workflow

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Lint
        run: ruff check app/ tests/

      - name: Unit tests
        run: pytest tests/ -v --junitxml=test-results.xml

      - name: Eval tests
        run: python evals/test_harness.py
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}

  build-and-deploy:
    needs: lint-and-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Build Docker image
        run: |
          docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:${{ github.sha }} .

      - name: Push to Artifact Registry
        run: |
          gcloud auth configure-docker $REGION-docker.pkg.dev
          docker push $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:${{ github.sha }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy $SERVICE_NAME \
            --image $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:${{ github.sha }} \
            --region $REGION \
            --allow-unauthenticated \
            --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
```

## 2. Cloud Build

```yaml
# cloudbuild.yaml
steps:
  - name: python:3.11
    id: install
    entrypoint: pip
    args: ["install", "-r", "requirements.txt"]

  - name: python:3.11
    id: lint
    entrypoint: ruff
    args: ["check", "app/", "tests/"]

  - name: python:3.11
    id: test
    entrypoint: pytest
    args: ["tests/", "-v", "--junitxml=test-results.xml"]
    env:
      - "GOOGLE_API_KEY=$_GOOGLE_API_KEY"

  - name: python:3.11
    id: eval
    entrypoint: python
    args: ["evals/test_harness.py"]
    env:
      - "GOOGLE_API_KEY=$_GOOGLE_API_KEY"

  - name: gcr.io/cloud-builders/docker
    id: build
    args: ["build", "-t", "$_ARTIFACT_REGISTRY/$PROJECT_ID/$_SERVICE_NAME:$COMMIT_SHA", "."]

  - name: gcr.io/cloud-builders/docker
    id: push
    args: ["push", "$_ARTIFACT_REGISTRY/$PROJECT_ID/$_SERVICE_NAME:$COMMIT_SHA"]

  - name: gcr.io/google.com/cloudsdktool/cloud-sdk
    id: deploy
    entrypoint: gcloud
    args:
      - "run"
      - "deploy"
      - "$_SERVICE_NAME"
      - "--image=$_ARTIFACT_REGISTRY/$PROJECT_ID/$_SERVICE_NAME:$COMMIT_SHA"
      - "--region=$_REGION"
      - "--allow-unauthenticated"

substitutions:
  _SERVICE_NAME: my-workflow
  _REGION: us-central1
  _ARTIFACT_REGISTRY: us-central1-docker.pkg.dev

images:
  - "$_ARTIFACT_REGISTRY/$PROJECT_ID/$_SERVICE_NAME:$COMMIT_SHA"
```

## 3. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 4. Environment Configuration

```
# .env.example — copy to .env for local dev, never commit real values
GOOGLE_API_KEY=your-api-key
GOOGLE_CLOUD_PROJECT=your-project-id
STRIPE_API_KEY=your-stripe-key
LOG_LEVEL=INFO
```

### Per-Environment Config

```python
# app/config.py
import os
from pydantic import BaseModel

class Config(BaseModel):
    env: str = os.getenv("ENV", "dev")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    google_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    model_name: str = os.getenv("MODEL_NAME", "gemini-2.5-flash")

    @property
    def is_production(self) -> bool:
        return self.env == "prod"

    @property
    def model_config(self) -> dict:
        if self.is_production:
            return {"temperature": 0.1, "top_p": 0.95}
        return {"temperature": 0.7, "top_p": 0.95}

config = Config()
```

## Deployment Targets

| Target | Use Case | Key Config |
|--------|----------|------------|
| Cloud Run | HTTP/gRPC serving, auto-scale to zero | `--allow-unauthenticated`, `--concurrency` |
| Agent Engine | Managed ADK runtime, A2A native | `adk deploy` command |
| GKE | Full control, GPU workloads, batch jobs | Kubernetes Deployment + Service |

## CI/CD Checklist

- [ ] Dependencies pinned with hashes (`pip freeze --require-hashes`)
- [ ] Secrets in CI/CD secrets manager, never in repo
- [ ] Evals run as CI gate (block deploy on eval failure)
- [ ] Docker image tagged with commit SHA for traceability
- [ ] Deployment uses rolling update or blue/green
- [ ] Health check endpoint (`/health`) returns 200
- [ ] Readiness check verifies agent is initialized
- [ ] Rollback command documented and tested

## 5. Azure DevOps Pipeline

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include: [main]

variables:
  - name: serviceName
    value: my-workflow
  - name: region
    value: eastus

stages:
  - stage: Test
    jobs:
      - job: LintAndTest
        pool:
          vmImage: ubuntu-latest
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.11'
          - script: pip install -r requirements.txt
            displayName: Install dependencies
          - script: ruff check app/ tests/
            displayName: Lint
          - script: pytest tests/ -v --junitxml=test-results.xml
            displayName: Unit tests
            env:
              GOOGLE_API_KEY: $(GOOGLE_API_KEY)
          - script: python evals/test_harness.py
            displayName: Eval tests
            env:
              GOOGLE_API_KEY: $(GOOGLE_API_KEY)

  - stage: BuildAndDeploy
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - job: Deploy
        pool:
          vmImage: ubuntu-latest
        steps:
          - task: Docker@2
            inputs:
              containerRegistry: 'acr-connection'
              repository: $(serviceName)
              command: 'buildAndPush'
              Dockerfile: '**/Dockerfile'
              tags: $(Build.SourceVersion)
          - task: AzureCLI@2
            inputs:
              azureSubscription: 'azure-connection'
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                az containerapp update \
                  --name $(serviceName) \
                  --resource-group my-rg \
                  --image myacr.azurecr.io/$(serviceName):$(Build.SourceVersion) \
                  --set-env-vars GOOGLE_CLOUD_PROJECT=$(GOOGLE_CLOUD_PROJECT)
```

## 6. GitLab CI Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - test
  - eval
  - build
  - deploy

variables:
  SERVICE_NAME: my-workflow
  REGION: us-central1

.test_base:
  image: python:3.11
  before_script:
    - pip install -r requirements.txt

lint:
  extends: .test_base
  stage: test
  script:
    - ruff check app/ tests/

unit_tests:
  extends: .test_base
  stage: test
  script:
    - pytest tests/ -v --junitxml=test-results.xml
  artifacts:
    reports:
      junit: test-results.xml

eval_tests:
  extends: .test_base
  stage: eval
  script:
    - python evals/test_harness.py
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY

build_and_push:
  image: docker:latest
  stage: build
  services:
    - docker:dind
  script:
    - docker build -t $REGION-docker.pkg.dev/$GCP_PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:$CI_COMMIT_SHA .
    - echo "$GCP_SA_KEY" | docker login -u _json_key --password-stdin https://$REGION-docker.pkg.dev
    - docker push $REGION-docker.pkg.dev/$GCP_PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:$CI_COMMIT_SHA
  only:
    - main

deploy_cloud_run:
  image: google/cloud-sdk:latest
  stage: deploy
  script:
    - echo "$GCP_SA_KEY" > /tmp/key.json
    - gcloud auth activate-service-account --key-file=/tmp/key.json
    - gcloud run deploy $SERVICE_NAME
      --image $REGION-docker.pkg.dev/$GCP_PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:$CI_COMMIT_SHA
      --region $REGION
      --allow-unauthenticated
      --set-env-vars "GOOGLE_CLOUD_PROJECT=$GCP_PROJECT_ID"
  only:
    - main
```

## 7. Canary Deployment Pattern

Roll out to a small percentage first, validate, then promote:

```yaml
# GitHub Actions canary deploy step
- name: Deploy canary
  run: |
    gcloud run deploy $SERVICE_NAME-canary \
      --image $IMAGE:${{ github.sha }} \
      --region $REGION \
      --no-traffic \
      --tag canary

- name: Route 10% traffic to canary
  run: |
    gcloud run services update-traffic $SERVICE_NAME \
      --region $REGION \
      --to-tags canary=10

- name: Validate canary (run for 5 minutes)
  run: |
    # Run eval suite against canary endpoint
    CANARY_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
    for i in $(seq 1 12); do
      curl -s "$CANARY_URL/health" | grep -q "ok" && break
      sleep 25
    done
    # Check error rate on canary
    ERROR_RATE=$(gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=100 --freshness=5m | wc -l)
    if [ "$ERROR_RATE" -gt 5 ]; then
      echo "Canary error rate too high: $ERROR_RATE"
      gcloud run services update-traffic $SERVICE_NAME --region $REGION --to-tags canary=0
      exit 1
    fi

- name: Promote canary to 100%
  run: |
    gcloud run services update-traffic $SERVICE_NAME \
      --region $REGION \
      --to-latest
```

## 8. Blue-Green Deployment Pattern

Deploy new version alongside old, switch traffic atomically:

```python
# scripts/blue_green_deploy.py
"""Blue-green deployment for Cloud Run. Switches traffic atomically."""

BLUE_REVISION = "my-workflow-00001-abc"
GREEN_REVISION = "my-workflow-00002-def"

def deploy_green():
    """Deploy green (new version) without traffic."""
    subprocess.run([
        "gcloud", "run", "deploy", "my-workflow",
        "--image", f"gcr.io/project/my-workflow:{GREEN_REVISION}",
        "--region", "us-central1",
        "--no-traffic",  # Don't route traffic yet
    ])

def smoke_test_green():
    """Validate green revision before switching traffic."""
    green_url = f"https://{GREEN_REVISION}---my-workflow-xxxxx-uc.a.run.app"
    # Run health, readiness, and eval checks against green
    assert requests.get(f"{green_url}/health").status_code == 200
    assert requests.get(f"{green_url}/ready").json()["status"] == "ready"
    # Eval suite against green
    subprocess.run(["pytest", "evals/", "--base-url", green_url], check=True)

def switch_traffic():
    """Atomically switch all traffic to green."""
    subprocess.run([
        "gcloud", "run", "services", "update-traffic", "my-workflow",
        "--region", "us-central1",
        "--to-revisions", f"{GREEN_REVISION}=100",
    ])

def rollback():
    """Instant rollback: switch 100% back to blue."""
    subprocess.run([
        "gcloud", "run", "services", "update-traffic", "my-workflow",
        "--region", "us-central1",
        "--to-revisions", f"{BLUE_REVISION}=100",
    ])

if __name__ == "__main__":
    deploy_green()
    smoke_test_green()
    switch_traffic()
```

## 9. Rollback Strategy

```bash
# Instant rollback to specific revision
gcloud run services update-traffic my-workflow \
  --region us-central1 \
  --to-revisions my-workflow-00001-abc=100

# Rollback to last known good image (stored in Artifact Registry)
LAST_GOOD=$(gcloud artifacts docker tags list \
  us-central1-docker.pkg.dev/PROJECT/my-workflow/my-workflow \
  --filter="tags:prod-stable" --format="value(tags)" | head -1)

gcloud run deploy my-workflow \
  --image us-central1-docker.pkg.dev/PROJECT/my-workflow/my-workflow:$LAST_GOOD \
  --region us-central1

# Tag current stable as prod-stable after successful deploy
gcloud artifacts docker tags add \
  us-central1-docker.pkg.dev/PROJECT/my-workflow/my-workflow:$CURRENT_SHA \
  us-central1-docker.pkg.dev/PROJECT/my-workflow/my-workflow:prod-stable
```

**Rollback checklist:**
- [ ] Every deploy tags the image with both commit SHA AND environment (e.g., `prod-stable`)
- [ ] Rollback command is a single `gcloud run services update-traffic` call (no rebuild)
- [ ] Rollback tested in staging before production deploy
- [ ] Database migrations are backward-compatible (rollback doesn't break schema)
- [ ] Monitoring alerts trigger if rollback was needed (track deploy failures)
- [ ] On-call runbook includes exact rollback command with placeholders filled
