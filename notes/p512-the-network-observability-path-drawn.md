---
id: p512
title: "The network observability path, drawn"
slug: the-network-observability-path-drawn
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, Observability, SRE, DevOps, eBPF]
source: "LinkedIn post P512 · Network series"
linkedin_date: 2030-01-03
design: architecture
---

# The network observability path, drawn

A latency alert fires and three dashboards disagree about which hop is slow. The observability path is how you stop guessing.

## Quick reference

- **Sources:** Flow logs (FLOW) · eBPF probes (EBPF) · Interface counters (NIC)
- **Pipeline:** Collector (COLL) · Time-series store (TSDB)
- **Action:** Alerts (PAGE) · Dashboards (DASH) · Runbooks (RUN)

**Request flow:** Flow logs → Collector → Time-series store → Alerts; Time-series store → Dashboards; Time-series store → Runbooks; eBPF probes → Collector; Interface counters → Collector

## Explained

### Sources

Flow logs record who talked to whom, how many bytes moved and whether the security group accepted the flow. eBPF probes read the kernel's socket and scheduler events without copying every packet, which is how retransmits and queue time become visible. Interface counters are the cheapest signal: bytes, packets, drops and errors straight from the wire.

### Pipeline

A collector receives all three streams, batches them and adds the labels that make them joinable: account, region, node and pod. The time-series store keeps those labels for as long as the retention budget allows, and cardinality, not volume, is what makes it expensive. Sampling is a budget decision, not a technical one.

### Action

Alerts fire on symptoms worth waking for. Dashboards put the path beside the number. Runbooks turn the page into three commands and a rollback. An alert without a runbook is only a notification.

The drawing builds top to bottom: the three source nodes feed the collector, the collector writes to the store, and the store fans out to alerts, dashboards and runbooks. A packet then travels each arrow in turn.

> **The honest caveat:** flow logs aggregate, eBPF depends on the kernel, and counters cannot say which flow dropped. None of the three is complete alone.

> **The lesson:** instrument the path, not the box.

## In one line

> **Measure the path, not the box.** A counter without a path is a number without an owner.

**Read the counters**

```bash
curl -s localhost:9100/metrics | head
```
