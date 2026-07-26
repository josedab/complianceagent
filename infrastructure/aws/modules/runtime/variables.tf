variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "secrets_manager_name" {
  description = "Name of the Secrets Manager JSON secret containing core, Stripe, and transactional-email credentials"
  type        = string
}

# --- ECR image URLs ---

variable "ecr_api_url" {
  description = "ECR repository URL for the API image"
  type        = string
}

variable "ecr_frontend_url" {
  description = "ECR repository URL for the frontend image"
  type        = string
}

variable "ecr_crawler_url" {
  description = "ECR repository URL for the crawler/worker image"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

# --- Network ---

variable "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  type        = string
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string
}

variable "backend_target_group_arn" {
  description = "ALB target group ARN for the backend API"
  type        = string
}

variable "frontend_target_group_arn" {
  description = "ALB target group ARN for the frontend"
  type        = string
}

# --- S3 ---

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for documents/evidence"
  type        = string
}

# --- Public URLs ---

variable "api_public_url" {
  description = "Public URL for the API (e.g., https://api.complianceagent.ai)"
  type        = string
  default     = "https://api.complianceagent.ai"
}

variable "app_public_url" {
  description = "Public URL for the frontend app (e.g., https://app.complianceagent.ai)"
  type        = string
  default     = "https://app.complianceagent.ai"
}

variable "auth_cookie_domain" {
  description = "Parent domain shared by API and frontend authentication cookies"
  type        = string
  default     = ".complianceagent.ai"
}

# --- Capacity ---

variable "api_cpu" {
  description = "CPU units for the API task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Memory in MiB for the API task"
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Desired number of API task replicas"
  type        = number
  default     = 2
}

variable "api_max_count" {
  description = "Maximum number of API task replicas for autoscaling"
  type        = number
  default     = 10
}

variable "frontend_cpu" {
  description = "CPU units for the frontend task"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Memory in MiB for the frontend task"
  type        = number
  default     = 512
}

variable "frontend_desired_count" {
  description = "Desired number of frontend task replicas"
  type        = number
  default     = 2
}

variable "worker_cpu" {
  description = "CPU units for the worker task"
  type        = number
  default     = 1024
}

variable "worker_memory" {
  description = "Memory in MiB for the worker task"
  type        = number
  default     = 2048
}

variable "worker_desired_count" {
  description = "Desired number of worker task replicas"
  type        = number
  default     = 2
}

variable "worker_max_count" {
  description = "Maximum number of worker task replicas for autoscaling"
  type        = number
  default     = 8
}
