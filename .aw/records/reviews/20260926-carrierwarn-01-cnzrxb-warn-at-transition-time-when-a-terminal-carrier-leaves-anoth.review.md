# Review findings: plan cnzrxb

- Subject-Id: cnzrxb
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `21b22c3b`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED
(exit 0, `findings: 0`) before any revision. No pre-review snapshot was needed: the lane-input copy at
`.aw/state/lane-inputs/rev-6/` is byte-identical to the tracked file (`diff` -> IDENTICAL) and
`git status --short` was empty.

THE PROBLEM IS REAL AND BOTH CITED INCIDENTS VERIFIED. `b20b7a74` re-pointed plan `8ud1is`'s deferred
row off executed carrier `0yrtne`, and its own commit message says "the obligation was satisfied
there"; `e0581df0` did the same for `a6xbso` off executed `8apjpp`, recording that the carrier "has
since executed, delivering the AW-Run/AW-Item/AW-Committed-By trailers". So in both cases the carrier
HAD done the work and CI went red anyway. F-1's correction of the source backlog item is also right:
`check_durable_carrier` sweeps every pending plan on every `aw check plans`, which `.github/workflows/tests.yml`
runs fail-closed, so the item's "clean tree in the window" claim was false. The maintainer's
finished-versus-abandoned ruling is the right shape and I did not revisit it.

**THREE MEASURED DEFECTS WOULD EACH HAVE MADE THE PLAN FAIL ITS OWN STATED OUTCOME.** These are the
substance of this review.

FIRST, `warning` DOES NOT MEAN NON-FAILING. E-01 asked for severity `warn` and registration "at
warning severity so `aw check plans` does NOT exit nonzero on it". Driven:

```text
error -> exit 1
warning -> exit 1
warn -> exit 1
info -> exit 0
```

`artifact_core.drift_exit_code` is `1 if any(severity != "info")`. And this is not an obscure corner:
the comment on `_CARRIER_LEGACY_SEVERITY`, a few lines above the very frozenset E-01 edits, states it
verbatim, "`artifact_core.drift_exit_code` exempts ONLY `info`, so a `warning` here would exit 1 on a
clean tree ... and fail CI", citing `check.stale-index-missing` as "`info`, the ONLY non-failing
severity". So the item as written would have shipped a change whose headline outcome was false, and
V-01 (which asked only for the finding, not the exit code) would not have caught it. Corrected to
`info`, with V-01 now demanding the exit codes and the honest cost stated in the gate and CHANGELOG:
`info` also routes to `ipd_lint`'s advisories, so the pre-transition gate stops blocking too.

SECOND, THE TWO-RULE SPLIT NEEDS AN EMITTER CHANGE THE PLAN NEVER MENTIONED. `evaluate_durable_carrier`
emits AT MOST ONE Drift per plan, with the hardcoded `_CARRIER_RULE` and one severity from
`carrier_severity_for_plan`, joining up to five reasons into one detail. Driven on a plan carrying one
finished-carrier row and one wholly uncarried row:

```text
Drift count: 1
 rule: check.ipd-uncarried-obligation | severity: error
 detail: 2 obligation(s) name no durable carrier: deferred row 1: carrier bk0001 resolves only to a
 terminal/hidden artifact (done); nothing revisits it; deferred row 2 records an outstanding
 obligation with NO durable carrier; ...
```

A per-row verdict change therefore cannot produce a non-failing finished finding at all: the plan's own
mixed case still collapses to one `error`. Worse, a careless fix in the other direction would make the
ABANDONED and uncarried rows non-failing too, disabling the rule the maintainer explicitly kept. This
is now the larger half of E-01 (partition failures by rule, emit one Drift per rule with its own
severity and its own cap) and is pinned by a new E-08 that FAILS against the current emitter. I also
added it as a genuine stop condition, because it is the failure mode a hurried execution would ship.

