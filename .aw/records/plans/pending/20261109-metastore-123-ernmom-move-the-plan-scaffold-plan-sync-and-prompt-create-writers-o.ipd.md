# IPD: Move the plan scaffold, plan sync and prompt create writers onto artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires every metadata writer to write through `artifact_meta` in phase B. `aw ipd scaffold`, `aw ipd sync` and `aw prompts new` still write metadata by hand (`rg -c "atomic_write\(|write_text\(|git_mv\("`: `ipd_authoring` 5, `prompts` 1). This is part of `n5sxxk` (itself part of `xexn45`), split 2026-11-09 so each item names one command's writers.
- Scope: Move `ipd_authoring.run_scaffold` and `prompts.run_new` (with `prompts.render_metadata_comment`) onto `artifact_meta.create` (`n5sxxk` E-01, scaffold and prompts subset) and `ipd_authoring.run_sync` onto `artifact_meta.append` (`n5sxxk` E-02, sync subset). EXCLUDES: research (`s95hj6`), adopt and set_records (`x2dxvf`), `--summary` (`py2vu9`); `ipd_authoring.backfill_plan_ids` and `ipd_authoring._atomic_write` are not named writers (`xexn45` F-09 records them).
- Scope-Paths: agent_workflows/ipd_authoring.py, agent_workflows/prompts.py, agent_workflows/artifact_meta.py, .aw/records/plans/pending/20261109-metastore-123-ernmom-move-the-plan-scaffold-plan-sync-and-prompt-create-writers-o.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 123
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ernmom

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from n5sxxk (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The plan scaffold, the plan id sync and the prompt create command write through `artifact_meta`, each keeping a named, tested behavior.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the test modules its V-item names GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/ernmom/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/ernmom/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: plan and prompt writers

- [ ] E-01 Move the plan scaffold onto `artifact_meta.create`, pinned first (`n5sxxk` E-01, scaffold subset): `ipd_authoring.run_scaffold` passes its fields and its created-history message as events; the body skeleton stays the command's own rendering. Behaviors kept: preview prints the exact bytes `--apply` writes and writes nothing (`tests/test_ipd_authoring.py::test_dry_run_writes_nothing`); conformant output (`tests/test_ipd_authoring.py::test_apply_writes_conforming_child`); the UTC history date (`tests/test_scaffold_history_clock.py`).
  - Depends on: none
  - Expected outcome: the two pinned modules pass before and after with equal outcome lists; `rg -n "Workflow history" agent_workflows/ipd_authoring.py` shows no text-building of the history section inside `ipd_authoring.run_scaffold`.
  - Execution state: pending

- [ ] E-02 Move the plan id sync onto `artifact_meta.append`, pinned first (`n5sxxk` E-02, sync subset): `ipd_authoring.run_sync` (the `Highest E allocated` watermark set). Behaviors kept: watermark (`tests/test_ipd_authoring.py::test_sync_assigns_from_watermark_and_advances`, `test_sync_backfills_missing_id_and_leaves_present_id`).
  - Depends on: E-01
  - Expected outcome: `tests/test_ipd_authoring.py` passes before and after with equal outcome lists.
  - Execution state: pending

- [ ] E-03 Move the prompt create command onto `artifact_meta.create`, pinned first (`n5sxxk` E-01, prompts subset): `prompts.run_new` with `prompts.render_metadata_comment`, so the `aw-prompt` comment is rendered by the legacy writer's comment form. Behaviors kept: preview prints the intended path and writes nothing (`tests/test_prompts_new.py::test_dry_run_prints_intended_path_and_writes_nothing`); the prompt comment stays the single first line with the body byte-identical (`tests/test_prompts_set_surface.py::test_comment_write_with_body_byte_identity`).
  - Depends on: none
  - Expected outcome: the two pinned modules pass before and after with equal outcome lists; `tests/test_prompts_set_surface.py` still calls `prompts.render_metadata_comment` as a thin adapter with its signature unchanged.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`. In phase B, `append` and `create` render through the one legacy renderer `artifact_meta.write_legacy` (file form) and `artifact_meta.render_legacy_text` (string form), both added by `7yr827`.
- UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4); atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`.
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- The prompt mirror is the single `aw-prompt` comment (`prompts.render_metadata_comment`, `inject_metadata_id6`, `update_metadata_status`); nothing visible may precede the prompt body (spec `20260808-1958-01-prompt-purity-lint` R1/P4).

## Findings

| Id | Evidence (measured 2026-11-09 at `3d0ddb845`) | Finding |
|---|---|---|
| F-01 | Raw writes attributed to the enclosing `def` (`rg -n "atomic_write\(|write_text\("` then the nearest preceding `def`): `prompts.run_new`, `ipd_authoring.run_scaffold`, `ipd_authoring.run_sync`, `ipd_authoring.backfill_plan_ids`, `ipd_authoring._atomic_write` (2) | `backfill_plan_ids` and `_atomic_write` are not named writers; `xexn45` records them in F-09 with a reason. |
| F-02 | Pinned-module test counts (`rg -c "^\s*def test_"`): `test_ipd_authoring` 31, `test_scaffold_history_clock` 8, `test_prompts_new` 22, `test_prompts_set_surface` 6 | E-01 names 6 units, E-02 3, E-03 6. |
| F-03 | `tests/test_prompts_set_surface.py` calls `prompts.render_metadata_comment` directly | The function keeps its signature as a thin adapter over the legacy writer, so the pin stays valid without editing assertions; Order 11 (`9o83cr`) may delete the adapter. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). No reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free).

## Proposed changes (ordered, validatable)

1. Move the plan scaffold (E-01).
2. Move the plan id sync (E-02).
3. Move the prompt create command (E-03).

## Deferred / out of scope (with reason)

- The family finish (the cross-module `rg` audits of the five modules and the core gate) and, after the whole writer move, the merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the documentation lines and the full gates.
  - Carrier: n5sxxk

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/artifact_meta.py` is declared for the prompt comment field mapping; acknowledge it at finalize when unmodified.

## Required tests / validation

No new module. Pinned before and after (equal outcome lists): the modules of V-01, V-02 and V-03.

## Spec / documentation sync

None. Implements `4sd62s` section 7 step 4 for these commands; no documented behavior changes.

## Open questions

None open. Every question this work raised was resolved before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `diff` of `.aw/state/ernmom/E-01-before.txt` and `.aw/state/ernmom/E-01-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_ipd_authoring.py::test_dry_run_writes_nothing` (both classes); `test_apply_writes_conforming_child`; the per-module PASSED count (equal before and after) of `tests/test_scaffold_history_clock.py`. Plus the E-01 `rg -n "Workflow history" agent_workflows/ipd_authoring.py` output, each hit labeled by its enclosing `def`, none inside `ipd_authoring.run_scaffold`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/ernmom/E-02-before.txt` and `.aw/state/ernmom/E-02-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_ipd_authoring.py::test_sync_assigns_from_watermark_and_advances`; `test_sync_backfills_missing_id_and_leaves_present_id`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the `diff` of `.aw/state/ernmom/E-03-before.txt` and `.aw/state/ernmom/E-03-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_prompts_new.py::test_dry_run_prints_intended_path_and_writes_nothing`; `tests/test_prompts_set_surface.py::test_comment_write_with_body_byte_identity`; the per-module PASSED counts (equal before and after) of both modules.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit ernmom -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize ernmom` itself.
