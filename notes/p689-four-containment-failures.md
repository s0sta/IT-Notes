---
id: p689
title: "Four containment failures"
slug: four-containment-failures
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, CyberSecurity, SRE, DevOps, Containment]
source: "LinkedIn post P689 · IR series"
linkedin_date: 2031-02-20
design: explainer
---

# Four containment failures

Containment fails in four predictable ways, and each one turns a response into a second incident.

## Quick reference

### Cutting your own access

- You deny 0.0.0.0/0 and lose SSH mid-edit
- Keep a console outside the rules you change
- Test the rule from the management subnet
- Out-of-band access is the real control

### Locking a shared account

- The build account serves four teams
- Disabling it stops every pipeline at once
- Disable the person, rotate the shared secret
- Hold the shared account for its owner

### Blocking a CDN IP

- One edge address serves a thousand customers
- A /32 block is a shared outage
- Check the ASN and the allow rules first
- Block the path or the session, not the CDN

### Killing the wrong flag

- Two flags gate the same checkout path
- The kill switch is not the rollback
- Pull the flag with an owner and a default
- Rehearse the off state in a drill

> **Note:** A containment step fails when it removes the path you need to finish it.

## Explained

### Cutting your own access

You paste a deny rule for 0.0.0.0/0, the SSH session dies mid-edit, and the host is a black hole with a pager. The fix is a management path outside the rules you are changing: a console, a jump host on another subnet, or an out-of-band card.

### Locking a shared account

The build account carries four teams' pipelines. Disabling it stops every deploy at once, and the incident becomes a delivery outage. Disable the person's account, rotate the shared secret, and hold the shared account for its owner.

### Blocking a CDN IP

One edge address serves a thousand customers. A /32 block looks precise and takes a slice of the internet with it. Check the ASN, the allow rules and the hostnames behind the address before the block.

### Killing the wrong flag

Two flags gate the same checkout path, and the friendly name is not the one that controls the failure. Pull the flag with an owner and a default, and rehearse the off state in staging.

> **The honest caveat:** every one of these is cheap to discover in a drill and expensive to discover at 03:00.

> **The lesson:** containment removes a path, and the path you remove is sometimes your own.

## In one line

> **Contain the blast, not the response.** Every failed containment is a control that was never tried in a drill.

**Try it in a drill**

```bash
nft -c -f quarantine.nft
```
