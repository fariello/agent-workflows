# IPD: Add 'aw releases' owner verb to inspect and list release records

- Date: 2026-08-29
- Kind: child
- Concern: Releases are a first-class record class (`.aw/records/releases/`, `releases.py`, `Blocks-Release` gating across every tree) but the ONE records tree with no owner-verb: backlog, specs, plans, and research all have `aw <type>`, whereas releases has none. Developers and agents cannot ask "what is the planned release, its id6/version, and everything gating it?" on demand via a dedicated CLI owner-verb.
- Scope: Add the `releases` (and `release` alias) owner verb to the `aw` CLI with subcommands: `list` (default bare `aw releases`), `show` (detailed view with aggregated release blockers), `new` (scaffold a release record via CLI with dry-run/apply), and `check` (fail-closed front-matter validation), with full `--json` and `--agent` support, tab completion integration, and test coverage.
- Scope-Paths: agent_workflows/releases.py, agent_workflows/cli.py, agent_workflows/completion.py, .aw/records/releases/README.md, tests/test_releases.py, tests/test_releases_cli.py
- Item-Dependencies: none
- From-Backlog: ackme8
- Blocks-Release: next
- Priority: medium
- Status: to-review
- Set: ackme8
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: w0ln4q

## Workflow history

- 2026-08-29 to-review (Antigravity): graduated from backlog ackme8; fully authored plan with 5 E/V pairs covering 'aw releases' owner verb.
- 2026-08-29 draft (Antigravity): created.

## Goal

Provide a dedicated, first-class `aw releases` owner verb that brings parity to the `.aw/records/releases/` tree, enabling users and agents to list releases, inspect the active release and its blocking items, scaffold new release records, and validate release metadata.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: release query and blocker resolution primitives

- [ ] E-01 In `agent_workflows/releases.py`, add release query/listing data structures and reader functions: define `ReleaseRecord` (holding `id6`, `version`, `status`, `summary`, `path`, and workflow history), implement `list_releases(repo_root: Path) -> List[ReleaseRecord]` discovering all `.release.md` records, `get_release(repo_root: Path, selector: str) -> Optional[ReleaseRecord]` resolving by id6, version, filename, or `next`, and `get_release_blockers(repo_root: Path, selector: str) -> List[dict]` discovering all backlog, specs, and plans items carrying `- Blocks-Release:` matching the selected release.
  - Depends on: none
  - Expected outcome: `list_releases`, `get_release`, and `get_release_blockers` provide clean programmatic access to all release records and their gating blockers across all record trees.
  - Execution state: pending

### Task group 2: release command runners (list, show, new, check)

- [ ] E-02 In `agent_workflows/releases.py`, implement the command runners for the CLI verbs: `run_list(args)` (renders a formatted table of release records, supporting `--json` and `--agent`), `run_show(args)` (renders the full release record details along with all gating release-blocker items with status, priority, and path), `run_new(args)` (CLI wrapper around `create_release` with `--version`, `--summary`, `--status`, preview by default, `--apply` to write), and `run_check(args)` (runs `validate_release` across all release records, reporting drift and exiting 0 clean, 1 findings).
  - Depends on: E-01
  - Expected outcome: all four release subcommands are callable with standard `args`, supporting human terminal formatting, `--json`, and `--agent` JSONL modes with correct exit codes.
  - Execution state: pending

### Task group 3: CLI parser and dispatch integration

- [ ] E-03 In `agent_workflows/cli.py`, register the `releases` subcommand (with alias `release`), add its subparsers (`list`, `show`, `new`, `check`), configure CLI arguments (`--version`, `--summary`, `--status`, `--apply`, selector), wire default bare `aw releases` to list releases, and route execution to `releases.run_*` handlers.
  - Depends on: E-02
  - Expected outcome: `aw releases`, `aw release`, `aw releases show next`, `aw releases new --version ... --summary ... --apply`, and `aw releases check` are fully discoverable via `aw --help` and execute cleanly.
  - Execution state: pending

### Task group 4: tab completion and doctor integration

- [ ] E-04 In `agent_workflows/completion.py`, register `releases` and `release` commands in static shell completion tables for Bash, Zsh, and Fish, and implement dynamic completion in `aw __complete` for `aw releases show` resolving release id6s, versions, and `next`.
  - Depends on: E-03
  - Expected outcome: shell tab completion suggests `releases` and `release` subcommands and dynamically completes release selectors.
  - Execution state: pending

### Task group 5: documentation and test suite

