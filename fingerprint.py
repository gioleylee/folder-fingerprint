"""Create and compare SHA-256 snapshots of a directory."""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path


def raise_walk_error(error):
    raise error


def snapshot(root):
    root = Path(root)
    if not root.is_dir():
        raise ValueError(f"{root}: expected a directory")
    files = {}
    for parent, directories, names in os.walk(root, onerror=raise_walk_error):
        directory = Path(parent)
        directories[:] = [
            name for name in directories
            if not (directory / name).is_symlink() and not (directory / name).is_junction()
        ]
        for name in names:
            path = directory / name
            if path.is_symlink() or not path.is_file():
                continue
            with path.open("rb") as stream:
                files[path.relative_to(root).as_posix()] = hashlib.file_digest(stream, "sha256").hexdigest()
    return files


def read_manifest(path):
    with path.open(encoding="utf-8-sig") as stream:
        files = json.load(stream)
    if not isinstance(files, dict) or any(
        not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
        for digest in files.values()
    ):
        raise ValueError("expected a JSON object mapping paths to lowercase SHA-256 hashes")
    return files


def compare(expected, actual):
    return {
        "added": sorted(actual.keys() - expected.keys()),
        "removed": sorted(expected.keys() - actual.keys()),
        "changed": sorted(path for path in expected.keys() & actual.keys() if expected[path] != actual[path]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("snapshot").add_argument("root", type=Path)
    check = commands.add_parser("check")
    check.add_argument("root", type=Path)
    check.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            print(json.dumps(snapshot(args.root), indent=2, sort_keys=True))
            return 0
        report = compare(read_manifest(args.manifest), snapshot(args.root))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2))
    return int(any(report.values()))


if __name__ == "__main__":
    raise SystemExit(main())
