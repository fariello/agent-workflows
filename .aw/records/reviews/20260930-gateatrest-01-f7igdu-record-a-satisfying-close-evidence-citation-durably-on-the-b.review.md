# Review findings: plan f7igdu

- Subject-Id: f7igdu
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-601 (HIGH, fixed), PR-602 (MEDIUM, fixed), PR-603 (LOW, fixed), PR-604 (LOW, fixed), PR-605 (LOW, fixed)

## Round 1

Reviewed at HEAD `61a78c9ea` in an isolated review lane. The plan file was committed and unmodified in the
lane (`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `conforming` with zero findings after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator checklist row check does not apply.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests on
RE-EXECUTING the measurements and on probing the surfaces the plan reasoned about without driving.

THE CENTRAL DEFECT IS REAL AND REPRODUCES EXACTLY, which for a plan of this kind is the finding that
matters most. Driven end to end in a scratch repo against the real CLI: `aw backlog set aaaaaa --status done
--evidence .aw/records/research/EVID.md` exits 0 and moves the item to `done/`; the written file carries
`- Blocks-Release: next` and NO trace of the citation anywhere, including in its `## Workflow history` (the
appended line reads only `status -> done`); and re-asking `evaluate_blocking_close` about that written item
with no `evidence=` returns `legitimate=False, severity='error', path=None` with the gate-dropping reason. So
a legitimate `SATISFIED` close is genuinely indistinguishable at rest from an illegitimate hand close, and
the plan's premise holds without qualification.

EVERY STRUCTURAL CLAIM THE DESIGN RESTS ON ALSO HOLDS. The predicate's arm order is exactly `DE-GATED`,
`HANDOFF`, `SATISFIED`, then the two refusals, so E-04's "order is unchanged" and E-03's dependence on
`HANDOFF` winning are both sound. `_TEMPLATE_OWNED_KEYS` is exactly the nine keys quoted, and the
non-template branch appends such a line verbatim. The `Gate-Summary` drop rule is real and conditioned on
`item.status == "blocked"`, so the naming caution in E-01 is well founded rather than decorative.
`set_release_exempt_kind_line` is exactly the strip-then-insert-after-`- Status:`-falling-back-to-`- Id:`
shape E-03 says to copy. F-05's round trip reproduces: an item carrying `- Close-Evidence:` survives
`aw backlog set --status open` byte-identically while `validate_item` returns `[]` and `parse_item` exposes
no attribute, which is precisely the "preserved but untyped and unvalidated" state E-02 closes. F-02's hook
docstring is quoted verbatim. F-04's runner argv is exact, and its docstring independently confirms the
positional spelling cannot even accept `--evidence`. Both open questions were re-verified and stand.

