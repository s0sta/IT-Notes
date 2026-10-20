---
id: p148
title: "Anatomy of a URL"
slug: anatomy-of-a-url
sections: [it]
topic: "Web servers, TLS & HTTP"
tags: [WebDevelopment, Networking, API, DevOps, ITSupport]
source: "LinkedIn post P148 · IT series"
linkedin_date: 2027-09-07
design: anatomy
---

# Anatomy of a URL

You type and read URLs all day. Taken apart, a URL is a precise instruction, and each part tells a different system what to do.

## Quick reference

```text
https://api.example.com:8443/v2/orders?status=open#details
```

| Part | Name | What it means |
|:--|:--|:--|
| `https://` | Scheme | The protocol. https means the connection is encrypted. |
| `api.example.com` | Host | The server's name, resolved to an IP by DNS. |
| `:8443` | Port | Which service on the host. 443 for https is implied. |
| `/v2/orders` | Path | Which resource on the server you are asking for. |
| `?status=open` | Query | Parameters: filters, pages, search terms. |
| `#details` | Fragment | A spot on the page. The browser keeps it; the server never sees it. |

## Explained

https:// is the scheme, the protocol. https means the connection is encrypted with TLS; http is plain text. Other schemes exist too, like ssh:// or postgres:// in connection strings. This part decides how the client talks to the server.

`api.example.com` is the host. DNS resolves this name to an IP address so the request can be routed. This is the part that moves when you migrate servers, and the part a wrong DNS record breaks.

:8443 is the port, which service on that host to reach. It is usually hidden because 443 is implied for https and 80 for http. You only see it when a service runs somewhere non-standard.

`/v2/orders` is the path, which resource you are asking for. On an API this maps to an endpoint; on a site it maps to a page or file.

?status=open is the query string, extra parameters after the question mark. Filters, pagination, search terms and tracking tags all live here, joined by &.

\#details is the fragment. It points at a spot within the page, and crucially, the browser keeps it to itself. The server never receives the fragment, which surprises people debugging why a value never arrives.

Why it matters: when a request misbehaves, knowing which part does what tells you where to look, from DNS for the host to the query string for a missing parameter.

## In one line

> **Every part tells the server something.** Read a URL and you know exactly what is being asked.

**Inspect one**

```bash
curl -v 'https://api.example.com/v2/orders?status=open'
```
