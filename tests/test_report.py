from datetime import datetime, timedelta

from patchpulse.models import ComplianceStatus
from patchpulse.policy import CompliancePolicy
from patchpulse.report import FleetReport, build_report, format_alert
from tests.conftest import make_instance


def mixed_fleet_report(now: datetime) -> FleetReport:
    instances = [
        make_instance("i-0000000000000000c", "ok-01"),
        make_instance("i-0000000000000000b", "patch-01", critical_missing=1),
        make_instance("i-0000000000000000a", "old-01", scan_age=timedelta(days=30)),
    ]
    return build_report(instances, CompliancePolicy(), now)


def test_findings_are_ordered_by_severity_then_instance_id(now: datetime) -> None:
    report = mixed_fleet_report(now)

    assert [f.status for f in report.findings] == [
        ComplianceStatus.STALE,
        ComplianceStatus.NON_COMPLIANT,
        ComplianceStatus.COMPLIANT,
    ]


def test_counts_and_attention(now: datetime) -> None:
    report = mixed_fleet_report(now)

    assert report.count(ComplianceStatus.COMPLIANT) == 1
    assert len(report.needs_attention) == 2


def test_report_serialises_to_plain_data(now: datetime) -> None:
    data = mixed_fleet_report(now).to_dict()

    assert data["total"] == 3
    assert data["counts"] == {"stale": 1, "non_compliant": 1, "compliant": 1}
    assert data["generated_at"] == now.isoformat()
    assert data["findings"][1] == {
        "instance_id": "i-0000000000000000b",
        "name": "patch-01",
        "status": "non_compliant",
        "reasons": ["1 critical patches missing"],
    }


def test_alert_lists_only_instances_needing_attention(now: datetime) -> None:
    alert = format_alert(mixed_fleet_report(now))

    assert alert is not None
    assert alert.startswith("PatchPulse: 2 of 3 instances need attention")
    assert "old-01 (i-0000000000000000a): stale, last patch scan 30 days ago" in alert
    assert "patch-01 (i-0000000000000000b): non_compliant, 1 critical patches missing" in alert
    assert "ok-01" not in alert


def test_no_alert_when_everything_is_compliant(now: datetime) -> None:
    report = build_report([make_instance()], CompliancePolicy(), now)

    assert format_alert(report) is None


def test_empty_fleet_produces_no_alert(now: datetime) -> None:
    report = build_report([], CompliancePolicy(), now)

    assert report.to_dict()["total"] == 0
    assert format_alert(report) is None
