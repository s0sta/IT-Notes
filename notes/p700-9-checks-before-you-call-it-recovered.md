---
id: p700
title: "9 checks before you call it recovered"
slug: 9-checks-before-you-call-it-recovered
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, SRE, CyberSecurity, DevSecOps, Checklist]
source: "LinkedIn post P700 · IR series"
linkedin_date: 2031-03-18
design: checklist
---

# 9 checks before you call it recovered

The pager is quiet and the dashboard is green. That is the moment to slow down: a service can be up and still be compromised, misconfigured or running on data from the wrong hour.

## Quick reference

### Access

```bash
# Old credentials fail
curl -H 'Authorization: old'
# Certificate serial matches
openssl x509 -noout -serial
# Sessions are revoked
SELECT count(*) FROM sessions
```

### Config

- **Config hash matches LKG** — `sha256sum -c manifest`
- **Image digest is pinned** — `kubectl get pod -o yaml`
- **Feature flags are reverted** — flag audit log

### Data

```bash
# Restore point is drilled
pg_restore -l dump
# Row counts match the LKG
SELECT count(*) FROM orders
# Replication is caught up
pg_last_wal_replay_lsn()
```

## Explained

### Access

Old credentials fail. Run the old token against the API and watch it return 401; a vault entry that says "rotated" is not proof.  
The certificate serial matches. `openssl x509 -noout -serial -in cert.pem` on each host, then `openssl s_client -connect host:443` from outside; a reload that never happened is invisible from the file.  
Sessions are revoked. Count the active sessions for the affected users, then count them again after the revoke. A stolen cookie does not care that the password changed.

### Config

The config hash matches the LKG. sha256sum every drifted file against the manifest before the service starts.  
The image digest is the one that passed. `kubectl get pod -o yaml` shows the digest; a tag can move, a digest cannot.  
Feature flags are back to the known good. The flag audit log names who changed what, and the kill switch is off.

### Data

The restore point is drilled. `pg_restore -l` reads the dump; a row count in a scratch schema is better.  
The row counts match the last known good. Compare orders, users and the ledger, not just the table count.  
Replication is caught up. pg_last_wal_replay_lsn on the replica should match the primary before you trust a read.

> **The honest caveat:** a green checklist is evidence of checks, not proof of safety.

> **The lesson:** recovery ends when an independent check passes, not when the pager stops.

## In one line

> **Recovered is a test result.** A quiet pager is not a passing check.

**The first check**

```bash
openssl x509 -noout -serial
```
