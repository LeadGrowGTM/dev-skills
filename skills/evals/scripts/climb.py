#!/usr/bin/env python3
"""Hill-climb a plugin's skill descriptions against its smoke cases, or report a result.

  climb.py run    [--plugin DIR] [--cap 60] [--iters 5] [--model M]
  climb.py report RESULT.json

run: score the smoke cases (tag "smoke", 2 runs each) on train and hold, ask
Claude for new descriptions for the skills that failed on train, and keep them
only if hold improves and no skill's hold trigger rate drops by more than one
run. Stops after --iters, at the first rejected change, or before a pass would
cross --cap. report: per-skill rates and the spec verdict (hold trigger >= 90%,
hold clean >= 95%, no depth grader failed).
"""
import argparse
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from new_case import skills_of  # noqa: E402
from propose import claude_p_argv  # noqa: E402

PASS_COST = 10.0  # first-pass estimate only (48 smoke cases x 2 runs x ~$0.10); the loop then uses the last real pass cost
DESC = re.compile(r"^description: .*$", re.M)
YAML_BREAK = re.compile(r":(\s|$)| #")


def desc_problem(desc):
    """Why this string cannot be a one-line YAML description, or None if it can."""
    if not desc or "\n" in desc:
        return "description must be one non-empty line"
    if len(desc) > 1536:
        return f"description is {len(desc)} chars, max 1536"
    if not desc[0].isalnum():
        return "description must start with a letter or digit (YAML reads [ - ` & * ! and quotes specially)"
    if YAML_BREAK.search(desc):
        return "description contains ': ', a trailing ':' or ' #'"
    return None


def body(md):
    return md.split("\n---\n", 1)[1].strip() if md.startswith("---") and "\n---\n" in md else md.strip()


def score(result):
    out = {sp: {"trigger": defaultdict(lambda: [0, 0]), "clean": [0, 0], "fails": []} for sp in ("train", "hold")}
    for case in result["cases"]:
        o = out.get(case["name"].split("-", 1)[0])
        if o is None:
            continue
        prompt = body(case.get("promptMarkdown", ""))
        for one in case["arms"]["with"]:
            clean = True
            for g in one["graders"]:
                kind, _, skill = g["name"].partition("-")
                if kind == "fires":
                    o["trigger"][skill][0] += bool(g["passed"])
                    o["trigger"][skill][1] += 1
                    if not g["passed"]:
                        o["fails"].append({"miss": skill, "prompt": prompt})
                elif kind == "silent" and not g["passed"]:
                    clean = False
                    o["fails"].append({"false_fire": skill, "prompt": prompt})
            o["clean"][0] += clean
            o["clean"][1] += 1
    return out


def rates(split):
    hit = sum(p for p, _ in split["trigger"].values())
    n = sum(t for _, t in split["trigger"].values())
    c, runs = split["clean"]
    return (hit / n if n else 1.0), (c / runs if runs else 1.0)


def accept(old, new):
    if sum(rates(new["hold"])) <= sum(rates(old["hold"])):
        return False
    (oc, on), (nc, nn) = old["hold"]["clean"], new["hold"]["clean"]
    if on and nn and oc / on - nc / nn > 1 / on + 1e-9:
        return False  # more wrong fires is a loss even when the trigger rate rose
    for skill, (p, n) in old["hold"]["trigger"].items():
        q, m = new["hold"]["trigger"].get(skill, (0, 0))
        if n and m and p / n - q / m > 1 / n + 1e-9:
            return False
    return True


def set_description(md, desc):
    problem = desc_problem(desc)
    if problem:
        raise ValueError(problem)
    new, n = DESC.subn(lambda _: "description: " + desc, md, count=1)
    if n != 1:
        raise ValueError("SKILL.md has no one-line description field")
    return new


def propose(descs, fails, failing, model):
    current = "\n".join(f"- {s}: {d}" for s, d in descs.items())
    seen = "\n".join(f"- {'MISSED ' + f['miss'] if 'miss' in f else 'WRONGLY FIRED ' + f['false_fire']}: "
                     f"{f['prompt'][:300]}" for f in fails[:60])
    prompt = (f"These are the skill descriptions of one Claude Code plugin. Claude sees only these when deciding "
              f"which skill to load.\n{current}\n\nOn training prompts these failures happened:\n{seen}\n\n"
              f"Rewrite the descriptions of only these skills: {', '.join(sorted(failing))}. Fix misses by naming the "
              "user's intent and phrasing; fix wrong fires by saying what the skill is not for and where that job "
              "belongs. One line each, at most 1536 characters, most important use case first, never a colon followed "
              "by a space, never ' #'. Do not paste the failing prompts. Answer with only a JSON object "
              '{"<skill>": "<new description>"} and do not use any tools.')
    r = subprocess.run(claude_p_argv(prompt, model), capture_output=True, text=True, check=True, timeout=900)
    out = json.loads(r.stdout)
    m = re.search(r"\{.*\}", out.get("result", ""), re.S)
    return (json.loads(m.group(0)) if m else {}), out.get("total_cost_usd", 0.0)


