# Runbook

Operational notes for the alarms and deployment steps in this repo. Written so that whoever is on call (which, for a project this size, is just me) doesn't have to reconstruct the reasoning at 2am.

## Alarm: aws-cicd-demo-<env>-high-cpu

**What it means:** average CPU across the Auto Scaling Group has been above 80% for two 5-minute periods.

**First checks:**
1. CloudWatch -> EC2 -> per-instance CPU. Is it one instance or all of them?
2. If it's all instances and traffic actually went up, this might just be the ASG needing to scale out. Check `asg_max_size`, it defaults to 2; raise it if real load justifies it.
3. If it's one instance and traffic is normal, something on that box is stuck. Get a shell via SSM (`aws ssm start-session --target <instance-id>`) and check `docker stats` and `docker logs app`.

**If it's not resolving itself:** terminate the bad instance manually; the ASG will replace it from the launch template. That's the entire point of using an ASG instead of a single instance.

## Alarm: aws-cicd-demo-<env>-alb-5xx

**What it means:** more than 5 `5xx` responses from app targets (not from the ALB itself) in 5 minutes.

**First checks:**
1. Pull recent logs: `docker logs app --since 10m | grep '"status": 5'` on each instance, or check the JSON logs if they're being shipped anywhere.
2. The app's own error handler logs an `internal_error` entry with `request_id` for anything unhandled. Match that request id against the access log line for the same request to see the path and method that triggered it.
3. Check `/ready` directly. If it's returning 503, the store check is failing, which currently only happens if something is very wrong (see `app/main.py`, the `ready()` handler).

**Rollback:** redeploy the previous known-good image tag. Every image in GHCR is tagged with the commit SHA it was built from, so this is `docker pull ghcr.io/16phani/aws-cicd-pipeline-demo:<previous-sha>` on each instance, or re-running `user_data.sh` logic pointed at that tag.

## Alarm: aws-cicd-demo-<env>-unhealthy-hosts

**What it means:** the ALB's health check (`GET /health`, expects `200`) is failing for at least one target.

**First checks:**
1. Is the container even running? `docker ps` on the instance.
2. If it's running but failing health checks, hit `/health` directly from inside the instance (`curl localhost:5000/health`) to rule out a security group issue versus an actual app problem.
3. Check the Docker `HEALTHCHECK` status: `docker inspect --format='{{json .State.Health}}' app`.

## Deploying a change

Normal path: open a PR, let `ci.yml` run, merge to `main`, `cd.yml` builds and pushes the image automatically. The EC2 instances pull on launch (via `user_data.sh.tpl`), so getting a new image onto already-running instances means either:

- Replacing instances (`terraform apply` after bumping `asg_desired_capacity` down then up, or an instance refresh), or
- SSHing/SSM-ing in and running `docker pull` + `docker run` by hand for a quick fix.

A proper rolling deploy mechanism (ASG instance refresh tied to a new launch template version per release) is the natural next step here and is called out in the limitations section of the README rather than pretended to already exist.

## Getting a shell on an instance

No SSH key needed if `ssh_cidr` was left empty (the default):

```bash
aws ssm start-session --target <instance-id> --region ap-south-1
```

Requires the AWS CLI and Session Manager plugin installed locally, and IAM permissions to start a session, separate from the instance's own role.
