#!/usr/bin/env python3
"""Turn mined candidates into proposed eval cases, then pad each skill to --target.

Reads <plugin>/evals/mine-out/candidates.jsonl and each skill's own description,
calls `claude -p`, and writes <plugin>/evals/mine-out/proposed.jsonl, one
{"slug", "expect", "prompt", "source"} per line, for a human to review before
make_cases.py writes anything that gets committed.

  propose.py --map evals/mine-map.json [--plugin DIR] [--target 40] [--model M]
"""
import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from new_case import SLUG, skills_of  # noqa: E402

DESC = re.compile(r"^description: (.*)$", re.M)
RULES = """Rules for every prompt you write:
- One self-contained message a user of this plugin would type, casual or formal.
- Never name a skill or the plugin. Never include a client name, a person's name, an email, a key, or a home-directory path; say "a client", "a teammate", "our repo".
- slug: lowercase kebab-case, at most 40 chars, unique, naming the intent.
- expect: exactly one of {choices}.
Answer with only a JSON list, no prose. Do not use any tools."""


def descriptions(plugin):
    return {s: DESC.search((Path(plugin) / "skills" / s / "SKILL.md").read_text()).group(1) for s in skills_of(plugin)}


def claude_p_argv(prompt, model):
    """A text-only `claude -p`: the prompt holds real mined requests ("deploy X to prod"),
    so no built-in tools and no MCP servers. The prompt goes first; --tools is variadic."""
    return ["claude", "-p", prompt, "--model", model, "--output-format", "json",
            "--max-turns", "1", "--strict-mcp-config", "--tools", ""]


def ask(prompt, model):
    """One `claude -p` call that must answer with a JSON list. Returns (list, cost_usd)."""
    r = subprocess.run(claude_p_argv(prompt, model), capture_output=True, text=True, check=True, timeout=900)
    out = json.loads(r.stdout)
    m = re.search(r"\[.*\]", out.get("result", ""), re.S)
    if not m:
        raise ValueError("no JSON list in the answer: " + out.get("result", "")[:300])
    return json.loads(m.group(0)), out.get("total_cost_usd", 0.0)


def skills_block(descs, none_text):
    return "Skills (expect values) and what each is for:\n" + "\n".join(
        [f"- {s}: {d}" for s, d in descs.items()] + [f"- none: {none_text}"])


def label(cands, descs, none_text, model):
    choices = ", ".join([*descs, "none", "drop"])
    rows, cost = [], 0.0
    for i in range(0, len(cands), 20):
        items = "\n\n".join(
            f"[{j}] opening: {c['opening'][:600]}\n    recent turns: {' | '.join(t[:300] for t in c['context'])}\n"
            f"    skill that fired: {c['old_skill']}" for j, c in enumerate(cands[i:i + 20]))
        got, c = ask(f"{skills_block(descs, none_text)}\n\nEach item is a real session where a skill fired. Decide which "
                     "skill SHOULD fire for the user's intent and rewrite that intent as one standalone prompt. Use expect "
                     f"\"drop\" when the intent is unclear.\n\n{items}\n\n{RULES.format(choices=choices)}\n"
                     'Each element: {"i": <item number>, "slug": ..., "expect": ..., "prompt": ...}', model)
        cost += c
        rows += [dict(r, source="mined") for r in got if r.get("expect") != "drop"]
    return rows, cost


def augment(rows, descs, none_text, target, model):
    have = collections.Counter(r["expect"] for r in rows)
    out, cost = [], 0.0
    for s in descs:
        need = target - have[s]
        if need <= 0:
            continue
        seen = "\n".join([f"- {r['prompt']}" for r in rows if r["expect"] == s][:10]) or "- (none yet)"
        got, c = ask(f"{skills_block(descs, none_text)}\n\nWrite {need - need // 2} prompts that SHOULD fire {s} (vary "
                     "phrasing, length and formality; some never say the obvious keyword) and "
                     f"{need // 2} near-miss prompts that share words or topic with {s} but whose intent belongs to another "
                     f"skill or to none. Do not repeat these existing {s} prompts:\n{seen}\n\n"
                     f"{RULES.format(choices=', '.join([*descs, 'none']))}\n"
                     'Each element: {"slug": ..., "expect": ..., "prompt": ..., "kind": "paraphrase" or "near-miss"}', model)
        cost += c
        out += [dict(r, source=r.get("kind", "synthetic")) for r in got]
    return out, cost


def valid(rows, choices):
    seen, ok = set(), []
    for r in rows:
        slug = str(r.get("slug", ""))
        if (r.get("expect") in choices and SLUG.fullmatch(slug) and len(slug) <= 40
                and slug not in seen and r.get("prompt")):
            seen.add(slug)
            ok.append({k: r[k] for k in ("slug", "expect", "prompt", "source")})
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plugin", default=".")
    ap.add_argument("--map", required=True)
    ap.add_argument("--target", type=int, default=40)
    ap.add_argument("--model", default="claude-opus-5-5")
    a = ap.parse_args()
    out_dir = Path(a.plugin) / "evals/mine-out"
    cands = [json.loads(l) for l in (out_dir / "candidates.jsonl").read_text().splitlines() if l.strip()]
    none_text = json.loads(Path(a.map).read_text())["none"]
    descs = descriptions(a.plugin)
    choices = {*descs, "none"}
    mined, c1 = label(cands, descs, none_text, a.model)
    mined = valid(mined, choices)
    extra, c2 = augment(mined, descs, none_text, a.target, a.model)
    rows = valid(mined + extra, choices)
    (out_dir / "proposed.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(dict(collections.Counter(r["expect"] for r in rows)), f"cost ${c1 + c2:.2f}", "->", out_dir / "proposed.jsonl")


if __name__ == "__main__":
    main()
