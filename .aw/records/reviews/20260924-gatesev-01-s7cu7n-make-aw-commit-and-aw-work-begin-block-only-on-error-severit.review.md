# Review findings: plan s7cu7n

- Subject-Id: s7cu7n
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `gatesev`, the sole child, graduated from backlog `7a53rm`
(`Blocks-Release: next`, `Work-Kind: bug`, `Priority: high`). Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review, and
`--phase review-finalize` conforms after the revisions, so nothing below is structural. The plan file
was committed and byte-identical to the lane input, so no pre-review snapshot was needed. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check and its bounded repair loop do not apply.

DISCLOSURE: a different model of the same family authored this plan, so treat this as near-self-review.
Its value rests on RE-MEASURING the claims rather than reading them, and that is what produced the
central finding: PR-001 came from asking the one question the plan's own method could not answer, which
is what `check_type(root, "plans")` ACTUALLY returns on a real fixture at the EXECUTING head rather than
at the authoring head. The plan's F-2 answered a neighbouring question (which separately-named sweep
functions run) and drew a conclusion the measurement contradicts.

WHAT HOLDS, AND IT IS THE CORE OF THE PLAN. The defect is real, the diagnosis is exactly right, and the
fix shape is correct. F-1 reproduced: the gate's predicate is the literal `if enriched.severity ==
"info": continue`, and a `warning` finding at the plan path refuses `aw commit` with rc 1 identically to
an `error`. The fail-closed reasoning behind E-02 is verified rather than assumed: `enrich_drift` fills
severity as `drift.severity or spec.severity`, `rule_spec` falls back to `_DEFAULT_RULESPEC` (`error`),
and a PRE-SET unrecognized severity survives enrichment (measured: a Drift carrying
`severity='bogus-tier'` comes out of `enrich_drift` still `bogus-tier`), so E-02's "blocking holds
everything else" genuinely refuses an unregistered rule, an empty severity, and a garbage tier. F-3
holds: every `warning` RuleSpec comment that speaks to commits says the tier must not block one, and
`grep` for the claimed strings returns exactly the quoted comments. F-4 holds:
`tests/test_work_primitives.py` was deleted by `19313eed` and no remaining test drives either verb's
findings gate, so E-03/E-04 create the coverage rather than editing it. F-6's reading of `8dto0g` is
accurate. The two-contracts distinction in Step 0 (lifecycle action gate versus `aw check` exit code) is
correct and is the insight that makes the whole plan sound. OQ-01 and OQ-02 were already resolved from
evidence with carriers declined, which is the right shape.

WHAT DOES NOT HOLD. Three things, and the first materially changes the plan's picture of its own
subject.

```text
review probe, HEAD de94e2dc (plan authored against 877545fc, 67 commits earlier)

REGISTRY SWEEP
  warning rules in RULE_REGISTRY                      11     <- plan's F-2 enumerated 9
  omitted by the plan                                 check.ipd-priority-required
                                                      check.ipd-work-kind-required

WHY THEY WERE MISSED (not an authoring error, a stale measurement)
  git show 877545fc:check_engine.py | grep -c ipd-priority-required        0
  git merge-base --is-ancestor 877545fc 9e3ed86e                          true
  9e3ed86e  feat(planprio): ... enforce them at ready-to-execute gate (lkexaw)  2026-09-24

ARE THEY GATE-REACHABLE? (unpatched engine, fresh `approved` fixture lacking both fields)
  enriched check_type(root, "plans") for the plan path:
    warning  check.ipd-priority-required
    warning  check.ipd-work-kind-required
    info     check.ipd-lint-diagnostic
  aw commit      -> rc 1  "refusing - 2 finding(s)"        naming both rules
  aw work begin  -> rc 1  "refusing to start - 2 finding(s)" naming both rules
  same fixture WITH - Priority: high / - Work-Kind: chore
                 -> rc 0  "aw commit: committed 1 path(s)"

THE DELETED FIXTURE E-03 SAYS TO COPY
  19313eed^:tests/test_work_primitives.py _PLAN has Priority? False  Work-Kind? False  Status: approved
  so copied verbatim it trips BOTH rules, and every authored case measures the wrong thing

