from datetime import datetime, timedelta

from patchpulse.page import render_page
from patchpulse.policy import CompliancePolicy
from patchpulse.report import build_report
from tests.conftest import make_instance


def test_page_shows_counts_and_every_instance(now: datetime) -> None:
    report = build_report(
        [
            make_instance("i-0000000000000000a", "ok-01"),
            make_instance("i-0000000000000000b", "patch-01", critical_missing=2),
            make_instance("i-0000000000000000c", "old-01", scan_age=timedelta(days=30)),
        ],
        CompliancePolicy(),
        now,
    )

    page = render_page(report)

    assert page.startswith("<!DOCTYPE html>")
    assert '<div class="count stale"><strong>1</strong>Stale</div>' in page
    assert '<div class="count non_compliant"><strong>1</strong>Non-compliant</div>' in page
    assert '<div class="count compliant"><strong>1</strong>Compliant</div>' in page
    assert "2 critical patches missing" in page
    assert "Within policy" in page
    assert now.isoformat() in page


def test_page_escapes_instance_names(now: datetime) -> None:
    report = build_report(
        [make_instance(name='<script>alert("x")</script>')], CompliancePolicy(), now
    )

    page = render_page(report)

    assert "<script>" not in page
    assert "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;" in page


def test_page_for_empty_fleet(now: datetime) -> None:
    page = render_page(build_report([], CompliancePolicy(), now))

    assert "0 instances, evaluated as of" in page
    assert "<tbody></tbody>" in page
