import hashlib
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
