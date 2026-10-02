import hashlib
import zipfile
from pathlib import Path

from tools.package_lambda import ROOT, build, main


def test_package_contains_code_and_fixture_only(tmp_path: Path) -> None:
    archive = build(ROOT, tmp_path / "lambda.zip")

    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()

    assert "patchpulse/handler.py" in names
    assert "patchpulse/__init__.py" in names
    assert "fixtures/fleet.json" in names
    assert not [name for name in names if "__pycache__" in name or name.startswith("tests/")]
    assert names == sorted(names)


def test_package_is_reproducible(tmp_path: Path) -> None:
    first = build(ROOT, tmp_path / "a" / "lambda.zip")
    second = build(ROOT, tmp_path / "b" / "lambda.zip")

    assert (
        hashlib.sha256(first.read_bytes()).digest() == hashlib.sha256(second.read_bytes()).digest()
    )


def test_cli_writes_to_the_given_path(tmp_path: Path) -> None:
    output = tmp_path / "out" / "lambda.zip"

    assert main(["--output", str(output)]) == 0
    assert output.is_file()
