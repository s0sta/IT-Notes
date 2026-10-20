---
id: p121
title: "Fix: MySQL Too many connections"
slug: fix-mysql-too-many-connections
sections: [it]
topic: "Databases & SQL"
tags: [MySQL, MariaDB, Databases, Linux, Troubleshooting]
source: "LinkedIn post P121 · Linux + IT series"
linkedin_date: 2027-07-06
design: steps
---

# Fix: MySQL Too many connections

ERROR 1040: Too many connections. The database server is running, but the website, the app and even you cannot connect. Here is how to get back in and find the cause.

## Quick reference

### Diagnose — Who is using the connections?

```sql
# The limit. The default is only 151.
SHOW VARIABLES LIKE 'max_connections';
# Every connection: user, host, state and query.
SHOW FULL PROCESSLIST;
# How many right now. Watch it over time.
SHOW STATUS LIKE 'Threads_connected';
```

### Fix — Get the app connecting again

```sql
# End a stuck long query that holds everything up.
KILL 48213;
# Raise the limit now. Check memory first.
SET GLOBAL max_connections = 300;
# Also in my.cnf, or it resets on restart.
max_connections = 300
```

### Prevent — Find the real cause

- **Many Sleep connections?** — The app opens connections and never closes them.
- `wait_timeout = 300` — Close idle connections after 5 minutes.
- **Use a connection pool** — Reuse a few connections instead of hundreds.

## Explained

One useful detail first: MySQL keeps one extra connection for an account with admin rights, so root can usually still log in when everyone else is refused.

### Diagnose

SHOW VARIABLES LIKE 'max_connections' shows the limit. The default is only 151, which a busy application can reach quickly.  
SHOW FULL PROCESSLIST lists every connection: user, host, how long it has been there, and its query. Hundreds in Sleep state point to the application. A few long queries with everything else waiting point to a slow query or a lock.  
SHOW STATUS LIKE 'Threads_connected' gives the current count. Watching it over time shows whether it climbs steadily, which is a leak, or spikes with traffic.

### Fix

KILL 48213 ends a stuck query that is holding locks and making every other connection wait.  
SET GLOBAL `max_connections = 300` raises the limit immediately, without a restart. Every connection uses memory, so check you have room first.  
`max_connections = 300` in my.cnf, otherwise the setting is lost on the next restart.

### Prevent

Many Sleep connections means the application opens connections and does not close them, or keeps far too many open. That is a code or configuration fix, not a database one.  
`wait_timeout = 300` closes idle connections after five minutes instead of the default eight hours.  
A connection pool lets the application reuse a small number of connections instead of opening a new one per request.

Raising the limit buys time. Finding out who holds the connections fixes it.

## In one line

> **More connections is not the fix.** Find out who holds them, and why they never let go.

**The first look**

```bash
mysql -e 'SHOW FULL PROCESSLIST'
```
