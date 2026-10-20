---
id: p104
title: "9 nginx settings worth knowing"
slug: 9-nginx-settings-worth-knowing
sections: [it]
topic: "Web servers, TLS & HTTP"
tags: [Nginx, Linux, WebPerformance, WebSecurity, DevOps]
source: "LinkedIn post P104 · Linux + IT series"
linkedin_date: 2027-05-27
design: steps
---

# 9 nginx settings worth knowing

nginx works out of the box. These nine settings are what make it work well, safely, and in front of a real application.

## Quick reference

### Safety — Hide and limit

```bash
# Hide the nginx version in headers and error pages.
server_tokens off;
# Maximum upload size. Too small gives a 413 error.
client_max_body_size 64m;
# Rate-limit logins. Needs a limit_req_zone first.
limit_req zone=login burst=5;
```

### Speed — Faster responses

```bash
# Compress text responses. Often half the size or less.
gzip on;
# Let browsers cache static files for 30 days.
expires 30d;
# Reuse client connections instead of opening new ones.
keepalive_timeout 65;
```

### Proxy — In front of an app

```bash
# How long to wait for a slow backend before a 504.
proxy_read_timeout 120s;
# Pass the real client IP to the app.
proxy_set_header X-Real-IP $remote_addr;
# Send every plain HTTP request to HTTPS.
return 301 https://$host$request_uri;
```

## Explained

### Safety

- `server_tokens off;` — hides the nginx version number in response headers and error pages. It will not stop a real attacker, but there is no reason to advertise it.
- `client_max_body_size 64m;` — the maximum size of a request body. The default is only 1 MB, which is why file uploads and big WordPress imports fail with "413 Request Entity Too Large".
- `limit_req zone=login burst=5;` — rate limiting for sensitive paths like login pages. It needs a matching limit_req_zone in the http block, which defines the key and the rate.

### Speed

- `gzip on;` — compresses HTML, CSS, JavaScript and JSON. Text responses often shrink to a third of their size. Add gzip_types for anything beyond HTML.
- `expires 30d;` — in a location for static files, tells browsers to cache images, CSS and JS for 30 days instead of asking again on every page.
- `keepalive_timeout 65;` — keeps client connections open so the next request skips a new TCP and TLS handshake.

### Proxy

- `proxy_read_timeout 120s;` — how long nginx waits for a response from the backend. Too short and slow reports or exports fail with 504. Too long and stuck requests pile up.
- `proxy_set_header X-Real-IP $remote_addr;` — passes the real client IP to the application. Without it, every visitor looks like 127.0.0.1 in your app logs.
- `return 301 https://$host$request_uri;` — in the port 80 server block, sends every HTTP request to HTTPS.

After every change: `nginx -t && systemctl reload nginx`.

## In one line

> **Defaults are a starting point.** Five minutes in the config saves a day of tickets.

**Always after editing**

```bash
nginx -t && systemctl reload nginx
```
