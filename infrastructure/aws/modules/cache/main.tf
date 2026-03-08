resource "aws_security_group" "redis" {
  name_prefix = "complianceagent-redis-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "complianceagent-${var.environment}"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "complianceagent-${var.environment}"
  description                = "ComplianceAgent Redis cluster"
  node_type                  = var.redis_node_type
  num_cache_clusters         = 2
  port                       = 6379
  parameter_group_name       = "default.redis7"
  engine_version             = "7.0"
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  automatic_failover_enabled = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}
