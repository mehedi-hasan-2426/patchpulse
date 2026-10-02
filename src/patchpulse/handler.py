import os
from datetime import UTC, datetime
from typing import Any

from patchpulse.report import FleetReport, build_report, format_alert
from patchpulse.settings import Settings, load_settings
from patchpulse.sources import ComplianceSource, FixtureSource


def run(source: ComplianceSource, settings: Settings, now: datetime) -> FleetReport:
    return build_report(source.fetch(), settings.policy, now)


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    settings = load_settings(os.environ)
    report = run(FixtureSource(settings.fixture_path), settings, datetime.now(UTC))
    return {**report.to_dict(), "alert": format_alert(report)}
