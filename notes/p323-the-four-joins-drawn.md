---
id: p323
title: "The four joins, drawn"
slug: the-four-joins-drawn
sections: [it]
topic: "Databases & SQL"
tags: [SQL, PostgreSQL, Databases, DataEngineering, Joins]
source: "LinkedIn post P323 · Data series"
linkedin_date: 2028-10-19
design: explainer
---

# The four joins, drawn

A join is where two tables meet, and where the row count stops being obvious. Four shapes cover most queries you will write.

## Quick reference

### INNER JOIN

- Only pairs where the ON clause is true
- Unmatched rows disappear from both sides
- A many-to-many join can grow the result
- The default when you write JOIN

### LEFT JOIN

- Every row from the left table survives
- Unmatched right columns come back NULL
- Count left rows before and after to check
- WHERE b.id IS NULL finds the orphans

### RIGHT and FULL

- RIGHT keeps the right table, a mirror of LEFT
- FULL keeps both sides, NULL where no match
- MySQL has no FULL OUTER JOIN; use UNION
- Most RIGHT JOINs read better as LEFT

### CROSS JOIN

- Every left row pairs with every right row
- n rows times m rows, with no ON clause
- Useful for date grids and test matrices
- A missing WHERE gives the same set

> **Note:** A join is a filter on pairs: the ON clause decides which pairs survive.

## Explained

**Inner and left**  
INNER JOIN keeps only the pairs where the ON clause is true; unmatched rows from either side disappear. LEFT JOIN keeps every row from the left table and fills the right columns with NULL when there is no match. Count the left rows before and after, or add WHERE b.id IS NULL to find the ones that never matched.

**Right and full**  
RIGHT JOIN is the mirror of LEFT: every right row survives. Most people rewrite it as a LEFT JOIN with tables swapped, because the reading order then matches the data flow. FULL JOIN keeps both sides and puts NULLs wherever a match is missing. MySQL has no FULL OUTER JOIN, so there you union a LEFT and a RIGHT.

**Cross**  
CROSS JOIN pairs every left row with every right row: n times m rows, with no ON clause. It is the right tool for a date grid or a test matrix, and the wrong tool by accident. FROM a, b with no WHERE is the same set.

> **The honest caveat:** a join does not filter rows in place; it builds pairs first. A missing or too-wide ON clause multiplies the result before any WHERE runs, which is how a report grows from 200 rows to 2 million.

> **The lesson:** draw the Venn diagram, then count the rows; the picture and the count disagree more than you think.

## In one line

> **The ON clause decides the rows.** A join multiplies rows before it filters them, so the count is the first check.

**See the plan**

```sql
EXPLAIN SELECT * FROM a JOIN b USING (id);
```
