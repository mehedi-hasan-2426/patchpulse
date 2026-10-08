import json
from datetime import datetime
from pathlib import Path

import pytest

from patchpulse.__main__ import main
from patchpulse.handler import handler, run
from patchpulse.models import InstanceCompliance
from patchpulse.settings import load_settings
from tests.conftest import make_instance

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "fleet.json"


class StaticSource:
    def __init__(self, instances: list[InstanceCompliance]) -> None:
        self._instances = instances

    def fetch(self) -> list[InstanceCompliance]:
        return self._instances


def test_run_uses_the_given_source_and_policy(now: datetime) -> None:
    source = StaticSource([make_instance(critical_missing=1)])

    report = run(source, load_settings({"PATCHPULSE_MAX_CRITICAL_MISSING": "1"}), now)

    assert len(report.needs_attention) == 0


def test_handler_returns_report_and_alert(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATCHPULSE_FIXTURE_PATH", str(FIXTURE))
    monkeypatch.setenv("PATCHPULSE_MAX_SCAN_AGE_DAYS", "90")

    result = handler({}, None)

    assert result["total"] == 5
    assert result["counts"]["non_compliant"] == 2
    assert result["alert"].startswith("PatchPulse: 2 of 5 instances need attention")


def test_cli_reports_demo_fleet(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("PATCHPULSE_FIXTURE_PATH", str(FIXTURE))

    exit_code = main(["--as-of", "2026-10-01T12:00:00+00:00"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "3 of 5 instances need attention" in output
    assert "reporting-01 (i-0a1b2c3d4e5f6071b): stale" in output
    assert "web-01" not in output


def test_cli_reports_a_compliant_fleet(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    path = tmp_path / "fleet.json"
    path.write_text('{"instances": []}', encoding="utf-8")
    monkeypatch.setenv("PATCHPULSE_FIXTURE_PATH", str(path))

    assert main([]) == 0
    assert "All 0 instances are compliant." in capsys.readouterr().out


@pytest.mark.parametrize(
    ("variable", "value", "message"),
    [
        ("PATCHPULSE_FIXTURE_PATH", "does-not-exist.json", "patchpulse:"),
        ("PATCHPULSE_MAX_SCAN_AGE_DAYS", "0", "between 1 and 90"),
    ],
)
def test_cli_exits_with_two_on_bad_input(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    variable: str,
    value: str,
    message: str,
) -> None:
    monkeypatch.setenv("PATCHPULSE_FIXTURE_PATH", str(FIXTURE))
    monkeypatch.setenv(variable, value)

    assert main([]) == 2
    assert message in capsys.readouterr().err


def test_cli_rejects_naive_as_of() -> None:
    with pytest.raises(SystemExit):
        main(["--as-of", "2026-10-01T12:00:00"])


def test_cli_writes_html_page(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PATCHPULSE_FIXTURE_PATH", str(FIXTURE))
    page = tmp_path / "site" / "index.html"

    exit_code = main(["--as-of", "2026-10-01T12:00:00+00:00", "--html", str(page)])

    assert exit_code == 1
    content = page.read_text(encoding="utf-8")
    assert "5 instances, evaluated as of" in content
    assert "reporting-01" in content


def test_cli_reports_unwritable_html_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setenv("PATCHPULSE_FIXTURE_PATH", str(FIXTURE))
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")

    assert main(["--html", str(blocker / "index.html")]) == 2
    assert "patchpulse:" in capsys.readouterr().err


@pytest.mark.parametrize("with_html", [False, True])
def test_cli_writes_json_report(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    with_html: bool,
) -> None:
    monkeypatch.setenv("PATCHPULSE_FIXTURE_PATH", str(FIXTURE))
    report_path = tmp_path / "reports" / "fleet.json"
    html_path = tmp_path / "site" / "index.html"
    arguments = ["--as-of", "2026-10-01T12:00:00+00:00", "--json", str(report_path)]
    if with_html:
        arguments.extend(["--html", str(html_path)])

    exit_code = main(arguments)

    assert exit_code == 1
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["generated_at"] == "2026-10-01T12:00:00+00:00"
    assert payload["total"] == 5
    assert payload["counts"] == {"stale": 1, "non_compliant": 2, "compliant": 2}
    assert len(payload["findings"]) == 5
    assert payload["findings"][0]["name"] == "reporting-01"
    assert payload["findings"][0]["status"] == "stale"
    assert payload["findings"][0]["reasons"]
    assert "3 of 5 instances need attention" in capsys.readouterr().out
    if with_html:
        assert "reporting-01" in html_path.read_text(encoding="utf-8")


def test_cli_exports_a_compliant_fleet_as_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixture = tmp_path / "empty-fleet.json"
    fixture.write_text('{"instances": []}', encoding="utf-8")
    monkeypatch.setenv("PATCHPULSE_FIXTURE_PATH", str(fixture))
    report_path = tmp_path / "report.json"

    assert main(["--json", str(report_path)]) == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["total"] == 0
    assert payload["findings"] == []
    assert payload["counts"] == {"stale": 0, "non_compliant": 0, "compliant": 0}


def test_cli_reports_unwritable_json_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setenv("PATCHPULSE_FIXTURE_PATH", str(FIXTURE))
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")

    assert main(["--json", str(blocker / "report.json")]) == 2
    assert "patchpulse:" in capsys.readouterr().err


def test_cli_does_not_export_json_with_invalid_settings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PATCHPULSE_FIXTURE_PATH", str(FIXTURE))
    monkeypatch.setenv("PATCHPULSE_MAX_SCAN_AGE_DAYS", "0")
    report_path = tmp_path / "report.json"

    assert main(["--json", str(report_path)]) == 2
    assert not report_path.exists()
