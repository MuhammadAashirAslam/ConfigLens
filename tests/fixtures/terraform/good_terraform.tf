terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = "us-east-1"
  version = "~> 5.0"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Target environment"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Database master password"
}

resource "aws_db_instance" "production_db" {
  allocated_storage = 50
  engine            = "postgres"
  instance_class    = "db.t3.medium"
  name              = var.environment
  password          = var.db_password

  lifecycle {
    prevent_destroy = true
  }
}
