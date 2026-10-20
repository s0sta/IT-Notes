---
id: p168
title: "A zero-downtime database migration"
slug: a-zero-downtime-database-migration
sections: [it, devsecops]
topic: "Databases & SQL"
tags: [Databases, DevOps, SRE, Migration, CloudComputing]
source: "LinkedIn post P168 · IT series"
linkedin_date: 2027-10-24
design: timeline
---

# A zero-downtime database migration

Changing a database schema on a live system sounds scary because the naive way, altering a column in place, locks tables and breaks the running app. The safe way is a sequence that never requires downtime. It is called expand and contract.

## Quick reference

| Time | Step | What happens |
|:--|:--|:--|
| **Step 1** | Add, do not change | Add the new column or table. Nothing reads it yet. |
| **Step 2** | Write to both | Deploy code that writes old and new side by side. |
| **Step 3** | Backfill | Copy existing rows into the new shape, in batches. |
| **Step 4** | Read from new | Switch reads to the new column, still writing both. |
| **Step 5** | Stop writing old | Once new is trusted, drop the old writes. |
| **Step 6** | Clean up | Remove the old column, long after the switch. |

## Explained

Step 1, add, do not change. Add the new column or table alongside the old one. Nothing reads it yet, so this change is invisible and safe. Crucially, you never rename or retype a column in place while code depends on it.

Step 2, write to both. Deploy application code that writes to both the old and the new column at once. Now every new row is correct in both shapes, and the old code still works because the old column is still there.

Step 3, backfill. Copy the existing rows into the new shape, in small batches so you do not lock the table or overload the database. This can run for hours in the background without anyone noticing.

Step 4, read from new. Switch the application to read from the new column, while still writing to both. If something is wrong, you can switch reads back instantly.

Step 5, stop writing old. Once the new column is trusted in production, remove the code that writes the old one.

Step 6, clean up. Much later, when you are certain nothing depends on it, drop the old column.

The principle: expand the schema, migrate the data and traffic gradually, then contract. Each step is independently deployable and reversible, so there is never a moment where a rollback breaks.

## In one line

> **Expand, migrate, then contract.** Never change a column in place on a live database.

**The pattern:** add -> dual-write -> backfill -> switch -> drop
