from datetime import UTC, datetime, timedelta

import pytest

from patchpulse.models import InstanceCompliance

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def make_instance(
    instance_id: str = "i-0123456789abcdef0",
    name: str = "web-01",
    *,
    critical_missing: int = 0,
    security_missing: int = 0,
    other_missing: int = 0,
    scan_age: timedelta = timedelta(hours=1),
) -> InstanceCompliance:
    return InstanceCompliance(
        instance_id=instance_id,
        name=name,
        critical_missing=critical_missing,
        security_missing=security_missing,
        other_missing=other_missing,
        last_scan_at=NOW - scan_age,
    )


@pytest.fixture
def now() -> datetime:
    return NOW
