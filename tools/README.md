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

`tools/untrack-workflow-artifacts.py` is a backwards-compatible delegating shim that safely migrates a repository's run records from the retired repo-root `workflow-artifacts/` directory to the canonical `.aw/workflow-artifacts/` directory without deleting local files.

The tool delegates to `engine.migrate_root_workflow_artifacts`, which preserves git history using `git mv` (so `git log --follow` reaches past the migration commit), commits the relocation in dedicated path-scoped commits, and untracks the destination files so the framework-owned `.aw/.gitignore` rule (`/workflow-artifacts/`) governs them going forward. Standard repository setup with `aw install` (or `agent-workflows install`) automatically runs this same migration.

### Usage

1. **Dry run (default)**:
   ```bash
   python3 tools/untrack-workflow-artifacts.py
   ```
   Inspects the repository state and prints what would be relocated and untracked. Makes no changes to the repository or working tree.

2. **Apply migration**:
   ```bash
   python3 tools/untrack-workflow-artifacts.py --apply
   ```
   Relocates run records from `workflow-artifacts/` to `.aw/workflow-artifacts/` with history preserved in Git, untracks the records at the new path, and removes the retired directory once empty. Does not create or modify any root `.gitignore`.

3. **Compatibility flag `--commit`**:
   ```bash
   python3 tools/untrack-workflow-artifacts.py --apply --commit
   ```
   Accepted for backwards compatibility. Because the underlying migration already makes its own path-scoped commits for the relocation, `--commit` is a no-op that prints an explanatory note.

### Remediation Guidance for Already-Committed Artifacts

If a repository has previously committed run records from the retired `workflow-artifacts/` path to Git history:

1. **Size the Exposure First**:
   Run the local-leaks sanitizer to assess whether committed records contain sensitive local paths, usernames, or session IDs:
   ```bash
   aw sanitize . --agent
   ```

2. **Remediation Option A: Relocate and Untrack (Recommended)**:
   Run `aw install` or `python3 tools/untrack-workflow-artifacts.py --apply` to migrate run records to `.aw/workflow-artifacts/` and stop tracking future changes. This preserves local files and commit history without rewriting Git history.

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

`tools/watch-agy.py` acts as a convenience wrapper around `pwatch.py` (now the compat shim), defaulting to `-m agy` when invoked without process filter arguments. `tools/watch-runners.py` is the compatibility shim forwarding to `agent_workflows.runners_monitor` (`aw runners`).

### Exit Status

`aw pwatch` (including `--runners --table`) and `aw runners` return:
- `0`: clean exit after `--once` or interrupt via Ctrl-C (SIGINT).
- `143`: terminated by SIGTERM.
- `1`: runtime error (e.g. fatal failure reading `/proc`).
- `2`: command-line argument validation or usage error.

In all cases, the alternate screen is exited and the terminal state is restored cleanly.

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

## `lost_guard_census.py`

`tools/lost_guard_census.py` is a reproducible scanner that audits test suite trims (defaulting to commits `80db6750c` and `19313eed`) to identify properties that lost test coverage and dangling test references in live code comments and documentation.

The tool provides an audit that distinguishes between deliberate code-pin test retirements (tests pinning AST or internal implementation details, which must never be restored per GUIDING_PRINCIPLES P16) and genuine behavioral coverage gaps. It measures test removals across both deleted and modified files using multiset difference, computes reach bounds, and cross-references live backlog items to deduplicate known issues.

### Exclusions and Acknowledged Non-Citations

Axis A scans repository files for test path citations and flags dangling references. To prevent false positives while keeping the audit strict, the scanner defines two non-defect categories:

1. **Placeholders:** Generic illustrative paths used in docstrings, schema examples, and comments. The recognized placeholder set comprises `tests/test_x.py`, `tests/test_extra.py`, `tests/test_foo.py`, `tests/test_secret.py`, and `tests/test_demo.py`.
2. **Acknowledged non-citations (keyed exemptions):** Explicit, reviewed table entries in `ACKNOWLEDGED_NON_CITATIONS` keyed by `(carrying_file, cited_path)` mapping to an explanatory rationale.

What qualifies for an acknowledgement:
- Synthetic fixture literals inside test data or mock objects that construct non-existent test paths to test harness behavior.
- Illustrative placeholders in tool or library documentation.
- Deliberate past-tense historical mentions where surrounding prose already explains that the suite was retired or deleted (and which are already exempted by `tests/test_docs_test_citations.py`).

What does NOT qualify:
- Any present-tense pointer a reader or maintainer is invited to follow or run.

Rule for new exemptions:
A new acknowledgement must always be an explicit, reviewed table entry with a specific carrying file, target path, and reason. Blanket file-level exclusions or regex pattern exemptions are strictly prohibited to ensure every exemption remains auditable and visible.

### Usage