def climb(plugin, cap, iters, model, run_eval=None, propose_fn=propose):
    plugin = Path(plugin).resolve()
    files = {s: plugin / "skills" / s / "SKILL.md" for s in skills_of(plugin)}
    results = plugin / "evals" / "results"
    results.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    spent, log = 0.0, []

    def real_eval(i, budget):
        path = results / f"climb-{stamp}-{i}.json"
        subprocess.run(["claude", "plugin", "eval", str(plugin), "--tag", "smoke", "--runs", "2", "--ablation", "none",
                        "--trust-plugin", "--no-publish", "--model", model, "--threshold", "0", "-j", "4",
                        "--max-cost-usd", f"{budget:.2f}", "--json", str(path)], check=False)
        if not path.exists():
            raise SystemExit("plugin eval wrote no result; see its output above")
        return json.loads(path.read_text())

    run_eval = run_eval or real_eval

    def evaluate(i):
        nonlocal spent
        r = run_eval(i, max(0.01, cap - spent))
        spent += r.get("costUsd", 0.0)
        return r

    base = evaluate(0)
    if base.get("partial"):
        raise SystemExit(f"cost cap hit on the baseline pass (${spent:.2f})")
    best = score(base)
    last_cost = base.get("costUsd", PASS_COST)
    log.append((0, rates(best["train"]), rates(best["hold"]), "baseline"))
    for i in range(1, iters + 1):
        failing = {f.get("miss") or f.get("false_fire") for f in best["train"]["fails"]} & set(files)
        if not failing:
            log.append((i, None, None, "no train failures, stop"))
            break
        if spent + last_cost > cap:
            log.append((i, None, None, "next pass would cross the cap, stop"))
            break
        descs = {s: DESC.search(f.read_text()).group(0)[len("description: "):] for s, f in files.items()}
        new, cost = propose_fn(descs, best["train"]["fails"], failing, model)
        spent += cost
        backup = {s: f.read_text() for s, f in files.items()}
        changed = []
        for s, d in new.items():
            if s in failing:
                try:
                    files[s].write_text(set_description(backup[s], d))
                    changed.append(s)
                except ValueError as e:
                    print(f"skip {s}: {e}")
        if not changed:
            log.append((i, None, None, "proposal unusable, stop"))
            break
        kept = False
        try:  # an untested description must never survive a crash, Ctrl-C or a rejected pass
            r = evaluate(i)
            last_cost = r.get("costUsd", last_cost)
            cand = score(r)
            kept = not r.get("partial") and accept(best, cand)
        finally:
            if not kept:
                for s, f in files.items():
                    f.write_text(backup[s])
        if not kept:
            log.append((i, rates(cand["train"]), rates(cand["hold"]),
                        "rejected, reverted" + (" (cost cap)" if r.get("partial") else "")))
            break
        best = cand
        log.append((i, rates(cand["train"]), rates(cand["hold"]), "kept " + ",".join(changed)))
    for i, tr, ho, note in log:
        fmt = lambda x: f"trigger {x[0]:.0%} clean {x[1]:.0%}" if x else "-"
        print(f"iter {i}: train {fmt(tr)} | hold {fmt(ho)} | {note}")
    print(f"spent ${spent:.2f} of ${cap:.2f}")


def report(path):
    r = json.loads(Path(path).read_text())
    s = score(r)
    for sp in ("train", "hold"):
        if not s[sp]["clean"][1]:
            print(f"{sp}: n/a (no runs)")
            continue
        t, c = rates(s[sp])
        print(f"{sp}: trigger {t:.0%}, clean {c:.0%}")
        for skill, (p, n) in sorted(s[sp]["trigger"].items()):
            print(f"  {skill}: {p}/{n}")
    depth = sorted({case["name"] for case in r["cases"] for one in case["arms"]["with"] for g in one["graders"]
                    if g["name"].split("-", 1)[0] in ("reads", "skips") and not g["passed"]})
    t, c = rates(s["hold"])
    ok = t >= 0.90 and c >= 0.95 and not depth and s["hold"]["clean"][1] > 0 and not r.get("partial")
    print("depth failures:", ", ".join(depth) or "none")
    if r.get("partial"):
        print("partial result: the cost cap stopped the pass, so this cannot pass")
    print(f"cost ${r.get('costUsd', 0):.2f}")
    print("VERDICT", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--plugin", default=".")
    r.add_argument("--cap", type=float, default=60.0)
    r.add_argument("--iters", type=int, default=5)
    r.add_argument("--model", default="claude-opus-5-5")
    p = sub.add_parser("report")
    p.add_argument("result")
    a = ap.parse_args()
    if a.cmd == "run":
        climb(a.plugin, a.cap, a.iters, a.model)
    else:
        sys.exit(report(a.result))


if __name__ == "__main__":
    main()
