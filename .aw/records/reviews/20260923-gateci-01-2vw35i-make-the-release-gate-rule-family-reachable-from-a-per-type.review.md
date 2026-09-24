# Review findings: plan 2vw35i

- Subject-Id: 2vw35i
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `b4dc3a58` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review, so nothing found below is structural;
`--phase review-finalize` conforms after revision.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests
entirely on RUNNING the claims rather than re-reading them, which is what produced the findings below.

THE PLAN'S DIAGNOSIS IS CORRECT AND ITS DELIVERABLE IS NOT. Both halves of F-1/F-2 re-confirmed:

```text
# F-1: CI never runs the sweep
.github/workflows/local-leaks.yml: 0
.github/workflows/secret-scan.yml: 0
.github/workflows/tests.yml:       0      # grep -c "check all"

# F-2: the family is unreachable per-type (counts drifted; mechanism did not)
check_types([backlog]) total=5   family members: NONE
check_types([all])     total=26  family members: ['check.from-backlog-dangling',
                                                  'check.live-bug-ungated']
```

THE DECIDING MEASUREMENT IS THE ONE THE PLAN NEVER MADE: what the family reports on this tree RIGHT
NOW, which is what its proposed fail-closed CI step would enforce.

```text
live_bug_gate              findings=1  rules=['check.live-bug-ungated']
release_gate_consistency   findings=0
blocks_release             findings=0
from_backlog               findings=1  rules=['check.from-backlog-dangling']
FAMILY TOTAL: 2   drift_exit_code: 1
  check.live-bug-ungated      | .aw/records/backlog/open/...7l1ggb....backlog.md   severity=error
  check.from-backlog-dangling | .aw/records/plans/executed/...mjx7ne....ipd.md     severity=error
```

So E-03 as written lands a step that is RED ON ARRIVAL, and NEITHER finding is this plan's to fix:

```text
# (a) the plan's own named regression target carries a maintainer decision AGAINST gating it
7l1ggb history: "Not a release gate: the instance was repaired in zz5yxq's commit
  (the fork is now classified), and the residual work is a test-harness hardening
  (add the missing-direction assertion), not a shipping defect."
# and the plan's own deferral already says: "GATING 7l1ggb ITSELF ... is a maintainer
# judgement about that bug, not a side effect of wiring a check."

# (b) the other finding is unfixable by construction
releases.check_from_backlog detail: "From-Backlog 'none' does not resolve to a backlog item"
  -> the value is the literal SENTINEL `none`, in a plan under executed/
AGENTS.md: do not add commits to a plan already in executed/
executed plan rgaasb already recorded it: "the one live check.from-backlog-dangling
  (a From-Backlog: none in an executed/ plan) is pre-existing and is NOT this plan's to fix"
```

That is the exact failure the plan cites `4y7nzh` to avoid ("a gate that stays red stops being read"),
except the plan would be the direct cause rather than an inheritor.

E-02 WAS ALSO PROPOSING TO OVERTURN A WRITTEN DECISION WITHOUT CITING IT. `check_types` carries this
beside `check_live_bug_gate`:

```text
# (2) IT IS THEREFORE NOT REPORTED BY `aw check backlog`, and that is a known, stated cost, not
# an oversight: `check_type('backlog')` never reaches this block ... Wiring it into the backlog
# content path instead was rejected because it would surface this ONE rule while its four
# siblings stayed invisible on the same command, which is a more confusing contract than
# "the family lives on the full sweep". Consumers must use `aw check` / `aw check all`.

# (1) IT IS DELIBERATELY *NOT* ADDED INSIDE `check_release_gate_consistency` ... That function is
# composed by `check_commit_invariants`, the opt-in PRE-COMMIT aggregator, and every rule in it is
# COMMIT- or RECEIPT-scoped for a reason ... putting it there would refuse a commit because some
# OTHER party's bug item elsewhere in the tree is ungated - exactly the shared-checkout failure
# AGENTS.md warns against.
```