THIRD, BOTH RUNNER MECHANISMS THE PLAN NAMED ARE INERT. E-04 proposed adding the new rule code to
`RETRYABLE_FINALIZE_FINDING_TEXTS`. But `finalize_refusal_is_retryable` locates findings with
`line.strip().startswith("IPD-")`, while `aw ipd finalize` prints `  {d.rule} {d.detail}`, so a
`check.*` line is invisible to it. Driven on a realistic carrier refusal message: `finding_lines` is
`[]` and the predicate returns False, by its own documented fail-closed rule. And E-03's send-back is
worse than inert, it is silent:

```text
finalize_retry_decision(item, state, "carrier-verification-unresolved: ...")
-> retry=False exhausted=False reason=''
```

which is LEAVE-ALONE with no error. The deeper problem is the premise: in E-03's case finalize
SUCCEEDED, so there is no refusal message and the refusal arm is never entered. Both items keep their
goal with achievable mechanisms: E-04 now PROVES the self-refusal is gone via a conforming
pre-transition lint (which `info` delivers for free) and is forbidden from widening the fail-closed
locator; E-03 takes its own structural bound in the shape `attempt["defect_reasked"]` already uses,
and records an asked-and-unanswered outcome, which is the precedent the defect re-ask sets in terms.

**I ALSO CHANGED WHAT E-03 DOES ON AN UNRESOLVED ANSWER, and this is a behavior decision a human should
see.** The plan had the item "not integrated and reported, lane preserved". But the unresolved row is
in ANOTHER plan, while plan B itself is finalized and verified, so withholding B's integration strands
correct validated work over a third party's row. That is the lane-stranding outcome the runner's whole
send-back design exists to stop. E-03 now records the refusal, reports it, and integrates B; blocking
integration is flagged as a policy change to raise explicitly rather than take as a side effect.

**A DIRECT COLLISION WITH A REVIEWED PENDING PLAN WAS UNDECLARED.** `xz59ai` (Set `carrierauth`,
`Status: reviewed`) rewrites `_resolve_carrier`'s terminal verdict and `evaluate_carrier_obligation`'s
`raw_carrier` branch to KEEP the refusal at `error` while printing a pasteable
`- Carrier-Evidence: <path>` and a warning against `Carrier-Declined`. This plan makes the same case
non-failing. Both declare `agent_workflows/check_engine.py`, both were pending, and neither named the
other, so whichever ran second would silently undo the other's reviewed behavior. The substance is
complementary (a non-failing finding that still prints the exact fix is strictly better than either
alone), so I declared `- Item-Dependencies: executed:xz59ai` and added E-09 to preserve its remedy text
inside the new advisory and to verify its tests.

