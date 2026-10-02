from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from patchpulse.models import ComplianceStatus, Finding, InstanceCompliance
from patchpulse.policy import CompliancePolicy

SEVERITY_ORDER = {status: rank for rank, status in enumerate(ComplianceStatus)}


@dataclass(frozen=True)
class FleetReport:
    generated_at: datetime
    findings: tuple[Finding, ...]

    def count(self, status: ComplianceStatus) -> int:
        return sum(1 for finding in self.findings if finding.status is status)

    @property
    def needs_attention(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.status is not ComplianceStatus.COMPLIANT)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "total": len(self.findings),
            "counts": {status.value: self.count(status) for status in ComplianceStatus},
            "findings": [
                {
                    "instance_id": finding.instance.instance_id,
                    "name": finding.instance.name,
                    "status": finding.status.value,
                    "reasons": list(finding.reasons),
                }
                for finding in self.findings
            ],
        }


def build_report(
    instances: Iterable[InstanceCompliance], policy: CompliancePolicy, now: datetime
) -> FleetReport:
    findings = sorted(
        (policy.evaluate(instance, now) for instance in instances),
        key=lambda finding: (SEVERITY_ORDER[finding.status], finding.instance.instance_id),
    )
    return FleetReport(generated_at=now, findings=tuple(findings))


def format_alert(report: FleetReport) -> str | None:
    attention = report.needs_attention
    if not attention:
        return None

    lines = [
        f"PatchPulse: {len(attention)} of {len(report.findings)} instances need attention "
        f"({report.generated_at.isoformat()})",
        "",
    ]
    for finding in attention:
        reasons = "; ".join(finding.reasons)
        lines.append(
            f"- {finding.instance.name} ({finding.instance.instance_id}): "
            f"{finding.status.value}, {reasons}"
        )
    return "\n".join(lines)
