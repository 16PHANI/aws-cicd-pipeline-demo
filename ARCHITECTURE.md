# Architecture

## Request path

```
Internet
   |
   v
[ALB :80]  (security group: alb-sg, 0.0.0.0/0 -> 80)
   |
   v
[Target Group]  health check: GET /health every 15s
   |
   v
[Auto Scaling Group, 1-2x EC2]  (security group: app-sg, ALB only -> app port)
   |  each instance, via user_data.sh.tpl:
   |    - installs Docker
   |    - clones this repo
   |    - docker build + docker run, gunicorn serving the Flask app
   v
[gunicorn -> Flask app]
   |
   +--> /health   liveness
   +--> /ready    readiness
   +--> /metrics  Prometheus exposition format
   +--> /api/tasks  the actual API
```

## Delivery path

```
git push
   |
   v
GitHub Actions: ci.yml (lint, test+coverage, bandit, docker build, terraform checks)
   |  on push to main, after ci.yml passes
   v
GitHub Actions: cd.yml
   +--> publish-image: build + push to ghcr.io, tagged latest and <sha>
   +--> terraform-plan: OIDC into AWS, terraform plan (skipped unless AWS_ROLE_ARN is set)
```

## Observability path

```
Flask app --> /metrics --> Prometheus (scrapes every 15s) --> Grafana dashboard
                                |
                         (in AWS: CloudWatch instead, via EC2/ALB metrics)
                                v
                    3 alarms (CPU, ALB 5xx, unhealthy hosts) --> SNS --> email
```

## Decisions and why

**Default VPC instead of a custom one.** A new VPC means subnets, route tables, an internet gateway, NAT if you want private subnets, and a lot of surface area that has nothing to do with what this repo is demonstrating. Using the account's default VPC means `terraform apply` works in a fresh account without any networking prerequisites. A production version of this would almost certainly want its own VPC; the network module is small enough to swap out without touching compute or monitoring.

**ALB + ASG instead of one EC2 instance.** The earlier version of this project was a single EC2 instance with a security group. That's a fine learning exercise but it's not how anyone runs a service that needs to stay up: one instance is one failure domain, and there's no way to roll out a change without downtime. An ALB with a target group health-checking `/health`, in front of an Auto Scaling Group, is the smallest setup that actually tolerates an instance failing or being replaced.

**IMDSv2 enforced, SSH off by default.** `metadata_options.http_tokens = "required"` on the launch template closes the classic SSRF-to-instance-credentials path (an app bug that lets an attacker make an HTTP request can otherwise reach the instance metadata service and steal the IAM role's temporary credentials). SSH is opt-in via `ssh_cidr`; the IAM role attaches `AmazonSSMManagedInstanceCore` so you can get a shell through Session Manager instead, which doesn't need an open port 22 or a keypair to manage.

**Three CloudWatch alarms, not one.** High CPU is the alarm every tutorial includes and the least useful one on its own; a service can be CPU-fine and still be returning 500s to every user. ALB 5xx rate and unhealthy host count are closer to what actually pages someone in a real incident, so they're in here from the start instead of being a "future improvement."

**GHCR over Docker Hub.** Pushing to `ghcr.io` only needs the `GITHUB_TOKEN` every workflow already has. No account to create, no secret to add, no rate limit to hit. The image is public the moment the repo is public.

**Terraform plan via OIDC, off by default.** Long-lived AWS access keys sitting in repo secrets are a liability even in a demo repo. OIDC federation means GitHub Actions assumes a role for the duration of the job and nothing else ever holds a credential. It's gated behind a repo variable so that cloning this repo and running CI doesn't silently expect you to have an AWS account connected.