So the gap is a recorded tradeoff, not an oversight, and the remedy E-02 proposed is the one already
refused. This does not kill the plan (the tradeoff can be revisited) but it changes the burden of
argument, constrains any per-type form to expose the WHOLE family, and settles OQ-01 on evidence.

THREE SMALLER MEASURED FINDINGS, each of which would have cost the executor a round trip:

```text
# PR-004: the job E-03 wants to join is ALREADY RED, and this plan is one of the reasons
check plans:    exit 1  findings 12  ['check.collisions-not-checked','check.ipd-uncarried-obligation']
check releases: exit 0  findings 1   ['check.collisions-not-checked']
check backlog:  exit 1  findings 5   ['check.collisions-not-checked','check.name-nonconformant']
check specs:    exit 0  findings 1   ['check.collisions-not-checked']
evaluate_durable_carrier(2vw35i) -> "6 obligation(s) name no durable carrier"
# After revision: 0 findings.

# PR-006: the family E-03 would enforce CONTAINS a known false-positive rule
4le6yz: open, Work-Kind: bug, Blocks-Release: next
  "check.from-backlog-gate-mismatch fires on an id6-vs-next gate spelling difference
   that denotes the SAME release"  (raw string equality; `next` resolves to f33nrj)
0cqf33: open, Work-Kind: bug, Blocks-Release: next  (same rule, same cause)
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness); C (operability) | family driven directly: 2 findings, `drift_exit_code` 1; `7l1ggb` history "Not a release gate: ... not a shipping defect"; the plan's own `GATING 7l1ggb ITSELF` deferral | E-03's fail-closed step is RED ON ARRIVAL and its named regression target is illegitimate. `check.live-bug-ungated` fires on `7l1ggb`, whose record carries a deliberate maintainer decision that it is not a gate and which the plan's own deferral forbids gating. Landing the step reds `main` on a finding this plan may not clear, reproducing the `4y7nzh` failure the plan cites to avoid. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-03 rewritten: fail-closed ONLY if E-01 shows the family clean, otherwise the advisory `\|\| true` + `::warning::` shape the maintainer already uses, with blocking findings and the flip precondition named in a comment. Suppression explicitly forbidden. Goal, Scope, F-3 and V-03 rewritten; recorded as plan F-7. |
| PR-002 | BLOCKER | IN-SCOPE | A; D (anti-regression) | `releases.check_from_backlog` detail "From-Backlog 'none' does not resolve to a backlog item"; `AGENTS.md` executed-plan rule; `rgaasb` deferral text | The family's SECOND blocking finding is unfixable by construction: a `From-Backlog: none` sentinel in an `executed/` plan that must not be edited, already recorded as not-to-be-fixed by a prior executed plan. So no legitimate act available to this plan makes the family clean, which independently confirms PR-001's conclusion. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as plan F-8; added as an explicit deferral with a holding carrier and an E-01 obligation to file a dedicated item for the `none`-sentinel verdict question; V-01 requires that id6. The scope check forbids "fixing" the verdict here. |
| PR-003 | BLOCKER | IN-SCOPE | C (architecture); F (honest documentation) | the quoted `check_types` comment beside `check_live_bug_gate`, points (1) and (2) | E-02 proposed the remedy the codebase already REJECTED IN WRITING, and the plan never acknowledged the decision exists. The comment states the per-type invisibility is "a known, stated cost, not an oversight" and rejects backlog-path wiring because it surfaces one rule while four siblings stay invisible; it also records why the rule is not folded into the commit-scoped pre-commit aggregator. | C:Medium; U:Low; S:Low; F:Low; Overall:Medium | FIXED | Recorded as plan F-6. E-01 must quote both points; E-02 must expose the WHOLE family (a one-rule form is the refused shape) and must not widen `check_commit_invariants`; OQ-01 RESOLVED to the distinct named target on this evidence; conventions and spec-sync updated to require correcting the now-stale comment and docstring. |
| PR-004 | MEDIUM | UNDER-SCOPE | G (plan executability) | four per-type exit codes; `evaluate_durable_carrier(2vw35i)` -> 6 uncarried obligations | Two omissions with one root: the plan asserted CI would newly fail on its step while the existing fail-closed `check plans` step ALREADY exits 1 with 12 findings, and THIS PLAN is one of them, so it would have blocked its own finalize (`aw ipd lint --phase pre-transition` merges the same `error`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as plan F-9. Every `## Deferred` row and OQ-01 now carries `- Carrier:`/`- Carrier-Declined:`; re-measured `evaluate_durable_carrier` -> 0 findings. E-01 must measure the existing steps' exit codes; the required tests now expect `check plans` to still exit 1 for the unrelated reason rather than "still green". |
| PR-005 | MEDIUM | IN-SCOPE | G (live-artifact re-derivation convention) | authoring 4/49 versus review 5/26 for the same two commands | Four load-bearing counts are LIVE ARTIFACT counts stated as fixed facts, and three of the four had already drifted between authoring and review. Under the re-derivation convention such counts belong in prose as context and must be re-derived at execution, never asserted as the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and F-1..F-4 now carry both figures and label them drifting; E-01 explicitly requires re-derivation and says the authoring/review figures are context, never the bar. |
| PR-006 | MEDIUM | IN-SCOPE | A; F (prevent a rule people route around) | `4le6yz` and `0cqf33` front matter (both `open`, `bug`, `Blocks-Release: next`); `4le6yz`'s measured two-finding reproduction | The family E-03 would make fail-closed CONTAINS a rule with known, gated, live false-positive defects: `check.from-backlog-gate-mismatch` compares gate spellings literally, so `next` versus its resolved release id6 reads as a broken handoff. Making that fail-closed can red `main` on a correctly-preserved gate. The plan cited both items only as "verdicts are owned elsewhere" and never drew the enforcement consequence. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-5 rewritten to state the consequence; added to conventions as "a known-false-positive rule must not be made fail-closed"; strengthens E-03's advisory fallback with a second independent reason. |
| PR-007 | MEDIUM | UNDER-SCOPE | E (testing/verification); D | `check_live_bug_gate`'s handoff-exemption block ("a correctly-handed-off bug would be flagged forever and the rule would train people to ignore it") | E-04 tested only fires/does-not-fire. It never tested the HANDOFF EXEMPTION (a live ungated bug whose `From-Backlog` carrier holds the gate must NOT be flagged), which is the rule's most consequential branch and the likeliest regression, nor that the WHOLE family is reachable rather than one member. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now requires a per-member reachability assertion, the handoff-exemption case, and an explicit prohibition on asserting the live tree is family-clean. V-04 demands each as evidence. |
| PR-008 | MEDIUM | IN-SCOPE | F (honest documentation) | the `check_types` comment; `check_live_bug_gate` docstring point (2); `AGENTS.md` release-gate section | Three documentation surfaces become FALSE if E-02/E-03 land, and spec-sync addressed only one of them, asking to make the `AGENTS.md` sentence accurate on the assumption the step is fail-closed. Under PR-001 the likely outcome is advisory, so writing the fail-closed sentence would reproduce the same overclaim the section already makes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync rewritten to require amending `AGENTS.md` to match WHAT SHIPS (naming the flip precondition if advisory), and to correct both the `check_types` comment and the `check_live_bug_gate` docstring while PRESERVING the reason the original rejection was recorded. |
| PR-009 | LOW | UNDER-SCOPE | G (execution contract) | OQ-01's authored `Owner:` ("this plan's executor"); `SUPPORTED` holds 8 record types | OQ-01 was left `open` for the executor to decide although the repository answers it, and its recommended remedy (a new named target) implies an undeclared `cli.py` edit and risks being added to `check_engine.SUPPORTED`, which enumerates record TYPES, not check targets. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 RESOLVED at review to the distinct named target with the evidence and the accepted cost recorded (D-1). Scope check now flags `cli.py` as undeclared-and-likely-needed and forbids adding the target to `SUPPORTED`; V-02 requires a statement of where it lives. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: per-type reachability, or a distinct named check target? | RESOLVED: the distinct named target. Written into the plan with the evidence and the accepted cost, so the executor does not re-derive it. | PER-TYPE: rejected on three measured grounds. The `check_types` comment already refused it for surfacing one rule while four siblings stay invisible (so an admissible per-type form would need a backlog check reading releases and plans, muddying the boundary per-type commands exist to draw); F-4 means its natural CI home is the step that must stay advisory; and F-7/F-8 mean E-03 needs a rule set narrow BY CONSTRUCTION whose advisory state is reasonable about independently of backlog debt. | the quoted `check_types` comment (both points); `tests.yml` advisory step + `DECISION 18-r2ks4k-D1`; the family's measured 2 findings at exit 1 | yes |
| D-2 | PR-001/PR-002 make the plan's headline deliverable ("CI FAILS on a live ungated bug") unachievable today. REPLAN, or repair? | Repair: keep reachability as the primary deliverable and make the fail-closed flip CONDITIONAL, with an advisory fallback that is still strictly better than today. | REPLAN: rejected because F-1 and F-2 are real, re-confirmed, and unowned elsewhere; the plan's structure, scope fence and three of four E-items survive; and retiring it would strand the inherited `Blocks-Release: next`. Also rejected: keeping fail-closed and clearing the two findings, which would require gating an item the maintainer decided is not a gate and editing an `executed/` plan. | `plan-review.md` Step 2.4 (REPLAN only when bounded edits cannot repair); `AGENTS.md` (executed-plan immutability; shared-checkout rules); `7l1ggb` history | yes |
| D-3 | Should the review itself clear either blocking family finding so E-03 can land fail-closed? | No. Neither is touched, and the plan is explicitly forbidden from touching them. | Gating `7l1ggb` with `--blocks-release next`: rejected, it overturns a recorded maintainer decision about a specific bug. Editing the `executed/` plan's `From-Backlog: none`: rejected, `AGENTS.md` forbids it and `rgaasb` already recorded it as not-to-be-fixed. Narrowing E-03's rule set to dodge them: rejected as suppression, which inverts the plan's purpose. | `AGENTS.md` (executed plans; do not revert another party's decisions); `rgaasb`'s deferral; `plan-review.md` (review plans only, change no code or data) | yes |
| D-4 | Is the `none` sentinel a rule DEFECT (should read as absent, not dangling) that this review should record as such? | Record it as a genuine open verdict question with a HOLDING carrier (`wu8qjy`) and require E-01 to file a dedicated item if it still blocks. Do not decide the verdict here. | Asserting it IS a defect and scoping the fix into this plan: rejected because verdict changes are excluded by this plan's own discipline and by F-5's precedent (`4le6yz`/`0cqf33` are separate items for exactly this reason). Asserting it is CORRECT behavior: rejected as an unverified claim; `none` is plainly a sentinel meaning "no source", which reading as dangling is at least arguable. | the plan's own `FIXING INDIVIDUAL GATE RULES` deferral; `rgaasb`'s treatment of the same finding; `check.from-backlog-dangling`'s registry entry | yes |
| D-5 | `4le6yz`/`0cqf33` are live gated bugs inside the family E-03 would enforce. Does that block this plan? | No, but it is recorded as a second independent reason the advisory fallback must exist, and as a convention ("a known-false-positive rule must not be made fail-closed"). | Treating it as a blocker requiring those items to be fixed first: rejected because they currently produce ZERO findings on this tree (measured: `check_release_gate_consistency` -> 0), so the risk is latent rather than live and blocking on it would stall a plan that improves visibility today. | `check_release_gate_consistency` driven live -> 0 findings; `4le6yz`'s measured reproduction at an earlier HEAD | yes |

