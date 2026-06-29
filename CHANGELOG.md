# Changelog

All notable changes to this project are recorded here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [2.0.0] - 2026-06-29

### Added
- Gunicorn as the production WSGI server instead of Flask's dev server.
- Structured JSON logging with a per-request id, propagated via `X-Request-ID`.
- `/ready` endpoint, separate from `/health` (liveness vs. readiness).
- Prometheus metrics endpoint (`/metrics`) via `prometheus-flask-exporter`.
- Input validation on task title/status with consistent JSON error responses.
- Pagination and status filtering on `GET /api/tasks`.
- pytest suite expanded from 4 to 16 tests; coverage gate enforced at 85% in CI.
- `bandit` static security scan and `pip-audit` dependency scan in CI.
- `pre-commit` config (black, isort, flake8, terraform fmt/validate).
- Multi-stage Dockerfile, smaller runtime image, explicit non-root user.
- `docker-compose.yml` running the app alongside Prometheus and a provisioned Grafana dashboard.
- Terraform split into `network` / `compute` / `monitoring` modules.
- Application Load Balancer + Auto Scaling Group, replacing the single bare EC2 instance.
- IAM role with SSM access (no SSH keypair required) and IMDSv2 enforced.
- CloudWatch alarms for ALB 5xx rate and unhealthy host count, in addition to CPU.
- `cd.yml`: publishes the Docker image to GHCR on every push to `main` using only `GITHUB_TOKEN`.
- Optional OIDC-based Terraform plan job in CD, gated behind a repo variable.
- `ARCHITECTURE.md`, `RUNBOOK.md`, `SECURITY.md`.

### Changed
- README rewritten to document the actual architecture and its tradeoffs, including an explicit "what this doesn't do" section.

## [1.0.0] - 2026-06-20

### Added
- Initial Flask Task API (in-memory, CRUD on `/api/tasks`, `/health`).
- Dockerfile (non-root, basic healthcheck).
- GitHub Actions: lint, test, Docker build (no push).
- Terraform: single EC2 instance, security group, CPU and status-check CloudWatch alarms.
