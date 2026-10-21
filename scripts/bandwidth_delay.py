#!/usr/bin/env python3
"""Compute the bandwidth-delay product and the window it demands.

Usage:
    python3 bandwidth_delay.py
    python3 bandwidth_delay.py --rtt 40 --mbps 1000
    python3 bandwidth_delay.py --rtt 40 --mbps 1000 --window 65535
    python3 bandwidth_delay.py --rtt 150 --mbps 10000 --window 262144

Units: --rtt is milliseconds, --mbps is megabits per second (1,000,000 bits)
and --window is bytes. The bandwidth-delay product is:

    BDP = bandwidth in bits per second x RTT in seconds / 8

The result is in bytes: the data that must be in flight to fill the path.
The window needed for line rate is the BDP. The throughput of a window is:

    window in bytes x 8 / RTT in seconds

in bits per second, printed in megabits. A window below the BDP is
window-limited: the path is not the limit, the receive window is, and the
exit code is 1.

Cron (daily, 08:30):  30 8 * * *  python3 bandwidth_delay.py --window 5000000
CI step: python3 bandwidth_delay.py --rtt 40 --window 5000000  # fails if small

Exit codes: 0 clean or no window to check, 1 the window is undersized,
2 usage or input error.

By s0sta.com
"""
import argparse
import math
import sys

DEFAULT_RTT_MS = 40.0
DEFAULT_MBPS = 1000.0
DEFAULT_MSS = 1460


def parse_args(argv=None):
    """Parse the command line."""
    parser = argparse.ArgumentParser(
        description="Compute BDP in bytes and the window needed for line rate.")
    parser.add_argument("--rtt", type=float, default=DEFAULT_RTT_MS,
                        metavar="MS", help="round-trip time in ms (40)")
    parser.add_argument("--mbps", type=float, default=DEFAULT_MBPS,
                        metavar="MBPS", help="bandwidth in Mbps (1000)")
    parser.add_argument("--window", type=int, default=None, metavar="BYTES",
                        help="TCP window to check in bytes (none)")
    parser.add_argument("--mss", type=int, default=DEFAULT_MSS, metavar="BYTES",
                        help="MSS used to count segments (1460)")
    return parser.parse_args(argv)


def bdp_bytes(mbps, rtt_ms):
    """Return the bandwidth-delay product in bytes."""
    return mbps * 1_000_000 / 8 * (rtt_ms / 1000)


def window_mbps(window_bytes, rtt_ms):
    """Return the throughput of a window in Mbps."""
    return window_bytes * 8 / (rtt_ms / 1000) / 1_000_000


def main(argv=None):
    """Print the BDP, the line-rate window and one verdict; return an exit code."""
    args = parse_args(argv)

    if args.rtt <= 0:
        print("ERROR --rtt must be greater than zero", file=sys.stderr)
        return 2
    if args.mbps <= 0:
        print("ERROR --mbps must be greater than zero", file=sys.stderr)
        return 2
    if args.window is not None and args.window < 0:
        print("ERROR --window must be zero or more bytes", file=sys.stderr)
        return 2
    if args.mss <= 0:
        print("ERROR --mss must be greater than zero", file=sys.stderr)
        return 2

    bdp = bdp_bytes(args.mbps, args.rtt)
    need = math.ceil(bdp)
    segments = math.ceil(bdp / args.mss)

    print("RTT %.1f ms   bandwidth %.1f Mbps" % (args.rtt, args.mbps))
    print("BDP %d bytes (%.2f MB, %d segments of %d)"
          % (need, bdp / 1_000_000, segments, args.mss))
    print("window for line rate %d bytes" % need)

    if args.window is None:
        print("no --window given; nothing to check")
        return 0

    rate = window_mbps(args.window, args.rtt)
    share = 100.0 * args.window / bdp if bdp else 0.0
    print("window %d bytes -> %.1f Mbps (%.1f%% of line rate)"
          % (args.window, rate, share))

    if args.window < bdp:
        print("ERR window is %d bytes below the BDP" % (need - args.window))
        return 1
    print("OK window covers the BDP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
