---
id: p518
title: "Network health at a glance"
slug: network-health-at-a-glance
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, Observability, SRE, Dashboard, DevOps]
source: "LinkedIn post P518 · Network series"
linkedin_date: 2030-01-17
design: dashboard
---

# Network health at a glance

The pager fires on latency, and the dashboard that explains it has six tiles, none of which is CPU.

## Quick reference

**Status:** Last 15 minutes

| Metric | Value | Note |
|:--|:--|:--|
| p95 latency | **48 ms** | edge to origin |
| Packet loss | **0.2%%** | inter-AZ path |
| Retransmits | **1.8%** | of TCP segments |
| DNS failures | **0.4%%** | SERVFAIL and timeouts |
| LB 5xx | **0.12%** | server-side requests |
| Bandwidth headroom | **38%** | peak vs provisioned |

## Explained

### The path

p95 latency is 48 ms from edge to origin, which means one request in twenty is slower and the average is hiding it. A missing tile is a blind spot, not a zero. Packet loss is 0.2% on the inter-AZ path, low enough to look healthy and high enough to cost retransmits. Retransmits are 1.8% of TCP segments, the tile that usually explains the other two.

### The edges

DNS failures are 0.4%, and the split matters: NXDOMAIN is a client asking for a name that does not exist, while SERVFAIL and timeouts are yours. LB 5xx is 0.12% of requests, server-side failures only; a rise in 4xx is a client or a broken deploy, not a sick backend.

### The margin

Bandwidth headroom is 38% at peak, measured against provisioned egress; below 20% a single large response can fill the pipe. Read the six together: loss explains retransmits, retransmits explain latency, and headroom explains why it got worse at noon. One large response at 38% headroom is a spike, not a capacity plan.

> **The honest caveat:** p95 hides the p99 that a few users remember, and a tile is only comparable when its label names the window and the population.

> **The lesson:** a network board should point at the next query, not answer it.

## In one line

> **Six tiles, one direction.** A board should point at the next query, not answer it.

**Follow the drop:** nstat -az TcpRetransSegs
