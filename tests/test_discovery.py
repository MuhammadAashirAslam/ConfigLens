"""Unit tests for DevOps configuration file discovery and classification."""

from pathlib import Path
from configlens.discovery import (
    detect_category,
    discover_files,
    is_docker_compose,
    is_dockerfile,
    is_github_actions_workflow,
    is_kubernetes,
    is_terraform,
    parse_ignore_file,
    should_ignore_path,
)
from configlens.models import Category


def test_github_actions_detection(tmp_path: Path):
    """Test detection of GitHub Actions workflow files."""
    wf1 = tmp_path / ".github" / "workflows" / "build.yml"
    wf2 = tmp_path / ".github" / "workflows" / "deploy.yaml"
    other = tmp_path / "workflows" / "test.yml"
    non_yaml = tmp_path / ".github" / "workflows" / "README.md"

    wf1.parent.mkdir(parents=True)
    wf1.write_text("name: Build\n", encoding="utf-8")
    wf2.write_text("name: Deploy\n", encoding="utf-8")
    other.parent.mkdir(parents=True)
    other.write_text("name: Test\n", encoding="utf-8")
    non_yaml.write_text("# Workflows\n", encoding="utf-8")

    assert is_github_actions_workflow(wf1) is True
    assert is_github_actions_workflow(wf2) is True
    assert is_github_actions_workflow(other) is False
    assert is_github_actions_workflow(non_yaml) is False
    assert detect_category(wf1) == Category.GITHUB_ACTIONS


def test_dockerfile_detection(tmp_path: Path):
    """Test detection of Dockerfiles by name, suffix, and content."""
    df1 = tmp_path / "Dockerfile"
    df2 = tmp_path / "Dockerfile.prod"
    df3 = tmp_path / "app.dockerfile"
    df_content = tmp_path / "build_step"
    regular = tmp_path / "main.py"

    df1.write_text("FROM python:3.11-slim\n", encoding="utf-8")
    df2.write_text("FROM alpine:latest\n", encoding="utf-8")
    df3.write_text("FROM golang:1.21\n", encoding="utf-8")
    df_content.write_text("# Container build\nFROM node:18\n", encoding="utf-8")
    regular.write_text("print('hello')\n", encoding="utf-8")

    assert is_dockerfile(df1) is True
    assert is_dockerfile(df2) is True
    assert is_dockerfile(df3) is True
    assert is_dockerfile(df_content) is True
    assert is_dockerfile(regular) is False
    assert detect_category(df1) == Category.DOCKERFILE


def test_docker_compose_detection(tmp_path: Path):
    """Test detection of Docker Compose files."""
    dc1 = tmp_path / "docker-compose.yml"
    dc2 = tmp_path / "compose.yaml"
    dc_content = tmp_path / "stack.yml"
    regular = tmp_path / "config.yml"

    dc1.write_text("services:\n  web:\n    image: nginx\n", encoding="utf-8")
    dc2.write_text("services:\n  db:\n    image: postgres\n", encoding="utf-8")
    dc_content.write_text("services:\n  redis:\n    image: redis\n", encoding="utf-8")
    regular.write_text("app_name: myapp\nversion: 1\n", encoding="utf-8")

    assert is_docker_compose(dc1) is True
    assert is_docker_compose(dc2) is True
    assert is_docker_compose(dc_content) is True
    assert is_docker_compose(regular) is False
    assert detect_category(dc1) == Category.DOCKER_COMPOSE


def test_terraform_detection(tmp_path: Path):
    """Test detection of Terraform HCL files."""
    tf1 = tmp_path / "main.tf"
    tf2 = tmp_path / "terraform.tfvars"
    regular = tmp_path / "main.tf.bak"

    tf1.write_text('resource "aws_s3_bucket" "b" {}\n', encoding="utf-8")
    tf2.write_text('region = "us-east-1"\n', encoding="utf-8")
    regular.write_text('backup\n', encoding="utf-8")

    assert is_terraform(tf1) is True
    assert is_terraform(tf2) is True
    assert is_terraform(regular) is False
    assert detect_category(tf1) == Category.TERRAFORM


def test_kubernetes_detection(tmp_path: Path):
    """Test detection of Kubernetes YAML manifests."""
    k8s1 = tmp_path / "k8s" / "deployment.yaml"
    k8s2 = tmp_path / "manifests" / "service.yml"
    not_k8s = tmp_path / "other.yaml"

    k8s1.parent.mkdir(parents=True)
    k8s1.write_text("apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app\n", encoding="utf-8")
    k8s2.parent.mkdir(parents=True)
    k8s2.write_text("apiVersion: v1\nkind: Service\nmetadata:\n  name: svc\n", encoding="utf-8")
    not_k8s.write_text("foo: bar\nbaz: qux\n", encoding="utf-8")

    assert is_kubernetes(k8s1) is True
    assert is_kubernetes(k8s2) is True
    assert is_kubernetes(not_k8s) is False
    assert detect_category(k8s1) == Category.KUBERNETES


def test_discover_files_with_gitignore(tmp_path: Path):
    """Test directory discovery respects .gitignore patterns and ignores build dirs."""
    # Create valid files
    (tmp_path / "Dockerfile").write_text("FROM alpine\n", encoding="utf-8")
    (tmp_path / "main.tf").write_text('variable "x" {}\n', encoding="utf-8")

    # Create ignored file
    (tmp_path / "ignored.tf").write_text('variable "ignored" {}\n', encoding="utf-8")
    (tmp_path / ".gitignore").write_text("ignored.tf\n*.secret.tf\n", encoding="utf-8")

    # Create default ignored directory
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "Dockerfile").write_text("FROM alpine\n", encoding="utf-8")

    discovered = discover_files(tmp_path, respect_gitignore=True)
    paths = [f.relative_path.as_posix() for f in discovered]

    assert "Dockerfile" in paths
    assert "main.tf" in paths
    assert "ignored.tf" not in paths
    assert "__pycache__/Dockerfile" not in paths


def test_discover_files_only_category(tmp_path: Path):
    """Test filtering discovered files by category."""
    (tmp_path / "Dockerfile").write_text("FROM alpine\n", encoding="utf-8")
    (tmp_path / "main.tf").write_text('variable "x" {}\n', encoding="utf-8")

    discovered = discover_files(tmp_path, only={Category.DOCKERFILE})
    assert len(discovered) == 1
    assert discovered[0].category == Category.DOCKERFILE
    assert discovered[0].relative_path.name == "Dockerfile"
