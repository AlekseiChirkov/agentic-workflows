---
trigger: always_on
---
# Infrastructure Standards

Applies to all IaC code: Terraform, CDK, Pulumi, Docker, CI/CD configs.

---

## General Principles

- **IaC is code** — same quality standards apply: modularity, naming, documentation, review
- **No manual changes** to resources managed by IaC — all changes go through code
- **Least privilege IAM** — every service account/role gets only what it needs, nothing more
- **No secrets in code** — use Secret Manager (GCP), Secrets Manager (AWS), or Vault
- **Encryption by default** — at rest and in transit for all data stores and communication
- **Immutable infrastructure** — replace, don't patch

---

## Terraform Structure

```
infrastructure/
├── modules/
│   ├── cloud-run-service/     # Reusable module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── postgres-instance/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── staging/
│   │   ├── main.tf            # Calls modules with staging values
│   │   ├── variables.tf
│   │   └── terraform.tfvars   # Non-secret values
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
└── shared/
    └── state-backend.tf       # Remote state configuration
```

**Module rules:**
- Every module has `variables.tf`, `outputs.tf`, `main.tf` minimum
- Every variable has `description` and `type` — `validation` block where applicable
- Every output has `description`
- Module README documents: what it creates, required variables, outputs, example usage

---

## Terraform Code Standards

```hcl
# variables.tf — always typed and described
variable "service_name" {
  type        = string
  description = "Name of the Cloud Run service. Used as resource name prefix."

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,28}[a-z0-9]$", var.service_name))
    error_message = "Service name must be lowercase alphanumeric with hyphens, 4-30 chars."
  }
}

variable "min_instances" {
  type        = number
  description = "Minimum number of Cloud Run instances. Set to 1 to avoid cold starts."
  default     = 0
}

# main.tf — explicit, no magic
resource "google_cloud_run_v2_service" "main" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }
    }
  }
}
```

**Rules:**
- No hardcoded project IDs, regions, or environment-specific values in modules
- Use `locals` for computed values, not inline expressions in resources
- Run `terraform fmt` before every commit
- Run `terraform validate` in CI
- Use `terraform plan` output as PR artifact

---

## IAM: Least Privilege Pattern

```hcl
# Create dedicated service account per service
resource "google_service_account" "api_service" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service account for ${var.service_name}"
  project      = var.project_id
}

# Grant only what is needed — never roles/editor or roles/owner
resource "google_project_iam_member" "api_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api_service.email}"
}
```

**Forbidden IAM:**
- `roles/editor` or `roles/owner` on service accounts
- `allUsers` or `allAuthenticatedUsers` on non-public resources
- Sharing service accounts between services
- Long-lived service account keys (use Workload Identity)

---

## Docker Standards

```dockerfile
# Always pin base image to specific digest or version tag — never :latest
FROM python:3.12.3-slim-bookworm AS base

# Non-root user — required
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy dependency files first — layer cache optimization
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

# Copy source code last
COPY src/ ./src/

USER appuser

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Rules:**
- Multi-stage builds for compiled languages
- Never run as root
- Pin exact versions — never `:latest`
- `.dockerignore` must exclude: `.git`, `tests/`, `*.pyc`, `.env`, local configs

---

## Observability: Required from Day One

Every service must expose:

**Structured logging:**
```python
# Every request logged with trace context
{"level": "info", "event": "request_completed", "method": "POST",
 "path": "/orders", "status": 201, "duration_ms": 45, "trace_id": "..."}
```

**Health endpoints:**
```python
# /health/live  — is the process alive?
# /health/ready — can it serve traffic? (DB connected, dependencies up)
@router.get("/health/live")
async def liveness() -> dict:
    return {"status": "ok"}

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict:
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}
```

**Metrics:** expose `/metrics` in Prometheus format via `prometheus-fastapi-instrumentator`.

---

## Environment Configuration

```python
# config.py — Pydantic Settings, all config from environment
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str
    database_pool_size: int = 10

    # GCP
    gcp_project_id: str
    gcp_region: str = "us-central1"

    # App
    environment: Literal["local", "staging", "production"]
    log_level: str = "INFO"
    secret_key: str  # injected from Secret Manager in production

settings = Settings()
```

**Rules:**
- All config from environment variables — no config files committed with values
- Secrets injected at runtime from Secret Manager — never in `.env` files committed to git
- `.env.example` committed with all keys and placeholder values
- Local `.env` in `.gitignore`
