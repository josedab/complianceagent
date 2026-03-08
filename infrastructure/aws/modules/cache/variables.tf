variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
}

variable "ecs_security_group_id" {
  description = "ECS security group ID (allowed to connect to Redis)"
  type        = string
}
