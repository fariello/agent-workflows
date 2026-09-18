# Repository Tools

This directory contains standalone utility scripts for repository maintenance, workflow execution, and migration.

## `aw agy exec` (was `agy_run.py`)

`aw agy exec` is a unified multi-mode runner and skeptical validator for Antigravity (Gemini 3.7 Flash High). It runs a primary task turn with calibrated diligence framing, followed automatically by an evidence-backed skeptical validation turn in the exact same conversation session.

The logic is packaged as `agent_workflows.agy_run` and the canonical surface is `aw agy exec`. `tools/agy_run.py` is a thin compat shim that forwards to the packaged core, so existing `python3 tools/agy_run.py ...` invocations keep working. Note the surface is `aw agy exec`, NOT `aw agy run`: `aw agy run` (and `runagy`) remain aliases of the separate multi-IPD queue driver `aw agy runipd`, which is a genuinely distinct tool.

### Execution Modes

1. **IPD Mode**:
   ```bash
   aw agy exec 7cvh9t            # or: python3 tools/agy_run.py 7cvh9t
   aw agy exec --ipd .agents/plans/pending/20260816-test.md
   ```
   Executes the pending Implementation Plan Document, then runs a skeptical self-audit verifying falsifiable tests, code path wiring, and actual command outputs.

2. **Spec-to-IPD Mode**:
   ```bash
   aw agy exec --spec .agents/docs/specs/example.spec.md
   ```
   Authors a conformant IPD from a specification document using `aw ipd scaffold`, assigns IDs with `aw ipd sync`, verifies with `aw ipd lint`, and audits complete requirement coverage.

3. **Prompt File Mode**:
   ```bash
   aw agy exec --file .aw/records/prompts/untracked/brief.md
   aw agy exec -f .aw/records/prompts/untracked/brief.md
   ```
   Executes an external prompt brief with post-run verification.

4. **Raw Prompt Mode**:
   ```bash
   aw agy exec -p "refactor installer error handling in engine.py"
   aw agy exec --prompt "add unit tests for resolve_target_layout"
   ```
   Provides convenient `agy -c -p` ergonomics with two-turn skeptical validation.

### Session Continuity and Isolation

- Resume project conversation (default): `aw agy exec -p "..."`
- Attach to specific conversation ID: `aw agy exec -s <session_id> -p "..."`
- Force clean slate without inheriting context: `aw agy exec --new-session 7cvh9t`
- List sessions for this workspace: `aw agy exec --list-sessions`
- Skip verification turn: `aw agy exec --no-audit -p "..."`

## `aw agy sessions` (was `agy_sessions.py`)

Inspects and lists Antigravity sessions for a project workspace or across all projects. It displays the session ID, start timestamp, last active timestamp, duration, whether the session is currently in use (ACTIVE vs IDLE via file locks), and initial prompt snippet.

The logic is packaged as `agent_workflows.agy_sessions` and the canonical surface is `aw agy sessions`. `tools/agy_sessions.py` is a thin compat shim that forwards to the packaged core, so existing invocations keep working.

### Usage

```bash
# List sessions for current directory:
aw agy sessions            # or: python3 tools/agy_sessions.py

# List sessions for a specific directory:
aw agy sessions /path/to/project

# List all sessions across all projects:
aw agy sessions --all

# Output machine-readable JSON:
aw agy sessions --json
```

## `aw agy view` (was `view-antigravity-jsonl.py`)

Formats Antigravity JSONL event logs as readable, pipe-friendly terminal text.

The logic is packaged as `agent_workflows.agy_view` and the canonical surface is `aw agy view` (with a `view-antigravity-jsonl` subcommand alias). `tools/view-antigravity-jsonl.py` is a thin compat shim that forwards to the packaged core.

### Usage

```bash
# Format a JSONL log (or - for stdin):
aw agy view path/to/log.jsonl      # or: python3 tools/view-antigravity-jsonl.py path/to/log.jsonl

# Only emit records containing some text, and also dump the raw objects:
aw agy view --match tool --raw path/to/log.jsonl
```

## `antigravity_execute_ipd.py`

`tools/antigravity_execute_ipd.py` is a backwards-compatible wrapper that delegates directly to `tools/agy_run.py` (now the compat shim, which re-exports the packaged `agent_workflows.agy_run` core) in IPD mode. Existing invocations continue to work without modification.

## `untrack-workflow-artifacts.py`

`tools/untrack-workflow-artifacts.py` safely stops tracking a repository's `workflow-artifacts/` directory without deleting local files.

