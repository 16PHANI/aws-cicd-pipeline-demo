variable "app_port" {
  description = "Port the app listens on"
  type        = number
}

variable "ssh_cidr" {
  description = "CIDR allowed to SSH. Empty string disables the rule entirely."
  type        = string
  default     = ""
}
