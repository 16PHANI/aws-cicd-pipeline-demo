# Remote state is not wired up by default. Terraform can't create the S3
# bucket and DynamoDB lock table and then use them as its own backend in
# the same apply, so bootstrapping has to happen once, separately (either
# by hand or with a tiny one-off Terraform config that only creates those
# two resources). Once that bucket and table exist, uncomment this block
# and run `terraform init -migrate-state`.
#
# terraform {
#   backend "s3" {
#     bucket         = "REPLACE-WITH-YOUR-TFSTATE-BUCKET"
#     key            = "aws-cicd-pipeline-demo/terraform.tfstate"
#     region         = "ap-south-1"
#     dynamodb_table = "tfstate-locks"
#     encrypt        = true
#   }
# }
