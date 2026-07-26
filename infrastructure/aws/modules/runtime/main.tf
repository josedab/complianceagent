# ComplianceAgent — ECS Runtime Module
# Deploys API, frontend, worker, beat, and migration task definitions + services
# with Secrets Manager injection, autoscaling, and deployment circuit breakers.

# ------------------------------------------------------------------
# Secrets Manager data source — expects a JSON secret with keys:
#   SECRET_KEY, DATABASE_URL, REDIS_URL, COPILOT_API_KEY, etc.
# ------------------------------------------------------------------
data "aws_secretsmanager_secret" "app" {
  name = var.secrets_manager_name
}

data "aws_secretsmanager_secret_version" "app" {
  secret_id = data.aws_secretsmanager_secret.app.id
}

# ------------------------------------------------------------------
# IAM — task execution role (pull images, read secrets, write logs)
# ------------------------------------------------------------------
data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name               = "complianceagent-${var.environment}-exec"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets" {
  name = "secrets-access"
  role = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [data.aws_secretsmanager_secret.app.arn]
    }]
  })
}

# ------------------------------------------------------------------
# IAM — task role (runtime permissions: S3, SES, etc.)
# ------------------------------------------------------------------
resource "aws_iam_role" "task" {
  name               = "complianceagent-${var.environment}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy" "task_s3" {
  name = "s3-access"
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ]
      Resource = [
        var.s3_bucket_arn,
        "${var.s3_bucket_arn}/*"
      ]
    }]
  })
}

# ------------------------------------------------------------------
# CloudWatch Log Groups
# ------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/complianceagent-${var.environment}/api"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/complianceagent-${var.environment}/frontend"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/complianceagent-${var.environment}/worker"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "beat" {
  name              = "/ecs/complianceagent-${var.environment}/beat"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "migrate" {
  name              = "/ecs/complianceagent-${var.environment}/migrate"
  retention_in_days = 14
}

# ------------------------------------------------------------------
# Shared secret references for container definitions
# ------------------------------------------------------------------
locals {
  secret_arn     = data.aws_secretsmanager_secret.app.arn
  s3_bucket_name = element(split(":", var.s3_bucket_arn), 5)

  backend_secrets = [
    { name = "SECRET_KEY", valueFrom = "${local.secret_arn}:SECRET_KEY::" },
    { name = "DATABASE_URL", valueFrom = "${local.secret_arn}:DATABASE_URL::" },
    { name = "REDIS_URL", valueFrom = "${local.secret_arn}:REDIS_URL::" },
    { name = "COPILOT_API_KEY", valueFrom = "${local.secret_arn}:COPILOT_API_KEY::" },
    { name = "SENTRY_DSN", valueFrom = "${local.secret_arn}:SENTRY_DSN::" },
    { name = "GITHUB_APP_ID", valueFrom = "${local.secret_arn}:GITHUB_APP_ID::" },
    { name = "GITHUB_APP_PRIVATE_KEY", valueFrom = "${local.secret_arn}:GITHUB_APP_PRIVATE_KEY::" },
    { name = "GITHUB_WEBHOOK_SECRET", valueFrom = "${local.secret_arn}:GITHUB_WEBHOOK_SECRET::" },
    { name = "STRIPE_API_KEY", valueFrom = "${local.secret_arn}:STRIPE_API_KEY::" },
    { name = "STRIPE_WEBHOOK_SECRET", valueFrom = "${local.secret_arn}:STRIPE_WEBHOOK_SECRET::" },
    { name = "SMTP_HOST", valueFrom = "${local.secret_arn}:SMTP_HOST::" },
    { name = "SMTP_USER", valueFrom = "${local.secret_arn}:SMTP_USER::" },
    { name = "SMTP_PASSWORD", valueFrom = "${local.secret_arn}:SMTP_PASSWORD::" },
    { name = "SMTP_FROM_EMAIL", valueFrom = "${local.secret_arn}:SMTP_FROM_EMAIL::" },
    { name = "EMAIL_API_ENDPOINT", valueFrom = "${local.secret_arn}:EMAIL_API_ENDPOINT::" },
    { name = "EMAIL_API_KEY", valueFrom = "${local.secret_arn}:EMAIL_API_KEY::" },
  ]

  backend_env = [
    { name = "ENVIRONMENT", value = var.environment },
    { name = "DEBUG", value = "false" },
    { name = "LOG_LEVEL", value = "INFO" },
    { name = "NEXT_PUBLIC_APP_URL", value = var.app_public_url },
    { name = "NEXT_PUBLIC_API_URL", value = var.api_public_url },
    { name = "AUTH_COOKIE_DOMAIN", value = var.auth_cookie_domain },
    { name = "CORS_ORIGINS", value = jsonencode([var.app_public_url]) },
    { name = "ALLOWED_HOSTS", value = jsonencode([
      trimprefix(var.api_public_url, "https://"),
      trimprefix(var.app_public_url, "https://"),
    ]) },
    { name = "AVATAR_BUCKET", value = local.s3_bucket_name },
    { name = "AWS_REGION", value = var.aws_region },
  ]
}

