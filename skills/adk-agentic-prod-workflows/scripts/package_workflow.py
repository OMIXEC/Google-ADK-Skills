#!/usr/bin/env python3
"""Package an ADK workflow for deployment.

Generates deployment-ready artifacts:
- Dockerfile
- cloudbuild.yaml / cloudbuild.json
- Deployment config (Cloud Run, Agent Engine, GKE)
- Environment configuration

Usage:
    python package_workflow.py --source app/ --name my-flow --target cloud-run
    python package_workflow.py --source app/ --name my-flow --target agent-engine
    python package_workflow.py --source . --name my-flow --target gke
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None


TARGETS = {
    "cloud-run": "Google Cloud Run (serverless container)",
    "agent-engine": "Google Agent Engine (managed ADK runtime)",
    "gke": "Google Kubernetes Engine",
    "ecs": "AWS ECS Fargate (serverless containers)",
    "eks": "AWS EKS (managed Kubernetes)",
    "lambda": "AWS Lambda (Docker container)",
    "container-apps": "Azure Container Apps (serverless containers)",
    "aks": "Azure AKS (managed Kubernetes)",
    "all": "All targets",
}


def generate_dockerfile(name: str, source_dir: str, port: int = 8080) -> str:
    return f"""FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY {source_dir}/ ./app/

