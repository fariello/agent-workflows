# Review: pin the approval-gate corpus test to named id6s, child h3bjue (Set gatepin)

- Subject-Id: h3bjue
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `72d1b018`. Structural preflight `aw ipd lint --phase author` conformed (clean, 0 findings)
before semantic review, and `--phase review-finalize` conformed after the revisions.

DISCLOSURE: authored in the same repository and by the same model family as the plan, so treat this as a
near-self-review and worth less than an independent one.

THE DIAGNOSIS IS EXACTLY RIGHT AND THE RESTRAINT IS EXEMPLARY. `test_no_pending_plan_is_refused_on_a_verdict_today`
really does assert something false whenever the gate works; the correct pattern really does exist twice in the
same class; refusing to delete the test or to edit `32ij2j` is correct and the plan says so in capitals. It
also corrected three of its own backlog item's claims, including proving from commit `31169afd` that the
sibling instance was DELIBERATELY rewritten rather than self-healed by drift, which is a stronger precedent
for the fix than the item had. Every structural claim re-verified: `67 passed`, `32ij2j` in `superseded/` via
`32e4b74f` with its REJECT record intact, the renamed orchestrator test at `:890` carrying the cited
reasoning, `112 passed` in that module, `_find` and both siblings at the cited lines, and all eight sibling
id6s resolving from the dispositions named.

TWO FINDINGS CHANGE THE WORK, and both came from measuring what the plan PROPOSED rather than what it
diagnosed. The diagnosis was verified in minutes; the proposed remedy did not survive the same treatment.

FIRST, THE REPLACEMENT PROPERTY CANNOT FAIL. Both the plan and backlog `yw6759` recommend "no plan whose
newest review record contains an APPROVING verdict token is refused". `newest_verdict` computes its polarity
as `_, polarity = classify_verdict(message)` and returns that value, so the property compares a function to
its own internal call. It holds across all 608 corpus plans because it must, not as evidence about the gate.
Shipping it would replace a test that is false whenever the gate works with one that is true whenever
anything happens, which is strictly worse: the first fails loudly. A falsifiable replacement was found and
verified in BOTH directions and is now specified in the plan.

SECOND, E-02 ALONE IS A NET LOSS OF COVERAGE. The assertion being removed parses 104 real, human-authored
review records on every suite run (measured: 70 positive, 15 neutral, 19 unparseable). E-02 replaces that
with a handful of pinned ids, and E-03 as written explicitly permitted answering "no corpus property
wanted". Those two steps together would have repaired the false-by-construction defect by deleting the
class's stated reason for existing. E-03 is now a build rather than a decision, and OQ-01 is resolved
accordingly rather than left with the maintainer, because two measurements settle it.

There is an irony worth naming, because it is the plan's own lesson: this plan exists because a test was
shipped that could not fail in the direction it claimed to check, and its proposed fix had the same defect
in the opposite direction. The gate added to the plan is that every new assertion must be demonstrated
FAILING before it is demonstrated passing.

