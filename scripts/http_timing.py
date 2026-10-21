#!/usr/bin/env python3
"""Measure the HTTP timing phases of one URL.

    python3 http_timing.py https://example.com --budget 1.5
    python3 http_timing.py http://127.0.0.1:8080/ --budget 0.25

Prints dns, tcp, tls and ttfb, then total to the first response byte,
in milliseconds. Exits 1 when total exceeds --budget, and 2 on a usage,
URL or connection error. The request is one GET; nothing is written.

Cron/CI: python3 http_timing.py "$URL" --budget 2 || exit 1
By s0sta.com
"""
import argparse
import socket
import ssl
import sys
import time
from urllib.parse import urlsplit


def parse_url(url):
    """Return scheme, host, port and request path for an http(s) URL."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValueError("URL must start with http:// or https://")
    if not parts.hostname:
        raise ValueError("URL has no hostname")
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("URL has an invalid port") from exc
    if port is None:
        port = 443 if parts.scheme == "https" else 80
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return parts.scheme, parts.hostname, port, path


def tcp_connect(infos, timeout):
    """Connect to the first working address and return the socket."""
    last = None
    for family, socktype, proto, _, sockaddr in infos:
        sock = socket.socket(family, socktype, proto)
        sock.settimeout(timeout)
        try:
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            last = exc
            sock.close()
    raise last or OSError("no address to connect to")


def measure(url, timeout, insecure):
    """Time each phase of one GET, in milliseconds."""
    scheme, host, port, path = parse_url(url)
    started = time.perf_counter()
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    after_dns = time.perf_counter()
    sock = tcp_connect(infos, timeout)
    after_tcp = time.perf_counter()
    if scheme == "https":
        context = ssl.create_default_context()
        if insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        sock = context.wrap_socket(sock, server_hostname=host)
    after_tls = time.perf_counter()
    default_port = 443 if scheme == "https" else 80
    shown = "[%s]" % host if ":" in host else host
    host_header = shown if port == default_port else "%s:%d" % (shown, port)
    request = (
        "GET %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "User-Agent: http-timing/1.0\r\n"
        "Accept: */*\r\n"
        "Connection: close\r\n\r\n" % (path, host_header)
    ).encode("ascii", "replace")
    sock.sendall(request)
    first = sock.recv(1)
    after_first = time.perf_counter()
    sock.close()
    if not first:
        raise OSError("the server closed before the first byte")
    return {
        "dns": (after_dns - started) * 1000,
        "tcp": (after_tcp - after_dns) * 1000,
        "tls": (after_tls - after_tcp) * 1000,
        "ttfb": (after_first - after_tls) * 1000,
        "total": (after_first - started) * 1000,
    }


def report(phases, budget):
    """Print the phase table and return the process exit code."""
    total = phases["total"]
    print("%-8s%9s%8s" % ("phase", "ms", "share"))
    for name in ("dns", "tcp", "tls", "ttfb", "total"):
        ms = phases[name]
        share = (ms / total * 100) if total > 0 else 0.0
        print("%-8s%9.1f%7.1f%%" % (name, ms, share))
    if total > budget * 1000:
        print("OVER budget by %.1f ms" % (total - budget * 1000))
        return 1
    print("within budget: %.1f ms of %.0f ms" % (total, budget * 1000))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Measure DNS, TCP, TLS, TTFB and total for one URL.")
    parser.add_argument("url", help="http:// or https:// URL to time")
    parser.add_argument("--budget", type=float, default=1.5,
                        help="total budget in seconds (default: 1.5)")
    parser.add_argument("--timeout", type=float, default=10.0,
                        help="connect and read timeout in seconds (default: 10)")
    parser.add_argument("--insecure", action="store_true",
                        help="skip TLS verification (test fixtures only)")
    args = parser.parse_args(argv)
    if args.budget <= 0:
        parser.error("--budget must be greater than zero")
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    try:
        phases = measure(args.url, args.timeout, args.insecure)
    except ValueError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2
    except ssl.SSLError as exc:
        print("ERROR TLS handshake failed: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2
    return report(phases, args.budget)


if __name__ == "__main__":
    sys.exit(main())
