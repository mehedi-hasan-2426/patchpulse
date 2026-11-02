import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from patchpulse.handler import run
from patchpulse.page import render_page
from patchpulse.report import format_alert
from patchpulse.settings import SettingsError, load_settings
from patchpulse.sources import FixtureSource, FleetDataError


def parse_as_of(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None:
        raise argparse.ArgumentTypeError("--as-of must include a time zone")
    return timestamp


def _same_file(first: Path, second: Path) -> bool:
    return first.resolve() == second.resolve() or (
        first.exists() and second.exists() and first.samefile(second)
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="patchpulse")
    parser.add_argument("--as-of", type=parse_as_of, default=None)
    parser.add_argument("--html", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None, help="write the fleet report as JSON")
    arguments = parser.parse_args(argv)

    try:
        settings = load_settings(os.environ)
        if any(
            path is not None and _same_file(path, settings.fixture_path)
            for path in (arguments.html, arguments.json)
        ):
            raise SettingsError("report output must not overwrite fleet input")
        if (
            arguments.html is not None
            and arguments.json is not None
            and _same_file(arguments.html, arguments.json)
        ):
            raise SettingsError("HTML and JSON outputs must be different files")
        now = arguments.as_of or datetime.now(UTC)
        report = run(FixtureSource(settings.fixture_path), settings, now)
        if arguments.html is not None:
            arguments.html.parent.mkdir(parents=True, exist_ok=True)
            arguments.html.write_text(render_page(report), encoding="utf-8")
        if arguments.json is not None:
            arguments.json.parent.mkdir(parents=True, exist_ok=True)
            arguments.json.write_text(
                json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
            )
    except (SettingsError, FleetDataError, OSError) as error:
        print(f"patchpulse: {error}", file=sys.stderr)
        return 2

    print(format_alert(report) or f"All {len(report.findings)} instances are compliant.")
    return 1 if report.needs_attention else 0


if __name__ == "__main__":
    raise SystemExit(main())
