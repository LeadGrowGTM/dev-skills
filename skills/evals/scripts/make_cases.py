#!/usr/bin/env python3
"""Write reviewed proposals into eval cases. Run only after a human has reviewed proposed.jsonl.

The first --per-group cases (by slug) of each (expect, split) pair get the smoke tag.

  make_cases.py [--plugin DIR] [--per-group 4] [PROPOSED.jsonl]
"""
import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from new_case import split_for, write_case  # noqa: E402


def build(plugin, rows, per_group=4):
    counts = collections.Counter()
    written = skipped = 0
    for r in sorted(rows, key=lambda r: r["slug"]):
        key = (r["expect"], split_for(r["slug"]))
        try:
            write_case(plugin, r["slug"], r["prompt"], r["expect"],
                       tags=[f"src-{r['source']}"], smoke=counts[key] < per_group)
        except FileExistsError:
            skipped += 1
            continue
        counts[key] += 1
        written += 1
    return written, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plugin", default=".")
    ap.add_argument("--per-group", type=int, default=4)
    ap.add_argument("proposed", nargs="?")
    a = ap.parse_args()
    path = Path(a.proposed or Path(a.plugin) / "evals/mine-out/proposed.jsonl")
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    print("written %d, skipped %d" % build(a.plugin, rows, a.per_group))


if __name__ == "__main__":
    main()
