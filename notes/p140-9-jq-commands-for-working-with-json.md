---
id: p140
title: "9 jq commands for working with JSON"
slug: 9-jq-commands-for-working-with-json
sections: [it, devsecops]
topic: "Linux"
tags: [jq, JSON, DevOps, CommandLine, API]
source: "LinkedIn post P140 · IT series"
linkedin_date: 2027-08-19
design: terminal
---

# 9 jq commands for working with JSON

Almost every API and cloud CLI returns JSON, and reading it by eye is painful. jq filters, reshapes and extracts it from the command line. Nine patterns cover most of what you will ever need.

## Quick reference

### Pull out what you need

```bash
# pretty-print any JSON. The first thing you run
curl -s api/users | jq '.'
# one field. jq '.user.email' goes deeper
jq '.name' user.json
# the first element of an array
jq '.items[0]' data.json
```

### Narrow it down

```bash
# one field from every array element
jq '.items[].sku' order.json
# keep only objects that match a condition
jq '.[] | select(.active)' users.json
# count elements
jq '.items | length' order.json
```

### Change the shape

```bash
# build a smaller object
jq '.items[] | {sku, qty}'  order.json
# -r: raw strings, no quotes. Great for scripts
jq -r '.users[].email' u.json
# map to numbers, then sum them
jq '[.items[].qty] | add' o.json
```

## Explained

### Read

`curl -s api/users | jq '.'` pretty-prints any JSON with colour and indentation. The first thing to run on an ugly response.  
`jq '.name' user.json` pulls one field. Go deeper with jq '.user.email', and quote keys with spaces or dashes as jq '.["content-type"]'.  
`jq '.items[0]' data.json` gets the first element of an array.

### Filter

`jq '.items[].sku' order.json` pulls one field from every element of an array. The [] means "for each".  
`jq '.[] | select(.active)' users.json` keeps only the objects where a condition is true. select is how you filter.  
`jq '.items | length' order.json` counts the elements. Simple and constantly useful.

### Reshape

jq '.items[] | {sku, qty}' `order.json` builds a smaller object with only the fields you care about.  
`jq -r '.users[].email' u.json` prints raw strings without the surrounding quotes. Essential when feeding the output into a loop or another command.  
jq '[.items[].qty] | add' `order.json` collects all the quantities into an array and sums them. jq does maths too.

The mental model: jq is a pipeline, like the shell. Each filter transforms the JSON and passes it to the next, separated by |.

JSON becomes readable, and scriptable.

## In one line

> **JSON becomes readable.** One tool turns API noise into the one value you wanted.

**Try it**

```bash
curl -s api/health | jq .
```
