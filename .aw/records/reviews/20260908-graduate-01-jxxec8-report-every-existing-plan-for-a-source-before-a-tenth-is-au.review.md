# Review: report every existing plan for a source before a tenth is authored, child jxxec8 (Set graduate)

- Subject-Id: jxxec8
- Subject-Type: ipd
- Reviewed-At: 2026-09-09
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `7fc7d449`. `aw ipd lint --phase author` CONFORMING before semantic review and
`--phase review-finalize` CONFORMING after every revision, so nothing in this round is structural.

DISCLOSURE: the same agent/model authored this plan, so this is a SELF-REVIEW. Its value therefore rests
on EXECUTING the plan's claims rather than re-reading them. SIX things were run rather than inspected:
the whole plans tree was re-walked parsing both source fields plus `- Status:` and `- Set:`; the SPECS
tree was walked the same way (which produced the round's one HIGH finding); every caller of
`find_from_backlog_plans` and `find_from_backlog_artifacts` was grepped and the call sites read;
`artifact_core.drift_exit_code` and `check_engine.RULE_REGISTRY` were read and their severities counted;
the full bare suite was run; and `aw check all`'s per-rule counts were parsed from the `--agent`
diagnostics array.

WHAT SURVIVED AND WHAT DID NOT. This plan is unusually well grounded, and most of what review checked
held: the dual-link measurement (F-8) reproduced exactly, the five named plans confirmed; the severity
trap (F-5) is real and the engine documents it in its own comment; the coordination finding about
`bwgyum` (F-9) is correct and the orchestrator already carries the constraint and CID-7; the corrected
suite baseline (Step 0) matched to the node id; and the `f1sw71` status correction (F-10) is right. What
did NOT hold is a scope decision the plan never surfaced as a decision: the view was PLANS ONLY.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | UNDER-SCOPE | A. Correctness; D. Anti-regression (a fixed defect about to be reintroduced) | walked `.aw/records/specs` parsing both fields: 5 specs carry a source link (`c4gd2h`->`kjzlgw`, `7ckptx`->`vqv9im`, `6m4kow`->`25kzda`, `77tr3o`->`kxkc04`, `2vev8j`->`ms06pi`); `check_engine.py:1947-1960`, `:2959`; `oc_runipd.py:1153-1158` | **THE VIEW WAS SCOPED TO PLANS ONLY, WHICH WOULD REINTRODUCE A DEFECT THIS REPOSITORY ALREADY FIXED AND WOULD BE SILENT ON A CARRIER OF EVERY EXAMPLE CLUSTER THE PLAN USES TO ARGUE ITS CASE.** A SPEC is an equally valid graduation carrier: `find_from_backlog_artifacts` exists verbatim because "the HANDOFF route previously scanned plan IPDs ONLY, so a spec-first graduation ... was invisible and its backlog item could never legitimately close", and `check_from_spec_dangling` already reuses BOTH `_iter_plan_ipds` and `_iter_spec_records` for the same reason. Measured, FIVE specs carry a source link and ALL FIVE sit on clusters this plan names: `kjzlgw`, `vqv9im`, `25kzda`, `kxkc04`, `ms06pi`. The motivating spec `6m4kow` is itself a CARRIER of backlog `25kzda`, so a plans-only index answers "what already exists for `25kzda`" with nine plans and omits the spec that addresses it. That is precisely the already-addressed case the maintainer asked to be shown, and it would pass every plans-only test by construction. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | Scope, Concern, E-01, E-03, E-04, E-05, Step 0, the deferral list, the scope fence and V-01/V-03/V-04/V-05 all now cover PLANS AND SPECS. E-01 gained the measurement and the `bklgrad` citation; E-04 gained a second live assertion (`6m4kow` under `25kzda`, `77tr3o` under `kxkc04`) and a spec-only fixture; E-05 gained mutation 3 (read `_iter_plan_ipds` only, prove both new assertions fail). F-11 added HIGH. `Scope-Paths` did NOT widen: both spec helpers already live in `check_engine.py`, which is recorded in the scope check. |
| PR-602 | MEDIUM | IN-SCOPE | C. Architecture (a reuse instruction weak enough to satisfy by rewriting) | `find_from_backlog_artifacts` at `check_engine.py:1947`; its caller comment at `oc_runipd.py:1153-1158`; the single-pass index at `check_engine.py:2256-2262` | **A DIRECTLY REUSABLE SHARED LOOKUP ALREADY ANSWERS HALF THIS QUESTION AND THE PLAN NEVER NAMES IT.** `find_from_backlog_artifacts(repo, id6)` already returns every plan AND spec carrying `From-Backlog: <id6>`, and the runner calls it under an explicit comment: "THE ONE SHARED LOOKUP ... A second implementation here would be the same divergence defect this repository keeps hitting, so there is deliberately no local scan." The plan said only "reuse the existing readers", which an executor can satisfy by reusing a REGEX while still writing a third traversal of the edge, the very drift F-9 raises against another Set. The performance shape is also already solved in-tree: `:2256-2262` builds a single-pass index precisely because per-item calls "re-walked the complete plans tree per item". | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now names the symbol, quotes the ONE-SHARED-LOOKUP precedent, and requires that a NEW function be justified in the plan and placed beside its siblings. The single-pass-index precedent is cited for the whole-corpus shape. Step 0 records both. V-01 requires naming which symbol was consumed. F-12 added. |
| PR-603 | MEDIUM | IN-SCOPE | F. UX (an unqualified reassurance that can cause the harm the plan prevents) | the index's input is the `From-*` bullet, not the work; 106 of the tree's sources carry a link; OQ-02's recommendation | **THE VIEW'S "NOTHING EXISTS" ANSWER IS THE ONE OUTPUT THAT CAN CAUSE THE DUPLICATION THIS PLAN EXISTS TO PREVENT, AND IT WAS UNQUALIFIED.** The reverse index reads only the two `From-*` bullets, so a source addressed by work carrying no such link is invisible to it. OQ-02 recommends an explicit affirmative "nothing yet, proceed", which is the right UX and, without a stated coverage boundary, is a stronger claim than the data supports: it reads as "no work exists" when it means "no LINKED work exists". E-03 already required honesty about three cases but not about the view's own input. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires the output to name the artifact types searched AND to qualify what its silence proves. V-03 requires the coverage-boundary sentence be pasted. A new deferral entry states that unlinked work is out of scope with the reason. F-13 added. |
| PR-604 | LOW | IN-SCOPE | E. Testing (a correct constraint with an unnamed precedent) | `artifact_core.py:405-415`; `check_engine.py:188-190`, `:343`; registry counted 24 error / 6 warning / 2 info of 32 | F-5's severity reasoning is EXACTLY right and review confirmed every part of it, but the plan gave the executor no precedent to copy and no mention that a rule also owes an INVARIANT id. Measured: `drift_exit_code` returns 1 if any severity `!= "info"`; the engine documents that misreading in its own comment; `_DEFAULT_RULESPEC` is `error` with an EMPTY invariant, so an unregistered rule silently errors AND silently drops its invariant trace; and two `info` rules already exist (`check.ipd-draft-ready-to-review`, `check.stale-index-missing`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and Step 0 now cite the exact call sites, name both `info` precedents with the measured severity distribution, and require a deliberate invariant id or an explicit empty-with-reason (citing `check.review-finding-unescalated`'s precedent). V-02 requires the invariant id and the copied precedent be stated. F-14 added. |

