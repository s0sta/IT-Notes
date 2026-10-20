#!/usr/bin/env python3
"""plan_diff.py - compare two PostgreSQL EXPLAIN (FORMAT JSON) plans.

Reads the saved output of EXPLAIN (FORMAT JSON) and reports what changed:
the node types in order, the root Total Cost and the root Plan Rows. A node
type change is reported but does not fail the run. The new plan is worse when
its root cost is over --cost-factor times the old cost, or its root row
estimate is over --row-factor times the old estimate; then the exit code is 1
so a CI job can fail on the regression.

Read-only: it opens two files and writes nothing.

Exit codes: 0 clean or unchanged, 1 the new plan is worse, 2 usage or input
error (missing file, invalid JSON, or not an EXPLAIN array).

Usage:
    psql -c "EXPLAIN (FORMAT JSON) SELECT * FROM orders WHERE id = 1" -o old.json
    psql -c "EXPLAIN (FORMAT JSON) SELECT * FROM orders WHERE id = 1" -o new.json
    python3 plan_diff.py old.json new.json
    python3 plan_diff.py old.json new.json --cost-factor 1.5
    python3 plan_diff.py old.json new.json --row-factor 3
    python3 plan_diff.py old.json new.json --json

CI, fail the job when the new plan regresses:
    python3 plan_diff.py old.json new.json || exit 1

By s0sta.com
"""
import argparse
import json
import sys


class PlanError(Exception):
    """Anything that should end the run with exit code 2."""


def load_plan(path):
    """Load the root Plan object from one EXPLAIN (FORMAT JSON) file."""
    try:
        with open(path) as fh:
            doc = json.load(fh)
    except OSError as exc:
        raise PlanError("cannot read %s: %s" % (path, exc))
    except ValueError as exc:
        raise PlanError("%s is not JSON: %s" % (path, exc))
    if isinstance(doc, list):
        if len(doc) != 1 or not isinstance(doc[0], dict):
            raise PlanError("%s is not an EXPLAIN array with one object" % path)
        doc = doc[0]
    if not isinstance(doc, dict) or "Plan" not in doc:
        raise PlanError("%s has no Plan object" % path)
    plan = doc["Plan"]
    if not isinstance(plan, dict):
        raise PlanError("%s: Plan is not an object" % path)
    return plan


def check_node(plan):
    """Reject a plan node that is missing the fields or types we need."""
    if not isinstance(plan.get("Node Type"), str):
        raise PlanError("a plan node has no string Node Type")
    for key in ("Total Cost", "Plan Rows"):
        value = plan.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise PlanError("a plan node has no numeric %r" % key)


def walk(plan, out):
    """Append (node type, total cost, plan rows) for every node, in order."""
    check_node(plan)
    out.append((plan["Node Type"], plan["Total Cost"], plan["Plan Rows"]))
    children = plan.get("Plans", [])
    if not isinstance(children, list):
        raise PlanError("a plan node has a non-list Plans value")
    for child in children:
        if not isinstance(child, dict):
            raise PlanError("a Plans entry is not an object")
        walk(child, out)
    return out


def pct(old, new):
    """Percentage change, or n/a when the old value is zero."""
    if old == 0:
        return "n/a"
    return "%+.1f%%" % ((new - old) / old * 100.0)


def compare(old_path, new_path, cost_factor, row_factor):
    """Build the report dictionary for two plan files."""
    old_root = load_plan(old_path)
    new_root = load_plan(new_path)
    old_nodes = walk(old_root, [])
    new_nodes = walk(new_root, [])

    old_cost, old_rows = old_root["Total Cost"], old_root["Plan Rows"]
    new_cost, new_rows = new_root["Total Cost"], new_root["Plan Rows"]
    cost_worse = new_cost > old_cost * cost_factor
    row_worse = new_rows > old_rows * row_factor

    old_types = [node[0] for node in old_nodes]
    new_types = [node[0] for node in new_nodes]
    changes = []
    for i, (a, b) in enumerate(zip(old_types, new_types)):
        if a != b:
            changes.append({"position": i + 1, "old": a, "new": b})
    return {
        "old_file": old_path,
        "new_file": new_path,
        "old_nodes": old_types,
        "new_nodes": new_types,
        "node_count": [len(old_types), len(new_types)],
        "changes": changes,
        "old_cost": old_cost,
        "new_cost": new_cost,
        "old_rows": old_rows,
        "new_rows": new_rows,
        "cost_factor": cost_factor,
        "row_factor": row_factor,
        "cost_worse": cost_worse,
        "row_worse": row_worse,
        "worse": cost_worse or row_worse,
    }


def print_report(rep):
    """The human-readable report."""
    print("PLAN DIFF  %s -> %s" % (rep["old_file"], rep["new_file"]))
    print("NODES      %d -> %d" % (rep["node_count"][0], rep["node_count"][1]))
    for change in rep["changes"][:10]:
        print("CHANGED    node %d: %s -> %s"
              % (change["position"], change["old"], change["new"]))
    if len(rep["changes"]) > 10:
        print("CHANGED    ... and %d more" % (len(rep["changes"]) - 10))
    if not rep["changes"]:
        print("CHANGED    none")
    print("COST       %.2f -> %.2f  (%s)"
          % (rep["old_cost"], rep["new_cost"],
             pct(rep["old_cost"], rep["new_cost"])))
    print("ROWS       %.0f -> %.0f  (%s)"
          % (rep["old_rows"], rep["new_rows"],
             pct(rep["old_rows"], rep["new_rows"])))
    if rep["worse"]:
        reasons = []
        if rep["cost_worse"]:
            reasons.append("cost over %.2fx" % rep["cost_factor"])
        if rep["row_worse"]:
            reasons.append("rows over %.2fx" % rep["row_factor"])
        print("VERDICT    WORSE (%s)" % ", ".join(reasons))
    else:
        print("VERDICT    OK (within %.2fx cost and %.2fx rows)"
              % (rep["cost_factor"], rep["row_factor"]))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Compare two PostgreSQL EXPLAIN (FORMAT JSON) plans.",
        epilog="Exit codes: 0 clean, 1 the new plan is worse, 2 usage or input error.")
    parser.add_argument("old", help="old plan JSON file")
    parser.add_argument("new", help="new plan JSON file")
    parser.add_argument("--cost-factor", type=float, default=1.2, metavar="X",
                        help="fail when new cost is over X times the old cost (default 1.2)")
    parser.add_argument("--row-factor", type=float, default=2.0, metavar="X",
                        help="fail when new rows are over X times the old rows (default 2.0)")
    parser.add_argument("--json", action="store_true", help="print one JSON report")
    args = parser.parse_args(argv)

    if args.cost_factor <= 0 or args.row_factor <= 0:
        parser.error("--cost-factor and --row-factor must be positive")
    try:
        rep = compare(args.old, args.new, args.cost_factor, args.row_factor)
    except PlanError as exc:
        print("ERR %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(rep, indent=2, sort_keys=True))
    else:
        print_report(rep)
    return 1 if rep["worse"] else 0


if __name__ == "__main__":
    sys.exit(main())
