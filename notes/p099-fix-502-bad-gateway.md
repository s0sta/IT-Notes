---
id: p99
title: "Fix: 502 Bad Gateway"
slug: fix-502-bad-gateway
sections: [it]
topic: "Web servers, TLS & HTTP"
tags: [Nginx, Linux, WebDevelopment, Troubleshooting, SysAdmin]
source: "LinkedIn post P99 · Linux + IT series"
linkedin_date: 2027-05-16
design: steps
---

# Fix: 502 Bad Gateway

502 Bad Gateway. nginx is running fine. What failed is the application behind it: PHP-FPM, Node, Gunicorn or whatever nginx passes requests to.

## Quick reference

### Diagnose — What is nginx trying to reach?

```bash
# The upstream error: refused, timed out, or no socket.
tail -f /var/log/nginx/error.log
# Is the app server running at all?
systemctl status php8.3-fpm
# Which socket or port nginx expects to find.
grep -r fastcgi_pass /etc/nginx/sites-enabled/
```

### Fix — Reconnect the two

```bash
# Bring the backend back. Then read its own log.
systemctl restart php8.3-fpm
# The socket nginx expects must exist, with that exact name.
ls -l /run/php/
# After fixing the path, test and reload.
nginx -t && systemctl reload nginx
```

### Prevent — Stop the next one

- `pm.max_children` — Too few PHP workers queue up and time out under load.
- **Monitor the backend** — Check the app port or socket, not only nginx.
- **Version in the socket name** — A PHP upgrade changes php8.2 to php8.3. Update nginx.

## Explained

### Diagnose

- `tail -f /var/log/nginx/error.log` — nginx writes exactly what went wrong when it tried to reach the backend. "Connection refused" means nothing is listening. "No such file or directory" means the socket does not exist. "upstream timed out" is a 504, a slow backend rather than a missing one.
- `systemctl status php8.3-fpm` — is the backend service running? If it crashed, its own log or `journalctl -u php8.3-fpm` explains why.
- `grep -r fastcgi_pass /etc/nginx/sites-enabled/` — which socket or port nginx expects. For apps behind proxy_pass, search for that instead.

### Fix

- `systemctl restart php8.3-fpm` — get the backend running again, then read its log so it does not happen again tonight.
- `ls -l /run/php/` — the socket in the nginx config must exist with exactly that name, and nginx must have permission to use it.
- `nginx -t && systemctl reload nginx` — after correcting the path, test the config and reload. No downtime.

### Prevent

- `pm.max_children` — when all PHP-FPM workers are busy, new requests wait and eventually fail. Size it to your RAM and traffic, and watch the log for "server reached `pm.max_children`".
- **Monitor the backend** — an uptime check that only tests nginx can stay green while the app is dead. Check a page that needs the application.
- **Version in the socket name** — a PHP upgrade from 8.2 to 8.3 often changes the socket path. The upgrade succeeds, and the site returns 502 until nginx is updated.

## In one line

> **502 means look behind nginx.** The error shows in nginx. The cause almost never lives there.

**The first command**

```bash
tail -20 /var/log/nginx/error.log
```
