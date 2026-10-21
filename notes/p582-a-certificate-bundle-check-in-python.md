---
id: p582
title: "A certificate bundle check in Python"
slug: a-certificate-bundle-check-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, TLS, DevSecOps, CyberSecurity, SRE]
source: "LinkedIn post P582 · PythonFixes series"
linkedin_date: 2030-06-16
design: code
script: cert_bundle_check.py
---

# A certificate bundle check in Python

The leaf certificate had a year left. The bundle still failed on Friday, because the intermediate above it had expired in January.

## Quick reference

The full script is at the end of this note: `cert_bundle_check.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 cert_bundle_check.py /tmp/fullchain.pem
```

**Example output**

```text
OK api.example.com 2027-10-20
EXPIRED Example Intermediate CA 2026-01-01
```

## Explained

### What it does

It reads every CERTIFICATE block in a PEM bundle, decodes the DER, and prints the subject and expiry of each one. The visible lines print OK api.example.com 2027-10-20 and EXPIRED Example Intermediate CA 2026-01-01. The full script adds the chain order and, with `--key`, an ssl check that the key matches the leaf. Exit 1 is expiry, order or a mismatch; 2 is unreadable input.

### How to run it

`python3 cert_bundle_check.py fullchain.pem --key tls.key`. Add `--warn-days 21` to fail three weeks early. CI runs it before the deploy; cron runs it weekly against the file the ingress mounts, not a repository copy.

### The fix

Replace the expired intermediate, order the file leaf first, then intermediate, then root, and deploy the full chain. Re-run until it prints OK. If the key does not match, find the certificate that belongs to the key before you touch DNS.

### Prevention

Build the bundle in the pipeline and check it there, so what reaches production is what passed. Keep the expiry warning in the deploy job; a calendar reminder is not a check.

> **The honest caveat:** it checks dates and order, not signatures. A forged bundle with the right names passes, so use openssl verify when trust matters.

> **The lesson:** a certificate is valid only inside the bundle that carries it.

## In one line

> **A valid leaf does not save a bundle.** The date is one check; the chain and the key are the other three.

**Check the dates**

```bash
python3 cert_bundle_check.py fullchain.pem
```

## Script: cert_bundle_check.py

Download: [scripts/cert_bundle_check.py](../scripts/cert_bundle_check.py)

