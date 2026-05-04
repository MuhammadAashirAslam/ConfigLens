# ConfigLens

**Static Analysis & Technical Debt Detection for DevOps Configuration**

ConfigLens is an open-source static analysis CLI that scans repository DevOps configuration files — GitHub Actions workflows, Dockerfiles, Docker Compose files, Terraform, and Kubernetes manifests — and detects configuration debt, maintenance risks, and security drift without running containers or requiring cloud network access.

---

## Key Principles

- **Zero Network, Zero Build**: Operates strictly on local files on disk without external network calls or cluster dependencies.
- **Unified DevOps Mental Model**: A single CLI and consistent findings report across all DevOps configurations in a repo.
- **Actionable Insights**: Every finding includes the file location, exact line number, severity level, rule identifier, and a concrete fix suggestion.
- **Fast & Deterministic**: Sub-second scans designed for local developer pre-commit checks and CI pull-request gating.

---

## Supported Categories

| Category | File Detection Patterns | Example Debt Scanned |
|---|---|---|
| **GitHub Actions** | `.github/workflows/*.{yml,yaml}` | Unpinned actions, missing caching, open permissions |
| **Dockerfile** | `Dockerfile*`, `*.dockerfile` | Latest tags, running as root, unnecessary layers |
| **Docker Compose** | `compose*.{yml,yaml}`, `docker-compose*.{yml,yaml}` | Unpinned images, hardcoded secrets, broad ports |
| **Terraform** | `*.tf`, `*.tfvars` | Missing lifecycle blocks, unpinned providers, hardcoded secrets |
| **Kubernetes** | `*.{yml,yaml}` (with `apiVersion`/`kind`) | Missing resource limits, missing liveness probes, root containers |

---

## Installation

```bash
# Install editable development version
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

---

## Quickstart

```bash
# Scan current repository
configlens scan .

# Filter by category
configlens scan . --only github-actions,dockerfile

# Specify custom ignore file
configlens scan . --ignore .configlensignore

# Output results in JSON format
configlens scan . --format json
```

---

## Development

```bash
# Run unit tests
pytest

# Run tests with verbose output
pytest -v
```

---

## License

Distributed under the [MIT License](LICENSE). Copyright (c) 2026 Muhammad Aashir Aslam.
