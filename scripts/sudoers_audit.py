#!/usr/bin/env python3
"""sudoers_audit.py - audit a sudoers file for over-broad grants.

Reads one sudoers file and reports grants that turn delegated work into
full administrative access: any NOPASSWD tag, an ALL=(ALL) ALL rule, a
wildcard command path, a blanket command set, and every user or group
that can run all commands.

Usage:
    python3 sudoers_audit.py
    python3 sudoers_audit.py /etc/sudoers
    python3 sudoers_audit.py --help

CI (fail the build when a role grants full sudo):
    python3 sudoers_audit.py /etc/sudoers.d/deploy || exit 1

Cron (weekly check of the managed sudoers tree):
    30 6 * * 1 python3 /opt/s0sta/sudoers_audit.py /etc/sudoers

Exit codes: 0 no findings, 1 at least one finding, 2 usage error or
unreadable, empty or rule-free input.

Read-only: the file is opened for reading. Nothing is written, no user
or group is changed and no command is executed. Reports name users and
command paths, never a command argument, so a password passed on a
command line is not echoed.

This is a line parser, not visudo. User_Alias, Runas_Alias and
Cmnd_Alias definitions are expanded, but #include and #includedir
directives are reported on stderr and not followed: audit each included
file directly. A comma inside a command argument must be escaped, as
sudoers itself requires. Run visudo -c for syntax, then this script for
exposure.

By s0sta.com
"""
import argparse
import re
import sys

DEFAULT_PATH = "/etc/sudoers"

ALIAS = re.compile(
    r"^(User_Alias|Runas_Alias|Cmnd_Alias)\s+"
    r"([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.+)$",
    re.IGNORECASE,
)
INCLUDE = re.compile(r"^[#@]include(dir)?\s+(\S+)", re.IGNORECASE)
RUNAS = re.compile(r"^\(([^)]*)\)\s*(.*)$")
TAG = re.compile(
    r"\b(?:NOPASSWD|PASSWD|NOEXEC|EXEC|SETENV|NOSETENV|LOG_INPUT|NOLOG_INPUT|"
    r"LOG_OUTPUT|NOLOG_OUTPUT|MAIL|NOMAIL|FOLLOW|NOFOLLOW)\s*:\s*",
    re.IGNORECASE,
)
NOPASSWD = re.compile(r"\bNOPASSWD\s*:", re.IGNORECASE)


class InputError(Exception):
    """An input file that cannot be audited."""


def read_text(path):
    """Return the sudoers text, or raise InputError."""
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
    """Yield (line number, joined line) for one logical line."""
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
    """Remove a # comment, but keep include directives intact."""
    stripped = line.strip()
    if INCLUDE.match(stripped):
        return stripped
    if stripped.startswith(("#", "@")):
        return ""
    return stripped.split("#", 1)[0].strip()


def split_escaped(text, separator=","):
    """Split on a separator that is not backslash-escaped."""
    parts = []
    current = ""
    escaped = False
    for char in text:
        if escaped:
            current += char
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == separator:
            parts.append(current)
            current = ""
        else:
            current += char
    parts.append(current)
    return [part.strip() for part in parts if part.strip()]


def expand(items, aliases, seen=None):
    """Expand aliases in a list, keeping any ! negation prefix."""
    seen = set() if seen is None else set(seen)
    out = []
    for item in items:
        raw = item.strip()
        if not raw:
            continue
        negated = raw.startswith("!")
        name = raw[1:].strip() if negated else raw
        if name in aliases and name not in seen:
            inner = expand(aliases[name], aliases, seen | {name})
        else:
            inner = [name]
        for value in inner:
            out.append(("!" if negated else "") + value)
    return out


def parse_aliases(lines):
    """Return (user aliases, runas aliases, command aliases, includes)."""
    users = {}
    runas = {}
    commands = {}
    includes = []
    for _number, raw in lines:
        line = strip_comment(raw)
        if not line or line.lower().startswith("defaults"):
            continue
        if INCLUDE.match(line):
            includes.append(line)
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


