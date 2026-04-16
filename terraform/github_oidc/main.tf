terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Local backend — state stays in this directory (gitignored via projects/alex/.gitignore)
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}
