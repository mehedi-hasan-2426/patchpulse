from datetime import datetime, timedelta

import pytest

from patchpulse.models import ComplianceStatus
from patchpulse.policy import CompliancePolicy
from tests.conftest import make_instance


def test_clean_recent_instance_is_compliant(now: datetime) -> None:
    finding = CompliancePolicy().evaluate(make_instance(other_missing=5), now)

    assert finding.status is ComplianceStatus.COMPLIANT
    assert finding.reasons == ()


@pytest.mark.parametrize(
    ("critical", "security", "expected_reasons"),
    [
        (1, 0, ("1 critical patches missing",)),
        (0, 2, ("2 security patches missing",)),
        (3, 4, ("3 critical patches missing", "4 security patches missing")),
    ],
)
def test_missing_patches_make_instance_non_compliant(
    now: datetime, critical: int, security: int, expected_reasons: tuple[str, ...]
) -> None:
    instance = make_instance(critical_missing=critical, security_missing=security)

    finding = CompliancePolicy().evaluate(instance, now)

    assert finding.status is ComplianceStatus.NON_COMPLIANT
    assert finding.reasons == expected_reasons


def test_thresholds_allow_counts_up_to_the_limit(now: datetime) -> None:
    policy = CompliancePolicy(max_critical_missing=1, max_security_missing=2)

    at_limit = policy.evaluate(make_instance(critical_missing=1, security_missing=2), now)
    over_limit = policy.evaluate(make_instance(critical_missing=2, security_missing=2), now)

    assert at_limit.status is ComplianceStatus.COMPLIANT
    assert over_limit.status is ComplianceStatus.NON_COMPLIANT


def test_scan_exactly_at_max_age_is_not_stale(now: datetime) -> None:
    finding = CompliancePolicy().evaluate(make_instance(scan_age=timedelta(days=7)), now)

    assert finding.status is ComplianceStatus.COMPLIANT


def test_old_scan_is_stale_even_with_missing_patches(now: datetime) -> None:
    instance = make_instance(critical_missing=5, scan_age=timedelta(days=8, seconds=1))

    finding = CompliancePolicy().evaluate(instance, now)

    assert finding.status is ComplianceStatus.STALE
    assert finding.reasons == ("last patch scan 8 days ago",)


def test_scan_reported_in_the_future_is_treated_as_fresh(now: datetime) -> None:
    finding = CompliancePolicy().evaluate(make_instance(scan_age=-timedelta(minutes=5)), now)

    assert finding.status is ComplianceStatus.COMPLIANT
