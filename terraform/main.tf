terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "aws-cicd-pipeline-demo"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

module "network" {
  source   = "./modules/network"
  app_port = var.app_port
  ssh_cidr = var.ssh_cidr
}

module "compute" {
  source = "./modules/compute"

  environment            = var.environment
  instance_type          = var.instance_type
  app_port               = var.app_port
  vpc_id                 = module.network.vpc_id
  subnet_ids             = module.network.subnet_ids
  alb_security_group_id  = module.network.alb_security_group_id
  app_security_group_id  = module.network.app_security_group_id
  asg_min_size           = var.asg_min_size
  asg_max_size           = var.asg_max_size
  asg_desired_capacity   = var.asg_desired_capacity
}

module "monitoring" {
  source = "./modules/monitoring"

  environment              = var.environment
  asg_name                 = module.compute.asg_name
  target_group_arn_suffix  = module.compute.target_group_arn_suffix
  load_balancer_arn_suffix = module.compute.load_balancer_arn_suffix
  alarm_email              = var.alarm_email
}
