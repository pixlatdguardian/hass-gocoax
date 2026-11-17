"""Build a component-only ZIP; never include local captures or credentials."""

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    component = root / "custom_components" / "gocoax"
    manifest = json.loads((component / "manifest.json").read_text())
    if manifest["domain"] != "gocoax":
        raise ValueError("Unexpected integration domain")
    args.output.mkdir(parents=True, exist_ok=True)
    archive = args.output / f"gocoax-readonly-{manifest['version']}.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as result:
        for path in sorted(component.rglob("*")):
            if (
                path.is_file()
                and path.suffix in (".py", ".json")
                and "__pycache__" not in path.parts
            ):
                result.write(path, path.relative_to(root).as_posix())
        result.write(root / "LICENSE.md", "LICENSE.md")
        result.write(root / "README.md", "README.md")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(f"{digest}  {archive.name}\n")
    print(f"Built {archive.name}; SHA256 {digest}")


if __name__ == "__main__":
    main()
