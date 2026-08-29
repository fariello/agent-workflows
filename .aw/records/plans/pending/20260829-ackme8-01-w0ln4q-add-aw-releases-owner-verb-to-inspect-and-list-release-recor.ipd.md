# IPD: Add 'aw releases' owner verb to inspect and list release records

- Date: 2026-08-29
- Kind: child
- Concern: Releases are a first-class record class (`.aw/records/releases/`, `releases.py`, `Blocks-Release` gating across every tree) but the ONE records tree with no owner-verb: backlog, specs, plans, and research all have `aw <type>`, whereas releases has none. Developers and agents cannot ask "what is the planned release, its id6/version, and everything gating it?" on demand via a dedicated CLI owner-verb.
- Scope: Add the `releases` (and `release` alias) owner verb to the `aw` CLI with subcommands: `list` (default bare `aw releases`), `show` (detailed view with aggregated release blockers), `new` (scaffold a release record via CLI with dry-run/apply), with full `--json` and `--agent` support, tab completion integration, and test coverage. A `releases check` subcommand is deliberately EXCLUDED: `aw check releases` already validates release records via `check_engine.py:489` -> `releases.validate_release` (verified working: `aw check releases` -> `CONFORMS 1 releases checked`), so adding a second validation entry point would duplicate a canonical path.
- Scope-Paths: agent_workflows/releases.py, agent_workflows/cli.py, agent_workflows/completion.py, .aw/records/releases/README.md, tests/test_releases.py, tests/test_releases_cli.py
- Item-Dependencies: none
- From-Backlog: ackme8
- Blocks-Release: next
- Priority: medium
- Status: approved
- Set: ackme8
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: w0ln4q
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 fixed; readiness GO - PENDING HUMAN APPROVAL. PR-001 get_release_blockers must REUSE attention.release_blockers (attention.py:582) not re-scan; PR-002 dropped the duplicate 'releases check' subcommand (aw check releases already validates via check_engine.py:489, verified CONFORMS) and added a test asserting it is not reintroduced; PR-003 replaced all five un-falsifiable V-items (which said only 'tests passing'/'100% verification') with exact commands plus required strings, set-equality and adversarial assertions; also hardened the execution gate with a scope fence, honesty rule, and reuse rule.

- 2026-08-29 to-review (Antigravity): graduated from backlog ackme8; fully authored plan with 5 E/V pairs covering 'aw releases' owner verb.
- 2026-08-29 draft (Antigravity): created.

## Goal

Provide a dedicated, first-class `aw releases` owner verb that brings parity to the `.aw/records/releases/` tree, enabling users and agents to list releases, inspect the active release and its blocking items, scaffold new release records, and validate release metadata.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: release query and blocker resolution primitives

- [ ] E-01 In `agent_workflows/releases.py`, add release query/listing data structures and reader functions: define `ReleaseRecord` (holding `id6`, `version`, `status`, `summary`, `path`, and workflow history), implement `list_releases(repo_root: Path) -> List[ReleaseRecord]` discovering all `.release.md` records, `get_release(repo_root: Path, selector: str) -> Optional[ReleaseRecord]` resolving by id6, version, filename, or `next`, and `get_release_blockers(repo_root: Path, selector: str) -> List[dict]` which MUST REUSE the existing public `attention.release_blockers(items, repo_root)` (attention.py:582) over the attention item scan rather than re-implementing a second `- Blocks-Release:` walk. Re-implementing the scan would create a duplicate path that can drift from the board's answer (architecture rule: use existing canonical mechanisms).
  - Depends on: none
  - Expected outcome: `list_releases`, `get_release`, and `get_release_blockers` provide clean programmatic access; `get_release_blockers` returns the SAME blocker set as `aw attention` for the same release (single source of truth, no second scan). `get_release` resolves via the existing `resolve_release`/`describe_planned_release` (releases.py:134) for the `next` sentinel rather than a new resolver.
  - Execution state: pending

