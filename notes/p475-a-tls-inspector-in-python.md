---
id: p475
title: "A TLS inspector in Python"
slug: a-tls-inspector-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [TLS, Security, Python, Networking, DevOps]
source: "LinkedIn post P475 · Network series"
linkedin_date: 2029-10-09
design: code
script: tls_inspect.py
---

# A TLS inspector in Python

A certificate expires on a Sunday and the first person to notice is a customer. Checking one host takes a handshake, and the facts are all in the certificate the server already sends.

## Quick reference

The full script is at the end of this note: `tls_inspect.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 tls_inspect.py example.com --port 443
```

**Example output**

```text
TLSv1.3 TLS_AES_256_GCM_SHA384
days 212 SANs example.com, www.example.com
```

## Explained

### What it prints

The script connects, negotiates TLS, and prints the protocol version, the cipher, the subject, the DNS names in the SAN extension, and the days left before notAfter. Those are the five things a support ticket usually needs.

### What it flags

Two checks make it exit 1. A certificate with fewer than 30 days left is expiring, because renewal queues and approval windows are longer than people remember. A hostname that matches none of the SAN entries is a mismatch, which is what a browser turns into a full-page warning. Wildcards match one label only: \*.example.com covers api.example.com, not a.b.example.com.

### How to run it

`python3 tls_inspect.py example.com`, or the host and `--port` for a non-standard listener. Add `--days 14` to tighten the expiry threshold, and `--cafile` for a private CA. Exit 0 means clean, 1 means a finding, 2 means the name, the port or the connection failed. The full script is attached: standard library only, one handshake, no writes.

> **The honest caveat:** the script checks the certificate the server presents now. It cannot see the renewal job that will run next week, so put it in cron and let it page before the customer does.

> **The lesson:** expiry is a date you can test, so test it.

## In one line

> **Trust is a date, not a feeling.** A certificate is a fact with an expiry attached.

**Check one host**

```bash
python3 tls_inspect.py example.com
```

## Script: tls_inspect.py

Download: [scripts/tls_inspect.py](../scripts/tls_inspect.py)

```python
#!/usr/bin/env python3
"""Inspect the TLS certificate served by one host.

    python3 tls_inspect.py example.com
    python3 tls_inspect.py 127.0.0.1 --port 8443 --cafile /tmp/test-ca.pem
    python3 tls_inspect.py example.com --days 14

Prints the protocol, cipher, subject, SANs and days to expiry. Exits 1
when the certificate expires within --days, does not match the hostname,
or fails verification; 0 when clean; 2 on a usage or connection error.
One handshake; nothing is written.

Cron/CI: python3 tls_inspect.py "$HOST" --days 21 || exit 1
By s0sta.com
"""
import argparse
import ipaddress
import socket
import ssl
import sys
import time

NAMES = {
    "commonName": "CN",
    "organizationName": "O",
    "organizationalUnitName": "OU",
    "countryName": "C",
    "stateOrProvinceName": "ST",
    "localityName": "L",
}


def format_subject(cert):
    """Turn the subject tuple into CN=..., O=... form."""
    parts = []
    for rdn in cert.get("subject", ()):
        for key, value in rdn:
            parts.append("%s=%s" % (NAMES.get(key, key), value))
    return ", ".join(parts) or "(none)"


def dns_match(host, names):
    """Match a hostname against SAN DNS names, one wildcard label only."""
    host = host.lower().rstrip(".")
    for raw in names:
        name = raw.lower().rstrip(".")
        if name == host:
            return True
        if name.startswith("*."):
            suffix = name[2:]
            if host.count(".") == suffix.count(".") + 1 and host.endswith("." + suffix):
                return True
    return False


def ip_match(host, names):
    """Match an IP address against SAN IP entries."""
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    for value in names:
        try:
            if ipaddress.ip_address(value) == address:
                return True
        except ValueError:
            continue
    return False


def host_matches(host, sans):
    """Check a hostname or IP against the certificate's SAN entries."""
    dns = [value for kind, value in sans if kind == "DNS"]
    ips = [value for kind, value in sans if kind == "IP Address"]
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return dns_match(host, dns)
    return ip_match(host, ips)


def inspect(host, port, sni, timeout, cafile):
    """Connect once and return the certificate facts."""
    raw = socket.create_connection((host, port), timeout)
    try:
        context = ssl.create_default_context()
        if cafile:
            try:
                context.load_verify_locations(cafile=cafile)
            except OSError as exc:
                raise ValueError("cannot load CA file: %s" % exc)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
        sock = context.wrap_socket(raw, server_hostname=sni)
    except Exception:
        raw.close()
        raise
    try:
        cert = sock.getpeercert()
        version = sock.version() or "?"
        cipher = sock.cipher() or ("?", None, None)
    finally:
        sock.close()
    if not cert:
        raise ValueError("the server presented no certificate")
    not_after = cert.get("notAfter")
    if not not_after:
        raise ValueError("the certificate has no notAfter field")
    expiry = ssl.cert_time_to_seconds(not_after)
    days = (expiry - time.time()) / 86400
    sans = cert.get("subjectAltName", ())
    return {
        "version": version,
        "cipher": cipher[0],
        "bits": cipher[2] if cipher[2] is not None else "?",
        "subject": format_subject(cert),
        "sans": sans,
        "expiry": time.strftime("%Y-%m-%d", time.gmtime(expiry)),
        "days": days,
        "match": host_matches(sni, sans),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inspect one host's TLS certificate and expiry.")
    parser.add_argument("host", help="hostname or IP address to inspect")
    parser.add_argument("--port", type=int, default=443,
                        help="TCP port (default: 443)")
    parser.add_argument("--sni", default=None,
                        help="hostname for SNI and matching (default: host)")
    parser.add_argument("--days", type=float, default=30.0,
                        help="expiry warning threshold in days (default: 30)")
    parser.add_argument("--timeout", type=float, default=10.0,
                        help="connect and handshake timeout (default: 10)")
    parser.add_argument("--cafile", default=None,
                        help="CA bundle to trust instead of the system store")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if args.days < 0:
        parser.error("--days must not be negative")
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    check_name = args.sni or args.host
    try:
        info = inspect(args.host, args.port, check_name, args.timeout, args.cafile)
    except ssl.SSLCertVerificationError as exc:
        reason = getattr(exc, "verify_message", str(exc))
        print("FINDING certificate verify failed: %s" % reason)
        return 1
    except ValueError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2
    except ssl.SSLError as exc:
        print("ERROR TLS handshake failed: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    sans = info["sans"]
    shown = ", ".join(value for _, value in sans) or "(none)"
    print("host      %s:%d" % (args.host, args.port))
    print("protocol  %s" % info["version"])
    print("cipher    %s (%s bits)" % (info["cipher"], info["bits"]))
    print("subject   %s" % info["subject"])
    print("SANs      %s" % shown)
    print("expires   %s (%.1f days)" % (info["expiry"], info["days"]))

    findings = []
    if info["days"] < 0:
        findings.append("EXPIRED %.1f days ago" % -info["days"])
    elif info["days"] < args.days:
        findings.append(
            "EXPIRING %.1f days left (threshold %.0f)"
            % (info["days"], args.days))
    if not info["match"]:
        findings.append("MISMATCH %s not in the SANs" % check_name)
    if findings:
        for finding in findings:
            print("FINDING   %s" % finding)
        return 1
    print("OK        no findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