### Deferred and open

No finding is DEFERRED, OPEN, or REPLAN. Every finding above is FIXED, so no escalation to a
`- Blocking: yes` question is owed under the `review_findings_gate` rule (default `block_at: HIGH`;
no `review_findings_gate` key is configured in `.aw/config/project.json`).

OQ-01 is now `- Status: resolved` (D-1), so the plan carries no open question at all.

#### Correction to D-3's `Reversible` column, recorded rather than silently edited

D-3 was first written `Reversible: no` and that was a MIS-CLASSIFICATION, caught by
`check.review-decision-unescalated` firing on this record. The rule is a backstop and it was right to
fire, so the honest response is to state why the value changed rather than to quietly satisfy the gate.

The `Reversible` column judges the COST OF BEING WRONG ABOUT THE DECISION THAT WAS MADE. D-3 decided to
CHANGE NOTHING: not to gate `7l1ggb`, not to edit the `executed/` plan, not to narrow E-03's rule set.
A decision to leave two artifacts untouched is trivially reversible; a later maintainer who disagrees
can gate the item or resolve the sentinel question at any time, and nothing was published, migrated, or
deleted. What is irreversible is the REJECTED alternative (editing an `executed/` plan, or overturning a
recorded maintainer decision about a specific bug), and that asymmetry is exactly WHY the refusal is
correct. I had recorded the irreversibility of the path not taken, which is the wrong cell to put it in.

