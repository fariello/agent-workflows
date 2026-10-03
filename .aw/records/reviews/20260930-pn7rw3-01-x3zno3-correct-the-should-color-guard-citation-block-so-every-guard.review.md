# Review findings: plan x3zno3

- Subject-Id: x3zno3
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file in `pending/` was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review and
again at `author` and `review-finalize` after revision. The plan is `- Kind: child`, so the `IPD-S407`
orchestrator child-row check does not apply.

THIS IS AN EXCEPTIONALLY WELL-EVIDENCED PLAN AND I FOUND NO DEFECT IN ITS REASONING. Every one of F-01
through F-09 reproduces exactly as written, which is rare enough to state plainly:

- F-01 verifies and is correctly stronger than the backlog item. All three cited guard files are absent
  (`ls` -> three `No such file or directory`), and a DEFINITION search for
  `test_exactly_one_definition_package_wide` and `OneOriginatingDefinitionTests`
  (`^\s*(def|class) ...`) returns ZERO matches. The plan's distinction between "mentioned" and "defined"
  is the right one and its predicted occurrence counts are exact: the former has two non-bytecode
  occurrences (`agent_workflows/runner_shared.py:331` and `tests/test_runner_shared.py:315`), which are
  the two false claims themselves.
- F-02 and F-03 verify. The shipped docstring of `runner_shared.should_color` carries the full three-guard
  argument ending "an import fails all three", AND the independent fourth claim that a module-level import
  is "REFUSED by a shipped guard: `tests/test_orchestrator_probe_cache.py::...`" whose file is absent. The
  plan is right that this is the more consequential instance and right that the item does not mention it.
- F-04 verifies: `ShouldColorGridTests` resolves at `tests/test_term.py:122`, `SharedColorDecisionTests`
  at `tests/test_runner_shared.py:4892`, and `OneOriginatingDefinitionTests` resolves nowhere while being
  cited twice more in `agent_workflows/term.py` (lines 340 and 568), exactly as described.
- F-05 verifies: both hosts carry `should_color as should_color` (multi-line import form, `oc_runipd.py:652`
  and `agy_runipd.py:354`) and `oc_runipd.py:869` lists the string in `__all__`. The plan's honesty here is
  notable: it records that an import would ALSO satisfy those, so the surviving justification is narrower
  than the one being replaced, and instructs E-04 to state the narrower truth rather than substitute a new
  overclaim. That is the correct instinct and it is what keeps this fix from recreating the defect.
- F-06 verifies by independent AST walk: one top-level definition, body `[ImportFrom, Return]` after the
  docstring, and `-k SharedColorDecision` returns `1 passed`.
- F-07's census verifies to the hit (26 across 7 files, same per-file distribution), and its claim that
  `t0ovw6` already fixed the host runners holds: `oc_runipd.py` and `agy_runipd.py` now carry 5 and 4
  occurrences of the corrective "deleted in `19313eed`" shape while `runner_shared.py` carries ZERO.
- F-08 verifies (`LaneIntegrationExtractionTests` 4 citations / 0 definitions;
  `tests/test_rununify_host_descriptor.py` absent) and F-09's bounding argument holds, including that
  pending plan `1jg2m2` declares only `docs/` plus `CONTRIBUTING.md` and so inherits no guard for
  `agent_workflows/`.
- Both maintainer rulings verify VERBATIM at their sources, and the deferral rows are unusually honest:
  three of seven are `Carrier-Declined` with real reasons, and the `verifier_evidence_corpus.json` row
  correctly identifies a case that must NOT be "fixed" because the string is regression-fence DATA.

SO EVERY FINDING I RAISED IS ABOUT DRIFT SINCE AUTHORING, NOT ABOUT THE PLAN'S JUDGEMENT. Three days
passed and the repository moved under it.

