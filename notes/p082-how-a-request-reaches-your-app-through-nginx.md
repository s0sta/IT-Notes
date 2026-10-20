---
id: p82
title: "How a request reaches your app through nginx"
slug: how-a-request-reaches-your-app-through-nginx
sections: [it]
topic: "Web servers, TLS & HTTP"
tags: [Nginx, Linux, WebDevelopment, DevOps, SysAdmin]
source: "LinkedIn post P82 · Linux series"
linkedin_date: 2027-04-06
design: pipeline
---

# How a request reaches your app through nginx

A user opens your website. Before your application runs a single line of code, the request passes through six stages. Each one can fail in its own way.

## Quick reference

1. **DNS lookup** — The browser turns shop.example.com into an IP address. · *A record*
2. **TCP connection** — A connection opens to port 443 on your server. · `:443`
3. **TLS handshake** — nginx shows the certificate and the link is encrypted. · `ssl_certificate`
4. **server block match** — nginx picks the site by the host name in the request. · `server_name`
5. **location and proxy_pass** — The path decides: serve a static file, or pass to the app. · `proxy_pass`
6. **App answers, nginx logs** — The app replies, nginx returns it and writes the log line. · `access.log`

## Explained

1. **DNS lookup.** The browser asks DNS for the IP address of shop.example.com. Wrong or stale records send users to the wrong server, or nowhere. `dig shop.example.com +short` shows what the world sees.

2. **TCP connection.** The browser connects to port 443 on that IP. A firewall rule, a security group or nginx not listening shows up here as a timeout or "connection refused". `ss -tlnp` shows what is listening.

3. **TLS handshake.** nginx presents the certificate from ssl_certificate. An expired certificate, a missing intermediate or a name that does not match fails here, before any HTTP is sent.

4. **server block match.** nginx reads the Host header and picks the server block whose server_name matches. If none match, the default server answers, which is why people sometimes see the wrong site.

5. **location and proxy_pass.** Inside that server block, the URL path is matched against location blocks. A static file is served directly. Everything else is passed to the application, for example a PHP-FPM socket or an app on 127.0.0.1:8000.

6. **App answers, nginx logs.** The application responds, nginx sends the response back, and writes one line to `access.log`. Errors from the app connection go to `error.log`, with messages like "upstream timed out" or "connect() failed".

> **The practical use:** when someone says "the site is down", these six stages are your checklist. `curl -v` walks through most of them in one command.

## In one line

> **Every hop can fail. Each one has a log.** Know the hop, and you know where to look.

**Follow one request**

```bash
curl -v https://shop.example.com/health
```
