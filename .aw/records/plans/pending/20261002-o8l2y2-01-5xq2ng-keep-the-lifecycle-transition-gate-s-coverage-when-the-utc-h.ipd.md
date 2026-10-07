# IPD: Report when the lifecycle-transition gate validates NOTHING, so the UTC history-date fix cannot silently retire it

- Date: 2026-10-02
- Kind: child
- Concern: `check.lifecycle-transition-invalid` derives its event order from HISTORY DATES, and the UTC history-date fix the sibling plans implement REMOVES the date variation it depends on, so a correct fix silently converts a live `error`-severity gate into one that validates nothing and reports nothing. The mechanism is `ipd_lifecycle._plan_status_event_groups`, which classifies a history block's direction by comparing ADJACENT RECORD DATES and yields `ordered=False` when a block has one distinct date ("none (single date / 1 record) -> unknown"), and `check_engine.check_lifecycle_transitions`, which on an `ordered=False` group with more than one distinct status sets `prev = None` and `unvalidated = True`, SKIPPING every transition in it. Measured in this lane at HEAD `4ec14077c` over the 123 pending plans carrying a history block: the gate validates 30 transitions today; after collapsing only the <=1 day intra-block gaps that are the local/UTC skew signature it validates 2, and 20 plans lose all coverage. The failure is SILENT by construction: a gate that validates nothing emits no finding, so `aw check plans` goes GREENER as it goes blinder, and nothing in the three sibling plans' validation can observe it because each correctly asserts on dates written into artifacts rather than on what the gate still examines. Spec `2vev8j` 4.3 ruled this reader should stop depending on dates at all and use an explicit per-artifact `seq`; that is UNIMPLEMENTED (`record_history` holds no `seq`), so the date-derived classifier is still load-bearing and the 4.4 UTC ruling lands on top of it.
- Scope: IN: one `info`-severity companion rule that reports when a plan's history carries two or more distinct lifecycle statuses yet the gate validated ZERO transitions, so the gate's own blindness is visible in its output; and an outcome test that pins the reported-not-silent property across the date-collapse. OUT, each with a reason recorded under "Deferred": the production clock fix (`5ivkdh`); the cross-spelling guard (`ayhveg`); the scaffold site (`9wcei0`); the plan-family `created` site (`rfyrvp`); the duplicate convergence (`qjm4bg`); implementing spec 4.3's `seq`; changing the direction classifier; and relaxing or strengthening the existing `error` rule's verdicts.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_lifecycle_gate_coverage.py, CHANGELOG.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: o8l2y2
- From-Spec: 2vev8j
- Blocks-Release: next
- Set: o8l2y2
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 5xq2ng

## Workflow history
- 2026-10-07 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101, PR-102, PR-103, PR-104, PR-105, PR-106. Round 2 at HEAD `fe2ee961c` in an isolated review lane; plan byte-identical to the lane input, so no pre-review snapshot. Re-replayed the walk (gitignored probe): 137 pending plans, 104 validated, 62 multi-status zeros (all with an `ordered=False` group), 18 single-status zeros, the <=1-day collapse 104 -> 68 with 21 plans losing all; existing rule now returns 0 findings. Thesis holds. Fixed: siblings `5ivkdh`/`9wcei0` executed and `rfyrvp` superseded, so stale carrier/spec prose reconciled (PR-101); live counts and F-04/F-06/F-08 re-measured with all bars still re-derived (PR-102); wiring corrected to `check_content`'s plans branch, which `check_type` composes (PR-103); unsatisfiable 'only finding is the new rule exits 0' replaced by the canonical two-limb severity + `drift_exit_code` proof (PR-104); collateral to other `check_content` callers named with a report-not-edit rule (PR-105); gate rewritten: forged-looking Readiness sentence removed, paste-output rule added, scope fence made a declaration instead of a STOP, finalize ownership made conditional on runner vs hand execution, OQ-01 owner recorded (PR-106).
- 2026-10-02 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Reviewed at HEAD `07a0dd8e1` in an isolated review lane; plan committed and byte-identical to the lane input, so no pre-review snapshot. Replayed `check_lifecycle_transitions`' walk over the live pending tree (gitignored probe, no production edit): 184 pending plans, 41 validated transitions, 124 multi-status zero-coverage plans (all from `ordered=False` groups), 31 single-status zeros; the <=1-day collapse leaves 3 validated and 26 plans losing all, so F-04's thesis holds and is larger than authored. Fixture replay confirms the decisive pair: a two-date legal lifecycle validates 3, the one-date version validates 0 with one unordered group. Confirmed `drift_exit_code` exempts only `info`, `Drift.severity` exists, `check.collisions-not-checked` precedent, `2vev8j` 4.3/4.4 text, all five sibling plans pending and unexecuted. Fixed: E-02 now emits from a SIBLING function sharing one walk helper, because `tests/test_history_order.py` asserts `check_lifecycle_transitions(...) == []` on fixture (e), a two-status single-date plan that is exactly the new rule's trigger (PR-001); live counts and the existing-rule finding set (now 5, not 3) re-measured and every bar re-derived at execution rather than pinned to authoring (PR-002, PR-005); day-one volume (~124 `info` findings) stated and a before/after count demanded (PR-003); the `reverted` base-run instruction replaced with a shared-checkout-safe route (PR-004).
- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `o8l2y2`. The item describes the two-clock divergence, which is ALREADY owned by five review-ready plans (`5ivkdh` the production fix, `ayhveg` the cross-spelling guard, `9wcei0` the scaffold site, `rfyrvp` the plan-family `created` site, and `qjm4bg` the duplicate convergence, that last one naming `o8l2y2` as one of five pure duplicates it closes). Rather than author a sixth copy of the same fix, the authoring turn re-derived the item's claim and then asked what the fix BREAKS, finding a consequence none of the five covers: the `error`-severity lifecycle-transition gate derives event order from the very date variation the fix removes. The two-clock divergence itself was reproduced end to end at HEAD `4ec14077c` under `TZ=Pacific/Honolulu` (local `2026-10-01`, UTC `2026-10-02`) through the real CLI with no hand-editing, and the coverage collapse was measured over the live pending corpus (30 validated transitions -> 2). Bare suite baseline at authoring: `3 failed, 4624 passed, 2 skipped` (all three pre-existing, in unrelated modules).
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the lifecycle-transition gate SAY when it validated nothing, so that unifying the history clock
cannot retire a live `error`-severity check without anyone noticing.