THE MOST CONSEQUENTIAL DRIFT IS THAT `ery0ia` IS NOW `approved`, NOT `reviewed` (PR-001). That plan deletes
the entire comment block E-03 targets, and it is now cleared to execute, so E-03's "satisfied by deletion"
branch is the LIKELY path rather than the exception. I verified the block boundary is real rather than
assumed: the false `should_color` claim sits at `tests/test_runner_shared.py:313` and the
`SUPERSEDED_SINCE_MOVE = (` assignment at `:353`, inside the block `ery0ia` E-02 deletes "WITH ITS OWN
PRECEDING BLOCK". I also checked the thing that would have made this a collision and it is clean:
`ery0ia` declares `tests/test_runner_shared.py` ALONE, so E-04's production subject
(`agent_workflows/runner_shared.py`) is unambiguously this plan's. Better still, `ery0ia`'s own
review-added F-09 resolves that block's six coverage pointers BY SYMBOL and deletes the unresolvable ones,
naming `OneOriginatingDefinitionTests` and `test_exactly_one_definition_package_wide` as "`pn7rw3`'s own
subject ... dissolved by the deletion". So under the deletion branch E-03's full intent is satisfied by
another plan. The plan's design already handled this correctly through E-03's idempotency and V-03's route
(b); what it lacked was the updated likelihood, so an executor would not read a near-certain no-op as a
missing subject.

THE SECOND DRIFT HAD A REAL FAILURE MODE (PR-002). Two of E-02's three recorded baselines have moved: the
bare suite from `3387 passed` to `3523 passed` (+136) and `tests/test_runner_shared.py` from `119` to `126`
(+7), with `tests/test_term.py` unchanged at 28. The plan's DESIGN is already right (E-02 re-derives at
execution rather than asserting the authoring figures, which is exactly the live-artifact re-derivation
convention), but V-03 and V-04 said "equals V-02's baseline" while the surrounding prose displayed specific
numbers, and V-04 declares a moved count "a FAILURE of this V-item, not a note". An executor comparing
against the printed `3387` would stop on a legitimate, unrelated difference. Both V-items now state that the
authoring and review figures are CONTEXT and the bar is the executor's own pre-edit measurement. I also
added the attribution rule the plan needed but did not have: if `ery0ia` lands BETWEEN V-02 and the later
V-items (now likely, per PR-001) the per-file count may legitimately change, so the executor must name the
landing commit and re-baseline rather than attribute a neighbour's deletion to this plan, which is the only
way a real regression stays visible.

ONE FINDING IS THE PLAN COMMITTING ITS OWN SUBJECT (PR-004), which is worth recording for the irony as much
as the impact: it cites the maintainer ruling at
`.aw/records/backlog/open/20260928-pn7rw3-...`, and the item now lives under `graduated/` (it moved when
this plan graduated it). The ruling text itself verifies verbatim at the new path, so no reasoning changes,
but a plan about dangling citations should not carry one.

ONE PRE-EXISTING RECORD DEFECT SURFACED AND WAS FIXED (PR-006), the same one this sweep found on `szkgb8`:
the two same-date history records were ordered `draft` then `to-review` descending the file, which a
newest-first reader derives as a backwards `to-review -> draft` transition, so `aw check plans` reported
`check.lifecycle-transition-invalid`. Confirmed on the PRE-REVIEW lane input that it predates this review;
adding a correctly-placed `reviewed` record is what made the date group classifiable and surfaced it.
Reordering clears it with no content change.

