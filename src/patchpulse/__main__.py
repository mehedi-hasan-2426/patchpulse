import argparse
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="patchpulse")
    parser.add_argument("--as-of", type=parse_as_of, default=None)
    parser.add_argument("--html", type=Path, default=None)
    arguments = parser.parse_args(argv)

    try:
        settings = load_settings(os.environ)
        now = arguments.as_of or datetime.now(UTC)
        report = run(FixtureSource(settings.fixture_path), settings, now)
        if arguments.html is not None:
            arguments.html.parent.mkdir(parents=True, exist_ok=True)
            arguments.html.write_text(render_page(report), encoding="utf-8")
    except (SettingsError, FleetDataError, OSError) as error:
        print(f"patchpulse: {error}", file=sys.stderr)
        return 2

    print(format_alert(report) or f"All {len(report.findings)} instances are compliant.")
    return 1 if report.needs_attention else 0


if __name__ == "__main__":
    raise SystemExit(main())