This plan does not fix the clock and does not change a single verdict the gate reaches today. It
closes the observability hole that lets a correct fix look like an improvement while removing
enforcement.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: make the blindness observable

- [ ] E-01 Register ONE new `info`-severity rule in `check_engine.RULE_REGISTRY` for "the lifecycle gate examined this plan and validated no transition at all", and nothing else in this item. Give its registry comment the reason it exists: the gate's inputs are DATE-DERIVED, the UTC history-date ruling (spec `2vev8j` 4.4) removes date variation, and a gate that validates nothing is otherwise indistinguishable in output from a gate that found nothing wrong.

    IT MUST BE `info`, AND THAT IS A CORRECTNESS REQUIREMENT RATHER THAN A PREFERENCE. Measured in this lane: `artifact_core.drift_exit_code` maps `error`, `warning` and an EMPTY severity all to exit 1, and only `info` to exit 0. A zero-coverage plan is not a malformed plan, so anything but `info` would convert a reporting gap into a repository-wide red gate across the pending plans that already have two or more distinct statuses and zero validated transitions (79 at authoring; 124 of 184 at the first review on 2026-10-02; 62 of 137 at the second review on 2026-10-07; a live population that moves daily and must be re-derived at execution). `check.collisions-not-checked` is the precedent registered in this same file for exactly this shape, an `info` rule whose purpose its own comment states as "it removes the silence without inventing a failure".

    DO NOT CHANGE `check.lifecycle-transition-invalid`'s SPEC OR SEVERITY. The new rule is a companion that reports coverage; the existing rule keeps reporting violations. Touching the latter would put this plan in the business of changing verdicts, which is explicitly out of scope.
  - Depends on: none
  - Expected outcome: `RULE_REGISTRY` carries one new `info` rule id with a comment stating the date-derivation reason and naming spec `2vev8j` 4.4; nothing emits it yet; the bare suite's failing node-id set equals a baseline RE-DERIVED at execution HEAD before any edit (the authoring `3 failed, 4624 passed, 2 skipped` is context, not the bar), because no behavior has moved.
  - Execution state: pending

