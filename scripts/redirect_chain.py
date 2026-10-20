#!/usr/bin/env python3
"""redirect_chain.py - follow an HTTP redirect chain and audit the hops.

Opens a URL with urllib, records every redirect and its target, prints the
chain, then checks the hops, the http to https upgrade and the HSTS header.
A final 4xx or 5xx is also a finding, because a redirect that lands on an
error page is a slower error.

Exit codes: 0 clean, 1 finding, 2 usage or input error.

Usage:
    python3 redirect_chain.py http://github.com
    python3 redirect_chain.py http://example.com --max-hops 2
    python3 redirect_chain.py https://example.com --require-hsts
    python3 redirect_chain.py http://example.com --json

Cron or CI, fail when the chain is too long or never upgrades:
    python3 redirect_chain.py http://shop.example.com --max-hops 2 || exit 1

By s0sta.com
"""
import argparse
import http.client
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

REDIRECT_CODES = (301, 302, 303, 307, 308)
USER_AGENT = "s0sta-redirect-check/1.0"
HSTS = "Strict-Transport-Security"


class FetchError(Exception):
    """Anything that should end the run with exit code 2."""


class Recorder(urllib.request.HTTPRedirectHandler):
    """An opener handler that records each redirect before following it."""

    def __init__(self):
        super().__init__()
        self.hops = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.hops.append({"code": code, "from": req.full_url, "to": newurl})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def valid_url(text):
    """Only http and https, and only with a host."""
    parts = urllib.parse.urlsplit(text)
    return parts.scheme in ("http", "https") and bool(parts.netloc)


def fetch(start, timeout):
    """Follow the chain and return hops, the final URL, status and headers."""
    rec = Recorder()
    rec.max_redirections = 10
    opener = urllib.request.build_opener(rec)
    request = urllib.request.Request(start, headers={"User-Agent": USER_AGENT})
    try:
        resp = opener.open(request, timeout=timeout)
        return {"hops": rec.hops, "final": resp.geturl(),
                "status": resp.getcode(), "headers": resp.headers, "stuck": False}
    except urllib.error.HTTPError as exc:
        if exc.code in REDIRECT_CODES:
            final = rec.hops[-1]["to"] if rec.hops else start
            return {"hops": rec.hops, "final": final, "status": exc.code,
                    "headers": exc.headers, "stuck": True}
        return {"hops": rec.hops, "final": exc.geturl(), "status": exc.code,
                "headers": exc.headers, "stuck": False}
    except http.client.HTTPException as exc:
        raise FetchError("malformed HTTP response: %s" % exc)
    except OSError as exc:
        raise FetchError(str(exc))


def hsts_value(result):
    """HSTS only counts when the final response arrived over HTTPS."""
    final = result["final"] or ""
    if urllib.parse.urlsplit(final).scheme != "https":
        return None
    headers = result["headers"]
    value = headers.get(HSTS) if headers else None
    return value.strip() if value else None


def audit(start, result, max_hops, require_hsts):
    """Return (findings, warnings, hsts) for one fetched chain."""
    findings, warnings = [], []
    hops = len(result["hops"])
    if result["stuck"]:
        findings.append(
            "redirect not followed: loop, missing Location, or over 10 hops")
    if hops > max_hops:
        findings.append("%d hops exceeds --max-hops %d" % (hops, max_hops))

    start_scheme = urllib.parse.urlsplit(start).scheme
    final = result["final"] or start
    final_scheme = urllib.parse.urlsplit(final).scheme
    if start_scheme == "http" and final_scheme != "https":
        findings.append("no http -> https upgrade")
    if start_scheme == "https" and final_scheme == "http":
        findings.append("https downgraded to http")
    if final_scheme not in ("http", "https"):
        findings.append("redirect leaves HTTP: %s" % final)
    status = result["status"] or 0
    if status >= 400:
        findings.append("final status %d" % status)
    elif 300 <= status < 400 and not result["stuck"]:
        findings.append("final status %d is an unfollowed redirect" % status)

    hsts = hsts_value(result)
    if final_scheme == "https":
        if not hsts:
            if require_hsts:
                findings.append("HSTS required but missing")
            else:
                warnings.append("no Strict-Transport-Security header")
    return findings, warnings, hsts


def report(start, result, findings, warnings, hsts, max_hops, as_json):
    """Print the chain and the verdict, or one JSON object."""
    hops = result["hops"]
    start_scheme = urllib.parse.urlsplit(start).scheme
    final = result["final"] or ""
    final_scheme = urllib.parse.urlsplit(final).scheme
    if as_json:
        print(json.dumps({
            "start": start,
            "hops": hops,
            "final": result["final"],
            "status": result["status"],
            "upgraded": start_scheme == "http" and final_scheme == "https",
            "hsts": hsts,
            "findings": findings,
            "warnings": warnings,
            "ok": not findings,
        }, indent=2, sort_keys=True))
        return

    print("CHAIN %s  max %d hops" % (start, max_hops))
    for i, hop in enumerate(hops, 1):
        print("  %d  %d  %s -> %s" % (i, hop["code"], hop["from"], hop["to"]))
    if result["final"]:
        number = len(hops) + 1 if hops else 1
        print("  %d  %d  %s" % (number, result["status"], result["final"]))

    if start_scheme == "https":
        print("UPGRADE n/a  already https")
    elif final_scheme == "https":
        print("UPGRADE yes  http -> https")
    else:
        print("UPGRADE no  still http")
    if final_scheme == "https":
        print("HSTS %s" % (hsts or "missing"))
    for warning in warnings:
        print("WARN %s" % warning)
    for finding in findings:
        print("ALERT %s" % finding)

    if findings:
        print("ALERT %d finding(s), %d warning(s)" % (len(findings), len(warnings)))
        return
    if start_scheme == "https":
        state = "already https"
    elif final_scheme == "https":
        state = "upgraded"
    else:
        state = "not upgraded"
    if final_scheme == "https":
        security = "HSTS present" if hsts else "no HSTS"
    else:
        security = "no HTTPS"
    print("OK %d hop(s), %s, %s, final %d"
          % (len(hops), state, security, result["status"]))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Follow an HTTP redirect chain and audit each hop.",
        epilog="Exit codes: 0 clean, 1 finding, 2 usage or input error.")
    parser.add_argument("url", help="http:// or https:// URL to check")
    parser.add_argument("--max-hops", type=int, default=3, metavar="N",
                        help="fail when the chain has more than N hops, default 3")
    parser.add_argument("--timeout", type=float, default=10.0, metavar="SEC",
                        help="socket timeout in seconds, default 10")
    parser.add_argument("--require-hsts", action="store_true",
                        help="fail when the final HTTPS response has no HSTS header")
    parser.add_argument("--json", action="store_true",
                        help="print one JSON report instead of text")
    args = parser.parse_args(argv)

    if not valid_url(args.url):
        parser.error("URL must start with http:// or https:// and include a host")
    if not 0 <= args.max_hops <= 10:
        parser.error("--max-hops must be between 0 and 10")
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    try:
        result = fetch(args.url, args.timeout)
    except (FetchError, ValueError) as exc:
        print("ERR %s" % exc, file=sys.stderr)
        return 2

    findings, warnings, hsts = audit(args.url, result, args.max_hops, args.require_hsts)
    report(args.url, result, findings, warnings, hsts, args.max_hops, args.json)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
