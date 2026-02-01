---
sidebar_position: 2
title: AWS Deployment
description: Deploy ComplianceAgent on AWS with Terraform
---

# AWS Deployment

Production deployment on AWS using Terraform for infrastructure as code.

## Architecture Overview

```
                                   ┌─────────────────────────────────────────────────────────────────┐
                                   │                          AWS Cloud                               │
                                   │                                                                  │
                                   │  ┌──────────────────────────────────────────────────────────┐   │
                                   │  │                         VPC                               │   │
┌──────────┐      ┌──────────┐    │  │                                                           │   │
│  Users   │─────▶│CloudFront│────┼──┼──▶┌─────────────┐    ┌─────────────┐                     │   │
└──────────┘      └──────────┘    │  │   │     ALB     │───▶│  ECS Fargate │                     │   │
                                   │  │   └─────────────┘    │  (Backend)   │                     │   │
                                   │  │                       └──────┬──────┘                     │   │
                                   │  │                              │                            │   │
                                   │  │  ┌───────────────────────────┼────────────────────────┐  │   │
                                   │  │  │         Private Subnets   │                        │  │   │
                                   │  │  │                           ▼                        │  │   │
                                   │  │  │  ┌─────────────┐   ┌─────────────┐                 │  │   │
                                   │  │  │  │    RDS      │   │ElastiCache  │                 │  │   │
                                   │  │  │  │ (Postgres)  │   │  (Redis)    │                 │  │   │
                                   │  │  │  └─────────────┘   └─────────────┘                 │  │   │
                                   │  │  │                                                     │  │   │
                                   │  │  │  ┌─────────────┐   ┌─────────────┐                 │  │   │
                                   │  │  │  │OpenSearch   │   │   Secrets   │                 │  │   │
                                   │  │  │  │ (Search)    │   │  Manager    │                 │  │   │
                                   │  │  │  └─────────────┘   └─────────────┘                 │  │   │
                                   │  │  └────────────────────────────────────────────────────┘  │   │
                                   │  │                                                           │   │
                                   │  └──────────────────────────────────────────────────────────┘   │
                                   │                                                                  │
                                   └─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- AWS Account with appropriate permissions
- Terraform 1.5+
- AWS CLI configured
- Domain name (optional, for custom domain)

## Quick Start

```bash
cd infrastructure/terraform/aws

# Initialize Terraform
terraform init

# Review plan
terraform plan -var-file="production.tfvars"

# Apply infrastructure
terraform apply -var-file="production.tfvars"
```

## Terraform Configuration

### Main Configuration

```hcl
# main.tf
terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "complianceagent-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "ComplianceAgent"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
```

### Variables

```hcl
# variables.tf
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "ecs_cpu" {
  description = "ECS task CPU units"
  type        = number
  default     = 1024
}

variable "ecs_memory" {
  description = "ECS task memory (MB)"
  type        = number
  default     = 2048
}

variable "min_capacity" {
  description = "Minimum ECS tasks"
  type        = number
  default     = 2
}

variable "max_capacity" {
  description = "Maximum ECS tasks"
  type        = number
  default     = 10
}
```

### Production Values

```hcl
# production.tfvars
environment       = "production"
aws_region        = "us-east-1"
domain_name       = "compliance.example.com"
db_instance_class = "db.r6g.xlarge"
ecs_cpu           = 2048
ecs_memory        = 4096
min_capacity      = 3
max_capacity      = 20
```

### VPC Configuration

```hcl
# vpc.tf
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "complianceagent-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Environment = var.environment
  }
}
```

### ECS Configuration

```hcl
# ecs.tf
resource "aws_ecs_cluster" "main" {
  name = "complianceagent-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "complianceagent-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ecs_cpu
  memory                   = var.ecs_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "${aws_ecr_repository.backend.repository_url}:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]
      
      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_secretsmanager_secret.database_url.arn
        },
        {
          name      = "GITHUB_TOKEN"
          valueFrom = aws_secretsmanager_secret.github_token.arn
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "backend"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

resource "aws_ecs_service" "backend" {
  name            = "backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.min_capacity
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  depends_on = [aws_lb_listener.https]
}
```

### RDS Configuration

```hcl
# rds.tf
resource "aws_db_instance" "main" {
  identifier = "complianceagent-${var.environment}"

  engine         = "postgres"
  engine_version = "16.1"
  instance_class = var.db_instance_class

  allocated_storage     = 100
  max_allocated_storage = 500
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn

  db_name  = "complianceagent"
  username = "complianceagent"
  password = random_password.db_password.result

  multi_az               = true
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "complianceagent-final-${formatdate("YYYY-MM-DD", timestamp())}"

  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  tags = {
    Name = "complianceagent-${var.environment}"
  }
}
```

### Auto Scaling

```hcl
# autoscaling.tf
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

resource "aws_appautoscaling_policy" "memory" {
  name               = "memory-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 80
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
```

## Secrets Management

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "complianceagent/production/github-token" \
  --secret-string "ghp_xxxxxxxxxxxx"

aws secretsmanager create-secret \
  --name "complianceagent/production/secret-key" \
  --secret-string "your-secret-key-here"
```

## Deployment Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy-aws.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: complianceagent-backend
  ECS_SERVICE: backend
  ECS_CLUSTER: complianceagent-production

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG ./backend
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --force-new-deployment
```

## Monitoring

### CloudWatch Alarms

```hcl
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "complianceagent-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "CPU utilization is too high"
  
  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.backend.name
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

## Cost Estimation

| Component | Instance/Size | Monthly Cost (approx) |
|-----------|--------------|----------------------|
| ECS Fargate | 3x 2vCPU/4GB | $150 |
| RDS Postgres | db.r6g.xlarge Multi-AZ | $400 |
| ElastiCache | cache.r6g.large | $150 |
| ALB | Standard | $30 |
| CloudFront | 100GB transfer | $20 |
| **Total** | | **~$750/month** |

---

See also: [Kubernetes Deployment](./kubernetes) | [Environment Variables](./environment-variables)
