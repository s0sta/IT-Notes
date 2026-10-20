---
id: p337
title: "Isolation levels and the anomalies they stop"
slug: isolation-levels-and-the-anomalies-they-stop
sections: [it]
topic: "Databases & SQL"
tags: [Databases, SQL, PostgreSQL, Transactions, DataEngineering]
source: "LinkedIn post P337 · Data series"
linkedin_date: 2028-11-21
design: explainer
---

# Isolation levels and the anomalies they stop

Two sessions read the same row and both are sure they are right. Isolation levels say which of them may be surprised, and the fourth panel is its bill.

## Quick reference

### Dirty read

- One transaction reads an uncommitted row
- The writer rolls back and the row never existed
- Stopped by READ COMMITTED and above
- PostgreSQL never allows it at all

### Non-repeatable read

- You read a row, then someone commits an update
- The same SELECT returns a different value
- READ COMMITTED takes a new snapshot per statement
- REPEATABLE READ holds one snapshot throughout

### Phantom read

- A re-run query returns rows that were not there
- Another transaction inserted and committed a match
- PostgreSQL REPEATABLE READ stops it with a snapshot
- InnoDB uses next-key locks for locking reads

### Serialization failure

- SERIALIZABLE checks whether the order was possible
- A dangerous cycle aborts one transaction with 40001
- The fix is a retry, not a longer timeout
- It replaces a wrong answer with a visible failure

> **Note:** SERIALIZABLE is the level that refuses to guess, and the one that asks you to retry.

## Explained

**Dirty read**  
One transaction updates a row, another reads the uncommitted value, and the first rolls back. The reader acted on a row that never existed. READ COMMITTED and above prevent it; PostgreSQL maps READ UNCOMMITTED to READ COMMITTED, so it never happens there.

**Non-repeatable read**  
You read a row, another transaction commits an update, and you read it again in the same transaction and get a different value. READ COMMITTED takes a new snapshot for each statement, so it allows this. REPEATABLE READ holds one snapshot for the whole transaction and stops it.

**Phantom read**  
You run a query, another transaction inserts a matching row and commits, and the same query returns an extra row. A snapshot at REPEATABLE READ prevents it in PostgreSQL; MySQL InnoDB uses next-key locks for locking reads and a consistent snapshot for plain SELECTs. SERIALIZABLE closes the remaining gaps.

**Serialization failure**  
The fourth panel is not an anomaly; it is what a serializable engine does when it cannot prove a safe order for two transactions. One is aborted with SQLSTATE 40001, and the correct response is to retry the transaction, not to raise the timeout.

> **The honest caveat:** PostgreSQL REPEATABLE READ is snapshot isolation, and it still allows write skew; only SERIALIZABLE prevents that class of bug.

> **The lesson:** pick the weakest level that keeps your invariants, then handle the retries the stronger one demands.

## In one line

> **Choose the level, accept the cost.** Stronger isolation does not remove the anomaly; it changes its shape.

**Check the level**

```sql
SHOW transaction_isolation;
```
