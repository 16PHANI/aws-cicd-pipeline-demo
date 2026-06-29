variable "environment" {
  type = string
}

variable "asg_name" {
  type = string
}

variable "target_group_arn_suffix" {
  type = string
}

variable "load_balancer_arn_suffix" {
  type = string
}

variable "alarm_email" {
  type    = string
  default = ""
}