- [ ] E-05 Author a comprehensive test suite in `tests/test_releases_cli.py` covering all CLI subcommands (`list`, `show`, `new`, `check`, `--json`, `--agent`, error paths, and blocker resolution) and update `.aw/records/releases/README.md` and repo documentation to document the `aw releases` command family.
  - Depends on: E-03, E-04
  - Expected outcome: all new tests pass with 100% verification of CLI functionality and documentation reflects the new owner verb.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Owner verbs follow the `aw <type> [new|set|check|show|list]` pattern with aliases (e.g. `aw specs`/`spec`, `aw backlog`, `aw research`).
- CLI output contract: human-formatted colored output on TTY, `--agent` emits `aw.agent/v1` JSONL, `--json` emits full structured JSON, and exit codes are 0 (clean), 1 (findings), 2 (usage/error).
- Release records live under `.aw/records/releases/*.release.md` with `- Id:`, `- Status:`, `- Version:`, `- Summary:`.
- `Blocks-Release: <id6|next>` gates point to release records and are resolved via `releases.resolve_release`.
- Plan front-matter fields for graduation: `- From-Backlog: <id6>` pairs with `- Blocks-Release: <release>` so release-gating backlog items can safely transition to `done` via handoff.

## Findings

- `releases.py` already contains core record creation (`create_release`), validation (`validate_release`), and resolution (`resolve_release`, `describe_planned_release`, `load_active_release`), but lacked CLI entry points and owner verb commands.
- `aw attention` already aggregates release blockers, but there was no dedicated CLI verb to inspect release blockers on demand without running the full attention sweep.
- Adding `aw releases` completes owner-verb parity across all record classes (`plans`, `specs`, `backlog`, `research`, `releases`).

## Proposed changes (ordered, validatable)

1. `agent_workflows/releases.py`: add `ReleaseRecord`, `list_releases`, `get_release`, `get_release_blockers`, and runner functions `run_list`, `run_show`, `run_new`, `run_check`.
2. `agent_workflows/cli.py`: register `releases` / `release` parser, subparsers, argument definitions, and dispatch logic.
3. `agent_workflows/completion.py`: register completion schemas and dynamic resolver for release selectors.
4. `.aw/records/releases/README.md`: update documentation with CLI usage examples.
5. `tests/test_releases_cli.py`: add comprehensive test suite testing CLI subcommands, JSON/agent formatting, and blocker resolution.

## Deferred / out of scope (with reason)

- Modifying release record front-matter schema: out of scope, existing schema (`Id`, `Status`, `Version`, `Summary`) is stable and conformant.
- Interactive release promotion workflow: out of scope, releases are ship-gate anchors; full release execution is handled by `release-review`.

## Scope check

- Over-scope: none.
- Under-scope: none; covers query primitives, CLI dispatch, tab completion, docs, and tests.

## Required tests / validation

- Unit tests for `list_releases`, `get_release`, `get_release_blockers`.
- CLI integration tests for `aw releases`, `aw releases list`, `aw releases show <id6|next>`, `aw releases new`, `aw releases check`.
- Format tests verifying `--json` and `--agent` outputs.
- Tab completion tests for `releases` subcommands and release selectors.
- Regression tests ensuring `aw check` and `aw attention` continue to operate cleanly.

Validation command: `python3 -m pytest tests/test_releases.py tests/test_releases_cli.py -q`

## Spec / documentation sync

- Update `.aw/records/releases/README.md` to document the `aw releases` owner verb and subcommands.
- Update `AGENTS.md` or CLI help references if appropriate.

## Open questions

### OQ-01: Should bare `aw releases` default to `list` or show `show next`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Default to `list` (matching `aw backlog` and other owner verbs), while `aw releases show` defaults to `next` when no selector is given.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `list_releases`, `get_release`, and `get_release_blockers` pass unit tests in `tests/test_releases_cli.py` demonstrating discovery, selector resolution (`id6`, version, `next`), and blocker resolution across backlog, specs, and plans.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `run_list`, `run_show`, `run_new`, and `run_check` pass unit tests verifying human formatted output, `--json`, and `--agent` JSONL streams with correct exit codes.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: CLI integration tests demonstrate `aw releases`, `aw release`, `aw releases list`, `aw releases show next`, `aw releases new`, and `aw releases check` parse arguments correctly and dispatch to runner functions.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Completion tests demonstrate `aw completion` generates completion scripts containing `releases` / `release` and `aw __complete` dynamically resolves release targets.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Full test suite execution `python3 -m pytest tests/test_releases.py tests/test_releases_cli.py -q` exits 0 with all tests passing, and documentation accurately reflects the command.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Standard child plan execution under Set `ackme8`. Executes path-scoped modifications within `Scope-Paths`. Validation requires running the test suite and capturing actual runner output.
