---
id: p338
title: "The Redis cheat sheet"
slug: the-redis-cheat-sheet
sections: [it]
topic: "Databases & SQL"
tags: [Redis, Databases, Caching, DevOps, DataEngineering]
source: "LinkedIn post P338 · Data series"
linkedin_date: 2028-11-23
design: cheatsheet
---

# The Redis cheat sheet

Redis is fast because it does one thing at a time, which is also why one careless command can stall every client. Four blocks cover what matters.

## Quick reference

### Keys

```text
SCAN 0 MATCH user:* COUNT 100
EXISTS user:42
TYPE user:42
DEL user:42
UNLINK user:42
```

### Strings

```sql
SET user:42:name Ada
GET user:42:name
SET lock:job 1 NX PX 30000
INCR page:views
MSET a 1 b 2
```

### Hashes

```text
HSET user:42 name Ada
HGET user:42 name
HGETALL user:42
HINCRBY user:42 logins 1
HDEL user:42 name
HSCAN user:42 0
```

### Streams/TTL

```text
XADD events * type signup
XLEN events
XREAD COUNT 10 STREAMS events 0
EXPIRE user:42 3600
TTL user:42
PERSIST user:42
```

## Explained

**Keys**  
`SCAN 0 MATCH user:* COUNT 100` walks the keyspace in slices instead of blocking on the whole thing. `EXISTS user:42` answers whether a key is there, `TYPE user:42` says what it is, DEL removes it synchronously, UNLINK removes it and frees memory in the background.

**Strings**  
`SET user:42:name Ada` stores a value, GET reads it, and `SET lock:job 1 NX PX 30000` is the atomic lock: it only writes when the key is absent and expires after thirty seconds. `INCR page:views` is atomic, and `MSET a 1 b 2` writes several keys in one round trip.

**Hashes**  
`HSET user:42 name Ada` sets a field, HGET reads one, HGETALL reads the whole hash, and `HINCRBY user:42 logins 1` increments a counter without a read-modify-write race. HDEL removes a field, and HSCAN walks a large hash in slices.

**Streams and TTL**  
`XADD events * type signup` appends an entry with an auto ID, XLEN counts entries, and `XREAD COUNT 10 STREAMS events 0` reads from the beginning. `EXPIRE user:42 3600` sets a TTL, TTL reads it, and PERSIST removes it. TTL returns -1 for no expiry and -2 for a missing key.

> **The honest caveat:** expiry is lazy and sampled, so a key can outlive its deadline slightly, and a replica waits for the primary's delete.

> **The lesson:** the command you choose is the complexity you accept; every O(N) command pauses everyone.

## In one line

> **Every command has a cost.** The single thread is the feature and the limit.

**Find the hot key**

```bash
redis-cli --bigkeys
```
