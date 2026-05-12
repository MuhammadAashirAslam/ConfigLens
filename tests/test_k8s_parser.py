"""Unit tests for Kubernetes manifest parser."""

from pathlib import Path
from configlens.parsers.k8s_parser import parse_k8s_content, parse_k8s_file

SAMPLE_K8S = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-api
  namespace: production
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: web-api
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
      containers:
        - name: web
          image: myorg/web-api:v1.2.3
          resources:
            limits:
              cpu: "500m"
              memory: "512Mi"
            requests:
              cpu: "100m"
              memory: "128Mi"
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  ports:
    - port: 80
      targetPort: 8080
"""


def test_k8s_parser_multi_document():
    """Verify multi-document manifest parsing extracts workloads and containers."""
    mf = parse_k8s_content(SAMPLE_K8S, Path("deployment.yaml"))
    assert len(mf.documents) == 2

    dep = mf.documents[0]
    assert dep.kind == "Deployment"
    assert dep.name == "web-api"
    assert dep.namespace == "production"
    assert dep.pod_security_context.get("runAsNonRoot") is True
    assert len(dep.containers) == 1

    container = dep.containers[0]
    assert container.name == "web"
    assert container.image == "myorg/web-api:v1.2.3"
    assert container.resources.get("limits", {}).get("cpu") == "500m"
    assert container.liveness_probe is not None
    assert container.readiness_probe is not None

    svc = mf.documents[1]
    assert svc.kind == "Service"
    assert svc.name == "web-service"
    assert len(svc.containers) == 0


def test_k8s_parser_graceful_missing_file():
    """Verify non-existent manifest file degrades gracefully."""
    mf = parse_k8s_file(Path("does_not_exist.yaml"))
    assert len(mf.documents) == 0
    assert len(mf.parse_errors) == 1