### Task group 2: release command runners (list, show, new, check)

- [ ] E-02 In `agent_workflows/releases.py`, implement the command runners for the CLI verbs: `run_list(args)` (renders a formatted table of release records, supporting `--json` and `--agent`), `run_show(args)` (renders the full release record details along with all gating release-blocker items with status, priority, and path), `run_new(args)` (CLI wrapper around `create_release` with `--version`, `--summary`, `--status`, preview by default, `--apply` to write). No `run_check` is added (see Scope: `aw check releases` is the canonical validator).
  - Depends on: E-01
  - Expected outcome: all three release subcommands (list, show, new) are callable with standard `args`, supporting human terminal formatting, `--json`, and `--agent` JSONL modes with correct exit codes.
  - Execution state: pending

### Task group 3: CLI parser and dispatch integration

- [ ] E-03 In `agent_workflows/cli.py`, register the `releases` subcommand (with alias `release`), add its subparsers (`list`, `show`, `new`, `check`), configure CLI arguments (`--version`, `--summary`, `--status`, `--apply`, selector), wire default bare `aw releases` to list releases, and route execution to `releases.run_*` handlers.
  - Depends on: E-02
  - Expected outcome: `aw releases`, `aw release`, `aw releases show next`, and `aw releases new --version ... --summary ... --apply` are fully discoverable via `aw --help` and execute cleanly.
  - Execution state: pending

### Task group 4: tab completion and doctor integration

- [ ] E-04 In `agent_workflows/completion.py`, register `releases` and `release` commands in static shell completion tables for Bash, Zsh, and Fish, and implement dynamic completion in `aw __complete` for `aw releases show` resolving release id6s, versions, and `next`.
  - Depends on: E-03
  - Expected outcome: shell tab completion suggests `releases` and `release` subcommands and dynamically completes release selectors.
  - Execution state: pending

### Task group 5: documentation and test suite

- [ ] E-05 Author a comprehensive test suite in `tests/test_releases_cli.py` covering all CLI subcommands (`list`, `show`, `new`, `--json`, `--agent`, error paths, and blocker resolution) and update `.aw/records/releases/README.md` and repo documentation to document the `aw releases` command family.
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

1. `agent_workflows/releases.py`: add `ReleaseRecord`, `list_releases`, `get_release`, `get_release_blockers` (reusing `attention.release_blockers`), and runner functions `run_list`, `run_show`, `run_new`.
2. `agent_workflows/cli.py`: register `releases` / `release` parser, subparsers, argument definitions, and dispatch logic.
3. `agent_workflows/completion.py`: register completion schemas and dynamic resolver for release selectors.
4. `.aw/records/releases/README.md`: update documentation with CLI usage examples.
5. `tests/test_releases_cli.py`: add comprehensive test suite testing CLI subcommands, JSON/agent formatting, and blocker resolution.

## Deferred / out of scope (with reason)

- Modifying release record front-matter schema: out of scope, existing schema (`Id`, `Status`, `Version`, `Summary`) is stable and conformant.
- A `releases check` subcommand: EXCLUDED as a duplicate of the working `aw check releases` (check_engine.py:489). Validation stays single-sourced.
- Interactive release promotion workflow: out of scope, releases are ship-gate anchors; full release execution is handled by `release-review`.

## Scope check

- Over-scope: none.
- Under-scope: none; covers query primitives, CLI dispatch, tab completion, docs, and tests.

## Required tests / validation

