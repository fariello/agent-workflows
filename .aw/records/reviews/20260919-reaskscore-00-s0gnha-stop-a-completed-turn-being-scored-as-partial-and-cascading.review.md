# Review findings: plan s0gnha

- Subject-Id: s0gnha
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `24a3c262`. The plan on disk was byte-identical to the sealed lane input (`diff`
reported no difference) and `git status --porcelain` was empty, so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0, both
before and after the revisions; `--phase review-finalize` also reports `clean` after them.

THE DIAGNOSIS IS EXCELLENT AND THE SET SHAPE IS RIGHT. This is the strongest class of plan in this
repository: three independent defects, each measured in named runs with on-disk artifacts cited, each
fixable alone, and a correct refusal to "fix" the dependency cascade that propagated the harm. I verified
the central mechanism claim against the runner rather than accepting the prose, and it holds: the scoring
call, the defect re-ask block, the injected `recollect`, and `integration_gate_relevant` sit in exactly
the order the children describe, `reconcile_disposition` really is pure in all three copies, the body
really does already call it twice on the stop paths, and `lane_containment.py`'s own comment really does
say the recollect destination is "the submission `reconcile_disposition` actually reads". `skn8uk`'s
OQ-02 resolution is also correct on a point that is easy to get wrong: a rescued item reaching the gate
with `verify_disp is None` does fall to `integration_is_earned`'s suite branch, which is a real reviewed
path and not a hole.

WHERE THIS REVIEW SPENT ITS EFFORT: the parent was authored as a three-child orchestrator, a fourth child
(`svacmz`) was added two commits later in response to the orchestrator coverage gate, and the parent was
never reconciled with its own new child. That left duplicated ownership of the Set's only end-to-end
proof, plus two mechanical defects that would each have refused this plan's own finalize. Every finding
below was measured.

**1. The parent still claims work `svacmz` now owns, so the Set's central proof has two owners and no
second observer.** `svacmz` was authored specifically because the coverage gate refused
`aw oc run reaskscore` naming `s0gnha`, and its own Concern says it "OWNS THE VERIFICATION E-02 AND E-03
DESCRIBE". But the parent's E-02 and E-03 were left verbatim, so both plans instructed an agent to pin
the five constants and reconstruct SHAPE A and SHAPE B. That is not merely redundant. The parent's items
are performed by NOBODY under a runner retirement
(`ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']` states the skip and its reason),
so the duplicate copy is the one that gets ticked without being done, and a reader comparing the two
cannot tell which is authoritative. Fixed by rewriting the parent's E-02 into a RECEIPT CHECK over
`svacmz`'s four `Observed evidence` blocks (explicitly forbidding a re-run performed here, which would
make the parent the observer of its own receipt) and repointing the Completion criteria, the Cross-IPD
validation rows, and the Required tests section at `svacmz` as owner.

**2. The parent still counts three children, four ways.** `- Scope:` said "the three child plans" and
enumerated three; E-01 and V-01's expected outcomes said "all three children"; the first Completion
criterion said "All three children"; OQ-01's rationale said "all three children are conforming". The
child table has FOUR rows. Fixed throughout, and E-01/V-01 now also carry `svacmz`'s three `executed:`
edges so the dispatch order it depends on is stated where an executor reads it.

**3. Two self-carriers would have refused this plan's own finalize, at `error` severity.** The spec row
in Deferred and OQ-01 both carried `- Carrier: s0gnha`, pointing at the plan that holds them.
`check_engine._resolve_carrier` fails a carrier resolving only to a TERMINAL artifact, and `executed` is
in `_CARRIER_TERMINAL_STATUSES`, so a self-carrier resolves while the plan is pending and goes terminal at
the exact moment the plan finalizes. Measured by substituting an `executed` status for `s0gnha` in the
live carrier index: 2 of 5 obligations flipped from legitimate to failing, with the reason "resolves only
to a terminal/hidden artifact (executed); nothing revisits it". The severity is `error` and not the
grandfathered advisory tier because `carrier_severity_for_plan` compares the plan's own `- Date:`
(2026-09-19) against `CARRIER_CUTOVER_DATE` (`20260919`), and this plan is the first day of the error
tier; the rule is evaluated at `pre-transition` (`ipd_lint._CARRIER_CHECKPOINTS`), which is precisely the
checkpoint this plan's own gate paragraph requires to report conforming. Fixed by converting both to
`- Carrier-Declined:` with the measured reason recorded, and re-measured afterwards: 0 failing.

