---
id: p332
title: "PostgreSQL architecture, drawn"
slug: postgresql-architecture-drawn
sections: [it]
topic: "Databases & SQL"
tags: [PostgreSQL, Databases, Architecture, SRE, DataEngineering]
source: "LinkedIn post P332 · Data series"
linkedin_date: 2028-11-09
design: architecture
---

# PostgreSQL architecture, drawn

A slow query is rarely one process. PostgreSQL splits the work across a supervisor, a process per connection, and a few background workers that all write the same files.

## Quick reference

- **Tier 1 · Client:** Application (APP) · Connection pooler (POOL)
- **Tier 2 · Processes:** Postmaster (POST) · Backend process (BACK) · WAL writer (WAL) · Checkpointer (CKPT)
- **Tier 3 · Storage:** Heap files (HEAP) · WAL segments (WAL) · WAL archive (ARCH)

**Request flow:** Application → Connection pooler → Postmaster → Backend process → WAL writer → WAL segments → WAL archive; Backend process → Heap files; Checkpointer → Heap files

## Explained

**Client**  
The application opens a connection, and a pooler keeps a small set of server connections warm. PostgreSQL forks a backend process per connection, so each idle connection still costs memory; the pooler exists to stop that cost growing with every application worker.

**Processes**  
The postmaster listens on the port and forks a backend for each client. The backend parses, plans and executes the query, reads pages through shared buffers, and writes WAL buffers before the change reaches the heap. The WAL writer flushes those buffers into WAL segments. The checkpointer writes dirty shared buffers back to the data files and updates the control file.

**Storage**  
Heap files hold table pages in 8 kB blocks, and indexes live in their own files. WAL segments hold the redo stream, 16 MB each by default, and the WAL archive keeps completed segments for point-in-time recovery and for rebuilding a standby. The archive is written by archive_command, not by the checkpointer.

> **The honest caveat:** a transaction-mode pooler breaks session state such as advisory locks and SET, so use session mode when the application depends on it.

> **The lesson:** every query is a process reading pages and writing WAL, and durability is the WAL reaching disk.

## In one line

> **Processes write, WAL decides.** The diagram is a hierarchy of processes over two kinds of file.

**Check the archiver**

```sql
SELECT * FROM pg_stat_archiver;
```