ENV PORT={port}
ENV PYTHONUNBUFFERED=1
EXPOSE {port}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:{port}/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{port}"]
"""


def generate_cloudbuild(name: str, source_dir: str, region: str = "us-central1") -> dict:
    return {
        "steps": [
            {"name": "python:3.11", "id": "install", "entrypoint": "pip",
             "args": ["install", "-r", "requirements.txt"]},
            {"name": "python:3.11", "id": "lint", "entrypoint": "ruff",
             "args": ["check", source_dir, "tests/"]},
            {"name": "python:3.11", "id": "test", "entrypoint": "pytest",
             "args": ["tests/", "-v", "--junitxml=test-results.xml"],
             "env": ["GOOGLE_API_KEY=$_GOOGLE_API_KEY"]},
            {"name": "python:3.11", "id": "eval", "entrypoint": "python",
             "args": ["evals/test_harness.py"],
             "env": ["GOOGLE_API_KEY=$_GOOGLE_API_KEY"]},
            {"name": "gcr.io/cloud-builders/docker", "id": "build",
             "args": ["build", "-t", f"{region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}:$COMMIT_SHA", "."]},
            {"name": "gcr.io/cloud-builders/docker", "id": "push",
             "args": ["push", f"{region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}:$COMMIT_SHA"]},
            {"name": "gcr.io/google.com/cloudsdktool/cloud-sdk", "id": "deploy",
             "entrypoint": "gcloud",
             "args": ["run", "deploy", name,
                      f"--image={region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}:$COMMIT_SHA",
                      f"--region={region}",
                      "--allow-unauthenticated",
                      "--set-env-vars", f"GOOGLE_CLOUD_PROJECT=$PROJECT_ID"]},
        ],
        "substitutions": {
            "_SERVICE_NAME": name,
            "_REGION": region,
            "_ARTIFACT_REGISTRY": f"{region}-docker.pkg.dev",
        },
        "images": [f"{region}-docker.pkg.dev/$PROJECT_ID/{name}/{name}:$COMMIT_SHA"],
    }


def generate_cloud_run_yaml(name: str, region: str = "us-central1") -> dict:
    return {
        "apiVersion": "serving.knative.dev/v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "annotations": {
                "run.googleapis.com/ingress": "all",
                "run.googleapis.com/ingress-status": "all",
                "autoscaling.knative.dev/maxScale": "10",
                "run.googleapis.com/cpu-throttling": "false",
            },
        },
        "spec": {
            "template": {
                "spec": {
                    "containerConcurrency": 80,
                    "timeoutSeconds": 300,
                    "serviceAccountName": f"{name}-sa@${{PROJECT_ID}}.iam.gserviceaccount.com",
                    "containers": [{
                        "image": f"{region}-docker.pkg.dev/${{PROJECT_ID}}/{name}/{name}:latest",
                        "env": [
                            {"name": "LOG_LEVEL", "value": "INFO"},
                            {"name": "MODEL_NAME", "value": "gemini-2.5-flash"},
                        ],
                        "resources": {
                            "limits": {"cpu": "1000m", "memory": "512Mi"},
                            "requests": {"cpu": "500m", "memory": "256Mi"},
                        },
                        "startupProbe": {
                            "httpGet": {"path": "/health"},
                            "initialDelaySeconds": 5,
                            "periodSeconds": 10,
                        },
                        "livenessProbe": {
                            "httpGet": {"path": "/health"},
                            "periodSeconds": 30,
                        },
                    }],
                }
            }
        },
    }


def generate_agent_engine_config(name: str) -> dict:
    return {
        "agent_config": {
            "name": name,
            "display_name": name.replace("-", " ").title(),
            "description": f"ADK workflow: {name}",
            "runtime": {
                "type": "python",
                "version": "3.11",
            },
            "entry_point": "app.workflow:graph_agent",
            "scaling": {
                "min_instances": 0,
                "max_instances": 5,
            },
            "observability": {
                "logging": True,
                "tracing": True,
                "metrics": True,
            },
        }
    }


def generate_gke_yaml(name: str, region: str = "us-central1") -> dict:
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "labels": {"app": name}},
        "spec": {
            "replicas": 2,
            "selector": {"matchLabels": {"app": name}},
            "strategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {"maxSurge": 1, "maxUnavailable": 0},
            },
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": {
                    "serviceAccountName": f"{name}-sa",
                    "containers": [{
                        "name": name,
                        "image": f"{region}-docker.pkg.dev/${{PROJECT_ID}}/{name}/{name}:latest",
                        "ports": [{"containerPort": 8080}],
                        "env": [
                            {"name": "LOG_LEVEL", "value": "INFO"},
                            {"name": "GOOGLE_CLOUD_PROJECT", "valueFrom": {
                                "fieldRef": {"fieldPath": "metadata.namespace"}}},
                        ],
                        "resources": {
                            "limits": {"cpu": "1000m", "memory": "512Mi"},
                            "requests": {"cpu": "250m", "memory": "256Mi"},
                        },
                        "readinessProbe": {
                            "httpGet": {"path": "/health", "port": 8080},
                            "initialDelaySeconds": 10,
                            "periodSeconds": 15,
                        },
                        "livenessProbe": {
                            "httpGet": {"path": "/health", "port": 8080},
                            "initialDelaySeconds": 30,
                            "periodSeconds": 30,
                        },
                    }],
                },
            },
        },
    }


def generate_github_actions(name: str, region: str = "us-central1") -> dict:
    return {
        "name": f"{name} CI/CD",
        "on": {
            "push": {"branches": ["main"]},
            "pull_request": {"branches": ["main"]},
        },
        "env": {
            "PROJECT_ID": "${{ secrets.GCP_PROJECT_ID }}",
            "REGION": region,
            "SERVICE_NAME": name,
        },
        "jobs": {
            "lint-and-test": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {"uses": "actions/setup-python@v5", "with": {"python-version": "3.11"}},
                    {"name": "Install dependencies", "run": "pip install -r requirements.txt"},
                    {"name": "Lint", "run": "ruff check app/ tests/"},
                    {"name": "Unit tests", "run": "pytest tests/ -v --junitxml=test-results.xml"},
                    {"name": "Eval tests", "run": "python evals/test_harness.py",
                     "env": {"GOOGLE_API_KEY": "${{ secrets.GOOGLE_API_KEY }}"}},
                ],
            },
            "build-and-deploy": {
                "needs": "lint-and-test",
                "if": "github.ref == 'refs/heads/main'",
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    # Pin to commit SHA in production: "google-github-actions/auth@<COMMIT_SHA>"
                    {"id": "auth", "uses": "google-github-actions/auth@5a50e581162a13f4baa8916d01180d2acbc04363",  # v2.1.0
                     "with": {"credentials_json": "${{ secrets.GCP_SA_KEY }}"}},
                    {"name": "Build and push", "run": (
                        f"docker build -t {region}-docker.pkg.dev/${{{{ secrets.GCP_PROJECT_ID }}}}/{name}/{name}:${{{{ github.sha }}}} . && "
                        f"gcloud auth configure-docker {region}-docker.pkg.dev && "
                        f"docker push {region}-docker.pkg.dev/${{{{ secrets.GCP_PROJECT_ID }}}}/{name}/{name}:${{{{ github.sha }}}}"
                    )},
                    {"name": "Deploy to Cloud Run", "run": (
                        f"gcloud run deploy {name} "
                        f"--image {region}-docker.pkg.dev/${{{{ secrets.GCP_PROJECT_ID }}}}/{name}/{name}:${{{{ github.sha }}}} "
                        f"--region {region} --allow-unauthenticated "
                        f"--set-env-vars GOOGLE_CLOUD_PROJECT=${{{{ secrets.GCP_PROJECT_ID }}}}"
                    )},
                ],
            },
        },
    }


def generate_eval_harness(name: str) -> str:
    return f'''"""Evaluation harness for {name} workflow.

