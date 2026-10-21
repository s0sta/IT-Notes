---
id: p698
title: "Recovery command cheat sheet"
slug: recovery-command-cheat-sheet
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, CyberSecurity, Linux, SRE, CommandLine]
source: "LinkedIn post P698 · IR series"
linkedin_date: 2031-03-13
design: cheatsheet
---

# Recovery command cheat sheet

Recovery is a set of small proofs. Did the old credential stop working? Does the serial match? Is the config the hash that worked? Is the snapshot restorable? Each block answers one of those.

## Quick reference

### Secrets

```bash
vault kv metadata get secret/db
aws secretsmanager list-secrets
gcloud secrets versions list db
vault token lookup
systemctl status vault-agent
```

### Certs

```bash
openssl x509 -noout -serial -in cert.pem
openssl x509 -noout -dates -in cert.pem
openssl s_client -connect host:443
systemctl reload nginx
kubectl rollout restart deploy/api
```

### Config

```bash
sha256sum /etc/nginx/nginx.conf
diff -u lkg/nginx.conf /etc/nginx.conf
cp -p lkg/nginx.conf /etc/nginx.conf
nginx -t && systemctl reload nginx
kubectl rollout undo deploy/api
```

### Data

```bash
aws rds describe-db-snapshots
pg_restore -l /backup/app.dump
restic snapshots --last 5
velero restore create --from-backup b
kubectl get pvc -n prod
```

## Explained

### Secrets

Read metadata, never the value. `vault kv metadata get secret/db` shows versions and timestamps; `aws secretsmanager list-secrets` shows rotation dates; `gcloud secrets versions list db` lists versions; `vault token lookup` shows policies and TTL; `systemctl status vault-agent` proves the agent is running. A command that prints a secret is not a recovery command.

### Certs

`openssl x509 -noout -serial -in cert.pem` reads the serial; -dates reads the validity window; `openssl s_client -connect host:443` proves what the listener serves. `systemctl reload nginx` applies a new file, and `kubectl rollout restart deploy/api` does the same for a pod. Reload after every copy, never before.

### Config

sha256sum proves the file; diff shows what changed; `cp -p` restores it; `nginx -t` proves it parses; `nginx -t && systemctl reload nginx` applies it. `kubectl rollout undo deploy/api` returns the Deployment to the previous ReplicaSet. A hash match is not a config test.

### Data

`aws rds describe-db-snapshots` lists the RDS snapshots; `pg_restore -l` reads a dump without restoring it; `restic snapshots --last 5` lists the restic ones; velero restore create `--from-backup b` starts a cluster restore; `kubectl get pvc -n prod` shows what is bound. Prove before you restore.

> **The honest caveat:** some commands prove; some change. None of them proves the restored data is correct.

> **The lesson:** recovery commands should prove state before they change it.

## In one line

> **Prove the state, then change it.** Every block answers a question the incident asked.

**Prove the serial**

```bash
openssl x509 -noout -serial
```
