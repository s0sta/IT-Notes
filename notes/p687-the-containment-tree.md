---
id: p687
title: "The containment tree"
slug: the-containment-tree
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, CyberSecurity, SRE, DevOps, Containment]
source: "LinkedIn post P687 · IR series"
linkedin_date: 2031-02-16
design: architecture
---

# The containment tree

The first hour of containment is a tree, not a checklist. You scope what you know, cut the paths you can see, and verify that the cut did what you meant.

## Quick reference

- **Tier 1 · Scope:** Host (HOST) · Identity (IDENT)
- **Tier 2 · Cut:** Network path (NET) · Access path (ACL)
- **Tier 3 · Verify:** Service health (SVC) · Evidence (EVID)

**Request flow:** Host → Network path → Service health; Network path → Evidence; Identity → Access path → Service health; Access path → Evidence

## Explained

### Scope

Scope is the host and the identity. The host is an address, a name, a role and a set of open ports. The identity is a login, a session and the tokens it can mint. You cannot contain what you cannot name, and you cannot name what nobody inventoried.

### Cut

Cut is the network and the access. The network cut drops east-west traffic first and keeps the management path. The access cut ends the sessions at the identity provider, then revokes the keys and tokens that outlive a password. Both cuts are paths, not machines: a host with no route is contained even when it is still running.

### Verify

Verify is the service and the evidence. The service check proves the safe part still answers, so you are not trading an incident for a silent outage. The evidence step captures the process list, the connections and the auth log before they age out.

> **The honest caveat:** a missing arrow is the failure. If the tree does not show that the build account reads the flag, the cut will find it for you.

> **The lesson:** scope it, cut it, then prove it, in that order, every time.

## In one line

> **Scope it, cut it, then prove it.** Containment is a tree: the root is what you know, the leaves what you can prove.

**Scope before cut**

```bash
ss -tlnp; last -n 20
```
