#!/usr/bin/env python3
"""Audit an SSH client configuration for weak settings and key hygiene.

Usage:
    python3 ssh_audit.py
    python3 ssh_audit.py --home /home/deploy
    python3 ssh_audit.py --home /tmp/ssh_fixture

Checks:
    - ~/.ssh, ~/.ssh/config and ~/.ssh/authorized_keys permissions
    - PasswordAuthentication yes and PermitRootLogin yes in the config
    - DSA (ssh-dss) and ssh-rsa keys in authorized_keys
    - authorized_keys entries with no comment, including bare keys that
      carry no options either

Exit codes:
    0  no findings
    1  at least one finding
    2  usage or input error

Run it weekly from cron, or as a CI step before a deploy:

    0 6 * * 1 python3 /opt/s0sta/ssh_audit.py --home /home/deploy

By s0sta.com
"""
import argparse
import os
import re
import sys

KEY_TYPES = (
    "ssh-ed25519",
    "ssh-rsa",
    "ssh-dss",
    "ecdsa-sha2-nistp256",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp521",
    "sk-ssh-ed25519@openssh.com",
    "sk-ecdsa-sha2-nistp256@openssh.com",
)
WEAK = ("ssh-rsa", "ssh-dss")
WEAK_PREFIXES = ("ssh-rsa-cert-", "ssh-dss-cert-")


def split_entry(raw):
    """Return (options, key_type, comment) for one authorized_keys line.

    OpenSSH allows a comma-separated options field, which may contain quoted
    strings and spaces, before the key type. Blank lines and comments return
    None. A malformed line returns whatever could be read.
    """
    line = raw.strip()
    if not line or line.startswith("#"):
        return None

    # Walk to the first unquoted space: that ends the first token.
    in_quote = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            in_quote = not in_quote
        elif ch == "\\" and in_quote:
            i += 1
        elif ch.isspace() and not in_quote:
            break
        i += 1
    first = line[:i]
    rest = line[i:].strip()

    if first in KEY_TYPES or first.startswith(("ssh-", "ecdsa-", "sk-")):
        options, key_type, tail = "", first, rest
    else:
        options = first
        parts = rest.split(None, 1)
        if not parts:
            return options, "", ""
        key_type = parts[0]
        tail = parts[1].strip() if len(parts) > 1 else ""

    # tail is "base64 [comment]"; the comment may contain spaces.
    parts = tail.split(None, 1)
    comment = parts[1].strip() if len(parts) > 1 else ""
    return options, key_type, comment


def check_mode(path, want, findings):
    try:
        mode = os.stat(path).st_mode & 0o777
    except OSError as exc:
        findings.append("{}: cannot stat ({})".format(path, exc.strerror))
        return
    if mode & 0o077:
        findings.append("{}: mode {:04o}, expected {:04o}".format(path, mode, want))


def audit(home):
    ssh = os.path.join(home, ".ssh")
    findings = []
    check_mode(ssh, 0o700, findings)

    cfg_path = os.path.join(ssh, "config")
    keys_path = os.path.join(ssh, "authorized_keys")

    if os.path.isfile(cfg_path):
        check_mode(cfg_path, 0o600, findings)
        with open(cfg_path, "r", errors="replace") as fh:
            for n, raw in enumerate(fh, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                parts = re.split(r"\s*=\s*|\s+", line, 1)
                if len(parts) != 2:
                    continue
                key = parts[0].lower()
                value = parts[1].split("#", 1)[0].strip().lower()
                if key == "passwordauthentication" and value in ("yes", "true"):
                    findings.append("config:{}: PasswordAuthentication yes".format(n))
                elif key == "permitrootlogin" and value in ("yes", "true"):
                    findings.append("config:{}: PermitRootLogin yes".format(n))

    if os.path.isfile(keys_path):
        check_mode(keys_path, 0o600, findings)
        with open(keys_path, "r", errors="replace") as fh:
            for n, raw in enumerate(fh, 1):
                entry = split_entry(raw)
                if entry is None:
                    continue
                options, key_type, comment = entry
                if not key_type:
                    findings.append("authorized_keys:{}: unreadable entry".format(n))
                    continue
                if key_type in WEAK or key_type.startswith(WEAK_PREFIXES):
                    findings.append(
                        "authorized_keys:{}: weak key type {}".format(n, key_type))
                if not comment:
                    if options:
                        findings.append(
                            "authorized_keys:{}: key has no comment".format(n))
                    else:
                        findings.append(
                            "authorized_keys:{}: no comment or options".format(n))

    return findings


def main():
    ap = argparse.ArgumentParser(
        description="Audit an SSH client configuration for weak settings and "
                    "key hygiene.")
    ap.add_argument("--home", default="~",
                    help="home directory to audit (default: ~)")
    args = ap.parse_args()

    home = os.path.abspath(os.path.expanduser(args.home))
    if not os.path.isdir(home):
        ap.error("not a directory: {}".format(home))
    ssh = os.path.join(home, ".ssh")
    if not os.path.isdir(ssh):
        ap.error("no .ssh directory under {}".format(home))
    if not (os.path.isfile(os.path.join(ssh, "config"))
            or os.path.isfile(os.path.join(ssh, "authorized_keys"))):
        ap.error("no config or authorized_keys under {}".format(ssh))

    try:
        findings = audit(home)
    except OSError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2
    for line in findings:
        print(line)
    if findings:
        print("{} finding(s) in {}".format(len(findings), ssh))
        return 1
    print("clean: {}".format(ssh))
    return 0


if __name__ == "__main__":
    sys.exit(main())