**WHAT I MEASURED AND DID NOT TURN INTO A BLOCKING FINDING.** The follow-up-turn primitive E-03 needs
DOES exist and I confirmed its shape rather than letting the executor invent one: `resume_via_launcher`
has exactly two callers (defect re-ask, gate answer), each reading `attempt["session_id"]`, passing
`work_dir`, and branching on `host_labels == OC_HOST_LABELS` for `resume_session` versus
`session_id` + `use_continue=False`; its docstring records that a test pins each host's launcher to two
callers so a third direct call is forbidden, and that an isolated lane turn is otherwise ALWAYS a fresh
session (`lanesess xd9sll`, four lanes lost). I wrote that into E-03 as a requirement. I also checked
the out-of-lane edit is safe at integration: `integrate_lane_branch` calls
`execute_merge_and_revalidate_gate` WITHOUT `declared_scope`, so the gate's scope-fence arm is not
armed, and finalize's scope reconciliation is already past by the time this turn runs; keeping the edit
in its own commit avoids commit-boundary cohesion attributing another plan's paths to B later. Both
existing follow-up turns sit ~500 and ~800 lines BEFORE finalize in `execute_item_core`, so E-03's
placement after finalize is genuinely new ground, which is why I required the launcher-path test case.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. correctness; G. executability (a stated outcome that is false) | driven: `drift_exit_code` -> `error` 1, `warning` 1, `warn` 1, `info` 0; the `_CARRIER_LEGACY_SEVERITY` comment states it verbatim and cites `check.stale-index-missing` | **E-01's `warn`/`warning` TIER STILL EXITS 1, so "aw check plans exits 0 on a finished carrier" was unachievable as written.** The only non-failing severity is `info`. V-01 as authored asked for the finding but not the exit code, so nothing in the plan would have caught it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now specifies `info` with the measurement and the in-tree authority; F-5 records it; V-01 demands both exit codes and the advisory pre-transition lint; the gate and CHANGELOG state the cost (the gate stops blocking too, and the finding is skimmable). |
| PR-002 | HIGH | UNDER-SCOPE | A. correctness (a change that cannot express its own outcome) | driven: a plan with a finished row plus an uncarried row -> ONE Drift, `check.ipd-uncarried-obligation`, `error`, reasons concatenated; `evaluate_durable_carrier` hardcodes `_CARRIER_RULE` and one `carrier_severity_for_plan` severity | **EMITTING TWO RULES REQUIRES SPLITTING THE EMITTER, WHICH THE PLAN NEVER MENTIONS.** One Drift per plan, one rule, one severity. So a per-row verdict change cannot make the finished case non-failing, and a careless fix would make the abandoned/uncarried rows non-failing too, disabling the rule the maintainer kept. No item or test covered the mixed plan. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium (bounded: partition the failure list and emit per rule, with a test that fails first) | FIXED | E-01 gains the emitter split as its larger half; new E-08 pins the mixed case and must FAIL against the current emitter; new V-08; F-6 records the drive; the Scope check names it; a genuine stop condition forbids shipping a fix that de-fangs the abandoned case. |
| PR-003 | HIGH | IN-SCOPE | A. correctness; C. operability (a send-back that silently does nothing) | driven: `finalize_retry_decision(item, state, "carrier-verification-unresolved: ...")` -> `retry=False exhausted=False reason=''`; finalize returned 0 in this path so there is no `fin_msg` to classify | **E-03's SEND-BACK IS A SILENT NO-OP AND ITS PREMISE DOES NOT HOLD.** The retry machinery classifies FINALIZE REFUSALS; here finalize SUCCEEDED. An unrecognized string returns LEAVE-ALONE with no error, so the "unresolved row" path would quietly do nothing while the plan claims a bounded send-back. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 now takes its own structural bound (the per-attempt flag pattern the defect re-ask uses, which never loops) and RECORDS an unresolved answer via `record_refusal`, citing the re-ask's own "asked and did not answer is itself a finding" precedent; F-8 records the drive; V-03 demands the recorded refusal and the one-dispatch proof; E-06 case (b) no longer tests a budget that cannot fire. |
| PR-004 | MEDIUM | IN-SCOPE | C. operability (stranding verified work) | the unresolved row lives in a DIFFERENT plan; plan B is finalized and verified; the runner's send-back design exists to stop stranded lanes | **NOT INTEGRATING PLAN B OVER ANOTHER PLAN'S UNRESOLVED ROW STRANDS CORRECT WORK.** E-03 said the item "stays non-integrated and is reported, lane preserved" for a condition B does not own. | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-03 now records and reports the refusal and INTEGRATES B, and states that blocking integration would be a policy change to raise explicitly; E-06 case (b) asserts B still integrates; the gate's point (3) is rewritten so the human approves the actual behavior. |
| PR-005 | MEDIUM | IN-SCOPE | A. correctness; B. security-adjacent (loosening a fail-closed allowlist) | `finalize_refusal_is_retryable` collects lines via `startswith("IPD-")`; `ipd_lifecycle` prints `  {d.rule} {d.detail}`; driven on a carrier refusal: `finding_lines == []`, predicate False | **E-04's MECHANISM IS INVISIBLE TO THE CLASSIFIER**, so adding the rule to `RETRYABLE_FINALIZE_FINDING_TEXTS` changes nothing; making it work would require widening a deliberately fail-closed line locator that a test pins on purpose. | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | E-04 re-scoped to PROVE the self-refusal is gone via a conforming pre-transition lint (which `info` delivers with no `ipd_lint` edit), with the classifier explicitly left alone; V-04 requires a diff showing it UNCHANGED, or a justification plus the measurement that a refusing path survived; F-7 records it; a stop condition forbids the widening. |
| PR-006 | MEDIUM | UNDER-SCOPE | A. correctness (two plans rewriting one branch on opposite premises) | `xz59ai` is `Status: reviewed`, declares `agent_workflows/check_engine.py`, and its E-03 rewrites `_resolve_carrier`'s terminal branch to KEEP the refusal while printing a pasteable `- Carrier-Evidence:`; this plan makes the same case non-failing; neither named the other | **AN UNDECLARED COLLISION WITH A REVIEWED PENDING PLAN ON THE SAME FUNCTION.** Whichever executed second would silently undo the other's reviewed behavior. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Declared `- Item-Dependencies: executed:xz59ai`; new E-09 preserves `xz59ai`'s pasteable remedy inside the new advisory and verifies its tests; new V-09; F-9 records the collision and why the combination is the better outcome; a stop condition covers executing before it lands; the gate tells the human they are approving that ordering. |
| PR-007 | MEDIUM | UNDER-SCOPE | E. testing (an undeclared path holding the tests this changes) | `tests/test_check_engine.py` is the only file containing `Carrier` assertions today (`rg -l Carrier tests/` -> that file alone), including the carrier-severity cutover test | **THE FILE HOLDING THE EXISTING CARRIER TESTS IS NOT IN `- Scope-Paths:`.** E-01 changes verdicts those tests assert, so the breakage would surface in E-07's bare suite as a surprise and the edit would be out of scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `tests/test_check_engine.py` to `- Scope-Paths:`; E-08 lives there and must reconcile the existing expectations deliberately; V-08 requires each changed expectation named with its reason. |
| PR-008 | LOW | IN-SCOPE | E. testing; G. executability (stale corpus facts and a changed signature) | measured: 47 pending plans (not ~65), and across all of them 9 carrier rows resolve to a LIVE owner and ZERO to a finished or abandoned one; `_question_obligations(open_questions, *, plan_text=None)` is now called with `plan_text=`; live `check plans` exits 1 on a PRE-EXISTING uncarried row in `2yqt0a` | **THE CORPUS CLAIMS ARE STALE AND ONE CALLED SIGNATURE MOVED.** E-02's timing target cites a wrong plan count; E-05's cases do not exist in the tree so they must be fixtures; E-07's implied clean `check plans` is not achievable today; and omitting the new `plan_text` keyword would re-report scaffold placeholder questions to an agent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 records all four; E-02 re-derives the count and passes `plan_text=`; E-05 builds fixtures and sets the carrier cutover in them (else grandfathering, not this change, decides the tier); E-07 and V-07 expect zero live findings of the new rule and require naming any surviving pre-existing finding. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01 asks for `warn` severity to stop failing CI. Accept, or check what the exit convention does with it? | CHECK, and `warning` exits 1; specify `info`, the only non-failing tier. | (a) Accept `warn`: rejected, the item's own expected outcome would be false and CI would stay red, which is the entire defect the plan exists to fix. (b) Change `drift_exit_code` to exempt `warning` too: rejected outright, that would silently de-fang every `warning`-tier rule in the registry, far outside this plan's concern. | `drift_exit_code` driven for all four spellings; the `_CARRIER_LEGACY_SEVERITY` comment and its `check.stale-index-missing` precedent read in place. | yes |
| D-2 | Can a per-row verdict change alone emit a second, non-failing rule? | NO. The emitter must be split to produce one Drift per rule; make that explicit and pin the mixed case. | (a) Leave the emitter alone: rejected, driven proof that a mixed plan collapses to one `error` Drift, so the plan's outcome is unreachable. (b) Emit one Drift per ROW: rejected, the five-reason cap and the one-Drift-per-plan shape exist because 664 rows across 106 plans would otherwise add a line each to every clean `aw check plans`, a measured reason recorded in the function's own docstring. | `evaluate_durable_carrier` read end to end; mixed-plan case driven; the docstring's per-row rationale read. | yes |
| D-3 | E-03/E-04 reuse the finalize retry machinery. Trust it, or drive it? | DRIVE IT: both are inert. Give E-03 its own structural bound and re-scope E-04 to a proof. | (a) Widen `finalize_refusal_is_retryable`'s locator so `check.*` lines are seen: rejected, it is deliberately fail-closed and test-pinned, and loosening it would admit refusal classes spec 5.5 forbids retrying. (b) Add a second retry budget: rejected, the plan's own conventions forbid it and the defect re-ask shows a structural one-shot flag is sufficient and safer. | `finalize_refusal_is_retryable` and `finalize_retry_decision` driven with a carrier message; `ipd_lifecycle`'s finding renderer read; the defect re-ask's never-loops docstring read. | yes |
| D-4 | An unresolved verification answer: block plan B's integration, or record and continue? | RECORD AND INTEGRATE. Blocking is called out as a separate policy question. | (a) Block integration as authored: rejected, the unresolved row belongs to another plan while B is finalized and verified, so blocking strands validated work, which is the exact outcome the send-back design exists to prevent. (b) Say nothing and leave it ambiguous: rejected, the executor would have to guess, and the human would approve a behavior nobody stated. | The runner's stranded-lane rationale in `handle_finalize_refusal` / `finalize_retry_decision`; the ownership distinction between B and the row's plan. | yes |
| D-5 | Two pending plans rewrite `_resolve_carrier` on opposite premises. Pick a winner, or order them? | ORDER THEM, this one AFTER `xz59ai`, and preserve `xz59ai`'s remedy text inside this plan's advisory. | (a) Let both stand undeclared: rejected, whichever ran second would silently undo a reviewed behavior. (b) Retire or supersede `xz59ai`: rejected, it is narrower, already reviewed, and its pasteable-fix text is valuable precisely BECAUSE this plan stops the finding from blocking (a skimmable advisory that names the exact fix is better than one that does not). (c) Merge them into one plan: rejected, that discards a completed review and mixes a message change with a runner change. | `xz59ai` read in full (its Scope-Paths, E-03, and gate); this plan's E-01 compared against it. | yes |
| D-6 | The plan cites "~65 pending plans" and expects live examples. Accept, or measure? | MEASURE: 47 plans, and ZERO rows in the finished or abandoned state, so fixtures are mandatory and a clean live run is not the bar. | (a) Accept the number: rejected, a timing target over a wrong denominator is not checkable and the population moves as lanes land. (b) Wait for a live example to appear: rejected, it would make the tests depend on a future defect, and both historical examples were already fixed by hand. | Carrier rows enumerated across all 47 pending plans via `_carrier_index` plus the two obligation parsers; live `aw check plans --agent` run. | yes |

