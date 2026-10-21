---
id: p699
title: "Four recovery failures, explained"
slug: four-recovery-failures-explained
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, SRE, CyberSecurity, Kubernetes, Reliability]
source: "LinkedIn post P699 · IR series"
linkedin_date: 2031-03-16
design: explainer
---

# Four recovery failures, explained

Most recoveries fail in the same four places, and none of them is a tool failure. They are all a step taken in the wrong order, or a check that was never run.

## Quick reference

### Rotation out of order

- Dependency rotates after its consumers
- Two credentials live at once
- Auth errors look like a new incident

### One certificate, many hosts

- One reload, several listeners
- The edge serves a serial the backends do not
- Replace everywhere before any reload

### The restore point is missing

- Newest snapshot still creating
- Catalog says complete, nobody restored it
- No complete point inside the window

### Draining too fast

- PDB allows one, node holds two replicas
- Second eviction blocks the drain
- Force it and capacity drops below the floor

> **Note:** All four are a step taken too early, not a tool that failed.

## Explained

### Rotation out of order

Rotate a dependency after its consumers and both credentials are live at once. The API keeps the old password in a pool, the worker reconnects with it, and every auth error looks like a new incident. Rotate the dependency first, verify the consumer, then retire the old value.

### One certificate, many hosts

A certificate shared by four hosts is one change with four reloads. Reload the load balancer before the web hosts have the file and the edge serves a serial the backends do not. Replace everywhere, then reload one host at a time.

### The restore point is missing

The newest snapshot is still creating, the one before it failed, and the one that works is outside the window. The catalog said "backup complete"; nobody restored it. A restore point must be complete, before the incident, and drilled.

### Draining too fast

The PDB allows one disruption and the node holds two of the three replicas. Drain it and the second eviction blocks; force it and the service drops below its floor. Capacity is part of the plan, not an afterthought.

> **The honest caveat:** these four are the common failures, not the only ones.

> **The lesson:** recovery fails in the gaps between steps, where nobody checked.

## In one line

> **Recovery fails in the gaps.** The plan is the check between the steps.

**Check the order**

```bash
python3 node_drain.py drain.json
```
