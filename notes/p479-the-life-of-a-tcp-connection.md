---
id: p479
title: "The life of a TCP connection"
slug: the-life-of-a-tcp-connection
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [TCP, Networking, SRE, DevOps, Linux]
source: "LinkedIn post P479 · Network series"
linkedin_date: 2029-10-18
design: timeline
---

# The life of a TCP connection

A connection is born, works, idles and dies, and the kernel keeps a state for every step. Knowing the six states explains most of what ss shows you.

## Quick reference

| Time | Step | What happens |
|:--|:--|:--|
| **0 ms** | SYN | Client sends SYN with its initial sequence number and options. |
| **1 ms** | Established | SYN-ACK returns, ACK completes it; data flows both ways. |
| **2 h** | Keep-alive | First probe after 7200 s idle; nine misses drop the socket. |
| **2 h+** | Idle | No payload, but a file descriptor and a conntrack entry remain. |
| **60 s** | TIME_WAIT | The active closer waits 2 x MSL before the tuple is reused. |
| **60 s+** | Closed | The tuple is released and the ephemeral port can be reused. |

## Explained

### The start

SYN. The client sends a SYN with an initial sequence number and options. The socket sits in SYN_SENT, and the server creates an entry in SYN_RECV.

Established. The SYN-ACK returns and the ACK completes the handshake. Both sockets move to ESTABLISHED and data can flow both ways. This is the only state where the application reads and writes normally.

### The idle

Keep-alive. When enabled, after two hours idle by default on Linux, the kernel sends a probe with no payload. If the peer answers, the timer resets. If nine probes go unanswered, the connection is dropped.

Idle. Between probes the connection is idle but still established, and it still consumes a file descriptor, a buffer and a conntrack entry. Thousands of idle connections are held open, not leaked.

### The end

TIME_WAIT. The side that closes first waits 60 seconds on Linux before the tuple can be reused. The wait absorbs delayed duplicates and lets the final ACK be retransmitted if it was lost.

Closed. The tuple is released and the ephemeral port can be reused. The next connection may get the same port with a new sequence number.

> **The honest caveat:** keep-alive does not survive every middlebox. A NAT or firewall may drop the idle mapping long before two hours, and the next write discovers a dead connection.

> **The lesson:** read the state before you blame the application.

## In one line

> **Every state is a promise.** The kernel keeps it so your application does not have to.

**Watch the state**

```bash
ss -tan state time-wait
```
