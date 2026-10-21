---
id: p520
title: "Quiz: 3 network operations questions"
slug: quiz-3-network-operations-questions
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, TCP, Observability, SRE, CloudNative]
source: "LinkedIn post P520 · Network series"
linkedin_date: 2030-01-22
design: quiz
---

# Quiz: 3 network operations questions

Three questions separate a team that watches the network from one that watches the graph. Answer before you read on.

## Quick reference

**Q1. Why do retransmits rise before latency does when loss begins?**

- a) Retransmits make the RTT longer
- b) TCP repairs loss below the request
- c) Latency is only sampled hourly

> **Answer:** b) TCP repairs loss below the request. A lost segment is resent, and the counter increments immediately. The request only slows when the repair takes a timeout or a second loss.

**Q2. What does a rising bandwidth-delay product imply?**

- a) The link is getting faster
- b) The round trip is falling
- c) More bytes must be in flight

> **Answer:** c) More bytes must be in flight. BDP is bandwidth times RTT. More capacity or more distance means a larger window is needed to fill the pipe; a fixed window loses throughput.

**Q3. Why do flow logs miss a packet dropped in the fabric?**

- a) They capture only TCP traffic
- b) They record flows, not packets
- c) They sample one packet in ten

> **Answer:** b) They record flows, not packets. A flow log aggregates counters after the fact. A packet dropped before its flow is recorded, or inside the network, leaves no entry; a REJECT entry is a policy drop.

## Explained

### Question one

Why do retransmits rise before latency does when loss begins? TCP repairs a lost segment below the request: the counter increments on every resend, while the request only slows when the repair takes a timeout or a second loss. The average barely moves because the repair succeeds; the counter sees every packet, including the ones that never reached the server.

### Question two

What does a rising BDP imply? Bandwidth times RTT is the data the path can hold. If either grows, the window must grow with it or throughput falls, which is why a new region needs a bigger window before it needs a faster link.

### Question three

Why do flow logs miss a packet dropped in the fabric? A flow log records flows, not packets: it aggregates counters after the fact, so a packet dropped before its flow is accounted for never appears. A REJECT entry shows a policy drop; silence shows nothing at all. That is why a capture, not a dashboard, settles a drop argument.

> **The honest caveat:** counters are per host and per direction, so a retransmit seen at the sender may be invisible at the receiver.

> **The lesson:** loss shows up in counters before it shows up in percentiles.

## In one line

> **Watch the repair, not the average.** Loss shows up in counters before it shows up in percentiles.

**Read tcp stats:** nstat -az TcpRetransSegs
