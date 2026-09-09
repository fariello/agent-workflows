# Review: mint a fresh child setid on graduation and prevent a cross-type duplicate at every creation and move verb, child dw7i3m (Set setidhard)

- Subject-Id: dw7i3m
- Subject-Type: ipd
- Reviewed-At: 2026-09-09
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: no-go

## Round 1

Reviewed at HEAD `1444e4a6`. `aw ipd lint --phase author` CONFORMING before semantic review and
`--phase review-finalize` CONFORMING after every revision, so nothing in this round is structural.

DISCLOSURE: the same agent/model authored this plan, so this is a SELF-REVIEW. Its value therefore
rests on EXECUTING the plan's claims rather than re-reading them. Six things were run rather than
inspected: `check_collisions` was CALLED both ways on the live tree (which produced the HIGH finding
and the severity raise); `aw check` and `aw doctor` were both run and their setid-collision counts
compared; the F-8 group defect was REPRODUCED in a scratch repository with three fixture plans;
`compute_target_name` was called directly to isolate where the Order reset actually comes from; the
`Graduated-To` grep was run; and the full bare suite was measured. Five of those six produced
findings, and two of them (PR-401, PR-403) are cases where the plan's own description of a defect is
wrong in a way that would misdirect the executor.

READINESS IS `no-go` AND THAT IS NOT A CRITICISM OF THIS PLAN. Its verdict is clean and every finding
is fixed, but Order 00 carries TWO questions that are still `Blocking: yes` / `Status: open`, spec
`4w7d6s` is still `draft`, and this child's declared dependency (`Graduated-To`) does not exist in the
codebase yet. One of those open questions can CANCEL half this plan. A plan whose convention half a
pending maintainer ruling may delete is genuinely not ready to execute, so `no-go` is the honest
readiness even though the review found nothing unrepairable.