- [ ] E-02 Emit the new rule from a NEW SIBLING of `check_engine.check_lifecycle_transitions` (never from that function's own return; see the separation paragraph below) when, for one plan, the gate's own walk validated ZERO transitions while the plan's history carries TWO OR MORE distinct forward lifecycle statuses. Compute it from the SAME walk that produces the existing verdicts, in the same pass, so the two can never disagree about what was examined.

    THE TWO-DISTINCT-STATUSES CONDITION IS WHAT MAKES THIS A SIGNAL INSTEAD OF NOISE, and it must not be dropped for a simpler "validated zero" test. Measured over the 123 pending plans with a history block at authoring (re-measured at review: 31 of 184 on 2026-10-02, 18 of 137 on 2026-10-07): 22 of them validate zero transitions LEGITIMATELY, because their history records only ONE distinct status and there is genuinely no transition to check. Reporting those would emit 22 findings that no author can act on, which is precisely the "a gate that false-positives on correct behavior TRAINS agents to bypass it" failure mode recorded in backlog `gjadwm` and quoted in `tk1gqo`.

    STATE THE DAY-ONE VOLUME HONESTLY. The rule fires on the existing population immediately: about 124 `info` findings on `aw check plans` at the first review (beside 45 existing `info`), and about 62 at the second review on 2026-10-07 (beside 78 existing `info`); re-derive the number at execution rather than quoting either. That is the measured blindness, which is the point, but a report that becomes mostly this rule is a readability cost. Keep it to ONE finding per plan (the `check.scope-drift` collapse precedent) with a bounded detail, and paste the before/after per-rule `info` counts in V-04 so the maintainer sees the volume rather than discovering it.

    THE DETAIL MUST NAME WHAT WAS SKIPPED AND WHY, not merely that coverage was zero. Include the distinct statuses found and the dates of the groups the walk could not order, because the actionable remedy differs: a single-date burst is the clock-collapse case this plan exists for, while a mixed-direction block is a different cause with a different fix.

    EMIT IT FROM A SEPARATE PUBLIC FUNCTION, NOT INTO `check_lifecycle_transitions`'s RETURN LIST, and that is a regression requirement rather than a preference. `tests/test_history_order.py::HistoryOrderFixtureTests` calls `check_lifecycle_transitions` DIRECTLY and asserts `drift == []` (fixtures a, b, c, e) and `len(drift) == 1` (fixture d); fixture (e) is a two-status single-date plan that validates zero transitions, i.e. EXACTLY the shape the new rule fires on (verified at review 2026-10-02 by replaying the walk: `('2026-09-01', False)`, 0 validated), so appending the new finding to that function's return breaks a test this plan does not declare and must not edit. So: factor the existing per-plan walk into ONE private helper that returns BOTH the violation drifts and the count of validated transitions (plus the distinct statuses and the unordered group dates), have `check_lifecycle_transitions` return exactly what it returns today from that helper, and add a sibling (for example `check_lifecycle_transition_coverage`) that calls the SAME helper and emits only the new rule. Wire the sibling into the plans-type branch of `check_engine.check_content` (which `check_type` composes; the existing call sits under the comment "agentadhere Phase 3 (IPD wqj1ne): event-derived transition validity") immediately after the existing `check_lifecycle_transitions` call, fail-isolated in the same `try/except Exception: pass` shape as every neighbour there. Do NOT add it to `check_commit_invariants`, which never composed the existing rule either. One helper, two callers: the two outputs still cannot disagree about what was examined, which is what the "same walk, same pass" requirement above exists to guarantee.

    THE NEW FINDING REACHES EVERY `check_content(repo, "plans")` CALLER, so check the suite for collateral. Tests that drive `check_content`/`check_type`/`aw check plans` over fixture plans (for example `tests/test_check_engine.py`, `tests/test_check_engine_from_spec_missing.py`, `tests/test_carrier_reverse_lookup.py`, `tests/test_work_gate_severity.py`) were read at review and filter by rule id or by severity `warning`/`error`, so an extra `info` finding should not move them; the bare-suite failure-set comparison is the proof. If one DOES move because it counts unfiltered findings over a multi-status single-date fixture, that is a regression of this plan: report it with the node id rather than editing an undeclared test.

    SCOPE IT EXACTLY AS THE EXISTING RULE IS SCOPED. That function already skips any plan not under `pending/`, with a recorded reason (terminal-dir plans carry slimmed pre-rule histories and re-litigating them would be a whole-tree false-positive explosion). The companion inherits that scoping for the same reason.
  - Depends on: E-01
  - Expected outcome: a pending plan whose history holds two or more distinct statuses and yields no validated transition produces exactly one `info` finding from the new sibling function (and through `check_type(repo, "plans")`), naming its distinct statuses and its unorderable group dates; a plan with one distinct status produces none; `check_lifecycle_transitions` returns byte-identical results to before on every fixture, so `tests/test_history_order.py` passes unmodified; `aw check plans` still exits on the same code it did before for every fixture, because `info` does not gate.
  - Execution state: pending

### Task group 2: pin the property that the clock fix would otherwise erase

- [ ] E-03 Add `tests/test_lifecycle_gate_coverage.py` asserting the REPORTED-NOT-SILENT property across the date collapse, driving the real checker over fixture plans rather than inspecting the module. The decisive case is a PAIR: one plan whose legal `draft -> to-review -> reviewed -> approved` history is spread over two dates (the gate validates transitions, no coverage finding), and the same lifecycle with every record on ONE date (the gate validates nothing, and the new `info` finding appears). The second half is the post-UTC-fix world, and the assertion is that it is REPORTED rather than silent.

    ASSERT ON THE CHECKER'S OUTPUT, NEVER ON THE SOURCE. No `inspect`, no regex over `check_engine.py`, no asserting that a module mentions `timezone.utc`: GUIDING_PRINCIPLES P16 and the `AGENTS.md` no-code-pinning rule both forbid it, and the observable outcome here is the finding set the checker returns.

    ALSO PIN THE NEGATIVE AND THE EXIT CODE, because both are load-bearing and neither is implied by the positive case. A one-distinct-status plan must produce NO coverage finding (this is E-02's noise guard, and without a test it will be "simplified" away by a later reader), and a run whose only finding is the new `info` rule must still exit 0 (this is E-01's severity requirement, and it is what keeps the existing multi-status zero-coverage plans, 62 at the second review, from turning the gate red). PROVE IT IN THE CANONICAL TWO-LIMB SHAPE, because a fixture plan driven through the whole `check_type` sweep can trip OTHER rules (for example the `info` `check.ipd-lint-diagnostic` or a `warning`), so 'a run whose only finding is the new rule' is not reliably constructible: (a) `check_engine.rule_spec(<new id>).severity == "info"`, and (b) `artifact_core.drift_exit_code` over the ENRICHED findings the new sibling returns equals 0, contrasted with the same list `_replace(severity="error")` equalling 1. A whole-CLI `aw check plans` exit 0 over the fixture is an optional third limb, usable only if the fixture is otherwise clean.

    BUILD FIXTURES, DO NOT ASSERT OVER THE LIVE CORPUS. A test keyed to "20 plans lose coverage" would be a census that rots within a day; the measured corpus numbers belong in this plan's Findings as motivation, not in an assertion.
  - Depends on: E-02
  - ALSO PIN THE NON-REGRESSION OF THE EXISTING RULE IN THIS FILE: drive `check_lifecycle_transitions` on the one-date fixture and assert it still returns `[]`, so the separation E-02 requires is itself tested.
  - Expected outcome: `tests/test_lifecycle_gate_coverage.py` passes, containing at minimum the two-date/one-date pair, the single-status negative, and the exit-0 assertion; demonstrated RED before E-01 and E-02 (the one-date case reports nothing) and GREEN after.
  - Execution state: pending

- [ ] E-04 Record the finding and the limit in `CHANGELOG.md` in one entry, stating that the lifecycle gate now reports when it validated no transitions, and stating the LIMIT plainly: this makes the blindness visible, it does not restore the lost enforcement, which needs spec `2vev8j` 4.3's explicit per-artifact `seq`.

    SAY THE LIMIT, because an entry claiming the gate was fixed would be false and would discourage the real fix. The honest claim is observability, and the reason the real fix is out of scope is that `seq` is a storage-contract change the spec already owns and this plan must not pre-empt.
  - Depends on: E-03
  - Expected outcome: one `CHANGELOG.md` entry describing the new `info` rule and naming the `seq` limitation, containing no em or en dash.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16). This plan's whole claim is about what the checker REPORTS, so every assertion drives the checker and reads its findings.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and deselects `slow`/`livecorpus`; `-n0` is forbidden, and a second `-q` suppresses the `N passed` line this plan requires pasted. Use `-o addopts=""` only when a narrowed run needs per-test counts.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- SEVERITY DECIDES EXIT CODE, and the mapping is not uniform: measured in this lane, `artifact_core.drift_exit_code` returns 1 for `error`, for `warning` AND for an EMPTY severity string, and 0 only for `info`. `core.Drift` is a NamedTuple whose `severity` is its NINTH field, so it must be passed by KEYWORD; a positional near-miss silently lands the value in another field.
