variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment name, used in resource names and tags"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "instance_type" {
  description = "EC2 instance type for the app launch template"
  type        = string
  default     = "t3.micro"
}

variable "app_port" {
  description = "Port the Flask/gunicorn app listens on inside the container"
  type        = number
  default     = 5000
}

variable "ssh_cidr" {
  description = "CIDR allowed to SSH into instances. Leave blank to disable SSH entirely and manage access via SSM Session Manager instead."
  type        = string
  default     = ""
}

variable "asg_min_size" {
  description = "Minimum number of instances in the Auto Scaling Group"
  type        = number
  default     = 1
}

variable "asg_max_size" {
  description = "Maximum number of instances in the Auto Scaling Group"
  type        = number
  default     = 2
}

variable "asg_desired_capacity" {
  description = "Desired number of instances in the Auto Scaling Group"
  type        = number
  default     = 1
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications via SNS. Leave blank to skip the subscription."
  type        = string
  default     = ""
}
