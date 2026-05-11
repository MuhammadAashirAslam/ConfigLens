"""Unit tests for Terraform HCL parser."""

from pathlib import Path
from configlens.parsers.terraform_parser import parse_terraform_content, parse_terraform_file

SAMPLE_TF = """
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment target environment"
}

resource "aws_s3_bucket" "data_bucket" {
  bucket = "company-data-prod"

  lifecycle {
    prevent_destroy = true
  }
}
"""


def test_terraform_parser_blocks():
    """Verify HCL blocks and attributes are parsed with accurate line numbers."""
    tf = parse_terraform_content(SAMPLE_TF, Path("main.tf"))

    assert len(tf.blocks) >= 3
    assert len(tf.variables) == 1
    assert len(tf.providers) == 1
    assert len(tf.resources) == 1

    var = tf.variables[0]
    assert var.labels == ["environment"]
    assert var.attributes["default"] == "production"

    prov = tf.providers[0]
    assert prov.labels == ["aws"]
    assert prov.attributes["region"] == "us-east-1"

    res = tf.resources[0]
    assert res.labels == ["aws_s3_bucket", "data_bucket"]
    assert res.attributes["bucket"] == "company-data-prod"
    assert len(res.nested_blocks) == 1
    lifecycle = res.nested_blocks[0]
    assert lifecycle.block_type == "lifecycle"
    assert lifecycle.attributes.get("prevent_destroy") == "true"


def test_terraform_parser_graceful_missing():
    """Verify non-existent file handling degrades gracefully."""
    tf = parse_terraform_file(Path("non_existent.tf"))
    assert len(tf.blocks) == 0
    assert len(tf.parse_errors) == 1
