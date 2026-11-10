# Folder Fingerprint

Record SHA-256 hashes for regular files, then check the folder against that snapshot. Paths are relative to the scanned root. Symlinks and Windows junctions inside the root are skipped.

```sh
python fingerprint.py snapshot ./files --output files.sha256.json
python fingerprint.py check ./files files.sha256.json
```

Store the manifest outside the scanned directory. The check prints added, removed, and changed paths and exits with status 0 for a match, 1 for differences, or 2 for errors. Use Python 3.12 or later. Without `--output` the manifest is printed to standard output; `--output` always writes UTF-8, so it is the safer choice in Windows PowerShell 5.1, where `>` re-encodes the text. The tool uses only the Python standard library.

Run tests from the project directory with `python -m unittest -v`.
