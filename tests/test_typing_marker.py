from pathlib import Path

import patchpulse


def test_package_ships_type_marker() -> None:
    assert (Path(patchpulse.__file__).parent / "py.typed").is_file()