SCOPE: only this child was a candidate. Read as evidence: `check_engine.py` (`check_collisions`
`:832-916`, the `include_retired` parameter, the `seen_sets` map, the `:1760` caller), `doctor.py:530`,
`artifact_core.generate_id6`, `artifact_rename.py` (`compute_target_name` `:86`, `run_group_generic`
`:647-741`), `ipd_authoring.py`, `backlog.py`, `research_cmd.py`, `cli.py`'s `--order` registrations,
spec `4w7d6s` (I1/I3/I4/G1), siblings `yku4ga`/`drzbs9`/`bwgyum`, and backlog `sjsoqq`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | IN-SCOPE | A. Correctness; B. Security of a gate (a gate that fails OPEN) | called `check_collisions(Path('.'), include_retired=False/True)`: 40 vs 86 findings, `agentadhere` 0 vs 1; `check_engine.py:832-835`, `:1760`; `doctor.py:530`; `aw check` 40 vs `aw doctor` 81 | **THE RETIRED-FILTER TRAP IS LIVE INSIDE THE EXACT PREDICATE E-01 EXTRACTS FROM, NOT A PRECEDENT TO LEARN FROM, AND THE TWO SHIPPED COMMANDS ALREADY DISAGREE BY MORE THAN A FACTOR OF TWO.** The plan describes this as something "the id6 twin hit" and asks the executor to override the default "if" the helper has one. Measured: `check_collisions` takes `include_retired` as a third parameter DEFAULTING TO FALSE, and its two callers pass different values (`doctor.py:530` hardcodes True, `check_engine.py:1760` passes through, default False). Calling it both ways on the live tree yields 40 versus 86 `check.setid-collision` findings, and in the False branch `agentadhere` is INVISIBLE (0 hits) despite being owned by 7 executed plans plus 1 backlog item. End to end `aw check` reports 40 and `aw doctor` reports 81. This is HIGH rather than MEDIUM because the failure mode is a gate that FAILS OPEN: a predicate inheriting that flag answers "available" for a token seven executed plans own, so the mint proceeds and the gate silently permits the precise collision it was built to refuse. It also changes Order 01's target, since a sweep driven by 40 leaves the retired-only half in place. | C:Low; U:Low; S:Medium; F:High; Overall:Medium | FIXED | F-7 raised HIGH and rewritten with the measured numbers and both call sites. E-01 gained a paragraph stating the predicate must NOT inherit a caller's flag (bind True internally or take no such parameter, with a comment) and must state which number Order 01 targets. V-01 now demands the property be proven NUMERICALLY: paste both branch counts from the executor's own tree, paste the signature showing no inherited flag, and a predicate agreeing with the False branch is a FAILED validation. Required-tests and Step 0 now require BOTH `aw check` and `aw doctor` per-rule counts. |
| PR-402 | HIGH | UNDER-SCOPE | G. Executability (an unresolved blocking gate stated as a caution) | Order 00 OQ-01 and OQ-02 both `- Blocking: yes` / `- Status: open`; spec `4w7d6s` `- Status: draft`; `grep -rn "Graduated-To" agent_workflows/` returns nothing; `bwgyum` is `reviewed` in `pending/` | **THE PLAN TREATS TWO LIVE BLOCKING QUESTIONS AND AN UNBUILT DEPENDENCY AS ADVICE ("do not begin task group 3 on a guess") RATHER THAN AS A HARD STOP, AND ITS OWN THREE RESOLVED OQs INVITE THE MISREADING.** Verified: both of Order 00's questions are still open and blocking, the spec they depend on is still `draft`, `Graduated-To` exists nowhere in `agent_workflows/`, and Order 02 has not executed. So E-04 is not merely risky to guess at, it is currently UNPERFORMABLE, and OQ-02's answer could delete it outright. Meanwhile this child's own OQ-01..OQ-03 all read `resolved`, so a reader skimming the open-questions section sees a clean plan. The plan needed to separate the half that is safe under any ruling (E-01..E-03, cross-type prevention, which is I3 and is not what OQ-02 questions) from the half a ruling can cancel (E-04..E-05). | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The gate gained two paragraphs: one stating both inherited questions are open and blocking with the lint consequence, that this plan's own resolved OQs are NOT the gate, and the split between the safe and cancellable halves with the instruction to do prevention and STOP; one recording that `Graduated-To` does not exist and the dependency is genuinely unmet. E-04 gained the same check up front. V-04 now requires pasting Order 00's OQ-02 RESOLVED with its answer quoted, and declares performing E-04 while it is open a FAILED validation. |
| PR-403 | MEDIUM | IN-SCOPE | A. Correctness (a measured defect described wrongly) | reproduced in a scratch repo: `20260908-oldset-{01,02,03}` -> `20260908-newset-{00,01,02}`, front matter Orders 0,1,2; `artifact_rename.py:682`, `:741`; `compute_target_name` preserves order when `new_order is None` | **F-8's DESCRIPTION IS WRONG IN A WAY THAT WOULD MAKE THE EXECUTOR MISS THE REAL SYMPTOM, AND THE PLAN ASKS AN EXECUTOR TO AVOID WORSENING A BEHAVIOR IT MIS-STATES.** The plan claims `aw group ... --rename --apply` without `--order` "reset the Order to `00` on all four of this Set's plans, including three children, silently producing three Order-0 children". Reproduced: it RENUMBERS the group sequentially from zero in selector order, so three plans at Orders 1, 2, 3 become 00, 01, 02. Exactly ONE artifact per call lands on Order 0, so the claimed three-Order-0-children outcome cannot come from one group call. Also localized the mechanism, which the plan does not: it is `run_group_generic`'s `order_val = (start_order + i) if start_order is not None else None` plus the metadata write, NOT `compute_target_name`, which was called directly and PRESERVES the order when `new_order` is None. That matters because the executor is told to edit this file and not disturb the behavior, and a wrong mental model of where it lives is how it gets disturbed. It also means the separately-filed report would be triaged against a defect that does not reproduce. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-8 rewritten with the reproduction, the corrected renumbering description, and the localized mechanism. The Concern's hazard paragraph and the Step 0 convention both corrected. The deferred-scope entry now says to report the renumbering rather than a blanket reset. V-03 now requires a before/after fixture group run showing the SAME Orders, so "did not change it" is proven rather than asserted. |
| PR-404 | MEDIUM | IN-SCOPE | D. Anti-regression (a wrong named baseline and stale criteria) | `python3 -m pytest` -> `1 failed, 5919 passed, 3 skipped, 2 xfailed`; the failure is the environmental `test_reporting_contract` case; `aw check` -> 238 findings | Two validation figures the plan states as criteria are stale: the suite baseline is `1 failed, 5919 passed`, not `1 failed, 5648 passed`, and `aw check all` reports 238 findings, not 98. The plan correctly says never to compare totals, which limits the damage, but it also names an expected failure without identifying it, and the real one is environmental (a gitignored local `opencode-recovery/` dump), so it is machine-specific and will not reproduce elsewhere. An executor inheriting a wrong expected-failure can excuse a genuine regression as the known one. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06, required-tests and Step 0 all carry the re-measured figures, the environmental cause, and the instruction to measure the executor's own baseline and compare node ids. |
| PR-405 | LOW | IN-SCOPE | A. Correctness (an inventory figure overstated) | `grep -rln "^- Set: agentadhere" .aw/records/` -> 7 plans + 1 backlog | The `agentadhere` case is cited twice as "eight `executed` plans"; it is 7 executed plans plus 1 backlog item (the backlog item being the cross-type half that makes it a collision at all). The argument is unaffected, but the number appears in E-01 and V-01 as concrete evidence an executor is told to reproduce, so a wrong count invites a false negative when they measure 7. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in E-01, F-7 and V-01 to 7 executed plans plus 1 backlog item. |
| PR-406 | LOW | IN-SCOPE | G. Executability (moving inventory figures used loosely) | this plan cites 21 and 29; Order 00 OQ-03 cites 30; `aw check` shows 40 (86 retired-inclusive) | The plan quotes three different inventory sizes across its own prose (21 existing collisions, 29 live findings) and its parent quotes a fourth (30), while the live count is 40 or 86 depending on the retired flag. None of these is used as a pass criterion, so this is LOW, but a reader cannot tell which number is authoritative, and PR-401 shows the discrepancy is partly mechanical rather than just temporal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 now records all four figures with the reason they differ and instructs re-measurement, noting the CONVENTION claim (21 of 21 graduations reused the setid) is what the finding actually rests on and is unaffected. |

