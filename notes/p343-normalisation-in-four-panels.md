---
id: p343
title: "Normalisation in four panels"
slug: normalisation-in-four-panels
sections: [it]
topic: "Databases & SQL"
tags: [SQL, DatabaseDesign, DataModelling, PostgreSQL, Backend]
source: "LinkedIn post P343 · Data series"
linkedin_date: 2028-12-05
design: explainer
---

# Normalisation in four panels

The table has one column holding three phone numbers, and the reporting query has to split them on every run. That column is the first normal form problem, and it is the easiest one to see.

## Quick reference

### 1NF - Atomic columns

- One value per cell, no lists in a column
- A repeating group becomes its own table
- Each row needs a key you can point at
- Split the phone numbers before the query does

### 2NF - No partial keys

- Only matters with a composite key
- Every non-key column needs the whole key
- A column that needs half the key moves out
- Order lines depend on order and product

### 3NF - No transitive deps

- Non-key columns depend on the key alone
- A city stored next to a postcode is a dependency
- Move the lookup to its own table
- One fact, one place, one row to update

### When to denormalise

- After a measured query, never before
- Copy a column to remove a join on a hot read
- Accept the write cost and the drift risk
- Write down the rule that keeps the copy true

> **Note:** Normal forms describe a fact once. Denormalising copies it back on purpose.

## Explained

**First normal form**  
Every cell holds one value. No comma-separated list, no repeating group, no array stuffed into a text column. A repeating group becomes its own table with one row per value, and every row gets a key so you can point at it later.

**Second normal form**  
This one only applies when the key is composite. Every non-key column must depend on the whole key, not half of it. If a column depends on the order id alone when the key is order id plus product id, it belongs in the order table.

**Third normal form**  
No transitive dependency: a non-key column must not depend on another non-key column. The postcode determines the city, so storing both in the orders table means two rows can disagree about the same city. Move the pair to a lookup table and keep the postcode as the reference.

**When to denormalise**  
After a measured query, copy a column or keep a summary table to remove a join. You pay on every write and you own the drift.

> **The honest caveat:** normal forms are a design discipline, not a performance plan. A fully normalised schema is still slow if the indexes and the statistics are wrong.

> **The lesson:** normalise until the model is honest, then denormalise only where a query proves it.

## In one line

> **Normalise first, then measure.** Denormalise for a query you have timed, never for a feeling.

**Find the duplicate**

```bash
pg_dump --schema-only db | grep -c city
```
