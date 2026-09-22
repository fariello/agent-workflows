# Review findings: plan n9na1c

- Subject-Id: n9na1c
- Subject-Type: ipd
- Reviewed-At: 2026-09-22
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `25842592` in an isolated review lane. The target plan was committed and byte-identical
to the driver's staged input (`md5sum` matched), so the pre-review snapshot was correctly skipped per
Step 1. Structural preflight `aw ipd lint --phase author --agent` reported `conforming` before review
and `--phase review-finalize --agent` reported `conforming` after the revisions.

THE DEFECT IS REAL AND THE PRIMARY EVIDENCE REPRODUCES, which matters to establish first because almost
everything below is about how the proposed fix goes wrong rather than whether a fix is needed. I read the
cited run record through the repository's own `attention._resolve_runs_repo_root` rather than trusting the
prose. `ld8lb3` carries `integration_gate_answer` with `answer: not-mine`, `usable: True`, `asked: True`,
`ask_reason: "the driver-run suite refused integration and the turn's session is resumable"`, and a
one-element `failing_tests` set; its `integration_released_by_answer` is `not-mine`; its
`attempts[0]["finalized"]` is `True`; and its `post_merge_revalidation` then reports `passed: False` with
`measured: True` on a failing set BYTE-IDENTICAL to that one attributed id, while the passing count rose
from `8063` to `8064`. Final status `merge-refused`. So F-1 through F-4 and F-6 all hold, the release was
honored at gate 1 exactly as documented, and gate 2 re-litigated it having never seen the answer.

THE PLAN'S SECOND MEASURED CLAIM IS FALSE, AND IT WAS DRIVING AN E-ITEM AND A SCOPE WIDENING. The plan
asserts that `65cuw0` "hit the SAME combined-red refusal in the same run with `integration_gate_answer`
equal to `null`, meaning it was never asked at all", concludes "the ask is not reliably reached", and
builds E-02 (investigate) plus half of E-04 (fix it) plus a `Scope-Paths` contingency on that. Measured:
`65cuw0`'s `suite_check` is `passing: True`, `exit_code: 0`, `failures: []`, summary
`8118 passed, 3 skipped, 2 xfailed`, and its `integration_signal` is `driver-run-suite`
(`INTEGRATION_EARNED_BY_SUITE`), not `suite-failed`. I then called the real predicate with exactly those
recorded values and it returned `(False, 'integration was earned; there is nothing to answer')`. The item
was not asked because NOTHING FAILED at gate 1. A `null` answer record is the correct record for it, the
two items did not share a gate-1 refusal at all, and there is no ask-reachability defect to fix. Left
standing, E-02 would have sent an executor to find the cause of a non-defect and E-04 would have
"fixed" a predicate that is already right.

What `65cuw0` actually demonstrates is worse for this plan than the false claim was: an item can reach
gate 2 having never been asked, so it carries no answer and no attributed set, and this plan's channel
does nothing for it. This plan therefore rescues exactly ONE of the two measured stranded lanes. That is
recorded as F-11 and is why sibling `tgyfs2` carries `Priority: high` while this one carries `medium`.

THE DOMINANT FINDING IS THAT THE PROPOSED COMPARISON FAILS OPEN BY THREE INDEPENDENT ROUTES, all three
measured at review rather than reasoned about. This is the same comparison sibling `tgyfs2` proposes, but
the direction of its errors is reversed and that reversal is the whole point: in `tgyfs2` an unsound
subtraction causes OVER-refusal, which is today's behavior and recoverable by hand, whereas here it
licenses a PASS and merges work nothing cleared.

Route one is the `32ij2j` inversion, which `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`
exists for and describes in terms: that plan "compared failing SETS as a subset and derived them from an
always-empty string, so every lane passed including one that broke everything", and the always-empty read
was ALREADY SHIPPED in `run_suite_check` until `h5pyqa` repaired it. Measured here: a genuinely red
post-merge run whose text yields no parseable ids gives `extract_suite_failures(...) == ()`, so E-04's
authored rule ("a merged-tree red consisting ONLY of attributed-away ids passes") is VACUOUSLY TRUE and
the tree integrates.

Route two is the truncation cap, and it needs no extractor bug at all. `extract_suite_failures` stops at
`SUITE_FAILURE_LINE_LIMIT` (40) in first-seen order. Measured: 45 attributed pre-existing failures plus
ONE genuine lane regression both cap at 40, the regression is TRUNCATED OUT of the merged list before the
comparison ever sees it, the subtraction finds nothing new, and a lane that introduced a failure passes.
The same cap in `tgyfs2` fabricates 20 falsely-new ids and over-refuses; here it hides a real regression.

