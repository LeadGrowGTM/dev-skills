#!/usr/bin/env python3
"""Write one `claude plugin eval` case into <plugin>/evals/.

The expected skill gets a must-fire grader and every other skill in the plugin a
must-stay-silent grader, so a suite of these cases is a confusion matrix. The
case is named <split>-<expect>-<slug>; the 60/40 train/hold split is fixed by a
hash of the slug so it never moves.

  new_case.py SLUG EXPECT "PROMPT" [--plugin DIR] [--reads references/x.md]...
              [--skips references/y.md]... [--tag T]... [--smoke] [--runs N]

EXPECT is a skill name in the plugin, or "none" (no skill of this plugin should fire).
"""
import argparse
import hashlib
import re
from pathlib import Path

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def skills_of(plugin):
    return sorted(p.name for p in (Path(plugin) / "skills").iterdir() if (p / "SKILL.md").is_file())


def split_for(slug):
    return "train" if int(hashlib.sha1(slug.encode()).hexdigest(), 16) % 10 < 6 else "hold"


def skill_pattern(skill):
    # Skill names are [a-z0-9-]; inserted raw because "\-" is a syntax error in a /u JS regex.
    return r'"skill"\s*:\s*"(?:[\w-]+:)?' + skill + '"'


def grader(tool, pattern, silent):
    bounds = "min: 0\nmax: 0\n" if silent else ""
    return f"---\ntype: tool_used\ntool: {tool}\ninput_match: '{pattern}'\n{bounds}---\n"


def write_case(plugin, slug, prompt, expect, reads=(), skips=(), tags=(), smoke=False, runs=3):
    skills = skills_of(plugin)
    if not SLUG.fullmatch(slug) or len(slug) > 50:
        raise ValueError(f"bad slug {slug!r}: lowercase kebab-case, at most 50 chars")
    if expect not in skills + ["none"]:
        raise ValueError(f"expect {expect!r} is not one of {skills} or none")
    split = split_for(slug)
    name = f"{split}-{expect}-{slug}"
    case = Path(plugin) / "evals" / name
    graders = case / "graders"
    graders.mkdir(parents=True)  # FileExistsError on a repeat slug
    depth = bool(reads or skips)
    all_tags = [split, f"expect-{expect}", *tags] + (["smoke"] if smoke else []) + (["depth"] if depth else [])
    (case / "prompt.md").write_text(
        f"---\nname: {name}\ntags: [{', '.join(all_tags)}]\nruns: {runs}\n"
        f"max_turns: {6 if depth else 4}\nallowed_tools: [Read, Glob, Grep, Skill]\n---\n{prompt.strip()}\n")
    for s in skills:
        kind = "fires" if s == expect else "silent"
        (graders / f"{kind}-{s}.md").write_text(grader("Skill", skill_pattern(s), kind == "silent"))
    for path, silent in [(r, False) for r in reads] + [(r, True) for r in skips]:
        kind = "skips" if silent else "reads"
        (graders / f"{kind}-{Path(path).stem}.md").write_text(grader("Read", path.replace(".", r"\."), silent))
    return case


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("expect")
    ap.add_argument("prompt")
    ap.add_argument("--plugin", default=".")
    ap.add_argument("--reads", action="append", default=[])
    ap.add_argument("--skips", action="append", default=[])
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--runs", type=int, default=3)
    a = ap.parse_args()
    print(write_case(a.plugin, a.slug, a.prompt, a.expect, a.reads, a.skips, a.tag, a.smoke, a.runs))


if __name__ == "__main__":
    main()