```bash
# Print summary table with counting rules and reach bounds:
python3 tools/lost_guard_census.py --summary

# Run Axis A (dangling test file path citations) and show attribution:
python3 tools/lost_guard_census.py --axis a

# Run Axis B (dangling ::Symbol test citations):
python3 tools/lost_guard_census.py --axis b

# Run code-pin classifier report:
python3 tools/lost_guard_census.py --classifier

# Run backlog deduplication and candidate triage:
python3 tools/lost_guard_census.py --dedupe

# Run all sections:
python3 tools/lost_guard_census.py --all

# Print inventory of uncited deleted files with per-file facts:
python3 tools/lost_guard_census.py --uncited

# Output uncited inventory as JSON for --from-json consumers:
python3 tools/lost_guard_census.py --uncited --format json
```

## `mutation_probe.py`

`tools/mutation_probe.py` tests whether a test selection fails when a named production function is mutated.

### Purpose and Isolation

In-memory mutation via pytest plugins cannot reach behavior exercised through subprocess invocations, such as CLI runs that spawn a fresh Python interpreter. Conversely, mutating tracked files in a shared checkout risks polluting concurrent work. To satisfy both constraints, `mutation_probe.py` creates a disposable detached git worktree in a temporary directory outside the repository. The mutant is applied directly to the worktree disk copy, making it visible to both in-process and subprocess tests, while leaving the invoking checkout untouched. The probe always removes and prunes the worktree when finished.

The probe tests committed `HEAD` only. Uncommitted edits in the invoking checkout are not seen.

### Operators

The tool supports five explicit mutation operators:
- `return-none`: replaces the function body with `return None`.
- `return-true`: replaces the function body with `return True`.
- `return-false`: replaces the function body with `return False`.
- `negate-return`: wraps every `return <expr>` of the function in `not (...)`, leaving nested functions untouched.
- `raise`: replaces the function body with `raise RuntimeError("mutant")`.

### Verdict Classes and Baseline Subtraction

Because test suites may have pre-existing failures, raw failure is not a kill signal. The probe runs the test selection on the unmutated tree to record baseline failures, applies the mutant, and then subtracts baseline failing nodes (`newly_failing = mut_fail - base_fail`). To prevent flaky tests from being counted as kills, newly failing nodes are re-tested against the restored unmutated tree; any node that fails again unmutated is moved to `flaky` and dropped from `newly_failing`.

The tool emits one of six verdicts:
- `killed`: newly failing nodes contain at least one non-collection test.
- `killed-by-import`: all newly failing nodes are collection errors, indicating an import-time call broke.
- `survived`: newly failing set is empty.
- `invalid`: the target qualname is absent, or the operator cannot apply.
- `timeout`: a test run exceeded the configured timeout.
- `error`: baseline XML was missing, or the isolation preflight check failed.

### Positive Controls via `--extra-test`

The `--extra-test COMMIT:PATH` option extracts a test blob from `<COMMIT>^:<PATH>` and writes it into the worktree before running baseline tests. This allows deleted or historical tests to be replayed as positive controls to demonstrate that the test selection is capable of killing the mutant. Overwriting a path at `HEAD` is tracked and reported.

### Measured Cost

A default-selection test run on the full suite takes approximately 200 seconds here. Because a probe runs at least two full passes (baseline and mutant, plus an optional rerun for flaky confirmation), running against the full suite requires roughly 7 minutes. Narrowing the test selection with `-- <pytest args>` is recommended for fast feedback.

### Usage

```bash
# Run a positive control with an extra test:
python3 tools/mutation_probe.py agent_workflows/run_freeze.py::freeze_requirements \
    --op raise \
    --extra-test 19313eed:tests/test_run_freeze.py \
    --format json \
    -- tests/test_run_freeze.py

# Run a probe with targeted test selection:
python3 tools/mutation_probe.py agent_workflows/m.py::is_even \
    --op negate-return \
    -- tests/test_m.py
```

## `deleted_test_replay.py`

`tools/deleted_test_replay.py` is a test replay harness that executes historical or trim-deleted test files against the current tree and reports machine-readable verdicts and per-test outcomes.

### Purpose and Isolation

The harness provides a deterministic, side-effect-free way to execute deleted test files against current code to verify whether historical assertions still hold.

To prevent collisions with concurrent work and ensure tests see repository root imports and root `conftest.py` sandboxing, the tool creates a throwaway detached git worktree of committed `HEAD` in a temporary directory outside the checkout. The replayed test blob is extracted from git (`<commit>^:<path>`) and written at its original repository-relative path inside that worktree. Uncommitted edits in the invoking checkout are not seen. When execution completes, the harness always removes and prunes the temporary worktree and deletes the temporary directory.

### Verdict Classes

Each replayed file receives one of seven closed verdict classes:
- `pass`: all collected tests passed (exit 0).
- `fail`: one or more assertions failed against current code (exit 1).
- `error-import`: test collection failed due to a missing module (exit 2 with `ModuleNotFoundError` or `ImportError`).
- `error-collect`: test collection failed due to another collection error such as a syntax error (exit 2).
- `no-tests`: the test file defines no runnable tests (exit 5).
- `timeout`: test execution exceeded the configured timeout (the child process group is terminated with SIGKILL).
- `error`: pytest internal error, usage error, unexpected termination, or missing test result XML.

### Handoff from `lost_guard_census.py`

