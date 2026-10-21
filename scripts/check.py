#!/usr/bin/env python3
"""Structural lint for the dev-skills plugin. Prints WARN/FAIL lines; exit 1 on any FAIL.

Limits: only the listed skills, a one-line description of at most
1536 chars with no ': ' or ' #' (YAML would misparse it), a SKILL.md body under
150 lines, every references/ file linked from another file in its skill, every
file SKILL.md links present, and no machine-specific paths.
"""
import json
import re
import sys
from pathlib import Path

SKILLS = {"build", "evals", "grill"}
MAX_DESC, MAX_BODY = 1536, 150
LOCAL = re.compile(r"/home/[\w.-]+/|/Users/[^/\s]+/")
CITATION = re.compile(r"<!--.*?-->|\(src: [^)]*\)", re.S)  # provenance may name the author's paths; commands may not
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/evals/scripts"))
from climb import desc_problem  # noqa: E402  one rule for check and climb
LINK = re.compile(r"(?<![\w/])((?:references|scripts|assets)/[\w.-]*\w)")


def frontmatter(text):
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        return None, text
    head, body = text[4:].split("\n---\n", 1)
    fields = {}
    for line in head.splitlines():
        key, sep, value = line.partition(": ")
        if sep and not line.startswith(" "):
            fields[key] = value
    return fields, body


def check(root):
    root = Path(root)
    fails, warns = [], []
    try:
        manifest = json.loads((root / ".claude-plugin/plugin.json").read_text())
    except (OSError, ValueError) as e:
        return [f"plugin.json unreadable: {e}"], warns
    if manifest.get("name") != "dev-skills":
        fails.append("plugin.json name is not dev-skills")
    if not manifest.get("version"):
        fails.append("plugin.json has no version")
    skills_dir = root / "skills"
    dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []
    for missing in sorted(SKILLS - {d.name for d in dirs}):
        warns.append(f"missing skill {missing}")
    for d in dirs:
        if d.name not in SKILLS:
            fails.append(f"{d.name}: not one of the listed skills")
            continue
        f = d / "SKILL.md"
        if not f.is_file():
            fails.append(f"{d.name}: no SKILL.md")
            continue
        text = f.read_text()
        fields, body = frontmatter(text)
        if fields is None:
            fails.append(f"{d.name}: no frontmatter")
            continue
        if fields.get("name") != d.name:
            fails.append(f"{d.name}: name field is {fields.get('name')!r}")
        desc = fields.get("description", "")
        problem = desc_problem(desc)
        if problem:
            fails.append(f"{d.name}: {problem}")
        n = len(body.splitlines())
        if n >= MAX_BODY:
            fails.append(f"{d.name}: SKILL.md body is {n} lines, max {MAX_BODY - 1}")
        docs = {p: p.read_text(errors="ignore") for p in d.rglob("*.md")}
        for ref in sorted((d / "references").glob("*.md")):
            rel = f"references/{ref.name}"
            if not any(rel in t for p, t in docs.items() if p != ref):
                fails.append(f"{d.name}: {rel} is not linked from any other file in the skill")
        for link in sorted(set(LINK.findall(text))):
            if not (d / link).exists():
                fails.append(f"{d.name}: SKILL.md links {link}, which does not exist")
    for p in sorted(skills_dir.rglob("*")) if skills_dir.is_dir() else []:
        if p.is_file() and "__pycache__" not in p.parts and LOCAL.search(CITATION.sub("", p.read_text(errors="ignore"))):
            fails.append(f"{p.relative_to(root)}: machine-specific path")
    return fails, warns


def main(argv):
    fails, warns = check(argv[1] if len(argv) > 1 else Path(__file__).resolve().parents[1])
    for w in warns:
        print("WARN", w)
    for f in fails:
        print("FAIL", f)
    print("check: ok" if not fails else f"check: {len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
