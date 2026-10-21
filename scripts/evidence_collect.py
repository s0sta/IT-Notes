#!/usr/bin/env python3
"""evidence_collect.py - hash a case directory into one defensible manifest.

Walks a path, hashes every regular file with SHA-256, counts the lines in a
process export and the sockets in a network export, and prints one manifest
to stdout: a line per artefact, the totals, and a bundle hash over all the
artefacts together. Capture the manifest beside the bundle, not inside it.

The manifest is the evidence. It proves that the bytes you kept are the
bytes you collected, and the bundle hash proves that no line was removed
from the list afterwards.

Usage:
    python3 evidence_collect.py /cases/inc-214
    python3 evidence_collect.py /cases/inc-214 --ps ps.txt --net ss.txt
    python3 evidence_collect.py /cases/inc-214 ps.txt ss.txt
    python3 evidence_collect.py /cases/inc-214 --ps ps.txt --net ss.txt --json
    python3 evidence_collect.py /cases/inc-214 --ps ps.txt --net ss.txt > manifest.txt
    python3 evidence_collect.py --help

CI (seal the bundle and fail the job when an artefact cannot be read):
    python3 evidence_collect.py /cases/inc-214 --ps ps.txt --net ss.txt > manifest.txt

Cron (one manifest per case, kept next to the bundle):
    17 * * * * python3 /opt/s0sta/evidence_collect.py /cases/inc-214 --ps /cases/inc-214/ps.txt --net /cases/inc-214/ss.txt > /cases/inc-214/manifest.txt

Exit codes: 0 manifest complete, 1 an artefact could not be read or the path
holds no regular file, 2 usage error or a missing path.

Read-only: opens the given files for reading, hashes the bytes and prints.
It writes nothing, changes nothing and makes no network call. It never
prints file contents, only names, sizes and digests.

Symbolic links are recorded by target and not followed, so a link planted
inside the case directory cannot pull a file from outside it into the
bundle. Directories are not hashed; an empty directory is a finding, not a
clean run.

By s0sta.com
"""
import argparse
import hashlib
import json
import os
import stat
import sys

CHUNK = 1024 * 1024
PS_SKIP = ("pid", "user", "uid", "owner")
NET_SKIP = ("state", "proto", "netid", "recv-q", "active", "local")
NET_STATES = ("estab", "listen", "time-wait", "close-wait", "syn-sent",
              "fin-wait-1", "fin-wait-2", "last-ack", "closing", "closed",
              "unconn", "syn-recv")


class InputError(Exception):
    """An input that cannot be audited."""


