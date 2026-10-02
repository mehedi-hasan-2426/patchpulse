# PatchPulse

Reports which EC2 instances are behind on security patches and produces an alert you can send
to the people who own them.

[![CI](https://github.com/mehedi-hasan-2426/patchpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/mehedi-hasan-2426/patchpulse/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB)
![Terraform 1.10+](https://img.shields.io/badge/terraform-1.10%2B-7B42BC)

## Overview

Patch dashboards show what is missing, but they rarely tell you which machines have stopped
reporting at all. PatchPulse checks every instance against a simple policy, flags instances
whose last patch scan is too old to trust, and lists the problems in one short message. It
runs from the command line or on a schedule in AWS Lambda.

## Example

```text
$ patchpulse --as-of 2026-10-01T12:00:00+00:00
PatchPulse: 3 of 5 instances need attention (2026-10-01T12:00:00+00:00)

- reporting-01 (i-0a1b2c3d4e5f6071b): stale, last patch scan 19 days ago
- web-02 (i-0a1b2c3d4e5f60719): non_compliant, 2 critical patches missing; 1 security patches missing
- batch-01 (i-0a1b2c3d4e5f6071a): non_compliant, 4 security patches missing
```

This is the output for the synthetic fleet in `fixtures/fleet.json`.

## How it works

```mermaid
flowchart LR
    schedule[EventBridge schedule] --> lambda[Lambda handler]
    cli[patchpulse CLI] --> source
    lambda --> source[Compliance source]
    source --> policy[Compliance policy]
    policy --> report[Fleet report]
    report --> alert[Alert text]
    report --> html[HTML export]
```

A compliance source returns one record per instance. The policy turns each record into one
of three states:

| State | When |
|---|---|
| `stale` | The last patch scan is older than the allowed age. Stale instances are listed first, because missing data can hide missing patches. |
| `non_compliant` | More critical or security patches are missing than the policy allows. |
| `compliant` | The scan is recent and the missing patches are within the limits. |

The report counts each state. If anything is stale or non-compliant, it also produces the
alert text shown above. The Lambda handler returns the report and alert as JSON. The CLI
prints the alert and can also write the report as an HTML file.

## Quick start

You need Python 3.12 or newer.

```sh
git clone https://github.com/mehedi-hasan-2426/patchpulse.git
cd patchpulse
python -m venv .venv
```

Activate the environment with `source .venv/bin/activate` on Linux and macOS, or
`.venv\Scripts\Activate.ps1` in PowerShell on Windows. Then install and run:

```sh
pip install -e .
patchpulse --as-of 2026-10-01T12:00:00+00:00
```

`--as-of` fixes the evaluation time, so the output matches the example above. Without it,
PatchPulse uses the current time and the synthetic instances become stale as their scan dates
age.

Add `--html report.html` to also write the report as a standalone HTML file, for example to
attach to a ticket.

## Using your own data

PatchPulse reads a JSON file with one record per instance. Point it at your own file with
`PATCHPULSE_FIXTURE_PATH`:

```sh
PATCHPULSE_FIXTURE_PATH=/path/to/fleet.json patchpulse
```

In PowerShell, set `$env:PATCHPULSE_FIXTURE_PATH = "C:\path\to\fleet.json"` first.

The file must contain an `instances` list:

```json
{
  "instances": [
    {
      "instance_id": "i-0123456789abcdef0",
      "name": "web-01",
      "critical_missing": 0,
      "security_missing": 1,
      "other_missing": 4,
      "last_scan_at": "2026-09-30T02:15:00+00:00"
    }
  ]
}
```

| Field | Type | Rules |
|---|---|---|
| `instance_id` | string | `i-` followed by 8 or 17 lowercase hexadecimal characters |
| `name` | string | 1 to 128 characters after trimming spaces |
| `critical_missing` | integer | 0 or more |
| `security_missing` | integer | 0 or more |
| `other_missing` | integer | 0 or more, reported but not used by the policy |
| `last_scan_at` | string | ISO 8601 timestamp with a time zone, for example `+00:00` |

The input is validated before anything is evaluated. A file is rejected if it is not valid
JSON, if a record breaks a rule above, if an instance ID appears twice, or if it lists more than
10,000 instances. The error message names the record and the field.

## Configuration

Policy limits come from environment variables:

| Variable | Default | Allowed | Meaning |
|---|---|---|---|
| `PATCHPULSE_FIXTURE_PATH` | `fixtures/fleet.json` | any path | Fleet file to read |
| `PATCHPULSE_MAX_CRITICAL_MISSING` | `0` | 0 to 100 | Critical patches allowed before an instance is non-compliant |
| `PATCHPULSE_MAX_SECURITY_MISSING` | `0` | 0 to 100 | Security patches allowed before an instance is non-compliant |
| `PATCHPULSE_MAX_SCAN_AGE_DAYS` | `7` | 1 to 90 | Days since the last scan before an instance is stale |

An invalid value stops the run with a message such as
`PATCHPULSE_MAX_SCAN_AGE_DAYS must be between 1 and 90`. PatchPulse never falls back to a
default when a value is set but wrong.

Command line options:

| Option | Meaning |
|---|---|
| `--as-of TIMESTAMP` | Evaluate at this time instead of now. Must include a time zone. |
| `--html PATH` | Also write the report as an HTML file. Parent folders are created. |

Exit codes make the CLI easy to use in scripts and CI jobs:

| Code | Meaning |
|---|---|
| `0` | Every instance is compliant |
| `1` | At least one instance is stale or non-compliant |
| `2` | Invalid configuration, invalid data, or a file could not be read or written |

## Development

```powershell
.\.venv\Scripts\ruff check .
.\.venv\Scripts\ruff format --check .
.\.venv\Scripts\mypy
.\.venv\Scripts\pytest
```

CI runs the same checks plus a gitleaks secret scan. Tests fail below 95% coverage. Actions
are pinned to commit SHAs and Dependabot keeps them and the dev tools up to date.

Build the Lambda deployment package with:

```powershell
.\.venv\Scripts\python -m tools.package_lambda
```

The archive is written to `dist/lambda.zip`. Entries are sorted and timestamps are fixed, so
unchanged source always produces the same file hash.

## Deploying to your AWS account

The `infra/envs/dev` environment runs PatchPulse in Lambda once a day. It creates one Lambda
function, an execution role that can only write its own logs, a log group with 14-day
retention, and an EventBridge schedule. These are billable AWS resources, so check current
Lambda, CloudWatch Logs and S3 prices for your region before applying.

The deployed function reads the fleet file bundled in the package. Replace
`fixtures/fleet.json` with your own data before building, or the function reports on the
synthetic fleet.

Replace every value in angle brackets with your own.

1. Install Terraform 1.10 or newer and the AWS CLI, and sign in to an account that may create
   IAM roles, Lambda functions, EventBridge rules and CloudWatch log groups.
2. Create an S3 bucket for Terraform state, `<your-state-bucket>`, in `<aws-region>`.
3. Copy `infra/envs/dev/backend.hcl.example` to `infra/envs/dev/backend.hcl` and fill in the
   bucket and region. Git ignores `backend.hcl`.
4. Build the deployment package from the repository root:

   ```sh
   python -m tools.package_lambda
   ```

5. Plan and apply from `infra/envs/dev`:

   ```sh
   terraform init -backend-config=backend.hcl
   terraform plan -var="aws_region=<aws-region>" -out=tfplan
   terraform apply tfplan
   ```

6. Run it once and read the result:

   ```sh
   aws lambda invoke --function-name "$(terraform output -raw function_name)" response.json
   ```

   The response contains the report counts, every finding and the alert text. Logs go to the
   group shown by `terraform output -raw log_group_name`.
7. Remove everything when you are done:

   ```sh
   terraform destroy -var="aws_region=<aws-region>"
   ```

Policy limits for the deployed function are Terraform variables in
`infra/envs/dev/variables.tf`: `max_critical_missing`, `max_security_missing`,
`max_scan_age_days` and `schedule_expression`.

## Reusing the Terraform module

The Lambda module in `infra/modules/lambda` works without the rest of this repository. Build a
package with `python -m tools.package_lambda`, then reference the module from your own
configuration:

```hcl
module "patch_report" {
  source = "github.com/mehedi-hasan-2426/patchpulse//infra/modules/lambda?ref=<tag-or-commit>"

  name                = "<function-name>"
  package_path        = "<path-to>/lambda.zip"
  schedule_expression = "cron(0 6 * * ? *)"

  environment_variables = {
    PATCHPULSE_MAX_SCAN_AGE_DAYS = "7"
  }
}
```

Always pin `ref` to a tag or commit. The [module README](infra/modules/lambda/README.md) lists
every input and output.

## License

MIT, see [LICENSE](LICENSE).
