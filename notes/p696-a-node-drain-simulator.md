---
id: p696
title: "A node drain simulator"
slug: a-node-drain-simulator
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Kubernetes, IncidentResponse, SRE, Reliability]
source: "LinkedIn post P696 · IR series"
linkedin_date: 2031-03-09
design: code
script: node_drain.py
---

# A node drain simulator

The node is hot and the fix is a drain. One Deployment has no PDB headroom; another has two pods on the node. kubectl drain moves what it can and waits on the rest.

## Quick reference

The full script is at the end of this note: `node_drain.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 node_drain.py /tmp/drain.json -n node-1 -m 3
```

**Example output**

```text
ORDER web-1, web-2
FAIL 1 pod would block the drain
```

## Explained

### What it does

`node_drain.py` reads kubectl get pods,nodes,pdb -A -o json, matches each pod on the target node to its PDBs, and simulates evictions one at a time. It prints EVICT for each movable pod and BLOCK for each pod a zero PDB stops. DaemonSets are skipped, emptyDir is flagged, and capacity is checked against `--min-free`. Exit 1 means a block or capacity below the floor.

### What the screen shows

The fourteen lines map each PDB to the app label and walk the pods. The blocked fixture ends on ORDER web-1, web-2 and FAIL 1 pod would block the drain.

### How to run it

kubectl get pods,nodes,pdb -A -o json > `/tmp/drain.json`, then `python3 node_drain.py /tmp/drain.json --node node-1 --min-free 3`. It only reads the dump; the printed command carries `--dry-run=server`.

### The fix

Drain in the printed order. If a PDB blocks, scale up, wait for the new pod to become Ready, then evict. Raise `--min-free` for a small cluster; two nodes is not a capacity plan.

### Prevention

Set PDBs from the real replica count. minAvailable 2 on three replicas leaves one eviction; on two replicas it blocks every drain.

> **The honest caveat:** the simulation trusts the PDB status in the dump; a controller that has not reconciled can make the numbers stale.

> **The lesson:** a drain is a capacity change with a queue, so respect the queue.

## In one line

> **Drain one pod, not the app.** Capacity is a constraint, not a result.

**Count the headroom**

```bash
python3 node_drain.py drain.json
```

## Script: node_drain.py

Download: [scripts/node_drain.py](../scripts/node_drain.py)

