# ComplianceAgent Infrastructure - Terraform Configuration

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    bucket         = "complianceagent-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
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

# --- Modules ---

module "vpc" {
  source = "./modules/vpc"

  environment = var.environment
  vpc_cidr    = var.vpc_cidr
  aws_region  = var.aws_region
}

module "compute" {
  source = "./modules/compute"

  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnets
}

module "database" {
  source = "./modules/database"

  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnets
  ecs_security_group_id = module.compute.ecs_security_group_id
}

module "cache" {
  source = "./modules/cache"

  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnets
  redis_node_type       = var.redis_node_type
  ecs_security_group_id = module.compute.ecs_security_group_id
}

module "storage" {
  source = "./modules/storage"

  environment = var.environment
}

module "runtime" {
  source = "./modules/runtime"

  environment          = var.environment
  aws_region           = var.aws_region
  secrets_manager_name = "complianceagent/${var.environment}/app-secrets"

  ecr_api_url      = module.storage.ecr_backend_repository_url
  ecr_frontend_url = module.storage.ecr_frontend_repository_url
  ecr_crawler_url  = module.storage.ecr_crawler_repository_url
  image_tag        = var.image_tag

  ecs_cluster_arn           = module.compute.ecs_cluster_arn
  ecs_cluster_name          = module.compute.ecs_cluster_name
  private_subnet_ids        = module.vpc.private_subnets
  ecs_security_group_id     = module.compute.ecs_security_group_id
  backend_target_group_arn  = module.compute.backend_target_group_arn
  frontend_target_group_arn = module.compute.frontend_target_group_arn
  s3_bucket_arn             = module.storage.documents_bucket_arn

  api_public_url     = "https://api.${var.domain_name}"
  app_public_url     = "https://app.${var.domain_name}"
  auth_cookie_domain = ".${var.domain_name}"
}