I CHECKED THREE THINGS THE PLAN DOES NOT CLAIM, all clean. The `xvp5vx` and `p5qx91` carriers both resolve
to real backlog records (`graduated`, each `Graduated-To` itself). `should_color` is NOT in
`agent_workflows/__init__.py`, so the Spec/documentation-sync claim that the edited docstring is "an
internal implementation note on a module that is not in the package's public re-export set" is accurate.
And spec `uonrjg` R9.3a.2 genuinely exists and genuinely concerns the depth resolver, so the plan's
statement that it corrects claims about which TESTS enforce it rather than the requirement itself is right,
and declaring no `.spec.md` is correct.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G (executability) / C | `.aw/records/plans/pending/20260929-qdro85-01-ery0ia-...ipd.md` `- Status: approved` (its history shows `- 2026-09-30 approved` above `- 2026-09-30 reviewed`); block boundary at `tests/test_runner_shared.py:313` (false claim) and `:353` (`SUPERSEDED_SINCE_MOVE = (`) | **THE CONCURRENT PLAN THIS ONE IS SEQUENCED AROUND HAS ADVANCED FROM `reviewed` TO `approved`, SO E-03'S DELETION BRANCH IS NOW THE LIKELY PATH RATHER THAN THE EXCEPTION.** The plan's Step 0 and authoring history both describe `ery0ia` as `Status: reviewed`; it is now cleared to execute and a runner may dispatch it first or alongside. Nothing in the plan's design breaks (E-03 is deliberately idempotent and V-03 carries route (b)), but an executor reading "if `ery0ia` landed first" as a remote contingency may treat a near-certain no-op as a missing subject. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 0 now records the `approved` status with the measured block boundary, states that the deletion branch is EXPECTED, and confirms the two plans cannot collide on the production file (`ery0ia` declares `tests/test_runner_shared.py` alone; E-04's subject is `agent_workflows/runner_shared.py`). Added the verified fact that `ery0ia`'s own F-09 deletes the `OneOriginatingDefinitionTests` and `test_exactly_one_definition_package_wide` pointers by symbol, so E-03's intent is fully satisfied under that branch. New F-10; the authoring history carries a dated inline correction rather than a rewrite. |
| PR-002 | MEDIUM | IN-SCOPE | E (verification) | Measured at review HEAD `3b39f14ef`: bare `python3 -m pytest` -> `3523 passed, 2 skipped`; `tests/test_runner_shared.py -o addopts=""` -> `126 passed`; `tests/test_term.py -o addopts=""` -> `28 passed`, against the plan's recorded `3387` / `119` / `28` | **TWO OF E-02'S THREE BASELINES HAVE DRIFTED, AND V-04 TREATS A MOVED COUNT AS A FAILURE,** so an executor comparing against the printed figures would stop on a legitimate unrelated difference. The suite moved +136 and the per-file +7 between authoring HEAD `6992d396` and review HEAD. The plan's design is already correct (E-02 re-derives at execution), but the V-items' "equals V-02's baseline" sat beside displayed numbers, and V-04 says a moved count "is a FAILURE of this V-item, not a note". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now states plainly that the authoring AND review numbers are CONTEXT, not an acceptance bar, records both sets with their HEADs, and says the bar is the executor's own pre-edit measurement. V-02 says the same; V-03 and V-04 now compare against "V-02's OWN recorded" count. New F-11. |
| PR-003 | MEDIUM | IN-SCOPE | E / G | V-03 and V-04 as authored; PR-001's finding that `ery0ia` may now land mid-execution | **NO RULE EXISTED FOR ATTRIBUTING A COUNT CHANGE CAUSED BY A NEIGHBOUR LANDING MID-EXECUTION,** which PR-001 makes a live possibility rather than a theoretical one. `ery0ia` deletes module-level assignments from `tests/test_runner_shared.py`; if it lands between V-02 and V-03/V-04 the per-file count legitimately changes, and the plan offered the executor only "equals V-02's baseline" (which would fail) with no way to distinguish a neighbour's change from a real regression this plan caused. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 adds a route-(b)-only allowance requiring the landing commit be NAMED and the difference attributed to it, then re-baselined. V-04 adds the same exception with the requirement to re-run the baseline AT that commit before comparing, so a neighbour's change is neither blamed on this plan nor allowed to mask a real regression. Both state it must be evidenced rather than assumed. |
| PR-004 | LOW | IN-SCOPE | A (correctness of the record) / F | `grep -rln "^- Id: pn7rw3" .aw/records/backlog/` resolves to `.aw/records/backlog/graduated/20260928-pn7rw3-...`, `- Status: graduated`; the plan cites `.aw/records/backlog/open/20260928-pn7rw3-...` | **THE PLAN CITES ITS OWN BACKLOG ITEM AT A PATH THAT NO LONGER EXISTS, which is the exact class of defect it was written to fix.** The item moved from `open/` to `graduated/` when this plan graduated it. The quoted maintainer ruling verifies VERBATIM at the new path, so no reasoning is affected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 0's citation corrected to the `graduated/` path, with a parenthetical recording that the item moved and that the authoring text cited the pre-move location. New F-12. |
| PR-005 | LOW | IN-SCOPE | G (execution contract) | Plan `## Approval and execution gate` as authored | **THE EXECUTION CONTRACT WAS MISSING THE HONESTY RULE, SCOPE RECONCILIATION, AND CONDITIONAL TRANSITION OWNERSHIP.** It correctly stated path-scoped commit, never-push, never-`--no-verify`, staged-set verification, and a legitimate concurrent-edit STOP (which the 2026-09-01 ruling preserves as a different case). It did not carry the hard-MUST "paste the ACTUAL output" rule, said nothing about what to do when an out-of-scope edit is necessary, and instructed the executor to "move this plan to `executed/`" unconditionally, which is wrong when a runner dispatched it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now carries the paste-the-actual-output rule (pointed at this plan's own subject: prose nobody checked), states the fence as a declaration reconciled with `--scope-reason`/`--scope-ack` (naming `tests/test_runner_shared.py` as the likely ack under E-03's deletion branch), keeps the genuine concurrent-edit STOP, and states the conditional transition ownership (runner finalizes when it dispatched; executor runs `aw ipd finalize` otherwise). |

