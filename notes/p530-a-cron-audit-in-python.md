---
id: p530
title: "A cron audit in Python"
slug: a-cron-audit-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Cron, Linux, DevSecOps, CyberSecurity]
source: "LinkedIn post P530 · PythonSec series"
linkedin_date: 2030-02-14
design: code
script: cron_audit.py
---

# A cron audit in Python

A crontab is a list of commands that run without a terminal, often as root, often after everyone who wrote them has left. Five checks make the risk visible.

## Quick reference

The full script is at the end of this note: `cron_audit.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 cron_audit.py /tmp/crontab
```

**Example output**

```text
FINDING 5 of 5 checks
ALERT no MAILTO /tmp/crontab
```

## Explained

### What it flags

A root job is the first: the user field says who runs it, and root means no permission boundary. A world-writable script is the second: another account can replace the code between runs. A relative path is the third, because cron's working directory is not yours. A missing MAILTO is the fourth: output goes to a local mailbox nobody reads. A curl or wget piped into a shell is the fifth, and it is remote code execution on a schedule.

### What the screen shows

The 14 visible lines split environment lines from jobs, look for root, a curl pipe, a ./ path and MAILTO, then stat every script path for the other-write bit. On the fixture they print FINDING 5 of 5 checks, then ALERT no MAILTO `/tmp/crontab`.

### How to run it

`python3 cron_audit.py /etc/crontab /etc/cron.d` audits system files. `crontab -l | python3 cron_audit.py - --user-crontab --owner root` audits a user table and treats every job as root. `--cwd` resolves relative paths as cron would. Exit 0 is clean, 1 is a finding, 2 is unreadable or unparseable input. It only reads.

> **The honest caveat:** a crontab can call a wrapper that hides everything. This reads the line, not the shell script it starts.

> **The lesson:** the crontab is code that runs as root, so review it like code.

## In one line

> **Cron is a root shell.** Every line runs with the privileges of the account that owns it.

**Read the crontab**

```bash
crontab -l | python3 cron_audit.py -
```

## Script: cron_audit.py

Download: [scripts/cron_audit.py](../scripts/cron_audit.py)

