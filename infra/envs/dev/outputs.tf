output "function_name" {
  description = "Invoke with: aws lambda invoke --function-name <this> response.json"
  value       = module.patchpulse.function_name
}

output "log_group_name" {
  description = "Where the function logs go"
  value       = module.patchpulse.log_group_name
}