- Unit tests for `list_releases`, `get_release`, `get_release_blockers`.
- CLI integration tests for `aw releases`, `aw releases list`, `aw releases show <id6|next>`, `aw releases new`.
- A test asserting NO `aw releases check` subcommand is registered (the canonical validator stays `aw check releases`), so the duplicate path cannot be reintroduced.
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
  - Required evidence: Pasted `python3 -m pytest tests/test_releases.py -q` output showing named unit tests pass for: `list_releases` discovering every `.release.md` under `.aw/records/releases/` (assert the returned count equals the on-disk count from `ls .aw/records/releases/*.release.md | wc -l`); `get_release` resolving BY id6, BY version string, BY filename, and BY the `next` sentinel (4 separate assertions), and returning None for an unknown selector; and `get_release_blockers` returning EXACTLY the same id6 set as `attention.release_blockers` for the same release - assert set equality against the existing function, proving no second scan was written. ALSO paste `grep -n "attention.release_blockers\|from agent_workflows.attention import" agent_workflows/releases.py` showing the reuse is real.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `python3 -m pytest tests/test_releases_cli.py -q` output for named tests asserting: `run_list` human output contains the planned release's id6 AND version; `run_list` with `--json` emits parseable JSON whose record count matches `list_releases`; `run_list` with `--agent` emits `aw.agent/v1` JSONL (assert the `schema` key equals `aw.agent/v1`); `run_show next` output names the release AND lists each blocker's id6 with its status; `run_new` WITHOUT `--apply` writes NO file (assert the releases dir listing is byte-identical before/after) and WITH `--apply` creates a conformant record that `aw check releases` then passes. Exit codes asserted explicitly: 0 clean, 2 on a bad selector.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted terminal output of each real invocation: `aw releases` (bare, defaults to list), `aw release` (alias), `aw releases list`, `aw releases show next`, and `aw releases new --version 9.9.9 --summary "probe"` (preview, no `--apply`) - each exiting 0 with the expected content. PLUS `aw releases --help` showing exactly the subcommands `list`, `show`, `new` and NOT `check`. PLUS the adversarial assertion: `aw releases check` MUST fail as an unknown subcommand (paste the nonzero exit / usage error), proving the duplicate validator was not reintroduced.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `aw completion bash | grep -c releases` (nonzero) and the same for zsh and fish, showing all three generated scripts carry the verb. PLUS pasted dynamic completion output proving real resolution, not a static list: `aw __complete --cword 3 -- aw releases show` MUST emit the actual planned release id6 (`f33nrj`) and the `next` sentinel - assert those exact tokens appear. PLUS a test in `tests/test_completion.py` asserting the same, so a future refactor cannot silently drop it.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `python3 -m pytest tests/test_releases.py tests/test_releases_cli.py -q` summary line AND a full default-suite run `python3 -m pytest -p no:randomly` summary line, both green with the counts shown (a bare "all tests passing" claim is NOT acceptable evidence). PLUS pasted `grep -n "aw releases" .aw/records/releases/README.md` showing the documented usage, and `aw check releases` still exiting 0 (regression: the new verb did not break the canonical validator). Any V-item whose command was not actually run stays `pending`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (add the missing `releases` owner verb); E-items are ordered sub-steps of that single deliverable (primitives -> runners -> CLI wiring -> completion -> docs/tests).

Execution contract:

1. Open questions: OQ-01 resolved; execution requires explicit human approval.
2. Scope fence: touch ONLY the declared Scope-Paths. Do NOT add a `releases check` subcommand (`aw check releases` is the canonical validator, check_engine.py:489) and do NOT re-implement the blocker scan (reuse `attention.release_blockers`, attention.py:582). If the work seems to need more, STOP and report.
3. Honesty rule (HARD MUST): every V-item's Observed evidence is the ACTUAL pasted stdout/exit code of the named command. "All tests passing", "verified", or a summarized result is NOT evidence; a V-item whose command was not run stays `Result: pending`.
4. Reuse rule: prefer extending the existing surfaces (`resolve_release`, `describe_planned_release`, `validate_release`, `attention.release_blockers`, the existing `completion.py` tables and `__complete`) over new parallel implementations. A second path that answers the same question as the board is a defect, not a feature.
5. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push; never `--no-verify`.
6. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed.
