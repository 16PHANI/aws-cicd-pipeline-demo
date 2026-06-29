output "alb_dns_name" {
  description = "Public DNS name of the load balancer. curl http://<this>/health once apply finishes."
  value       = module.compute.alb_dns_name
}

output "asg_name" {
  description = "Name of the Auto Scaling Group running the app"
  value       = module.compute.asg_name
}
