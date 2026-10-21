---
id: p697
title: "The recovery path, drawn"
slug: the-recovery-path-drawn
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, CyberSecurity, SRE, DevSecOps, Recovery]
source: "LinkedIn post P697 · IR series"
linkedin_date: 2031-03-11
design: architecture
---

# The recovery path, drawn

The incident is contained. The attacker's session is dead, the bad deploy is stopped, and the database is three hours behind. The order you recover in decides whether the next hour is a fix or a second incident.

## Quick reference

- **Tier 1 · Rotate:** Secrets (ROT) · Certificates (REPL) · Tokens (REVOK)
- **Tier 2 · Rollback:** Config files (HASH) · Container image (DIG) · Feature flags (FLAG)
- **Tier 3 · Restore:** Data snapshot (RSTR) · Traffic (SHFT) · Verification (PROVE)

**Request flow:** Secrets → Config files → Data snapshot → Traffic → Verification; Certificates → Config files; Tokens → Config files; Container image → Data snapshot

**Around it:** Audit log (LOG) · Status page (PAGE) · Evidence store (EVID)

## Explained

### Rotate

Access comes first. Rotate every secret the attacker could have read: the database password, the API token, the signing key. Replace every certificate they could have copied, including the shared ones. This is the tier most often skipped. Verification is not "the new value is in the vault"; it is "the old value fails".

### Roll back

Configuration comes second. Roll the config files back to the last known good hash, then the container image to the digest that passed the last check, then the feature flags. Roll back to a known good, not to "the previous version"; the previous version may be the one that broke.

### Restore

Data comes last. Pick a snapshot before the incident, prove it is complete, and restore into a scratch environment before you point traffic at it. Move traffic only after verification. Restoring data first can overwrite the evidence you need and re-infect the system through a credential you have not rotated.

Around the three tiers sit the audit log, the status page and the evidence store, because a recovery without a record is just a story.

> **The honest caveat:** the order is a default, not a law. A data-destroying incident may force restore earlier, but access still comes first.

> **The lesson:** recovery is a sequence with dependencies, not a checklist of independent fixes.

## In one line

> **Access first, data last.** The order is a dependency chain, not a menu.

**Start with access**

```bash
python3 credential_rotate.py rot.json
```
