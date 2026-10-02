variable "aws_region" {
  description = "Region for every resource in this environment"
  type        = string
  default     = "eu-central-1"
}

variable "package_path" {
  description = "Deployment zip built by python -m tools.package_lambda"
  type        = string
  default     = "../../../dist/lambda.zip"
}

variable "schedule_expression" {
  description = "When the check runs"
  type        = string
  default     = "cron(0 6 * * ? *)"
}

variable "max_critical_missing" {
  description = "Critical patches allowed before an instance is non-compliant"
  type        = number
  default     = 0
}

variable "max_security_missing" {
  description = "Security patches allowed before an instance is non-compliant"
  type        = number
  default     = 0
}

variable "max_scan_age_days" {
  description = "Days since the last scan before an instance is stale"
  type        = number
  default     = 7
}
