import hashlib
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from fingerprint import compare, read_manifest, snapshot


class FingerprintTests(TestCase):
    def test_reports_all_change_types(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            modified = root / "nested" / "modified.txt"
            modified.write_bytes(b"old")
            removed = root / "removed.txt"
            removed.touch()
            before = snapshot(root)
            self.assertEqual(before["nested/modified.txt"], hashlib.sha256(b"old").hexdigest())
            modified.write_bytes(b"new")
            removed.unlink()
            (root / "added.txt").touch()
            self.assertEqual(compare(before, snapshot(root)), {
                "added": ["added.txt"],
                "removed": ["removed.txt"],
                "changed": ["nested/modified.txt"],
            })

    def test_rejects_invalid_manifest(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text('{"file": "wrong"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                read_manifest(path)

    def test_snapshot_output_round_trips_and_stays_outside_root(self):
        script = Path(__file__).with_name("fingerprint.py")

        def run(*args):
            return subprocess.run([sys.executable, str(script), *args], capture_output=True).returncode

        with TemporaryDirectory() as directory:
            root = Path(directory) / "files"
            root.mkdir()
            (root / "naïve.txt").write_bytes(b"data")
            manifest = Path(directory) / "manifest.json"
            self.assertEqual(run("snapshot", str(root), "--output", str(manifest)), 0)
            self.assertEqual(read_manifest(manifest), snapshot(root))
            self.assertEqual(run("check", str(root), str(manifest)), 0)
            self.assertEqual(run("snapshot", str(root), "--output", str(root / "inside.json")), 2)
            self.assertFalse((root / "inside.json").exists())
