# IPD: Widen the HANDOFF arm so every From-Backlog carrier, gated or not, must be terminal

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `kntbbc` (residue of `2o5wka` OQ-02 and `jf3j4q`'s deferred row naming `kntbbc` as carrier): `check_engine.evaluate_blocking_close`'s HANDOFF arm builds `same_gate_carriers` by keeping only carriers whose gate `_same_release` matches the item's, then requires `all(_carrier_eval(_c) for _c in same_gate_carriers)`. A sibling carrier with NO `- Blocks-Release:` line (or a different one) is dropped by that filter, so `aw backlog set <item> --status done` closes a gated item while that sibling is still pending. `runner_shared.evaluate_backlog_close` filters carriers by KIND, not by gate, and refuses the same close. The two "single-sourced" close predicates therefore still disagree on which carriers count.
- Scope: IN: (a) in `check_engine.evaluate_blocking_close`'s HANDOFF arm, keep the existing ENTRY condition (at least one same-gate carrier must exist, so the gate is still provably handed to a carrier that inherited it) but require EVERY `From-Backlog` carrier of the item, whatever its gate, to be executed/implemented before HANDOFF returns legitimate; (b) make the not-shipped refusal name the carriers that actually block (including an ungated or differently gated sibling); (c) align `check_engine.release_gate_warnings`' `check.orphaned-live-blocker` `--status done` advice so it is emitted only when every From-Backlog PLAN of the item is executed (preserving its plans-only design); (d) add a third grandfathered cohort description in `check_engine.check_release_gate_consistency` for "same-gate carriers executed, a sibling carrier is not" so the advisory detail is not false; (e) behavioral tests for every case; (f) correct the five prose sites that state the HANDOFF rule as "EVERY same-gate carrier" (repo-local `AGENTS.md` paragraph, `.aw/records/backlog/README.md`, the two `engine.py` pre-commit template comments, the `cli.py` help description, the hook module docstring) plus a `CHANGELOG.md` line. OUT: SATISFIED and DE-GATED arms, the `graduated`/`parked`/priority-demote branches, the lane-carrier override mechanism, the runner (`runner_shared.evaluate_backlog_close` is the REFERENCE converged onto, not edited), `check.from-backlog-gate-mismatch` (unchanged), widening `release_gate_warnings` to spec carriers, and the SATISFIED-arm work owned by pending `ncmugb`.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/hooks/backlog_blocking_close_gate.py, tests/test_backlog_handoff_close.py, tests/test_check_engine_release_gate.py, AGENTS.md, .aw/records/backlog/README.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: kntbbc
- Set: kntbbc
- Order: 1
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: jykyqb

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: jykyqb verified (set kntbbc, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003 (all fixed; divergence re-reproduced in a scratch repo (check_engine HANDOFF legitimate, runner refuses); corpus re-measured 479 gated items, 0 flips; retired-sibling semantics decided and pinned; unsatisfiable `aw check` 0-errors bar corrected).
- 2026-10-12 to-review (aw set): Graduated from backlog kntbbc. Divergence reproduced, E-04 prototyped against the full bare suite (identical 38-failure pre-existing set with and without, 0 new) and the corpus (0 of 473 gated items flip); prototype reverted.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `check_engine.evaluate_blocking_close` refuse a HANDOFF close while ANY `From-Backlog` carrier of the item (gated, ungated, or differently gated) is not executed/implemented, so it agrees with `runner_shared.evaluate_backlog_close` on which carriers count, and make every advisory and prose surface that describes the HANDOFF rule say the same thing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [x] E-01 REPRODUCE THE DIVERGENCE AND CAPTURE A SUITE BASELINE at the executing HEAD, before any edit. (a) On a `git init` scratch repo (a resolvable `next` release record, a `graduated` item gated `next`, one EXECUTED carrier gated `next`, one PENDING carrier with `- From-Backlog:` and NO `- Blocks-Release:` line), call `check_engine.evaluate_blocking_close(repo, item, "done")` and `runner_shared.evaluate_backlog_close(repo, item_id6, [])` and record both verdicts. (b) Run the full suite BARE (`python3 -m pytest`, no added flags) and save the sorted `FAILED` lines to a scratch file as the pre-edit failure set.
  - Depends on: none
  - Expected outcome: `evaluate_blocking_close` returns `legitimate=True, path='HANDOFF'`; `evaluate_backlog_close` returns `close=False` naming the pending carrier. A pre-edit failure set exists for E-10 to compare against.
  - STOP CONDITION: if the two verdicts already AGREE (both refuse), another change has landed the fix; report and stop rather than editing.
  - The baseline failure set is NOT expected to be empty. Measured at authoring (HEAD `f8452a0be`, this lane): `38 failed, 7181 passed, 2 skipped`, all 38 in modules unrelated to release gates (for example `tests/test_no_project_exit_is_cannot_run.py`, `tests/test_read_class_callers_refuse.py`, `tests/test_finalize_sendback.py`). The bar is "no NEW failure", not "green".
  - Execution state: performed

### Task group 2: tests first (they must fail before the fix)

- [x] E-02 ADD HANDOFF-ARM CASES to `tests/test_backlog_handoff_close.py` (class `BacklogHandoffCloseBehaviorTests`, reusing `_write_backlog_item`, `_write_plan`, `_write_spec`, whose `blocks_release=None` already omits the line). Each case drives `cli.main(["backlog", "set", "item01", "--status", "done", "--dir", ..., "--message", "close"])` and/or `check_engine.evaluate_blocking_close`, asserting exit code, the item's resulting directory, stderr and `verdict.path`/`verdict.legitimate`: (1) executed same-gate plan + PENDING UNGATED plan -> refused rc 1, item still in `graduated/`, stderr names the ungated plan's id; and in the same case assert `runner_shared.evaluate_backlog_close(self.repo, "item01", [])` is `close=False`, so the convergence is pinned by outcome; (2) executed same-gate plan + EXECUTED UNGATED plan -> allowed rc 0, `path == "HANDOFF"`, item in `done/`; (3) executed same-gate plan + PENDING plan gated to a DIFFERENT release value -> refused; (4) executed same-gate plan + UNGATED spec in `approved/` with `- Status: approved` -> refused, and the same with `- Status: implemented` -> allowed; (5) ONLY an executed UNGATED plan, no same-gate carrier -> still refused (unchanged entry condition); (6) executed same-gate plan + UNGATED plan in `superseded/` (`_write_plan(..., bucket="superseded", status="superseded", blocks_release=None)`) -> refused, stderr names the superseded plan, and `aw backlog set done item01 --blocks-release - ...` (DE-GATED) on the same tree -> allowed rc 0. Case (6) pins the OQ-01(c) decision that a retired sibling counts as unfinished, exactly as a retired SAME-gate carrier already does today and as the runner does. Each docstring cites `kntbbc` and states that cases (1), (3), (4-refused) and (6-refused) deliberately tighten the `2o5wka` same-gate rule.
  - Depends on: E-01
  - Expected outcome: run before E-04, cases (1), (3), (4-refused) and (6-refused) FAIL and cases (2), (4-allowed), (5) and (6-DE-GATED) PASS.
  - Case (3) needs no release record for the other value: `_same_release` falls back to string equality when a value does not resolve, so `blocks_release="other"` is a different gate.
  - Execution state: performed

- [x] E-03 ADD ADVISORY CASES to `tests/test_check_engine_release_gate.py`. (a) Beside `test_release_gate_warnings_multi_carrier_all_executed_remedy`: an `open` item gated `next` with an EXECUTED plan gated `next` and a PENDING plan with no `- Blocks-Release:` -> `check_engine.release_gate_warnings(repo)` yields one `check.orphaned-live-blocker` whose detail contains `--status graduated` and not `--status done`. (b) Beside `test_rule_blocking_close_grandfathered_cohort_details` (the "heh05a E-05 case 8" test): a `done` item gated `next` with an EXECUTED same-gate plan and a PENDING ungated plan, under the same cutover config, -> `check_engine.check_release_gates(repo, grandfathered=True)` reports one `check.blocking-close-grandfathered` whose detail contains `cohort: same-gate carrier(s) executed but a sibling carrier is not`.
  - Depends on: E-02
  - Expected outcome: before E-04/E-05/E-06, (a) FAILS (today the advice is `--status done`) and (b) FAILS (today no finding is emitted because the close is judged legitimate).
  - Do NOT change the existing case 8 assertions: the two existing cohort strings stay byte-identical (E-06).
  - Execution state: performed

### Task group 3: the predicate and its two advisory consumers

- [x] E-04 WIDEN THE HANDOFF ARM in `check_engine.evaluate_blocking_close`. In the block under the comment `# HANDOFF: EVERY From-Backlog PLAN or SPEC with the SAME Blocks-Release must be EXECUTED/IMPLEMENTED.`, keep building `same_gate_carriers` exactly as today, additionally keep `all_carriers = [p for p, _br in carrier_items]`, and change the legitimacy test to `same_gate_carriers and all(_carrier_eval(c) for c in all_carriers)`. In the not-shipped refusal (the `if same_gate_carriers:` block), list the carriers that are NOT terminal (computed with the same `_carrier_eval`), not only the same-gate ones, and keep its three fixes unchanged. Update the docstring's `HANDOFF` line and the arm's comment to state: at least one same-gate carrier exists AND every From-Backlog carrier, gated or not, is executed/implemented, matching `runner_shared.evaluate_backlog_close` (backlog `kntbbc`).
  - Depends on: E-03
  - Expected outcome: E-02's cases all pass. `carrier_items` is reused, so no new `find_from_backlog_artifacts` call is introduced (the single-item contract enforced by `tests/test_carrier_scan_single_item_contract.py` is untouched). The lane override still applies, because `_carrier_eval` is what iterates.
  - Do NOT change arm order (DE-GATED, HANDOFF, SATISFIED, refusals), `_same_release`, `_carrier_is_executed`, `_lane_carrier_is_executed`, or the verdict's `reason` string on the success path (`jf3j4q` recorded it as machine-consumed and deliberately left alone).
  - Execution state: performed

- [x] E-05 ALIGN `check_engine.release_gate_warnings`. Alongside `plan_gates_by_backlog`, accumulate per backlog id6 whether EVERY From-Backlog plan (any gate) is executed, and emit the `--status done` advice only when `gates_map[item_gate]` AND that all-plans flag are both true; otherwise emit the existing `--status graduated` advice. Keep the function plans-only and keep its single `_iter_plan_ipds` walk.
  - Depends on: E-04
  - Expected outcome: E-03(a) passes; `test_release_gate_warnings_multi_carrier_all_executed_remedy` and every other existing warning test still pass.
  - WHY: without this, `aw check` would advise `aw backlog set <id6> --status done`, exactly the command E-04 now refuses, which is the "advises the route that refuses" defect `2o5wka` E-05 already fixed once in this function.
  - Execution state: performed

- [x] E-06 ADD THE THIRD GRANDFATHERED COHORT in `check_engine.check_release_gate_consistency`'s grandfathered arm. Where `cohort_desc` is chosen, distinguish: no same-gate carrier -> existing `"no same-gate carrier"`; same-gate carriers present and not all executed -> existing `"same-gate carrier(s) present but not all executed"`; same-gate carriers all executed (so the refusal came from a sibling) -> new `"same-gate carrier(s) executed but a sibling carrier is not"`. Use `_carrier_is_executed`, reusing the `carrier_items` already read from `shared_carrier_idx`.
  - Depends on: E-05
  - Expected outcome: E-03(b) passes and the existing case 8 test still passes with its two strings unchanged.
  - Execution state: performed

### Task group 4: prose

- [x] E-07 UPDATE THE REPO-LOCAL RULE STATEMENTS. (a) `AGENTS.md`, the paragraph beginning "Close-legitimacy rule for a release-blocking backlog item" (BELOW `<!-- /aw:block -->`; anchor on that quoted string, not a line number, and make no edit inside any `<!-- aw:` block): fix (1) currently reads "HANDOFF, EVERY same-gate carrier (From-Backlog plan or spec) carrying `- From-Backlog: <this id6>` and the same `- Blocks-Release: <R>` must be executed or implemented"; restate it as: at least one carrier carrying `- From-Backlog: <this id6>` and the same `- Blocks-Release: <R>` must exist, and EVERY From-Backlog carrier of the item, whatever its gate, must be executed or implemented. Keep the "multi-carrier item stays `graduated`" clause. (b) `.aw/records/backlog/README.md`, the sentence containing "once every same-gate carrier executes": change it to "once every From-Backlog carrier, gated or not, executes". User-facing prose: no em or en dashes.
  - Depends on: E-06
  - Expected outcome: neither file contains the phrase "every same-gate carrier" / "EVERY same-gate carrier" any more; `git diff AGENTS.md` shows no line inside an `aw:` managed block changed.
  - CO-EDITOR: pending `ncmugb` (backlog `7lfe87`) declares `AGENTS.md` and `.aw/records/backlog/README.md` and edits the SATISFIED fix (2) wording. This item owns fix (1) only. If fix (2) has already been rewritten, that is `ncmugb` landing first: leave it.
  - Execution state: performed

- [x] E-08 UPDATE THE SHIPPED AND INSTALLED PROSE SITES that say "EVERY same-gate": (a) both occurrences in `agent_workflows/engine.py` (`_BACKLOG_CLOSE_GATE_PRECOMMIT_TEMPLATE` and `_BACKLOG_CLOSE_GATE_PRECOMMIT_BLOCK`), changing "HANDOFF: EVERY same-gate From-Backlog carrier (plan or spec)" to "HANDOFF: a same-gate From-Backlog carrier exists and EVERY From-Backlog carrier (plan or spec), gated or not,"; (b) the `cli.py` `_DESCRIPTIONS["backlog-blocking-close-gate"]` text "HANDOFF: EVERY same-gate From-Backlog carrier executed or implemented" to "HANDOFF: a same-gate From-Backlog carrier exists and EVERY From-Backlog carrier, gated or not, is executed or implemented"; (c) the `agent_workflows/hooks/backlog_blocking_close_gate.py` module docstring clause "HANDOFF (EVERY same-gate `From-Backlog` carrier present in the staged tree with the same `Blocks-Release` must be executed or implemented)" to say a same-gate carrier must exist and every `From-Backlog` carrier, gated or not, must be executed or implemented. Change ONLY the HANDOFF clause in each site (the `jf3j4q` boundary: leave the surrounding attribution, delegation and limits sentences untouched).
  - Depends on: E-07
  - Expected outcome: `grep -rn "EVERY same-gate" agent_workflows` returns nothing; `tests/test_backlog_close_gate_prose.py` passes unchanged (its regexes `HANDOFF[^)]*\bEVERY\b[^)]*From-Backlog` and `HANDOFF:[^)]*\bEVERY\b[^)]*From-Backlog` still match because no `)` precedes `EVERY` in the new text).
  - INSTALL SURFACE: (a) is written into every managed target that opts into the hook, so keep the edit to the clause. The new wording must keep a `)`-free run from `HANDOFF` through `EVERY` to `From-Backlog`; re-run the prose test rather than assuming.
  - Execution state: performed

- [x] E-09 ADD ONE `CHANGELOG.md` LINE under the pending `2.0.0` entry stating that `aw backlog set <item> --status done` on a release-gated item now also waits for any ungated or differently gated `From-Backlog` sibling plan or spec to execute, matching the runner's own close rule. User-facing prose: no em or en dashes.
  - Depends on: E-08
  - Expected outcome: `git diff CHANGELOG.md` shows one added line in the pending section and nothing else.
  - Execution state: performed

### Task group 5: validate

- [x] E-10 RUN THE FULL SUITE BARE AND RE-MEASURE. (a) `python3 -m pytest` with no added flags; save its sorted `FAILED` lines and diff against E-01's set. (b) `aw check release-gates`, and `aw check --agent` before (at E-01) and after, compared as per-rule finding counts. (c) Re-run the corpus measurement: one pass over `backlog._iter_items` with `check_engine._from_backlog_carrier_index(repo)` built ONCE; for every item with a `- Blocks-Release:`, compute `old = bool(same) and all(_carrier_is_executed(p) for p in same)` and `new = bool(same) and all(_carrier_is_executed(p) for p, _ in carriers)` (where `same` filters by `_same_release`), and list items where `old != new`.
  - Depends on: E-09
  - Expected outcome: (a) the post-edit failure set equals or is a subset of the pre-edit set; (b) `aw check release-gates` CONFORMS with 0 errors, and `aw check` shows no rule of the release-gate family (`check.blocking-*`, `check.from-backlog-*`, `check.orphaned-live-blocker`) whose count rose. `aw check` as a whole is NOT expected to exit 0: at review it already reported `findings`, exit 1, 123 findings from unrelated rules (e.g. 72 `check.lifecycle-transition-unvalidated`); (c) zero items flip (the gated-item count is live: 473 at authoring, 479 at review, both 0 flips). Measured at authoring with a prototype of E-04 (reverted): the bare suite produced the identical 38-failure set before and after, and 0 of 473 gated items changed verdict (`done` 321 legitimate / 105 not, unchanged). The only gated items with an ungated carrier at all are `1f9m2j`, `hyx1dg`, `t156g1`, each `done` with a single EXECUTED ungated carrier and no same-gate carrier, whose verdict E-04 does not change.
  - STOP CONDITION: any NEW failing test, or any flipped historical verdict that `aw check release-gates` now reports as an error, means report rather than adjust tests.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The close predicate is single-sourced: `check_engine.evaluate_blocking_close` backs `backlog` set (both spellings, via `status_set`), `set_records`, the `aw check` rule `check.blocking-item-closed-without-gate`, and `hooks.backlog_blocking_close_gate`, so E-04 reaches every surface without editing callers.
- A plan's terminal state is its PATH (`executed` segment), a spec's is its `- Status:` (`implemented`); `check_engine._carrier_is_executed` encodes both and is reused, not reimplemented.
- Per-item carrier lookups use `find_from_backlog_artifacts`; bulk work uses `_from_backlog_carrier_index`. `tests/test_carrier_scan_single_item_contract.py` enforces it; E-04 adds no lookup.
- Tests assert outcomes (exit codes, directories, verdict fields, stderr), never source structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). `tests/test_backlog_handoff_close.py` is the model: `git init` scratch repo, `AW_HOME`/`XDG_CONFIG_HOME` isolated.
- Run the suite BARE (`python3 -m pytest`); `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Sev | Finding | Why it matters |
|---|---|---|---|
| F-01 | MED | `check_engine.evaluate_blocking_close` HANDOFF arm: `if _same_release(repo_root, carrier_br, blocks_release, cache=release_cache): same_gate_carriers.append(_p)` then `if same_gate_carriers and all(_carrier_eval(_c) for _c in same_gate_carriers)`. A carrier whose gate is `None` or another value never enters the `all(...)`. | The hole `kntbbc` names. |
| F-02 | MED | `runner_shared.evaluate_backlog_close` takes `carriers = [Path(p) for p, _br in _ce.find_from_backlog_artifacts(repo, item_id6)]` (the gate is discarded), then requires every IPD carrier `plan_bucket(...) == "executed"` and, in the mixed case, every non-IPD carrier `_ce._carrier_is_executed`. | The reference E-04 converges onto. Both predicates already share `find_from_backlog_artifacts` and `_carrier_is_executed`; only the FILTER differs. |
| F-03 | MED | `2o5wka` F-06/OQ-02 measured the divergence and deferred it because widening "changes WHICH carriers the arm considers" (different blast radius) and because `check.from-backlog-gate-mismatch` reports the shape. `jf3j4q`'s Deferred section names `kntbbc` as the carrier. | Provenance; the blast radius is what F-05 measures. |
| F-04 | LOW | `check.from-backlog-gate-mismatch` (`check_release_gate_consistency` Rule 2) skips TERMINAL carriers (`is_retired`) and only flags LIVE ones. So it reports a live ungated sibling, but it is an `aw check` error, not a refusal at the setter: the hand close still succeeds today. | Why the advisory rule does not make this fix redundant. |
| F-05 | MED | BLAST RADIUS, MEASURED BY PROTOTYPE at HEAD `f8452a0be` in this lane (edit reverted, `git status` clean afterwards): with E-04's legitimacy change alone, the targeted modules (`test_backlog_handoff_close`, `test_check_engine_release_gate`, `test_gate_drop_audit`, `test_from_backlog_cardinality`, `test_status_set_partial_batch`) gave `115 passed`; the bare full suite gave `38 failed, 7181 passed, 2 skipped` both with and without the prototype, and `comm -3` of the two sorted FAILED sets was EMPTY. | No existing test pins the permissive behavior, unlike `2o5wka`, which had to reverse one. The 38 are pre-existing and unrelated. |
| F-06 | MED | CORPUS EFFECT, MEASURED: 473 gated backlog items; old vs new HANDOFF legitimacy differs for 0 of them. Only three gated items have any ungated carrier (`1f9m2j`, `hyx1dg`, `t156g1`, all `done`, one executed ungated carrier, zero same-gate carriers), and they are judged identically by both rules. `aw check release-gates` CONFORMS (`169 release-gates checked, errors 0`). | No grandfathering decision is needed; the change is purely forward-looking. |
| F-07 | LOW | `release_gate_warnings` folds `gates_map[gate] = gates_map.get(gate, True) and is_exec` keyed by gate, so a pending ungated plan lands under key `""` and does not affect the `next` key's `--status done` advice. | E-05: otherwise `aw check` advises a close E-04 refuses. |
| F-08 | LOW | The grandfathered arm's `cohort_desc` is chosen only from "no same-gate carrier" vs "same-gate carrier(s) present but not all executed"; after E-04 a refusal can come from a sibling while every same-gate carrier is executed, making the second string false. `tests/test_check_engine_release_gate.py` asserts both existing strings verbatim. | E-06 adds a third string instead of rewording the two existing ones. |
| F-09 | LOW | Five prose sites say "EVERY same-gate": `AGENTS.md` fix (1), `.aw/records/backlog/README.md`, `engine.py` (two template copies), `cli.py` `_DESCRIPTIONS`, hook docstring (found by `grep -rn "EVERY same-gate\|every same-gate carrier"`). `tests/test_backlog_close_gate_prose.py` asserts on the installed YAML and rendered help via `HANDOFF[^)]*\bEVERY\b[^)]*From-Backlog`. `DECISIONS.md` also says "all same-gate From-Backlog carriers executed" inside a dated decision entry. | E-07/E-08 scope. `DECISIONS.md` is a historical record and is NOT edited (see Deferred). |
| F-10 | LOW | Pending `ncmugb` (`to-review`, backlog `7lfe87`) edits `evaluate_blocking_close`'s SATISFIED arm and declares `AGENTS.md` and the backlog README. Its E-02 forbids changing "the HANDOFF arm"; this plan forbids changing SATISFIED. No other pending plan mentions `same_gate_carriers` or `release_gate_warnings` (`grep -ln` over `.aw/records/plans/pending/`). | Semantic split recorded; `- Item-Dependencies: none` is correct because the runner isolates and merges each plan. |

## Proposed changes (ordered, validatable)

1. E-01: reproduce the divergence and capture the suite baseline.
2. E-02, E-03: add failing behavioral tests for the predicate, the warning advice, and the grandfathered cohort.
3. E-04: widen the HANDOFF legitimacy test to every carrier, keeping the same-gate entry condition; name the blocking carriers in the refusal.
4. E-05: require all From-Backlog plans executed before `release_gate_warnings` advises `--status done`.
5. E-06: add the third grandfathered cohort string.
6. E-07, E-08, E-09: correct the repo-local, shipped and installed prose and add a CHANGELOG line.
7. E-10: full suite against baseline, `aw check`, corpus re-measure.

## Deferred / out of scope (with reason)

- Dropping the same-gate ENTRY condition (letting an item with only ungated executed carriers close on HANDOFF). That would let a gated item close without any carrier having inherited its gate, which is exactly the dropped-handoff shape the gate exists to prevent; OQ-01 records the decision.
  - Carrier-Declined: a deliberate design choice, not owed work.
- Widening `release_gate_warnings` to spec carriers. Its own comment records plans-only as deliberate and "a separate behavior change"; E-05 preserves it.
  - Carrier-Declined: a recorded settled decision, not unfinished work.
- `DECISIONS.md`'s "all same-gate From-Backlog carriers executed" wording inside a dated decision entry. Decision entries record what was decided when; rewriting one would falsify history.
  - Carrier-Declined: historical record, correct as of its date.
- Spec `llbr2b` Section 3.5 (`to-review`) describes HANDOFF as "a `From-Backlog` plan or spec carrying the SAME `Blocks-Release`", already stale since `2o5wka` and not approved. Not amended here (see Spec sync).
  - Carrier-Declined: the spec is under review and its author owns re-stating it; this plan reports the drift instead of editing a draft contract it does not own.
- The SATISFIED-arm executed-plan rule: owned by pending `ncmugb`.
  - Carrier: ncmugb

## Scope check

- Over-scope: `agent_workflows/engine.py`, `agent_workflows/cli.py` and the hook docstring are not named by the backlog item. Declared deliberately: they state the HANDOFF rule as "EVERY same-gate", which E-04 makes imprecise, and `jf3j4q` just established that these three sites must state the predicate's actual cardinality. Leaving them would recreate the drift that plan closed. `CHANGELOG.md` is added because the change tightens a user-visible command.
- Under-scope: none. The item asks only for the carrier filter to stop dropping ungated siblings; E-04 does that, and E-05/E-06 keep the two advisory consumers truthful about it.

## Required tests / validation

- `tests/test_backlog_handoff_close.py`: the E-02 cases (1) to (5), driven through `cli.main(["backlog", "set", ...])`, `check_engine.evaluate_blocking_close` and `runner_shared.evaluate_backlog_close` on `git init` scratch repos, asserting exit codes, item directory, stderr and verdict fields.
- `tests/test_check_engine_release_gate.py`: the E-03 warning and grandfathered-cohort cases, asserting rule ids and detail text produced by `release_gate_warnings` and `check_release_gates`.
- `tests/test_backlog_close_gate_prose.py` unchanged and passing (installed YAML and rendered help, both real outputs).
- Full suite BARE, `python3 -m pytest`, with the FAILED set compared to E-01's baseline.
- `aw check release-gates` and `aw check` with 0 errors; the corpus re-measure showing 0 flips.
- No test reads production source or asserts on code structure.

## Spec / documentation sync

- No `.spec.md` is edited, so none is in `- Scope-Paths:`. The only spec text describing this predicate is `llbr2b` Section 3.5 (`- Status: to-review`, not approved), which was already imprecise before this plan (it omits the every-carrier rule `2o5wka` shipped). Spec `25kzda`'s `BACKLOG-GATE-HANDOFF` row governs gate PRESERVATION at graduation, not close legitimacy, and is unaffected. The executor reports the `llbr2b` drift in the final report so its author can restate Section 3.5.
- Docs: `AGENTS.md` (repo-local paragraph), `.aw/records/backlog/README.md`, `CHANGELOG.md`, plus the shipped prose in E-08.

## Open questions

### OQ-01: Should a different-gate or ungated sibling block the close, and should the same-gate entry condition stay?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED from repository evidence. (a) EVERY carrier blocks, whatever its gate, ungated or differently gated: the runner reference (F-02) discards the gate entirely, so this is the only filter that converges; and a differently gated sibling is still unfinished work the item asked for. (b) The same-gate ENTRY condition STAYS: without it an item whose only carriers dropped the gate could close on HANDOFF, which is the dropped-handoff case `check.from-backlog-gate-mismatch` and the close gate exist to stop; F-06 measures that keeping it changes no live verdict. The runner itself is stricter still (it also requires the run to have earned the close), which is a runner-only concern and out of scope. (c) ADDED AT REVIEW: a RETIRED sibling (`superseded/` or `not-executed/`) counts as not terminal and blocks the HANDOFF close. This follows from reusing `_carrier_is_executed` (true only for an `executed` path segment or spec `implemented`), matches the runner (`plan_bucket(plan) != "executed"` is unexecuted) and matches today's behavior for a retired SAME-gate carrier (measured at review: same-gate executed plus same-gate superseded is refused today). Measured at review: 16 gated `done` items carry a superseded carrier and none flips verdict; no LIVE gated item carries one. The remedy for such an item is SATISFIED (`--evidence` on the executed plan) or DE-GATED, both unchanged; E-02 case (6) pins it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: PASTE the fixture script and both verdicts side by side (`evaluate_blocking_close` -> `legitimate=True path='HANDOFF'`, `evaluate_backlog_close` -> `close=False` with the pending carrier named), produced by the E-01 script calling those two functions. PASTE the pre-edit bare-suite summary line and the count of saved FAILED lines. Agreeing verdicts fail this item.
  - Observed evidence:
    ```python
    import tempfile
    from pathlib import Path
    from agent_workflows import check_engine, runner_shared
    from tests.test_backlog_handoff_close import _make_scratch_repo, _write_backlog_item, _write_plan

    with tempfile.TemporaryDirectory() as tmp:
    repo = _make_scratch_repo(Path(tmp))
    # a graduated item gated next
    item = _write_backlog_item(repo, "item01", status="graduated", blocks_release="next")
    # one EXECUTED carrier gated next
    p_exec = _write_plan(repo, "plan01", bucket="executed", status="executed", from_backlog="item01", blocks_release="next")
    # one PENDING carrier with - From-Backlog: and NO - Blocks-Release: line
    p_pend = _write_plan(repo, "plan02", bucket="pending", status="approved", from_backlog="item01", blocks_release=None)

    v1 = check_engine.evaluate_blocking_close(repo, item, "done")
    v2 = runner_shared.evaluate_backlog_close(repo, "item01", [])

    print(f"evaluate_blocking_close -> legitimate={v1.legitimate} path={v1.path!r} reason={v1.reason!r}")
    print(f"evaluate_backlog_close  -> close={v2.close} reason={v2.reason!r}")
    ```
    Output:
    ```
    evaluate_blocking_close -> legitimate=True path='HANDOFF' reason="gate 'next' handed off to a From-Backlog plan or spec"
    evaluate_backlog_close  -> close=False reason='IPD carrier(s) not executed: .aw/records/plans/pending/20260926-testset-01-plan02-test-plan.ipd.md'
    ```
    Pre-edit bare suite summary line:
    ```
    7931 passed, 4 skipped, 18 xfailed, 3 warnings in 957.98s (0:15:57)
    ```
    Count of saved FAILED lines:
    ```
    0 /tmp/pytest_baseline_failed.txt
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE `python3 -m pytest -o addopts="" tests/test_backlog_handoff_close.py -v` output run BEFORE E-04 showing cases (1), (3), (4-refused), (6-refused) failing and (2), (4-allowed), (5), (6-DE-GATED) passing; then the same command AFTER E-04 showing all passing. Paste the new test names.
  - Observed evidence:
    BEFORE E-04:
    ```
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_6_refused_executed_same_gate_superseded_ungated_plan FAILED [ 12%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_1_executed_same_gate_pending_ungated_refused FAILED [ 25%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_4_refused_executed_same_gate_approved_ungated_spec FAILED [ 37%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_4_allowed_executed_same_gate_implemented_ungated_spec PASSED [ 50%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_2_executed_same_gate_executed_ungated_allowed PASSED [ 62%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_5_only_executed_ungated_plan_refused PASSED [ 75%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_6_degated_executed_same_gate_superseded_ungated_plan_allowed PASSED [ 87%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_3_executed_same_gate_pending_different_gate_refused FAILED [100%]
    =========================== short test summary info ============================
    FAILED tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_6_refused_executed_same_gate_superseded_ungated_plan
    FAILED tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_1_executed_same_gate_pending_ungated_refused
    FAILED tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_4_refused_executed_same_gate_approved_ungated_spec
    FAILED tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_3_executed_same_gate_pending_different_gate_refused
    ================== 4 failed, 4 passed, 32 deselected in 3.55s ==================
    ```
    AFTER E-04:
    ```
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_2_executed_same_gate_executed_ungated_allowed PASSED [ 12%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_4_refused_executed_same_gate_approved_ungated_spec PASSED [ 25%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_4_allowed_executed_same_gate_implemented_ungated_spec PASSED [ 37%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_6_degated_executed_same_gate_superseded_ungated_plan_allowed PASSED [ 50%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_1_executed_same_gate_pending_ungated_refused PASSED [ 62%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_6_refused_executed_same_gate_superseded_ungated_plan PASSED [ 75%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_5_only_executed_ungated_plan_refused PASSED [ 87%]
    tests/test_backlog_handoff_close.py::BacklogHandoffCloseBehaviorTests::test_kntbbc_case_3_executed_same_gate_pending_different_gate_refused PASSED [100%]
    ======================= 8 passed, 32 deselected in 4.36s =======================
    ```
    New test names:
    - test_kntbbc_case_1_executed_same_gate_pending_ungated_refused
    - test_kntbbc_case_2_executed_same_gate_executed_ungated_allowed
    - test_kntbbc_case_3_executed_same_gate_pending_different_gate_refused
    - test_kntbbc_case_4_refused_executed_same_gate_approved_ungated_spec
    - test_kntbbc_case_4_allowed_executed_same_gate_implemented_ungated_spec
    - test_kntbbc_case_5_only_executed_ungated_plan_refused
    - test_kntbbc_case_6_refused_executed_same_gate_superseded_ungated_plan
    - test_kntbbc_case_6_degated_executed_same_gate_superseded_ungated_plan_allowed
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE `python3 -m pytest -o addopts="" tests/test_check_engine_release_gate.py -v -k "<new test names>"` BEFORE E-04 showing both new cases failing, and AFTER E-06 showing both passing.
  - Observed evidence:
    BEFORE E-04:
    ```
    FAILED tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_release_gate_warnings_executed_same_gate_pending_ungated_advises_graduated
    FAILED tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_rule_blocking_close_grandfathered_cohort_sibling_not_executed
    ======================= 2 failed, 50 deselected in 0.67s =======================
    ```
    AFTER E-06:
    ```
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_rule_blocking_close_grandfathered_cohort_sibling_not_executed PASSED [ 50%]
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_release_gate_warnings_executed_same_gate_pending_ungated_advises_graduated PASSED [100%]
    ======================= 2 passed, 50 deselected in 0.59s =======================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the `git diff` hunk of `evaluate_blocking_close` showing the all-carrier legitimacy test, the unchanged same-gate entry condition, the refusal listing non-terminal carriers, and unchanged arm order. RE-RUN V-01's fixture script and paste both verdicts now AGREEING (`legitimate=False`, `close=False`). PASTE `python3 -m pytest -o addopts="" tests/test_carrier_scan_single_item_contract.py` passing.
  - Observed evidence:
    Diff hunk:
    ```diff
    @@ -5678,11 +5678,12 @@ def evaluate_blocking_close(
             return CloseVerdict(
                 True, "ok", "no release gate to preserve", (), "DE-GATED"
             )
    -        # HANDOFF: EVERY From-Backlog PLAN or SPEC with the SAME Blocks-Release must be EXECUTED/IMPLEMENTED.
    +        # HANDOFF: at least one same-gate carrier exists AND every From-Backlog carrier, gated or not,
    +        # is executed/implemented, matching runner_shared.evaluate_backlog_close (backlog kntbbc).
         # Maintainer ruling 2026-09-26 (OQ-01, backlog rwhbci, closescope 2a6phj), tightened by
    -        # anycarrier Order 1 (2o5wka, backlog lsbd32) to require all same-gate carriers executed,
    -        # converging onto runner_shared.evaluate_backlog_close.
    +        # anycarrier Order 1 (2o5wka, backlog lsbd32) and kntbbc Order 1 (jykyqb).
         same_gate_carriers: List[Path] = []
    +        all_carriers: List[Path] = []
         if item_id6:
             release_cache: Dict[str, Optional[Path]] = {}
             carrier_items = (
    @@ -5690,6 +5691,7 @@ def evaluate_blocking_close(
                 if carrier_index is not None
                 else find_from_backlog_artifacts(repo_root, item_id6)
             )
    +            all_carriers = [p for p, _br in carrier_items]
             for _p, carrier_br in carrier_items:
                 if _same_release(
                     repo_root, carrier_br, blocks_release, cache=release_cache
    @@ -5703,7 +5705,7 @@ def evaluate_blocking_close(
                 return _carrier_is_executed(c)

             if same_gate_carriers and all(
    -                _carrier_eval(_c) for _c in same_gate_carriers
    +                _carrier_eval(_c) for _c in all_carriers
             ):
                 return CloseVerdict(
                     True,
    @@ -5726,7 +5728,8 @@ def evaluate_blocking_close(
             )
         # If same-gate carriers exist but none is executed, give the graduated-first refusal (E-04).
         if same_gate_carriers:
    -            carrier_list = ", ".join(p.name for p in same_gate_carriers)
    +            non_terminal = [c for c in all_carriers if not _carrier_eval(c)]
    +            carrier_list = ", ".join(p.name for p in (non_terminal or same_gate_carriers))
             return CloseVerdict(
                 False,
                 "error",
    ```
    Fixture script re-run (agreeing):
    ```
    evaluate_blocking_close -> legitimate=False path=None reason="gate 'next' is handed off to From-Backlog carrier(s) (20260926-testset-01-plan02-test-plan.ipd.md) but the work has not shipped (carrier is not executed/implemented)"
    evaluate_backlog_close  -> close=False reason='IPD carrier(s) not executed: .aw/records/plans/pending/20260926-testset-01-plan02-test-plan.ipd.md'
    ```
    Single item contract test:
    ```
    ============================== 9 passed in 16.67s ==============================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the `release_gate_warnings` diff hunk and the pytest output for every `release_gate_warnings` test in `tests/test_check_engine_release_gate.py` (`-k release_gate_warnings`), all passing.
  - Observed evidence:
    Diff hunk:
    ```diff
    @@ -6773,8 +6773,9 @@ def release_gate_warnings(repo_root: Path) -> List[_core.Drift]:
     # Note: this index is PLANS-ONLY (_iter_plan_ipds plus From-Backlog), so a spec
     # carrier produces no warning here. This asymmetry is deliberate (E-05): the predicate
     # is spec-aware, but widening this advisory is a separate behavior change.
    -    # We record whether ALL same-gate plans are executed (closescope 2a6phj E-05, anycarrier 2o5wka E-05).
    +    # We record whether ALL same-gate plans are executed and whether ALL plans are executed (closescope 2a6phj E-05, anycarrier 2o5wka E-05, kntbbc jykyqb E-05).
     plan_gates_by_backlog: Dict[str, Dict[str, bool]] = {}
    +    all_plans_executed_by_backlog: Dict[str, bool] = {}
     for _p, text in _iter_plan_ipds(repo_root):
         backlog_id = _from_backlog_value(text)
         if not backlog_id:
    @@ -6782,6 +6782,9 @@ def release_gate_warnings(repo_root: Path) -> List[_core.Drift]:
         is_exec = _carrier_is_executed(_p)
         gates_map = plan_gates_by_backlog.setdefault(backlog_id, {})
         gates_map[gate] = gates_map.get(gate, True) and is_exec
    +        all_plans_executed_by_backlog[backlog_id] = (
    +            all_plans_executed_by_backlog.get(backlog_id, True) and is_exec
    +        )

     warnings: List[_core.Drift] = []
     for f in _backlog._iter_items(repo_root):
    @@ -6795,8 +6795,9 @@ def release_gate_warnings(repo_root: Path) -> List[_core.Drift]:
         if not item_gate or not _id6:
             continue
         gates_map = plan_gates_by_backlog.get(_id6)
    +        all_plans_exec = all_plans_executed_by_backlog.get(_id6, False)
         if gates_map is not None and item_gate in gates_map:
    -            if gates_map[item_gate]:
    +            if gates_map[item_gate] and all_plans_exec:
                 # Executed carrier: remedy advises closing done with the corrected --status spelling (F-9)
                 warnings.append(
    ```
    Pytest output:
    ```
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_release_gate_warnings_orphaned_live_blocker_remedy PASSED [ 33%]
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_release_gate_warnings_multi_carrier_all_executed_remedy PASSED [ 66%]
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_release_gate_warnings_executed_same_gate_pending_ungated_advises_graduated PASSED [100%]
    ======================= 3 passed, 49 deselected in 0.71s =======================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE the cohort diff hunk showing both existing strings unchanged and the new one added, and the pytest output for the existing case 8 test and the new E-03(b) test, both passing.
  - Observed evidence:
    Diff hunk:
    ```diff
    @@ -6510,9 +6510,14 @@ def check_release_gate_consistency(
                             boundary_desc = "no cutover configured"

                         if same_gate_carriers:
    -                            cohort_desc = (
    -                                "same-gate carrier(s) present but not all executed"
    -                            )
    +                            if all(_carrier_is_executed(p) for p in same_gate_carriers):
    +                                cohort_desc = (
    +                                    "same-gate carrier(s) executed but a sibling carrier is not"
    +                                )
    +                            else:
    +                                cohort_desc = (
    +                                    "same-gate carrier(s) present but not all executed"
    +                                )
                         else:
                             cohort_desc = "no same-gate carrier"
    ```
    Pytest output:
    ```
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_rule_blocking_close_grandfathered_cohort_details PASSED [ 50%]
    tests/test_check_engine_release_gate.py::TestCheckEngineReleaseGate::test_rule_blocking_close_grandfathered_cohort_sibling_not_executed PASSED [100%]
    ======================= 2 passed, 50 deselected in 0.70s =======================
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: PASTE `git diff AGENTS.md .aw/records/backlog/README.md`, plus `grep -n "<!-- /aw:block -->" AGENTS.md` and the edited paragraph's line number showing the edit is below the marker, plus `grep -rni "every same-gate carrier" AGENTS.md .aw/records/backlog/README.md` returning nothing.
  - Observed evidence:
    ```diff
    diff --git a/.aw/records/backlog/README.md b/.aw/records/backlog/README.md
    index f9152e13e..25b97082a 100644
    --- a/.aw/records/backlog/README.md
    +++ b/.aw/records/backlog/README.md
    @@ -154,7 +154,7 @@ For the full ruling, rationale, and limits, see DECISIONS.md entry D161.

     When a backlog item becomes committed execution work, author an IPD under `.aw/records/plans/pending/`,
     then transition the item to `graduated` via `aw backlog set <item> --status graduated` with a history
    -line citing the plan id. Once the plan executes (or, for a multi-carrier item, once every same-gate carrier executes), the item can be closed `done` via
    +line citing the plan id. Once the plan executes (or, for a multi-carrier item, once every From-Backlog carrier, gated or not, executes), the item can be closed `done` via
     `aw backlog set <item> --status done`. The backlog captured the intent; the plan owns execution.

     Record what the item became with `--graduated-to <setid>`, the FORWARD half of the graduation link:
    diff --git a/AGENTS.md b/AGENTS.md
    index a3a66663c..6ed4ec303 100644
    --- a/AGENTS.md
    +++ b/AGENTS.md
    @@ -227,8 +227,9 @@ rule nudge when a pending plan cites a spec without carrying the link.
     Close-legitimacy rule for a release-blocking backlog item: both spellings of `aw backlog set`
     (positional `aw backlog set done <item>` and flag `aw backlog set <item> --status done`) on an item carrying
     `- Blocks-Release: <R>` FAIL CLOSED unless the gate is provably preserved or released via one of three
    -fixes: (1) HANDOFF, EVERY same-gate carrier (From-Backlog plan or spec) carrying `- From-Backlog: <this id6>` and
    -the same `- Blocks-Release: <R>` must be executed or implemented (set with `aw ipd set ... --from-backlog <id6>`);
    +fixes: (1) HANDOFF, at least one carrier carrying `- From-Backlog: <this id6>` and the same
    +`- Blocks-Release: <R>` must exist, and EVERY From-Backlog carrier of the item, whatever its gate,
    +must be executed or implemented (set with `aw ipd set ... --from-backlog <id6>`);
     a multi-carrier item stays `graduated` until the last carrier executes; (2) SATISFIED, a resolvable in-tree artifact citation
     `aw backlog set done <item> --evidence <path>`; (3) DE-GATED, clear the gate first (or in the same call)
     with `aw backlog set done <item> --blocks-release -`. Parking a blocker or demoting its priority is
    ```
    Lines:
    `grep -n "<!-- /aw:block -->" AGENTS.md`: 125
    `grep -n "Close-legitimacy rule for a release-blocking backlog item" AGENTS.md`: 227 (below marker)
    `grep -rni "every same-gate carrier" AGENTS.md .aw/records/backlog/README.md`: empty output.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: PASTE `git diff agent_workflows/engine.py agent_workflows/cli.py agent_workflows/hooks/backlog_blocking_close_gate.py` (HANDOFF clause only), `grep -rn "EVERY same-gate" agent_workflows` returning nothing, and `python3 -m pytest -o addopts="" tests/test_backlog_close_gate_prose.py -v` passing.
  - Observed evidence:
    ```diff
    diff --git a/agent_workflows/cli.py b/agent_workflows/cli.py
    index 27f62b711..5c1476822 100644
    --- a/agent_workflows/cli.py
    +++ b/agent_workflows/cli.py
    @@ -682,7 +682,7 @@ _DESCRIPTIONS = {
         "bypass-catcher for a hand-edit that skips 'aw backlog set done'. Inspects the staged diff and "
         "delegates to the shared 'check_engine.evaluate_blocking_close' predicate (via the commit-scoped "
         "'check.blocking-item-closed-without-gate' rule), reconstructing legitimacy from PERSISTED state "
    -        "(HANDOFF: EVERY same-gate From-Backlog carrier executed or implemented; DE-GATED: Blocks-Release cleared), so the hook, setter, "
    +        "(HANDOFF: a same-gate From-Backlog carrier exists and EVERY From-Backlog carrier, gated or not, is executed or implemented; DE-GATED: Blocks-Release cleared), so the hook, setter, "
         "and 'aw check' never diverge. Gates the 'done' case only (park/demote warns are surfaced by "
         "'aw check'/'aw attention'). LOCAL best-effort, OPT-IN only (--no-verify bypasses it; the "
         "portable authority is the 'aw check' rule + CI); commit-scoped (historical done items "
    diff --git a/agent_workflows/engine.py b/agent_workflows/engine.py
    index 86a3915c8..60a0f850c 100755
    --- a/agent_workflows/engine.py
    +++ b/agent_workflows/engine.py
    @@ -5851,7 +5851,7 @@ _BACKLOG_CLOSE_GATE_PRECOMMIT_TEMPLATE = """\
     # hook below into your existing .pre-commit-config.yaml instead of this file.
     repos:
       # OPT-IN local guard (bklggrad f1dhht): refuse committing a release-blocking backlog item closed to
    -  # `- Status: done` without a preserved-or-satisfied gate (HANDOFF: EVERY same-gate From-Backlog carrier (plan or spec)
    +  # `- Status: done` without a preserved-or-satisfied gate (HANDOFF: a same-gate From-Backlog carrier exists and EVERY From-Backlog carrier (plan or spec), gated or not,
       # must be executed or implemented, DE-GATED, or a persisted evidence citation). Delegates to the shared close-legitimacy
       # predicate. LOCAL best-effort only (--no-verify bypasses it); the portable authority is the `aw check` rule + CI.
       - repo: local
    @@ -5867,7 +5867,7 @@ repos:
     # The hook block to hand a user (or append) when a .pre-commit-config.yaml already exists.
     _BACKLOG_CLOSE_GATE_PRECOMMIT_BLOCK = """\
       # OPT-IN local guard (bklggrad f1dhht): refuse committing a release-blocking backlog item closed to
    -  # `- Status: done` without a preserved-or-satisfied gate (HANDOFF: EVERY same-gate From-Backlog carrier (plan or spec)
    +  # `- Status: done` without a preserved-or-satisfied gate (HANDOFF: a same-gate From-Backlog carrier exists and EVERY From-Backlog carrier (plan or spec), gated or not,
       # must be executed or implemented, DE-GATED, or a persisted evidence citation). Delegates to the shared close-legitimacy
       # predicate. LOCAL best-effort only (--no-verify bypasses it); the portable authority is the `aw check` rule + CI.
       - repo: local
    diff --git a/agent_workflows/hooks/backlog_blocking_close_gate.py b/agent_workflows/hooks/backlog_blocking_close_gate.py
    index 72897b4e8..9e66f0839 100644
    --- a/agent_workflows/hooks/backlog_blocking_close_gate.py
    +++ b/agent_workflows/hooks/backlog_blocking_close_gate.py
    @@ -16,8 +16,8 @@ diverge. Per OQ-01 the hook gates the fail-closed `done` case ONLY (blocking->pa
     WARNs are surfaced by `aw check`/`aw attention`, not at commit time).

     Commit-time legitimacy is reconstructed from PERSISTED state only (the predicate is called WITHOUT an
    -`evidence=` arg): HANDOFF (EVERY same-gate `From-Backlog` carrier present in the staged tree with the
    -same `Blocks-Release` must be executed or implemented) and DE-GATED (`Blocks-Release` absent from the
    +`evidence=` arg): HANDOFF (a same-gate `From-Backlog` carrier present in the staged tree with the
    +same `Blocks-Release` must exist and every `From-Backlog` carrier, gated or not, must be executed or implemented) and DE-GATED (`Blocks-Release` absent from the
     staged item) are decidable from the staged tree. A transient `--evidence` CLI arg is NOT visible to the
     hook, but the setter now durably persists the citation as a `- Close-Evidence:` bullet (gateatrest
     f7igdu, via `backlog.set_close_evidence_line`), so the SATISFIED path IS honored from persisted state.
    ```
    `grep -rn --exclude="*.pyc" "EVERY same-gate" agent_workflows` returns empty.
    `python3 -m pytest -o addopts="" tests/test_backlog_close_gate_prose.py -v`:
    `============================== 3 passed in 0.97s ===============================`
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: PASTE `git diff CHANGELOG.md` showing the single added line and confirm it contains no em or en dash.
  - Observed evidence:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 55be43f04..b5657f013 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -56,6 +56,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
     - Added: `check.gate-ref-dangling` (error severity) to report well-formed artifact or todo gate references that resolve to neither an in-repo path nor an inventoried artifact id6, and `check.gate-ref-discharged` (warning severity) to detect gates whose targets have completed or parked, preventing gates from silently outliving their blockers.
     - Added: `check.lifecycle-transition-unvalidated` companion rule (info severity) in `aw check plans` to report when the lifecycle gate examined a plan carrying two or more distinct forward statuses but validated zero transitions because date variation was removed, making gate coverage loss observable; this visibility does not restore lost transition enforcement, which requires spec 2vev8j Section 4.3 explicit per-artifact seq.
     - Fixed: the runner's backlog close predicate now requires a mixed item's spec carriers to be implemented before closing the item.
    +- Fixed: aw backlog set <item> --status done on a release-gated item now also waits for any ungated or differently gated From-Backlog sibling plan or spec to execute, matching the runner's own close rule.
     - Fixed: `aw specs set`, `aw backlog set`, and `aw set` now refuse a Gate-Kind outside the documented vocabulary (artifact, date, decision, external, issue, todo) or a Gate-Ref that does not match its kind, whichever spelling is used, instead of writing an invalid gate record that the checker later reports.
     - Fixed: `aw backlog new --status blocked` now refuses a Gate-Kind outside the documented vocabulary or a malformed Gate-Ref instead of writing a record the checker later reports.
     - Fixed: positional evidence-satisfied backlog closes now persist their citation portably, so aw check release-gates no longer reports a legitimate close as a dropped release gate.
    ```
    No em or en dash confirmed.
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: PASTE the post-edit bare-suite summary line, the `comm -13 <baseline> <post>` output (new failures) which must be empty, `aw check release-gates` output with 0 errors, the before/after per-rule `aw check --agent` counts showing no release-gate-family rule rose (the whole `aw check` exiting 1 on unrelated rules is expected and is not a failure of this item), and the corpus re-measure script and its output listing flipped items (expected none).
  - Observed evidence:
    Post-edit bare-suite summary line:
    ```
    7941 passed, 4 skipped, 18 xfailed, 3 warnings in 998.10s (0:16:38)
    ```
    `comm -13 /tmp/pytest_baseline_failed.txt /tmp/pytest_post_failed.txt`:
    ```
    (empty - 0 new failures)
    ```
    `aw check release-gates`:
    ```
    AW check  release-gates                                                  3125 ms
    ✓ CONFORMS  225 release-gates checked

    Evidence
      backlog  112   specs  21   plans  91   releases  1
      errors  0   warnings  0   info  0

    Next  aw releases list
    Agent output: --agent
    ```
    Before/after per-rule `aw check --agent` counts:
    ```
    Rule comparison: baseline=105, post=104
      check.gate-ref-discharged: 3 -> 3
      check.graduated-to-dangling: 3 -> 3
      check.ipd-carrier-finished-unverified: 10 -> 10
      check.ipd-carrier-ungated: 2 -> 2
      check.lifecycle-transition-unvalidated: 79 -> 79
      check.name-nonconformant: 1 -> 1
      check.plan-spec-link-missing: 4 -> 4
      check.scope-drift: 1 -> 0 (-1)
      check.spec-criteria-uncovered: 1 -> 1
      check.system-layout-missing: 1 -> 1
    ```
    Corpus re-measure script output:
    ```
    Total gated items checked: 495
    Flipped items count: 0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the declared `- Scope-Paths:` through `aw commit jykyqb -- <paths>`, never `git add -A`, never push, no tag or release. Verify the staged set with `git diff --cached --name-only` before committing; this checkout is shared. Paste actual runner output for every test claim.

SEQUENCE: E-02 and E-03 land BEFORE E-04, so the before-failing evidence V-02 and V-03 demand exists. Writing the fix first makes that evidence unobtainable.

STOP CONDITIONS (report, do not proceed): the divergence no longer reproduces (E-01); any new failing test beyond E-01's baseline (E-10); a historical item newly reported as an error by `aw check release-gates` (E-10); or `llbr2b` has become `approved` with a positive same-gate-only claim, which would turn this into a spec amendment requiring a declared `.spec.md` in `- Scope-Paths:`.

POST-GATE LIFECYCLE. `- Readiness:` was written by `/plan-review`. Explicit human approval via `aw ipd set approved` is required before execution. Finalize with the tooled path (`aw ipd finalize jykyqb ... --apply` or the runner's self-finalize), gated on `aw ipd lint --phase pre-transition` conforming and every `V-*` carrying pasted evidence. Backlog `kntbbc` has no `- Blocks-Release:`, so it closes `done` after this plan executes without a gate handoff.
