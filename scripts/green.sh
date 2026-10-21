#!/usr/bin/env bash
# dev-skills green: unit tests, structural lint, Claude Code's own manifest check.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -q
python3 scripts/check.py
claude plugin validate .
