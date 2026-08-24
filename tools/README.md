# Repository Tools

This directory contains standalone utility scripts for repository maintenance, workflow execution, and migration.

## `agy_run.py`

`tools/agy_run.py` is a unified multi-mode runner and skeptical validator for Antigravity (Gemini 3.7 Flash High). It runs a primary task turn with calibrated diligence framing, followed automatically by an evidence-backed skeptical validation turn in the exact same conversation session.

### Execution Modes

1. **IPD Mode**:
   ```bash
   python3 tools/agy_run.py 7cvh9t
   python3 tools/agy_run.py --ipd .agents/plans/pending/20260816-test.md
   ```
   Executes the pending Implementation Plan Document, then runs a skeptical self-audit verifying falsifiable tests, code path wiring, and actual command outputs.

2. **Spec-to-IPD Mode**:
   ```bash
   python3 tools/agy_run.py --spec .agents/docs/specs/example.spec.md
   ```
   Authors a conformant IPD from a specification document using `aw ipd scaffold`, assigns IDs with `aw ipd sync`, verifies with `aw ipd lint`, and audits complete requirement coverage.

3. **Prompt File Mode**:
   ```bash
   python3 tools/agy_run.py --file .agents/prompts/local/brief.md
   python3 tools/agy_run.py -f .agents/prompts/local/brief.md
   ```
   Executes an external prompt brief with post-run verification.

4. **Raw Prompt Mode**:
   ```bash
   python3 tools/agy_run.py -p "refactor installer error handling in engine.py"
   python3 tools/agy_run.py --prompt "add unit tests for resolve_target_layout"
   ```
   Provides convenient `agy -c -p` ergonomics with two-turn skeptical validation.

### Session Continuity and Isolation

- Resume project conversation (default): `python3 tools/agy_run.py -p "..."`
- Attach to specific conversation ID: `python3 tools/agy_run.py -s <session_id> -p "..."`
- Force clean slate without inheriting context: `python3 tools/agy_run.py --new-session 7cvh9t`
- List sessions for this workspace: `python3 tools/agy_run.py --list-sessions`
- Skip verification turn: `python3 tools/agy_run.py --no-audit -p "..."`

## `agy_sessions.py`

`tools/agy_sessions.py` inspects and lists Antigravity sessions for a project workspace or across all projects. It displays the session ID, start timestamp, last active timestamp, duration, whether the session is currently in use (ACTIVE vs IDLE via file locks), and initial prompt snippet.

### Usage

```bash
# List sessions for current directory:
python3 tools/agy_sessions.py

# List sessions for a specific directory:
python3 tools/agy_sessions.py /path/to/project

# List all sessions across all projects:
python3 tools/agy_sessions.py --all

# Output machine-readable JSON:
python3 tools/agy_sessions.py --json
```

## `antigravity_execute_ipd.py`

`tools/antigravity_execute_ipd.py` is a backwards-compatible wrapper that delegates directly to `tools/agy_run.py` in IPD mode. Existing invocations continue to work without modification.

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

## `pwatch.py`

`tools/pwatch.py` is a generic process-tree watcher and recorder. It monitors and visualizes process trees matching user-defined strings or regular expressions, collapsing redundant sibling processes and same-name threads with box line art and 256-color styling.

### Usage

```bash
# Watch processes matching a case-insensitive string or bare argument:
python3 tools/pwatch.py python3
python3 tools/pwatch.py -m opencode

# Match with case-sensitive strings (-M) or regular expressions (-R, -r):
python3 tools/pwatch.py -M Python -R '^pytest.*'

# Exclude processes matching strings or regexes (-eM, -em, -eR, -er):
python3 tools/pwatch.py python3 -em pyright

# Record matching processes in the watched tree to JSONL (-rM, -rm, -rR, -rr):
python3 tools/pwatch.py python3 -rm pytest --record-file /tmp/pytest-runs.jsonl
```

### Backwards Compatibility

`tools/watch-agy.py` acts as a convenience wrapper around `pwatch.py`, defaulting to `-m agy` when invoked without process filter arguments.

## `ipdrunner/` (runipd)

`tools/ipdrunner/runipd.py` is a restartable, non-interactive driver for reviewing and executing queues of IPDs, Sets, and plan files. It automatically routes `to-review` plans to OpenCode `/plan-review` (sharing session context across turns) and `approved` plans to full execution. It persists durable run state, session IDs, event streams, decisions, and outcomes under `.aw/records/runs/<run-id>/`.

### Usage

```bash
# Review a to-review plan:
python3 tools/ipdrunner/runipd.py 20260824-ipdrunner-01-pr2nd0-harden.ipd.md

# Review all to-review plans in a set using an existing session:
python3 tools/ipdrunner/runipd.py ipdrunner --session <session_id>

# Execute an approved plan:
python3 tools/ipdrunner/runipd.py 5ahblp

# Execute multiple sets and plans in sequence:
python3 tools/ipdrunner/runipd.py v6zie5 unifyfileio ipdgates execset

# Inspect run status:
python3 tools/ipdrunner/runipd.py status --repo /path/to/repo <run-id>

# Resume a run:
python3 tools/ipdrunner/runipd.py resume --repo /path/to/repo <run-id>
```
