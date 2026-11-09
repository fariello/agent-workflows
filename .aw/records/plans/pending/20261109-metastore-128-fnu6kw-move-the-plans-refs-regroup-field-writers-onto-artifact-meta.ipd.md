# IPD: Move the plans_refs regroup field writers onto artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires `aw rename plans` and `aw group plans` to write their metadata edits through `artifact_meta` in phase B. Measured: `agent_workflows/plans_refs.py` holds 4 hand-built bullet literals, written by `plans_refs._set_metadata` from `plans_refs.apply_renames`. This is part of `bsl45u` (itself part of `xexn45`), split 2026-11-09.
- Scope: Move `plans_refs._set_metadata` and its caller `plans_refs.apply_renames` onto `artifact_meta.append` (`bsl45u` E-01, plans_refs subset), and confirm `plans_archive.apply_shard_moves` stays a pure move. EXCLUDES: `artifact_rename` (`1hfmpb`), research shelf verbs (`9gy5jk`).
- Scope-Paths: agent_workflows/plans_refs.py, agent_workflows/artifact_meta.py, .aw/records/plans/pending/20261109-metastore-128-fnu6kw-move-the-plans-refs-regroup-field-writers-onto-artifact-meta.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:1hfmpb
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 128
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: fnu6kw

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from bsl45u (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The plans rename and regroup verbs edit metadata only through `artifact_meta`, and every invalid plan in a batch still refuses before any file is touched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the test modules its V-item names GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/fnu6kw/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/fnu6kw/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: plans_refs writers

- [ ] E-01 Move `plans_refs._set_metadata` and `plans_refs.apply_renames` onto `artifact_meta.append`, pinned first (`bsl45u` E-01): the Set and Order edits become `set` events, validated for the whole batch before the first `write_legacy`, so the yqv6b7 E-03 pre-pass refusal (an invalid plan raises before any file is touched) still holds. `plans_refs._set_metadata` keeps its signature as a thin adapter, because `tests/test_plans_order_grammar.py` calls it directly. Behaviors kept: Order preservation and refusals (`tests/test_plans_group_order_preservation.py`, `tests/test_plans_order_grammar.py::test_set_metadata_raises_on_unmatchable_order_line`).
  - Depends on: none
  - Expected outcome: the two pinned modules pass before and after with equal outcome lists.
  - Execution state: pending

- [ ] E-02 Confirm `plans_archive.apply_shard_moves` stays a pure move (phase B writes no path event): run `tests/test_plans_archive.py::test_move_is_tracked_git_rename` before and after E-01 and check that `agent_workflows/plans_archive.py` is unmodified.
  - Depends on: E-01
  - Expected outcome: the test passes before and after; `git diff --stat agent_workflows/plans_archive.py` is empty.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`. In phase B, `append` and `create` render through the one legacy renderer `artifact_meta.write_legacy` (file form) and `artifact_meta.render_legacy_text` (string form), both added by `7yr827`.
- UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4); atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`.
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- The rename ledger is `record_history.record_rename`, written by `artifact_rename` and `plans_refs`; the sidecar is gitignored (`.aw/.gitignore` `records/history.jsonl`).
- File moves stay `artifact_core.git_mv` in phase B; section 7: "the writers of path-bearing events start at the cutover commit".

## Findings

| Id | Evidence (measured 2026-11-09 at `3d0ddb845`) | Finding |
|---|---|---|
| F-01 | `rg -n "_set_metadata\(" agent_workflows/plans_refs.py`: the def and one call inside `apply_renames`; the ledger write `_rh.record_rename` is in `apply_renames` | One writer and its caller. |
| F-02 | Pinned-module test counts: `test_plans_group_order_preservation` 8, `test_plans_order_grammar` 12, `test_plans_archive` 15 | E-01 names 6 units, E-02 4. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). No reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free).
- D-4 (rename ledger). KEPT until the cutover: `record_history.record_rename` still writes the gitignored sidecar; no `rename` event exists in phase B.

## Proposed changes (ordered, validatable)

1. Move the plans_refs writer (E-01).
2. Confirm the archive shard move stays pure (E-02).

## Deferred / out of scope (with reason)

- The family close-out (the after-run of the four shared rename modules against `.aw/state/bsl45u/family-before.txt`, the D-4 ledger check), and the final gates of the writer move.
  - Carrier: bsl45u

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/plans_archive.py` is deliberately NOT declared: it stays a pure move.

## Required tests / validation

No new module. Pinned before and after: the modules of V-01 and V-02.

## Spec / documentation sync

None. Implements `4sd62s` section 7 step 4 for `plans_refs`; no documented behavior changes.

## Open questions

None open. Every question this work raised was resolved before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `diff` of `.aw/state/fnu6kw/E-01-before.txt` and `.aw/state/fnu6kw/E-01-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_plans_order_grammar.py::test_set_metadata_raises_on_unmatchable_order_line` (the batch-refusal-before-write behavior); the per-module PASSED counts (equal before and after) of `tests/test_plans_group_order_preservation.py` and `tests/test_plans_order_grammar.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the before and after PASSED line of `tests/test_plans_archive.py::test_move_is_tracked_git_rename` and the empty output of `git diff --stat agent_workflows/plans_archive.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit fnu6kw -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize fnu6kw` itself.