CONFIRMED SOUND, AND THIS PLAN'S EVIDENCE DISCIPLINE IS ITS STRONGEST FEATURE. Every measurement review
could re-run reproduced. The dual-link finding (F-8) is exact: `84j8d7`, `5942n7`, `ueg5cf` and `pgq326`
each carry `Backlog: kxkc04` plus `Spec: 77tr3o`, and `h0zljh` carries `Backlog: vqv9im` plus
`Spec: 7ckptx`, so a first-match read really would drop five edges and under-report two clusters. The
single most valuable thing in the plan is its refusal to implement a `count > 1` rule (F-4), and the
measurement backs it emphatically: the largest cluster is nine plans of correct decomposition, so a
uniqueness rule would flag 24 legitimate clusters and teach readers to ignore it. The severity analysis
(F-5) is verified to the line. The `bwgyum` coordination finding (F-9) is real and already carried by the
orchestrator as a symmetric constraint plus CID-7, which is the right place for it. The `f1sw71`
correction (F-10) is right (`graduated`, not open) and the reasoning that the exclusion is UNCHANGED
because the gap is unbuilt is correct. Step 0's suite correction is right to the node id, including that
`test_orchestrator_retirement.py` now passes. The derive-never-pin rule is the plan's own best insight
and review watched it prove itself a third time: 71 plans in the item, 125 bullets when authored, 171
bullets over 166 files across 106 sources one day later. And the decision to implement the item's
"minimum useful version" is correctly justified rather than convenient, because the third case genuinely
has no mechanism.

