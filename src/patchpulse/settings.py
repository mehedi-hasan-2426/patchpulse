from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from patchpulse.policy import CompliancePolicy

DEFAULT_FIXTURE_PATH = Path("fixtures/fleet.json")


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    fixture_path: Path
    policy: CompliancePolicy


def load_settings(environ: Mapping[str, str]) -> Settings:
    defaults = CompliancePolicy()
    policy = CompliancePolicy(
        max_critical_missing=_bounded_int(
            environ, "PATCHPULSE_MAX_CRITICAL_MISSING", defaults.max_critical_missing, 0, 100
        ),
        max_security_missing=_bounded_int(
            environ, "PATCHPULSE_MAX_SECURITY_MISSING", defaults.max_security_missing, 0, 100
        ),
        max_scan_age=timedelta(
            days=_bounded_int(
                environ, "PATCHPULSE_MAX_SCAN_AGE_DAYS", defaults.max_scan_age.days, 1, 90
            )
        ),
    )
    fixture_path = Path(environ.get("PATCHPULSE_FIXTURE_PATH", str(DEFAULT_FIXTURE_PATH)))
    return Settings(fixture_path=fixture_path, policy=policy)


def _bounded_int(
    environ: Mapping[str, str], name: str, default: int, minimum: int, maximum: int
) -> int:
    raw = environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise SettingsError(f"{name} must be an integer") from error
    if not minimum <= value <= maximum:
        raise SettingsError(f"{name} must be between {minimum} and {maximum}")
    return value
