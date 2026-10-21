---
id: p477
title: "The edge path"
slug: the-edge-path
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [CDN, Networking, CloudArchitecture, DevOps, Security]
source: "LinkedIn post P477 · Network series"
linkedin_date: 2029-10-14
design: architecture
---

# The edge path

A user types a name and a page appears. Between those two events sit three tiers, and each one can add latency, cost or a failure mode.

## Quick reference

- **Client:** Browser (WEB) · DNS resolver (DNS)
- **Edge:** CDN edge (CDN) · WAF (WAF)
- **Origin:** Load balancer (LB) · Application (APP)

**Request flow:** DNS resolver → Browser → CDN edge → WAF → Load balancer → Application

## Explained

### Client

The browser starts with DNS. It asks the resolver, which answers with an address and a TTL. Then it connects to the edge, not to your origin. The first lookup and the round trip to the nearest point of presence bound everything the client does.

### Edge

The CDN terminates TLS near the user, looks up the object in its cache and answers a hit without touching your network. On a miss it forwards to the origin through a persistent connection. The WAF sits in the same path, inspecting the request before it passes; a block here never reaches the load balancer.

### Origin

The load balancer receives the request, picks a healthy target and opens or reuses a connection to the application. The application does the work and returns the response, which the CDN may cache for the next user.

### The path in order

Browser, resolver, CDN, WAF, load balancer, application. Every arrow is a place to measure. A long DNS TTL slows a failover; a broad WAF rule blocks a checkout; a shallow health check sends traffic to a dead app.

> **The honest caveat:** the edge only helps what it can cache or terminate. A personalised POST still crosses the whole path, and a wrong TTL can serve stale content.

> **The lesson:** draw the path, then measure each arrow on it.

## In one line

> **The shortest path is the edge.** Every hop you remove is a hop that cannot fail.

**Check the edge**

```bash
curl -sI https://example.com
```
