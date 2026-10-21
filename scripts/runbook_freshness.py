#!/usr/bin/env python3
"""Flag runbooks that are stale, unowned or pointing at a missing file.

Scans a directory of markdown runbooks and checks three things a runbook
needs before anyone trusts it at 03:00:

    reviewed    a "Last reviewed: YYYY-MM-DD" line in the first 40 lines,
                no older than --days (default 90)
    owner       an "Owner: name" line that is not a placeholder
    links       every relative markdown link resolves to a real file

Metadata is read from the first 40 lines and may be plain, bold or a list
item:

    Last reviewed: 2026-07-14
    **Owner:** payments-oncall

Accepted date formats are YYYY-MM-DD, YYYY/MM/DD and DD/MM/YYYY. A missing
date counts as stale; an unreadable one is reported as BADDATE. External
links, anchors and absolute paths are ignored. A relative link is resolved
against the directory of the runbook that contains it.

Usage:
    python3 runbook_freshness.py docs/runbooks
    python3 runbook_freshness.py docs/runbooks --days 120
    python3 runbook_freshness.py docs/runbooks --today 2026-10-21

--today makes the age calculation reproducible in a test or during a review.

Exit codes: 0 every runbook is fresh, owned and linked, 1 at least one
finding, 2 usage or an input directory with no markdown files.

CI (documentation gate, fail the build when a runbook rots):
    python3 runbook_freshness.py docs/runbooks --days 90 || exit 1

Cron (Monday 07:00, mail the owners):
    0 7 * * 1 python3 /opt/s0sta/runbook_freshness.py /srv/docs/runbooks

The script is read-only. It reads the markdown and checks the filesystem;
it never edits a runbook or touches a link. A fresh date proves somebody
opened the file, not that the commands in it still work. Rehearse the drill.

Standard library only, Python 3.8+.

By s0sta.com
"""
import argparse
import datetime
import os
import re
import sys
from urllib.parse import unquote

DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y")
META = re.compile(r"^(last reviewed|reviewed|owner)\s*:\s*(.+)$", re.I)
LINK = re.compile(r"\]\(([^)]+)\)")
PLACEHOLDERS = {"", "-", "?", "n/a", "na", "none", "tbd", "todo", "unassigned"}


class InputError(Exception):
    """Anything that should end the run with exit code 2."""


def markdown_files(root):
    """Return sorted markdown paths under root, skipping dot directories."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if name.lower().endswith(".md"):
                found.append(os.path.join(dirpath, name))
    return found


def metadata(text):
    """Return {'last reviewed': value, 'owner': value} from the first 40 lines."""
    found = {}
    for line in text.splitlines()[:40]:
        clean = re.sub(r"^[#>\-+*]+\s+", "", line.strip())
        clean = clean.replace("**", "").replace("__", "")
        match = META.match(clean.strip())
        if not match:
            continue
        key = match.group(1).lower()
        if key == "reviewed":
            key = "last reviewed"
        if key not in found:
            found[key] = match.group(2).strip()
    return found


def review_date(value):
    """Parse the first token of a review date, or return None."""
    token = value.split()[0] if value.split() else ""
    token = token.strip(".,;:()[]")
    for fmt in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(token, fmt).date()
        except ValueError:
            continue
    return None


def relative_links(text):
    """Return [(raw, path)] for relative markdown links worth checking."""
    links = []
    for raw in LINK.findall(text):
        target = raw.strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        target = target.split()[0] if target.split() else ""
        if not target:
            continue
        low = target.lower()
        if low.startswith(("#", "/", "http://", "https://", "mailto:", "tel:", "data:")):
            continue
        if "{{" in target or "}}" in target:
            continue
        path = unquote(target.split("#")[0].split("?")[0])
        if path:
            links.append((target, path))
    return links


def check_runbook(path, root, today, days):
    """Return a list of (kind, detail) findings for one runbook."""
    rel = os.path.relpath(path, root)
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError as exc:
        return [("UNREADABLE", "%s: %s" % (rel, exc))]

    findings = []
    meta = metadata(text)

    if "last reviewed" not in meta:
        findings.append(("NODATE", "%s has no last reviewed line" % rel))
    else:
        when = review_date(meta["last reviewed"])
        if when is None:
            findings.append(("BADDATE", "%s has an unreadable review date: %s"
                             % (rel, meta["last reviewed"])))
        elif when > today:
            findings.append(("FUTURE", "%s claims a future review: %s" % (rel, when)))
        else:
            age = (today - when).days
            if age > days:
                findings.append(("STALE", "%s last reviewed %s, %d days ago"
                                 % (rel, when, age)))

    owner = meta.get("owner", "").strip().lower()
    if owner in PLACEHOLDERS:
        findings.append(("UNOWNED", "%s has no owner" % rel))

    base = os.path.dirname(path)
    for raw, target in relative_links(text):
        resolved = os.path.normpath(os.path.join(base, target))
        if not os.path.exists(resolved):
            findings.append(("BROKEN", "%s -> %s" % (rel, raw)))
    return findings


def positive(value):
    """argparse type for a non-negative integer."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not an integer" % value)
    if number < 0:
        raise argparse.ArgumentTypeError("%s is negative" % value)
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Find runbooks that are stale, unowned or link to a "
                    "file that no longer exists.",
        epilog="Exit codes: 0 clean, 1 findings, 2 usage or input error.")
    parser.add_argument("root", help="directory of markdown runbooks")
    parser.add_argument("--days", type=positive, default=90,
                        help="maximum age in days (default: 90)")
    parser.add_argument("--today", help="date to measure age from (YYYY-MM-DD)")
    args = parser.parse_args(argv)

    try:
        root = os.path.abspath(args.root)
        if not os.path.isdir(root):
            raise InputError("not a directory: %s" % root)
        if args.today:
            today = review_date(args.today)
            if today is None:
                raise InputError("--today is not a date: %s" % args.today)
        else:
            today = datetime.date.today()
        paths = markdown_files(root)
        if not paths:
            raise InputError("no markdown files under %s" % root)
    except InputError as exc:
        print("ERR %s" % exc, file=sys.stderr)
        return 2

    findings = []
    for path in paths:
        findings.extend(check_runbook(path, root, today, args.days))

    stale = sum(1 for kind, _ in findings
                if kind in ("STALE", "NODATE", "BADDATE", "FUTURE"))
    unowned = sum(1 for kind, _ in findings if kind == "UNOWNED")
    broken = sum(1 for kind, _ in findings if kind == "BROKEN")

    if not findings:
        print("OK %d runbooks fresh, owned and linked" % len(paths))
        return 0

    print("FINDING %d stale, %d unowned, %d broken" % (stale, unowned, broken))
    for kind, detail in findings:
        print("%s %s" % (kind, detail))
    return 1


if __name__ == "__main__":
    sys.exit(main())
