output "primary_endpoint_address" {
  description = "Redis primary endpoint address"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "security_group_id" {
  description = "Redis security group ID"
  value       = aws_security_group.redis.id
}
