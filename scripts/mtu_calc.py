#!/usr/bin/env python3
"""Compute the usable MTU and TCP MSS under common tunnel overheads.

Usage:
    python3 mtu_calc.py
    python3 mtu_calc.py --profile vxlan --mtu 1500
    python3 mtu_calc.py --profile gre --underlay 9001
    python3 mtu_calc.py --profile ipsec --ipsec-overhead 73

Profiles and overhead, in bytes:
    plain    0   no encapsulation
    vxlan   50   outer Ethernet 14 + outer IPv4 20 + UDP 8 + VXLAN 8
    gre     24   outer IPv4 20 + GRE 4
    ipsec  varies, 50 by default; ESP and outer IP, NAT-T adds 8 more

The usable MTU is the underlay MTU minus the profile overhead. The TCP MSS is
the usable MTU minus 40 bytes, the 20-byte IPv4 header plus the 20-byte TCP
header. If the configured inner MTU is larger than the usable MTU, the profile
will fragment when the don't-fragment bit is clear, or black-hole when ICMP
fragmentation-needed is filtered, so the exit code is 1.

Cron (daily, 08:15):  15 8 * * *  python3 mtu_calc.py --profile vxlan --mtu 1450
CI step: python3 mtu_calc.py --profile vxlan --mtu 1450   # fails if it drifts

Exit codes: 0 clean, 1 the configured MTU does not fit, 2 usage or input error.

By s0sta.com
"""
import argparse
import sys

OVERHEAD = {"plain": 0, "vxlan": 50, "gre": 24}
DEFAULT_IPSEC = 50
IPV4_TCP = 40
MIN_MTU = 68
MAX_MTU = 65535


def parse_args(argv=None):
    """Parse the command line."""
    parser = argparse.ArgumentParser(
        description="Compute usable MTU and TCP MSS for a tunnel profile.")
    parser.add_argument("--profile", choices=("plain", "vxlan", "gre", "ipsec"),
                        default="plain", help="encapsulation profile (plain)")
    parser.add_argument("--underlay", type=int, default=1500, metavar="BYTES",
                        help="underlay MTU in bytes (1500)")
    parser.add_argument("--mtu", type=int, default=1500, metavar="BYTES",
                        help="configured inner MTU to check (1500)")
    parser.add_argument("--ipsec-overhead", type=int, default=DEFAULT_IPSEC,
                        metavar="BYTES",
                        help="IPsec overhead for the ipsec profile (50)")
    return parser.parse_args(argv)


def overhead_for(profile, ipsec_overhead):
    """Return the encapsulation overhead in bytes for one profile."""
    if profile == "ipsec":
        return ipsec_overhead
    return OVERHEAD[profile]


def compute(profile, underlay, ipsec_overhead):
    """Return (overhead, usable MTU, TCP MSS) for one profile."""
    overhead = overhead_for(profile, ipsec_overhead)
    usable = underlay - overhead
    return overhead, usable, usable - IPV4_TCP


def main(argv=None):
    """Print one profile and return the exit code."""
    args = parse_args(argv)

    if not MIN_MTU <= args.underlay <= MAX_MTU:
        print("ERROR --underlay must be %d..%d bytes" % (MIN_MTU, MAX_MTU),
              file=sys.stderr)
        return 2
    if not MIN_MTU <= args.mtu <= MAX_MTU:
        print("ERROR --mtu must be %d..%d bytes" % (MIN_MTU, MAX_MTU),
              file=sys.stderr)
        return 2
    if not 0 <= args.ipsec_overhead <= 200:
        print("ERROR --ipsec-overhead must be 0..200 bytes", file=sys.stderr)
        return 2

    overhead, usable, mss = compute(args.profile, args.underlay,
                                    args.ipsec_overhead)
    if mss <= 0:
        print("ERROR underlay %d is too small for profile %s"
              % (args.underlay, args.profile), file=sys.stderr)
        return 2

    print("%-9s %s" % ("profile", args.profile))
    print("%-9s %d bytes" % ("overhead", overhead))
    print("%-9s %d bytes" % ("underlay", args.underlay))
    print("%-9s %d bytes" % ("usable", usable))
    print("%-9s %d bytes" % ("TCP MSS", mss))

    over = args.mtu - usable
    if over > 0:
        print("FRAG configured %d bytes is %d over the usable MTU"
              % (args.mtu, over))
        return 1
    print("OK configured %d bytes fits the usable MTU" % args.mtu)
    return 0


if __name__ == "__main__":
    sys.exit(main())