```python
#!/usr/bin/env python3
"""cert_bundle_check.py - check a PEM certificate bundle before you deploy it.

Reads every CERTIFICATE block in a PEM bundle, decodes the DER with base64
and the standard library, and reports each certificate's subject, expiry and
position in the chain. With --key it asks ssl to load the bundle and the key
together, which proves the private key matches the leaf.

A bundle that deploys cleanly can still fail in a browser: the leaf may be
expired, the chain may be out of order, or the key may belong to another
certificate. This script answers those three questions with an exit code.

Usage:
    python3 cert_bundle_check.py fullchain.pem
    python3 cert_bundle_check.py fullchain.pem --key tls.key
    python3 cert_bundle_check.py fullchain.pem --warn-days 21
    cat fullchain.pem | python3 cert_bundle_check.py -
    python3 cert_bundle_check.py --help

CI (stop a deploy of an expired or misordered bundle):
    python3 cert_bundle_check.py fullchain.pem --key tls.key || exit 1

Cron (weekly, with three weeks of warning):
    0 7 * * 1 python3 /opt/s0sta/cert_bundle_check.py /etc/tls/fullchain.pem --warn-days 21

Exit codes: 0 clean, 1 expired, inside --warn-days, out of order or a key
mismatch, 2 usage error or unreadable, empty or invalid input.

Read-only: both files are opened for reading. Nothing is written, no service
is reloaded and no network call is made. A certificate is not a secret and no
key material is printed, only whether the key matches the leaf.

It checks dates and order, not signatures: it does not build a trust path to
a system store, so a forged bundle with the right names passes. Use openssl
verify for trust and this script for the deploy-time facts.

By s0sta.com
"""
import argparse
import base64
import binascii
import re
import ssl
import sys
from datetime import datetime, timedelta, timezone

PEM = re.compile(
    r"-----BEGIN CERTIFICATE-----\s*(.*?)\s*-----END CERTIFICATE-----",
    re.S,
)
LABELS = {
    "2.5.4.3": "CN",
    "2.5.4.5": "serialNumber",
    "2.5.4.6": "C",
    "2.5.4.7": "L",
    "2.5.4.8": "ST",
    "2.5.4.10": "O",
    "2.5.4.11": "OU",
    "1.2.840.113549.1.9.1": "emailAddress",
}
STRINGS = {
    0x0C: "utf-8",       # UTF8String
    0x13: "ascii",       # PrintableString
    0x14: "latin-1",     # TeletexString
    0x16: "ascii",       # IA5String
    0x1E: "utf-16-be",   # BMPString
}


class InputError(Exception):
    """An input that cannot be audited."""


def tlv(data, pos):
    """Read one DER tag-length-value; return (tag, value, next position)."""
    if pos + 2 > len(data):
        raise InputError("truncated DER")
    tag = data[pos]
    size = data[pos + 1]
    pos += 2
    if size & 0x80:
        count = size & 0x7F
        if not 1 <= count <= 4 or pos + count > len(data):
            raise InputError("bad DER length")
        size = int.from_bytes(data[pos:pos + count], "big")
        pos += count
    end = pos + size
    if end > len(data):
        raise InputError("truncated DER value")
    return tag, data[pos:end], end


def children(data):
    """Yield (tag, value) for each DER value inside data."""
    pos = 0
    while pos < len(data):
        tag, value, pos = tlv(data, pos)
        yield tag, value


def decode_oid(raw):
    """Turn DER OID bytes into dotted form."""
    if not raw:
        raise InputError("empty OID")
    parts = [raw[0] // 40, raw[0] % 40]
    value = 0
    for byte in raw[1:]:
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            parts.append(value)
            value = 0
    if value:
        raise InputError("truncated OID")
    return ".".join(str(part) for part in parts)


def decode_string(tag, raw):
    """Decode the string types that appear in an X.509 name."""
    if tag not in STRINGS:
        raise InputError("unsupported name string")
    try:
        return raw.decode(STRINGS[tag])
    except UnicodeDecodeError:
        raise InputError("undecodable name")


def read_name(der):
    """Return an X.501 name as [(label, value), ...]."""
    parts = []
    for tag, rdn in children(der):
        if tag != 0x31:
            raise InputError("bad name: expected a set")
        for atag, attribute in children(rdn):
            if atag != 0x30:
                raise InputError("bad name: expected a sequence")
            items = list(children(attribute))
            if len(items) < 2:
                raise InputError("bad name attribute")
            oid = decode_oid(items[0][1])
            parts.append((LABELS.get(oid, oid),
                          decode_string(items[1][0], items[1][1])))
    if not parts:
        raise InputError("empty name")
    return parts


def read_time(tag, raw):
    """Parse a UTCTime or GeneralizedTime into an aware UTC datetime."""
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        raise InputError("undecodable time")
    zone = "+0000"
    if text.endswith("Z"):
        text = text[:-1]
    elif len(text) > 5 and text[-5] in "+-":
        zone = text[-5:]
        text = text[:-5]
    if not text.isdigit():
        raise InputError("bad time")
    if tag == 0x17:
        if len(text) == 10:
            text += "00"
        if len(text) != 12:
            raise InputError("bad UTCTime")
        year = int(text[:2])
        text = str(year + (2000 if year < 50 else 1900)) + text[2:]
    elif tag == 0x18:
        if len(text) == 12:
            text += "00"
        if len(text) != 14:
            raise InputError("bad GeneralizedTime")
    else:
        raise InputError("bad time tag")
    try:
        value = datetime(
            int(text[0:4]), int(text[4:6]), int(text[6:8]),
            int(text[8:10]), int(text[10:12]), int(text[12:14]),
            tzinfo=timezone.utc,
        )
    except ValueError:
        raise InputError("bad time value")
    if zone != "+0000":
        sign = 1 if zone[0] == "+" else -1
        value -= sign * timedelta(
            hours=int(zone[1:3]), minutes=int(zone[3:5]))
    return value


def read_cert(der):
    """Return subject, issuer and validity for one DER certificate."""
    tag, outer, end = tlv(der, 0)
    if tag != 0x30 or end != len(der):
        raise InputError("not a DER certificate")
    blocks = list(children(outer))
    if len(blocks) != 3 or blocks[0][0] != 0x30:
        raise InputError("not a certificate sequence")
    fields = list(children(blocks[0][1]))
    start = 1 if fields and fields[0][0] == 0xA0 else 0
    if len(fields) < start + 6:
        raise InputError("truncated certificate")
    wanted = (0x02, 0x30, 0x30, 0x30, 0x30, 0x30)
    for offset, expected in enumerate(wanted):
        if fields[start + offset][0] != expected:
            raise InputError("unexpected certificate field")
    validity = list(children(fields[start + 3][1]))
    if len(validity) != 2:
        raise InputError("bad validity")
    return {
        "issuer": read_name(fields[start + 2][1]),
        "not_before": read_time(validity[0][0], validity[0][1]),
        "not_after": read_time(validity[1][0], validity[1][1]),
        "subject": read_name(fields[start + 4][1]),
    }


def canon(name):
    """Normalise a name for issuer/subject comparison."""
    return tuple((label, " ".join(value.lower().split()))
                 for label, value in name)


def show(name):
    """Return CN=... for a name, or the first attribute when there is no CN."""
    for label, value in name:
        if label == "CN":
            return "CN=%s" % value
    label, value = name[0]
    return "%s=%s" % (label, value)


def read_bundle(path):
    """Return parsed certificates from a PEM file or stdin."""
    try:
        if path == "-":
            text = sys.stdin.read()
        else:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except UnicodeDecodeError:
        raise InputError("%s: not text" % path)
    if not text.strip():
        raise InputError("%s: empty input" % path)
    blocks = PEM.findall(text)
    if not blocks:
        raise InputError("%s: no CERTIFICATE block found" % path)
    certs = []
    for number, body in enumerate(blocks, start=1):
        try:
            der = base64.b64decode("".join(body.split()), validate=True)
        except (binascii.Error, ValueError):
            raise InputError("certificate %d: invalid base64" % number)
        try:
            certs.append(read_cert(der))
        except InputError as exc:
            raise InputError("certificate %d: %s" % (number, exc))
    return certs


def parse_now(text):
    """Parse --now; a naive value is treated as UTC."""
    raw = text.strip()
    if raw.endswith(("Z", "z")):
        raw = raw[:-1] + "+00:00"
    try:
        value = datetime.fromisoformat(raw)
    except ValueError:
        raise InputError("--now is not ISO 8601: %r" % text)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def check_key(bundle, key):
    """Return (matches, reason) for a bundle and key, using ssl."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        context.load_cert_chain(certfile=bundle, keyfile=key)
    except ssl.SSLError as exc:
        reason = getattr(exc, "reason", "") or str(exc)
        if reason == "KEY_VALUES_MISMATCH":
            return False, "key values mismatch"
        raise InputError("cannot load the key: %s" % reason)
    except OSError as exc:
        raise InputError("cannot load the key: %s" % (exc.strerror or exc))
    return True, ""


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check a PEM certificate bundle (read-only).")
    parser.add_argument("bundle", nargs="?", default="-",
                        help="PEM bundle file; stdin when omitted")
    parser.add_argument("--key", help="private key file to match to the leaf")
    parser.add_argument("--warn-days", type=int, default=0,
                        help="also fail when a certificate expires inside N days")
    parser.add_argument("--now", help="ISO 8601 reference time (for testing)")
    args = parser.parse_args(argv)
    if args.warn_days < 0:
        parser.error("--warn-days must not be negative")
    if args.bundle == "-" and args.key:
        parser.error("--key needs the bundle as a file, not stdin")

    try:
        now = parse_now(args.now) if args.now else datetime.now(timezone.utc)
        certs = read_bundle(args.bundle)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    findings = []
    for number, cert in enumerate(certs, start=1):
        subject = show(cert["subject"])
        if cert["not_after"] <= now:
            days = (now - cert["not_after"]).days
            findings.append("cert %d expired" % number)
            state = "EXPIRED %s (%d days ago)" % (cert["not_after"].date(), days)
        elif cert["not_before"] > now:
            findings.append("cert %d not yet valid" % number)
            state = "NOT YET VALID %s" % cert["not_before"].date()
        else:
            days = (cert["not_after"] - now).days
            if args.warn_days and days < args.warn_days:
                findings.append("cert %d expires in %d days" % (number, days))
                state = "EXPIRING %s (%d days)" % (cert["not_after"].date(), days)
            else:
                state = "expires %s (%d days)" % (cert["not_after"].date(), days)
        print("CERT %d %s %s" % (number, subject, state))

    for number in range(len(certs) - 1):
        below = certs[number]
        above = certs[number + 1]
        if canon(below["issuer"]) != canon(above["subject"]):
            findings.append("order %d/%d" % (number + 1, number + 2))
            print("ORDER cert %d issuer %s does not match cert %d subject %s"
                  % (number + 1, show(below["issuer"]),
                     number + 2, show(above["subject"])))
    if len(certs) > 1:
        names = " -> ".join(show(cert["subject"]) for cert in certs)
        ordered = not any(item.startswith("order ") for item in findings)
        print("ORDER %s%s" % ("" if ordered else "CHECK ", names))
    if canon(certs[-1]["subject"]) != canon(certs[-1]["issuer"]):
        print("NOTE %s is not self-signed; a root may be missing"
              % show(certs[-1]["subject"]))

    key_state = "not checked"
    if args.key:
        try:
            matches, reason = check_key(args.bundle, args.key)
        except InputError as exc:
            print("ERROR %s" % exc, file=sys.stderr)
            return 2
        if matches:
            key_state = "matches the leaf"
            print("KEY matches the leaf certificate")
        else:
            key_state = "does not match"
            findings.append("key mismatch")
            print("KEY does not match the leaf certificate (%s)" % reason)

    if findings:
        print("FINDING %d: %s" % (len(findings), ", ".join(findings)))
        return 1
    print("OK %d certificate(s), order fine, key %s"
          % (len(certs), key_state))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
