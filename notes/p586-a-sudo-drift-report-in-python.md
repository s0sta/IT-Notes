---
id: p586
title: "A sudo drift report in Python"
slug: a-sudo-drift-report-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Linux, Sudo, DevSecOps, CyberSecurity]
source: "LinkedIn post P586 · PythonFixes series"
linkedin_date: 2030-06-25
design: code
script: sudo_drift.py
---

# A sudo drift report in Python

A one-line sudoers change let the deploy user run every command without a password. The review approved a restart command; the merged line said ALL.

## Quick reference

The full script is at the end of this note: `sudo_drift.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 sudo_drift.py before after
```

**Example output**

```text
WIDEN %deploy ALL
ADDED carol /usr/bin/passwd
```

## Explained

### What it does

It parses two sudoers snapshots, expands the aliases, and compares what each user can run. It reports a new user, a new NOPASSWD grant, a command added to an existing rule, a wildcard path and a runas list that became ALL. A change that only removes or narrows grants exits 0. On screen the diff prints WIDEN %deploy ALL and ADDED carol `/usr/bin/passwd`, then exits 1.

### How to run it

`python3 sudo_drift.py before.sudoers after.sudoers`. In CI, render the before file from the main branch and the after file from the pull request, then let the exit code gate the merge. From cron, compare the baseline with the live file.

### The fix

Revert the widening or scope it to one command: NOPASSWD on `/usr/bin/systemctl` restart app is a grant you can defend. Re-run the diff until it exits 0, then run `visudo -c` to prove the file still parses.

### Prevention

Keep sudoers in Git and review every NOPASSWD line as a privilege change. A command added to an existing rule is the quiet case, because the diff looks like a longer line rather than a new permission.

> **The honest caveat:** this is a line parser, not visudo. Includes are reported and not followed, and arguments are compared as text, so a clean diff is not a clean host.

> **The lesson:** sudo drift is a silent grant until someone diffs it.

## In one line

> **Sudo drift is a silent grant.** A longer line in a text file can be full root on the host.

**Diff before merge**

```bash
python3 sudo_drift.py old.conf new.conf
```

## Script: sudo_drift.py

Download: [scripts/sudo_drift.py](../scripts/sudo_drift.py)