# ------------------------------------------------------------------
# Task Definition — API
# ------------------------------------------------------------------
resource "aws_ecs_task_definition" "api" {
  family                   = "complianceagent-api-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name         = "api"
    image        = "${var.ecr_api_url}:${var.image_tag}"
    essential    = true
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]

    environment = local.backend_env
    secrets     = local.backend_secrets

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 30
    }

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.api.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "api"
      }
    }

    stopTimeout = 30
  }])
}

# ------------------------------------------------------------------
# Task Definition — Frontend
# ------------------------------------------------------------------
resource "aws_ecs_task_definition" "frontend" {
  family                   = "complianceagent-frontend-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name         = "frontend"
    image        = "${var.ecr_frontend_url}:${var.image_tag}"
    essential    = true
    portMappings = [{ containerPort = 3000, protocol = "tcp" }]

    environment = [
      { name = "NODE_ENV", value = "production" },
      { name = "NEXT_PUBLIC_API_URL", value = var.api_public_url },
      { name = "NEXT_PUBLIC_APP_URL", value = var.app_public_url },
    ]

    healthCheck = {
      command     = ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 20
    }

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "frontend"
      }
    }
  }])
}

# ------------------------------------------------------------------
# Task Definition — Worker (crawler image)
# ------------------------------------------------------------------
resource "aws_ecs_task_definition" "worker" {
  family                   = "complianceagent-worker-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "worker"
    image     = "${var.ecr_crawler_url}:${var.image_tag}"
    essential = true
    command   = ["celery", "-A", "app.workers", "worker", "--loglevel=info", "--concurrency=4"]

    environment = local.backend_env
    secrets     = local.backend_secrets

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "worker"
      }
    }

    stopTimeout = 120
  }])
}

# ------------------------------------------------------------------
# Task Definition — Beat (single instance scheduler)
# ------------------------------------------------------------------
resource "aws_ecs_task_definition" "beat" {
  family                   = "complianceagent-beat-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "beat"
    image     = "${var.ecr_api_url}:${var.image_tag}"
    essential = true
    command   = ["celery", "-A", "app.workers", "beat", "--loglevel=info"]

    environment = local.backend_env
    secrets     = local.backend_secrets

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.beat.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "beat"
      }
    }
  }])
}

# ------------------------------------------------------------------
# Task Definition — Migration (one-shot)
# ------------------------------------------------------------------
resource "aws_ecs_task_definition" "migrate" {
  family                   = "complianceagent-migrate-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "migrate"
    image     = "${var.ecr_api_url}:${var.image_tag}"
    essential = true
    command   = ["alembic", "upgrade", "head"]

    environment = local.backend_env
    secrets     = local.backend_secrets

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.migrate.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "migrate"
      }
    }
  }])
}

# ------------------------------------------------------------------
# ECS Services — API
# ------------------------------------------------------------------
resource "aws_ecs_service" "api" {
  name            = "complianceagent-api-${var.environment}"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.backend_target_group_arn
    container_name   = "api"
    container_port   = 8000
  }
}

# ------------------------------------------------------------------
# ECS Services — Frontend
# ------------------------------------------------------------------
resource "aws_ecs_service" "frontend" {
  name            = "complianceagent-frontend-${var.environment}"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.frontend_target_group_arn
    container_name   = "frontend"
    container_port   = 3000
  }
}

# ------------------------------------------------------------------
# ECS Services — Worker
# ------------------------------------------------------------------
resource "aws_ecs_service" "worker" {
  name            = "complianceagent-worker-${var.environment}"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }
}

# ------------------------------------------------------------------
# ECS Services — Beat (exactly 1 replica)
# ------------------------------------------------------------------
resource "aws_ecs_service" "beat" {
  name            = "complianceagent-beat-${var.environment}"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.beat.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }
}

# ------------------------------------------------------------------
# Autoscaling — API
# ------------------------------------------------------------------
resource "aws_appautoscaling_target" "api" {
  max_capacity       = var.api_max_count
  min_capacity       = var.api_desired_count
  resource_id        = "service/${var.ecs_cluster_name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "api-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# ------------------------------------------------------------------
# Autoscaling — Worker
# ------------------------------------------------------------------
resource "aws_appautoscaling_target" "worker" {
  max_capacity       = var.worker_max_count
  min_capacity       = var.worker_desired_count
  resource_id        = "service/${var.ecs_cluster_name}/${aws_ecs_service.worker.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "worker_cpu" {
  name               = "worker-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.worker.resource_id
  scalable_dimension = aws_appautoscaling_target.worker.scalable_dimension
  service_namespace  = aws_appautoscaling_target.worker.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
