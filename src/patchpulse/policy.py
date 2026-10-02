from dataclasses import dataclass
from datetime import datetime, timedelta

from patchpulse.models import ComplianceStatus, Finding, InstanceCompliance


@dataclass(frozen=True)
class CompliancePolicy:
    max_critical_missing: int = 0
    max_security_missing: int = 0
    max_scan_age: timedelta = timedelta(days=7)

    def evaluate(self, instance: InstanceCompliance, now: datetime) -> Finding:
        scan_age = now - instance.last_scan_at
        if scan_age > self.max_scan_age:
            return Finding(
                instance,
                ComplianceStatus.STALE,
                (f"last patch scan {scan_age.days} days ago",),
            )

        reasons = []
        if instance.critical_missing > self.max_critical_missing:
            reasons.append(f"{instance.critical_missing} critical patches missing")
        if instance.security_missing > self.max_security_missing:
            reasons.append(f"{instance.security_missing} security patches missing")

        status = ComplianceStatus.NON_COMPLIANT if reasons else ComplianceStatus.COMPLIANT
        return Finding(instance, status, tuple(reasons))