E-04 CASE (c) WITH THAT FIXTURE
  aw work begin bad001 -> rc 1 with THREE findings:
    check.name-nonconformant  +  check.ipd-priority-required  +  check.ipd-work-kind-required
  so an rc-only assertion passes even if check.name-nonconformant stopped firing

IS THE REQUIREMENT UN-GATED BY THE FIX? (OQ-03)
  aw ipd lint --phase author        rc 1  IPD-M110 / IPD-M111
  aw ipd lint --phase pre-execution rc 1  IPD-M110 / IPD-M111
  aw ipd begin                      rc 1  "pre-execution gate did NOT conform (error); no receipt written"
  -> no: the owning gate still refuses execution

V-05'S DASH CHECK
  printf 'a - b\n'      | grep -c $'\u2014|\u2013'   prints 0, EXITS 1
  printf 'a \u2014 b\n' | grep -c $'\u2014|\u2013'   prints 1, EXITS 0
  grep -c $'\u2014|\u2013' CHANGELOG.md              0 (file already clean)

CALLER SET (plan's under-scope premise, re-verified)
  grep -n _validate_plan_via_engine agent_workflows/*.py -> def + run_work_begin + run_commit  (unchanged)
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A (correctness) / E (verification) | plan `F-2`; `check_engine.check_plan_priority_required` reached from `check_content`'s plans branch; `9e3ed86e` (planprio `lkexaw`); `git merge-base --is-ancestor 877545fc 9e3ed86e` | F-2'S NARROWING CONCLUSION IS WRONG AT THE EXECUTING HEAD, AND IT UNDERSTATES THE LIVE BLAST RADIUS. F-2 concluded "today exactly ONE warning rule can block". Measured at HEAD `de94e2dc`, THREE can: `check.review-decision-unescalated` plus `check.ipd-priority-required` and `check.ipd-work-kind-required`, which the plan's nine-rule enumeration omits entirely because they did not exist when it was written (they landed in `9e3ed86e`, a DESCENDANT of the authoring HEAD `877545fc`). The two matter far more than the one the plan found: `check.review-decision-unescalated` needs an irreversible unescalated review decision to exist, whereas these fire on ANY plan whose `- Status:` is `approved`/`auto-approved` and which lacks either field, which is the ordinary case this gate meets. Measured end to end: such a plan is refused by BOTH verbs naming both rules, and commits normally once the fields are present. THE METHOD IS THE TRANSFERABLE PROBLEM: F-2 spied on separately-named `check_*` sweep callables, and these two reach the gate through `check_content`'s plans branch, so the spy could not see them and the same spy re-run today would make the same mistake. Consequence for the plan as written: it describes its own subject as "a latent trap for any future plan-scoped warning rule" when it is in fact a live, ordinary-path refusal, which understates the fix's value and, worse, leaves E-01 re-measuring with the method that missed it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-2's severity cell relabelled SUPERSEDED (its sweep-seam mechanics are kept, its conclusion is not); F-7 added with the full measurement and the ancestry proof; the Concern now states three reachable rules with the end-to-end output; Step 0 gains the `check_content`-plans-branch convention explaining why a call-site spy misses this family and instructing measurement via `check_type` on a real fixture. E-01 now REQUIRES re-deriving the reachable set from an unpatched `check_type(root, "plans")`, explicitly forbids re-using the spy, and makes an unconsidered `warning` rule a STOP condition; V-01 requires that list pasted. |
| PR-002 | HIGH | IN-SCOPE | E (testing and verification) | plan `E-03` ("modelled on the deleted module's `WorkPrimitivesTest.setUp`") and `E-04` case (c); `git show 19313eed^:tests/test_work_primitives.py` `_PLAN` (no `- Priority:`, no `- Work-Kind:`, `- Status: approved`) | THE PROPOSED FIXTURE MAKES EVERY TEST CASE MEASURE THE WRONG THING, AND IT IS THE SAME ROOT CAUSE AS PR-001. E-03 says to model the fixture on the deleted module's plan, which is `approved` and carries neither field, so it trips both rules from PR-001. Measured: that fixture UNPATCHED yields `aw commit: refusing - 2 finding(s)` and `aw work begin: refusing to start - 2 finding(s)`. Concretely: case (a) (the warning-commits case, which is the plan's whole point) would after the fix pass while silently carrying two unasserted advisories; cases (b), (c) and (d) would refuse over rules they never named, so the mutation run the plan relies on could not discriminate the fix from the fixture's own noise. E-04 case (c) is worse because it is the one deliberately UNPATCHED case, existing to catch the patching seam diverging from the real engine: measured, it refuses with THREE findings, so its authored rc-1 assertion passes even if `check.name-nonconformant` stopped firing altogether, which is precisely the divergence it exists to detect. | C:Low; U:Low; S:Low; F:High; Overall:Low | FIXED | E-03 now requires the fixture to carry real `- Priority:`/`- Work-Kind:` values, records the measurement showing why copying the deleted `_PLAN` verbatim corrupts every case, and adds a BASELINE case asserting the unpatched fixture produces NO finding at `warning` or above (printing the enriched `check_type` list), so a future rule that starts firing fails loudly instead of silently. E-04 case (c) must now assert on the rule id `check.name-nonconformant` AND that no `warning`-tier id appears, rather than on rc alone. |
| PR-003 | MEDIUM | UNDER-SCOPE | D (anti-regression / domain invariants) | `lkexaw` E-04 (executed): "`warning` while the pending corpus still carries sentinels, `error` once it does not. Note the end state is `error`; nothing may leave the rule permanently at `warning`"; measured `aw ipd lint`/`aw ipd begin` refusals | THE PLAN DID NOT KNOW IT WAS UN-GATING TWO DELIBERATELY STAGED RULES, AND SO NEITHER JUSTIFIED IT NOR RECORDED IT. The two rules PR-001 names are not ordinary advisories: they are a staged ROLLOUT whose recorded end state is `error`. Making `warning` non-blocking therefore has a consequence the plan never states (a plan missing Priority or Work-Kind becomes committable) and rests on an assumption it never checks (that the requirement is enforced elsewhere). The assumption happens to be TRUE, measured: the same fieldless approved plan is refused by `aw ipd lint` at both `author` and `pre-execution` with `IPD-M110`/`IPD-M111`, and `aw ipd begin` refuses with "no receipt written", so it cannot reach execution. But an unstated, unverified assumption underneath a commit-path behavior change is a gap regardless of its truth, and a later reader of the new predicate would have no way to know that `warning` here is a rollout stage rather than a permanent tier. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-07/V-07 (assigned by `aw ipd sync`) records the interaction in a `work_cmd` code comment naming both rules, `lkexaw`'s end-state obligation, and the lifecycle-gate-versus-exit-code distinction, and V-07 requires proof via the registry that neither rule was re-tiered by this plan. New OQ-03 resolves the question with the three facts and states the accepted cost. F-8 added. The `Deferred` re-tiering bullet is amended to acknowledge the pending promotion, and its decline DISCLOSES that the obligation lives only in an executed plan's prose (raised to the maintainer in the report rather than filed unilaterally, since a review may not mutate records). |
| PR-004 | MEDIUM | UNDER-SCOPE | G (executability) / 2026-09-01 maintainer scope-fence ruling | plan `## Approval and execution gate` and `## Scope check` under-scope bullet, as authored | THE GATE AND THE FENCE BOTH CARRIED THE STOP WORDING THE RULING SAYS TO FLAG, AND THE GATE NEVER SAID WHAT A HUMAN IS APPROVING. The under-scope bullet ended "if that caller lives outside `work_cmd.py`, STOP and declare the path first", framing a SCOPE question as a gate to clear; per the 2026-09-01 ruling a fence is a DECLARATION the runner reconciles afterwards, and the correct requirement is that an out-of-scope edit be made and then JUSTIFIED, which `aw ipd finalize` already enforces via `--scope-reason`/`--scope-ack`. The gate itself was one paragraph: no statement of what approval authorizes, no bare-suite instruction despite E-06 requiring one, and its single STOP condition (E-01 shows the warning case already commits) did not say what to DO in that case. For a change to what the repository's own mandatory commit path refuses, "what am I approving" is the costly omission. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten keeping `Size assessment: standard`: a "what a human is approving" paragraph naming the measured practical effect and stating that the `aw check` exit contract is unchanged; a declaration-style scope fence naming `check_engine.py` and `drift_exit_code` as OUT and routing excess to `--scope-reason`; the hard-MUST honesty rule with the BARE `python3 -m pytest` instruction and the explicit prohibition on `-n0`, a second `-q` and `-p no:randomly`; path-scoped `aw commit` with the three literal paths and never-push; and TWO genuine stop conditions, each now saying what to do (retire to `superseded/` with the reason; report the unconsidered rule). The under-scope bullet was rewritten as a declaration and re-verifies the caller set at the review HEAD. |
| PR-005 | LOW | IN-SCOPE | E (verification) | plan `V-05`, as authored (`git diff CHANGELOG.md \| grep -c $'\u2014\|\u2013'` printing `0`) | THE PROPOSED DASH CHECK'S EXIT CODE CONTRADICTS ITS EXPECTED OUTPUT. `grep -c` prints `0` on no match but EXITS 1, so the PASSING case reads as a command failure under any `set -e` or `&&` chain, and an executor may "fix" the check by weakening the expectation. Measured both directions. Minor, but V-05 is the only evidence gate on the one user-facing artifact this plan writes, where the no-em-dash rule genuinely applies. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now specifies `git diff CHANGELOG.md \| grep -n $'\u2014\|\u2013' \|\| echo "no em/en dash"` and requires the `no em/en dash` line pasted, with an explicit note not to use a bare `grep -c` and expect a zero exit. F-9 added recording the measurement and that `CHANGELOG.md` is currently dash-clean, so the new bullet is the only thing at risk. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001/PR-002: F-2's measurement is stale and two live gate-blocking rules were missed. Retire this plan and re-author against the current head, or repair it in place? | Repair in place: correct F-2, add F-7/F-8/F-9, and harden E-01/E-03/E-04 so the executor RE-DERIVES the reachable set rather than trusting any authored list. | (a) REPLAN (retire and re-author). Rejected: the diagnosis, the fix shape, the fail-closed reasoning and the two-contracts insight are all correct and independently verified; what is stale is one enumeration and the fixture it implies, both repairable with bounded edits, and re-authoring would discard correct work and re-incur the same staleness against the NEXT head. (b) Fix F-2's list to eleven rules and stop. Rejected: a corrected list goes stale the same way, which is the actual lesson; the durable fix is to make E-01 measure the set at execution time and STOP on an unconsidered rule. | `git merge-base --is-ancestor 877545fc 9e3ed86e` is true and `git show 877545fc:check_engine.py \| grep -c ipd-priority-required` is `0`, so the omission is a stale measurement rather than an analysis error; the workflow rubric's live-artifact convention requires a criterion counting a drifting population to state the property and RE-DERIVE at execution time, which is exactly this case. | yes |
| D-2 | OQ-03 (added at review): two of the rules being un-gated are staged toward `error` by `lkexaw`. Does making `warning` non-blocking here wrongly un-gate a requirement the repository decided to enforce? | No. Proceed, record the interaction in code (E-07), and re-tier nothing. | (a) Keep `warning` blocking to preserve these two rules' current effect. Rejected: it would also keep every FUTURE advisory rule blocking, which is the exact trap the plan exists to close, and it makes the gate's behavior depend on a rollout stage rather than on a severity contract. (b) Promote the two rules to `error` in this plan so nothing is un-gated. Rejected: it widens a three-path plan into `check_engine.py`, and the promotion's precondition (the pending corpus no longer needing the sentinel) is `lkexaw`'s judgement to make, not this plan's. (c) Exempt the two rules by name in the predicate. Rejected: a name-keyed exemption re-creates the two-value dial the plan is removing, one rule at a time. | Measured: the requirement is enforced by the gate that OWNS it, not by `aw commit`. A fieldless `approved` plan yields `IPD-M110`/`IPD-M111` from `aw ipd lint` at BOTH `author` and `pre-execution`, and `aw ipd begin` refuses with "pre-execution gate did NOT conform (error); no receipt written", so it cannot reach execution. `lkexaw` E-04's end-state clause is preserved because nothing is re-tiered: promotion restores blocking here automatically. Accepted cost, stated in OQ-03: until promotion, such a plan can be committed though not executed. | yes |
| D-3 | Does this plan need a spec amendment (it changes what a mandatory commit path refuses)? | No. The plan's `N/A` is correct and is kept; no `.spec.md` enters `- Scope-Paths:`. | Amending the invariant catalog `pqsx96`. Rejected: its I-01 row is about PATH SCOPING in the commit path, not about finding severity, so the amendment would be an addition rather than a correction, and the catalog is `- Status: draft` with its own recorded pending corrections (the I-09/I-16 misfiling note). Adding a row for this gate is a separate decision. | `grep -rln "aw commit\|work begin" .aw/records/specs/` returns only `pqsx96` (invariant catalog, I-01 = path scoping) and `c4gd2h` (runner quit), neither of which states the severity predicate; the three-tier model lives in `check_engine.RULE_REGISTRY` comments and `artifact_core.drift_exit_code`, which are code, not spec. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent s7cu7n -> {"outcome":"clean","exit":0,"findings":0}
aw ipd sync --apply                        s7cu7n -> assigned E-07; watermark advanced (06 -> 07)
aw ipd lint --phase review-finalize --agent s7cu7n -> {"outcome":"clean","exit":0,"findings":0}   (after revisions)
check.ipd-uncarried-obligation                     -> 0 before and after
aw sanitize --agent                                -> clean, 0 findings
em/en dashes in the revised plan                   -> 0

HEAD at review                                de94e2dc   (plan authored against 877545fc, 67 commits earlier)
lane input vs pending/ copy                   byte-identical -> no pre-review snapshot needed
plan Kind                                     child -> IPD-S407 not applicable

F-1 REPRODUCED   predicate is `if enriched.severity == "info": continue`; a warning finding at the
                 plan path -> `aw commit: refusing - 1 finding(s)` rc 1, same shape as an error
E-02 FAIL-CLOSED REASONING VERIFIED
  enrich_drift severity rule        `drift.severity or spec.severity`
  rule_spec('<unregistered>')       error   (_DEFAULT_RULESPEC)
  pre-set 'bogus-tier' survives     bogus-tier   -> so "everything else blocks" really refuses it
F-3 HOLDS        every warning RuleSpec comment addressing commits says the tier must not block one
F-4 HOLDS        no remaining test drives either verb's findings gate
caller set       def + run_work_begin + run_commit   (unchanged at review HEAD)

PR-001  warning rules in registry 11, not 9; omitted: check.ipd-priority-required, check.ipd-work-kind-required
        877545fc:check_engine.py grep -c ipd-priority-required -> 0
        merge-base --is-ancestor 877545fc 9e3ed86e -> true
        unpatched check_type(root,"plans") on a fieldless approved fixture -> both rules, warning
        aw commit -> refusing - 2 finding(s);  aw work begin -> refusing to start - 2 finding(s)
        with Priority+Work-Kind present -> committed 1 path(s)
PR-002  19313eed^ _PLAN: Priority False, Work-Kind False, Status approved  -> fixture trips both
        E-04 case (c) with it -> rc 1 with THREE findings, so rc alone cannot discriminate
PR-003  aw ipd lint author / pre-execution -> IPD-M110, IPD-M111 (rc 1 both)
        aw ipd begin -> rc 1 "pre-execution gate did NOT conform (error); no receipt written"
PR-005  grep -c on no match: prints 0, EXITS 1;  with a real em dash: prints 1, exits 0
        CHANGELOG.md currently contains 0 em/en dashes
```

### Verdict and readiness

Verdict `APPROVE WITH REVISIONS APPLIED`. All five findings `FIXED`; none is `OPEN`, `DEFERRED` or
`REPLAN`, so no escalation to a `- Blocking: yes` question is required and none was added. All three
open questions are `resolved` and carry carrier fields. Readiness `GO - PENDING HUMAN APPROVAL`: the
plan is `reviewed`, no BLOCKER or HIGH is left unfixed, and the only remaining step is the maintainer's
sign-off, which a review may not grant.

ONE ITEM FOR THE MAINTAINER, raised rather than filed because a review may not mutate records:
`lkexaw` E-04's obligation to promote `check.ipd-priority-required` and `check.ipd-work-kind-required`
from `warning` to `error` lives ONLY in an executed plan's prose. No live backlog item, spec, or plan
carries it, so `aw attention` cannot see it and nothing will remind anyone. This plan does not create
that gap and does not widen it, but it does now DEPEND on the promotion eventually happening for the
staged rollout to complete. Filing a backlog item for it is a one-line act the maintainer may want.
