#!/usr/bin/env python3
"""restore_drill.py - verify that a tar backup could be restored, without restoring it.

Opens a tar archive read-only and lists its members. Every path in the
expected-paths file must be present, every expected entry must hold bytes,
and the unpacked total must reach --min-mb. Nothing is extracted, so the
drill is safe against a production backup and safe in CI.

Expected-paths file: one path per line. Blank lines and lines starting with
"#" are ignored. Paths are matched after normalisation, so "./etc/app.conf"
and "etc/app.conf" are the same entry. A directory path matches every member
under it, which is how you assert that a whole tree is present.

Usage:
    python3 restore_drill.py backup.tar --expected etc.txt
    python3 restore_drill.py backup.tar.gz --expected etc.txt --min-mb 50
    python3 restore_drill.py --help

CI (fail the job when the drill fails):
    python3 restore_drill.py /backups/app.tar --expected /etc/s0sta/expected.txt || exit 1

Cron (weekly drill against the newest archive):
    0 3 * * 0 python3 /opt/s0sta/restore_drill.py /backups/latest.tar --expected /etc/s0sta/expected.txt

Exit codes: 0 every expected path is present and the size is sane,
1 the archive will not open, a path is missing or the size is too small,
2 usage or the expected-paths file cannot be read.

Read-only: the archive is opened with tarfile and only getmembers() is
called; nothing is extracted, written or executed. The restore command
printed at the end is a suggestion for a human, never run here.

By s0sta.com
"""
import argparse
import sys
import tarfile

MIB = 1024.0 * 1024.0


def load_expected(path):
    """Return the expected paths, or raise ValueError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValueError("%s: %s" % (path, exc))
    expected = []
    for line in lines:
        item = line.strip()
        if item and not item.startswith("#"):
            expected.append(item)
    if not expected:
        raise ValueError("%s: no expected paths" % path)
    return expected


def norm(name):
    """Normalise a tar member name for comparison."""
    while name.startswith("./"):
        name = name[2:]
    return name.lstrip("/").rstrip("/")


def args_for(argv):
    parser = argparse.ArgumentParser(
        description="Check that a tar backup holds the expected paths.")
    parser.add_argument("archive", help="tar file to inspect")
    parser.add_argument("--expected", required=True,
                        help="file with one expected path per line")
    parser.add_argument("--min-mb", type=int, default=1,
                        help="minimum unpacked size in MB (default 1)")
    args = parser.parse_args(argv)
    if args.min_mb < 0:
        parser.error("--min-mb must be zero or more")
    return args


def main(argv=None):
    args = args_for(argv)
    try:
        expected = load_expected(args.expected)
    except ValueError as exc:
        print("restore_drill: %s" % exc, file=sys.stderr)
        return 2

    try:
        with tarfile.open(args.archive, "r:*") as archive:
            members = archive.getmembers()
    except (tarfile.TarError, OSError) as exc:
        print("DRILL FAIL %s: %s" % (args.archive, exc))
        print("SUGGEST check the backup job, re-run it, then drill the new archive")
        return 1

    exact = {}
    dirs = set()
    for member in members:
        name = norm(member.name)
        if member.isdir():
            dirs.add(name)
        else:
            exact[name] = member
    total = sum(m.size for m in members if m.isfile())
    mib = total / MIB

    found = []
    missing = []
    empty = []
    for path in expected:
        key = norm(path)
        member = exact.get(key)
        if member is not None:
            found.append("RESTORE %s %d bytes" % (path, member.size))
            if member.size == 0:
                empty.append(path)
            continue
        under = [(n, m.size) for n, m in exact.items()
                 if n.startswith(key + "/")]
        if key in dirs or under:
            size = sum(s for _, s in under)
            word = "file" if len(under) == 1 else "files"
            found.append("RESTORE %s/ %d %s, %d bytes"
                         % (key, len(under), word, size))
            if size == 0:
                empty.append(path)
            continue
        missing.append(path)

    small = total < args.min_mb * 1024 * 1024
    print("ARCHIVE %s %d members %.1f MiB" % (args.archive, len(members), mib))
    for line in found:
        print(line)
    for path in missing:
        print("MISSING %s" % path)
    for path in empty:
        print("EMPTY %s" % path)
    if small:
        print("SMALL unpacked %.1f MiB < %d MiB" % (mib, args.min_mb))

    if missing or empty or small:
        print("DRILL FAIL %d missing, %d empty, %.1f MiB"
              % (len(missing), len(empty), mib))
        print("SUGGEST check the backup job, re-run it, then drill the new archive")
        return 1

    print("DRILL OK %d paths, %.1f MiB" % (len(expected), mib))
    print("SUGGEST mkdir -p /tmp/restore && tar -xf %s -C /tmp/restore"
          % args.archive)
    return 0


if __name__ == "__main__":
    sys.exit(main())
