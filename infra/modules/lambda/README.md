# Lambda module

Runs the PatchPulse handler on a schedule.

It creates a Python 3.13 arm64 function, an execution role that can only write to its own
log group, a log group with a retention period, and an EventBridge schedule that invokes
the function.

## Example

```hcl
module "patchpulse" {
  source = "github.com/mehedi-hasan-2426/patchpulse//infra/modules/lambda"

  name         = "patchpulse-dev"
  package_path = "${path.root}/../../../dist/lambda.zip"

  environment_variables = {
    PATCHPULSE_MAX_SCAN_AGE_DAYS = "7"
  }
}
```

Pin `source` to a tag or commit with `?ref=` in real use.

## Inputs

| Name | Default | Description |
|---|---|---|
| `name` | required | Name for the function, role, log group and schedule (1 to 56 characters) |
| `package_path` | required | Zip built by `python -m tools.package_lambda` |
| `schedule_expression` | `cron(0 6 * * ? *)` | EventBridge `cron()` or `rate()` expression |
| `environment_variables` | `{}` | Passed to the function |
| `log_retention_days` | `30` | CloudWatch retention value up to 365 |
| `memory_size` | `256` | 128 to 1024 MB |
| `timeout_seconds` | `30` | 1 to 300 |
| `tags` | `{}` | Applied to every resource |

## Outputs

| Name | Description |
|---|---|
| `function_name` | Name of the Lambda function |
| `function_arn` | ARN of the Lambda function |
| `role_name` | Execution role, for attaching further permissions |
| `log_group_name` | Log group for the function |
