# ComplianceAgent Infrastructure - Terraform Configuration

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