### Usage

1. **Dry run (default)**:
   ```bash
   python3 tools/untrack-workflow-artifacts.py
   ```
   Inspects the repository state and prints what would be untracked. Makes no changes.

2. **Apply migration (index-only)**:
   ```bash
   python3 tools/untrack-workflow-artifacts.py --apply
   ```
   Removes tracked `workflow-artifacts/` entries strictly from Git's index (`git rm -r --cached`), retains all local working-tree files, appends the `workflow-artifacts/` ignore rule to `.gitignore`, and stages both changes.

3. **Apply and commit**:
   ```bash
   python3 tools/untrack-workflow-artifacts.py --apply --commit
   ```
   Applies the migration and creates a dedicated commit (`chore: stop tracking workflow artifacts`). Rejects committing if unrelated files are staged.

### Remediation Guidance for Already-Committed Artifacts

If a repository has previously committed `workflow-artifacts/` run records to Git history:

1. **Size the Exposure First**:
   Run the local-leaks sanitizer to assess whether committed records contain sensitive local paths, usernames, or session IDs:
   ```bash
   aw sanitize . --agent
   ```

2. **Remediation Option A: Index-Only Stop Tracking (Recommended)**:
   Use `python3 tools/untrack-workflow-artifacts.py --apply` to stop tracking future changes and keep local files. This prevents future commits of run records without rewriting Git history.

