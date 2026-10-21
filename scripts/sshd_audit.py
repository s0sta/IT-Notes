#!/usr/bin/env python3
"""sshd_audit.py - audit an OpenSSH server configuration for weak settings.

Reads one sshd_config and reports the settings that widen the attack
surface: root login, password authentication, empty passwords, weak
Ciphers, MACs or key-exchange algorithms, and any non-default Port with
no firewall note in the file.

Usage:
    python3 sshd_audit.py
    python3 sshd_audit.py /etc/ssh/sshd_config
    python3 sshd_audit.py /tmp/sshd_config --allow-port 2222
    python3 sshd_audit.py --help

CI (fail the job when the host template is weak):
    python3 sshd_audit.py /etc/ssh/sshd_config || exit 1

Cron (weekly drift check):
    0 6 * * 1 python3 /opt/s0sta/sshd_audit.py /etc/ssh/sshd_config

Exit codes: 0 no findings, 1 at least one finding, 2 usage error or
unreadable, empty or directive-free input.

Read-only: the file is opened for reading. Nothing is written, no
service is reloaded and no network connection is made.

The first value of a keyword wins, as sshd_config documents. Directives
inside a Match block are conditional and are not scored; the script
reports how many conditional blocks it skipped on stderr. A non-default
port is treated as documented only when a comment names both the port
and a firewall, ufw, iptables, nftables, a security group or an
allowlist. Include directives are not followed: pass the merged file.

By s0sta.com
"""
import argparse
import re
import sys

DEFAULT_PATH = "/etc/ssh/sshd_config"

NAME = {
    "permitrootlogin": "PermitRootLogin",
    "passwordauthentication": "PasswordAuthentication",
    "permitemptypasswords": "PermitEmptyPasswords",
    "ciphers": "Ciphers",
    "macs": "MACs",
    "kexalgorithms": "KexAlgorithms",
}
CHECK_ORDER = (
    "permitrootlogin",
    "passwordauthentication",
    "permitemptypasswords",
    "ciphers",
    "macs",
    "kexalgorithms",
)

WEAK_CIPHERS = {
    "3des-cbc",
    "aes128-cbc",
    "aes192-cbc",
    "aes256-cbc",
    "blowfish-cbc",
    "cast128-cbc",
    "rijndael-cbc@lysator.liu.se",
}
WEAK_MACS = {
    "hmac-md5",
    "hmac-md5-96",
    "hmac-sha1",
    "hmac-sha1-96",
    "hmac-ripemd160",
    "umac-64@openssh.com",
}
WEAK_KEX = {
    "diffie-hellman-group1-sha1",
    "diffie-hellman-group14-sha1",
    "diffie-hellman-group-exchange-sha1",
}

FIREWALL = re.compile(
    r"\b(firewall|ufw|iptables|nftables|security group|allowlist|"
    r"allow list)\b",
    re.IGNORECASE,
)
DIRECTIVE = re.compile(r"^([A-Za-z][A-Za-z0-9]*)\s*(?:=\s*|\s+)(.+)$")


class InputError(Exception):
    """An input file that cannot be audited."""


def read_text(path):
    """Return the configuration text, or raise InputError."""
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


def parse(text):
    """Return first values, Port values, comments and skipped Match blocks."""
    first = {}
    ports = []
    comments = []
    matches = 0
    in_match = False
    for number, raw in enumerate(text.splitlines(), start=1):
        if "#" in raw:
            comments.append(raw.split("#", 1)[1])
        body = raw.split("#", 1)[0].strip()
        if not body:
            continue
        found = DIRECTIVE.match(body)
        if not found:
            continue
        key = found.group(1).lower()
        value = found.group(2).strip()
        if key == "match":
            in_match = True
            matches += 1
            continue
        if in_match:
            continue
        if key == "port":
            for token in value.split():
                try:
                    ports.append(int(token))
                except ValueError:
                    continue
            continue
        # sshd_config uses the first obtained value for every keyword.
        first.setdefault(key, (value, number))
    if not first and not ports:
        raise InputError("no directives found")
    return first, ports, " ".join(comments), matches


def list_tokens(value):
    """Split a comma list and drop an append or prepend marker."""
    value = value.strip()
    if value.startswith("-"):
        return []
    if value[:1] in ("+", "^"):
        value = value[1:]
    return [
        token.strip().lower()
        for token in value.split(",")
        if token.strip()
    ]


def weak_ciphers(value):
    """Return the weak cipher names enabled by one Ciphers line."""
    return [
        token
        for token in list_tokens(value)
        if (
            token in WEAK_CIPHERS
            or token.endswith("-cbc")
            or token.startswith("arcfour")
        )
    ]


def weak_macs(value):
    """Return the weak MAC names enabled by one MACs line."""
    return [
        token
        for token in list_tokens(value)
        if token in WEAK_MACS
        or token.startswith("hmac-md5")
        or token.startswith("hmac-sha1")
        or token.startswith("umac-64")
    ]


def weak_kex(value):
    """Return the weak key-exchange names enabled by one KexAlgorithms line."""
    return [
        token
        for token in list_tokens(value)
        if token in WEAK_KEX
        or token.startswith("diffie-hellman-group1")
        or token.startswith("diffie-hellman-group14-sha1")
        or token.startswith("gss-group1-sha1")
        or token.startswith("gss-gex-sha1")
    ]


def audit(first, ports, comments, allow_ports):
    """Return a list of (kind, message) findings."""
    findings = []
    for key in CHECK_ORDER:
        if key not in first:
            continue
        value, line = first[key]
        if key in (
            "permitrootlogin",
            "passwordauthentication",
            "permitemptypasswords",
        ):
            if value.strip().lower() == "yes":
                findings.append(
                    ("WEAK", "%s yes (line %d)" % (NAME[key], line)))
            continue
        check = {
            "ciphers": weak_ciphers,
            "macs": weak_macs,
            "kexalgorithms": weak_kex,
        }[key]
        for token in check(value):
            findings.append(
                ("WEAK", "%s %s (line %d)" % (NAME[key], token, line)))

    if not ports:
        ports = [22]
    for port in ports:
        if port == 22 or port in allow_ports:
            continue
        documented = FIREWALL.search(comments) and str(port) in comments
        if not documented:
            findings.append(("PORT", "Port %d has no firewall note" % port))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit one sshd_config for weak settings (read-only).")
    parser.add_argument(
        "config", nargs="?", default=DEFAULT_PATH,
        help="sshd_config to audit (default: %s)" % DEFAULT_PATH)
    parser.add_argument(
        "--allow-port", type=int, action="append", default=[], metavar="PORT",
        help="non-default port that is intentionally allowed (repeatable)")
    args = parser.parse_args(argv)

    for port in args.allow_port:
        if not 1 <= port <= 65535:
            parser.error("--allow-port must be between 1 and 65535")

    try:
        text = read_text(args.config)
        first, ports, comments, matches = parse(text)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    if matches:
        print(
            "NOTE %d Match block(s) skipped: conditional settings "
            "are not scored" % matches,
            file=sys.stderr,
        )

    findings = audit(first, ports, comments, set(args.allow_port))
    if findings:
        for kind, message in findings:
            print("%-5s %s" % (kind, message))
        print("FINDING %d finding(s) in %s" % (len(findings), args.config))
        return 1
    print("OK no findings in %s" % args.config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
