from datetime import timedelta
from pathlib import Path

import pytest

from patchpulse.settings import DEFAULT_FIXTURE_PATH, SettingsError, load_settings


def test_defaults_when_environment_is_empty() -> None:
    settings = load_settings({})

    assert settings.fixture_path == DEFAULT_FIXTURE_PATH
    assert settings.policy.max_critical_missing == 0
    assert settings.policy.max_security_missing == 0
    assert settings.policy.max_scan_age == timedelta(days=7)


def test_reads_overrides() -> None:
    settings = load_settings(
        {
            "PATCHPULSE_FIXTURE_PATH": "data/fleet.json",
            "PATCHPULSE_MAX_CRITICAL_MISSING": "1",
            "PATCHPULSE_MAX_SECURITY_MISSING": "100",
            "PATCHPULSE_MAX_SCAN_AGE_DAYS": "90",
        }
    )

    assert settings.fixture_path == Path("data/fleet.json")
    assert settings.policy.max_critical_missing == 1
    assert settings.policy.max_security_missing == 100
    assert settings.policy.max_scan_age == timedelta(days=90)


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("PATCHPULSE_MAX_CRITICAL_MISSING", "-1", "must be between 0 and 100"),
        ("PATCHPULSE_MAX_SECURITY_MISSING", "101", "must be between 0 and 100"),
        ("PATCHPULSE_MAX_SCAN_AGE_DAYS", "0", "must be between 1 and 90"),
        ("PATCHPULSE_MAX_SCAN_AGE_DAYS", "seven", "must be an integer"),
        ("PATCHPULSE_MAX_CRITICAL_MISSING", "", "must be an integer"),
    ],
)
def test_rejects_invalid_values(name: str, value: str, message: str) -> None:
    with pytest.raises(SettingsError, match=f"{name} {message}"):
        load_settings({name: value})
