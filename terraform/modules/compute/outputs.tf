output "alb_dns_name" {
  value = aws_lb.app.dns_name
}

output "asg_name" {
  value = aws_autoscaling_group.app.name
}

output "target_group_arn_suffix" {
  value = aws_lb_target_group.app.arn_suffix
}

output "load_balancer_arn_suffix" {
  value = aws_lb.app.arn_suffix
}