def parse_spec(line):
    """Return (users, runas, commands) for one user spec."""
    if "=" not in line:
        return None
    left, right = line.split("=", 1)
    parts = left.strip().split()
    if not parts:
        return None
    user_chunks = [parts[0]]
    index = 1
    while user_chunks[-1].endswith(",") and index < len(parts):
        user_chunks.append(parts[index])
        index += 1
    user_items = []
    for chunk in user_chunks:
        user_items.extend(split_escaped(chunk))
    if not user_items:
        return None

    body = right.strip()
    runas_items = ["root"]
    found = RUNAS.match(body)
    if found:
        runas_items = split_escaped(found.group(1).replace(":", ","))
        body = found.group(2).strip()
    body = TAG.sub("", body)
    commands = split_escaped(body)
    return user_items, runas_items, commands


def flatten_commands(commands, aliases, seen=None):
    """Expand Cmnd_Alias names into their command lists."""
    seen = set() if seen is None else set(seen)
    out = []
    for item in commands:
        raw = item.strip()
        name = raw[1:].strip() if raw.startswith("!") else raw
        if name in aliases and name not in seen:
            expanded = flatten_commands(aliases[name], aliases, seen | {name})
            if raw.startswith("!"):
                expanded = ["!" + value for value in expanded]
            out.extend(expanded)
        else:
            out.append(raw)
    return out


def audit(text):
    """Return a list of (kind, message) findings for one sudoers file."""
    lines = list(logical_lines(text))
    user_alias, runas_alias, cmd_alias, includes = parse_aliases(lines)
    findings = []
    full_users = set()
    specs = 0
    skipped = 0

    for number, raw in lines:
        line = strip_comment(raw)
        if (
            not line
            or INCLUDE.match(line)
            or ALIAS.match(line)
            or line.lower().startswith("defaults")
        ):
            continue
        parsed = parse_spec(line)
        if parsed is None:
            skipped += 1
            continue
        specs += 1
        user_items, runas_items, command_items = parsed
        users = expand(user_items, user_alias)
        runas = expand(runas_items, runas_alias)
        commands = flatten_commands(command_items, cmd_alias)
        positive = [value for value in users if not value.startswith("!")]
        if not positive:
            continue
        shown_users = ", ".join(positive)

        if NOPASSWD.search(raw):
            findings.append(
                ("SUDO", "line %d: NOPASSWD for %s" % (number, shown_users)))

        command_paths = []
        any_all = False
        for command in commands:
            raw_command = command.strip()
            negated = raw_command.startswith("!")
            clean = raw_command[1:].strip() if negated else raw_command
            path = clean.split()[0] if clean.split() else ""
            if path == "ALL" and not negated:
                any_all = True
            if path:
                command_paths.append((path, negated))

        runas_all = "ALL" in [value.lstrip("!") for value in runas]
        exact = (
            any_all
            and runas_all
            and len(command_paths) == 1
            and not command_paths[0][1]
        )
        if exact:
            findings.append(
                ("SUDO",
                 "line %d: ALL=(ALL) ALL for %s" % (number, shown_users)))
        elif any_all:
            findings.append(
                ("SUDO", "line %d: full command set ALL for %s"
                 % (number, shown_users)))

        for path, negated in command_paths:
            if (
                not negated
                and path.startswith("/")
                and ("*" in path or "?" in path)
            ):
                findings.append(
                    ("SUDO", "line %d: wildcard path %s for %s"
                     % (number, path, shown_users)))

        if any_all:
            full_users.update(positive)

    if full_users:
        findings.append(
            ("FULL", "users with full sudo: "
             + ", ".join(sorted(full_users))))
    return findings, specs, skipped, includes


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit a sudoers file for over-broad grants (read-only).")
    parser.add_argument(
        "sudoers", nargs="?", default=DEFAULT_PATH,
        help="sudoers file to audit (default: %s)" % DEFAULT_PATH)
    args = parser.parse_args(argv)

    try:
        text = read_text(args.sudoers)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    findings, specs, skipped, includes = audit(text)
    if includes:
        print(
            "NOTE %d include directive(s) not followed; "
            "audit each file directly" % len(includes),
            file=sys.stderr,
        )
    if skipped:
        print("NOTE %d line(s) not understood and skipped" % skipped,
              file=sys.stderr)
    if not specs:
        if includes:
            print("ERROR no rules in %s: only includes found" % args.sudoers,
                  file=sys.stderr)
            return 2
        print("ERROR no sudoers rules found in %s" % args.sudoers,
              file=sys.stderr)
        return 2

    if findings:
        for kind, message in findings:
            print("%-5s %s" % (kind, message))
        print("FINDING %d finding(s) in %s" % (len(findings), args.sudoers))
        return 1
    print("OK no findings in %s" % args.sudoers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