WHAT REVIEW FOUND was one under-counted consequence of the plan's own best convention, one deferral that has
gone stale in both of its claims, and three dated figures. None changes the design.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | UNDER-SCOPE | A (correctness), C (architecture), G (executability) | `agent_workflows/set_records.py` `close_on_answer` calling `evaluate_blocking_close(repo_root, backlog_path, "done", item_text=rendered)`; plan `## Scope check` | E-04 CHANGES FOUR CALLERS AND THE PLAN ENUMERATED ONE. Because the predicate is single-sourced (the plan's own first convention), a new at-rest INPUT reaches every caller that does not pass `evidence=`. Three do not: the `aw check` rule, the opt-in hook (the intended beneficiary), and `set_records.close_on_answer`. The Scope check dismisses the third because it "cannot produce a `SATISFIED` verdict and needs no write site" - true about WRITING, false about READING once E-04 lands, since an item already carrying the bullet gains a legitimacy route there. Measured: zero live items carry the bullet, so no live verdict changes on landing and the exposure is forward only, which is why the correct remedy is disclosure and enumeration rather than a design change or a scope widening. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-06 with the measurement. Added a bullet to E-04 requiring all four callers enumerated in the execution note with the new route's intendedness stated for each, and explicitly forbidding a caller-specific opt-out (which would fork the predicate the convention exists to keep single). Corrected the Scope check's under-scope paragraph to distinguish write site from read site. Extended V-04 to demand the enumeration plus a live-tree scan of how many items carry the bullet at execution time. |
| PR-602 | MEDIUM | IN-SCOPE | D (anti-regression), G | `.aw/records/plans/executed/20260929-anycarrier-01-2o5wka-...ipd.md` (`- Status: executed`); `check_engine.evaluate_blocking_close` docstring; backlog `lsbd32` in `done/` | THE `HANDOFF` DEFERRAL IS STALE IN BOTH ITS CLAIMS, AND ITS WARNING TO CHILD 02 IS NOW FALSE. The row defers the any-carrier-versus-all-carrier disagreement to "pending plan `2o5wka`" and warns that 4 of 175 historical closes "would become findings if that plan lands". Measured: `2o5wka` is EXECUTED, `lsbd32` is `done`, and the shipped predicate already requires EVERY same-gate carrier executed (its docstring says so and cites that plan). The warned population is 0 BY CONSTRUCTION, since a `HANDOFF` verdict can no longer coexist with an unexecuted carrier; a census confirms 0. Carrying the 4-item figure into child 02 would hand it a phantom to reconcile. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-07. Rewrote the deferral row as a correction rather than a deferral, stating the work is done, quoting the predicate's own tightening line, and recording that the population is zero by construction. Changed `Carrier: lsbd32` to `Carrier-Declined` with the reason that re-filing would assert outstanding work against an executed plan and a closed item. |
| PR-603 | LOW | IN-SCOPE | E (testing), G | plan F-03, F-04; censuses re-run at review | TWO CORPUS CENSUSES DRIFTED. F-03 cited 224 gated `done` items with `HANDOFF` 175 / illegitimate 49 / `SATISFIED` 0; re-measured, 236 with `HANDOFF` 183 / illegitimate 53 / `SATISFIED` 0. F-04 cited 146 of 224 runner-authored close lines; re-measured, 159 of 236. The load-bearing ZERO is unchanged in both directions, so both conclusions survive, but V-01 asks the executor to compare against the plan's numbers and would read ordinary corpus growth as a discrepancy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Appended the re-measured figures to F-03 and F-04 in place, labelling the authoring numbers as dated context and the zero as the finding. Extended V-01 to state that the figures have already drifted twice, to cite neither as the bar, and to say that only the zero is load-bearing. |
| PR-604 | LOW | IN-SCOPE | E, G | `tests/test_backlog_handoff_close.py` (20 test methods, 2 classes) | THE TEST FILE HAS TWICE THE CASES THE PLAN SAYS. The conventions section describes "its ten existing cases"; the file defines 20 test methods across `BacklogHandoffCloseBehaviorTests` and `BacklogGateDirSplitTests`. Two of them, `test_case_6_satisfied_evidence_allowed` and `test_case_7_degated_allowed`, are exactly the fixtures E-05's new cases (a) and (d) should extend, so the undercount cost a concrete reuse opportunity rather than only being inaccurate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected the conventions bullet to the real count and named the two classes. Added an instruction to E-05 to extend the two adjacent cases rather than build a fixture from scratch, naming which new case extends which. |
| PR-605 | LOW | IN-SCOPE | E, G | bare `python3 -m pytest` at review; backlog `tl8qmc`, `2wae2x` | ONE PRE-EXISTING SUITE FAILURE SITS IN A FILE THIS PLAN'S VALIDATION NAMES. Bare pytest reads `1 failed, 3427 passed, 2 skipped`; the failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a known local-versus-UTC history-date defect filed twice that fires only between local midnight and UTC midnight. The plan's validation section explicitly runs `tests/test_backlog.py` for per-test counts, so the executor WILL see it, and `tests/test_backlog.py` is not in `- Scope-Paths:`, so fixing it would be an undeclared edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-08 with the summary line and both backlog citations. Added a note to the validation section instructing the executor to report it as pre-existing with that citation rather than count it in the delta or fix it, and stating why (the file is out of declared scope). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `set_records.close_on_answer` becomes a new reader of the field after E-04 (PR-601). Should the plan suppress that route, widen scope to handle it, or accept and disclose it? | Accept and disclose: enumerate all four callers, state the new route is an accepted consequence of single-sourcing, and forbid a caller-specific opt-out. | (a) Add a flag or parameter letting `close_on_answer` skip the at-rest tier. Rejected because it would fork the single predicate that the plan's own first convention, and `AGENTS.md`, exist to keep single ("they cannot diverge"); a per-caller behavior switch is exactly the divergence that convention prohibits. (b) Widen `- Scope-Paths:` to include `set_records.py`. Rejected because no code change is needed there: it inherits the new input through the shared function, and declaring a file this plan does not edit would make the finalize scope gate demand a `--scope-ack`. (c) Say nothing. Rejected because the Scope check actively asserts the surface "needs no write site", which reads as "is unaffected" and is false about reading. | `set_records.close_on_answer`'s predicate call (no `evidence=`, `item_text=rendered`) read at review; a scan of `.aw/records/backlog/**.backlog.md` returning 0 items carrying the bullet, which bounds the exposure to forward-only; and `AGENTS.md`'s single-predicate rule. | yes |
| D-2 | The `HANDOFF` deferral's carrier (`lsbd32`) resolves to a CLOSED backlog item and an EXECUTED plan (PR-602). Keep the row as a deferral, delete it, or convert it? | Convert it to a correction that records what actually happened and declines a carrier. | (a) Delete the row. Rejected because the plan's prose warns child 02 about a 4-item population; deleting the row silently would leave that warning's reasoning unrecorded and a later reader could reintroduce it from the Set's history. (b) Keep `Carrier: lsbd32`. Rejected because a carrier field asserts outstanding work, and asserting it against a `done` item and an `executed` plan is false; it would also surface in any carrier-dangling check. | `2o5wka`'s `- Status: executed` and its location in `.aw/records/plans/executed/`; backlog `lsbd32` in `done/`; `evaluate_blocking_close`'s docstring line "tightened by anycarrier Order 1 (2o5wka, backlog lsbd32) to require all same-gate carriers executed"; and a census returning 0 HANDOFF-legitimate closes with an unexecuted same-gate carrier. | yes |
| D-3 | The plan is filed `chore`/`low` while its own F-01 is severity HIGH and the concern describes a gate that misjudges legitimate closes. Is the classification right, or is this a `bug` that should gate the next release? | Classification is right; leave `chore`/`low` and do not add `- Blocks-Release:`. | Reclassifying as `bug` and gating the release. Rejected on the repository's own stated test, which is USER-PERCEPTIBLE IMPACT: measured, the corpus contains ZERO `SATISFIED` closes, so no existing record is misjudged today and no user can observe the gap. The HIGH severity of F-01 describes the SHAPE of the defect (an unreconstructable legitimacy route), not its present reach, and the plan's gate paragraph already states this reasoning explicitly and honestly. | `AGENTS.md`'s "inefficiency a user can notice is a defect" test and its insistence that an unmeasured hunch is not a bug; the re-measured census showing `SATISFIED` 0 of 236 gated closes. | yes |

No `Reversible: no` decision was taken, so no escalation under the irreversible-decision rule is owed.

Both pre-existing open questions remain `resolved` and each was independently re-verified. OQ-01
(single-valued) stands on a re-checked fact: `evaluate_blocking_close`'s signature really does take
`evidence: Optional[str] = None` and returns on the first resolution, so a multi-valued field could express
a state the predicate cannot produce. OQ-02 (do not also record the `HANDOFF` carrier) stands: the carrier
really is reconstructable from `- From-Backlog:` plus the same `- Blocks-Release:`, which is what the
carrier scan reads, so a recorded copy would be redundant state a later rename could falsify. Their
`- Owner:` fields read `none`. That is accepted MECHANICALLY and the reason is narrow enough to state
precisely rather than wave at: `ipd_lint` computes `has_owner` as non-empty-and-not-`none`, but
`ipd_schema.open_question_error` consults it ONLY on the `deferred` branch, so a `resolved` question needs a
rationale and nothing else. Both of these are `resolved` with substantial rationales, so they conform. No
change was made, because the plan-review convention that an owner names who decided applies to a REVIEWER's
own resolution, and these two were resolved by the author at authoring time; this review's own choices are
recorded as D-1 through D-3 above rather than written into those fields.

No finding was left OPEN or DEFERRED, so no finding requires escalation as a `- Blocking: yes` question
under the review-findings gate.
