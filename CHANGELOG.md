# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] — 2026-05-18

### Added
- **25+ Rule Milestone Reached**: Expanded rule catalog to 26 static analysis rules spanning all 5 DevOps domains.
- **Rule Pack Presets**:
  - Added `--preset` CLI option supporting `security`, `debt`, and `all` rule packs.
  - Configuration support for `preset: security` / `preset: debt` in `.configlens.yml`.
- **Kubernetes Privileged Container Detection**:
  - Added `k8s-privileged-container` (CRITICAL) rule preventing host root escalation.
- **Tuned Heuristics**:
  - Allowed consecutive `RUN` instructions in intermediate Dockerfile builder stages for optimal build caching.
  - Hardened multi-document YAML stream loader to handle empty documents and comment separators.

---

## [0.1.0] — 2026-05-16

### Added
- **Core CLI Engine**: Multi-domain static analysis engine with `--fail-on` exit codes and deterministic sorting.
- **5 Supported DevOps Configuration Domains**:
  - **GitHub Actions**: Unpinned action versions, missing dependency caching, duplicate setup steps.
  - **Dockerfile**: Base image `:latest` tags, running as root user, consecutive `RUN` layers, hardcoded secrets.
  - **Docker Compose**: Hardcoded credentials, missing restart policies, unpinned service tags, broad `0.0.0.0` port bindings.
  - **Terraform**: Plaintext secrets, unpinned provider versions, missing `lifecycle.prevent_destroy`, unused variables.
  - **Kubernetes**: Missing CPU/memory limits, missing liveness/readiness probes, root containers, `:latest` image tags.
- **Reporting System**:
  - Colorized terminal report with per-category grouping and finding summary.
  - Machine-readable JSON output schema via `--format json`.
  - OASIS SARIF v2.1.0 report generator via `--format sarif` for GitHub Code Scanning.
- **CI/CD Integrations**:
  - Composite GitHub Action (`action.yml`) for automated PR gating.
  - Pre-commit repository hook (`.pre-commit-hooks.yaml`).
- **Configuration & Suppressions**:
  - Project configuration via `.configlens.yml` with rule enabling/disabling and severity overrides.
  - Inline comment suppression (`# configlens-ignore: <rule-id>`).