- A release-gated backlog item cannot be closed casually: `aw backlog set done` fails closed on an item carrying `- Blocks-Release:` unless the gate is HANDED OFF, SATISFIED with a resolvable in-tree citation, or explicitly DE-GATED. This plan closes nothing; the runner sets `o8l2y2` to `graduated` on the `From-Backlog` handoff, which preserves the gate.
- An `info` companion rule reporting what a checker did NOT examine is established practice in this file, not a new idea: `check.collisions-not-checked` exists for exactly that, and its comment states the principle ("it removes the silence without inventing a failure").

## Findings

Established in this lane at HEAD `4ec14077c`, by driving the real CLI and the real checker.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (THE BACKLOG ITEM'S OWN DEFECT, REPRODUCED) | Under `TZ=Pacific/Honolulu` (local `2026-10-01`, UTC `2026-10-02`), two real CLI calls on one fixture item wrote, into one file: `- 2026-10-02 same-status (aw set): m` and `- 2026-10-01 same-status (aw backlog): m`. No hand-editing. | **THE ITEM DESCRIBES A REAL, LIVE DEFECT.** It is confirmed rather than inherited, which is what licenses the rest of this plan to ask what its FIX does rather than re-fixing it. |
| F-02 | HIGH (THE ITEM'S FIX IS ALREADY OWNED FIVE TIMES) | `5ivkdh` (production fix, six modules), `ayhveg` (cross-spelling guard), `9wcei0` (`aw ipd scaffold` site), `rfyrvp` (plan-family `created` site), `qjm4bg` (duplicate convergence, whose E-03 closes `o8l2y2` by name as one of five "pure duplicates"). All five are `to-review` and release-gated. | **A SIXTH COPY OF THE CLOCK FIX WOULD COLLIDE WITH FOUR REVIEW-READY PLANS AND ADD NOTHING.** This is why this plan's subject is the fix's CONSEQUENCE, and it is also why `o8l2y2` closing through `qjm4bg` remains correct and is not contested here. |
| F-03 | HIGH (THE UNOWNED CONSEQUENCE) | `ipd_lifecycle._plan_status_event_groups` classifies a block's direction by comparing ADJACENT RECORD DATES and documents the tie case as "none (single date / 1 record) -> unknown"; `check_engine.check_lifecycle_transitions` then sets `prev = None` and `unvalidated = True` on an unordered group with more than one distinct status, SKIPPING its transitions. | **THE `error`-SEVERITY GATE'S INPUT IS THE EXACT DATE VARIATION THE UTC FIX REMOVES.** None of the five owning plans names this; `9wcei0` explicitly fences the classifier out as "conservative by design". So the consequence is unowned, which is this plan's reason to exist. |
| F-04 | HIGH (MEASURED, NOT INFERRED) | Over the 123 pending plans carrying a history block, replaying the checker's own walk: it validates **30** transitions today. Collapsing only the intra-block date gaps of <=1 day (the local/UTC skew signature, leaving genuine multi-day gaps alone) drops that to **2**, and **20** plans lose every validated transition. RE-MEASURED AT SECOND REVIEW (HEAD `fe2ee961c`, 2026-10-07, same walk and same <=1-day collapse): 137 pending plans, **104** validated today, **68** after the collapse, **21** plans losing every validated transition. The absolute drop is smaller because many current plans span multi-day gaps, but the per-plan loss is unchanged in shape. | **THE COVERAGE LOSS IS LARGE AND CONCRETE.** It is reported as a measurement with its method stated, not as a worst case: the collapse is restricted to skew-sized gaps precisely so the number reflects what the UTC fix can actually do. |
| F-05 | HIGH (WHY NO EXISTING TEST CAN CATCH IT) | A gate that validates zero transitions emits zero findings, so its output is identical to a clean run. `tests/test_history_order.py` and `tests/test_ipd_lifecycle_backward_edges.py` are the only test modules referencing this rule, and both assert on VIOLATIONS reported, never on transitions EXAMINED. | **THE REGRESSION IS INVISIBLE TO THE SUITE AND LOOKS LIKE AN IMPROVEMENT.** `aw check plans` gets GREENER as the gate goes blinder. This is the finding that makes an `info` report, not a stricter check, the right deliverable. |
| F-06 | MEDIUM (THE NOISE FLOOR, WHICH SHAPES E-02) | Of the 123 pending plans with a history block, **22** validate zero transitions LEGITIMATELY, carrying only ONE distinct status; **79** already carry two or more distinct statuses AND validate zero transitions. RE-MEASURED AT REVIEW (HEAD `07a0dd8e1`, same walk replayed): 184 pending plans, 41 validated transitions, **31** single-status zeros, **124** multi-status zeros, every one of the 124 caused by an `ordered=False` group; the <=1-day collapse leaves 3 validated and 26 plans losing all. RE-MEASURED AT SECOND REVIEW (HEAD `fe2ee961c`, 2026-10-07): 137 pending plans, **18** single-status zeros, **62** multi-status zeros, all 62 containing an `ordered=False` group. The numbers drift daily; the SHAPE (a large majority of pending plans already unaudited) holds. | **"VALIDATED ZERO" ALONE WOULD EMIT 22 UNACTIONABLE FINDINGS**, so the rule must require two or more distinct statuses. The 79 also fix the severity question: at anything above `info` this rule turns the repository red on day one. |
| F-07 | MEDIUM (THE REAL FIX IS OWNED BY AN UNIMPLEMENTED SPEC SECTION) | Spec `2vev8j` 4.3 (approved) rules that ordering is an explicit per-artifact `seq` and that "A full RFC 3339 UTC timestamp is retained for audit and display and is NEVER used to order", instructing the reader to "drop `events.reverse()`, the date sort, and the lifecycle-rank tiebreak". Measured: `record_history` contains no `seq`. | **THE DATE-DERIVED CLASSIFIER IS STILL LOAD-BEARING BECAUSE 4.3 IS UNIMPLEMENTED, WHILE 4.4 IS BEING IMPLEMENTED NOW.** Implementing one ruling without the other is what creates this window, and it bounds this plan honestly to observability rather than repair. |
| F-08 | MEDIUM (THE GATE IS ALREADY LIVE AND RED) | `check_lifecycle_transitions` over the live pending tree returns **3** `check.lifecycle-transition-invalid` findings today, on `5poaqh`, `fv6kep` and `36sifo`. The rule's registered severity is `error`. At the first review (HEAD `07a0dd8e1`) it returned **5** (adding `1xthrh`, `1znlxy`); at the second review (HEAD `fe2ee961c`, 2026-10-07) it returned **0**. | **THIS IS A LIVE, GATING RULE AND NOT A DORMANT ONE**, so silently reducing what it examines has immediate effect. The set moves both ways between days, so any execution must compare FINDING SETS BY NAME against a baseline re-derived at execution rather than expecting any authored value. A zero set is now also the case this plan exists for: with the existing rule reporting nothing, only the new rule can distinguish 'examined and clean' from 'examined nothing'. |
| F-09 | LOW (PRECEDENT FOR THE EXACT SHAPE) | `check.collisions-not-checked` is registered in this same file as `info`, for "a per-type `aw check <type>` does NOT run the cross-tree collision scan", with the stated aim that "`info` is the whole point: it removes the silence without inventing a failure". | **AN `info` RULE REPORTING WHAT A CHECKER DID NOT EXAMINE IS ESTABLISHED PRACTICE HERE.** This plan follows a pattern rather than introducing a mechanism. |
| F-10 | N/A (BASELINE) | Bare `python3 -m pytest` at HEAD `4ec14077c`: `3 failed, 4624 passed, 2 skipped, 3 warnings in 187.22s`, failing in `test_spec_review_attestation`, `test_run_finding_reachability` and `test_selector_type_containment`. | **THE BASE IS NOT ALL-GREEN**, so execution must compare failure sets BY NAME. None of the three involves a date, the checker, or the lifecycle gate. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/check_engine.py`: register one `info` rule for "the lifecycle gate validated no transition for this plan", with a comment naming spec `2vev8j` 4.4 and the date-derivation reason (E-01).
2. `agent_workflows/check_engine.py`: emit it from a new sibling function sharing ONE private walk helper with `check_lifecycle_transitions` (whose return stays unchanged), wired into the plans-type branch of `check_content` (composed by `check_type`), only when two or more distinct forward statuses are present, with a detail naming those statuses and the unorderable group dates (E-02).
3. `tests/test_lifecycle_gate_coverage.py`: the two-date/one-date fixture pair, the single-status negative, and the exit-0 assertion, driving the real checker (E-03).
4. `CHANGELOG.md`: one entry stating the new report and its limit, naming `seq` as the real fix (E-04).

## Deferred / out of scope (with reason)

- THE PRODUCTION CLOCK FIX IS NOT MADE HERE. `5ivkdh` declares `artifact_core.py`, `backlog.py`, `specs.py`, `status_set.py`, `releases.py` and `readiness_recheck.py` and routes every history writer onto one UTC helper. This plan touches none of those paths, so the two are disjoint and need no ordering edge. `5ivkdh` has since EXECUTED (2026-10-03), so the UTC clock is live and every new history record now writes the collapsed dates this plan's F-04 measures; the observability this plan adds is therefore no longer anticipatory but already needed.
  - Carrier: 5ivkdh
  - Carrier-Evidence: .aw/records/plans/executed/20261001-7qvs1c-01-5ivkdh-unify-every-artifact-history-date-onto-the-utc-clock-ruled-b.ipd.md
- THE CROSS-SPELLING TIMEZONE GUARD IS NOT BUILT HERE. `ayhveg` derives a differential guard from `command_surface.COMMAND_INVENTORY` and asserts recorded dates equal the UTC date. That proves the clock is right; it says nothing about what the lifecycle gate still examines, which is this plan's subject.
  - Carrier: ayhveg
- THE SCAFFOLD AND PLAN-FAMILY WRITER SITES ARE NOT TOUCHED. `9wcei0` owned `aw ipd scaffold`'s `draft` record and has EXECUTED; `rfyrvp` (the plan-family `created` record) was SUPERSEDED on 2026-10-03 by `9wcei0`, which carried that fix. Both live in `ipd_authoring.py`, which this plan does not declare.
  - Carrier: 9wcei0
  - Carrier-Evidence: .aw/records/plans/executed/20261002-jvw1kg-01-9wcei0-stamp-the-scaffold-s-draft-history-record-from-the-utc-clock.ipd.md
- THE DUPLICATE-ITEM CONVERGENCE IS NOT PERFORMED HERE, AND `o8l2y2` CLOSING AS A DUPLICATE IS NOT CONTESTED. `qjm4bg` E-03 names `o8l2y2` among five pure duplicates it closes once its carriers execute. That verdict is correct about the item's TEXT; this plan carries the item's `From-Backlog` handoff for the distinct consequence found while re-deriving it, and writes no status onto any backlog item.
  - Carrier: qjm4bg
- SPEC `2vev8j` 4.3's EXPLICIT PER-ARTIFACT `seq` IS NOT IMPLEMENTED HERE, AND IT IS THE REAL FIX. It is a storage-contract change across every writer and reader of history, with a migration and a checkpoint rule (4.7), and it is the only route that RESTORES the enforcement this plan merely makes visible. Folding it into an observability change would hide a major migration inside a small plan.
  - Carrier-Declined: not a defect; it is approved, unimplemented design whose scope exceeds this plan and which no evidence here lets this plan pre-empt.
- THE DIRECTION CLASSIFIER IS NOT CHANGED. `_plan_status_event_groups`'s "unknown direction means unordered" behavior is conservative by design, and `ipd_lifecycle` carries an explicit note that its two readers answer different questions and must not be unified. Loosening it to infer order from lifecycle rank was already measured and REJECTED under `tk1gqo` (it cannot represent the same-day re-review after approval that the maintainer later ruled legal in spec 4.8).
  - Carrier-Declined: not a defect; the classifier is correct to refuse to guess, and the information it needs does not exist in the record until `seq` does.
- THE EXISTING `error` RULE'S SEVERITY AND VERDICTS ARE UNCHANGED. Its live finding set (3 at authoring, 5 at the first review, 0 at the second; F-08) must be identical before and after this plan, re-derived at execution. Making the gate stricter to compensate for lost coverage would invent failures rather than report blindness.
  - Carrier-Declined: not a defect; the rule is correct about what it does examine.
- NO CORPUS MIGRATION AND NO HISTORY RESTAMPING. Records carry whichever clock wrote them; rewriting them to assert dates that were never recorded would be a false record (GUIDING_PRINCIPLES P4). The 20 plans in F-04 need no edit, because this plan changes reporting only.
  - Carrier-Declined: not a defect; existing records are the honest history.
- THE THREE PRE-EXISTING SUITE FAILURES ARE NOT FIXED (F-10). None involves a date, the checker, or the lifecycle gate.
  - Carrier-Declined: unrelated to this plan's subject; it touches neither those modules nor the code they exercise.

## Scope check

- Over-scope: none. Every declared path is edited by a numbered item: `agent_workflows/check_engine.py` (E-01, E-02), `tests/test_lifecycle_gate_coverage.py` (E-03), `CHANGELOG.md` (E-04).
- Under-scope: E-02 computes its signal from the SAME walk `check_lifecycle_transitions` performs, via a shared private helper both public functions call, over groups produced by `ipd_lifecycle._plan_status_event_groups`. Verified at both reviews that the producer already exposes everything needed (each group's date, members and `ordered` flag; second review replayed the one-date fixture to `[('2026-09-02', [approved, reviewed, to-review, draft], False)]`), so no producer change is required. Editing the classifier is out of scope because it would change the existing gate's verdicts under an observability mandate; if an executor nonetheless finds the signal underivable without it, mark E-02 `blocked` with the reason rather than editing `ipd_lifecycle.py`. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. Re-derive the baseline at execution HEAD before any edit (authoring measured `3 failed, 4624 passed, 2 skipped` at `4ec14077c`, F-10, as context only); compare FAILURE SETS BY NAME, never counts.
- `tests/test_lifecycle_gate_coverage.py` run alone with `-o addopts=""`, every case named, demonstrated RED at base (the one-date fixture reports nothing before E-01/E-02) and GREEN after. A guard never seen failing proves nothing.
- `tests/test_history_order.py` and `tests/test_ipd_lifecycle_backward_edges.py` each run individually, UNMODIFIED, with output pasted. They are the only modules exercising this rule, and they are the guard that E-02 did not change an existing verdict. `test_history_order.py` fixture (e) is specifically the guard that the new rule did not leak into `check_lifecycle_transitions`' return list.
- The EXISTING rule's finding set over the live pending tree, re-derived at execution HEAD before the edit and again after, diffed BY NAME. It was `3` at authoring (`5poaqh`, `fv6kep`, `36sifo`), `5` at the first review (adding `1xthrh`, `1znlxy`) and `0` at the second review, so no authored list is the bar; an execution that changes the before/after set has changed verdicts and is out of scope.
- A driven demonstration of the coverage property on fixtures, pasted: a two-date legal lifecycle (transitions validated, no coverage finding) and the SAME lifecycle on one date (zero validated, exactly one `info` finding). This is the plan's thesis and must be shown, not asserted.
- The two-limb exit proof (registry severity `info`; `drift_exit_code` over the sibling's enriched findings is 0 and is 1 with severity swapped to `error`), pasted. This is E-01's severity requirement, and at any other severity the multi-status zero-coverage plans in F-06 (124 at the first review, 62 at the second) turn the gate red.
- A single-distinct-status fixture producing NO coverage finding, pasted. This is E-02's noise guard.
- `AW_NO_REEXEC=1 aw check`, `AW_NO_REEXEC=1 aw check plans`, `AW_NO_REEXEC=1 aw attention --check` and `AW_NO_REEXEC=1 aw sanitize --agent`. `aw check` and `aw attention --check` exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET: re-derive before and after and diff. Do not "fix" another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing.

## Spec / documentation sync

No spec is amended, so no `.spec.md` file appears in `Scope-Paths`.

This plan is DOWNSTREAM of spec `2vev8j` and consistent with it on both counts. Section 4.4 (UTC for
every writer) was implemented by the sibling plans (`5ivkdh`, `9wcei0`, both executed) and this plan does not touch a clock. Section
4.3 (ordering is an explicit per-artifact `seq`, never a timestamp) is the ruling that WOULD remove
the date dependence entirely, and it is unimplemented (F-07); this plan reports the gap that opens
while 4.4 lands without 4.3, which is strictly less than 4.3 mandates and contradicts none of it.

`CHANGELOG.md` gets one entry, because a new reported diagnostic is user-visible, and it must name the
limit so no reader mistakes observability for repair.

## Open questions

### OQ-01: Should the lifecycle gate's lost coverage be RESTORED here rather than merely reported?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as REPORT, NOT RESTORE, because every restoration route has already been measured and rejected in this repository. Backlog `tk1gqo` records three reader-only fixes driven to numbers: `events.reverse()` gives 15 findings, a stable date sort gives 32 (WORSE, because dates are day-granular), and date-plus-lifecycle-rank gives 3 but INFERS order from a forward-only invariant that spec `2vev8j` 4.8 later abolished when the maintainer ruled a backward recovery edge legal. The maintainer further ruled on 2026-09-05 to research the storage question BEFORE touching the reader again, and an interim patch was written, measured and DELIBERATELY REVERTED rather than committed, with `aw check plans` left red BY DECISION. The research landed in four independent reports that all rejected inferring order from position OR dates, and the resulting spec Section 4.3 makes ordering an explicit per-artifact `seq`. So restoration is OWNED, DESIGNED and APPROVED, and it is a storage change this plan has no mandate for; what is NOT owned, and what no measured route addresses, is that the gate cannot say when it validated nothing. Worth raising to the maintainer (and not resolvable from evidence): spec 4.4 has now LANDED (`5ivkdh` executed 2026-10-03, `9wcei0` executed) while 4.3 remains unimplemented (re-checked 2026-10-07: `record_history.py` contains no `seq`), and that ordering is what opens this window, so the maintainer may wish to prioritize `seq` rather than accept an indefinite period of reported-but-unenforced lifecycle transitions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: the new registry entry quoted, showing `info` severity and a comment naming spec `2vev8j` 4.4 and the date-derivation reason. Plus a pasted `drift_exit_code` probe over the new rule's severity returning 0, since `error`, `warning` and an empty string all return 1 and a positional-field near-miss is a measured hazard. Plus a bare-suite run whose failure set BY NAME equals the baseline re-derived at execution HEAD before any edit (pasted), proving registration alone moved nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the checker driven over a fixture repository, with pasted output showing exactly one `info` finding for a plan carrying two or more distinct statuses and zero validated transitions, and the finding's detail naming both the distinct statuses and the unorderable group dates. Plus pasted proof of the scoping: a plan in a TERMINAL disposition directory with the same history produces no finding. Plus the existing `check.lifecycle-transition-invalid` set over the LIVE pending tree derived immediately BEFORE and AFTER the edit and diffed BY NAME, showing it unchanged (the authored values, 3 then 5 then 0, are context and not the bar). Plus `tests/test_history_order.py` passing UNMODIFIED, proving `check_lifecycle_transitions`' own return is unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `tests/test_lifecycle_gate_coverage.py` pasted FAILING at base and PASSING after. Produce the base run by writing the test BEFORE E-01/E-02 are applied, or by importing `git show HEAD:agent_workflows/check_engine.py` from a gitignored scratch location; do NOT `git stash` or revert the working tree (shared checkout, AGENTS.md). The failing base run is expected to fail on the missing sibling function or the missing finding, and that failure is the evidence; each with `-o addopts=""` and every case named. The two-date and one-date fixture outputs pasted side by side so the collapse is visible. The single-status negative pasted producing no finding. The two-limb exit proof from E-03 pasted: the registry severity `info`, `drift_exit_code` over the sibling's enriched findings returning 0, and the same list with severity swapped to `error` returning 1. Plus `tests/test_history_order.py` and `tests/test_ipd_lifecycle_backward_edges.py` results. Plus a statement that the test file contains no `inspect`, no source regex and no assertion over the live corpus.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the `CHANGELOG.md` entry quoted in full, showing it names both the new report and the `seq` limitation, and containing no em or en dash. Plus the final bare suite with its `N passed` line and its failure set compared BY NAME to the baseline. Plus `aw check`, `aw check plans`, `aw attention --check` and `aw sanitize --agent` before-and-after finding sets, with `aw check plans`' per-rule counts pasted before and after so the new rule's day-one `info` volume is visible and it is shown to be the ONLY rule whose count moved, and `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan's `- Readiness:` field is written by `/plan-review` only; no executor or author may write
or change it. It requires explicit human approval (`Status: approved`) before execution.

Execution contract: commit ONLY the files this plan changed, limited to its `Scope-Paths`, through
`aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push.
Verify the staged set with `git diff --cached --name-only` before each commit and unstage anything
not this plan's with `git restore --staged <path>`; this is a shared checkout and another agent's
uncommitted work must never enter a commit here.

Validation is not optional and not inferable: every `V-*` item demands pasted output from a command
actually run. In particular, a GREEN SUITE IS NOT EVIDENCE FOR THIS PLAN, because the regression it
addresses makes the suite greener rather than redder (F-05). The new guard MUST be demonstrated
failing before the change.

Paste the ACTUAL runner output for every test, check and lint claimed; a result not pasted is a
result not claimed.

SCOPE FENCE (a declaration the finalize scope gate reconciles, not a stop directive): this plan edits
only its `Scope-Paths`. It does not touch the clock (owned by `5ivkdh`, executed, and its siblings),
the direction classifier in `ipd_lifecycle.py`, the existing `error` rule's severity or any verdict
it reaches, any undeclared test, or spec 4.3's `seq`. Any out-of-scope edit that nonetheless proves
necessary must be justified with a `--scope-reason` at finalize; a declared path left unmodified needs
a `--scope-ack`.

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming. The
terminal transition to `.aw/records/plans/executed/` is tooled and its owner is conditional: under
`aw oc run` / `aw agy run` the RUNNER finalizes after its merge-and-revalidate gate, and the executor
must NOT run `aw ipd finalize` itself; in a hand execution with no runner, the executor runs
`aw ipd finalize <plan>`. Never `git mv` the plan or hand-edit the terminal state. Backlog item `o8l2y2` is handed off via `- From-Backlog:` and should reach
`graduated`, not `done`: this plan carries its `- Blocks-Release: next` gate, and the gate is released
only when this plan is `executed`.
