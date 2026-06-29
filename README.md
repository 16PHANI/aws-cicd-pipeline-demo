# aws-cicd-pipeline-demo

A small Flask API wrapped in the kind of delivery pipeline you'd actually want around a service in production: linting, tests with a coverage gate, a multi-stage Docker build, a GitHub Actions CI/CD setup that publishes a real image with zero configuration, and Terraform that stands up an ALB, an Auto Scaling Group, IAM roles, and CloudWatch alarms on AWS.

The API itself is a task tracker. It's deliberately simple, in-memory storage, a handful of REST endpoints. That's on purpose. This repo isn't trying to impress anyone with the to-do app; it's a vehicle for the pipeline and the infrastructure around it, which is the part that took the actual time.

[![CI](https://github.com/16PHANI/aws-cicd-pipeline-demo/actions/workflows/ci.yml/badge.svg)](https://github.com/16PHANI/aws-cicd-pipeline-demo/actions/workflows/ci.yml)
[![CD](https://github.com/16PHANI/aws-cicd-pipeline-demo/actions/workflows/cd.yml/badge.svg)](https://github.com/16PHANI/aws-cicd-pipeline-demo/actions/workflows/cd.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Why this exists

I wanted something I could point to that shows the full path from a code change to a running service: lint and test it, build it, scan it, ship it, monitor it, and have an alarm fire if it breaks. A lot of portfolio projects stop at "it has a Dockerfile." This one has a CI pipeline that actually runs on every push, a CD pipeline that actually publishes a container image to GHCR with no secrets to configure, and Terraform that models a real (if small) AWS architecture instead of a single bare EC2 instance.

## What's in here

```
app/             Flask app: routes, in-memory store, JSON logging, request-id middleware
tests/           pytest suite, 16 tests, coverage gate enforced at 85% in CI
terraform/       modular IaC: network, compute (ALB + ASG), monitoring (CloudWatch + SNS)
monitoring/      Prometheus scrape config + a Grafana dashboard, wired up in docker-compose
.github/         CI workflow, CD workflow, Dependabot config
Dockerfile       multi-stage build, non-root user, IMDSv2-only at the infra level
docker-compose.yml   app + Prometheus + Grafana, one command to look at real metrics locally
```

Full write-up of the architecture, including the diagram and the reasoning behind the ALB/ASG setup, is in [ARCHITECTURE.md](ARCHITECTURE.md). Incident-handling notes (what to check first if an alarm fires) are in [RUNBOOK.md](RUNBOOK.md).

## Running it locally

You need Python 3.11 and, for the container/infra parts, Docker.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

make test          # pytest, 16 tests
make cov           # pytest with coverage, fails under 85%
make lint          # flake8 + black --check + isort --check
make run           # flask dev server on :5000, for quick manual checks
```

Try it once it's up:

```bash
curl localhost:5000/health
curl -X POST localhost:5000/api/tasks -H 'Content-Type: application/json' -d '{"title":"ship it"}'
curl localhost:5000/api/tasks
```

`/health` is a liveness check (is the process alive). `/ready` is readiness (can it actually serve traffic). They're separate on purpose, a slow dependency should fail readiness, not liveness, otherwise the orchestrator restarts a perfectly healthy process for no reason.

## Running the full stack

```bash
make up      # docker compose up --build -d: api + prometheus + grafana
make logs    # tail the api's JSON logs
make down
```

Grafana comes up on `localhost:3000` (anonymous viewer access is enabled for local use, login is admin/admin if you need to edit anything) with a Prometheus data source and a starter dashboard already provisioned: request rate by status code, p95 latency by path, current 5xx rate. Prometheus itself is on `localhost:9090` if you'd rather query directly.

## Testing in detail

```bash
flake8 app tests                 # style
black --check app tests          # formatting
isort --check-only app tests     # import order
pytest --cov=app --cov-report=term-missing --cov-fail-under=85
bandit -r app -ll                 # static security scan
```

All of the above run in CI on every push and pull request (`.github/workflows/ci.yml`), along with `terraform fmt -check`, `terraform validate`, and `tflint` against the Terraform code, and a Docker build to make sure the image still builds. None of it needs AWS credentials, so it runs the same way on a fork as it does here.

If you have `pre-commit` installed, `pre-commit install` will run black, isort, flake8, and `terraform fmt`/`validate` automatically before each commit, so CI is mostly confirming what you already know locally.

## CI/CD

Two workflows:

- **ci.yml** runs on every push and PR: lint, test with the coverage gate, bandit, a Docker build (not pushed), and the Terraform checks above.
- **cd.yml** runs only on pushes to `main`, after `ci.yml` on that commit. It builds the Docker image and pushes it to GitHub Container Registry tagged `latest` and with the commit SHA, using the `GITHUB_TOKEN` that GitHub already provides to every workflow. No secret to add, no registry account to create.

There's a second job in `cd.yml`, `terraform-plan`, that runs `terraform plan` against real AWS using OIDC federation (no static AWS access keys stored in the repo at all). It's gated behind a repo variable, `AWS_ROLE_ARN`, and skips cleanly if that variable isn't set, rather than failing. To turn it on:

1. Create an IAM role in your AWS account that trusts GitHub's OIDC provider for this specific repo (AWS has a guide for this under "Configuring OpenID Connect in Amazon Web Services").
2. Set the repo variables `AWS_ROLE_ARN` and `AWS_REGION` under Settings -> Secrets and variables -> Actions -> Variables.
3. Push to `main`. The plan job will start showing up instead of being skipped.

I'm leaving it off by default so this repo doesn't assume anyone reading it has an AWS account they want this touching.

## Infrastructure

The Terraform under `terraform/` is split into three modules instead of one flat file, which is the difference between "it works" and "someone else can read it":

- `modules/network`: security groups, using the account's default VPC so this is runnable with zero extra setup.
- `modules/compute`: a launch template (IMDSv2 enforced, no SSH unless you explicitly set `ssh_cidr`, access via SSM Session Manager instead), an Auto Scaling Group, and an Application Load Balancer health-checking `/health`.
- `modules/monitoring`: an SNS topic and three CloudWatch alarms, high CPU, ALB 5xx rate, and unhealthy target count, not just CPU like most demo projects stop at.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # fill in your values
terraform init
terraform plan
terraform apply
```

Remote state (S3 + DynamoDB lock table) isn't wired up by default, see the comment in `terraform/backend.tf` for why and how to enable it once those resources exist.

**This costs real money once applied.** An ALB plus a `t3.micro` instance is a few dollars a day, not free-tier-forever. Run `terraform destroy` when you're done looking at it.

## Honest limitations

A few things this repo does not do, written down instead of glossed over:

- The task store is in-memory and per-process. Restart the container, or scale past one instance behind the ALB, and you'll see different tasks depending on which instance answers. A real version of this would put Postgres or DynamoDB behind the same `TaskStore` interface; the routes wouldn't need to change.
- The in-process lock in `app/store.py` protects against concurrent requests within one gunicorn worker, not across workers or instances. Fine for a demo, not a substitute for a real datastore's own concurrency control.
- `terraform-plan` in CD is the only job that needs real AWS access, and it's off by default (see above). Nothing else in this repo will touch your AWS bill unless you run `terraform apply` yourself.
- There's no auth on the API. Adding it would mean deciding on a real identity provider, which felt out of scope for what this repo is trying to show.

## License

MIT, see [LICENSE](LICENSE).