### Deferred and open

- (none). All eight findings were FIXED in place. Three are at the `HIGH` gate threshold (PR-001,
  PR-002, PR-003) and all three are fixed WITHIN this plan's scope, so no `- Blocking: yes`
  escalation is owed: each was a mechanism that could not deliver the item's own stated outcome, and
  each item now carries an achievable mechanism plus validation that would catch a regression. OQ-01
  was already resolved by the maintainer and I did not re-open it; I added OQ-02 (resolved, non-blocking)
  to RECORD the non-run consequence of the `info` tier, because a reader is entitled to see that a
  finished carrier now blocks nothing outside a run where today it blocks.

HONEST LIMITS, stated because they bound what this round proves. I verified the DEFECTS, the incidents,
the severity convention, the emitter shape, and both runner predicates by driving them; I did NOT
implement any of it, so that the emitter split lands correctly, that the follow-up turn dispatches
through `resume_via_launcher` at the post-finalize site, and that `xz59ai`'s remedy survives the merge
all remain E-01, E-03, E-09 work and V-01, V-03, V-08, V-09 evidence. My E-03 analysis rests on reading
the two existing `resume_via_launcher` call sites and on the fact that both sit BEFORE finalize in
`execute_item_core`; I did not execute a run, so whether a resumed session behaves identically AFTER a
finalize has moved the plan file is asserted by E-06 rather than measured by me, and it is the single
riskiest unproven assumption in the plan. I also did not audit whether any OTHER pending plan edits
`runner_shared.execute_item_core`'s finalize region, so the `xz59ai` collision is the one I found and
not provably the only one. Finally, `xz59ai` is `reviewed` but NOT executed, so this plan's declared
dependency is currently unsatisfiable until it runs.
