#!/usr/bin/env sh
# Install the agent workflows (release-review, plan-review, ...) into a repository.
#
# This shell wrapper looks for install-workflows.py next to itself and passes all
# arguments through to it. It clean-syncs the workflow bodies into .agents/workflows/,
# generates per-tool slash-command shims, and adds a one-line pointer to AGENTS.md.
# Stale framework files are pruned (tracked ones via `git rm`); nothing is committed.
#
# To update an existing install, just re-run this; framework files are updated in place
# (backed up unless --no-backup) and staged with git, never committed.
#
# Usage:
#
#   ./install-workflows.sh --repo /path/to/target-repo
#   ./install-workflows.sh --dry-run
#   ./install-workflows.sh --no-prune   # additive only

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PY_INSTALLER="$SCRIPT_DIR/install-workflows.py"

if [ ! -f "$PY_INSTALLER" ]; then
  echo "Could not find Python installer at: $PY_INSTALLER" >&2
  echo "Place install-workflows.py next to this shell script." >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$PY_INSTALLER" "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$PY_INSTALLER" "$@"
fi

echo "Could not find python3 or python on PATH." >&2
exit 1
