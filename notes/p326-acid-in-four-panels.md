---
id: p326
title: "ACID, in four panels"
slug: acid-in-four-panels
sections: [it]
topic: "Databases & SQL"
tags: [SQL, PostgreSQL, Databases, Transactions, DataEngineering]
source: "LinkedIn post P326 · Data series"
linkedin_date: 2028-10-26
design: explainer
---

# ACID, in four panels

A payment leaves one account and never reaches the other, and the database says the transaction committed. ACID is the four-part answer to how that is supposed to be impossible.

## Quick reference

### Atomicity - all or nothing

- A transaction is all or nothing
- Any error aborts the whole transaction
- ROLLBACK undoes every statement
- Savepoints allow a partial rollback

### Consistency - rules hold

- Constraints reject invalid rows
- NOT NULL, UNIQUE, CHECK, FOREIGN KEY
- Triggers and rules run inside the transaction
- Your application invariants are still yours

### Isolation - no interference

- Concurrent transactions cannot see uncommitted work
- READ COMMITTED is the PostgreSQL default
- SERIALIZABLE adds predicate locking (SSI)
- Higher isolation costs retries and locks

### Durability - it stays

- COMMIT returns only after the WAL is flushed
- synchronous_commit=on is the default
- fsync=off trades durability for speed
- A replica is not a substitute for a backup

> **Note:** Atomicity and durability are guarantees; isolation is the level you choose.

## Explained

**Atomicity and consistency**  
Atomicity means all or nothing: any error aborts the transaction, ROLLBACK undoes every statement, and a savepoint lets you undo part of it. Consistency means the database only moves between valid states: NOT NULL, UNIQUE, CHECK and FOREIGN KEY reject bad rows, and triggers run inside the same transaction. The invariants your application checks are still your job.

**Isolation and durability**  
Isolation keeps concurrent transactions from seeing each other's uncommitted work. READ COMMITTED is the PostgreSQL default; SERIALIZABLE adds SSI and can abort a transaction that would break a serial order. Durability means a committed change survives a crash: COMMIT returns after the WAL is flushed, synchronous_commit is on by default, and fsync=off trades that guarantee for speed.

**What it costs**  
Higher isolation means more locks or more retries. A serialisable transaction can fail with a serialisation error and must be retried, so the application needs a retry loop, not just a setting.

> **The honest caveat:** consistency in ACID is about constraints, not about your business rules. If no constraint encodes a rule, the database will happily commit a state your code calls impossible.

> **The lesson:** atomicity and durability are guarantees; isolation is a dial; consistency is only as strong as the constraints you wrote.

## In one line

> **A commit is a promise.** Atomicity and durability are guaranteed; isolation is the setting you choose.

**Check the level**

```sql
SHOW transaction_isolation;
```
