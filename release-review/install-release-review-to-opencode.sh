#!/usr/bin/env sh
# Install the modular release-review runbook and OpenCode command wrappers.
#
# This shell wrapper looks for install-release-review-to-opencode.py next to
# itself and passes all arguments through to it.
#
# Usage (clean-syncs the framework from this directory into the target repo;
# stale framework files are pruned, tracked ones via `git rm`, nothing committed):
#
#   ./install-release-review-to-opencode.sh --repo /path/to/target-repo
#   ./install-release-review-to-opencode.sh --dry-run
#   ./install-release-review-to-opencode.sh --force
#   ./install-release-review-to-opencode.sh --no-prune   # additive only

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PY_INSTALLER="$SCRIPT_DIR/install-release-review-to-opencode.py"

if [ ! -f "$PY_INSTALLER" ]; then
  echo "Could not find Python installer at: $PY_INSTALLER" >&2
  echo "Place install-release-review-to-opencode.py next to this shell script." >&2
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