| PR-006 | LOW | IN-SCOPE | A (record correctness) | `ipd_lifecycle._plan_status_event_groups` on the plan text; `check_engine.check_lifecycle_transitions`; `check.lifecycle-transition-invalid` | **THE TWO SAME-DATE HISTORY RECORDS WERE IN THE WRONG RELATIVE ORDER FOR A NEWEST-FIRST HISTORY,** so `aw check plans` reported `check.lifecycle-transition-invalid` against this plan. Authored `draft` then `to-review` descending the file, which a newest-first reader derives as the backwards transition `to-review -> draft`: `validate_transition` returns `ok=False, reason="missing predecessor: backwards transition 'to-review' -> 'draft'"`. Verified on the PRE-REVIEW lane input, so it is the plan's own latent defect and not introduced here; adding a correctly-placed `reviewed` record is what made the date group classifiable and surfaced it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reordered the two 2026-09-30 records so the history reads newest-first throughout (`reviewed`, `to-review`, `draft`). `_plan_status_event_groups` now yields `('2026-09-30', [('draft',...), ('to-review',...)], True)` and `('2026-10-01', [('reviewed',...)], True)`, and `aw check plans` reports zero findings naming `x3zno3` (was 1). No history CONTENT was altered, only the order of two records within one date. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | `ery0ia` is now `approved` and will likely delete E-03's entire subject. Should E-03 be removed, or the plan re-scoped to the production file alone? | KEEP E-03 as an idempotent item and record the raised likelihood. | (a) Delete E-03 and declare only `agent_workflows/runner_shared.py`: REJECTED, `ery0ia` is approved but NOT executed, so removing E-03 would leave the test-side defect uncovered if that plan is retired, deferred, or narrowed; the idempotent form costs one near-certain no-op and covers both futures. (b) Add an `Item-Dependencies` edge on `ery0ia`: REJECTED, it would BLOCK this plan on a plan that does not need to run first (E-04 is wholly independent) and would strand the production fix behind an unrelated queue position. (c) Re-scope `ery0ia` to also fix the production docstring: REJECTED, not this reviewer's plan to re-scope, and that plan declares one path deliberately. | `ery0ia` `- Status: approved` with `- Scope-Paths: tests/test_runner_shared.py` only; its F-06 explicitly declines to close `pn7rw3`; its Deferred routes production-file citations "Carrier: pn7rw3"; E-04's subject is a different file so no ordering constraint exists. | yes |
| D-2 | Two of E-02's baselines drifted. Update the recorded numbers, or change what the numbers mean? | Change what they MEAN: record both sets as context and make the bar the executor's own measurement. | (a) Just update `3387` -> `3523` and `119` -> `126`: REJECTED, it fixes today and re-rots tomorrow, since the suite is under active concurrent development and drifted +136 in three days; the plan would need re-review on every landing. (b) Delete the numbers entirely: REJECTED, they are useful calibration (an executor seeing 300 passed knows something is wrong) and the live-artifact convention asks for context in prose, not for silence. | The rubric's live-artifact re-derivation convention (a count of a drifting population states the property and re-derives at execution; a measured figure belongs in prose as context, never as the bar). E-02 already re-derived correctly; only the V-items' comparison target needed stating. | yes |
| D-3 | Verdict and readiness, given five findings all fixed, none BLOCKER or HIGH, and one resolved non-blocking open question. | `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval`. | `APPROVE` with no revisions: REJECTED, five findings required in-place edits. `REVIEWED - OPEN QUESTIONS`: REJECTED, OQ-01 is `resolved` and correctly so (the maintainer ruling recorded on the item answers it, so referring it upward would be asking a human what the repository already decided). Bare `NO-GO`: REJECTED, the workflow reserves it for genuine not-ready conditions and says a reviewed clean plan awaiting sign-off is `GO - PENDING HUMAN APPROVAL`. | Workflow readiness vocabulary; zero findings left OPEN or DEFERRED at or above the `high` gate threshold, so no escalation to a `Blocking: yes` question is owed; `aw ipd lint` clean at `author` and `review-finalize`; `aw check plans` reports no finding naming `x3zno3`. | yes |