```python
#!/usr/bin/env python3
"""node_drain.py - simulate a node drain before you run it.

Reads the output of `kubectl get pods,nodes,pdb -A -o json`, matches every pod
on the target node to the PodDisruptionBudgets that select it, and simulates
the eviction order one pod at a time. It prints the pods that would block, the
capacity left after the node goes, and the exact kubectl drain command with
--dry-run=server.

A drain blocks when a matching PDB has no disruptions left, when a pod has no
owner (kubectl needs --force), and when a pod uses emptyDir (kubectl needs
--delete-emptydir-data and the data is lost). DaemonSet and mirror pods are
skipped with --ignore-daemonsets. A drain fails the run when a pod would block
or when the ready schedulable node count falls below --min-free.

Usage:
    kubectl get pods,nodes,pdb -A -o json > /tmp/drain.json
    python3 node_drain.py /tmp/drain.json --node node-1
    python3 node_drain.py /tmp/drain.json --node node-1 --min-free 3
    kubectl get pods,nodes,pdb -A -o json | python3 node_drain.py - --node node-1

Cron (before a maintenance window, report only):
    0 5 * * 1 python3 /opt/s0sta/node_drain.py /etc/ir/drain.json \
      --node node-1 --min-free 3 >> /var/log/ir/drain.log 2>&1

CI (refuse a drain that would break the PDB or the capacity floor):
    python3 node_drain.py /tmp/drain.json --node node-1 --min-free 3 || exit 1

Exit codes: 0 the drain is clear, 1 a pod would block or capacity would fall
below --min-free, 2 usage error, unreadable JSON, bad object or unknown node.

Read-only: the JSON is opened for reading only. Nothing is cordoned, evicted
or drained and no kubectl command is run. The printed command carries
--dry-run=server so the API server can answer without changing the cluster;
remove that flag only after reading this plan. The status fields are a snapshot
and can lag the controllers.

By s0sta.com
"""
import argparse
import json
import sys


def die(message):
    print("ERROR " + message, file=sys.stderr)
    sys.exit(2)


def load(path):
    try:
        if path == "-":
            return json.load(sys.stdin)
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        die("%s: %s" % (path, exc.strerror or exc))
    except (ValueError, UnicodeError) as exc:
        die("%s: not valid JSON (%s)" % (path, exc))


def items_of(document):
    if isinstance(document, list):
        items = document
    elif isinstance(document, dict):
        if isinstance(document.get("items"), list):
            items = document["items"]
        else:
            items = []
            for key in ("pods", "nodes", "pdbs", "poddisruptionbudgets"):
                value = document.get(key)
                if value is None:
                    continue
                if not isinstance(value, list):
                    die("%s must be a list" % key)
                items.extend(value)
    else:
        die("the dump must be a JSON object or list")
    if not items:
        die("no Kubernetes objects in the dump")
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            die("object %d is not an object" % index)
        if not isinstance(item.get("kind"), str):
            die("object %d has no kind" % index)
    return items


def meta_of(item, label):
    metadata = item.get("metadata")
    if not isinstance(metadata, dict):
        die("%s has no metadata object" % label)
    name = metadata.get("name")
    if not isinstance(name, str) or not name.strip():
        die("%s has no name" % label)
    namespace = metadata.get("namespace") or "default"
    if not isinstance(namespace, str):
        die("%s has a bad namespace" % name)
    labels = metadata.get("labels") or {}
    if not isinstance(labels, dict):
        die("%s has bad labels" % name)
    return name.strip(), namespace, labels, metadata


def ready_of(node):
    status = node.get("status") or {}
    conditions = status.get("conditions") or []
    if not isinstance(conditions, list):
        die("%s has bad status.conditions" % node.get("metadata", {}).get("name"))
    for condition in conditions:
        if isinstance(condition, dict) and condition.get("type") == "Ready":
            return condition.get("status") == "True"
    return False


def number(value, label):
    if isinstance(value, bool):
        die("%s must be a number" % label)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    die("%s must be a number" % label)


def bound(value, total, label):
    """Return an integer bound; percentages round up like Kubernetes."""
    if isinstance(value, bool):
        die("%s must be an integer or a percentage" % label)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.endswith("%"):
        head = value[:-1]
        if head.isdigit() and total is not None:
            return (total * int(head) + 99) // 100
    die("%s must be an integer or a percentage" % label)


def allowed_of(pdb, name):
    status = pdb.get("status") or {}
    if "disruptionsAllowed" in status:
        value = status["disruptionsAllowed"]
        if isinstance(value, int) and not isinstance(value, bool):
            return max(0, value)
    spec = pdb.get("spec") or {}
    expected = status.get("expectedPods")
    current = status.get("currentHealthy")
    if expected is not None:
        expected = number(expected, "%s.status.expectedPods" % name)
    if current is not None:
        current = number(current, "%s.status.currentHealthy" % name)
    if "minAvailable" in spec:
        limit = bound(spec["minAvailable"], expected if expected is not None
                      else current, "%s.spec.minAvailable" % name)
        if current is None:
            return 0
        return max(0, current - limit)
    if "maxUnavailable" in spec:
        limit = bound(spec["maxUnavailable"], expected if expected is not None
                      else current, "%s.spec.maxUnavailable" % name)
        if expected is None or current is None:
            return 0
        return max(0, limit - (expected - current))
    return 0


def matches(selector, labels):
    if not isinstance(selector, dict):
        return False
    match_labels = selector.get("matchLabels") or {}
    expressions = selector.get("matchExpressions") or []
    if not isinstance(match_labels, dict) or not isinstance(expressions, list):
        die("a PDB selector is malformed")
    if not match_labels and not expressions:
        return False
    for key, value in match_labels.items():
        if labels.get(key) != value:
            return False
    for expression in expressions:
        if not isinstance(expression, dict):
            die("a PDB matchExpressions entry is not an object")
        key = expression.get("key")
        operator = expression.get("operator")
        values = expression.get("values") or []
        if operator == "In" and labels.get(key) not in values:
            return False
        elif operator == "NotIn" and labels.get(key) in values:
            return False
        elif operator == "Exists" and key not in labels:
            return False
        elif operator == "DoesNotExist" and key in labels:
            return False
        elif operator not in ("In", "NotIn", "Exists", "DoesNotExist"):
            die("unsupported PDB operator: %r" % operator)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Simulate a node drain against PodDisruptionBudgets and "
                    "print the safe order and the drain command.")
    parser.add_argument("dump", nargs="?", default="-",
                        help="kubectl get pods,nodes,pdb -o json; stdin when omitted")
    parser.add_argument("-n", "--node", required=True, help="node to drain")
    parser.add_argument("-m", "--min-free", type=int, default=2,
                        help="ready schedulable nodes that must remain (default 2)")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = parser.parse_args()

    if args.min_free < 0:
        die("--min-free must be zero or more")

    items = items_of(load(args.dump))
    nodes, pods, pdbs = [], [], []
    for item in items:
        kind = item["kind"]
        if kind == "Node":
            name, _, _, _ = meta_of(item, "Node")
            spec = item.get("spec") or {}
            if not isinstance(spec, dict):
                die("%s has a bad spec" % name)
            nodes.append({"name": name, "ready": ready_of(item),
                          "unschedulable": bool(spec.get("unschedulable"))})
        elif kind == "Pod":
            name, namespace, labels, metadata = meta_of(item, "Pod")
            spec = item.get("spec") or {}
            if not isinstance(spec, dict):
                die("%s has a bad spec" % name)
            node = spec.get("nodeName")
            owners = metadata.get("ownerReferences") or []
            if not isinstance(owners, list):
                die("%s has bad ownerReferences" % name)
            kinds = [owner.get("kind") for owner in owners
                     if isinstance(owner, dict)]
            volumes = spec.get("volumes") or []
            if not isinstance(volumes, list):
                die("%s has bad volumes" % name)
            annotations = metadata.get("annotations") or {}
            if not isinstance(annotations, dict):
                die("%s has bad annotations" % name)
            pods.append({
                "name": name, "namespace": namespace, "labels": labels,
                "node": node, "phase": (item.get("status") or {}).get("phase"),
                "deleting": bool(metadata.get("deletionTimestamp")),
                "daemonset": "DaemonSet" in kinds,
                "mirror": "kubernetes.io/config.mirror" in annotations,
                "bare": not owners,
                "empty_dir": any(isinstance(v, dict) and v.get("emptyDir") is not None
                                 for v in volumes),
            })
        elif kind == "PodDisruptionBudget":
            name, namespace, _, _ = meta_of(item, "PDB")
            spec = item.get("spec") or {}
            if not isinstance(spec, dict):
                die("%s has a bad spec" % name)
            pdbs.append({
                "name": name, "namespace": namespace,
                "selector": spec.get("selector") or {},
                "allowed": allowed_of(item, name),
            })
        else:
            continue

    if not nodes:
        die("the dump has no Node objects")
    target = next((node for node in nodes if node["name"] == args.node), None)
    if target is None:
        die("node %s is not in the dump" % args.node)

    on_node = [p for p in pods
               if p["node"] == args.node and p["phase"] not in ("Succeeded", "Failed")
               and not p["deleting"]]
    total = 0
    order = []
    blocked = 0
    any_daemonset = False
    any_empty = False
    for pod in sorted(on_node, key=lambda p: p["name"]):
        if pod["daemonset"]:
            any_daemonset = True
            print("SKIP %s daemonset (--ignore-daemonsets)" % pod["name"])
            continue
        if pod["mirror"]:
            print("SKIP %s mirror pod" % pod["name"])
            continue
        pod["pdbs"] = [pdb for pdb in pdbs
                       if pdb["namespace"] == pod["namespace"]
                       and matches(pdb["selector"], pod["labels"])]
        pod["headroom"] = min([pdb["allowed"] for pdb in pod["pdbs"]]
                              or [999])
        total += 1

    candidates = [p for p in on_node if not p["daemonset"] and not p["mirror"]]
    candidates.sort(key=lambda p: (p["bare"], -p["headroom"], p["name"]))

    for pod in candidates:
        if pod["bare"]:
            print("BLOCK %s bare pod, move it or add --force" % pod["name"])
            blocked += 1
            continue
        zero = [pdb for pdb in pod["pdbs"] if pdb["allowed"] <= 0]
        if zero:
            print("BLOCK %s pdb %s no disruptions allowed"
                  % (pod["name"], ",".join(pdb["name"] for pdb in zero)))
            blocked += 1
            continue
        before = [(pdb["name"], pdb["allowed"]) for pdb in pod["pdbs"]]
        for pdb in pod["pdbs"]:
            pdb["allowed"] -= 1
        order.append(pod["name"])
        if pod["pdbs"]:
            detail = ", ".join("%s:%d->%d"
                               % (name, old, pdb["allowed"])
                               for (name, old), pdb in zip(before, pod["pdbs"]))
            print("EVICT %d/%d %s pdb %s"
                  % (len(order), total, pod["name"], detail))
        else:
            print("EVICT %d/%d %s no pdb"
                  % (len(order), total, pod["name"]))

    for pod in candidates:
        if pod["empty_dir"]:
            any_empty = True
            print("WARN %s emptyDir, --delete-emptydir-data loses data"
                  % pod["name"])

    schedulable = [node for node in nodes
                   if node["ready"] and not node["unschedulable"]]
    remaining = len([node for node in schedulable if node["name"] != args.node])
    print("CAPACITY %d schedulable -> %d after the drain, min-free %d"
          % (len(schedulable), remaining, args.min_free))

    flags = []
    if any_daemonset:
        flags.append("--ignore-daemonsets")
    if any_empty:
        flags.append("--delete-emptydir-data")
    flags.append("--dry-run=server")
    print("COMMAND kubectl drain %s %s" % (args.node, " ".join(flags)))
    print("ORDER " + (", ".join(order) if order else "-"))

    low = remaining < args.min_free
    if low or blocked:
        reasons = []
        if low:
            reasons.append("capacity %d < min-free %d"
                           % (remaining, args.min_free))
        if blocked:
            reasons.append("%d pod%s would block the drain"
                           % (blocked, "" if blocked == 1 else "s"))
        print("FAIL " + ", ".join(reasons))
        return 1
    print("OK drain %s leaves %d schedulable nodes, %d eviction%s"
          % (args.node, remaining, len(order),
             "" if len(order) == 1 else "s"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