```python
#!/usr/bin/env python3
"""sudo_drift.py - show what a sudoers change widened.

Compares two sudoers snapshots (before and after) and reports the grants that
grew: a new user, a new NOPASSWD command, a command added to an existing rule,
a wildcard path, or a runas list that became ALL. A change that only removes
or narrows grants exits 0, so the check can gate a pull request.

Usage:
    python3 sudo_drift.py before.sudoers after.sudoers
    python3 sudo_drift.py before.sudoers after.sudoers --json
    python3 sudo_drift.py --help

CI (fail the change that widens sudo):
    python3 sudo_drift.py before.sudoers after.sudoers || exit 1

Cron (weekly diff of the managed snapshot against the live file):
    0 6 * * 1 python3 /opt/s0sta/sudo_drift.py /etc/s0sta/sudoers.baseline /etc/sudoers

Exit codes: 0 no widening, 1 at least one widening, 2 usage error or
unreadable, empty or rule-free input.

Read-only: both files are opened for reading. Nothing is written, no rule is
installed and no command is executed. Reports name users and command paths,
never a command argument, so a password passed on a sudo line is not echoed.

This is a line parser, not visudo. User_Alias, Runas_Alias and Cmnd_Alias are
expanded; #include and #includedir are reported on stderr and not followed; a
comma inside a command argument must be escaped, as sudoers itself requires.
Run visudo -c for syntax and this script for the change in exposure.

By s0sta.com
"""
import argparse
import fnmatch
import json
import re
import sys

ALIAS = re.compile(
    r"^(User_Alias|Runas_Alias|Cmnd_Alias)\s+([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.+)$",
    re.IGNORECASE,
)
INCLUDE = re.compile(r"^[#@]include(dir)?\s+(\S+)", re.IGNORECASE)
RUNAS = re.compile(r"^\(([^)]*)\)\s*(.*)$")
TAG = re.compile(
    r"^(?:(?:NOPASSWD|PASSWD|NOEXEC|EXEC|SETENV|NOSETENV|LOG_INPUT|"
    r"NOLOG_INPUT|LOG_OUTPUT|NOLOG_OUTPUT|MAIL|NOMAIL|FOLLOW|NOFOLLOW)"
    r"\s*:\s*)+",
    re.IGNORECASE,
)


class InputError(Exception):
    """An input that cannot be audited."""


def read_text(path):
    """Return the file text, or raise InputError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except UnicodeDecodeError:
        raise InputError("%s: not UTF-8 text" % path)
    if not text.strip():
        raise InputError("%s: empty input" % path)
    return text


def logical_lines(text):
    """Yield (line number, joined line) with continuations folded."""
    buffered = ""
    start = 1
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if not buffered:
            start = number
        if line.endswith("\\"):
            buffered += line[:-1] + " "
            continue
        buffered += line
        yield start, buffered
        buffered = ""
    if buffered:
        yield start, buffered


def strip_comment(line):
    """Remove a # comment, keeping an include directive readable."""
    stripped = line.strip()
    if INCLUDE.match(stripped):
        return stripped
    if stripped.startswith(("#", "@")):
        return ""
    return stripped.split("#", 1)[0].strip()


def split_escaped(text):
    """Split a comma list, keeping escaped commas inside an argument."""
    parts = []
    current = ""
    escaped = False
    for char in text:
        if escaped:
            current += char
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ",":
            parts.append(current)
            current = ""
        else:
            current += char
    parts.append(current)
    return [part.strip() for part in parts if part.strip()]


def parse_aliases(lines):
    """Return user, runas and command aliases plus include lines."""
    users = {}
    runas = {}
    commands = {}
    includes = []
    for number, raw in lines:
        line = strip_comment(raw)
        if not line:
            continue
        if INCLUDE.match(line):
            includes.append((number, line))
            continue
        found = ALIAS.match(line)
        if not found:
            continue
        kind = found.group(1).lower()
        name = found.group(2)
        values = split_escaped(found.group(3))
        if kind == "user_alias":
            users[name] = values
        elif kind == "runas_alias":
            runas[name] = values
        else:
            commands[name] = values
    return users, runas, commands, includes


def expand(items, aliases, seen=None):
    """Expand alias names in a list, dropping negated entries."""
    seen = set() if seen is None else set(seen)
    out = []
    for item in items:
        raw = item.strip()
        if not raw or raw.startswith("!"):
            continue
        if raw in aliases and raw not in seen:
            out.extend(expand(aliases[raw], aliases, seen | {raw}))
        else:
            out.append(raw)
    return out


def parse_runas(text):
    """Return the runas users from the text inside the parentheses."""
    users = []
    for chunk in text.replace(":", ",").split(","):
        name = chunk.strip()
        if name and not name.startswith("!"):
            users.append(name)
    return users or ["root"]


def parse_grants(text):
    """Return ({user: profile}, rule count, include lines, skipped count)."""
    lines = list(logical_lines(text))
    user_alias, runas_alias, cmd_alias, includes = parse_aliases(lines)
    profiles = {}
    rules = 0
    skipped = 0
    for number, raw in lines:
        line = strip_comment(raw)
        if (not line or INCLUDE.match(line) or ALIAS.match(line)
                or line.lower().startswith("defaults")):
            continue
        if "=" not in line:
            skipped += 1
            continue
        left, right = line.split("=", 1)
        tokens = left.split()
        if len(tokens) < 2:
            skipped += 1
            continue
        users = expand(split_escaped(" ".join(tokens[:-1])), user_alias)
        if not users:
            skipped += 1
            continue
        body = right.strip()
        runas = ["root"]
        found = RUNAS.match(body)
        if found:
            runas = expand(parse_runas(found.group(1)), runas_alias)
            body = found.group(2).strip()
        nopasswd = False
        commands = []
        for segment in split_escaped(body):
            tags = TAG.match(segment)
            if tags:
                names = re.findall(r"([A-Z_]+)\s*:", tags.group(0))
                if names:
                    nopasswd = names[-1].upper() == "NOPASSWD"
                segment = segment[tags.end():].strip()
            if not segment:
                continue
            if segment in cmd_alias:
                for command in expand([segment], cmd_alias):
                    commands.append((" ".join(command.split()), nopasswd))
            else:
                commands.append((" ".join(segment.split()), nopasswd))
        if not commands:
            skipped += 1
            continue
        rules += 1
        for user in users:
            profile = profiles.setdefault(
                user, {"cmds": {}, "runas": set(), "rules": 0})
            profile["rules"] += 1
            profile["runas"].update(runas)
            for command, flag in commands:
                profile["cmds"][command] = profile["cmds"].get(command, False) or flag
    return profiles, rules, includes, skipped


def covered(command, paths):
    """True when a command is already inside one of the granted paths."""
    if "ALL" in paths:
        return True
    return any(fnmatch.fnmatchcase(command, path)
               for path in paths if "*" in path or "?" in path)


def covered_nopasswd(command, profile):
    """True when a command is already granted without a password."""
    for path, flag in profile["cmds"].items():
        if not flag:
            continue
        if path == "ALL" or path == command:
            return True
        if ("*" in path or "?" in path) and fnmatch.fnmatchcase(command, path):
            return True
    return False


def display(command):
    """Show a command path, never its arguments."""
    return command if command == "ALL" else command.split()[0]


def compare(before, after):
    """Return (widenings, removed users, narrowed command count)."""
    widenings = []
    seen = set()

    def note(kind, user, detail):
        key = (kind, user, detail)
        if key not in seen:
            seen.add(key)
            widenings.append(key)

    removed = sorted(set(before) - set(after))
    narrowed = 0
    for user in sorted(after):
        profile = after[user]
        if user not in before:
            note("ADDED", user, "new user")
            continue
        old = before[user]
        old_paths = set(old["cmds"])
        for command in sorted(profile["cmds"]):
            flag = profile["cmds"][command]
            if command in old["cmds"]:
                if flag and not old["cmds"][command]:
                    note("NOPASSWD", user, display(command))
            elif not covered(command, old_paths):
                if flag:
                    note("NOPASSWD", user, display(command))
                elif "*" in command or "?" in command:
                    note("WILDCARD", user, display(command))
                else:
                    note("WIDEN", user, display(command))
            elif flag and not covered_nopasswd(command, old):
                note("NOPASSWD", user, display(command))
        if "ALL" in profile["runas"] and "ALL" not in old["runas"]:
            note("RUNAS", user, "ALL")
        for command in old["cmds"]:
            if command not in profile["cmds"]:
                narrowed += 1
    return widenings, removed, narrowed


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Compare two sudoers snapshots for wider privileges.")
    parser.add_argument("before", help="sudoers snapshot before the change")
    parser.add_argument("after", help="sudoers snapshot after the change")
    parser.add_argument("--json", action="store_true",
                        help="print the widenings as a JSON list")
    args = parser.parse_args(argv)
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        before_text = read_text(args.before)
        after_text = read_text(args.after)
        before, before_rules, before_includes, before_skipped = parse_grants(
            before_text)
        after, after_rules, after_includes, after_skipped = parse_grants(
            after_text)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2
    for path, includes, skipped in ((args.before, before_includes, before_skipped),
                                    (args.after, after_includes, after_skipped)):
        if includes:
            print("NOTE %s: %d include directive(s) not followed"
                  % (path, len(includes)), file=sys.stderr)
        if skipped:
            print("NOTE %s: %d line(s) not understood and skipped"
                  % (path, skipped), file=sys.stderr)
    if not before_rules or not after_rules:
        print("ERROR no sudoers rules found in %s"
              % (args.before if not before_rules else args.after),
              file=sys.stderr)
        return 2

    widenings, removed, narrowed = compare(before, after)
    if args.json:
        print(json.dumps([{"kind": kind, "user": user, "detail": detail}
                          for kind, user, detail in widenings], indent=2))
        return 1 if widenings else 0
    for kind, user, detail in widenings:
        print("%-8s %s %s" % (kind, user, detail))
    for user in removed:
        print("REMOVED  %s" % user)
    if widenings:
        print("FINDING %d widening(s) in %s" % (len(widenings), args.after))
        return 1
    print("OK no widening (%d user(s) removed, %d command(s) narrowed)"
          % (len(removed), narrowed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
