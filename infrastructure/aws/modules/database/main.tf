resource "aws_security_group" "rds" {
  name_prefix = "complianceagent-rds-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "complianceagent-${var.environment}"
  subnet_ids = var.private_subnet_ids
}

resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "aws_rds_cluster" "main" {
  cluster_identifier     = "complianceagent-${var.environment}"
  engine                 = "aurora-postgresql"
  engine_version         = "16.1"
  database_name          = "complianceagent"
  master_username        = "complianceagent"
  master_password        = random_password.db_password.result
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"
  skip_final_snapshot     = var.environment != "production"

  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 16
  }

  tags = {
    Name = "complianceagent-${var.environment}"
  }
}

resource "aws_rds_cluster_instance" "main" {
  count              = 2
  identifier         = "complianceagent-${var.environment}-${count.index}"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name = "complianceagent/${var.environment}/db-credentials"
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = aws_rds_cluster.main.master_username
    password = random_password.db_password.result
    host     = aws_rds_cluster.main.endpoint
    port     = 5432
    database = aws_rds_cluster.main.database_name
  })
}
