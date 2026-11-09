# IPD: Move the readiness re-check and coverage writers onto artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.4 requires the readiness re-check to write one gate `review` event and the coverage record one `op: coverage` event, so readiness and coverage can only be written by their owning events (AC-15). Measured: 61 history lines contain `readiness re-check` and 39 plans carry `- Coverage:` (`xexn45` F-06). This is part of `8q27jt` (itself part of `xexn45`), split 2026-11-09 so each item names one writer.
- Scope: Move `plan_readiness.recheck_readiness` (`8q27jt` E-01) and `coverage_record.write` (`8q27jt` E-02) onto `artifact_meta.append`, and create `tests/test_writers_obligations.py` with the readiness and coverage refusal cases, which `xexn45` E-13 extends. EXCLUDES: finalize scope fields (`9qhtrc`, `1dvb08`), retirement (`8q27jt`), the `status_set` engine (`2xwb9b`).
- Scope-Paths: agent_workflows/plan_readiness.py, agent_workflows/readiness_recheck.py, agent_workflows/coverage_record.py, agent_workflows/artifact_meta.py, tests/test_writers_obligations.py, .aw/records/plans/pending/20261109-metastore-130-d4w53g-move-the-readiness-re-check-and-coverage-writers-onto-artifa.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 130
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: d4w53g

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 8q27jt (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The readiness re-check and the coverage record write through `artifact_meta` as their owning events, and a hand-built `set readiness` or `set coverage` is refused with no byte written.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the test modules its V-item names GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/d4w53g/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/d4w53g/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: readiness re-check

- [ ] E-01 Move `plan_readiness.recheck_readiness` (`aw ipd recheck-readiness`) onto `artifact_meta.append` as ONE gate `review` event (4.4, 4.1a K2), pinned first: `review_kind: gate`, `readiness: go-pending-approval` (still pinned to `plan_readiness.RECHECK_TARGET_READINESS`, never caller input), and `message` = the existing `plan_readiness.format_recheck_history_entry` text. The legacy writer renders it as today: the `- Readiness:` line replaced and one `readiness re-check` history line prepended. Behaviors kept: `tests/test_plan_readiness_recheck.py` (40 tests, including `test_the_only_permitted_write_is_no_go_to_go_pending_approval`, `test_apply_writes_exactly_the_readiness_line_and_one_history_record`, `test_the_recheck_CLEARS_once_the_stale_finding_is_closed`), `tests/test_review_record_classifier.py`, `tests/test_read_verb_zero_match_refusal.py`.
  - Depends on: none
  - Expected outcome: the three pinned modules pass before and after with equal outcome lists.
  - Execution state: pending

- [ ] E-02 Set the gate event's `verdict` without minting one (`8q27jt` E-01, verdict rule): `plan_readiness.newest_verdict` returns a POLARITY and the raw newest review record, not a verdict string, so the event's `verdict` is the verdict token that `plan_readiness.classify_verdict` reads from that raw record (a member of `plan_readiness.VERDICTS`, as K2 requires of a `gate` event); when no token can be read the recheck refuses exactly as it does today. `readiness_recheck._run_stale_findings` and its call to `review_findings.append_round_resolving_stale` stay text edits of the REVIEW FILE body (N3), not metadata. Create `tests/test_writers_obligations.py` with a readiness case: a hand-built `set readiness=go` through `artifact_meta.append` is refused with no byte written, while the recheck path writes `go-pending-approval`.
  - Depends on: E-01
  - Expected outcome: the new readiness case passes; `tests/test_plan_readiness_recheck.py` still passes with an equal outcome list.
  - Execution state: pending

### Task group 2: coverage record

- [ ] E-03 Move `coverage_record.write` onto `artifact_meta.append` as ONE `op: coverage` event carrying `coverage` and `coverage_fingerprint` (4.4), pinned first; `coverage_checked` is written only as the legacy bullet that the legacy writer derives from the event's `at` day and the actor model (`<YYYY-MM-DD> by <model>`, its migrated-value format), so the post-cutover log never carries it. The `## Coverage findings` body section stays body text written by `coverage_record` (N3). The history line keeps the shape `- <day> coverage <verdict> (<tool>): fingerprint <12>, model <m>`, which `IPD-M112` reads in phase B. Add a coverage case to `tests/test_writers_obligations.py`: a `set coverage=pass` outside an `op: coverage` event is refused with no byte written. Behaviors kept: `tests/test_coverage_record.py` (`test_write_and_read_fail`, `test_write_pass_removes_findings_and_lints_conforming`, `test_checklist_edit_makes_is_current_false`), `tests/test_coverage_not_written.py`, `tests/test_history_date_clock_residual.py::test_coverage_record_write_records_utc_date`, `tests/test_orchestrator_readiness.py`, `tests/test_gradcover_end_to_end.py`.
  - Depends on: E-02
  - Expected outcome: the five pinned modules pass before and after with equal outcome lists; the coverage refusal case passes.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`. In phase B, `append` and `create` render through the one legacy renderer `artifact_meta.write_legacy` (file form) and `artifact_meta.render_legacy_text` (string form), both added by `7yr827`.
- UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4); atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`.
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- Finalize scope evidence is `evidence["scope_reconciliation"]` with `reasons` and `widened_paths` (`ipd_lifecycle._finalize_transaction`, `runner_shared.compute_scope_reconciliation`).
- Rollup retirement is `ipd_lifecycle.retire_orchestrator` -> `_finalize_transaction` with `evidence["transition"] == "orchestrator-rollup"`.

## Findings

| Id | Evidence (measured 2026-11-09 at `3d0ddb845`) | Finding |
|---|---|---|
| F-01 | Hidden units of the readiness move: `plan_readiness.recheck_readiness`, `plan_readiness.newest_verdict`, `plan_readiness.classify_verdict`, 3 pinned modules (`test_plan_readiness_recheck` 40, `test_review_record_classifier` 13, `test_read_verb_zero_match_refusal` 11 tests), 1 refusal case | Split into the event move (E-01) and the verdict rule with its refusal test (E-02). |
| F-02 | Hidden units of the coverage move: `coverage_record.write`, 5 pinned modules (`test_coverage_record` 7, `test_coverage_not_written` 8, `test_history_date_clock_residual` 2, `test_orchestrator_readiness` 24, `test_gradcover_end_to_end` 5 tests), 1 refusal case | E-03 names 8 units. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). No reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free).