A SECOND, SEPARATE LESSON FROM FIXING IT, worth recording because it is a trap for the next reviewer:
the corrected cell was first written as `yes (corrected; see the note below)`, and the rule KEPT FIRING.
`reviews.classify_reversible` normalizes the whole cell and returns `unknown` for any unrecognized
token, treating a blank and a decorated value identically on the stated ground that "a reader must not
be told a decision is safely reversible on the strength of a blank". So an annotated `yes` is NOT a
`yes`. The `Reversible` cell must hold a bare token; commentary belongs in prose, as it now does.

No escalation as a `- Blocking: yes` question is therefore owed, and none is added: manufacturing a
blocking question for a decision to preserve the status quo would stall the plan for no decision the
human actually needs to make. The substance is not lost: the two findings are recorded in the plan as
F-7 and F-8, the `none`-sentinel verdict question is an explicit deferral with a holding carrier and an
E-01 obligation to file a dedicated item, and E-03 cannot land fail-closed until they are resolved. So
the obligation is carried by the plan's own gate rather than by a question.

### Notes on what was NOT changed, and why

- No code, test, spec, or workflow file was touched by this review. Only the plan under review and this
  record. In particular `.github/workflows/tests.yml` is untouched, and no `check_engine` rule was
  altered even though PR-002 identifies a plausible rule defect (D-4 explains why that is deliberate).
- `7l1ggb` was NOT gated and the `executed/` plan was NOT edited (D-3). Both are other parties'
  decisions and artifacts; clearing a finding by editing them is exactly the shared-checkout and
  executed-plan violation `AGENTS.md` forbids.
- F-1, F-2 and F-4 were NOT retracted or downgraded. All three re-measured TRUE; only their COUNTS
  drifted, which PR-005 addresses by requiring re-derivation rather than by weakening the findings.
- `- Blocks-Release: next` was left in place. The gate is inherited from `wu8qjy`, a live `bug`, and
  PR-001/PR-002 show the enforcement hole is WIDER than filed (it cannot even be closed yet), so the
  gate is still earned.
- The plan's `- Status:` is left at `to-review` in this file; the transition to `reviewed` is applied
  through `aw ipd set reviewed` so it carries an attributed history line, per the untooled-status gate.
