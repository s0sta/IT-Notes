---
id: p513
title: "The packet capture cheat sheet"
slug: the-packet-capture-cheat-sheet
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, Tcpdump, Wireshark, Troubleshooting, SRE]
source: "LinkedIn post P513 · Network series"
linkedin_date: 2030-01-06
design: cheatsheet
---

# The packet capture cheat sheet

At 02:00 the API is slow, every dashboard is green, and the only evidence left is on the wire. Packet capture is the tool that turns an argument into a file.

## Quick reference

### Capture

```bash
tcpdump -i any -w /tmp/cap.pcap
tcpdump -i eth0 -s 0 -w cap.pcap
tshark -i eth0 -w /tmp/cap.pcapng
tcpdump -i eth0 -c 100 -nn
tcpdump -i eth0 -w cap.pcap -U
```

### Filter

```bash
tcpdump -i eth0 port 443
tcpdump -i eth0 host 10.0.0.5
tcpdump 'tcp[tcpflags] & tcp-syn != 0'
tcpdump -i eth0 net 10.0.0.0/24
tshark -i eth0 -f "port 53"
```

### Read

```bash
tcpdump -r cap.pcap -nn -tttt
tshark -r cap.pcap -Y http.request
tshark -r cap.pcap -q -z conv,tcp
tcpdump -r cap.pcap -A port 80
tshark -r cap.pcap -T fields -e ip.src
```

### Rotate

```bash
tcpdump -i eth0 -G 60 -w cap-%H%M.pcap
tcpdump -i eth0 -C 100 -w cap.pcap
tcpdump -i eth0 -W 5 -C 100 -w cap.pcap
tcpdump -i eth0 -z gzip -w cap.pcap
tshark -i eth0 -b duration:60 -w c.pcapng
```

## Explained

### Capture

Start with `tcpdump -i any -w /tmp/cap.pcap`, or `tshark -i eth0 -w /tmp/cap.pcapng` when you want the newer file format. Add -s 0 to keep the whole packet, -nn to stop the resolver turning addresses into names under load, and -U to write each packet as it arrives rather than in blocks.

### Filter

A capture without a filter fills the disk. Keep it narrow: `tcpdump -i eth0 port 443`, host 10.0.0.5, or 'tcp[tcpflags] & tcp-syn != 0' for handshakes. `tshark -f "port 53"` applies the same BPF before anything is written, which is cheaper than filtering later.

### Read

Read the file with `tcpdump -r cap.pcap -nn -tttt` for absolute timestamps, `tshark -Y http.request` for one protocol, and `tshark -q -z` conv,tcp for the conversation summary that shows who sent the most.

### Rotate

On a busy host, rotate: -G 60 starts a file a minute, -C 100 at a hundred megabytes, -W 5 keeps five, and -z gzip compresses each one as it closes. `tshark -b duration:60` does the same with one file a minute.

> **The honest caveat:** a capture on one host sees only traffic that reaches that host, and a pcap can hold credentials, so treat it like production data and delete it on a schedule.

> **The lesson:** capture the smallest slice that can still answer the question.

## In one line

> **Capture first, argue later.** A pcap settles a disagreement faster than a dashboard.

**Capture, then read**

```bash
tcpdump -i any -w /tmp/cap.pcap
```
