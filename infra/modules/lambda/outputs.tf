output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.this.function_name
}

output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.this.arn
}

output "role_name" {
  description = "Name of the execution role, for attaching further permissions"
  value       = aws_iam_role.function.name
}

output "log_group_name" {
  description = "CloudWatch log group that receives the function logs"
  value       = aws_cloudwatch_log_group.function.name
}