The harness integrates directly with `tools/lost_guard_census.py`. Passing `--from-json <inventory.json>` accepts the JSON output generated by `tools/lost_guard_census.py --uncited --format json` and replays every listed path in sequence after any positional paths.

### Usage

```bash
# Replay a single deleted test file:
python3 tools/deleted_test_replay.py 19313eed tests/test_run_freeze.py

# Output machine-readable JSON:
python3 tools/deleted_test_replay.py 19313eed tests/test_run_freeze.py --format json

# Replay an inventory list from lost_guard_census.py:
python3 tools/deleted_test_replay.py 19313eed --from-json uncited_inventory.json --format json

# Run with a custom per-file timeout:
python3 tools/deleted_test_replay.py 19313eed tests/test_run_freeze.py --timeout 60
```

## `replay_coverage_diff.py`

`tools/replay_coverage_diff.py` computes production line coverage differentials between surviving tests and replayed deleted tests to mechanically identify functions and lines whose test guards were lost.

### Purpose and Architecture

When evaluating uncited deleted tests, the tool provides a mechanical way to determine what production behavior a deleted test exercised that surviving tests do not. It runs in two phases:
1. `baseline`: runs surviving tests under `coverage run` with dynamic test contexts and subprocess tracing, producing a `baseline.json` mapping each production function to its covered body lines and reaching test contexts.
2. `diff`: replays deleted test files in detached worktrees via `deleted_test_replay.py` under the same coverage instrumentation, comparing replayed line reach against the baseline to categorize covered lines into `exclusive_lines` and `shared_lines`.

### In-Process vs Subprocess Narrowing

Coverage dynamic contexts record the specific test function names that execute each line of code. For in-process test calls, narrowing mutation probe execution to only the reaching tests is sound: a test that never executes a function body cannot have its outcome altered by mutating that body.

In contrast, reach through an external subprocess (such as CLI command invocations) executes in a separate process where pytest dynamic context tracking is unavailable, recording only the empty context. Functions covered only through child processes are flagged with `subprocess_only: true` in `baseline.json`. These functions cannot be narrowed safely and must be probed against the full selection.

### Audit-Time Dependency and Temp-Dir Rule

The script is an audit-time tool. The `coverage` package is not declared as a runtime or shipped test dependency. If `coverage` is not installed, the tool refuses execution with exit code 2 and prints an installation message.

All coverage databases, process start files, and combined data are kept strictly in temporary directories outside the repository tree and cleaned up after execution. No `.coverage*` files are ever left in the repository.

### Baseline Validation and Performance

A baseline is valid only for the exact git `HEAD` commit it records. Because line numbers are only comparable on the same tree, `diff` refuses with exit code 2 if `baseline.json`'s `head` differs from current `HEAD`.

In validation (V-01), computing the baseline over the surviving test selection with pytest-xdist completed in 1043.18 seconds (approximately 17.4 minutes), measuring 4136 production functions of which 115 were marked `subprocess_only`.

### Usage

```bash
# Generate baseline coverage for the current tree:
python3 tools/replay_coverage_diff.py baseline --out /tmp/base

# Run baseline serially or pass targeted pytest arguments:
python3 tools/replay_coverage_diff.py baseline --out /tmp/base -- -p no:xdist tests/test_m.py

# Diff a deleted test file against the baseline:
python3 tools/replay_coverage_diff.py diff 19313eed tests/test_run_freeze.py --baseline /tmp/base

# Output machine-readable diff JSON:
python3 tools/replay_coverage_diff.py diff 19313eed tests/test_run_freeze.py --baseline /tmp/base --format json

# Diff an entire inventory list from lost_guard_census.py:
python3 tools/replay_coverage_diff.py diff 19313eed --from-json uncited_inventory.json --baseline /tmp/base --format json
```

## `regen_agents_block.py`

`tools/regen_agents_block.py` regenerates the managed `<!-- aw:block -->` region of this repository's `AGENTS.md` from the generator (`engine.agents_managed_sections("aw")`) and re-records the section hashes in `.aw/system/managed-sections.json`.

### Purpose

In this repository, changes to pointer or reporting prose land as joint generator-plus-`AGENTS.md` commits where the full installer (`aw install .`) is not run. This repo-local tool provides a safe, focused path that rewrites only the managed block region between `<!-- aw:block -->` and `<!-- /aw:block -->`, keeping foreign header and footer text intact, and records updated section hashes in the manifest through `engine.merge_aw_block`. It never touches `GEMINI.md` or unrelated manifest entries.

### Exit Codes

- `0`: Success. The managed block and section hashes are up to date (or were cleanly reconciled).
- `1`: Staleness detected under `--check`. Text or section hash records are out of step.
- `2`: Refused. The file contains ambiguous block markers, legacy markers, drift (missing closer with trailing text), unknown section slugs, or declined tombstones.

### Usage

```bash
# Check if AGENTS.md or manifest records are stale (exit 1 if stale, 0 if current):
python3 -m tools.regen_agents_block --check

# Reconcile AGENTS.md managed block and manifest records in place:
python3 -m tools.regen_agents_block

# Run against a specific repository root directory:
python3 -m tools.regen_agents_block --dir /path/to/repo --check
```
