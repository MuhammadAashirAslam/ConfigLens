# ConfigLens — Rule Catalog & Reference Guide

This document catalogs every static analysis rule in ConfigLens, explaining its operational rationale, severity rating, anti-pattern example, and remediated configuration.

---

## 1. GitHub Actions

### `gha-unpinned-action-version`
- **Severity:** HIGH
- **Title:** Unpinned action version in workflow step
- **Rationale:** Referencing actions by mutable branch names (e.g., `@main`, `@master`) or release tags (e.g., `@v3`) allows upstream supply chain compromise or unexpected breaking changes to impact your CI. Pinning to a full 40-character commit SHA provides cryptographic immutability.
- **Bad:**
  ```yaml
  - uses: actions/checkout@main
  ```
- **Good:**
  ```yaml
  - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
  ```

---

### `gha-duplicate-setup-steps`
- **Severity:** MEDIUM
- **Title:** Duplicate action execution within job
- **Rationale:** Running the same action step (e.g. `actions/checkout` or `actions/setup-node`) multiple times in a single job indicates copy-paste errors or redundant build overhead.
- **Remediation:** Remove redundant steps or combine steps into composite actions.

---

### `gha-missing-caching`
- **Severity:** MEDIUM
- **Title:** Missing dependency caching in package setup action
- **Rationale:** Actions like `setup-python` and `setup-node` support first-class dependency caching. Omitting `cache:` wastes CI compute minutes and slows feedback loops.
- **Good:**
  ```yaml
  - uses: actions/setup-node@v4
    with:
      node-version: 20
      cache: npm
  ```

---

### `gha-missing-job-timeout`
- **Severity:** MEDIUM
- **Title:** Missing timeout on workflow job
- **Rationale:** Jobs without `timeout-minutes` can run up to 6 hours if hung on network requests or infinite loops, depleting organizational runner quotas.
- **Good:**
  ```yaml
  jobs:
    test:
      runs-on: ubuntu-latest
      timeout-minutes: 15
  ```

---

## 2. Dockerfile

### `dockerfile-latest-tag`
- **Severity:** HIGH
- **Title:** Base image uses latest or unpinned tag
- **Rationale:** `FROM node:latest` or `FROM alpine` produces non-deterministic builds. Upstream updates can introduce breaking changes or vulnerabilities without warning.
- **Good:**
  ```dockerfile
  FROM node:20.12.2-alpine3.19
  ```

---

### `dockerfile-running-as-root`
- **Severity:** CRITICAL
- **Title:** Container running as root user
- **Rationale:** Containers running without a `USER` instruction execute as `root`, increasing the severity of container breakout vulnerabilities.
- **Good:**
  ```dockerfile
  USER appuser
  ```

---

### `dockerfile-multiple-run-layers`
- **Severity:** LOW
- **Title:** Consecutive RUN instructions create extra image layers
- **Rationale:** Adjacent `RUN` instructions should be combined with `&&` and `\` to minimize image layer count and optimize caching.

---

### `dockerfile-baked-secrets`
- **Severity:** CRITICAL
- **Title:** Embedded plaintext secret in ARG or ENV
- **Rationale:** Declaring credentials in `ENV` or `ARG` persists secrets in image metadata and layers, making them readable by anyone with image access.

---

## 3. Docker Compose

### `compose-hardcoded-credentials`
- **Severity:** CRITICAL
- **Title:** Hardcoded credentials in environment variables
- **Rationale:** Storing plaintext database passwords or tokens in version-controlled compose files exposes credentials in git history.
- **Good:**
  ```yaml
  environment:
    - POSTGRES_PASSWORD=${DB_PASSWORD}
  ```

---

### `compose-missing-restart`
- **Severity:** MEDIUM
- **Title:** Missing container restart policy
- **Rationale:** Production services should define `restart: unless-stopped` or `restart: always` to ensure automatic recovery after host reboot or crash.

---

### `compose-latest-tag`
- **Severity:** HIGH
- **Title:** Service image uses latest tag
- **Rationale:** Using `:latest` causes unpredictable service drift across environments.

---

### `compose-broad-ports`
- **Severity:** HIGH
- **Title:** Database or internal service port exposed to 0.0.0.0
- **Rationale:** Internal datastores (PostgreSQL, Redis, MySQL) should not bind to `0.0.0.0`. Restrict to localhost (`127.0.0.1:5432:5432`) or use internal networks.

---

## 4. Terraform

### `tf-hardcoded-secret`
- **Severity:** CRITICAL
- **Title:** Hardcoded secret in Terraform configuration
- **Rationale:** Plaintext passwords in `.tf` files expose credentials in version control and state. Use input variables or secret managers (e.g. AWS Secrets Manager, Vault).

---

### `tf-unpinned-provider`
- **Severity:** HIGH
- **Title:** Unpinned or missing provider version constraint
- **Rationale:** Omitting `~>` or `=` provider constraints can cause `terraform init` to pull newer major provider versions with breaking schema changes.

---

### `tf-missing-prevent-destroy`
- **Severity:** HIGH
- **Title:** Missing prevent_destroy lifecycle protection on stateful resource
- **Rationale:** Stateful resources like `aws_db_instance` or `aws_s3_bucket` risk catastrophic data loss on accidental `terraform destroy`.

---

### `tf-unused-variables`
- **Severity:** LOW
- **Title:** Unused Terraform variable declaration
- **Rationale:** Unused variable declarations add maintenance debt and clutter module interfaces.

---

## 5. Kubernetes

### `k8s-missing-resource-limits`
- **Severity:** HIGH
- **Title:** Missing container resource limits
- **Rationale:** Workloads without CPU and memory limits can monopolize worker nodes, causing node unresponsiveness and noisy-neighbor outages.

---

### `k8s-missing-probes`
- **Severity:** MEDIUM
- **Title:** Missing health probes on service container
- **Rationale:** Long-running services without liveness and readiness probes prevent Kubernetes from routing traffic away from deadlocked pods or restarting failed containers.

---

### `k8s-root-container`
- **Severity:** CRITICAL
- **Title:** Container may run as root user
- **Rationale:** Lacking `securityContext.runAsNonRoot: true` or non-zero `runAsUser` permits container processes to run as root.

---

### `k8s-latest-image-tag`
- **Severity:** HIGH
- **Title:** Container image uses latest or untagged version
- **Rationale:** Untagged or `:latest` images violate immutability, causing different cluster nodes to run different builds of the same image tag.
