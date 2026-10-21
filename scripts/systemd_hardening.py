#!/usr/bin/env python3
"""systemd_hardening.py - score systemd service units on hardening.

Reads one .service file or a directory tree of units and gives each unit
a score out of 100 for the sandboxing and privilege directives it sets.
Four basics are worth 15 points each: NoNewPrivileges, ProtectSystem,
PrivateTmp and RestrictAddressFamilies. Eight further directives are
worth 5 each, including ProtectHome, PrivateDevices, ProtectKernel*
and SystemCallFilter.

Usage:
    python3 systemd_hardening.py /etc/systemd/system/sshd.service
    python3 systemd_hardening.py /etc/systemd/system
    python3 systemd_hardening.py /tmp/units --threshold 80
    python3 systemd_hardening.py --help

CI (fail a unit build when the score drops):
    python3 systemd_hardening.py ./units --threshold 70 || exit 1

Cron (weekly drift report for the boot image):
    15 5 * * 1 python3 /opt/s0sta/systemd_hardening.py /etc/systemd/system

Exit codes: 0 every unit is at or above the threshold, 1 at least one
unit is below it, 2 usage error, unreadable input or a directory with no
.service files.

Read-only: unit files are opened for reading. Nothing is written, no
unit is reloaded, started or stopped and no process is touched. Only
directive names are printed, never their values, so a credential in an
Environment= line is not echoed.

The score is a prompt, not a verdict. A network service may legitimately
skip PrivateNetwork and a unit that needs AF_NETLINK may list it in
RestrictAddressFamilies. Raise --threshold when you want the extras to
count. Only the [Service] section is read; drop-ins under .d/ are not
merged, so audit a merged unit with systemctl cat first.

By s0sta.com
"""
import argparse
import sys
from pathlib import Path

TRUE = ("yes", "true", "1", "on")
CHECKS = (
    ("NoNewPrivileges", TRUE, 15, True),
    ("ProtectSystem", ("strict", "full", "yes", "true"), 15, True),
    ("PrivateTmp", TRUE, 15, True),
    ("RestrictAddressFamilies", None, 15, True),
    ("ProtectHome", ("yes", "true", "read-only", "tmpfs"), 5, False),
    ("PrivateDevices", TRUE, 5, False),
    ("ProtectKernelTunables", TRUE, 5, False),
    ("ProtectKernelModules", TRUE, 5, False),
    ("ProtectControlGroups", TRUE, 5, False),
    ("RestrictNamespaces", TRUE, 5, False),
    ("LockPersonality", TRUE, 5, False),
    ("SystemCallFilter", None, 5, False),
)


class InputError(Exception):
    """An input path that cannot be audited."""


def unit_paths(path):
    """Return a sorted list of .service files for one file or directory."""
    root = Path(path)
    if root.is_dir():
        files = sorted(root.rglob("*.service"))
        if not files:
            raise InputError("%s: no .service files found" % path)
        return files
    if root.is_file():
        if root.suffix != ".service":
            raise InputError("%s: not a .service file" % path)
        return [root]
    raise InputError("%s: no such file or directory" % path)


def parse_service(text):
    """Return the [Service] key/value pairs, last value winning."""
    values = {}
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        if section != "service" or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            values[key] = value.strip()
    return values


def normalise(value):
    """Strip surrounding quotes and whitespace from a unit value."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def score(values):
    """Return (score, missing basics, missing extras)."""
    earned = 0
    missing_basics = []
    missing_extras = []
    for name, allowed, points, basic in CHECKS:
        value = values.get(name)
        if allowed is None:
            present = value is not None and normalise(value) != ""
        else:
            present = value is not None and normalise(value).lower() in allowed
        if present:
            earned += points
        elif basic:
            missing_basics.append(name)
        else:
            missing_extras.append(name)
    return earned, missing_basics, missing_extras


def audit(path, threshold):
    """Print one line per unit and return the number below the threshold."""
    low = 0
    units = 0
    for unit in unit_paths(path):
        try:
            text = unit.read_text(encoding="utf-8")
        except OSError as exc:
            raise InputError("%s: %s" % (unit, exc.strerror or exc))
        except UnicodeDecodeError:
            raise InputError("%s: not UTF-8 text" % unit)
        units += 1
        values = parse_service(text)
        points, missing_basics, missing_extras = score(values)
        missing = missing_basics + missing_extras
        shown = ", ".join(missing) if missing else "none"
        print("UNIT  %-28s score %3d missing %s" % (unit.name, points, shown))
        if points < threshold:
            low += 1
    if low:
        print("FINDING %d unit(s) below %d (%d scanned)"
              % (low, threshold, units))
    else:
        noun = "unit" if units == 1 else "units"
        print("OK all %d %s at or above %d" % (units, noun, threshold))
    return low


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Score systemd .service units on hardening (read-only).")
    parser.add_argument(
        "path", help="a .service file or a directory to scan")
    parser.add_argument(
        "--threshold", type=int, default=60,
        help="minimum passing score, 0-100 (default: 60)")
    args = parser.parse_args(argv)
    if not 0 <= args.threshold <= 100:
        parser.error("--threshold must be between 0 and 100")

    try:
        low = audit(args.path, args.threshold)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2
    return 1 if low else 0


if __name__ == "__main__":
    sys.exit(main())
