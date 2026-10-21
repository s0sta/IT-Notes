---
id: p674
title: "A service blast radius report"
slug: a-service-blast-radius-report
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, IncidentResponse, Microservices, SRE, DevOps]
source: "LinkedIn post P674 · IR series"
linkedin_date: 2031-01-16
design: code
script: blast_radius.py
---

# A service blast radius report

A database fails at 03:10. The team restarts it, and by 03:40 five unrelated services are down because nobody mapped who called whom. The failure was one service; the incident was the graph.

## Quick reference

The full script is at the end of this note: `blast_radius.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 blast_radius.py /tmp/s15/bg.json payments-db --max 3
```

**Example output**

```text
BLAST 5 services depend on payments-db
PATH web -> checkout -> payments-api -> payments-db
```

## Explained

### What it does

`blast_radius.py` reads a service dependency graph and a failing service, reverses the edges, and walks every transitive dependent. It prints the count, the hop distance for each service, and the longest dependency chains. When the count is over `--max`, it exits 1, so a change that widens the radius fails the check.

### What the screen shows

The panel loads the graph, propagates depth from payments-db, then prints BLAST 5 services depend on payments-db and PATH web -> checkout -> payments-api -> payments-db.

### How to run it

`python3 blast_radius.py /tmp/s15/bg.json payments-db --max 3`. A flat object, a services object or an edge list all work. Exit 0 is within `--max`, 1 is over it, 2 is a bad graph or an unknown service. It only reads.

### The fix

Keep the dependency graph in the repository and refresh it from traces. Before you restart a shared service, run the reverse closure and warn the five dependents. Restarting is not containment; the dependents are still failing.

### Prevention

Review the graph when a service is added. An unlisted dependency is an unknown blast radius.

> **The honest caveat:** a static graph misses runtime calls through queues, DNS and shared databases. Treat the count as a floor, not a ceiling.

> **The lesson:** impact is a count of dependents, not a feeling about the failing service.

## In one line

> **Impact is a count, not a feeling.** Count the dependents before you call it contained.

**Map the dependents**

```bash
python3 blast_radius.py graph.json api
```

## Script: blast_radius.py

Download: [scripts/blast_radius.py](../scripts/blast_radius.py)

