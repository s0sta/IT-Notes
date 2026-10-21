---
id: p639
title: "Four config and crypto failures"
slug: four-config-and-crypto-failures
sections: [it, devsecops]
topic: "Security & hardening"
tags: [DevSecOps, TLS, SSH, Linux, CyberSecurity]
source: "LinkedIn post P639 · ShellSec series"
linkedin_date: 2030-10-27
design: explainer
---

# Four config and crypto failures

Four failures look different in a ticket and identical in a shell. Each one is a comparison that nobody ran.

## Quick reference

### Silent drift

- A file changes and no ticket records it
- The next deploy quietly reverts it
- Fix: hash the tree, diff nightly
- Keep the baseline off the host

### Expired certificate

- The leaf expires while the chain is fine
- The client reports an error, not a renewal date
- Fix: warn at 30 days, renew at 14
- Check the mounted file on every node

### Weak key type

- ssh-rsa and ssh-dss are legacy algorithms
- A long RSA key can still sign with SHA-1
- Fix: ed25519 for people, rsa-sha2 for legacy
- Remove the key, then rotate the account

### Missing baseline

- No baseline means no definition of changed
- A backup is a copy, not a measurement
- Fix: store hashes off the host you audit
- Re-baseline after every approved change

> **Note:** Four failures, one habit: compare with something you trust.

## Explained

### Silent drift

A file changes and no ticket records it. The next deploy reverts it, or worse, keeps it. The fix is a hash of the tree and a nightly diff, with the baseline stored off the host so a local change cannot edit the evidence.

### Expired certificate

The leaf expires while the chain is fine, and the client reports a certificate error, not a date. Warn at 30 days and renew at 14, then check the file the ingress actually mounts on every node.

### Weak key type

ssh-rsa and ssh-dss are legacy algorithms. A long RSA key can still sign with SHA-1, because key length does not choose the signature hash. Use ed25519 for people and rsa-sha2 for legacy systems, then remove the old key and rotate the account.

### Missing baseline

No baseline means no definition of changed. A backup is a copy, not a measurement. Store hashes off the host you audit and re-baseline after every approved change, or the first finding will be an argument.

> **The honest caveat:** a weak key type is a policy failure, not proof of compromise, and a missing baseline cannot be reconstructed after the fact.

> **The lesson:** every one of these is a comparison, and every comparison needs a reference.

## In one line

> **Name the failure, then hash it.** Each panel is a check you can run before the page.

**Run the four**

```bash
sha256sum; openssl x509; ssh-keygen -lf
```