CONFIRMED SOUND, AND THIS PLAN'S SPEC READING AND SCOPE DISCIPLINE ARE ITS STRONGEST PARTS. Every
normative citation was checked against the spec text and all are accurate: I3 really does name those
five verb families and really does say "consulting the collision predicate the way id6 minting already
prevents id6 reuse" (`4w7d6s:68-71`); I4 really does require the specific setid-collision message plus
the `aw group ... --set <new>` recovery rather than a generic error (`:72-78`); G1 really does mandate a
fresh child setid (`:85`). The id6 precedent is exactly as described: `generate_id6(existing)` takes the
taken set from its caller and loops internally (`artifact_core.py:58-66`), so it is the right model and
OQ-02's reasoning about why looping is correct there and wrong for setids is sound. F-1 verified: a
search of `ipd_authoring.py` finds no setid-collision consult at all, so prevention is genuinely
unbuilt. The `check_collisions` internals are as described (`seen_sets` map, `prev_type != record_type`),
so E-01's "do not write a second detector" has a real target. Every one of the seven declared
`Scope-Paths` exists and each justification is correct about what that file holds, including the two
creation verbs (`backlog.run_new:340`, `research_cmd.plan_new_comparison:211`/`run_new_comparison:657`)
and the move machinery (`compute_target_name:86`, `run_group_generic:647`). The deliberate decision NOT
to declare `.aw/records/backlog/README.md` is correct and verified: Order 02 declares it three times in
its own `Scope-Paths`, so a second declaration really would collide at the finalize scope gate. The
three own OQs are all well-reasoned, and OQ-03's false-positive analysis (within-type clustering must
stay legal) is the right call and is backed by the existing checker's own type comparison.

