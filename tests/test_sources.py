import json
import re
from pathlib import Path
from typing import Any

import pytest

from patchpulse.sources import MAX_INSTANCES, FixtureSource, FleetDataError, parse_fleet

VALID_RECORD: dict[str, Any] = {
    "instance_id": "i-0123456789abcdef0",
    "name": " web-01 ",
    "critical_missing": 1,
    "security_missing": 2,
    "other_missing": 3,
    "last_scan_at": "2026-09-30T02:15:00+00:00",
}


def fleet(*records: dict[str, Any]) -> str:
    return json.dumps({"instances": list(records)})


def with_field(field: str, value: Any) -> dict[str, Any]:
    return {**VALID_RECORD, field: value}


def test_parses_a_valid_record() -> None:
    [instance] = parse_fleet(fleet(VALID_RECORD))

    assert instance.instance_id == "i-0123456789abcdef0"
    assert instance.name == "web-01"
    assert (instance.critical_missing, instance.security_missing, instance.other_missing) == (
        1,
        2,
        3,
    )
    assert instance.last_scan_at.utcoffset() is not None


def test_accepts_legacy_eight_character_instance_ids() -> None:
    [instance] = parse_fleet(fleet(with_field("instance_id", "i-0123abcd")))

    assert instance.instance_id == "i-0123abcd"


def test_empty_fleet_is_valid() -> None:
    assert parse_fleet(fleet()) == []


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ("not json", "not valid JSON"),
        ("[]", "'instances' list"),
        ('{"instances": {}}', "'instances' list"),
        ('{"instances": [42]}', "instances[0] must be an object"),
    ],
)
def test_rejects_malformed_documents(document: str, message: str) -> None:
    with pytest.raises(FleetDataError, match=re.escape(message)):
        parse_fleet(document)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("instance_id", "web-01", "instance_id"),
        ("instance_id", "i-0123456789ABCDEF0", "instance_id"),
        ("instance_id", None, "instance_id"),
        ("name", "   ", "name"),
        ("name", "x" * 129, "name"),
        ("name", 7, "name"),
        ("critical_missing", -1, "critical_missing"),
        ("security_missing", "2", "security_missing"),
        ("other_missing", True, "other_missing"),
        ("other_missing", 1.5, "other_missing"),
        ("last_scan_at", "yesterday", "last_scan_at"),
        ("last_scan_at", "2026-09-30T02:15:00", "time zone"),
        ("last_scan_at", 1727660100, "last_scan_at"),
    ],
)
def test_rejects_invalid_fields(field: str, value: Any, message: str) -> None:
    with pytest.raises(FleetDataError, match=message):
        parse_fleet(fleet(with_field(field, value)))


def test_rejects_duplicate_instance_ids() -> None:
    with pytest.raises(FleetDataError, match="duplicate instance id"):
        parse_fleet(fleet(VALID_RECORD, VALID_RECORD))


def test_rejects_oversized_fleets() -> None:
    document = json.dumps({"instances": [{}] * (MAX_INSTANCES + 1)})

    with pytest.raises(FleetDataError, match="more than"):
        parse_fleet(document)


def test_fixture_source_reads_a_file(tmp_path: Path) -> None:
    path = tmp_path / "fleet.json"
    path.write_text(fleet(VALID_RECORD), encoding="utf-8")

    assert len(FixtureSource(path).fetch()) == 1


def test_bundled_fixture_is_valid() -> None:
    path = Path(__file__).resolve().parent.parent / "fixtures" / "fleet.json"

    assert len(FixtureSource(path).fetch()) == 5
