# Security

This is a portfolio/demo project, not a service handling real user data, but it's built the way I'd want a small production service built.

## What's already in place

- Container runs as a non-root user (uid 1000), defined explicitly in the Dockerfile rather than relying on the base image's default.
- EC2 launch template enforces IMDSv2 (`http_tokens = "required"`), closing the SSRF-to-credential-theft path that IMDSv1 leaves open.
- No SSH access by default. The security group only opens port 22 if `ssh_cidr` is explicitly set; instance access otherwise goes through SSM Session Manager, which is logged and doesn't require a keypair.
- IAM role on the instance is scoped to `AmazonSSMManagedInstanceCore` only, nothing broader.
- CI/CD uses OIDC federation for the optional Terraform plan job, no long-lived AWS access keys stored anywhere in the repo.
- `bandit` runs in CI on every push against the app code.
- `pip-audit` runs in CI against `requirements.txt` (advisory for now, see below).
- Dependabot is configured for pip, Docker base images, GitHub Actions, and Terraform providers, weekly.

## What's intentionally not done

- `pip-audit` in CI is currently advisory (`|| true`) rather than blocking. I'd rather have it visible in the CI log and decide case by case than have a transitive dependency's CVE with no available fix block every PR.
- There's no authentication on the API. It's an in-memory demo task tracker; adding auth would mean picking a real identity provider, which is a bigger decision than this repo needs to make.
- Terraform state is local by default (see `terraform/backend.tf`). Local state is fine for one person running this; it is not fine for a team, which is exactly why that file documents how to switch to an S3 + DynamoDB backend before this gets used by more than one person.

## Reporting an issue

If you find an actual security problem in this code (not in the AWS account it could theoretically deploy to, since nothing here is currently running), open an issue or reach me directly: phanishankaredu@gmail.com.
