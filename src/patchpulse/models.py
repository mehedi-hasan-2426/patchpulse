from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


@dataclass(frozen=True)
class InstanceCompliance:
    instance_id: str
    name: str
    critical_missing: int
    security_missing: int
    other_missing: int
    last_scan_at: datetime


class ComplianceStatus(StrEnum):
    STALE = "stale"
    NON_COMPLIANT = "non_compliant"
    COMPLIANT = "compliant"


@dataclass(frozen=True)
class Finding:
    instance: InstanceCompliance
    status: ComplianceStatus
    reasons: tuple[str, ...]
