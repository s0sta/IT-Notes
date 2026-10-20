---
id: p328
title: "The psql cheat sheet"
slug: the-psql-cheat-sheet
sections: [it]
topic: "Databases & SQL"
tags: [PostgreSQL, psql, Databases, CommandLine, DataEngineering]
source: "LinkedIn post P328 · Data series"
linkedin_date: 2028-10-31
design: cheatsheet
---

# The psql cheat sheet

You open a terminal, connect to a database you last touched six months ago, and need to know what is in it before you change anything. psql answers most of that without a browser.

## Quick reference

### Connect

```bash
psql -h db -U app -d appdb
psql "postgresql://app@db/app"
psql -l
\c appdb
\conninfo
```

### Inspect

```text
\l
\dt
\d+ orders
\di
\df
```

### Query

```text
\timing
\x auto
\watch 2
SELECT * FROM orders LIMIT 10;
\e
```

### Admin

```text
\du
\password
SELECT pg_terminate_backend(123);
VACUUM (VERBOSE) orders;
ANALYZE orders;
```

## Explained

**Connect**  
`psql -h db -U app -d appdb` opens a session; the URL form, `psql "postgresql://app@db/app"`, does the same in one string. `psql -l` lists the databases, `\c appdb` switches to one, and `\conninfo` tells you which host, port, user and database you are actually on.

**Inspect**  
The backslash commands read the system tables. \\l lists databases, `\dt` lists tables, `\d+ orders` shows the columns, indexes, constraints and storage for one table, `\di` lists indexes and `\df` lists functions. None of them change anything.

**Query**  
`\timing` turns on the duration line, `\x auto` switches to expanded output when a row is wide, and `\watch 2` re-runs the last query every two seconds. `SELECT * FROM orders LIMIT 10;` is the query you will type most, and \\e opens the last statement in your editor.

**Admin**  
`\du` lists roles, `\password` changes the current role's password, and `SELECT pg_terminate_backend(123);` ends one session by PID. `VACUUM (VERBOSE) orders;` reclaims dead rows and `ANALYZE orders;` refreshes the statistics the planner uses.

> **The honest caveat:** psql is a client, not a backup tool. \\copy moves data, but it is not pg_dump, and the backslash commands are not SQL, so they cannot go inside a migration.

> **The lesson:** learn ten backslash commands and you stop opening a GUI to answer a question the prompt already knows.

## In one line

> **The database is one prompt away.** The prompt answers most questions before a GUI finishes loading.

**Reconnect**

```bash
psql -h db -U app -d appdb
```