3. **Remediation Option B: Git History Rewrite (Optional for Sensitive Exposure)**:
   If committed history contains sensitive credentials or private home paths that must be purged from Git history entirely, use `git-filter-repo` (or BFG Repo-Cleaner) to strip the directory from all commits:
   ```bash
   git filter-repo --path workflow-artifacts/ --invert-paths
   ```
   **WARNING (destructive; run ONLY with explicit human approval):** this REWRITES history, changes every subsequent commit SHA, and requires a coordinated force-push that invalidates all existing clones and open branches/PRs. It is NOT reversible by a normal pull. Do NOT run it automatically or as part of routine remediation; propose it, explain the blast radius, and wait for an explicit human decision before executing (consistent with the toolkit's never-rewrite-history-without-approval posture).

## `aw_upgrade_test.py` (upgrade rehearsal harness)

`tools/aw_upgrade_test.py` rehearses an install, update, or layout migration against a
DISPOSABLE copy of a real repository, so the upgrade path can be exercised on realistic
input before it is run on anything that matters.

It exists because every install test in `tests/` starts from a fresh `git init` or a
hand-seeded legacy tree, so nothing had ever installed OVER a previous version's real
on-disk state. That is the only path a real user takes: nobody gets a fresh install, they
get an upgrade over a tree an older version wrote, plus whatever drift accumulated since
(hand-edited managed blocks, half-finished migrations, stale backups, untracked working
material).

This is a maintainer rehearsal rig, not part of the shipped `aw` surface. It makes no
assertions about what a correct upgrade looks like; it produces evidence a human then
judges. Its observations are labeled as evidence, not verdicts, for that reason.

### Usage

```bash
tools/aw_upgrade_test.py list                    # candidate source repos + versions
tools/aw_upgrade_test.py list --installed-only --size
tools/aw_upgrade_test.py new pysyslib            # copy, upgrade, report
tools/aw_upgrade_test.py new pysyslib --rerun    # run twice to check idempotency
tools/aw_upgrade_test.py new pysyslib --no-run   # copy only; upgrade by hand later
tools/aw_upgrade_test.py new pysyslib -- --to-aw # pass flags through to `aw install`
tools/aw_upgrade_test.py new big-repo --strategy clone
tools/aw_upgrade_test.py sandboxes               # what sandboxes exist
tools/aw_upgrade_test.py probe <sandbox>         # re-probe state (read-only)
tools/aw_upgrade_test.py env <sandbox>           # exports to explore it safely
tools/aw_upgrade_test.py clean --all             # preview; add -y to remove
```

Anything after a bare `--` is passed to `aw install` verbatim, so any flag combination can
be rehearsed without this tool needing to know about it.

Sandboxes are named `<repo>.aw-upgrade-test.YYYYMMDD-HHMMSS/` and are created under a
dedicated sandbox root (see `--dest`, whose default is shown in `--help`) that sits outside
the configured discovery search roots. Use `--sibling` to place one beside its source
instead.

### Copy strategies

- `--strategy full` (default) uses `cp -a`: a faithful copy including `.git`, untracked, and
  gitignored material. Fidelity matters because the installer reads paths a clone would not
  reproduce, such as `.aw/state`, backups, and the install manifest.
- `--strategy clone` uses `git clone --local` plus a real copy of the framework trees, for
  repositories large enough that a full copy is impractical.

Hardlink copying is deliberately not offered. It would be cheap, but any in-place truncation
inside the sandbox would corrupt the source repository.

### The four safety invariants

This tool copies real repositories and runs a mutating installer on them, so each way it
could damage real work is closed by construction and covered by a test in
`tests/test_aw_upgrade_test.py`:

1. **Never mutate the source.** The source is only ever read, and copies never share inodes
   with it. A test writes through a sandbox file and asserts the source is unchanged.
2. **Never push.** A `cp -a` copy inherits `.git` verbatim, including remotes pointing at
   real upstreams. Every sandbox has its remotes removed immediately after the copy and
   before any install runs; removal is verified, a blackhole push URL is configured so a
   re-added remote still cannot reach a network, and sandbox commits get a throwaway
   identity rather than the operator's. A test performs an actual `git push` and asserts it
   fails.
3. **Never pollute the real inventory.** Sandboxes live outside the configured discovery
   search roots, and every `aw` invocation runs with `XDG_CONFIG_HOME` and `AW_HOME`
   redirected into the sandbox, so the user's real config is never written and a sandbox
   never becomes a managed repo. Use `env` to get the same isolation in your own shell.
4. **Never delete anything but a sandbox.** `clean` refuses any directory lacking the
   `.aw-upgrade-test.json` marker, so a mistyped path is refused rather than deleted. No
   flag bypasses that gate.

Sources that are git worktrees are skipped, since a worktree shares its parent repository's
object store and is neither a realistic user scenario nor a safe target.

## `aw pwatch` (was `pwatch.py`)

A generic process-tree watcher and recorder. It monitors and visualizes process trees matching user-defined strings or regular expressions, collapsing redundant sibling processes and same-name threads with box line art and 256-color styling.

The logic is packaged as `agent_workflows.pwatch` and the canonical surface is the top-level `aw pwatch`. `tools/pwatch.py` is a thin compat shim that forwards to the packaged core.

### Usage

```bash
# Watch processes matching a case-insensitive string or bare argument:
aw pwatch python3           # or: python3 tools/pwatch.py python3
aw pwatch -m opencode

# Match with case-sensitive strings (-M) or regular expressions (-R, -r):
aw pwatch -M Python -R '^pytest.*'

# Exclude processes matching strings or regexes (-eM, -em, -eR, -er):
aw pwatch python3 -em pyright

# Record matching processes in the watched tree to JSONL (-rM, -rm, -rR, -rr):
aw pwatch python3 -rm pytest --record-file /tmp/pytest-runs.jsonl
```

### Backwards Compatibility

`tools/watch-agy.py` acts as a convenience wrapper around `pwatch.py` (now the compat shim), defaulting to `-m agy` when invoked without process filter arguments.

## `aw oc runipd` (the OpenCode IPD runner)

The OpenCode IPD runner is a restartable, non-interactive driver for reviewing and executing queues of IPDs, Sets, and plan files. It automatically routes `to-review` plans to OpenCode `/plan-review` (sharing session context across turns) and `approved` plans to full execution. It persists durable run state, session IDs, event streams, decisions, and outcomes under `.aw/records/runs/<run-id>/`.

The runner is packaged in the toolkit as `agent_workflows.oc_runipd` and is invoked as `aw oc runipd` (alias `aw opencode runipd`), so it works in any environment where `aw` is installed. The old path `python3 tools/ipdrunner/runipd.py ...` still works: it is now a thin compatibility shim that delegates to the packaged runner.

### Usage

Primary (packaged command):

```bash
# Review a to-review plan:
aw oc runipd 20260824-ipdrunner-01-pr2nd0-harden.ipd.md

# Review all to-review plans in a set using an existing session:
aw oc runipd ipdrunner --session <session_id>

# Execute an approved plan:
aw oc runipd 5ahblp

# Execute multiple sets and plans in sequence:
aw oc runipd v6zie5 unifyfileio ipdgates execset

# Inspect run status:
aw oc runipd status --repo /path/to/repo <run-id>

# Resume a run:
aw oc runipd resume --repo /path/to/repo <run-id>
```

`aw opencode runipd ...` is an accepted alias. The legacy source-checkout path continues to work unchanged as a compatibility shim:

```bash
python3 tools/ipdrunner/runipd.py status --repo /path/to/repo <run-id>
```
