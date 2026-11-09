# IPD: Move the releases create and line-setter writers onto artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires every metadata writer to write through `artifact_meta` in phase B. The releases module still builds its bullets and history lines by hand (measured: 11 bullet literals and 4 history references in `agent_workflows/releases.py`). This is part of `g6tw94` (itself part of `xexn45`), split 2026-11-09 so each item names one module's writers.
- Scope: Move `releases.create_release` and `releases.plan_release` onto `artifact_meta.create` (`g6tw94` E-01, releases subset) and `releases.set_item_dependencies_line` and `releases.set_graduated_to_line` onto `artifact_meta.append` (`g6tw94` E-02, releases subset). EXCLUDES: specs (`b3l7y6`), backlog (`jlwedt`), the family audit (`g6tw94`).
- Scope-Paths: agent_workflows/releases.py, agent_workflows/artifact_meta.py, .aw/records/plans/pending/20261109-metastore-134-3466h8-move-the-releases-create-and-line-setter-writers-onto-artifa.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 134
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3466h8

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from g6tw94 (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The releases create path and the two field-line setters write through `artifact_meta`, each keeping a named, tested behavior.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the test modules its V-item names GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/3466h8/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/3466h8/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: releases writers

- [ ] E-01 Move the releases creating commands onto `artifact_meta.create`, pinned first (`g6tw94` E-01, releases subset): `releases.create_release` and `releases.plan_release`. Each passes its fields and its created-history message as events; the body text stays the command's own rendering. Behaviors kept: preview prints the exact bytes `--apply` writes (`tests/test_releases.py::test_plan_release_previews_exactly_what_create_writes`); conformant output (`tests/test_releases_cli.py::test_apply_creates_a_record_that_check_releases_passes`); the UTC history date (`tests/test_history_date_clock.py`); descriptive refusals before any write (`tests/test_specs_releases_descriptive_safety.py`, `tests/test_descriptive_refusal_hoist.py`).
  - Depends on: none
  - Expected outcome: the five pinned modules pass before and after with equal outcome lists; `rg -n "Workflow history" agent_workflows/releases.py` shows no text-building of the history section inside `releases.create_release` or `releases.plan_release`.
  - Execution state: pending

- [ ] E-02 Move the releases field-line setters onto `artifact_meta.append`, pinned first (`g6tw94` E-02, releases subset): `releases.set_item_dependencies_line` and `releases.set_graduated_to_line` (called by the `status_set` engine; Order 06 keeps the call site). Behaviors kept: graduation lines (`tests/test_graduation_forward_links.py`); body preservation and idempotence of both line writers (`tests/test_releases_sibling_line_writers_bounding.py::test_setting_value_preserves_body`, `test_writer_idempotence`, `test_graduated_to_multi_value_replacement_and_body_preservation`).
  - Depends on: E-01
  - Expected outcome: the two pinned modules pass before and after with equal outcome lists.
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
| F-01 | `rg -n "^def (plan_release|create_release|set_item_dependencies_line|set_graduated_to_line)\(" agent_workflows/releases.py`: all four exist | Four writer functions, one file. |
| F-02 | Pinned-module test counts (`rg -c "^\s*def test_"`): `test_releases` 21, `test_releases_cli` 37, `test_history_date_clock` 5, `test_specs_releases_descriptive_safety` 19, `test_descriptive_refusal_hoist` 3, `test_graduation_forward_links` 9, `test_releases_sibling_line_writers_bounding` 9 | E-01 names 8 units, E-02 names 5. |
| F-03 | `rg -l "set_item_dependencies_line|set_graduated_to_line" tests/`: only `tests/test_releases_sibling_line_writers_bounding.py` | That module was not pinned in `g6tw94`; it is the direct test of the two setters, so it is added to the E-02 pin list here (an addition, not a removal). |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). No reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free).

## Proposed changes (ordered, validatable)

1. Move the releases create commands (E-01).
2. Move the two releases field-line setters (E-02).

## Deferred / out of scope (with reason)

- The family finish (the cross-module `rg` audit of the three modules and the commit) and, after the whole writer move, the merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the documentation lines and the full gates.
  - Carrier: g6tw94

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/artifact_meta.py` is declared in case a field mapping must be added; acknowledge it at finalize when unmodified.

## Required tests / validation

No new module. Pinned before and after (equal outcome lists): the five modules of V-01 and the two of V-02.

## Spec / documentation sync

None. Implements `4sd62s` section 7 step 4 for the releases module; no documented behavior changes.

## Open questions

None open. Every question this work raised was resolved before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `diff` of `.aw/state/3466h8/E-01-before.txt` and `.aw/state/3466h8/E-01-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_releases.py::test_plan_release_previews_exactly_what_create_writes`; `tests/test_releases_cli.py::test_apply_creates_a_record_that_check_releases_passes`; the per-module PASSED counts (equal before and after) of `tests/test_history_date_clock.py`, `tests/test_specs_releases_descriptive_safety.py` and `tests/test_descriptive_refusal_hoist.py`. Plus the E-01 `rg -n "Workflow history" agent_workflows/releases.py` output with each hit labeled by its enclosing `def`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/3466h8/E-02-before.txt` and `.aw/state/3466h8/E-02-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_releases_sibling_line_writers_bounding.py::test_setting_value_preserves_body`; `test_writer_idempotence`; `test_graduated_to_multi_value_replacement_and_body_preservation`; the per-module PASSED count (equal before and after) of `tests/test_graduation_forward_links.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 3466h8 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 3466h8` itself.
