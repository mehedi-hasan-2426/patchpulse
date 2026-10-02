variable "name" {
  description = "Name for the function, its role, log group and schedule"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9-_]{1,56}$", var.name))
    error_message = "name must be 1 to 56 letters, digits, hyphens or underscores."
  }
}

variable "package_path" {
  description = "Path to the deployment zip built by tools/package_lambda.py"
  type        = string
}

variable "schedule_expression" {
  description = "EventBridge schedule, for example cron(0 6 * * ? *) for 06:00 UTC daily"
  type        = string
  default     = "cron(0 6 * * ? *)"

  validation {
    condition     = can(regex("^(cron|rate)\\(.+\\)$", var.schedule_expression))
    error_message = "schedule_expression must be a cron() or rate() expression."
  }
}

variable "environment_variables" {
  description = "Environment variables passed to the function, such as PATCHPULSE_ limits"
  type        = map(string)
  default     = {}
}

variable "log_retention_days" {
  description = "How long CloudWatch keeps the function logs"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365], var.log_retention_days)
    error_message = "log_retention_days must be a CloudWatch retention value up to 365."
  }
}

variable "memory_size" {
  description = "Function memory in MB"
  type        = number
  default     = 256

  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 1024
    error_message = "memory_size must be between 128 and 1024 MB."
  }
}

variable "timeout_seconds" {
  description = "Function timeout in seconds"
  type        = number
  default     = 30

  validation {
    condition     = var.timeout_seconds >= 1 && var.timeout_seconds <= 300
    error_message = "timeout_seconds must be between 1 and 300."
  }
}

variable "tags" {
  description = "Tags applied to every resource the module creates"
  type        = map(string)
  default     = {}
}