**4. E-03's backlog transitions are real work that a runner retirement performs by nobody, and the
coverage gate cannot catch it.** This is the subtler half of finding 1 and it is why I did not simply
delete the parent's items. After the rewrite, E-03 (two `aw backlog set` calls transitioning `yxfw4k` and
`x7wfyx`) is a genuine act with a real gate: `x7wfyx` carries `Blocks-Release: next`, so closing it `done`
would trip the close-legitimacy gate, and `graduated` is the honest value. Under a runner retirement its
checkbox is reported complete unperformed and the two items keep their pre-Set statuses while the parent
claims otherwise. The coverage gate does not fire, because it asks whether a parent carries work no child
COVERS, and this work is declared on the parent rather than unowned. I did NOT delete the item (AGENTS.md
and the gate's own instruction both forbid emptying a parent's checklist, and the transitions genuinely
must happen), and I did not author a fifth child for two shell commands on my own authority. Recorded as
OQ-02 with three shapes, and the gate paragraph now states the manual step explicitly.

**5. `dy9ymn` E-04 rests on a budget with no consumption wiring anywhere in the package, and a
release-blocking approved plan already owns closing that gap.** `dy9ymn` instructs the executor to bound
its retry "by the existing retry budget", to "use the run's already-resolved value" and to "introduce NO
second retry knob". Measured: `--retry-budget` is parsed, range-validated via
`run_recovery.validate_retry_budget`, and frozen into run options, and NOTHING READS THE FROZEN VALUE
BACK for item retries. `grep` for `options.*retry_budget`, `get("retry_budget")` and `["retry_budget"]`
across `agent_workflows/` returns nothing, and `run_recovery.plan_retry` / `retry_budget_remaining` have
zero callers outside their own module. The contrast is informative: the sibling
`integration_retry_limit` IS read back, at `runner_shared.py`'s `int(options.get(
"integration_retry_limit", ...))`. So `dy9ymn`'s executor will find no budget to spend and must either
build the consumption path (which is `xipfy1`'s declared scope, `approved`, `Blocks-Release: next`, and
whose own review already escalated a BLOCKER about the `RunEngine`/ledger substrate that path needs) or
invent the second knob `dy9ymn` forbids. `xipfy1` shares three of `dy9ymn`'s four `Scope-Paths`. Neither
plan cites the other; `grep` for `xipfy1|retrywire` across all five reaskscore plans returns 0. This is
`dy9ymn`'s defect to fix, not the parent's, and `dy9ymn` is outside this review's ledger, so it is
escalated as a HIGH finding with OQ-03 rather than edited.

**6. Citation drift is already material at authoring time, in a corpus that has a plan about exactly
this.** Measured by extracting every `file:line` citation from the five plans and comparing the line's
content at the authoring commit `f3da906e^` against HEAD: 22 of 74 distinct citations (30%) now point at
different code, with `skn8uk` worst at 12 of 25 (48%). None is out of range, so none announces itself.
Concrete cases: `skn8uk`'s headline `runner_shared.py:13107` (the scoring call, the single most important
anchor in the Set) now lands on `else None`; `:13337` (the integration gate) now lands on an
`"event": "lane-submissions-collected"` string; the parent's own `:6443` for
`SET_RETIREMENT_DONE_STATUS` (really at `:6736`) now lands on `raise DriverError(...)`. The cause is
mechanical and not carelessness: `runner_shared.py` went 13844 -> 14082 lines between authoring and now.
Plan `mzc019` exists for this exact defect, is `reviewed` / `go-pending-approval`, and requires a SYMBOL
or quoted-content anchor. I repaired the parent's own citation (now `runner_shared.SET_RETIREMENT_DONE_STATUS`
plus a quote of its comment) and recorded the child measurements; repairing 21 citations across four
child files is outside this review's ledger, so PR-006 is MEDIUM and advisory, with the note that an
executor must re-derive every anchor by symbol before trusting it.

**7. E-01 offered a parallel dispatch mode that does not exist.** It said `skn8uk` and `ty7w6o` "may run
in either order or in parallel lanes". Neither runner can dispatch two items concurrently: each
`run_queue` sorts the queued items, selects ONE whose dependencies are satisfied, and `break`s
(`oc_runipd.run_queue`, mirrored in `agy_runipd`), and there is no `--jobs`/`--parallel` flag in either
(`grep -c` for `concurrent.futures|ThreadPoolExecutor|--jobs|--parallel` returns 0 in both drivers). The
claim is harmless to correctness but it tells an executor a mode is available that is not. Fixed by
stating the measured single-dispatch property in E-01.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. executability; D. anti-regression | parent E-02/E-03 as authored vs `svacmz` Concern ("OWNS THE VERIFICATION E-02 AND E-03 DESCRIBE") and its E-01..E-04; `ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']` | `svacmz` was added to own the parent's E-02/E-03 after the coverage gate refused the Set, but the parent's items were left verbatim, so the Set's only end-to-end proof has two owners. The parent's copy is the one a runner retirement ticks WITHOUT performing, so the duplicate is strictly the unsafe one, and a reader cannot tell which is authoritative | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Parent E-02 rewritten as a RECEIPT CHECK over `svacmz`'s four `Observed evidence` blocks, explicitly forbidding a re-run performed by the parent; Completion criteria, Cross-IPD validation and Required tests repointed at `svacmz` as owner; V-02 rewritten to demand the quoted blocks and to FAIL on an empty one |
| PR-002 | MEDIUM | IN-SCOPE | G. executability; honest record | `- Scope:`, E-01, V-01, first Completion criterion and OQ-01 all said "three children"; the child table has 4 rows | The parent was never reconciled with its fourth child, so it under-counts its own Set in four places and omits `svacmz`'s three `executed:` dependency edges from the sequencing item an executor reads | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All five counts corrected to four; E-01 and V-01 now state `svacmz`'s edges and require evidence it was dispatched last |
| PR-003 | HIGH | IN-SCOPE | A. correctness; G. executability | Measured via `check_engine.evaluate_carrier_obligation` with an `executed` status substituted for `s0gnha`: 2 of 5 obligations flip to failing, "resolves only to a terminal/hidden artifact (executed)"; `_CARRIER_TERMINAL_STATUSES` contains `executed`; `carrier_severity_for_plan` vs `CARRIER_CUTOVER_DATE = "20260919"` and the plan's `- Date: 2026-09-19`; `ipd_lint._CARRIER_CHECKPOINTS = frozenset(("pre-transition",))` | The Deferred spec row and OQ-01 both carried `- Carrier: s0gnha`, a SELF-carrier that resolves while the plan is pending and goes TERMINAL at the plan's own finalize. `check.ipd-uncarried-obligation` would then report both at `error` severity (the plan's date is the first day of the post-cutover tier) at the `pre-transition` checkpoint, which is exactly the checkpoint the plan's own gate requires to report conforming, so the plan would refuse its own lifecycle transition | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both converted to `- Carrier-Declined:` with the measured reason recorded in the plan so a later author does not reintroduce the pattern; re-measured after the fix: 0 of 6 obligations failing at a simulated own-finalize |
| PR-004 | MEDIUM | UNDER-SCOPE | A. correctness; D. anti-regression | `ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`; `x7wfyx` front matter `- Blocks-Release: next`; the close-legitimacy gate in AGENTS.md and `check_engine.evaluate_blocking_close` | After PR-001's rewrite, E-03 (transition `yxfw4k` and `x7wfyx`) is real work a runner retirement performs by NOBODY, so its checkbox is reported complete while both items keep their pre-Set statuses. The orchestrator coverage gate cannot catch it, because it asks about work no child COVERS and this work is declared on the parent | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | Escalated as OQ-02 (non-blocking) with three shapes for the maintainer: leave it with the manual-step warning, author a fifth child, or move it onto `svacmz`. The gate paragraph now states the manual step explicitly. Deliberately NOT fixed by deleting the item (AGENTS.md forbids emptying a parent's checklist) nor by authoring a fifth child on my own authority |
| PR-005 | HIGH | UNDER-SCOPE | C. architecture; G. executability (cross-plan) | `grep` for `options.*retry_budget`/`get("retry_budget")`/`["retry_budget"]` across `agent_workflows/` returns nothing; `run_recovery.plan_retry` and `retry_budget_remaining` have zero callers outside their module; contrast `int(options.get("integration_retry_limit", ...))` which IS read back; `xipfy1` is `approved` / `Blocks-Release: next` and shares 3 of `dy9ymn`'s 4 `Scope-Paths`; `grep -c "xipfy1\|retrywire"` = 0 in all five reaskscore plans | `dy9ymn` E-04 bounds its retry by "the existing retry budget" and forbids a second knob, but no consumption path for the frozen budget exists: the value is parsed, validated and frozen, and read back by nothing. Its executor must therefore either build `xipfy1`'s declared scope (whose own review escalated a BLOCKER about the absent `RunEngine`/ledger substrate) or invent the knob `dy9ymn` forbids. Neither plan cites the other despite the 3-file overlap | C:Medium-High; U:Low; S:Low; F:Medium-High; Overall:Medium-High | FIXED | RESOLVED 2026-09-19 FROM THE REPOSITORY (no maintainer prompt was needed): SHAPE (b) is already chosen and implemented in `dy9ymn`'s own text, so the question had no live decision left. BOTH PREMISES EXPIRED BETWEEN THE TWO REVIEWS, which the timestamps make checkable: this review read `dy9ymn` at `24a3c262` and its lane merged at 12:53, while `dy9ymn`'s own round 1 landed at `27d399ed` 13:35, 42 minutes later. At `24a3c262` E-04 read "Use the run's already-resolved value ... introduce NO second retry knob" with `grep -c integration_attempts` = 0, the unbuildable form this finding correctly reports; at HEAD that wording is gone and the count is 7, E-04 now instructing the executor to count on the item mirroring the shipped `integration_attempts` precedent, needing no ledger and adding no knob. SECOND, `xipfy1` OQ-03 reads `- Status: resolved` at HEAD AND at `24a3c262` itself: the maintainer settled the substrate on 2026-09-10, choosing the drivers' own `state.json`/`events.jsonl`, so shape (a)'s stated cost never applied and the two answers agree. THE CODE FACT THIS FINDING MEASURED REMAINS TRUE and is not being waved away: re-measured at HEAD, no read of the frozen `retry_budget` exists anywhere, `plan_retry`/`retry_budget_remaining` still have zero external callers, `run_engine`/`RunEngine` appear 0 times in both drivers, and 0 of 214 run directories hold a `ledger.jsonl`. Only the INFERENCE that this leaves `dy9ymn` unexecutable was falsified. No edit to `dy9ymn` was made: it is `go-pending-approval`, carries no gating finding, and its OQ-04 already records the `xipfy1` relationship and the non-collision argument |
| PR-006 | MEDIUM | IN-SCOPE | E. testing; G. executability | Measured across the five plans at authoring commit `f3da906e^` vs HEAD: 22 of 74 distinct `file:line` citations drifted (30%), `skn8uk` 12 of 25 (48%), none out of range. `skn8uk`'s `runner_shared.py:13107` (the scoring call) now reads `else None`; `:13337` (the integration gate) now reads `"event": "lane-submissions-collected"`; parent `:6443` now reads `raise DriverError(...)` while the constant is at `:6736`. `runner_shared.py` grew 13844 -> 14082 lines. Plan `mzc019` (`reviewed`, `go-pending-approval`) requires symbol anchors | Nearly a third of the Set's citations already misdirect, silently, pointing at other valid plausible code rather than at nothing. The Set's load-bearing anchors are among the drifted, so an executor following them reads the wrong construct and reasons from there | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Fixed in the REVIEWED plan (the only file in this ledger); the 21 child citations are recorded, not repaired. The parent's own citation repaired to a SYMBOL anchor (`runner_shared.SET_RETIREMENT_DONE_STATUS` plus a quote of its comment). The 21 child citations are outside this review's ledger and are recorded here with their measurements; an executor MUST re-derive every anchor by symbol before trusting it. Not escalated as blocking: the drift misdirects but does not change any plan's design, and `mzc019` is the durable fix already in flight |
| PR-007 | LOW | IN-SCOPE | C. architecture; F. KISS | `oc_runipd.run_queue` selects one item and `break`s; `agy_runipd` mirrors it; `grep -c "concurrent.futures\|ThreadPoolExecutor\|--jobs\|--parallel"` = 0 in both drivers | E-01 said the two independent children "may run in either order or in parallel lanes", offering a dispatch mode neither runner has | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now states the measured single-dispatch property, so an executor working by hand does not look for a parallel mode |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The parent duplicates `svacmz`'s E-02/E-03. Delete the parent's items, or convert them? | CONVERT. E-02 becomes a receipt check over `svacmz`'s evidence blocks; E-03 becomes the Set-level backlog transitions that no child owns. The checklist keeps three items. | (a) DELETE both, leaving E-01 alone: rejected outright. AGENTS.md states that deleting a parent's checklist "causes exactly the lost or partial work it exists to prevent" and that an Order-0 orchestrator SHOULD carry a checklist of its children, and `svacmz`'s own gate paragraph says "Do NOT respond to a future firing of that gate by deleting a parent's items". (b) Leave both verbatim: rejected, that is PR-001 unfixed and the parent's copy is the one a retirement ticks unperformed. (c) Move the backlog transitions onto `svacmz` myself: rejected, `svacmz` is outside this review's ledger and its Scope says "tests and evidence only"; offered to the maintainer as OQ-02 shape (c) instead. | `ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']` for why a parent item is unperformed; AGENTS.md "AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN" for why the checklist stays; `svacmz` Concern and E-01..E-04 for what is already owned. | yes |
| D-2 | Two obligations carry `- Carrier: s0gnha`. Escalate to the maintainer, or fix them? | FIX to `- Carrier-Declined:` with the measured reason recorded in the plan. | (a) Leave them and escalate: rejected, the workflow forbids asking the human what the repository answers, and this is answerable by running the shipped predicate. (b) Hand them to a child: rejected as dishonest, since no child revisits the parent's question about bundling spec amendments; each amendment is genuinely already carried by the child that raised it, which is what the decline states. (c) Point them at `yxfw4k`: rejected, it is a backlog item about the rescoring defect and does not own a spec-amendment question. | Measured with `check_engine.evaluate_carrier_obligation` against the live carrier index with `s0gnha` set `executed`: 2 of 5 obligations fail with "resolves only to a terminal/hidden artifact (executed); nothing revisits it". `_CARRIER_TERMINAL_STATUSES` contains `executed`; `carrier_severity_for_plan` returns `error` for `- Date: 2026-09-19` against `CARRIER_CUTOVER_DATE = "20260919"`; `_CARRIER_CHECKPOINTS = frozenset(("pre-transition",))`. Re-measured after the fix: 0 of 6 failing. | yes |
| D-3 | `dy9ymn` E-04 depends on a retry budget nothing consumes, and `xipfy1` owns that gap. Add `executed:xipfy1` to `dy9ymn`, or escalate? | ESCALATE as OQ-03 with `- Finding: PR-005`, and do NOT edit `dy9ymn` or add the edge. | (a) Add `- Item-Dependencies: executed:xipfy1` to `dy9ymn`: rejected on two grounds. `dy9ymn` is not in the Step 0 ledger, and `xipfy1`'s own review escalated an unresolved BLOCKER (its helpers need a `RunEngine` over a `ledger.jsonl` that no driver run writes), so the edge would point at a plan that may not be executable as written, converting a HIGH finding into a stalled dependency. (b) Let `dy9ymn` count attempts locally on the item: that may well be the right answer, but it contradicts `dy9ymn`'s own "introduce NO second retry knob" instruction and spec `25kzda` 5.5's precedence, so it is a design decision rather than a repair. (c) Treat it as no finding because spec 5.5 says the budget exists: rejected, the spec describing a budget is not the same as code spending it, and the executor meets the code. | `grep` for every `retry_budget` read across `agent_workflows/`: parsed at the flag row, resolved by `resolve_retry_budget`, frozen in `freeze_run_policy_flags`, and read back by nothing; `run_recovery.plan_retry`/`retry_budget_remaining` zero external callers; `integration_retry_limit` IS read back at `int(options.get("integration_retry_limit", ...))`, which is the contrast proving the absence is real; `xipfy1` `- Status: approved`, `- Blocks-Release: next`, 3 of 4 `Scope-Paths` shared with `dy9ymn`; its own history records the `RunEngine`/ledger BLOCKER as OQ-03. | yes |
| D-4 | E-03's backlog transitions are unperformed under a runner retirement. Author a fifth child, or record the hazard? | RECORD as OQ-02 with three shapes, and state the required manual step in the gate. Do not author a fifth child. | (a) Author a fifth child owning two `aw backlog set` calls: rejected as a unilateral choice, not as wrong. It spends a full agent turn on two commands, and the ceremony-versus-safety trade is a maintainer judgement; offered as shape (b). (b) Say nothing and rely on the operator noticing: rejected, that is the measured 2026-09-08 failure mode where a rollup retired a plan whose own items were never performed. (c) Delete E-03: rejected, the transitions genuinely must happen and `x7wfyx` carries a release gate that a wrong close would trip. | `ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`; the coverage gate's question is about work no child COVERS, so declared-on-parent work escapes it; `x7wfyx` `- Blocks-Release: next` with `- Status: open`; AGENTS.md's close-legitimacy rule and `graduated` requirement. | yes |
| D-5 | 30% of the Set's citations have already drifted. Repair all of them, or record the measurement? | REPAIR the parent's own single citation to a symbol anchor; RECORD the child measurements as a MEDIUM finding without editing the children. | (a) Repair all 22: rejected, 21 of them are in four child plans outside the Step 0 ledger, and the review scope rule forbids expanding it. (b) Escalate as blocking: rejected, drift misdirects an executor but changes no plan's design, and every drifted anchor I checked still resolves by symbol, so the information is recoverable at execution time. (c) Say nothing because the linter passes: rejected, `aw ipd lint` proves structure only and explicitly establishes nothing semantic, and `mzc019` exists because review cannot preserve a reference type that expires by construction. | Measured 22 of 74 distinct citations drifted (30%) between `f3da906e^` and HEAD, `skn8uk` 12 of 25; `runner_shared.py` grew 13844 -> 14082 lines; plan `mzc019` `- Status: reviewed` / `- Readiness: go-pending-approval` requires symbol-or-content anchors and records that a drifted offset misdirects rather than failing. | yes |
