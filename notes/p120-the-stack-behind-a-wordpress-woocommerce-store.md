---
id: p120
title: "The stack behind a WordPress / WooCommerce store"
slug: the-stack-behind-a-wordpress-woocommerce-store
sections: [it]
topic: "Web servers, TLS & HTTP"
tags: [WooCommerce, WordPress, WebPerformance, Linux, Ecommerce]
source: "LinkedIn post P120 · Linux + IT series"
linkedin_date: 2027-07-04
design: stack
---

# The stack behind a WordPress / WooCommerce store

I look after a bilingual WooCommerce store with about 1,400 products. When someone says the site is slow, the useful question is always: which layer? A typical store runs on six of them.

## Quick reference

*Bottom to top: each layer can be the slow one*

1. **Server or VM** — CPU, RAM and fast NVMe disks. The foundation. · `4 vCPU / 8 GB`
2. **Linux** — Updates, firewall, time sync, enough free disk. · *Ubuntu LTS*
3. **nginx** — TLS, static files, compression, page cache. · `nginx`
4. **PHP-FPM** — Runs WordPress. Workers and OPcache matter. · `pm.max_children`
5. **MariaDB / MySQL** — Orders, products, sessions. Tune the buffer pool. · `buffer_pool`
6. **WordPress + Woo** — Theme, plugins and an object cache like Redis. · *Redis cache*

## Explained

L1, server or VM. CPU, memory and disk speed. If the server is out of RAM or the disk is slow, nothing above it can be fast. uptime, `free -h` and `df -h` are the first check.

L2, Linux. Security updates, a firewall, correct time, and free disk space. A full disk breaks sessions, uploads and the database at the same moment.

L3, nginx. Handles TLS, serves images, CSS and JavaScript directly, compresses responses, and can cache full pages for visitors who are not logged in. Static files should never reach PHP.

L4, PHP-FPM. Runs WordPress itself. pm.max_children decides how many requests can run at once. Too few and visitors queue during busy hours. Too many and the server runs out of memory. OPcache should always be on.

L5, MariaDB or MySQL. Products, orders, customers and sessions all live here. innodb_buffer_pool_size should be large enough to keep the active data in memory, and the slow query log shows which queries and plugins hurt.

L6, WordPress and WooCommerce. The theme, the plugins, and an object cache like Redis that saves repeated database queries. One badly written plugin can slow every page.

The method that works: measure from the bottom up. Server resources, then nginx and PHP-FPM logs, then slow queries, then plugins. Fix the slowest layer first.

## In one line

> **Slow is a layer, not a mystery.** Find the layer first. Then tune that one.

**Start at the bottom**

```bash
uptime; free -h; df -h
```
