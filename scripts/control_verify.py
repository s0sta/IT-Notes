#!/usr/bin/env python3
"""Check that every control in an inventory is still in its expected state.

A control inventory says what should be on. A config export says what is on.
This tool joins the two and reports the controls that are disabled, or that
cannot be verified at all. A control you cannot prove is a control you do not
have.

The inventory is JSON, one object per control:

    [{"control": "admin_mfa", "expected": true, "evidence": "iam.json"},
     {"control": "audit_logging", "expected": true, "evidence": "cloudtrail.json"},
     {"control": "encryption_at_rest", "expected": true, "evidence": "storage.json"}]

Each evidence file is a JSON object keyed by control id:

    {"admin_mfa": false, "audit_logging": true}

The evidence path is relative to the export directory and may not escape it.
Comparison is type-strict: true does not match "true", and 1 does not match
true. A missing file, invalid JSON, missing key or non-object export makes the
control UNVERIFIED; a value that is present but different makes it DISABLED.

Usage:
    python3 control_verify.py controls.json exports/
    python3 control_verify.py controls.json exports/ --quiet

Exit codes: 0 every control verified, 1 at least one disabled or unverified,
2 usage or an inventory that is missing, unreadable, invalid or empty.

CI (before a release, fail when a control is off):
    python3 control_verify.py controls.json exports/ || exit 1

Cron (daily 06:30, export first, then verify):
    30 6 * * * /opt/s0sta/export-config.sh && python3 /opt/s0sta/control_verify.py /etc/s0sta/controls.json /var/lib/s0sta/exports

The script is read-only. It reads the inventory and the exports and writes
nothing. Passing this check proves the setting matches the expected value in
the export you gave it; it does not prove the export is current. Put the
export timestamp beside the evidence and check that too.

Standard library only, Python 3.8+.

By s0sta.com
"""
import argparse
import json
import os
import sys

SCALARS = (bool, int, float, str)


class InputError(Exception):
    """Anything that should end the run with exit code 2."""


def load_inventory(path):
    """Return a non-empty list of controls, or raise InputError."""
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except OSError as exc:
        raise InputError("cannot read %s: %s" % (path, exc))
    except ValueError as exc:
        raise InputError("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(doc, list) or not doc:
        raise InputError("%s has no non-empty control list" % path)
    return doc


def control_fields(item, number):
    """Validate one control entry and return (control, expected, evidence)."""
    if not isinstance(item, dict):
        raise InputError("control %d is not an object" % number)
    control = item.get("control")
    expected = item.get("expected")
    evidence = item.get("evidence")
    if not isinstance(control, str) or not control:
        raise InputError("control %d has no name" % number)
    if not isinstance(expected, SCALARS):
        raise InputError("control %s has no boolean, number or string expected"
                         % control)
    if not isinstance(evidence, str) or not evidence:
        raise InputError("control %s has no evidence path" % control)
    if os.path.isabs(evidence):
        raise InputError("control %s evidence must be relative" % control)
    return control, expected, evidence


def same(expected, actual):
    """Return True only when both the type and the value match."""
    return type(expected) is type(actual) and expected == actual


def read_export(path, cache):
    """Return (document, error string). Cached by path."""
    if path not in cache:
        try:
            with open(path, encoding="utf-8") as handle:
                cache[path] = (json.load(handle), None)
        except OSError as exc:
            cache[path] = (None, "cannot read %s: %s" % (os.path.basename(path), exc))
        except ValueError:
            cache[path] = (None, "invalid JSON in %s" % os.path.basename(path))
    return cache[path]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify an inventory of controls against JSON config "
                    "exports and report disabled or unverifiable controls.",
        epilog="Exit codes: 0 all verified, 1 disabled or unverified, "
               "2 usage or input error.")
    parser.add_argument("inventory", help="JSON list of controls")
    parser.add_argument("exports", help="directory of JSON config exports")
    parser.add_argument("--quiet", action="store_true",
                        help="print the summary only")
    args = parser.parse_args(argv)

    try:
        root = os.path.realpath(args.exports)
        if not os.path.isdir(root):
            raise InputError("not a directory: %s" % root)
        inventory = load_inventory(args.inventory)

        controls = []
        seen = set()
        for number, item in enumerate(inventory, 1):
            control, expected, evidence = control_fields(item, number)
            if control in seen:
                raise InputError("duplicate control %s" % control)
            seen.add(control)
            controls.append((control, expected, evidence))
    except InputError as exc:
        print("ERR %s" % exc, file=sys.stderr)
        return 2

    cache = {}
    disabled = []
    unverified = []
    for control, expected, evidence in controls:
        path = os.path.realpath(os.path.join(root, evidence))
        if path != root and not path.startswith(root + os.sep):
            print("ERR control %s evidence escapes the export directory" % control,
                  file=sys.stderr)
            return 2
        doc, error = read_export(path, cache)
        if error:
            unverified.append((control, error))
            continue
        if not isinstance(doc, dict):
            unverified.append((control, "%s is not an object"
                               % os.path.basename(path)))
            continue
        if control not in doc:
            unverified.append((control, "missing key in %s"
                               % os.path.basename(path)))
            continue
        actual = doc[control]
        if not same(expected, actual):
            disabled.append((control, expected, actual))

    if not disabled and not unverified:
        print("OK %d controls verified" % len(controls))
        return 0

    print("FINDING %d disabled, %d unverified"
          % (len(disabled), len(unverified)))
    if disabled:
        print("DISABLED " + ", ".join(control for control, _, _ in disabled))
    if not args.quiet:
        for control, expected, actual in disabled:
            print("  %s: expected %s, got %s"
                  % (control, json.dumps(expected), json.dumps(actual)))
        for control, reason in unverified:
            print("UNVERIFIED %s: %s" % (control, reason))
    return 1


if __name__ == "__main__":
    sys.exit(main())
