#!/usr/bin/env python3
"""Mine skill invocations from Claude Code session logs into eval candidates.

For every Skill call whose skill is in the map, keep the session's opening
prompt and the 3 user turns before the call (the line right before is often
just "go"), scrubbed. Pasted chat is kept, cut to 400 chars, because it often IS
the intent; emails, keys and home paths are removed everywhere. Client names are
not caught here, which is why proposals get a human review before commit.
Output, local only: <plugin>/evals/mine-out/candidates.jsonl.

  mine.py --map evals/mine-map.json [--plugin DIR] [--logs ~/.claude/projects]

Map file: {"map": {"<old or new skill name>": "<skill that should fire, or none>"},
           "none": "<what belongs to no skill of this plugin>"}
"""
import argparse
import json
import re
from pathlib import Path

HARNESS = ("<command-", "<local-command", "<system-reminder", "<task-notification", "<bash-", "<user-prompt-submit-hook")
PASTE = re.compile(r"<pasted_content[^>]*>(.*?)</pasted_content[^>]*>", re.S)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# ponytail: over-scrubs long slugs and hashes too; safety beats fidelity for eval text
SECRET = re.compile(r"\b(?:sk|pk|rk)[-_][-_A-Za-z0-9]{12,}|\b(?:ghp|gho|ghs|xox[abp])_?[-_A-Za-z0-9]{12,}"
                    r"|\bAKIA[A-Z0-9]{12,}|\btr_(?:dev|prod|stg|pat)_\w+|\b[A-Za-z0-9+_-]{32,}\b")
ASSIGNED = re.compile(r"(?i)\b(\w*(?:key|token|secret|password|passwd)\w*\s*[=:]\s*)\S+")
HOME = re.compile(r"(?:/home|/Users)/[^/\s]+|[A-Za-z]:\\Users\\[^\\\s]+")


def scrub(text):
    text = PASTE.sub(lambda m: "[pasted: " + " ".join(m.group(1).split())[:400] + "]", text)
    text = EMAIL.sub("<email>", text)
    text = SECRET.sub("<secret>", text)
    text = ASSIGNED.sub(lambda m: m.group(1) + "<secret>", text)
    return HOME.sub("~", text)


def user_text(event):
    """Human-typed text of a user event, or None for tool results, skill bodies and harness lines."""
    if event.get("type") != "user" or event.get("isMeta"):
        return None
    content = event.get("message", {}).get("content")
    if isinstance(content, list):
        blocks = [b for b in content if isinstance(b, dict)]
        if any(b.get("type") == "tool_result" for b in blocks):
            return None
        content = " ".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    if not isinstance(content, str):
        return None
    content = content.strip()
    if not content or content.startswith(HARNESS):
        return None
    return content


def invocations(lines, mapping):
    opening, recent = None, []
    for line in lines:
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        text = user_text(event)
        if text:
            opening = opening or text
            recent = (recent + [text])[-3:]
            continue
        if event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content") or []:
            if not (isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill"):
                continue
            old = str(block.get("input", {}).get("skill", "")).split(":")[-1]
            if old in mapping and opening:
                yield {"old_skill": old, "expect": mapping[old],
                       "opening": scrub(opening), "context": [scrub(t) for t in recent]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plugin", default=".")
    ap.add_argument("--map", required=True)
    ap.add_argument("--logs", default=str(Path.home() / ".claude/projects"))
    a = ap.parse_args()
    mapping = json.loads(Path(a.map).read_text())["map"]
    out = Path(a.plugin) / "evals/mine-out/candidates.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    seen, counts = set(), {}
    with out.open("w") as w:
        for f in sorted(Path(a.logs).glob("*/*.jsonl")):
            with f.open(errors="ignore") as lines:
                for c in invocations(lines, mapping):
                    key = (c["old_skill"], c["opening"][:200])
                    if key in seen:
                        continue
                    seen.add(key)
                    c["session"] = f.stem
                    counts[c["expect"]] = counts.get(c["expect"], 0) + 1
                    w.write(json.dumps(c) + "\n")
    print(json.dumps(counts, sort_keys=True), "->", out)


if __name__ == "__main__":
    main()