## Proposed changes (ordered, validatable)

1. Readiness re-check as one gate `review` event (E-01).
2. The verdict rule and the readiness refusal test (E-02).
3. Coverage as one `op: coverage` event (E-03).

## Deferred / out of scope (with reason)

- The final merge-independence test, the AC-21 obligations test (which extends `tests/test_writers_obligations.py`), the raw-write audit (F-09), the documentation lines, and the full gates of the writer move.
  - Carrier: xexn45
- Finalize scope fields and the path-root rule.
  - Carrier: 9qhtrc
- Retirement writers.
  - Carrier: 8q27jt

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

New core test module: `tests/test_writers_obligations.py` (readiness and coverage refusal cases; `xexn45` E-13 adds the AC-21 and AC-6 cases). Contributes to `4sd62s` AC-15 and AC-14a (1)-(2) (owners named in `xexn45`).

## Spec / documentation sync

None. Implements `4sd62s` 4.4 for these two writers.

## Open questions

None open. Every question this work raised was resolved before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `diff` of `.aw/state/d4w53g/E-01-before.txt` and `.aw/state/d4w53g/E-01-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_plan_readiness_recheck.py::test_the_only_permitted_write_is_no_go_to_go_pending_approval`; `test_apply_writes_exactly_the_readiness_line_and_one_history_record`; `test_the_recheck_CLEARS_once_the_stale_finding_is_closed`; the per-module PASSED counts (equal before and after) of `tests/test_review_record_classifier.py` and `tests/test_read_verb_zero_match_refusal.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_obligations.py -k readiness` with the refusal case PASSED by name, quoting its assertion that the refused `set readiness=go` leaves the file sha256 unchanged and that the recheck path writes `go-pending-approval`; plus the re-run PASSED count of `tests/test_plan_readiness_recheck.py` equal to the E-01 after-list.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the `diff` of `.aw/state/d4w53g/E-03-before.txt` and `.aw/state/d4w53g/E-03-after.txt` (must print nothing), and from `-after.txt` the PASSED lines of each named unit: `tests/test_coverage_record.py::test_write_and_read_fail`; `test_write_pass_removes_findings_and_lints_conforming`; `test_checklist_edit_makes_is_current_false`; `tests/test_history_date_clock_residual.py::test_coverage_record_write_records_utc_date`; the per-module PASSED counts (equal before and after) of `tests/test_coverage_not_written.py`, `tests/test_orchestrator_readiness.py` and `tests/test_gradcover_end_to_end.py`. Plus `python3 -m pytest -o addopts="" -v tests/test_writers_obligations.py -k coverage` with the refusal case PASSED by name.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit d4w53g -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize d4w53g` itself.
