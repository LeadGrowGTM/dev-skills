# Hill-climbing skill descriptions

`<evals>` is the evals skill directory (the parent of this `references/` folder). Run the commands from the root of the plugin you are evaluating; `--plugin` defaults to the current directory.

The description is the only thing Claude sees when choosing a skill, so it is the
knob. Tune all of a plugin's skills together: fixing one skill's misses by making it
broader steals prompts from its neighbours, and only a confusion matrix shows that.

    python3 <evals>/scripts/climb.py run --cap 60 [--iters 5] [--plugin DIR] [--model M]

Each iteration:
1. Run the `smoke` cases (2 runs each) and score train and hold separately:
   trigger rate (expected skill fired) and clean rate (no wrong skill fired).
2. Send Claude the current descriptions plus the TRAIN failures only, and ask for
   new descriptions for just the skills that missed or wrongly fired.
3. Write them (one line, at most 1536 chars, no ': ' or ' #'), re-run, and keep them
   only if hold improves and no skill's hold trigger rate drops by more than one run.
   Otherwise revert and stop.

It stops after `--iters`, on the first rejected change, or before a pass would cross
`--cap`. Results land in `evals/results/climb-*.json`.

Then run the whole suite once and check it against the bar:

    claude plugin eval . --ablation none --trust-plugin --no-publish --model claude-opus-5-5 \
      --threshold 0 --max-cost-usd 45 -j 4 --json evals/results/final.json
    python3 <evals>/scripts/climb.py report evals/results/final.json   # VERDICT PASS: hold trigger >= 90%, clean >= 95%, no depth failures

For one skill on its own, skill-creator's `run_loop.py` (in the claude-plugins-official
skill-creator plugin) does a single-skill version of the same loop.
