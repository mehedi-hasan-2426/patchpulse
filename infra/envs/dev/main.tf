terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.67"
    }
  }

  backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "patchpulse"
      Environment = local.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  environment = "dev"
}

module "patchpulse" {
  source = "../../modules/lambda"

  name                = "patchpulse-${local.environment}"
  package_path        = var.package_path
  schedule_expression = var.schedule_expression
  log_retention_days  = 14

  environment_variables = {
    PATCHPULSE_FIXTURE_PATH         = "fixtures/fleet.json"
    PATCHPULSE_MAX_CRITICAL_MISSING = tostring(var.max_critical_missing)
    PATCHPULSE_MAX_SECURITY_MISSING = tostring(var.max_security_missing)
    PATCHPULSE_MAX_SCAN_AGE_DAYS    = tostring(var.max_scan_age_days)
  }
}