```python
#!/usr/bin/env python3
"""cron_audit.py - audit crontab lines for privilege and injection risk.

Reads one or more crontab files, or stdin, and reports root jobs, scripts
that are world-writable, relative script paths, a missing MAILTO and a
curl or wget command piped into a shell.

Usage:
    python3 cron_audit.py
    python3 cron_audit.py /etc/crontab /etc/cron.d/app
    crontab -l | python3 cron_audit.py - --user-crontab --owner deploy
    python3 cron_audit.py /tmp/crontab --cwd /srv
    python3 cron_audit.py --help

CI (fail the job when a generated crontab is unsafe):
    python3 cron_audit.py build/crontab || exit 1

Cron (weekly check of the system tables):
    45 6 * * 1 python3 /opt/s0sta/cron_audit.py /etc/crontab /etc/cron.d

Exit codes: 0 no findings, 1 at least one finding, 2 usage error or
unreadable input.

Read-only: files are opened for reading and stdin is consumed. Nothing
is written, no crontab is installed and no job is run. Reports name a
line, a user or a path, never a command body, so a credential in a
crontab is not echoed.

A system crontab carries a user field after the five time fields. Pass
--user-crontab for output from crontab -l, and --owner to name whose
crontab it is so root jobs can still be found. --cwd resolves relative
script paths; cron starts system jobs in / and user jobs in the owner's
home, so set it to match.

World-writable means the regular file has the other-write bit. A missing
script is not reported: cron may run it from another mount or after a
deploy. MAILTO="" counts as set and deliberately disables mail. The
curl check matches a pipe into sh, bash, zsh, dash or ksh; it does not
prove the URL is trusted.

By s0sta.com
"""
import argparse
import os
import re
import shlex
import stat
import sys

DEFAULT_PATH = "/etc/crontab"

SPECIAL = {
    "@reboot", "@yearly", "@annually", "@monthly", "@weekly", "@daily",
    "@midnight", "@hourly",
}
ENV = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
SHELL = re.compile(r"\b(sh|bash|zsh|dash|ksh)\b")
FETCH = re.compile(r"\b(curl|wget)\b")
SCRIPT_SUFFIX = (".sh", ".bash", ".py", ".pl", ".rb")
OPERATORS = {"|", "||", "&&", ";", ">", ">>", "<", "2>", "2>>", "&"}
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
DAYS = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
FIELDS = (
    (0, 59, None),
    (0, 23, None),
    (1, 31, None),
    (1, 12, MONTHS),
    (0, 7, DAYS),
)


class InputError(Exception):
    """An input that cannot be audited."""


def read_text(path):
    """Return (label, text) for a file or - for stdin, or raise InputError."""
    if path == "-":
        try:
            return "<stdin>", sys.stdin.read()
        except UnicodeDecodeError:
            raise InputError("stdin: not UTF-8 text")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return path, handle.read()
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except UnicodeDecodeError:
        raise InputError("%s: not UTF-8 text" % path)


def field_value(text, low, high, names):
    """True when one cron field component is in range or a known name."""
    value = text.strip()
    if not value:
        return False
    if names is not None and value.lower() in names:
        return True
    if not value.isdigit():
        return False
    return low <= int(value) <= high


def valid_field(token, low, high, names):
    """True for *, steps, lists and ranges in one cron field."""
    for part in token.split(","):
        core = part.split("/", 1)[0]
        if "/" in part:
            step = part.split("/", 1)[1]
            if not step.isdigit() or int(step) == 0:
                return False
        if core == "*":
            continue
        if "-" in core:
            first, second = core.split("-", 1)
            if not field_value(first, low, high, names):
                return False
            if not field_value(second, low, high, names):
                return False
        elif not field_value(core, low, high, names):
            return False
    return True


def valid_time(tokens):
    """True when the five time fields look like a crontab schedule."""
    return all(
        valid_field(token, low, high, names)
        for token, (low, high, names) in zip(tokens, FIELDS)
    )


def parse(text, user_mode, owner):
    """Return (environment, jobs, malformed count).

    A job is (line number, user or None, command token list).
    """
    environment = {}
    jobs = []
    malformed = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        assignment = ENV.match(line)
        if assignment:
            environment[assignment.group(1)] = assignment.group(2)
            continue
        try:
            tokens = shlex.split(line, comments=False, posix=True)
        except ValueError:
            malformed += 1
            continue
        if not tokens:
            continue
        if tokens[0].lower() in SPECIAL:
            if user_mode:
                user, command = owner, tokens[1:]
            else:
                if len(tokens) < 3:
                    malformed += 1
                    continue
                user, command = tokens[1], tokens[2:]
        else:
            if len(tokens) < 6 or not valid_time(tokens[:5]):
                malformed += 1
                continue
            if user_mode:
                user, command = owner, tokens[5:]
            else:
                if len(tokens) < 7:
                    malformed += 1
                    continue
                user, command = tokens[5], tokens[6:]
        if not command:
            malformed += 1
            continue
        jobs.append((number, user, command))
    return environment, jobs, malformed


def command_paths(command, cwd):
    """Return (kind, token) for every script-like path in a command."""
    found = []
    for token in command:
        if not token or token in OPERATORS or token.startswith("-"):
            continue
        if "://" in token:
            continue
        if token.startswith("/"):
            found.append(("absolute", token))
        elif token.startswith(("./", "../")) or (
            "/" in token and token.endswith(SCRIPT_SUFFIX)
        ):
            found.append(("relative", token))
    return found


def world_writable(path):
    """True when path is a regular file with the other-write bit set."""
    try:
        info = os.stat(path)
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode) and bool(info.st_mode & stat.S_IWOTH)


def piped_to_shell(command):
    """True when a curl or wget in the command is piped into a shell."""
    text = " ".join(command)
    if "|" not in text:
        return False
    left, right = text.split("|", 1)
    if not FETCH.search(left):
        return False
    return bool(SHELL.search(right))


def audit_file(label, environment, jobs, cwd):
    """Return a list of (kind, message) findings for one crontab."""
    findings = []

    for number, user, command in jobs:
        if user and user.lower() == "root":
            paths = command_paths(command, cwd)
            shown = paths[0][1] if paths else "inline command"
            findings.append(("ROOT", "line %d: root job %s" % (number, shown)))

    for number, _user, command in jobs:
        seen = set()
        for kind, token in command_paths(command, cwd):
            if token in seen:
                continue
            seen.add(token)
            if kind == "absolute":
                resolved = token
            else:
                resolved = os.path.normpath(os.path.join(cwd, token))
            if world_writable(resolved):
                findings.append(
                    ("WW", "line %d: %s is world-writable" % (number, token)))

    for number, _user, command in jobs:
        seen = set()
        for kind, token in command_paths(command, cwd):
            if kind != "relative" or token in seen:
                continue
            seen.add(token)
            findings.append(
                ("REL", "line %d: relative path %s" % (number, token)))

    if jobs and "MAILTO" not in environment:
        findings.append(("MAIL", "line %d: no MAILTO set" % jobs[0][0]))

    for number, _user, command in jobs:
        if piped_to_shell(command):
            findings.append(
                ("PIPE", "line %d: curl or wget piped to a shell" % number))

    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit crontab lines for privilege and injection risk.")
    parser.add_argument(
        "paths", nargs="*", default=[DEFAULT_PATH],
        help="crontab files to audit, or - for stdin "
             "(default: %s)" % DEFAULT_PATH)
    parser.add_argument(
        "--user-crontab", action="store_true",
        help="input has no user field, as produced by crontab -l")
    parser.add_argument(
        "--owner", default=None,
        help="owner of a user crontab, so root jobs can be found")
    parser.add_argument(
        "--cwd", default="/",
        help="directory used to resolve relative script paths (default: /)")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.cwd):
        parser.error("--cwd must be an existing directory")
    if args.owner is not None and not args.owner.strip():
        parser.error("--owner must not be empty")

    total = []
    labels = []
    malformed_total = 0
    jobs_total = 0
    for path in args.paths:
        try:
            label, text = read_text(path)
        except InputError as exc:
            print("ERROR %s" % exc, file=sys.stderr)
            return 2
        labels.append(label)
        if not text.strip():
            continue
        environment, jobs, malformed = parse(
            text, args.user_crontab, args.owner)
        malformed_total += malformed
        jobs_total += len(jobs)
        if not jobs and not environment and malformed:
            print("ERROR %s: no crontab lines understood" % label,
                  file=sys.stderr)
            return 2
        total.extend(audit_file(label, environment, jobs, args.cwd))

    if malformed_total:
        print("NOTE %d line(s) not understood and skipped" % malformed_total,
              file=sys.stderr)
    if not jobs_total:
        print("OK no jobs found in %s" % ", ".join(labels))
        return 0
    if total:
        for kind, message in total:
            print("%-5s %s" % (kind, message))
        print("FINDING %d finding(s) in %s" % (len(total), ", ".join(labels)))
        return 1
    print("OK no findings in %s" % ", ".join(labels))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
