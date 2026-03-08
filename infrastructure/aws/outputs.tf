output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "db_endpoint" {
  description = "RDS cluster endpoint"
  value       = module.database.cluster_endpoint
}

output "redis_endpoint" {
  description = "Redis primary endpoint address"
  value       = module.cache.primary_endpoint_address
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.compute.alb_dns_name
}

output "s3_bucket_name" {
  description = "Name of the documents S3 bucket"
  value       = module.storage.documents_bucket_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.compute.ecs_cluster_name
}

output "ecr_backend_repository_url" {
  description = "URL of the backend ECR repository"
  value       = module.storage.ecr_backend_repository_url
}

output "ecr_frontend_repository_url" {
  description = "URL of the frontend ECR repository"
  value       = module.storage.ecr_frontend_repository_url
}
