provider "aws" {
  region = "us-east-1"
}

variable "obsolete_api_key" {
  type        = string
  description = "Unused legacy key"
}

resource "aws_db_instance" "production_db" {
  allocated_storage = 20
  engine            = "postgres"
  instance_class    = "db.t3.micro"
  password          = "supersecret_password_123"
}
