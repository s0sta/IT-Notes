---
id: p324
title: "The SQL cheat sheet"
slug: the-sql-cheat-sheet
sections: [it]
topic: "Databases & SQL"
tags: [SQL, PostgreSQL, Databases, DataEngineering, CheatSheet]
source: "LinkedIn post P324 · Data series"
linkedin_date: 2028-10-22
design: cheatsheet
---

# The SQL cheat sheet

You know SQL until someone asks for a running total, a top row per group, or the difference between LEFT and FULL. The syntax is small; the habits are not.

## Quick reference

### Select

```sql
SELECT id, email FROM users LIMIT 10;
SELECT * FROM orders WHERE total > 100;
SELECT DISTINCT country FROM users;
SELECT count(*) FROM orders;
SELECT id, email FROM users ORDER BY id;
```

### Join

```sql
SELECT * FROM a JOIN b ON a.id = b.id;
SELECT * FROM a LEFT JOIN b USING (id);
SELECT * FROM a FULL JOIN b USING (id);
SELECT * FROM a CROSS JOIN b;
SELECT * FROM a JOIN b ON TRUE;
```

### Group

```sql
SELECT c, count(*) FROM t GROUP BY c;
SELECT a,b,count(*) FROM t GROUP BY a,b;
SELECT c, sum(x) FROM t GROUP BY c;
SELECT c, avg(x) FROM t GROUP BY c;
SELECT c, max(ts) FROM t GROUP BY c;
```

### Window

```sql
SELECT sum(x) OVER (ORDER BY id) FROM t;
SELECT rank() OVER (ORDER BY x) FROM t;
SELECT lag(x) OVER (ORDER BY id) FROM t;
SELECT count(*) OVER () FROM t;
SELECT row_number() OVER () FROM t;
```

## Explained

**Select**  
Start with five statements: `SELECT id, email FROM users LIMIT 10;` `SELECT * FROM orders WHERE total > 100;` `SELECT DISTINCT country FROM users;` `SELECT count(*) FROM orders;` and the same select with ORDER BY id. They cover the shape of a read.

**Join**  
The join block is four shapes and one trick: INNER JOIN with ON, LEFT JOIN with USING (id), FULL JOIN with USING (id), CROSS JOIN, and JOIN b ON TRUE, which is a cross join in disguise. USING (id) needs the same column name on both sides.

**Group**  
GROUP BY collapses rows into groups. `SELECT c, count(*) FROM t GROUP BY c;` counts them, sum and avg add and average a numeric column, and GROUP BY a,b groups on a pair. Every selected column is either grouped or aggregated.

**Window**  
A window function keeps the rows and adds a value over a frame. sum(x) OVER (ORDER BY id) is a running total, rank() numbers ties the same, lag(x) reaches the previous row, and count(\*) OVER () totals every row.

> **The honest caveat:** the cheat sheet is PostgreSQL syntax. USING, FILTER and window functions are widely supported, but the clause order in your engine may differ, and a window cannot go in WHERE.

> **The lesson:** the clause order is fixed, so learn the shape and the words stop mattering.

## In one line

> **Describe the rows, not the steps.** The clause order is fixed; the words are the only thing that changes.

**See the shape**

```sql
EXPLAIN (FORMAT JSON) SELECT 1;
```
