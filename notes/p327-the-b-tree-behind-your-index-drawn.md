---
id: p327
title: "The B-tree behind your index, drawn"
slug: the-b-tree-behind-your-index-drawn
sections: [it]
topic: "Databases & SQL"
tags: [SQL, PostgreSQL, Databases, Indexes, Performance]
source: "LinkedIn post P327 · Data series"
linkedin_date: 2028-10-29
design: architecture
---

# The B-tree behind your index, drawn

An index lookup feels like magic: one key in, one row out, even in a table with fifty million rows. Underneath, it is a small tree of pages and a short walk down.

## Quick reference

- **Root:** meta page (META) · root page (ROOT)
- **Internal:** internal page (INNER) · separator keys (KEY) · downlinks (PTR)
- **Leaf:** leaf page (LEAF) · row pointers (TID) · heap files (HEAP)

**Request flow:** meta page → root page → internal page → separator keys → downlinks → leaf page → row pointers → heap files

## Explained

**Root and internal**  
Block 0 of a PostgreSQL B-tree index is the metapage; it stores the root block number and the tree level. The root page is a B-tree page like any other. Below it, each internal page holds separator keys and downlinks: compare your key with the separators, follow one downlink, and repeat at the next level.

**Leaf**  
Leaf pages hold the index tuples in key order: the key and a row pointer, the six-byte address of the heap row. The leaves are also linked left and right, which is what makes a range scan cheap: find the first key, then walk the leaf chain. The heap files hold the actual rows, and an index-only scan still has to check visibility.

**Why it matters**  
Fanout is the trick. A page holds hundreds of keys, so three or four levels cover millions of rows. One lookup reads one page per level, usually three or four pages, instead of scanning the table.

> **The honest caveat:** PostgreSQL's B-tree is a Lehman-Yao variant with high keys and sibling links, not the textbook B+tree. The search shape is the same; the details are not.

> **The lesson:** the index is small because each page points to many others; the tree is shallow for the same reason.

## In one line

> **Down the tree, then to the heap.** The tree stays shallow because every page points to many others.

**See the depth**

```sql
SELECT * FROM bt_metap('idx');
```