WHAT THIS ROUND CHANGED ABOUT THE PLAN'S SHAPE. One thing, and it is a scope correction rather than a
defect in the plan's reasoning: the view now covers SPECS as well as plans. That matters more than its
size suggests for three reasons. It is a REGRESSION, not a gap: `bklgrad` `v58bvy` E-06 already fixed
exactly this omission on the handoff route, and a plans-only reverse index walks back into it. It is
INVISIBLE to the plan's own test plan, since every plans-only assertion passes on a plans-only
implementation, which is why a third mutation was added rather than only a fixture. And it lands on the
plan's own motivating example, because `6m4kow` is both the source of three plans and a carrier of
`25kzda`, so the one cluster the plan uses to argue its case is the one where a plans-only view is
silent. The remaining three findings are smaller: name the shared lookup the plan gestured at, qualify
the view's silence so its most frequent answer is not over-read, and give the severity constraint a
precedent to copy.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The view was plans-only. Widen it to specs here, or file a follow-on child? | WIDEN IT HERE, with a live assertion, a spec-only fixture, and a dedicated mutation. | (a) A follow-on child, rejected because the omission is a REGRESSION of a fix already shipped (`v58bvy` E-06), and shipping the known-incomplete view first would make the guard silent on a carrier of every example cluster it cites, including its own motivating case. (b) Note the limit in E-03's honesty statement and ship plans-only, rejected because "we did not look at specs" is not a limit of the mechanism, it is a choice, and the mechanism to look already exists and costs no new `Scope-Paths` entry. | 5 specs carry a source link, all 5 on named clusters; `check_engine.py:1947-1960` states the plans-only defect verbatim; `check_from_spec_dangling:2959` already reuses both iterators; `_iter_spec_records` and `find_from_backlog_specs` already live in the declared path. | yes |
| D-2 | `find_from_backlog_artifacts` exists. Mandate consuming it, or leave the shape to the executor? | Mandate NAMING it and justifying any new function, but allow a single-pass index with a stated reason. | (a) Mandate consuming it unconditionally, rejected because a per-source call re-walks the tree, which `check_engine.py:2256-2262` already worked around with a single-pass index, so a hard mandate would force the known-slow shape. (b) Leave "reuse the existing readers" as written, rejected because it is satisfiable by reusing a regex while writing a third traversal, which is the exact drift F-9 raises against another Set. | `oc_runipd.py:1153-1158`'s ONE-SHARED-LOOKUP comment; the single-pass index and its stated reason at `:2256-2262`; F-9's own P8 argument. | yes |
| D-3 | Should the zero-result answer carry a coverage boundary, given OQ-02 recommends an affirmative message? | Yes: require the output to name the types searched and qualify what silence proves. | Leaving OQ-02's affirmative message unqualified, rejected because the index's input is the `From-*` bullet rather than the work, so "nothing yet, proceed" overstates the evidence, and a false all-clear from a duplication guard is worse than no guard. Note this does NOT reverse OQ-02's recommendation, which review agrees with; it qualifies it. | The index reads only the two bullets; 106 sources carry a link; the plan's own F-6 sets the precedent of stating an undetectable case rather than faking it. | yes |
| D-4 | Readiness: `go-pending-approval` or `no-go`? | `go-pending-approval`. | `no-go`; rejected because this plan has NO genuine not-ready condition: both its open questions carry `Blocking: no` with reasons review verified (each completes under either answer), `- Item-Dependencies: none`, every symbol it depends on EXISTS today (unlike its sibling Set's `Graduated-To`), the lint conforms at `review-finalize`, and every finding is FIXED. The `bwgyum` coordination is a sequencing obligation carried by the orchestrator, not a blocker on this child. Unlike `setidhard`, no maintainer ruling can cancel this work. | `aw ipd lint --phase review-finalize` exit 0; both OQs `Blocking: no`; `find_from_backlog_artifacts`, both iterators and both regexes all present at HEAD; the workflow's definition of GO - PENDING HUMAN APPROVAL as the clean-bar readiness awaiting sign-off. | yes |
| D-5 | Should OQ-01 (rule versus read surface) be escalated to blocking, since it changes what is built? | No, leave `Blocking: no`. | Escalating it, rejected because E-02 requires a read-only surface answering the source-selector question under BOTH answers, so the deliverable exists either way and the choice is additive (a rule is a second surface over the same index). Its owner line already escalates to the maintainer for the one case that needs a human, a new rule severity. Review strengthened the guardrails (`info` only, invariant id, exit-code proof) rather than the gate. | The plan's own OQ-01 rationale, verified: both shapes satisfy the item's minimum version; `RULE_REGISTRY` shows `info` is a supported, precedented severity. | yes |
| D-6 | The plan cites many line numbers. Leave them, or add a re-locate mandate? | Keep them as orientation and extend the existing re-locate mandate to name every new symbol. | Removing the line numbers, rejected because they are load-bearing evidence for findings a reviewer must be able to check, and the plan already carries a RE-LOCATE BY SYMBOL instruction; the fix is to widen that instruction to the symbols this round added. | The gate's existing re-locate paragraph; every cited line verified at review round 2 and stamped as such. | yes |