Route three is the answer token. Measured by driving `perform_gate_answer` with a `fixed` answer and a
passing re-run: the outcome carries `release: True` AND a NON-EMPTY `failing_tests` set holding the
PRE-REPAIR failures. So a reader keyed on "is there an attributed set" rather than on "is the answer
`not-mine`" would clear exactly the ids whose repair did not survive the merge. E-03 as authored said
"reuse the answer record already persisted under `GATE_ANSWER_RECORD_KEY`" and named no token check.

E-03 ALSO PROPOSED BUILDING A CHANNEL THAT ALREADY EXISTS. `execute_item_core` writes BOTH
`attempt[GATE_ANSWER_RECORD_KEY]` and `item[GATE_ANSWER_RECORD_KEY]`, strictly BEFORE the integration
block constructs `val_runner`, and `gate_answer_record` already persists the id set as `failing_tests`
(verified by driving the real function and reading the record back). So the item is a READER plus a
NORMALIZER, not a write, and saying so removes the temptation to mint a second key for the same ids,
which is the producer/reader drift this module's own comments cite twice.

A SPEC AMENDMENT IS REQUIRED AND THE PLAN SAID NONE WAS. Spec `25kzda` Section 5.1 defines the one narrow
attribution exception and states that "The merge-and-revalidate gate, the scope fence, the commit-content
and hook checks, and the dependency checks are likewise untouched" and that the exception "adds an
ATTRIBUTED, REVIEWABLE input to one integration decision; it removes no gate". This plan makes that answer
govern a SECOND decision at the gate the spec names as untouched. The spec is `Status: approved`, so
shipping the code without amending it would leave the approved contract asserting the opposite of the
runner's behavior. `runner_shared`'s own baseline comment block anticipates this shape exactly ("would
REQUIRE amending spec `25kzda` because it would change the AUTHORITY under which a red suite may be
cleared"). The spec path is now declared in `Scope-Paths` and new E-06 owns the amendment.

TWO MECHANICAL FINDINGS ABOUT WHERE THE CHANGE LANDS. Both hosts' `validation_runner_for` lambdas pass
`dict(item)`, a SHALLOW copy, so on the deferral re-attempt path a READ of the answer record works while
any WRITE is lost; E-04 must depend only on the read, which is now stated and settled as OQ-04. And the
revalidation cache is keyed on the merged TREE and serves `{passed, reason, measured}` wholesale, so an
answer-relative verdict can be served to an item that answered differently or not at all; that is the
identical trap `tgyfs2` raised as its own OQ-03, and this plan now resolves it the same way so the two
siblings cannot disagree about what the cache means.

SEQUENCING WAS UNDECLARED BETWEEN TWO PLANS EDITING THE SAME FUNCTION. Both this plan and `tgyfs2` modify
the measured-red verdict inside `make_integration_validation_runner._runner`, both declared
`Item-Dependencies: none`, and `tgyfs2` is already `reviewed` with `Readiness: go-pending-approval`. The
runner sorts by dependency DEPTH and re-checks edges at dispatch, so with no edge either order was
possible and the second to land would rebase onto a function its author never read. `Item-Dependencies:
executed:tgyfs2` is now declared (edge grammar verified against `ipd_schema.parse_item_dependencies`,
which accepts `executed:` and rejects `ipd:`), and new E-07 owns the composition proof.

VERIFIED TRUE AND LEFT STANDING: F-1, F-2, F-3, F-4 and F-6 as written; OQ-01's resolution to use the ids
the agent was SHOWN rather than ids parsed from prose, which is the right discipline and is what makes the
scope of an answer auditable; OQ-02's refuse-and-name-only-the-new-id answer; the deferral of `fuk1mr` and
`iv4n2c`; the observation that `record_refusal` is the one refusal writer so no new renderer is needed; and
V-04's replay, which I confirmed is achievable as written (`resolve_lane_endpoints` returns base
`301a1d8fbc15` and branch `aw/lane/ld8lb3`, the branch still exists at `78891bde`, and
`git merge-tree --write-tree` produces tree `9ec0a5be8e52`, identical both to the lane head tree and to the
`tree` recorded in the item's `post_merge_revalidation`).

ONE FINDING WAS FOUND BY RUNNING THE REPOSITORY'S OWN CHECKER rather than by reading. `aw check` reported
`check.ipd-uncarried-obligation` at ERROR severity against this plan: its `- Date: 2026-09-22` is after
`CARRIER_CUTOVER_DATE`, so all six `## Deferred / out of scope` rows required a typed carrier and none had
one. Verified pre-existing rather than caused by my edits by stashing them and re-running. Every sibling
plan reviewed this week carries these fields, so this was a conformance gap and not a judgement call.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | B. Security-adjacent (a safety gate made permissive) / D. Anti-regression | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` and its docstring on plan `32ij2j`; the shipped `h5pyqa` always-empty read in `run_suite_check`; measured at review: `extract_suite_failures('') == ()`, so with one attributed id the "only attributed ids" test is vacuously true | THE AUTHORED RELEASE RULE IS THE COMPARISON THAT ALREADY INVERTED THIS GATE ONCE. E-04 said a merged-tree red consisting ONLY of attributed-away ids passes. An empty merged failing list satisfies that trivially, and an empty list on a genuinely red run is not hypothetical: it is the exact defect class shipped in `run_suite_check` until `h5pyqa`. A tree that broke everything would integrate. | C:Low; U:Low; S:High (this gate is the last thing between uncleared work and main); F:High; Overall:Low to fix, being one guard clause in a predicate the plan is already writing | FIXED | E-02(a) now states the rule in-code citing `32ij2j`; E-04 requires an EMPTY merged list on a non-passing suite to REFUSE; E-05 pins it as one of the three measured-reachable controls; V-04 and V-05 require the case pasted; recorded as F-7 and in the gate's hazard paragraph |
| PR-002 | BLOCKER | IN-SCOPE | A. Correctness (an unsound comparison that fails OPEN) | `oc_runipd.SUITE_FAILURE_LINE_LIMIT = 40` and `extract_suite_failures`' early `return tuple(seen)`; `pyproject.toml` `addopts = "-q -n auto --dist=worksteal ..."`; measured at review: 45 attributed failures + 1 genuine regression both cap at 40, `any('REGRESSION' in m for m in merged)` is False, subtraction yields `[]` | THE 40-LINE CAP HIDES A GENUINE REGRESSION AND PASSES THE LANE. The extractor truncates in first-seen order, so a badly-red tree can truncate the lane's own new failure out of the merged list entirely; the subtraction then finds nothing new and releases. Note the sign: the same cap in sibling `tgyfs2` causes over-refusal and is merely unreliable, while here it is a safety hole, because this plan's comparison licenses a pass. The plan treated both lists as complete sets and never mentioned the cap. | C:Low; U:Low; S:High; F:High; Overall:Low - a length check | FIXED | E-02(b) records the measurement; E-04 refuses when either list is at the cap, detected by length and never by parsing prose; E-05 requires a constructed 45+1 fixture; recorded as F-8 and as a conventions bullet |
| PR-003 | BLOCKER | IN-SCOPE | A. Correctness / B. Security-adjacent | measured at review by driving `perform_gate_answer` with `{'answer':'fixed'}` and a passing re-run: `release: True` with `failing_tests` holding the PRE-REPAIR ids; `GateAnswerVerdict.integrates` is True only for `not-mine` while `failing_tests` is populated for every answer | AN ANSWER-AGNOSTIC READ OF THE ID SET CLEARS THE WRONG FAILURES. E-03 said only "reuse the answer record" and named no token check, but the set is populated for `fixed`, `mine` and `needs-human` too (it is what the agent was shown). A `fixed` answer therefore carries a non-empty set AND a release, so reading the set without the token would clear exactly the ids whose repair did not survive the merge - a claim substituting for a measurement, which is what `fixed`'s re-run rule exists to prevent. | C:Low; U:Low; S:High; F:High; Overall:Low - one token comparison | FIXED | E-02(c) states the rule; E-03 requires `answer == not-mine` AND `usable`, returning an EMPTY set for every other token and for absent/unusable; E-05 adds `fixed` as a seventh control; V-03 requires all five answer shapes pasted; recorded as F-9 |
| PR-004 | HIGH | OVER-SCOPE | G. Plan executability (an E-item built on a false premise) | `65cuw0`'s `suite_check`: `passing: True`, `exit_code: 0`, `failures: []`, `8118 passed`; `integration_signal: driver-run-suite`; `gate_answer_is_warranted(integration_gate_relevant=True, earned=True, integration_signal=INTEGRATION_EARNED_BY_SUITE, session_id=...)` returns `(False, 'integration was earned; there is nothing to answer')` | THE ASK-REACHABILITY DEFECT DOES NOT EXIST. The Concern claimed `65cuw0` hit the same refusal and was never asked, and built E-02 plus half of E-04 plus a `Scope-Paths` contingency on it. Measured, `65cuw0` EARNED integration at gate 1 with a green suite, so there was nothing to ask about and a `null` answer record is correct. Left standing, an executor would investigate a non-defect and then "fix" a predicate that is already right - and might loosen it. | C:Low; U:Low; S:Medium (loosening the ask predicate would ask the judged agent about verdicts it must not answer); F:Low; Overall:Low | FIXED | Concern retracts the claim with the measured values; F-5 rewritten as an explicit retraction; E-02 repurposed to the three guard rules; E-04's reachability clause removed; the Scope check contingency removed; recorded as an explicit exclusion with a `Carrier-Declined` reason; F-11 records the consequence that this plan rescues one of the two stranded lanes |
| PR-005 | HIGH | UNDER-SCOPE | C. Architecture / specification synchronization | spec `25kzda` Section 5.1: "The merge-and-revalidate gate, the scope fence, the commit-content and hook checks, and the dependency checks are likewise untouched" and "it removes no gate"; spec `- Status: approved`; `runner_shared`'s baseline block: a comparison changing an outcome "would REQUIRE amending spec `25kzda`" | THE PLAN DECLARED NO SPEC AMENDMENT WHILE CHANGING THE CONTRACT A SPEC STATES. The attribution exception is specified as governing ONE integration decision and explicitly leaving the merge-and-revalidate gate untouched; this plan makes it govern that gate. Shipping the code alone would leave an approved spec asserting the opposite of the runner's behavior, which is the drift a declared spec edit exists to prevent. | C:Low; U:Low; S:Medium (the spec is the contract every other plan is reviewed against); F:Low; Overall:Low | FIXED | The spec file is added to `Scope-Paths` so both runners announce the edit and the finalize scope gate reconciles it; new E-06 owns the amendment and must preserve the exception's conjunctive conditions, captured-evidence requirement, `fixed` rule and honest limit verbatim; V-06 requires the diff and the unchanged-quotation proof; the spec-sync section is rewritten; recorded as F-10 |
| PR-006 | HIGH | IN-SCOPE | C. Architecture (rebuilding an existing mechanism) | `execute_item_core` writes `attempt[GATE_ANSWER_RECORD_KEY]` and `item[GATE_ANSWER_RECORD_KEY]` before the integration block builds `val_runner`; `gate_answer_record` returns `failing_tests`; verified at review by driving `perform_gate_answer` and reading the record back | E-03 PROPOSED A CHANNEL THAT ALREADY EXISTS, framed as "carry the set forward onto the item". Both the write and the id set are already there, on the very object the factory receives. Framed as new plumbing, an executor would plausibly add a second key for the same ids, which is precisely the producer/reader drift this module's comments cite twice (a renderer reading `driver_error` while the producer wrote `integration_deferral`). | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 rewritten as a READER plus a NORMALIZER that adds no key, no injection and no write, with the existing write site named by symbol; the normalization rules (node id, keep FAILED/ERROR apart, keep parametrization suffixes, unparseable line is never attributed) are spelled out; recorded as a conventions bullet |
| PR-007 | MEDIUM | IN-SCOPE | A. Correctness (a write that silently vanishes on one call path) | both hosts' `validation_runner_for=lambda item: make_integration_validation_runner(state, run_dir, dict(item), ...)`; `_record_revalidation`'s docstring ("IT WRITES THE ITEM AND DOES NOT PERSIST") | THE DEFERRAL RE-ATTEMPT PATH PASSES A SHALLOW COPY. A read of the answer record works through `dict(item)`; any write lands on the copy and is lost. A design that needed a durable write to explain its release would be broken on one of its two call paths, and the plan named neither path nor which it depended on. | C:Low; U:Medium (an unexplained pass is as hard to diagnose as an unexplained refusal); S:Low; F:Low; Overall:Low | FIXED | E-04 now states it depends only on the READ and routes any explanation through the existing `_record_revalidation` reason; raised and resolved as OQ-04 with the measurement; recorded as a conventions bullet |
| PR-008 | MEDIUM | IN-SCOPE | A. Correctness (a per-item verdict served from a shared cache) | the factory's `cache[tree_id] = {"passed":..., "reason":..., "measured":...}` and its cache-hit path; `ld8lb3` and `65cuw0` in ONE run with different answers (one `not-mine`, one absent) | THE REVALIDATION CACHE WOULD SERVE AN ANSWER-RELATIVE VERDICT ACROSS ITEMS. Keyed on the merged tree, the cache is correct while the verdict is a fact about the tree; this plan makes it relative to a per-item ANSWER without touching the cache, and the measured run contains two items whose answers differ. An item that never answered could be served a verdict released by another item's answer, which is the fail-open direction. | C:Medium; U:Low; S:Medium; F:Medium; Overall:Low-Medium | FIXED | E-04 requires either the attributed-set identity in the key or a per-item re-derivation, with the choice stated; raised as OQ-03 and resolved to cache-the-measurement to match sibling `tgyfs2`'s identical resolution; V-04 requires the two-items-one-tree case pasted |
| PR-009 | MEDIUM | UNDER-SCOPE | C. Architecture / sequencing | both plans declare `Scope-Paths: agent_workflows/runner_shared.py` and both modify the measured-red verdict in `make_integration_validation_runner._runner`; both declared `Item-Dependencies: none`; `tgyfs2` is `Status: reviewed`, `Readiness: go-pending-approval` | TWO PLANS REWRITE THE SAME VERDICT WITH NO DECLARED EDGE. The runner sorts by dependency depth and re-checks edges at dispatch, so an undeclared relationship is invisible to it and either order was possible; the second to land would rebase onto a function its author never read, and the composed behavior (two independent excuses over one refusal) was pinned by neither plan. | C:Medium; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | `Item-Dependencies: executed:tgyfs2` declared (grammar verified against `ipd_schema.parse_item_dependencies`); new E-07 requires the composed four-way matrix proved on the merged result, including that two refusing unknowns never compose into a pass; V-07 requires it pasted; the gate records that removing the edge makes E-07 unperformable |
| PR-010 | MEDIUM | IN-SCOPE | G. Plan executability / repository conformance | `aw check` reporting `check.ipd-uncarried-obligation`; `check_engine.carrier_severity_for_plan(text, root)` returns `error` for this plan's `- Date: 2026-09-22` against `CARRIER_CUTOVER_DATE = "20260919"`; all six deferred rows parsed with `fields == {}` | SIX DEFERRED ROWS CARRIED NO DURABLE CARRIER, at ERROR severity. Post-cutover, every `## Deferred / out of scope` row must name a `Carrier`, `Carrier-Evidence`, or `Carrier-Declined`, so that an obligation does not vanish when the plan reaches `executed` and classes `done` in `aw attention`. Verified pre-existing rather than caused by these edits by stashing them and re-running. | C:Low; U:Low; S:Low; F:Medium (an obligation silently disappearing is exactly what the rule prevents); Overall:Low | FIXED | Two rows handed off (`Carrier: fuk1mr`, `Carrier: iv4n2c`); four declined with reasons; re-verified by driving `evaluate_carrier_obligation` over all six rows (`ok` for each) and by `aw check` reporting zero findings for this plan |
| PR-011 | LOW | IN-SCOPE | E. Testing and verification | V-04 demanded a replay through "the real post-merge factory"; verified at review that `resolve_lane_endpoints` returns base `301a1d8fbc15` / branch `aw/lane/ld8lb3`, the branch exists at `78891bde`, and `git merge-tree --write-tree` gives tree `9ec0a5be8e52`, identical to the lane head tree and to the item's recorded `tree` | V-04's REPLAY IS ACHIEVABLE, which was worth proving rather than assuming, since the lane branch could have been pruned and the plan's central validation would then have been unperformable. Confirmed the recorded endpoints still resolve and reproduce the exact tree the failing revalidation measured. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-12 so the executor knows the replay inputs are live; V-04 now names the concrete base commit and attributed id to replay with |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan asserts an ask-reachability defect from `65cuw0`'s `null` answer record. Is that defect real? | NO. Retract the claim in the plan, delete E-02's investigation and E-04's reachability clause, and record the measured reason. | (a) Leave it and let the executor discover the premise is false, which spends a turn and risks a "fix" that loosens the ask predicate; (b) demote it to a deferred item, which would imply an open question the evidence closes; (c) ask the maintainer, which the repository itself answers. | `65cuw0`'s recorded `suite_check` is `passing: True`, `exit_code: 0`, `failures: []` (`8118 passed`) with `integration_signal: driver-run-suite`, and calling the real `gate_answer_is_warranted` with exactly those values returns `(False, 'integration was earned; there is nothing to answer')`. The predicate behaved correctly. | yes |
| D-2 | Does this plan require a `25kzda` amendment, or is consulting an existing record outside the spec's scope? | REQUIRES an amendment; declare the spec path and own it in E-06. | (a) Ship code only and treat the spec as describing intent rather than mechanism, which leaves an approved contract contradicting the runner; (b) file the amendment as follow-up work, which is the drift the declared-spec-edit rule exists to stop. | Section 5.1 states the exception "adds an ATTRIBUTED, REVIEWABLE input to one integration decision; it removes no gate" and names the merge-and-revalidate gate as "likewise untouched". `runner_shared`'s own baseline block independently states that a comparison here "would REQUIRE amending spec `25kzda`". ESCALATED because an approved spec is a published contract every other plan is reviewed against: maintainer told 2026-09-22 in this review's final report that E-06 amends `25kzda`, and the edit is declared in `Scope-Paths` so both runners announce it before the run starts. | no |
| D-3 | Should the attributed-set read be gated on the `not-mine` token, or on the presence of a non-empty set? | On the TOKEN, and require `usable` too. | Presence of the set, which is simpler and is what "reuse the answer record" implies. | Driving `perform_gate_answer` with `fixed` plus a passing re-run yields `release: True` with `failing_tests` holding the PRE-REPAIR ids, so a presence test clears failures whose repair did not survive the merge. `GateAnswerVerdict.integrates` is True for `not-mine` alone, and the module comment states `fixed` "releases only on an OBSERVED passing re-run". | yes |
| D-4 | An empty merged failing list on a red suite: release (nothing new) or refuse? | REFUSE. | Release, which the authored rule does implicitly and which reads as "nothing broke". | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` records plan `32ij2j` doing exactly this and calls the empty-list case the one "that was shipped wrong"; measured, `extract_suite_failures('') == ()`. Judged REVERSIBLE because it is the fail-CLOSED direction and nothing has shipped: a later maintainer who wants the permissive reading edits the plan or the predicate, at the cost of a rewrite. Recorded in the plan's hazard paragraph and pinned as E-05's most important control so the choice is visible rather than buried. | yes |
| D-5 | Either failing list at the 40-line cap: compare anyway or refuse? | REFUSE, detected by length. | Compare anyway and accept the error, which sibling `tgyfs2` can afford (over-refusal) but this plan cannot. | Measured: 45 attributed failures plus one genuine lane regression both cap at 40, the regression is truncated out of the merged list, and the subtraction releases a lane that introduced a failure. | yes |
| D-6 | The tree-keyed revalidation cache under an answer-relative verdict: widen the key or cache the measurement? | CACHE THE MEASUREMENT and re-derive the judgement per item. | Widen the key with the attributed-set identity, which is also sound but re-runs a ~107s suite for two items sharing a tree and disagreeing on their answer. | Sibling `tgyfs2` resolved the identical trap the same way at its own OQ-03; choosing differently would make the two siblings disagree about what the cache means, and they modify the same function. The expensive part is the suite RUN, which stays cached. | yes |
| D-7 | Declare a dependency edge on `tgyfs2`, or leave both `none`? | Declare `Item-Dependencies: executed:tgyfs2`. | Leave both `none` and rely on the isolated-worktree merge gate to catch the conflict, which catches textual conflict but not a semantic rebase onto a rewritten verdict, and pins the composed behavior nowhere. | Both plans modify the measured-red verdict in the same `_runner`; the runner sorts by dependency DEPTH and re-checks at dispatch, so an undeclared relationship cannot order them. `ipd_schema.parse_item_dependencies` accepts `executed:tgyfs2` and rejects `ipd:tgyfs2`. | yes |
| D-8 | The six deferred rows carry no typed carrier at ERROR severity. Hand off, decline, or ask? | Two handed off to existing live items (`fuk1mr`, `iv4n2c`); four declined with reasons. | Ask the maintainer which to file, which the rule itself answers by offering `Carrier-Declined` for exactly the not-outstanding case; or file new backlog items for prohibitions and non-defects, which would assert pending work that must never be done. | `check_engine.evaluate_carrier_obligation` accepts HANDOFF, SATISFIED or DECLINED and states the reason's merit is the reviewer's job; `fuk1mr` and `iv4n2c` both resolve live in the carrier index; every sibling plan reviewed this week uses the same pattern. Re-verified: all six rows now return `ok`. | yes |
