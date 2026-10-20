#!/usr/bin/env python3
"""Verify a backup manifest: age, size and SHA-256.

Reads a JSON manifest, checks that every listed backup is recent enough
and matches its recorded byte count and checksum, then exits 1 if anything
is stale or corrupt. It never writes to the backups or the manifest.

Usage:
    python3 backup_verify.py /srv/backups/manifest.json
    python3 backup_verify.py manifest.json --max-age-hours 8
    python3 backup_verify.py manifest.json --now 2026-10-20T09:00:00Z

Manifest:
    {"backups": [
        {"path": "db-2026-10-20.dump",
         "created_at": "2026-10-20T01:00:00Z",
         "bytes": 4194304,
         "sha256": "0123...cdef"}
    ]}

Relative paths are resolved against the directory that holds the manifest.
created_at is ISO 8601; a trailing Z is accepted, and a timestamp without
a zone is treated as UTC. A bare JSON list of entries is also accepted.

Exit codes:
    0  every backup is present, recent, the right size and the right hash
    1  at least one finding (missing, stale, wrong size or wrong hash)
    2  usage error, or a manifest that is missing, unreadable, invalid,
       has no entries, or has a malformed entry

Cron: 30 3 * * * python3 backup_verify.py /srv/backups/manifest.json
CI:   python3 backup_verify.py manifest.json --max-age-hours 26

By s0sta.com
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

CHUNK = 1024 * 1024
REQUIRED = ("path", "created_at", "bytes", "sha256")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class ManifestError(Exception):
    """The manifest cannot be used as a manifest."""


def parse_when(value):
    """Parse an ISO 8601 timestamp and return an aware UTC datetime."""
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        when = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError("bad timestamp: %r" % (value,))
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(timezone.utc)


def sha256_file(path):
    """Return the lowercase hex SHA-256 of a file, read in 1 MiB chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(CHUNK)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path):
    """Return the list of backup entries from a JSON manifest."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except OSError as exc:
        raise ManifestError("cannot read %s: %s" % (path, exc))
    except ValueError as exc:
        raise ManifestError("%s is not valid JSON: %s" % (path, exc))

    if isinstance(raw, dict):
        raw = raw.get("backups")
    if not isinstance(raw, list):
        raise ManifestError("manifest must be a list or an object with a backups list")
    if not raw:
        raise ManifestError("manifest lists no backups")
    return raw


def check_entry(index, entry):
    """Validate one manifest entry and return a normalised copy."""
    if not isinstance(entry, dict):
        raise ManifestError("entry %d is not an object" % index)
    missing = [key for key in REQUIRED if key not in entry]
    if missing:
        raise ManifestError("entry %d is missing %s" % (index, ", ".join(missing)))

    name = entry["path"]
    if not isinstance(name, str) or not name.strip():
        raise ManifestError("entry %d has an empty path" % index)

    created = entry["created_at"]
    if not isinstance(created, str):
        raise ManifestError("entry %d has a non-string created_at" % index)
    try:
        when = parse_when(created)
    except ValueError as exc:
        raise ManifestError("entry %d has a %s" % (index, exc))

    size = entry["bytes"]
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise ManifestError("entry %d has an invalid bytes value" % index)

    digest = entry["sha256"]
    if not isinstance(digest, str) or not SHA256_RE.match(digest):
        raise ManifestError("entry %d has an invalid sha256 value" % index)

    return {"path": name, "created_at": when, "bytes": size,
            "sha256": digest.lower()}


def verify(manifest_path, max_age_hours, now):
    """Check every backup and return (checked, findings, failed_count)."""
    entries = load_manifest(manifest_path)
    base = os.path.dirname(os.path.abspath(manifest_path))
    findings = []
    failed = 0

    for index, raw in enumerate(entries, 1):
        entry = check_entry(index, raw)
        name = entry["path"]
        target = name if os.path.isabs(name) else os.path.join(base, name)
        before = len(findings)

        age = (now - entry["created_at"]).total_seconds() / 3600.0
        if age < 0:
            findings.append("FAIL %s timestamp in the future" % name)
        elif age > max_age_hours:
            findings.append("FAIL %s stale: %.1fh > %.1fh"
                            % (name, age, max_age_hours))

        try:
            size = os.path.getsize(target)
        except FileNotFoundError:
            findings.append("FAIL %s missing" % name)
            failed += 1
            continue
        except OSError as exc:
            raise ManifestError("cannot stat %s: %s" % (target, exc))

        if size != entry["bytes"]:
            findings.append("FAIL %s size %d != %d"
                            % (name, size, entry["bytes"]))

        try:
            digest = sha256_file(target)
        except OSError as exc:
            raise ManifestError("cannot read %s: %s" % (target, exc))
        if digest != entry["sha256"]:
            findings.append("FAIL %s sha256 mismatch" % name)

        if len(findings) > before:
            failed += 1

    return len(entries), findings, failed


def plural(count, word):
    """Return a count and a correctly pluralised noun."""
    return "%d %s%s" % (count, word, "" if count == 1 else "s")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify backup age, size and SHA-256 from a JSON manifest.",
        epilog="Exit 0 clean, 1 finding, 2 usage or manifest error. By s0sta.com")
    parser.add_argument("manifest", help="path to the JSON manifest")
    parser.add_argument("--max-age-hours", type=float, default=26.0, metavar="H",
                        help="maximum age in hours (default: 26)")
    parser.add_argument("--now", metavar="ISO",
                        help="override the current UTC time (for tests)")
    args = parser.parse_args(argv)

    if not (args.max_age_hours >= 0):
        parser.error("--max-age-hours must be zero or positive")

    if args.now is None:
        now = datetime.now(timezone.utc)
    else:
        try:
            now = parse_when(args.now)
        except ValueError as exc:
            parser.error("--now has a %s" % exc)

    try:
        checked, findings, failed = verify(args.manifest, args.max_age_hours, now)
    except ManifestError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2

    for line in findings:
        print(line)
    if findings:
        print("FAIL %s, %d of %s affected"
              % (plural(len(findings), "finding"),
                 failed, plural(checked, "backup")))
        return 1
    print("OK %s checked" % plural(checked, "backup"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