def sha256_file(path):
    """Return the hex digest of a file, reading it in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def read_text(source):
    """Return the whole input as text, or raise InputError."""
    try:
        if source == "-":
            return sys.stdin.read()
        with open(source, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError as exc:
        raise InputError("%s: %s" % (source, exc.strerror or exc))


def count_ps(text):
    """Count process rows in a ps export, skipping any header and callbacks."""
    rows = 0
    for line in text.splitlines():
        fields = line.split()
        if not fields or fields[0].lower() in PS_SKIP:
            continue
        if line.startswith(("UID", "PID", "USER")):
            continue
        rows += 1
    return rows


def count_net(text):
    """Count socket rows in an ss or netstat export."""
    rows = 0
    for line in text.splitlines():
        fields = line.split()
        if not fields or fields[0].lower() in NET_SKIP:
            continue
        if fields[0].lower() in NET_STATES or fields[0].startswith(("tcp", "udp", "raw")):
            rows += 1
    return rows


def walk(root, exclude=()):
    """Return (files, links, skipped) for a directory, without following links."""
    files, links, skipped = [], [], []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            if os.path.realpath(full) in exclude:
                continue
            try:
                info = os.lstat(full)
            except OSError as exc:
                skipped.append((rel, exc.strerror or str(exc)))
                continue
            if stat.S_ISLNK(info.st_mode):
                try:
                    links.append((rel, os.readlink(full)))
                except OSError as exc:
                    skipped.append((rel, exc.strerror or str(exc)))
                continue
            if not stat.S_ISREG(info.st_mode):
                skipped.append((rel, "not a regular file"))
                continue
            try:
                digest = sha256_file(full)
            except OSError as exc:
                skipped.append((rel, exc.strerror or str(exc)))
                continue
            files.append({"path": rel, "size": info.st_size, "sha256": digest})
    files.sort(key=lambda row: row["path"])
    links.sort(key=lambda row: row[0])
    skipped.sort(key=lambda row: row[0])
    return files, links, skipped


def bundle_hash(files, exports):
    """Hash the artefact digests in manifest order: files first, then exports.

    Each digest is 64 hex characters, so the concatenation is unambiguous.
    Removing, adding or reordering one artefact changes the bundle hash.
    """
    digest = hashlib.sha256()
    for row in files:
        digest.update(row["sha256"].encode())
    for row in exports:
        digest.update(row["sha256"].encode())
    return digest.hexdigest()


def build_manifest(root, ps_path, net_path):
    """Return the manifest as a dict, or raise InputError."""
    if not os.path.exists(root):
        raise InputError("%s: no such path" % root)
    exclude = set(os.path.realpath(p) for p in (ps_path, net_path) if p and p != "-")
    if os.path.isdir(root):
        files, links, skipped = walk(root, exclude)
    else:
        info = os.lstat(root)
        if not stat.S_ISREG(info.st_mode):
            raise InputError("%s: not a regular file or directory" % root)
        files = [{"path": os.path.basename(root), "size": info.st_size,
                  "sha256": sha256_file(root)}]
        links, skipped = [], []

    exports = []
    if ps_path:
        text = read_text(ps_path)
        exports.append({"kind": "ps", "path": ps_path, "count": count_ps(text),
                        "unit": "lines", "sha256": sha256_file(ps_path)
                        if ps_path != "-" else hashlib.sha256(text.encode()).hexdigest()})
    if net_path:
        text = read_text(net_path)
        exports.append({"kind": "net", "path": net_path, "count": count_net(text),
                        "unit": "sockets", "sha256": sha256_file(net_path)
                        if net_path != "-" else hashlib.sha256(text.encode()).hexdigest()})

    manifest = {
        "root": root,
        "files": files,
        "links": [{"path": p, "target": t} for p, t in links],
        "skipped": [{"path": p, "reason": r} for p, r in skipped],
        "exports": exports,
        "bytes": sum(row["size"] for row in files),
        "bundle": bundle_hash(files, exports),
    }
    return manifest


def print_manifest(man):
    """Print the human manifest, one line per artefact."""
    print("MANIFEST %d files, %d exports" % (len(man["files"]), len(man["exports"])))
    for row in man["files"]:
        print("FILE %s %d %s" % (row["sha256"], row["size"], row["path"]))
    for row in man["links"]:
        print("LINK %s -> %s" % (row["path"], row["target"]))
    for row in man["exports"]:
        print("EXPORT %s %s %d %s" % (row["kind"], row["sha256"], row["count"], row["unit"]))
    for row in man["skipped"]:
        print("SKIP %s: %s" % (row["path"], row["reason"]))
    if man["skipped"]:
        print("INCOMPLETE %d artefact(s) not hashed" % len(man["skipped"]))
    print("TOTAL %d files, %d bytes" % (len(man["files"]), man["bytes"]))
    print("BUNDLE %s" % man["bundle"])


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Hash a case directory into an evidence manifest (read-only).")
    parser.add_argument("path", help="directory or single file to hash")
    parser.add_argument("exports", nargs="*", metavar="EXPORT",
                        help="optional process and network exports, in that order")
    parser.add_argument("--ps", metavar="FILE",
                        help="text export of the process list (ps -eo pid,user,args)")
    parser.add_argument("--net", metavar="FILE",
                        help="text export of the socket table (ss -tanp)")
    parser.add_argument("--json", action="store_true",
                        help="print the manifest as JSON instead of lines")
    args = parser.parse_args(argv)

    if len(args.exports) > 2:
        print("ERROR at most two positional exports (ps, then net)", file=sys.stderr)
        return 2
    if args.exports:
        args.ps = args.ps or args.exports[0]
    if len(args.exports) > 1:
        args.net = args.net or args.exports[1]

    try:
        man = build_manifest(args.path, args.ps, args.net)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    if not man["files"] and not man["skipped"]:
        print("MANIFEST 0 files, 0 exports")
        print("EMPTY no regular file under %s" % man["root"])
        print("BUNDLE %s" % man["bundle"])
        return 1

    if args.json:
        print(json.dumps(man, indent=2, sort_keys=True))
    else:
        print_manifest(man)
    return 1 if man["skipped"] else 0


if __name__ == "__main__":
    sys.exit(main())
