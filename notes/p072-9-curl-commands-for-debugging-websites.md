---
id: p72
title: "9 curl commands for debugging websites"
slug: 9-curl-commands-for-debugging-websites
sections: [it]
topic: "Web servers, TLS & HTTP"
tags: [Linux, curl, WebDevelopment, SysAdmin, Troubleshooting]
source: "LinkedIn post P72 · Linux series"
linkedin_date: 2027-03-14
design: terminal
---

# 9 curl commands for debugging websites

When a website misbehaves, the browser hides most of the story. curl shows all of it. Nine commands I would teach anyone who runs a website.

## Quick reference

### What did the server answer?

```bash
# -I: headers only. Status code and redirects at a glance
curl -I https://shop.example.com
# only the final status code. -L follows redirects
curl -sL -o /dev/null -w '%{http_code}\n' https://shop.example.com
# -v: connection, TLS and every header, step by step
curl -v https://shop.example.com
```

### Where is the time going?

```bash
# total time in seconds
curl -so /dev/null -w '%{time_total}\n' https://shop.example.com
# time to first byte. High means a slow backend
curl -so /dev/null -w '%{time_starttransfer}\n' https://shop.example.com
# fail fast instead of hanging forever
curl --connect-timeout 5 -m 10 https://api.example.com
```

### Test before DNS, with auth, without a UI

```bash
# test the new server before you change DNS
curl -I --resolve shop.example.com:443:203.0.113.20 https://shop.example.com
# send any header: tokens, Host, User-Agent
curl -H "Authorization: Bearer $TOKEN" https://api.example.com/me
# test a form or API call without the frontend
curl -X POST -d 'sku=BA-101' https://api.example.com/cart
```

## Explained

### What did the server answer?

- `curl -I https://shop.example.com` — headers only. You see the status code, redirects, cache headers and the server in one screen.
- `curl -sL -o /dev/null -w '%{http_code}\n' URL` — just the final status code after following redirects. Perfect for scripts and health checks.
- `curl -v URL` — the full conversation: which IP it connected to, the TLS handshake, every request and response header.

### Where is the time going?

- `curl -so /dev/null -w '%{time_total}\n' URL` — the total time of the request, in seconds.
- `curl -so /dev/null -w '%{time_starttransfer}\n' URL` — time to first byte. If this is high and the rest is fast, the network is fine and the backend is slow.
- `curl --connect-timeout 5 -m 10 URL` — give up after 5 seconds to connect and 10 seconds in total. Scripts should fail fast, not hang.

### Test before DNS, with auth, without a UI

- `curl -I --resolve shop.example.com:443:203.0.113.20 URL` — send the request to a new server IP while keeping the real host name. Test a migration before you change DNS.
- `curl -H "Authorization: Bearer $TOKEN" URL` — send any header you need: API tokens, a Host header, a User-Agent.
- `curl -X POST -d 'sku=BA-101' URL` — test a form or an API call directly, without clicking through the frontend.

> **One honest caveat:** -I sends a HEAD request, and a few apps answer HEAD differently from GET. If the result looks strange, compare with -v.

## In one line

> **Read the response, not the page.** The answer is in the headers more often than you think.

**Try it**

```bash
curl -sI https://shop.example.com | head -1
```