WHAT THIS ROUND CHANGED ABOUT THE PLAN'S SHAPE. Nothing about WHAT to build, and two important things
about what the executor must know before building it. The first is PR-401: this plan is a GATE, and the
one property that decides whether a gate is worth anything is whether it can fail open. The plan treated
the retired-artifact blindness as a historical lesson to be careful about; calling the function proved
it is live, defaulted to the unsafe value, and already produces two shipped commands that disagree 40
against 81. That converts a "be careful" note into a hard constraint on the predicate's signature, and
V-01 now proves it numerically instead of accepting an assertion. The second is PR-402: this plan is
half prevention and half convention change, and only the convention half is hostage to an open
maintainer ruling. The plan knew that and said so, but stated it as advice while its own resolved
open-questions section made the plan look clear to execute; the split is now explicit, with the
instruction to build prevention and STOP rather than guess. The rest is measurement hygiene: three
stated figures were stale and one described defect did not reproduce as written, which for a plan whose
executor is told to avoid worsening that very defect is worth the separate finding.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The extracted predicate could take `include_retired` like its parent, or refuse the parameter. Which? | Do not inherit a caller's flag: bind it True internally, or take no such parameter, with a comment saying why. | (a) Accept the parameter and document that callers should pass True; rejected because that is exactly the shape that already produced the 40-versus-81 divergence between `aw check` and `aw doctor`, and a mint site that forgets it gets a gate that fails OPEN on the `agentadhere` shape. (b) Change `check_collisions`'s own default to True; rejected as out of scope and behavior-changing for every existing caller, and it would alter `aw check`'s reported finding count, which Order 01's sweep is measured against. | Measured `check_collisions(Path('.'), include_retired=False)` -> 40 findings with `agentadhere` invisible, versus `True` -> 86 with it reported; `doctor.py:530` hardcodes True while `check_engine.py:1760` passes through; identity questions must see terminal artifacts per the plan's own F-7. | yes |
| D-2 | Should readiness be `go-pending-approval` (clean verdict, all findings fixed) or `no-go`? | `no-go`. | `go-pending-approval`; rejected because the readiness vocabulary reserves `no-go` for a genuine not-ready condition and this plan has three: two inherited `Blocking: yes` questions still open on Order 00, a `draft` spec, and a declared dependency whose subject (`Graduated-To`) does not exist in the codebase. One of those questions can CANCEL task group 3, so recording `go-pending-approval` would tell automation this plan is cleared to run when half of it may be about to be deleted. | Order 00 OQ-01/OQ-02 both `- Blocking: yes` / `- Status: open`; spec `4w7d6s` `- Status: draft`; `grep -rn "Graduated-To" agent_workflows/` empty; `bwgyum` `- Status: reviewed`; the workflow's own definition of NO-GO as "any open question". | yes |
| D-3 | F-8 does not reproduce as described. Correct the description, or drop the finding? | Correct it, keep it, and add a before/after fixture proof to V-03. | (a) Dropping F-8 as unreproducible; rejected because the underlying behavior IS real (Orders 1,2,3 became 00,01,02) and the executor is told to edit that very file, so removing the warning would remove the only thing telling them not to disturb it. (b) Widening scope to fix it here; rejected because the plan's own deferral reasoning is right (a different surface with its own tests, inside a gate plan), and the maintainer has already been told about it separately. | Reproduced in a scratch repo; `run_group_generic:682`/`:741` is the mechanism and `compute_target_name` was called directly to prove it preserves the order when `new_order is None`. | yes |
| D-4 | This plan's three OQs are all `resolved`; should any be re-opened given the corrections? | No, leave all three resolved. | Re-opening OQ-02 (what if the derived fresh setid is also taken?) in light of PR-401; rejected because that question is about the SUGGESTION's behavior when a candidate is taken, and PR-401 concerns whether the availability check can SEE a taken token. The corrections strengthen the premise those answers rest on rather than changing the answers: a predicate that sees terminal artifacts makes OQ-02's "say so and stop" more often reached, not less correct. | The three OQ resolutions read against the corrected F-7; `generate_id6`'s loop-internally design is what OQ-02 contrasts against and is unchanged. | yes |