Seven findings, all FIXED in place, no deferrals. E-item and V-item counts unchanged at five each: every fix
belonged inside an existing item, and E-03 changed from a decision to a build without splitting. OQ-01
resolved from evidence; OQ-03 strengthened; OQ-02 left with E-04 as the plan intended. No product code was
modified.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | E. testing; A. correctness | `agent_workflows/plan_readiness.py:414-416`; property verified to yield 0 violations over 608 plans by construction; synthetic no-token record reaches `NEGATIVE` with no `REJECT` | **The corpus property the plan recommends is UNFALSIFIABLE, so shipping it would leave the class with no working real-corpus check.** "No plan whose newest review record contains an APPROVING verdict token is refused" asks whether `classify_verdict`'s answer agrees with `newest_verdict`'s, and `newest_verdict` DERIVES its answer from that same call and returns it. The antecedent forces the consequent by one line of code, for any input. Its clean pass over the whole corpus is a property of its form. A test that cannot fail is worse than the one being removed, which at least fails loudly | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-03 rewritten from "decide whether" to BUILD, with the token property explicitly forbidden and the reason cited. Specified instead, verified falsifiable at review: every plan whose newest review record parses `NEGATIVE` must literally contain `REJECT`, which can fail via the no-verdict-token plus negative-readiness route (`:417-420`), survives a legitimate REJECT by construction, and whose failure mode is the real false-refusal class (a reviewer who records a readiness but omits the verdict token is silently refused). V-03 now demands BOTH directions and fails a passing-only validation. New F-15, F-16 |
| PR-002 | HIGH | UNDER-SCOPE | E. testing; D. anti-regression | polarity census over `pending/`: 104 plans, 70 positive, 15 neutral, 19 `None`; class docstring `tests/test_plan_readiness.py:770` | **E-02 alone is a net loss of coverage, and E-03 was permitted to decline the replacement.** The removed assertion exercises `newest_verdict` against 104 real review records every run; E-02 substitutes a handful of pinned ids. With E-03 answering "no", which the plan expressly allowed, the outcome is 104-plan coverage traded for N-plan coverage. That repairs the false-by-construction defect by deleting the value the class exists for ("a fixture-only suite can pass while the gate misjudges reality") rather than by fixing the proxy | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern block records the measured coverage and names the risk. E-02 now states plainly that it is a reduction and not the whole fix. E-03 is mandatory and OQ-01 is resolved to YES with the cost objection measured and answered (the module runs in 0.24s reading those files today). Proposed-changes gains a note that neither half alone is the repair. V-05 requires the net coverage position stated in one sentence. New F-14 |
| PR-003 | MEDIUM | IN-SCOPE | E. testing | 19 of 104 pending plans parse to polarity `None`; sibling assertion is `assertNotEqual(polarity, NEGATIVE)` (`:786-787`) | **A pinned id6 with `None` polarity would assert nothing while looking like coverage.** OQ-03's rule says pin ids whose polarity is "KNOWN AND POSITIVE", but the sibling's assertion passes trivially for `None`, and a large fraction of the corpus parses that way. An executor picking an id by convenience rather than measurement could satisfy the new test vacuously, which is the same defect class this plan treats as a bug and which the siblings' checked-counter exists to prevent | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | OQ-03 gains the measurement and the requirement that "known" means MEASURED. E-02 forbids pinning a `None`-polarity id and requires the measured polarity recorded per id, and prefers terminal dispositions with the reason (the sibling's three all sit in `executed/`, verified). V-02 requires the measured polarity pasted per id and explicit confirmation none is `None`. New F-17 |
| PR-004 | MEDIUM | IN-SCOPE | E. testing; D. anti-regression | briefing `1 failed, 5648 passed`; plan `5859 passed`; review `1 failed, 5958 passed, 3 skipped, 2 xfailed`; failure walks gitignored `opencode-recovery/` (1746 files) | **The baseline has now been recorded wrong three times, and the current failure invites destroying another party's data.** The plan's instruction to state observed counts rather than quote a figure is correct and was kept; what was missing is that the live failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, walking 189 files in a gitignored directory belonging to a co-worker. An executor reconciling three disagreeing baselines against one unexplained failure has an obvious wrong move available | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05, required-tests and V-05 all name the real failure with its mechanism and record all three stale baselines as the reason to measure your own. A prohibition on deleting, moving or modifying `opencode-recovery/` is added in E-05, required-tests and the gate. Bare-run flag rule added. New F-18 |
| PR-005 | LOW | IN-SCOPE | Evidence accuracy | 104 pending plans measured; plan says 92 | **The pending count drifted, and it is load-bearing in the execution contract.** The figure appears as the justification for building fixtures rather than mutating the live tree, so a stale number weakens the instruction it supports | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in E-01 and the execution contract; recorded as F-19. The "18 approved plans executing in live runs" claim was not independently verifiable at review and is now stated without the unverified count |
| PR-006 | LOW | IN-SCOPE | Evidence accuracy | `ls tests/test_run_viewer_isolation.py` -> absent; `utwr6y` `to-review`, declares it | **F-13's observation about `utwr6y` needed confirming rather than carrying forward.** The plan reports its E-03 file as missing; that is still true at review, and `utwr6y` is `to-review` and declares the path. Worth confirming because E-04's decision rests on `utwr6y` supplying an inventory rather than a guard | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-13 updated with the confirmation and the method |
| PR-007 | LOW | IN-SCOPE | project rules | `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md` is the single `Status: planned` record | **The `Blocks-Release: next` target was asserted but not resolved.** The gate asks a reviewer to weigh the release gate deliberately, which requires knowing which release it resolves to; `next` resolves to `f33nrj` | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now names the resolved release and restates the latency measurement (zero of 104 pending plans currently parse `NEGATIVE`, so the assertion is vacuously true rather than merely passing), with the recurrence argument sharpened and the decision left to the maintainer |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The recommended corpus property is unfalsifiable (PR-001). Forbid it and leave E-03 to find another, or specify a replacement? | Specify the replacement, verified in both directions before writing it into the plan: every `NEGATIVE`-parsing newest record must contain `REJECT` | Forbid the token property and let the executor design one (rejected: the plan, the backlog item and this reviewer's first reading all found the tautology plausible, so an executor is likely to land on it again or on something equally circular; a verified alternative costs one paragraph); drop the corpus property entirely (rejected: that is PR-002, it removes the class's stated value); keep the token property with a caveat (rejected: a test that cannot fail is not improved by a comment saying so) | `plan_readiness.py:414-416` for the tautology; `:417-420` for the second route to `NEGATIVE`; synthetic record verified to violate the replacement; 7 of 608 plans parse `NEGATIVE` and all contain `REJECT` | yes |
| D-2 | E-03 was a decision that could answer "no" (PR-002). Escalate the cost/benefit to the maintainer as OQ-01 asked, or resolve it? | Resolve it to YES and convert E-03 into a build | Leave OQ-01 open for the maintainer (rejected: it was posed as cost/benefit, but the cost was measurable and small (the module reads those 104 files today in 0.24s) and the benefit is the class's own stated premise, so the repository answers it and asking would spend a human turn on a fact); answer NO and accept named-id6 coverage only (rejected: makes the plan a net loss, which is PR-002) | polarity census; `tests/test_plan_readiness.py:770`; measured module runtime | yes |
| D-3 | Should review pick the concrete id6s for E-02, given PR-003 shows a wrong pick asserts nothing? | No. Keep OQ-03's rule-not-list resolution and add the measurement requirement instead | Name three ids now (rejected: a list authored at review ages exactly as OQ-03 argues, and the sibling's own docstring shows ids migrating between dispositions; the durable fix is "measure the polarity you pin", not "pin these three"); leave "known and positive" unqualified (rejected: 19 of 104 plans parse `None` and would satisfy the assertion vacuously) | OQ-03's own reasoning; the 19-of-104 census; `:786-787` assertion form | yes |
| D-4 | Three baselines disagree and the live failure walks a co-worker's gitignored directory (PR-004). Correct the number, or add a prohibition? | Both: record all three stale figures as the reason to measure your own, and prohibit touching `opencode-recovery/` in three places | Just update the number (rejected: it will be stale again within days, which is the pattern; the durable instruction is measure-your-own plus recognize-this-failure); ask for the directory to be cleaned (rejected outright: destroying another party's uncommitted work in a shared checkout) | Three recorded baselines; measured failure and its mechanism; AGENTS.md shared-checkout rule | yes |
| D-5 | The backlog item still recommends the unfalsifiable property. Correct the item too? | No. Require E-03 to state in the plan that the token property was rejected and why, so the correction travels with the work | Rewrite the item's body (rejected: it records what was believed when filed, and `/plan-review` edits the plan in scope, not another artifact's history); say nothing (rejected: the item outlives this plan and the next reader would reintroduce the tautology from it in good faith) | The item's own graduation note is where corrections belong; the plan carries `- From-Backlog: yw6759` | yes |
