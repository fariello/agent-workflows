# Review findings: plan 04vf1h

- Subject-Id: 04vf1h
- Subject-Type: ipd
- Reviewed-At: 2026-09-22
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5b29bfa0` in an isolated review lane. The plan was committed and unmodified, so no
pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0) before revision; `--phase review-finalize` CONFORMED after. `aw check` was run as well, and it
caught two error-severity findings the IPD linter does not see (PR-007, PR-008 below).

THE PLAN'S PREMISE IS SOUND AND IT VERIFIES END TO END, which is worth stating first because the rest of
this round is findings. The parent `a5wdne` does carry its six-criterion acceptance check as its ONLY
`E-*` item; its own E-01 text does record the retirement hazard verbatim as quoted; the retirement path
is real (`runner_shared` calls `ipd_lifecycle.retire_orchestrator`, `ipd_lifecycle.py:3333`); the three
children `li44r9`/`nmlx47`/`xdvglg` are all `approved` with `Item-Dependencies` forming the chain the
plan declares; and the parent's child table ALREADY carries the Order-04 row pointing at this file, so
the coverage gap this child closes is genuine and the fix is correctly shaped. A plan whose entire
product is a verification is also the right response to an orchestrator coverage refusal.

EVERY FINDING IS ONE CLASS OF DEFECT, and naming the class matters more than the six instances: the plan
inherited the PARENT'S DATED MEASUREMENTS as if they were constants. Because it is a verifier, each
stale constant would have produced a FALSE NEGATIVE - reporting a correctly-executed Set as incomplete -
which is the more damaging direction for this plan specifically. The plan's own honesty rule anticipated
only over-credulity (improvising a scan, accepting a vacuous guard) and had no counterpart for
over-strictness; that asymmetry is now stated in the gate.

MEASUREMENTS TAKEN THIS ROUND, all with the repository's OWN `_is_pure_delegation` predicate from
`tests/test_rununify_execute_item.py` rather than a private definition of "forked":

```text
84f140da (parent's review HEAD): co-defined=55 wrappers=21 forks=34 identical=16 divergent=18
5b29bfa0 (this review HEAD):    co-defined=58 wrappers=22 forks=36 identical=18 divergent=18
large still counted as forked, BOTH commits: build_parser, execute_item, initialize_run, main, run_queue
```

So the `34` baseline the plan pins drifted to 36 while the Set sat unexecuted (PR-001). And the 5-or-3
ambiguity resolves in an instructive way (PR-002): `initialize_run` and `execute_item` DO delegate to
`runner_shared.initialize_run_core` / `execute_item_core` exactly as the parent's Deferred section says,
yet each host copy holds THREE statements (host options plus two spawn closures), so neither matches the
one-statement wrapper shape the pin predicate recognizes and both still register as forks. Both of the
parent's contradictory readings are therefore accurate descriptions of different things, which is why the
fix is to report residuals BY NAME with a per-symbol classification rather than to pick a number.

THE VACUOUS GUARD IS STILL VACUOUS AT THIS HEAD, re-measured rather than taken from the parent:
`agy_runipd.py` contains 9 lines spelled `from agent_workflows.oc_runipd import`, while the guard row in
`test_review_findings_cascade.py` forbids only the substring `"import oc_runipd"` and passes. That gives
PR-006 its bite: a falsifiability demonstration written in the `import oc_runipd` spelling would be
rejected even by the vacuous guard and would prove nothing, so the spelling must be specified.

THE SUITE IS NOT GREEN AND WAS NEVER REQUIRED TO BE (PR-005). Bare run in this lane:

```text
2 failed, 8521 passed, 3 skipped, 2 xfailed, 3 warnings in 114.07s (0:01:54)
FAILED tests/test_orchestrator_retirement.py::RealRepositorySets::test_every_live_set_reaches_its_measured_verdict_for_its_measured_reason
FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
```

Both are unrelated to this Set. The `test_turn_bounds` failure is purely environmental - the ambient
`OPENCODE_CONFIG_CONTENT` leaks into the environment the test inspects, and the same file is `76 passed`
under `env -u OPENCODE_CONFIG_CONTENT`. The `RealRepositorySets` failure is corpus drift on the unrelated
`commitguard` Set, whose child `y9vpvv` reached `executed`; that test's own message instructs a reader to
re-measure and re-point the row and "NEVER to loosen the assertion". The parent's sixth criterion is
explicitly "NO NEW failures against a baseline taken THE SAME WAY ... never an absolute count", so the
plan's demand for a bare green suite was STRICTER THAN THE CRITERION IT CLAIMS TO VERIFY, and would have
failed the Set for two conditions no child caused.

TWO CRITERIA WERE ALSO OVER-DEMANDED AGAINST THE CHILDREN'S OWN APPROVED BARS (PR-003, PR-004). Order
03's V-03 states "A DOCUMENTED WALL SATISFIES THIS ITEM; a completed end-to-end execution is not
required", so demanding a completed third-host run here would make this item unsatisfiable by a correctly
executed Order 03. And Order 03's V-02 pins the pre-cutover evidence to the TRACKED fixtures in
`tests/test_run_analytics_sources.py`, stating that `.aw/records/runs/` is gitignored and absent from
every lane - confirmed: `.aw/.gitignore` ignores `records/runs/` and the directory is empty here. A
verifier hunting a run directory would have reported a gap that is a design property.

TWO DETERMINISTIC REPOSITORY ERRORS WERE ALSO CARRIED, both pre-existing and both invisible to the IPD
linter, which is why running `aw check` beside `aw ipd lint` mattered here (PR-007, PR-008). The plan's
`## Workflow history` had `draft` printed ABOVE `to-review` in a section that is newest-first, so the
derived event stream read as a backwards transition and `check.lifecycle-transition-invalid` fired at
`error`; reproduced independently with `ipd_lifecycle.validate_transition`, which returns "missing
predecessor: backwards transition 'to-review' -> 'draft'". And all three `## Deferred / out of scope` rows
named no durable carrier, so `check.ipd-uncarried-obligation` fired at `error` with the consequence stated
plainly in its own detail text: once the plan reaches `executed` those obligations class `done` in `aw
attention` and vanish with no record. Both were confirmed pre-existing by re-running `aw check` against the
pre-review commit and getting the same count for this plan. After the fixes, `aw check` reports ZERO
findings for this plan and the tree total fell 63 -> 61.

NOT FLAGGED, checked and correct: the plan claims no `Blocks-Release` and none is owed (its siblings
carry none and its work-kind is verification, not a bug); `Scope-Paths: .aw/records/plans/pending` is
right for a plan that writes only its own record and must author no code; the `Item-Dependencies` chain
matches the parent's child table; the gate already carried a scope fence in the DECLARATION form rather
than the forbidden "STOP and report" form; and the execution checklist and validation checklist were
already a clean 1:1 bijection with concrete per-item evidence demands, which is why no E-item was added
or split. Right-sizing: three E-items, each one concern and one focused pass; no split warranted.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / E. Verification | `.aw/records/plans/pending/20260921-hostdedup-04-04vf1h-verify-the-hostdedup-set-against-all-six-completion-criteria.ipd.md:35` ("against the 34-symbol baseline"); measured `84f140da` 34 forks vs `5b29bfa0` 36 forks with `tests/test_rununify_execute_item.py:104` `_is_pure_delegation` | The fork-count baseline is pinned to a DATED measurement that has already drifted 34 -> 36 while the Set sat unexecuted. An execution comparing its post-state against the remembered `34` measures against a tree that no longer exists, so the headline number would be wrong in the exact way the criterion exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires the pre-state RE-DERIVED with the same committed scanner at a named commit, both counts pasted, and the drift from `34` stated explicitly as a reportable fact. V-01 fails an execution that compares against the remembered figure. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness / G. Executability | `a5wdne` Completion criteria ("to the five large functions alone") vs `a5wdne` Deferred ("only 3 of the 5 ... remain forked"); measured: `initialize_run`/`execute_item` delegate to `runner_shared.*_core` yet hold 3 statements each and still count as forks | The residual target is ambiguous between 5 and 3, with BOTH readings present in the parent, and measurement shows both are simultaneously true for different reasons. A verifier reporting either bare number can be contradicted by the other reading, and neither tells a reader what is actually left forked. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now reports residuals BY NAME with each classified full fork / shared-core delegation / sanctioned wrapper; V-01 fails a bare count. Recorded as OQ-02 (decision D-1). |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing and verification | plan `:45` (property (a) demands "a third host completes a real IPD execution") vs `xdvglg` V-03 "A DOCUMENTED WALL SATISFIES THIS ITEM; a completed end-to-end execution is not required" | Property (a) over-demands against the child's OWN approved acceptance bar, making this item unsatisfiable by a correctly-executed Order 03 and converting a sanctioned outcome into a Set failure. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 and V-03 now accept the documented wall with its predicted-wall classification, while still failing a Set that produced NEITHER a run record nor a wall. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing and verification | plan `:47` ("the pre-cutover record named") vs `xdvglg` V-02 (tracked fixtures at `tests/test_run_analytics_sources.py`, "NOT from `.aw/records/runs/` which is gitignored and absent from every lane"); confirmed `.aw/.gitignore:14` `records/runs/` and the directory empty in this lane | The pre-cutover evidence source is unstated, so a verifier would look in `.aw/records/runs/`, find it absent by design in every lane, and report a gap that is a design property rather than a defect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now names the TRACKED fixture as the source per Order 03's V-02 and states that the run directory's absence is not evidence of anything. |
| PR-005 | HIGH | IN-SCOPE | D. Anti-regression / E. Verification | plan `:45,:93` ("paste a bare `python3 -m pytest`", "show the tree is green") vs `a5wdne` Completion criteria ("NO NEW failures against a baseline taken THE SAME WAY ... never an absolute count"); measured `2 failed, 8521 passed`, `tests/test_turn_bounds.py` `76 passed` under `env -u OPENCODE_CONFIG_CONTENT` | The suite criterion is written as an absolute green, which is STRICTER than the parent criterion it claims to verify and is unreachable: two failures exist at HEAD, one an ambient env leak and one unrelated `commitguard` corpus drift. As written this fails the Set for conditions no child caused, and invites an executor to "fix" an unrelated real-repository assertion its own message forbids loosening. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now requires the invocation form plus per-failure classification (pre-existing vs attributable) with like-for-like evidence; the Required tests section documents both current failures and their causes; the scope fence now forbids editing either test. Recorded as OQ-03 (decision D-2). |
| PR-007 | HIGH | IN-SCOPE | G. Executability / project lifecycle rules | `aw check` rule `check.lifecycle-transition-invalid` (severity `error`, deterministic, catalog I-03, `agent_workflows/check_engine.py:374`); reproduced directly with `ipd_lifecycle.validate_transition`, which returns `ok=False` "missing predecessor: backwards transition 'to-review' -> 'draft'" | The `## Workflow history` lines were in the WRONG ORDER for a newest-first section: the `2026-09-21 draft` line sat ABOVE the `2026-09-21 to-review` line, so `check_lifecycle_transitions` derived a backwards transition and the plan carried a deterministic error-severity repository finding. Pre-existing, not introduced by this review (verified by re-running `aw check` against the pre-review commit: identical finding count for this plan). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reordered the two 2026-09-21 history lines. Re-verified with `ipd_lifecycle.validate_transition`: `draft -> to-review` and `to-review -> reviewed` both `ok=True`. |
| PR-008 | HIGH | UNDER-SCOPE | C. Architecture and operability / project lifecycle rules | `aw check` rule `check.ipd-uncarried-obligation` (severity `error` post-cutover, `agent_workflows/check_engine.py:468`), detail "3 obligation(s) name no durable carrier ... once this plan reaches `executed` it classes `done` in `aw attention` and this vanishes with no record" | All three `## Deferred / out of scope` rows named no durable carrier, so the Set's remaining obligations would have silently disappeared from the attention view when this plan finalized. Each row is in fact a handoff to a named sibling rather than genuine new debt, so the obligation was real but trivially dischargeable. Pre-existing. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added `- Carrier: li44r9` to the lifting/unifying row and to the committing-the-scanner row (both are Order 01 deliverables), and `- Carrier: xdvglg` to the re-performing-child-validation row (Order 03 owns that evidence). `aw check` now reports ZERO findings for this plan, and the tree total fell 63 -> 61. |
| PR-006 | MEDIUM | IN-SCOPE | B. Security lens / E. Verification | plan `:40` (reintroduce "a coupling"); measured: 9 `from agent_workflows.oc_runipd import` lines in `agy_runipd.py` while the guard row in `tests/test_review_findings_cascade.py:713` forbids only `"import oc_runipd"` | The falsifiability demonstration does not say WHICH import spelling to reintroduce, and the choice decides whether the proof means anything: the vacuous guard already rejects `import oc_runipd`, so a demonstration in that spelling would pass while proving nothing about the coupling class. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now mandates the `from agent_workflows.oc_runipd import` form, requires both spellings COUNTED beside the green run, and requires the scratch copy to live outside the tracked tree so the scope fence is not breached. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Is the Set's residual target five forked large functions or three? | Neither: report the residual set BY NAME with a per-symbol classification, because both figures are defensible and neither is informative. | (a) Pick `5`, per the parent's Completion criteria - rejected: contradicted by the parent's own Deferred section and by the two unified `*_core` symbols. (b) Pick `3`, per the parent's Deferred section - rejected: measurement shows `initialize_run`/`execute_item` still count as forks under the repository's own pin predicate, so `3` would be contradicted by any scanner using that predicate. (c) Ask the maintainer - rejected: the repository answers it, and the answer is that the question is mis-posed. | `a5wdne` Completion criteria vs its Deferred section; measured with `tests/test_rununify_execute_item.py:104` `_is_pure_delegation` at HEAD `5b29bfa0` | yes |
| D-2 | The suite is not green at review HEAD. Should this plan report that as the Set failing? | No: classify each failure pre-existing or attributable, per the parent's actual stated gate. | (a) Keep the bare-green demand - rejected: unreachable at HEAD and stricter than the criterion being verified, so it would fail a correct Set. (b) Pin the exact current failure list as an accepted baseline - rejected: it would go stale exactly as the `34` did (PR-001), reproducing the defect one line below its own fix. (c) Have the executor fix the two failures - rejected: out-of-scope product/test edits, and `RealRepositorySets` explicitly forbids loosening its assertion. | `a5wdne` Completion criteria ("no NEW failures against a baseline taken the same way, never an absolute count"); measured bare run `2 failed, 8521 passed` and `tests/test_turn_bounds.py` `76 passed` under `env -u OPENCODE_CONFIG_CONTENT` | yes |
