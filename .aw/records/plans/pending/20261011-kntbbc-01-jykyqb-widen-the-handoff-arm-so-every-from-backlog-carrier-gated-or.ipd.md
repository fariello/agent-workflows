# IPD: Widen the HANDOFF arm so every From-Backlog carrier, gated or not, must be terminal

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `kntbbc` (residue of `2o5wka` OQ-02 and `jf3j4q`'s deferred row naming `kntbbc` as carrier): `check_engine.evaluate_blocking_close`'s HANDOFF arm builds `same_gate_carriers` by keeping only carriers whose gate `_same_release` matches the item's, then requires `all(_carrier_eval(_c) for _c in same_gate_carriers)`. A sibling carrier with NO `- Blocks-Release:` line (or a different one) is dropped by that filter, so `aw backlog set <item> --status done` closes a gated item while that sibling is still pending. `runner_shared.evaluate_backlog_close` filters carriers by KIND, not by gate, and refuses the same close. The two "single-sourced" close predicates therefore still disagree on which carriers count.
- Scope: IN: (a) in `check_engine.evaluate_blocking_close`'s HANDOFF arm, keep the existing ENTRY condition (at least one same-gate carrier must exist, so the gate is still provably handed to a carrier that inherited it) but require EVERY `From-Backlog` carrier of the item, whatever its gate, to be executed/implemented before HANDOFF returns legitimate; (b) make the not-shipped refusal name the carriers that actually block (including an ungated or differently gated sibling); (c) align `check_engine.release_gate_warnings`' `check.orphaned-live-blocker` `--status done` advice so it is emitted only when every From-Backlog PLAN of the item is executed (preserving its plans-only design); (d) add a third grandfathered cohort description in `check_engine.check_release_gate_consistency` for "same-gate carriers executed, a sibling carrier is not" so the advisory detail is not false; (e) behavioral tests for every case; (f) correct the five prose sites that state the HANDOFF rule as "EVERY same-gate carrier" (repo-local `AGENTS.md` paragraph, `.aw/records/backlog/README.md`, the two `engine.py` pre-commit template comments, the `cli.py` help description, the hook module docstring) plus a `CHANGELOG.md` line. OUT: SATISFIED and DE-GATED arms, the `graduated`/`parked`/priority-demote branches, the lane-carrier override mechanism, the runner (`runner_shared.evaluate_backlog_close` is the REFERENCE converged onto, not edited), `check.from-backlog-gate-mismatch` (unchanged), widening `release_gate_warnings` to spec carriers, and the SATISFIED-arm work owned by pending `ncmugb`.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/hooks/backlog_blocking_close_gate.py, tests/test_backlog_handoff_close.py, tests/test_check_engine_release_gate.py, AGENTS.md, .aw/records/backlog/README.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: kntbbc
- Set: kntbbc
- Order: 1
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: jykyqb
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
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

- [ ] E-01 REPRODUCE THE DIVERGENCE AND CAPTURE A SUITE BASELINE at the executing HEAD, before any edit. (a) On a `git init` scratch repo (a resolvable `next` release record, a `graduated` item gated `next`, one EXECUTED carrier gated `next`, one PENDING carrier with `- From-Backlog:` and NO `- Blocks-Release:` line), call `check_engine.evaluate_blocking_close(repo, item, "done")` and `runner_shared.evaluate_backlog_close(repo, item_id6, [])` and record both verdicts. (b) Run the full suite BARE (`python3 -m pytest`, no added flags) and save the sorted `FAILED` lines to a scratch file as the pre-edit failure set.
  - Depends on: none
  - Expected outcome: `evaluate_blocking_close` returns `legitimate=True, path='HANDOFF'`; `evaluate_backlog_close` returns `close=False` naming the pending carrier. A pre-edit failure set exists for E-10 to compare against.
  - STOP CONDITION: if the two verdicts already AGREE (both refuse), another change has landed the fix; report and stop rather than editing.
  - The baseline failure set is NOT expected to be empty. Measured at authoring (HEAD `f8452a0be`, this lane): `38 failed, 7181 passed, 2 skipped`, all 38 in modules unrelated to release gates (for example `tests/test_no_project_exit_is_cannot_run.py`, `tests/test_read_class_callers_refuse.py`, `tests/test_finalize_sendback.py`). The bar is "no NEW failure", not "green".
  - Execution state: pending

### Task group 2: tests first (they must fail before the fix)

- [ ] E-02 ADD HANDOFF-ARM CASES to `tests/test_backlog_handoff_close.py` (class `BacklogHandoffCloseBehaviorTests`, reusing `_write_backlog_item`, `_write_plan`, `_write_spec`, whose `blocks_release=None` already omits the line). Each case drives `cli.main(["backlog", "set", "item01", "--status", "done", "--dir", ..., "--message", "close"])` and/or `check_engine.evaluate_blocking_close`, asserting exit code, the item's resulting directory, stderr and `verdict.path`/`verdict.legitimate`: (1) executed same-gate plan + PENDING UNGATED plan -> refused rc 1, item still in `graduated/`, stderr names the ungated plan's id; and in the same case assert `runner_shared.evaluate_backlog_close(self.repo, "item01", [])` is `close=False`, so the convergence is pinned by outcome; (2) executed same-gate plan + EXECUTED UNGATED plan -> allowed rc 0, `path == "HANDOFF"`, item in `done/`; (3) executed same-gate plan + PENDING plan gated to a DIFFERENT release value -> refused; (4) executed same-gate plan + UNGATED spec in `approved/` with `- Status: approved` -> refused, and the same with `- Status: implemented` -> allowed; (5) ONLY an executed UNGATED plan, no same-gate carrier -> still refused (unchanged entry condition); (6) executed same-gate plan + UNGATED plan in `superseded/` (`_write_plan(..., bucket="superseded", status="superseded", blocks_release=None)`) -> refused, stderr names the superseded plan, and `aw backlog set done item01 --blocks-release - ...` (DE-GATED) on the same tree -> allowed rc 0. Case (6) pins the OQ-01(c) decision that a retired sibling counts as unfinished, exactly as a retired SAME-gate carrier already does today and as the runner does. Each docstring cites `kntbbc` and states that cases (1), (3), (4-refused) and (6-refused) deliberately tighten the `2o5wka` same-gate rule.
  - Depends on: E-01
  - Expected outcome: run before E-04, cases (1), (3), (4-refused) and (6-refused) FAIL and cases (2), (4-allowed), (5) and (6-DE-GATED) PASS.
  - Case (3) needs no release record for the other value: `_same_release` falls back to string equality when a value does not resolve, so `blocks_release="other"` is a different gate.
  - Execution state: pending

- [ ] E-03 ADD ADVISORY CASES to `tests/test_check_engine_release_gate.py`. (a) Beside `test_release_gate_warnings_multi_carrier_all_executed_remedy`: an `open` item gated `next` with an EXECUTED plan gated `next` and a PENDING plan with no `- Blocks-Release:` -> `check_engine.release_gate_warnings(repo)` yields one `check.orphaned-live-blocker` whose detail contains `--status graduated` and not `--status done`. (b) Beside `test_rule_blocking_close_grandfathered_cohort_details` (the "heh05a E-05 case 8" test): a `done` item gated `next` with an EXECUTED same-gate plan and a PENDING ungated plan, under the same cutover config, -> `check_engine.check_release_gates(repo, grandfathered=True)` reports one `check.blocking-close-grandfathered` whose detail contains `cohort: same-gate carrier(s) executed but a sibling carrier is not`.
  - Depends on: E-02
  - Expected outcome: before E-04/E-05/E-06, (a) FAILS (today the advice is `--status done`) and (b) FAILS (today no finding is emitted because the close is judged legitimate).
  - Do NOT change the existing case 8 assertions: the two existing cohort strings stay byte-identical (E-06).
  - Execution state: pending

### Task group 3: the predicate and its two advisory consumers

- [ ] E-04 WIDEN THE HANDOFF ARM in `check_engine.evaluate_blocking_close`. In the block under the comment `# HANDOFF: EVERY From-Backlog PLAN or SPEC with the SAME Blocks-Release must be EXECUTED/IMPLEMENTED.`, keep building `same_gate_carriers` exactly as today, additionally keep `all_carriers = [p for p, _br in carrier_items]`, and change the legitimacy test to `same_gate_carriers and all(_carrier_eval(c) for c in all_carriers)`. In the not-shipped refusal (the `if same_gate_carriers:` block), list the carriers that are NOT terminal (computed with the same `_carrier_eval`), not only the same-gate ones, and keep its three fixes unchanged. Update the docstring's `HANDOFF` line and the arm's comment to state: at least one same-gate carrier exists AND every From-Backlog carrier, gated or not, is executed/implemented, matching `runner_shared.evaluate_backlog_close` (backlog `kntbbc`).
  - Depends on: E-03
  - Expected outcome: E-02's cases all pass. `carrier_items` is reused, so no new `find_from_backlog_artifacts` call is introduced (the single-item contract enforced by `tests/test_carrier_scan_single_item_contract.py` is untouched). The lane override still applies, because `_carrier_eval` is what iterates.
  - Do NOT change arm order (DE-GATED, HANDOFF, SATISFIED, refusals), `_same_release`, `_carrier_is_executed`, `_lane_carrier_is_executed`, or the verdict's `reason` string on the success path (`jf3j4q` recorded it as machine-consumed and deliberately left alone).
  - Execution state: pending

- [ ] E-05 ALIGN `check_engine.release_gate_warnings`. Alongside `plan_gates_by_backlog`, accumulate per backlog id6 whether EVERY From-Backlog plan (any gate) is executed, and emit the `--status done` advice only when `gates_map[item_gate]` AND that all-plans flag are both true; otherwise emit the existing `--status graduated` advice. Keep the function plans-only and keep its single `_iter_plan_ipds` walk.
  - Depends on: E-04
  - Expected outcome: E-03(a) passes; `test_release_gate_warnings_multi_carrier_all_executed_remedy` and every other existing warning test still pass.
  - WHY: without this, `aw check` would advise `aw backlog set <id6> --status done`, exactly the command E-04 now refuses, which is the "advises the route that refuses" defect `2o5wka` E-05 already fixed once in this function.
  - Execution state: pending

- [ ] E-06 ADD THE THIRD GRANDFATHERED COHORT in `check_engine.check_release_gate_consistency`'s grandfathered arm. Where `cohort_desc` is chosen, distinguish: no same-gate carrier -> existing `"no same-gate carrier"`; same-gate carriers present and not all executed -> existing `"same-gate carrier(s) present but not all executed"`; same-gate carriers all executed (so the refusal came from a sibling) -> new `"same-gate carrier(s) executed but a sibling carrier is not"`. Use `_carrier_is_executed`, reusing the `carrier_items` already read from `shared_carrier_idx`.
  - Depends on: E-05
  - Expected outcome: E-03(b) passes and the existing case 8 test still passes with its two strings unchanged.
  - Execution state: pending

### Task group 4: prose

- [ ] E-07 UPDATE THE REPO-LOCAL RULE STATEMENTS. (a) `AGENTS.md`, the paragraph beginning "Close-legitimacy rule for a release-blocking backlog item" (BELOW `<!-- /aw:block -->`; anchor on that quoted string, not a line number, and make no edit inside any `<!-- aw:` block): fix (1) currently reads "HANDOFF, EVERY same-gate carrier (From-Backlog plan or spec) carrying `- From-Backlog: <this id6>` and the same `- Blocks-Release: <R>` must be executed or implemented"; restate it as: at least one carrier carrying `- From-Backlog: <this id6>` and the same `- Blocks-Release: <R>` must exist, and EVERY From-Backlog carrier of the item, whatever its gate, must be executed or implemented. Keep the "multi-carrier item stays `graduated`" clause. (b) `.aw/records/backlog/README.md`, the sentence containing "once every same-gate carrier executes": change it to "once every From-Backlog carrier, gated or not, executes". User-facing prose: no em or en dashes.
  - Depends on: E-06
  - Expected outcome: neither file contains the phrase "every same-gate carrier" / "EVERY same-gate carrier" any more; `git diff AGENTS.md` shows no line inside an `aw:` managed block changed.
  - CO-EDITOR: pending `ncmugb` (backlog `7lfe87`) declares `AGENTS.md` and `.aw/records/backlog/README.md` and edits the SATISFIED fix (2) wording. This item owns fix (1) only. If fix (2) has already been rewritten, that is `ncmugb` landing first: leave it.
  - Execution state: pending

- [ ] E-08 UPDATE THE SHIPPED AND INSTALLED PROSE SITES that say "EVERY same-gate": (a) both occurrences in `agent_workflows/engine.py` (`_BACKLOG_CLOSE_GATE_PRECOMMIT_TEMPLATE` and `_BACKLOG_CLOSE_GATE_PRECOMMIT_BLOCK`), changing "HANDOFF: EVERY same-gate From-Backlog carrier (plan or spec)" to "HANDOFF: a same-gate From-Backlog carrier exists and EVERY From-Backlog carrier (plan or spec), gated or not,"; (b) the `cli.py` `_DESCRIPTIONS["backlog-blocking-close-gate"]` text "HANDOFF: EVERY same-gate From-Backlog carrier executed or implemented" to "HANDOFF: a same-gate From-Backlog carrier exists and EVERY From-Backlog carrier, gated or not, is executed or implemented"; (c) the `agent_workflows/hooks/backlog_blocking_close_gate.py` module docstring clause "HANDOFF (EVERY same-gate `From-Backlog` carrier present in the staged tree with the same `Blocks-Release` must be executed or implemented)" to say a same-gate carrier must exist and every `From-Backlog` carrier, gated or not, must be executed or implemented. Change ONLY the HANDOFF clause in each site (the `jf3j4q` boundary: leave the surrounding attribution, delegation and limits sentences untouched).
  - Depends on: E-07
  - Expected outcome: `grep -rn "EVERY same-gate" agent_workflows` returns nothing; `tests/test_backlog_close_gate_prose.py` passes unchanged (its regexes `HANDOFF[^)]*\bEVERY\b[^)]*From-Backlog` and `HANDOFF:[^)]*\bEVERY\b[^)]*From-Backlog` still match because no `)` precedes `EVERY` in the new text).
  - INSTALL SURFACE: (a) is written into every managed target that opts into the hook, so keep the edit to the clause. The new wording must keep a `)`-free run from `HANDOFF` through `EVERY` to `From-Backlog`; re-run the prose test rather than assuming.
  - Execution state: pending

- [ ] E-09 ADD ONE `CHANGELOG.md` LINE under the pending `2.0.0` entry stating that `aw backlog set <item> --status done` on a release-gated item now also waits for any ungated or differently gated `From-Backlog` sibling plan or spec to execute, matching the runner's own close rule. User-facing prose: no em or en dashes.
  - Depends on: E-08
  - Expected outcome: `git diff CHANGELOG.md` shows one added line in the pending section and nothing else.
  - Execution state: pending

### Task group 5: validate

- [ ] E-10 RUN THE FULL SUITE BARE AND RE-MEASURE. (a) `python3 -m pytest` with no added flags; save its sorted `FAILED` lines and diff against E-01's set. (b) `aw check release-gates`, and `aw check --agent` before (at E-01) and after, compared as per-rule finding counts. (c) Re-run the corpus measurement: one pass over `backlog._iter_items` with `check_engine._from_backlog_carrier_index(repo)` built ONCE; for every item with a `- Blocks-Release:`, compute `old = bool(same) and all(_carrier_is_executed(p) for p in same)` and `new = bool(same) and all(_carrier_is_executed(p) for p, _ in carriers)` (where `same` filters by `_same_release`), and list items where `old != new`.
  - Depends on: E-09
  - Expected outcome: (a) the post-edit failure set equals or is a subset of the pre-edit set; (b) `aw check release-gates` CONFORMS with 0 errors, and `aw check` shows no rule of the release-gate family (`check.blocking-*`, `check.from-backlog-*`, `check.orphaned-live-blocker`) whose count rose. `aw check` as a whole is NOT expected to exit 0: at review it already reported `findings`, exit 1, 123 findings from unrelated rules (e.g. 72 `check.lifecycle-transition-unvalidated`); (c) zero items flip (the gated-item count is live: 473 at authoring, 479 at review, both 0 flips). Measured at authoring with a prototype of E-04 (reverted): the bare suite produced the identical 38-failure set before and after, and 0 of 473 gated items changed verdict (`done` 321 legitimate / 105 not, unchanged). The only gated items with an ungated carrier at all are `1f9m2j`, `hyx1dg`, `t156g1`, each `done` with a single EXECUTED ungated carrier and no same-gate carrier, whose verdict E-04 does not change.
  - STOP CONDITION: any NEW failing test, or any flipped historical verdict that `aw check release-gates` now reports as an error, means report rather than adjust tests.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: PASTE the fixture script and both verdicts side by side (`evaluate_blocking_close` -> `legitimate=True path='HANDOFF'`, `evaluate_backlog_close` -> `close=False` with the pending carrier named), produced by the E-01 script calling those two functions. PASTE the pre-edit bare-suite summary line and the count of saved FAILED lines. Agreeing verdicts fail this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE `python3 -m pytest -o addopts="" tests/test_backlog_handoff_close.py -v` output run BEFORE E-04 showing cases (1), (3), (4-refused), (6-refused) failing and (2), (4-allowed), (5), (6-DE-GATED) passing; then the same command AFTER E-04 showing all passing. Paste the new test names.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE `python3 -m pytest -o addopts="" tests/test_check_engine_release_gate.py -v -k "<new test names>"` BEFORE E-04 showing both new cases failing, and AFTER E-06 showing both passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the `git diff` hunk of `evaluate_blocking_close` showing the all-carrier legitimacy test, the unchanged same-gate entry condition, the refusal listing non-terminal carriers, and unchanged arm order. RE-RUN V-01's fixture script and paste both verdicts now AGREEING (`legitimate=False`, `close=False`). PASTE `python3 -m pytest -o addopts="" tests/test_carrier_scan_single_item_contract.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the `release_gate_warnings` diff hunk and the pytest output for every `release_gate_warnings` test in `tests/test_check_engine_release_gate.py` (`-k release_gate_warnings`), all passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE the cohort diff hunk showing both existing strings unchanged and the new one added, and the pytest output for the existing case 8 test and the new E-03(b) test, both passing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: PASTE `git diff AGENTS.md .aw/records/backlog/README.md`, plus `grep -n "<!-- /aw:block -->" AGENTS.md` and the edited paragraph's line number showing the edit is below the marker, plus `grep -rni "every same-gate carrier" AGENTS.md .aw/records/backlog/README.md` returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: PASTE `git diff agent_workflows/engine.py agent_workflows/cli.py agent_workflows/hooks/backlog_blocking_close_gate.py` (HANDOFF clause only), `grep -rn "EVERY same-gate" agent_workflows` returning nothing, and `python3 -m pytest -o addopts="" tests/test_backlog_close_gate_prose.py -v` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: PASTE `git diff CHANGELOG.md` showing the single added line and confirm it contains no em or en dash.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: PASTE the post-edit bare-suite summary line, the `comm -13 <baseline> <post>` output (new failures) which must be empty, `aw check release-gates` output with 0 errors, the before/after per-rule `aw check --agent` counts showing no release-gate-family rule rose (the whole `aw check` exiting 1 on unrelated rules is expected and is not a failure of this item), and the corpus re-measure script and its output listing flipped items (expected none).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the declared `- Scope-Paths:` through `aw commit jykyqb -- <paths>`, never `git add -A`, never push, no tag or release. Verify the staged set with `git diff --cached --name-only` before committing; this checkout is shared. Paste actual runner output for every test claim.

SEQUENCE: E-02 and E-03 land BEFORE E-04, so the before-failing evidence V-02 and V-03 demand exists. Writing the fix first makes that evidence unobtainable.

STOP CONDITIONS (report, do not proceed): the divergence no longer reproduces (E-01); any new failing test beyond E-01's baseline (E-10); a historical item newly reported as an error by `aw check release-gates` (E-10); or `llbr2b` has become `approved` with a positive same-gate-only claim, which would turn this into a spec amendment requiring a declared `.spec.md` in `- Scope-Paths:`.

POST-GATE LIFECYCLE. `- Readiness:` was written by `/plan-review`. Explicit human approval via `aw ipd set approved` is required before execution. Finalize with the tooled path (`aw ipd finalize jykyqb ... --apply` or the runner's self-finalize), gated on `aw ipd lint --phase pre-transition` conforming and every `V-*` carrying pasted evidence. Backlog `kntbbc` has no `- Blocks-Release:`, so it closes `done` after this plan executes without a gate handoff.
