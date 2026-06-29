#!/bin/bash
# Rendered by Terraform's templatefile() at launch-template creation time.
# ${app_port} below is substituted by Terraform, not by the shell.
set -euo pipefail

dnf update -y
dnf install -y docker git
systemctl enable --now docker

git clone https://github.com/16PHANI/aws-cicd-pipeline-demo.git /opt/app
cd /opt/app

docker build -t aws-cicd-pipeline-demo:latest .
docker run -d \
  --name app \
  --restart unless-stopped \
  -p ${app_port}:${app_port} \
  aws-cicd-pipeline-demo:latest
