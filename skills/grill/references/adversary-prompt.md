# Adversary prompt (send verbatim, with the plan path filled in)

Attack the plan in <PLAN PATH>. You are trying to find the reason it fails, not
to improve it. Read the plan and any code it names. Produce a numbered list of:

- unstated assumptions, and steps depending on something not established
- claims about the codebase or tools that may be false: check them against source
- cases the plan does not handle
- anything simpler that achieves the same outcome
- terms the plan uses loosely or in two senses
- contradictions between the plan and the code; quote both
- two concrete edge cases you invent, walked through the plan

For each item, say what evidence would settle it, with file:line where the answer
is in the repo. Do not propose a rewrite. Do not ask questions, nobody will answer.
Do not edit any file. Items already settled in "Prior rounds" below are not new;
raise them again only with new evidence.

Prior rounds:
<PASTE THE RESOLVED/CHANGED LIST, or "none">