Runs the workflow against test cases and reports pass/fail rates.
Use as CI gate: block deployment on eval failure.
"""

import json
import sys
import time
from pathlib import Path

TEST_CASES = [
    {{
        "id": "happy_path_001",
        "description": "Basic successful execution",
        "input": "Process a standard request",
        "expected_status": "ok",
        "max_latency_ms": 30000,
    }},
    {{
        "id": "edge_empty_input",
        "description": "Handle empty input gracefully",
        "input": "",
        "expected_status": "error",
    }},
    {{
        "id": "edge_long_input",
        "description": "Handle unusually long input",
        "input": "x" * 5000,
        "max_latency_ms": 30000,
    }},
]


def run_eval(test_case: dict) -> dict:
    """Run a single evaluation case. Override for your workflow."""
    # TODO: Import and run your actual workflow
    # from app.workflow import graph_agent
    # result = await runner.run(query=test_case["input"])

    start = time.monotonic()
    try:
        # Placeholder — replace with real workflow invocation
        result = {{"status": "ok"}}
        elapsed_ms = (time.monotonic() - start) * 1000

        checks = []
        if "expected_status" in test_case:
            checks.append(result.get("status") == test_case["expected_status"])
        if "max_latency_ms" in test_case:
            checks.append(elapsed_ms <= test_case["max_latency_ms"])

        passed = all(checks) if checks else True
        return {{
            "test_id": test_case["id"],
            "passed": passed,
            "latency_ms": elapsed_ms,
            "checks": checks,
            "result": result,
        }}
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {{
            "test_id": test_case["id"],
            "passed": False,
            "latency_ms": elapsed_ms,
            "error": str(e),
        }}


def main():
    print(f"Eval harness: {name}")
    print(f"Test cases: {{len(TEST_CASES)}}\\n")

    results = []
    for tc in TEST_CASES:
        r = run_eval(tc)
        results.append(r)
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{{status}}] {{tc['id']}}: {{tc['description']}} ({{r.get('latency_ms', 0):.0f}}ms)")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    rate = passed / total if total > 0 else 0

    print(f"\\n---")
    print(f"Results: {{passed}}/{{total}} passed ({{rate:.0%}})")

    # Write results for CI
    report = {{
        "workflow": "{name}",
        "passed": passed,
        "total": total,
        "pass_rate": rate,
        "results": results,
    }}
    Path("eval-results.json").write_text(json.dumps(report, indent=2))

    if rate < 1.0:
        print("\\nEval gate: BLOCKED — not all tests passed")
        sys.exit(1)
    else:
        print("\\nEval gate: PASSED")


if __name__ == "__main__":
    main()
'''


def generate_ecs_task_definition(name: str, region: str = "us-east-1") -> dict:
    return {
        "family": name,
        "networkMode": "awsvpc",
        "requiresCompatibilities": ["FARGATE"],
        "cpu": "512",
        "memory": "1024",
        "executionRoleArn": f"arn:aws:iam::${{AWS_ACCOUNT_ID}}:role/ecsTaskExecutionRole",
        "taskRoleArn": f"arn:aws:iam::${{AWS_ACCOUNT_ID}}:role/{name}-task-role",
        "containerDefinitions": [{
            "name": name,
            "image": f"${{AWS_ACCOUNT_ID}}.dkr.ecr.{region}.amazonaws.com/{name}:latest",
            "portMappings": [{"containerPort": 8080}],
            "environment": [
                {"name": "LOG_LEVEL", "value": "INFO"},
                {"name": "MODEL_NAME", "value": "gemini-2.5-flash"},
            ],
            "secrets": [
                {"name": "GOOGLE_API_KEY", "valueFrom": f"arn:aws:secretsmanager:{region}:${{AWS_ACCOUNT_ID}}:secret:google-api-key"},
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": f"/ecs/{name}",
                    "awslogs-region": region,
                    "awslogs-stream-prefix": "ecs",
                },
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
            },
        }],
    }


def generate_eks_deployment(name: str, region: str = "us-east-1") -> dict:
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "labels": {"app": name}},
        "spec": {
            "replicas": 2,
            "selector": {"matchLabels": {"app": name}},
            "strategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {"maxSurge": 1, "maxUnavailable": 0},
            },
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": {
                    "serviceAccountName": f"{name}-sa",
                    "containers": [{
                        "name": name,
                        "image": f"${{AWS_ACCOUNT_ID}}.dkr.ecr.{region}.amazonaws.com/{name}:latest",
                        "ports": [{"containerPort": 8080}],
                        "env": [
                            {"name": "LOG_LEVEL", "value": "INFO"},
                            {"name": "AWS_REGION", "value": region},
                        ],
                        "resources": {
                            "limits": {"cpu": "1000m", "memory": "512Mi"},
                            "requests": {"cpu": "250m", "memory": "256Mi"},
                        },
                        "readinessProbe": {
                            "httpGet": {"path": "/health", "port": 8080},
                            "initialDelaySeconds": 10,
                        },
                        "livenessProbe": {
                            "httpGet": {"path": "/health", "port": 8080},
                            "initialDelaySeconds": 30,
                        },
                    }],
                },
            },
        },
    }


def generate_lambda_config(name: str) -> dict:
    return {
        "function_name": name,
        "package_type": "Image",
        "image_uri": f"${{AWS_ACCOUNT_ID}}.dkr.ecr.${{AWS_REGION}}.amazonaws.com/{name}:latest",
        "timeout": 300,
        "memory_size": 1024,
        "environment": {
            "LOG_LEVEL": "INFO",
            "MODEL_NAME": "gemini-2.5-flash",
        },
        "triggers": {
            "api_gateway": {
                "type": "http",
                "path": "/workflow",
                "method": "POST",
            },
        },
    }


def generate_container_apps_config(name: str, region: str = "eastus") -> dict:
    return {
        "type": "Microsoft.App/containerApps",
        "apiVersion": "2024-03-01",
        "name": name,
        "location": region,
        "properties": {
            "configuration": {
                "ingress": {
                    "external": True,
                    "targetPort": 8080,
                    "allowInsecure": False,
                },
                "secrets": [
                    {"name": "google-api-key", "value": "${{GOOGLE_API_KEY}}"},
                ],
                "activeRevisionsMode": "Single",
            },
            "template": {
                "containers": [{
                    "name": name,
                    "image": f"myacr.azurecr.io/{name}:latest",
                    "env": [
                        {"name": "LOG_LEVEL", "value": "INFO"},
                        {"name": "MODEL_NAME", "value": "gemini-2.5-flash"},
                        {"name": "GOOGLE_API_KEY", "secretRef": "google-api-key"},
                    ],
                    "resources": {
                        "cpu": 0.5,
                        "memory": "1Gi",
                    },
                    "probes": [{
                        "type": "Liveness",
                        "httpGet": {"path": "/health", "port": 8080},
                        "initialDelaySeconds": 30,
                        "periodSeconds": 30,
                    }],
                }],
                "scale": {
                    "minReplicas": 0,
                    "maxReplicas": 10,
                },
            },
        },
    }


def generate_aks_deployment(name: str) -> dict:
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "labels": {"app": name}},
        "spec": {
            "replicas": 2,
            "selector": {"matchLabels": {"app": name}},
            "strategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {"maxSurge": 1, "maxUnavailable": 0},
            },
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": {
                    "containers": [{
                        "name": name,
                        "image": f"myacr.azurecr.io/{name}:latest",
                        "ports": [{"containerPort": 8080}],
                        "env": [
                            {"name": "LOG_LEVEL", "value": "INFO"},
                        ],
                        "envFrom": [{
                            "secretRef": {"name": f"{name}-secrets"},
                        }],
                        "resources": {
                            "limits": {"cpu": "1000m", "memory": "512Mi"},
                            "requests": {"cpu": "250m", "memory": "256Mi"},
                        },
                        "readinessProbe": {
                            "httpGet": {"path": "/health", "port": 8080},
                            "initialDelaySeconds": 10,
                        },
                        "livenessProbe": {
                            "httpGet": {"path": "/health", "port": 8080},
                            "initialDelaySeconds": 30,
                        },
                    }],
                },
            },
        },
    }


def package_workflow(name: str, source_dir: str, target: str, output_dir: str, region: str = "us-central1") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    generated = []

    # Dockerfile (always generated)
    dockerfile = generate_dockerfile(name, source_dir)
    (out / "Dockerfile").write_text(dockerfile)
    generated.append("Dockerfile")

    # GCP targets
    if target in ("cloud-run", "all"):
        cr_yaml = generate_cloud_run_yaml(name, region)
        (out / "cloud-run.yaml").write_text(yaml.dump(cr_yaml, default_flow_style=False) if yaml else json.dumps(cr_yaml, indent=2))
        generated.append("cloud-run.yaml")

        cb = generate_cloudbuild(name, source_dir, region)
        (out / "cloudbuild.yaml").write_text(yaml.dump(cb, default_flow_style=False, sort_keys=False) if yaml else json.dumps(cb, indent=2))
        generated.append("cloudbuild.yaml")

        gh = generate_github_actions(name, region)
        (out / "github-actions.yml").write_text(yaml.dump(gh, default_flow_style=False, sort_keys=False) if yaml else json.dumps(gh, indent=2))
        generated.append("github-actions.yml")

    if target in ("agent-engine", "all"):
        ae = generate_agent_engine_config(name)
        (out / "agent-engine.yaml").write_text(yaml.dump(ae, default_flow_style=False) if yaml else json.dumps(ae, indent=2))
        generated.append("agent-engine.yaml")

    if target in ("gke", "all"):
        gke = generate_gke_yaml(name, region)
        (out / "gke-deployment.yaml").write_text(yaml.dump(gke, default_flow_style=False) if yaml else json.dumps(gke, indent=2))
        generated.append("gke-deployment.yaml")

    # AWS targets
    if target in ("ecs", "all"):
        ecs = generate_ecs_task_definition(name, "us-east-1")
        (out / "ecs-task-definition.yaml").write_text(yaml.dump(ecs, default_flow_style=False) if yaml else json.dumps(ecs, indent=2))
        generated.append("ecs-task-definition.yaml")

    if target in ("eks", "all"):
        eks = generate_eks_deployment(name)
        (out / "eks-deployment.yaml").write_text(yaml.dump(eks, default_flow_style=False) if yaml else json.dumps(eks, indent=2))
        generated.append("eks-deployment.yaml")

    if target in ("lambda", "all"):
        lam = generate_lambda_config(name)
        (out / "lambda-config.yaml").write_text(yaml.dump(lam, default_flow_style=False) if yaml else json.dumps(lam, indent=2))
        generated.append("lambda-config.yaml")

    # Azure targets
    if target in ("container-apps", "all"):
        ca = generate_container_apps_config(name)
        (out / "container-apps.yaml").write_text(yaml.dump(ca, default_flow_style=False) if yaml else json.dumps(ca, indent=2))
        generated.append("container-apps.yaml")

    if target in ("aks", "all"):
        aks = generate_aks_deployment(name)
        (out / "aks-deployment.yaml").write_text(yaml.dump(aks, default_flow_style=False) if yaml else json.dumps(aks, indent=2))
        generated.append("aks-deployment.yaml")

    # Eval harness
    eval_harness = generate_eval_harness(name)
    (out / "evals" / "test_harness.py").write_text(eval_harness)
    (out / "evals" / "__init__.py").write_text(f"# Eval harness for {name}\n")
    generated.append("evals/test_harness.py")

    print(f"\nPackaged '{name}' for {target}:")
    for f in generated:
        print(f"  {out / f}")


def main():
    parser = argparse.ArgumentParser(
        description="Package an ADK workflow for deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--source", default="app", help="Source directory containing workflow code (default: app)")
    parser.add_argument("--name", required=True, help="Workflow/service name")
    parser.add_argument("--target", required=True, choices=list(TARGETS.keys()),
                        help="Deployment target")
    parser.add_argument("--output-dir", default=".", help="Output directory for generated artifacts")
    parser.add_argument("--region", default="us-central1", help="GCP region (default: us-central1)")

    args = parser.parse_args()

    print(f"Packaging workflow '{args.name}'")
    print(f"  Source: {args.source}")
    print(f"  Target: {args.target} — {TARGETS[args.target]}")
    print(f"  Region: {args.region}")

    if args.target == "agent-engine":
        print("\n  Note: Agent Engine deployment uses 'adk deploy' command.")
        print("  The generated config is for reference. See:")
        print("  https://cloud.google.com/agent-engine/docs/deploy")

    package_workflow(args.name, args.source, args.target, args.output_dir, args.region)


if __name__ == "__main__":
    main()
