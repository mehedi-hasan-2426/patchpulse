import argparse
import zipfile
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
EXCLUDED_PARTS = {"__pycache__"}


def package_files(root: Path) -> list[tuple[Path, str]]:
    package = root / "src" / "patchpulse"
    sources = [
        (path, path.relative_to(root / "src").as_posix())
        for path in package.rglob("*.py")
        if not EXCLUDED_PARTS.intersection(path.parts)
    ]
    fixture = root / "fixtures" / "fleet.json"
    return sorted([*sources, (fixture, "fixtures/fleet.json")], key=lambda item: item[1])


def build(root: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, name in package_files(root):
            entry = zipfile.ZipInfo(name, date_time=FIXED_TIMESTAMP)
            entry.external_attr = 0o644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, path.read_bytes())
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="package_lambda")
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "lambda.zip")
    arguments = parser.parse_args(argv)
    print(build(ROOT, arguments.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
