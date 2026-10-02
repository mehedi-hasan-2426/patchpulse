import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from patchpulse.models import InstanceCompliance

MAX_INSTANCES = 10_000
MAX_NAME_LENGTH = 128
INSTANCE_ID_PATTERN = re.compile(r"i-(?:[0-9a-f]{8}|[0-9a-f]{17})")
COUNT_FIELDS = ("critical_missing", "security_missing", "other_missing")


class FleetDataError(ValueError):
    pass


class ComplianceSource(Protocol):
    def fetch(self) -> list[InstanceCompliance]: ...


class FixtureSource:
    def __init__(self, path: Path) -> None:
        self._path = path

    def fetch(self) -> list[InstanceCompliance]:
        return parse_fleet(self._path.read_text(encoding="utf-8"))


def parse_fleet(document: str) -> list[InstanceCompliance]:
    try:
        data = json.loads(document)
    except json.JSONDecodeError as error:
        raise FleetDataError(f"fleet data is not valid JSON: {error.msg}") from error

    if not isinstance(data, dict) or not isinstance(data.get("instances"), list):
        raise FleetDataError("fleet data must be an object with an 'instances' list")

    records = data["instances"]
    if len(records) > MAX_INSTANCES:
        raise FleetDataError(f"fleet data has more than {MAX_INSTANCES} instances")

    instances = [_parse_instance(record, index) for index, record in enumerate(records)]

    seen: set[str] = set()
    for instance in instances:
        if instance.instance_id in seen:
            raise FleetDataError(f"duplicate instance id {instance.instance_id}")
        seen.add(instance.instance_id)

    return instances


def _parse_instance(record: Any, index: int) -> InstanceCompliance:
    location = f"instances[{index}]"
    if not isinstance(record, dict):
        raise FleetDataError(f"{location} must be an object")

    instance_id = record.get("instance_id")
    if not isinstance(instance_id, str) or not INSTANCE_ID_PATTERN.fullmatch(instance_id):
        raise FleetDataError(f"{location}.instance_id is not a valid EC2 instance id")

    name = record.get("name")
    if not isinstance(name, str) or not 0 < len(name.strip()) <= MAX_NAME_LENGTH:
        raise FleetDataError(f"{location}.name must be 1 to {MAX_NAME_LENGTH} characters")

    counts = {
        field: _parse_count(record.get(field), f"{location}.{field}") for field in COUNT_FIELDS
    }

    return InstanceCompliance(
        instance_id=instance_id,
        name=name.strip(),
        last_scan_at=_parse_timestamp(record.get("last_scan_at"), f"{location}.last_scan_at"),
        **counts,
    )


def _parse_count(value: Any, location: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FleetDataError(f"{location} must be a non-negative integer")
    return value


def _parse_timestamp(value: Any, location: str) -> datetime:
    if not isinstance(value, str):
        raise FleetDataError(f"{location} must be an ISO 8601 timestamp")
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as error:
        raise FleetDataError(f"{location} must be an ISO 8601 timestamp") from error
    if timestamp.tzinfo is None:
        raise FleetDataError(f"{location} must include a time zone")
    return timestamp
