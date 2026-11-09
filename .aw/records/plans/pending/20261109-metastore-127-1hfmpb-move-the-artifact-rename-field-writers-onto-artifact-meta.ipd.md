# IPD: Move the artifact_rename field writers onto artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires the rename and regroup verbs to write their metadata edits through `artifact_meta` in phase B, while the file move stays a git move until the cutover. Measured: `agent_workflows/artifact_rename.py` holds 11 hand-built bullet literals. This is the first part of `bsl45u` (itself part of `xexn45`), split 2026-11-09 so each item names one writer function.
- Scope: First capture the family baseline that `bsl45u` compares against, then move `artifact_rename._update_frontmatter_metadata` (the `aw rename <type>` metadata edit) and `artifact_rename._update_or_inject_set_metadata` (the `aw group <type>` Set and Order edit) onto `artifact_meta.append` (`bsl45u` E-01, artifact_rename subset). EXCLUDES: `plans_refs` (`fnu6kw`), research shelf verbs (`9gy5jk`), `rename` and path events (`cxxmyv`).
- Scope-Paths: agent_workflows/artifact_rename.py, agent_workflows/artifact_meta.py, .aw/records/plans/pending/20261109-metastore-127-1hfmpb-move-the-artifact-rename-field-writers-onto-artifact-meta.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 127
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1hfmpb

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from bsl45u (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The generic rename and regroup verbs edit Set, Order and Id only through `artifact_meta`, with their refusals and ledger behavior unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the test modules its V-item names GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/1hfmpb/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/1hfmpb/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: baseline and artifact_rename writers

- [ ] E-01 Before any edit of the rename family, capture the family baseline that `bsl45u` E-02 compares against: run the PIN-FIRST command over `tests/test_rename_ledger.py`, `tests/test_rename_group_machine_output.py`, `tests/test_mutation_result_facts.py` and `tests/test_artifact_refs_rewrite.py` into `.aw/state/bsl45u/family-before.txt`. These four modules exercise all three writer modules of the family (`artifact_rename`, `plans_refs`, `research_refs`), so they are compared once, after every part.
  - Depends on: none
  - Expected outcome: `.aw/state/bsl45u/family-before.txt` exists and lists only PASSED lines.
  - Execution state: pending

- [ ] E-02 Move `artifact_rename._update_frontmatter_metadata` onto `artifact_meta.append`, pinned first (`bsl45u` E-01): the Set, Order and injected-Id edits of `aw rename <type>` become `set` events; the file move stays `artifact_core.git_mv` and the rename ledger write is unchanged (D-4). Behaviors kept: the a88210 no-H1 rule and the rename verb (`tests/test_artifact_rename.py`, including `test_rename_prompts`, where the prompt id stays inside its comment); the spec id6 conversion (`tests/test_spec_id6_filenames.py::test_to_id6_preview_then_apply_injects_and_rewrites`, `test_to_id6_idempotent_on_clustered_spec`).
  - Depends on: E-01
  - Expected outcome: the two pinned modules pass before and after with equal outcome lists.
  - Execution state: pending

- [ ] E-03 Move `artifact_rename._update_or_inject_set_metadata` onto `artifact_meta.append`, pinned first (`bsl45u` E-01): the Set and Order edit of `aw group <type>` becomes `set` events, with validation for the whole batch before the first `write_legacy`, so a refused batch touches no file. Behaviors kept: `tests/test_artifact_group.py`.
  - Depends on: E-02
  - Expected outcome: `tests/test_artifact_group.py` passes before and after with equal outcome lists.
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
| F-01 | Raw writes attributed to the enclosing `def`: `_update_frontmatter_metadata` (2), `_update_or_inject_set_metadata` (1); callers `run_rename_generic` and `run_group_generic` | Two writer functions, one file. |
| F-02 | Pinned-module test counts (`rg -c "^\s*def test_"`): `test_artifact_rename` 7, `test_spec_id6_filenames` 21, `test_artifact_group` 8; shared: `test_rename_ledger` 13, `test_rename_group_machine_output` 14, `test_mutation_result_facts` 8, `test_artifact_refs_rewrite` 25 | E-01 names 5 units, E-02 6, E-03 3. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). No reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free).
- D-4 (rename ledger). KEPT until the cutover: `record_history.record_rename` still writes the gitignored sidecar; no `rename` event exists in phase B.

## Proposed changes (ordered, validatable)

1. Capture the family baseline (E-01).
2. Move the rename metadata edit (E-02).
3. Move the group Set and Order edit (E-03).

## Deferred / out of scope (with reason)

- The family close-out (the after-run of the four shared rename modules against `.aw/state/bsl45u/family-before.txt`, the D-4 ledger check), and the final gates of the writer move.
  - Carrier: bsl45u

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/artifact_meta.py` is declared in case a field mapping must be added; acknowledge it at finalize when unmodified.

## Required tests / validation

No new module. Pinned before and after: the modules of V-02 and V-03. E-01 writes the family baseline only.

## Spec / documentation sync

None. Implements `4sd62s` section 7 step 4 for `artifact_rename`; no documented behavior changes.

## Open questions

None open. Every question this work raised was resolved before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `wc -l .aw/state/bsl45u/family-before.txt` and `grep -c ^PASSED` of the same file (equal counts), plus `grep -c` per module showing a nonzero PASSED count for each of `tests/test_rename_ledger.py`, `tests/test_rename_group_machine_output.py`, `tests/test_mutation_result_facts.py` and `tests/test_artifact_refs_rewrite.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/1hfmpb/E-02-before.txt` and `.aw/state/1hfmpb/E-02-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_artifact_rename.py::test_rename_prompts`; `tests/test_spec_id6_filenames.py::test_to_id6_preview_then_apply_injects_and_rewrites`; `test_to_id6_idempotent_on_clustered_spec`; the per-module PASSED count (equal before and after) of `tests/test_artifact_rename.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the `diff` of `.aw/state/1hfmpb/E-03-before.txt` and `.aw/state/1hfmpb/E-03-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: the per-module PASSED count (equal before and after) of `tests/test_artifact_group.py`, with each of its test ids listed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. This part runs first among the `bsl45u` parts, because E-01 captures the family baseline before any rename writer changes.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 1hfmpb -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 1hfmpb` itself.
