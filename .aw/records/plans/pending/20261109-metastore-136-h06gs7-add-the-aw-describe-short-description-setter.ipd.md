# IPD: Add the aw describe short-description setter

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.2 SHORT DESCRIPTION requires a setter for the short description of an existing record. Measured: no `aw describe` verb exists (`rg -n "\"describe\"" agent_workflows/cli.py agent_workflows/command_surface.py`: no match). This is part of `6e93gt` (itself part of `xexn45`), split 2026-11-09.
- Scope: Add `aw describe <id6> --summary|--clear [--apply]` (`6e93gt` E-02), registered in `cli`, `command_surface` and `docs/cli-output-contract.md`. EXCLUDES: `--summary` at creation (`fekdwv`, `bir7xm`, `py2vu9`), the `CHANGELOG.md` line (`xexn45` E-14).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/artifact_meta.py, docs/cli-output-contract.md, tests/test_writers_create_summary.py, .aw/records/plans/pending/20261109-metastore-136-h06gs7-add-the-aw-describe-short-description-setter.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94, executed:n5sxxk, executed:fekdwv, executed:py2vu9
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 136
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: h06gs7

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 6e93gt (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw describe` sets or clears the short description on any existing record, including a terminal one, through `artifact_meta`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the setter

- [ ] E-01 Add the short-description setter `aw describe <id6> --summary <text> [--apply]` and `aw describe <id6> --clear [--apply]` (preview by default), registered in `cli`, `command_surface` and `docs/cli-output-contract.md`. It appends one `set` (or `unset`) of `short_description` through `artifact_meta.append` with no status change and is accepted on a terminal record (OQ-30: a terminal log accepts a `set` or `unset` of `short_description`). It resolves the selector through `selectors.resolve` and refuses zero or several matches with exit 2 (the `zyj8io` convention). Test module `tests/test_writers_create_summary.py`.
  - Depends on: none
  - Expected outcome: `aw describe <id6> --summary X` previews and writes nothing; `--apply` writes the field and one history line; the same call on an executed plan succeeds; `--clear --apply` removes it; an unknown id6 exits 2.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`. In phase B, `append` and `create` render through the one legacy renderer `artifact_meta.write_legacy` (file form) and `artifact_meta.render_legacy_text` (string form), both added by `7yr827`.
- UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4); atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`.
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).

## Findings

| Id | Evidence (measured 2026-11-09 at `3d0ddb845`) | Finding |
|---|---|---|
| F-01 | `rg -n "\"describe\"" agent_workflows/cli.py agent_workflows/command_surface.py`: no match | A new verb. |
| F-02 | Hidden units: one verb, `cli`, `command_surface`, `docs/cli-output-contract.md`, five transcript cases | One item. |

## Proposed changes (ordered, validatable)

1. Add `aw describe` (E-01).

## Deferred / out of scope (with reason)

- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` reconciliation of the `--summary` options and the `CHANGELOG.md` line, and the full gates of the writer move.
  - Carrier: xexn45
- The walkthrough-creating command `aw walkthrough new`, which lands with the documents that describe it.
  - Carrier: 90iqr1

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/artifact_meta.py` is declared in case the terminal-record acceptance needs a registry flag; acknowledge it at finalize when unmodified.

## Required tests / validation

Adds the `describe` cases to `tests/test_writers_create_summary.py` (created by `fekdwv`).

## Spec / documentation sync

`docs/cli-output-contract.md` gains the `aw describe` leaf here. No spec change.

## Open questions

None open. Every question this work raised was resolved before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the transcript in a fixture repository: `aw describe <id6> --summary "Adds a widget."` (preview, exit 0, `git status --porcelain` empty), the same with `--apply` (exit 0, `git diff` shows one `- Short-Description:` line and one history line), the same on an executed plan (exit 0), `--clear --apply` (bullet removed), and `aw describe zzzzzz --summary x; echo $?` printing `2`; plus `python3 -m pytest -o addopts="" -v tests/test_writers_create_summary.py -k describe` with each of those five cases PASSED by name, and `git diff docs/cli-output-contract.md` showing the new leaf.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit h06gs7 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize h06gs7` itself.
