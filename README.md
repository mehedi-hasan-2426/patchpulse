# PatchPulse

Patch compliance reporting and alerting for a fleet of EC2 instances.

This is a learning project. It is modelled on patching work I do in an enterprise DevOps
team, but it uses synthetic data only and contains nothing from my employer.

## Status

Milestone 1 of 6 is done: the Python core runs locally against a synthetic fleet. There is
no AWS infrastructure yet.

| Milestone | Scope | State |
|---|---|---|
| 1 | Python core, demo source, unit tests, CI | Done |
| 2 | Terraform modules and a dev environment | Planned |
| 3 | GitHub OIDC deploy to dev, CloudWatch alarms, SNS alerts | Planned |
| 4 | Prod environment behind a manual approval | Planned |
| 5 | Real SSM Patch Manager source and an incident walkthrough | Planned |
| 6 | Architecture diagram, costs and trade-offs | Planned |

## What it does

PatchPulse reads patch compliance data for each instance and sorts every instance into one of
three states:

| State | Meaning |
|---|---|
| `stale` | The last patch scan is older than the allowed age, so the data cannot be trusted |
| `non_compliant` | More critical or security patches are missing than the policy allows |
| `compliant` | Recent scan and within the policy limits |

It then builds a report and, if anything needs attention, an alert message. Stale instances
are listed first, because missing data hides problems.

## Quick start

Requires Python 3.12 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\patchpulse --as-of 2026-10-01T12:00:00+00:00
```

```text
PatchPulse: 3 of 5 instances need attention (2026-10-01T12:00:00+00:00)

- reporting-01 (i-0a1b2c3d4e5f6071b): stale, last patch scan 19 days ago
- web-02 (i-0a1b2c3d4e5f60719): non_compliant, 2 critical patches missing; 1 security patches missing
- batch-01 (i-0a1b2c3d4e5f6071a): non_compliant, 4 security patches missing
```

`--as-of` pins the evaluation time so the demo output stays the same as the fixture ages.
The command exits with `0` when everything is compliant, `1` when something needs attention,
and `2` on invalid configuration or data.

## Configuration

| Variable | Default | Allowed |
|---|---|---|
| `PATCHPULSE_FIXTURE_PATH` | `fixtures/fleet.json` | Path to a fleet JSON file |
| `PATCHPULSE_MAX_CRITICAL_MISSING` | `0` | 0 to 100 |
| `PATCHPULSE_MAX_SECURITY_MISSING` | `0` | 0 to 100 |
| `PATCHPULSE_MAX_SCAN_AGE_DAYS` | `7` | 1 to 90 |

Invalid values stop the run with a clear message instead of falling back silently.

## Design

```text
src/patchpulse/
  models.py    instance data, compliance states, findings
  policy.py    thresholds and the rules that turn data into findings
  sources.py   where data comes from, plus strict validation of fleet input
  report.py    report building and alert text
  settings.py  environment configuration with bounds
  handler.py   Lambda entry point
  __main__.py  command line entry point
```

Data sources share one small interface, `ComplianceSource`. The demo source reads a JSON
file. The SSM source planned for milestone 5 will implement the same interface, so the policy,
report and alert code will not change when real data is added.

Fleet data is treated as untrusted input. Instance IDs, names, counts and timestamps are
validated, timestamps must include a time zone, duplicates are rejected, and the instance count
is capped.

## Development

```powershell
.\.venv\Scripts\ruff check .
.\.venv\Scripts\ruff format --check .
.\.venv\Scripts\mypy
.\.venv\Scripts\pytest
```

CI runs the same checks plus a gitleaks secret scan. Tests fail below 95% coverage. Actions
are pinned to commit SHAs and Dependabot keeps them and the dev tools up to date.

## License

MIT, see [LICENSE](LICENSE).