```python
#!/usr/bin/env python3
"""blast_radius.py - count the services that depend on a failing one.

When a database or an API fails, the interesting number is not its own health
check. It is how many services cannot work without it. This script reads a
service dependency graph, reverses it, and walks the dependents transitively.
It prints the count, the hop distance for each service, and the longest
dependency chains, which are the paths an incident commander has to warn.

The graph is JSON. A flat object maps a service to the services it calls:

    {"checkout": ["payments-api"], "payments-api": ["payments-db"]}

An object with a "services" key is accepted too, as is an edge list:

    {"edges": [["checkout", "payments-api"], ["payments-api", "payments-db"]]}

Edge a -> b means a depends on b. The failing service must appear in the graph.
A cycle is reported on stderr and the paths fall back to the shortest chain;
the dependent count is still exact.

Usage:
    python3 blast_radius.py graph.json payments-db
    python3 blast_radius.py graph.json payments-db --max 3
    python3 blast_radius.py graph.json payments-db --paths 5
    python3 blast_radius.py --help

CI (fail a change that widens the blast radius of a critical service):
    python3 blast_radius.py graph.json payments-db --max 3 || exit 1

Exit codes: 0 impact at or below --max, 1 impact above --max, 2 usage error or
unreadable, empty, malformed or unknown-service input.

Read-only: opens the graph, computes in memory and prints. It writes nothing,
changes nothing and makes no network call.

By s0sta.com
"""
import argparse
import json
import sys
from collections import deque

DEFAULT_MAX = 5
DEFAULT_PATHS = 3


class InputError(Exception):
    """A graph that cannot be read."""


def load_graph(path):
    """Return a dependency map from JSON, or raise InputError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        raise InputError("%s is not JSON: %s" % (path, exc))
    if not isinstance(doc, dict):
        raise InputError("%s: expected a JSON object" % path)

    if "edges" in doc:
        raw_edges = doc["edges"]
        if not isinstance(raw_edges, list):
            raise InputError("%s: edges must be a list of pairs" % path)
        graph = {}
        for index, edge in enumerate(raw_edges, start=1):
            if (not isinstance(edge, (list, tuple)) or len(edge) != 2
                    or not all(isinstance(part, str) and part.strip()
                               for part in edge)):
                raise InputError("%s: edge %d must be [service, service]"
                                 % (path, index))
            dependent, dependency = edge[0].strip(), edge[1].strip()
            graph.setdefault(dependent, [])
            if dependency not in graph[dependent]:
                graph[dependent].append(dependency)
            graph.setdefault(dependency, [])
        if not graph:
            raise InputError("%s: no edges in graph" % path)
        return graph

    if "services" in doc:
        doc = doc["services"]
    if not isinstance(doc, dict) or not doc:
        raise InputError("%s: expected a non-empty service map" % path)
    graph = {}
    for name, deps in doc.items():
        if not isinstance(name, str) or not name.strip():
            raise InputError("%s: service names must be strings" % path)
        if not isinstance(deps, list):
            raise InputError("%s: %s must map to a list" % (path, name))
        clean = []
        for dep in deps:
            if not isinstance(dep, str) or not dep.strip():
                raise InputError("%s: %s has a non-string dependency"
                                 % (path, name))
            if dep.strip() not in clean:
                clean.append(dep.strip())
        graph[name.strip()] = clean
    for deps in list(graph.values()):
        for dep in deps:
            graph.setdefault(dep, [])
    if not graph:
        raise InputError("%s: no services in graph" % path)
    return graph


def reverse_graph(graph):
    """Return dependency -> dependents."""
    reverse = {name: [] for name in graph}
    for name, deps in graph.items():
        for dep in deps:
            reverse.setdefault(dep, []).append(name)
    return reverse


def reachable(start, reverse):
    """Return {service: hops} for every transitive dependent of start."""
    seen = {}
    queue = deque([(start, 0)])
    while queue:
        node, hops = queue.popleft()
        for nxt in reverse.get(node, []):
            if nxt in seen or nxt == start:
                continue
            seen[nxt] = hops + 1
            queue.append((nxt, hops + 1))
    return seen


def longest_paths(start, nodes, reverse):
    """Return (paths, cycle) for the longest chain to every dependent.

    paths maps a dependent to the chain that starts at it and ends at start.
    A cycle in the graph is reported instead of guessed at.
    """
    indegree = {node: 0 for node in nodes}
    for node in nodes:
        for nxt in reverse.get(node, []):
            if nxt in nodes:
                indegree[nxt] += 1
    queue = deque([start])
    distance = {start: 0}
    parent = {start: None}
    processed = 0
    while queue:
        node = queue.popleft()
        processed += 1
        for nxt in reverse.get(node, []):
            if nxt not in nodes:
                continue
            if distance.get(node, 0) + 1 > distance.get(nxt, 0):
                distance[nxt] = distance[node] + 1
                parent[nxt] = node
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    cycle = processed != len(nodes)
    if cycle:
        # Fall back to the BFS parent so a cycle still yields a usable chain.
        parent = {start: None}
        queue = deque([(start, 0)])
        while queue:
            node, hops = queue.popleft()
            for nxt in reverse.get(node, []):
                if nxt not in parent:
                    parent[nxt] = node
                    queue.append((nxt, hops + 1))

    paths = {}
    for node in nodes:
        if node == start:
            continue
        chain, seen, cursor = [], set(), node
        while cursor is not None and cursor not in seen:
            chain.append(cursor)
            seen.add(cursor)
            cursor = parent.get(cursor)
        if chain and chain[-1] == start:
            paths[node] = chain
    return paths, cycle


def report(start, reverse, max_impact, max_paths):
    """Return (finding, paths, lines, cycle) for one failing service."""
    dependents = reachable(start, reverse)
    count = len(dependents)
    lines = ["BLAST %d service%s depend%s on %s"
             % (count, "" if count == 1 else "s",
                "s" if count == 1 else "", start)]
    if not count:
        lines.append("OK no downstream dependents")
        return False, [], lines, False

    for name, hops in sorted(dependents.items(), key=lambda item: (item[1], item[0])):
        lines.append("DEPENDENT %-20s %d hop%s via %s"
                     % (name, hops, "" if hops == 1 else "s",
                        parent_name(name, start, reverse, dependents)))
    paths, cycle = longest_paths(start, [start] + list(dependents), reverse)
    ordered = sorted(paths.items(), key=lambda item: -len(item[1]))
    for name, chain in ordered[:max_paths]:
        lines.append("PATH " + " -> ".join(chain))
    finding = count > max_impact
    if finding:
        lines.append("FINDING %d dependent%s %s --max %d"
                     % (count, "" if count == 1 else "s",
                        "exceeds" if count == 1 else "exceed", max_impact))
    else:
        lines.append("OK %d dependent%s within --max %d"
                     % (count, "" if count == 1 else "s", max_impact))
    return finding, ordered, lines, cycle


def parent_name(node, start, reverse, dependents):
    """Return a one-hop closer service for the DEPENDENT line."""
    for candidate, hops in dependents.items():
        if node in reverse.get(candidate, []):
            return candidate
    return start


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Count transitive dependents of a failing service (read-only).")
    parser.add_argument("graph", help="dependency graph JSON")
    parser.add_argument("service", help="the failing service")
    parser.add_argument(
        "--max", type=int, default=DEFAULT_MAX, metavar="N",
        help="exit 1 when more than N services depend on it (default: %d)"
             % DEFAULT_MAX)
    parser.add_argument(
        "--paths", type=int, default=DEFAULT_PATHS, metavar="N",
        help="print at most N critical paths (default: %d)" % DEFAULT_PATHS)
    args = parser.parse_args(argv)

    if args.max < 0:
        parser.error("--max must not be negative")
    if args.paths < 1:
        parser.error("--paths must be at least 1")

    try:
        graph = load_graph(args.graph)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2
    if args.service not in graph:
        print("ERROR %s is not in the graph" % args.service, file=sys.stderr)
        return 2

    reverse = reverse_graph(graph)
    finding, _paths, lines, cycle = report(
        args.service, reverse, args.max, args.paths)
    if cycle:
        print("NOTE cycle in graph: paths are shortest chains", file=sys.stderr)
    for line in lines:
        print(line)
    return 1 if finding else 0


if __name__ == "__main__":
    sys.exit(main())
```
