# Review findings: plan obyhrm

- Subject-Id: obyhrm
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (BLOCKER, open), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a3e4d2c2`. The plan file was committed and unmodified
(`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review.
The plan is `- Kind: child`, so the `IPD-S407` orchestrator child-row check does not apply. After
revision the linter reports exactly one finding, `IPD-Q501` on the BLOCKING question this review
added, which is the intended fail-closed state and not an unrepaired structural defect.

THIS PLAN'S OWN REASONING IS THE BEST I HAVE REVIEWED IN THIS SWEEP, AND I RE-DROVE ALL OF IT RATHER
THAN TRUSTING IT. Every measurement reproduces, several to the exact string:

- F-1. Added a conformant 25th walkthrough (`- Id: pr0be1` matching its slot) and got
  `AssertionError: 25 != 24 : Census must find exactly 24 walkthroughs`, `1 failed, 3 passed`;
  removing it restored `4 passed`. The tree holds exactly 24 non-README walkthroughs.
- F-3. Performed the PARTIAL edit the backlog item's wording implies (both assertions gone, `exempt`
  left bound) and ruff failed exactly as recorded: `F841 Local variable 'exempt' is assigned to but
  never used`, ruff 0.16.3, exit 1. The plan is right that an executor following the item literally
  would leave the tree failing lint.
- F-2. Completed the fix (both assertions plus the binding): `All checks passed!` and `4 passed`
  WITH the 25th probe still present.
- F-7. Anti-hollowing holds in BOTH directions. A probe declaring `- Id: wr0ng1` in a `pr0be1` slot
  failed naming both tokens; a probe declaring NO `- Id:` failed with
  `declared in metadata region=None`. So the retained assertion is live, which is the P16 "never
  weaken" requirement.
- F-6. The load-bearing reason the `livecorpus` marker is refused reproduces exactly. In a synthetic
  repo, a modern-named walkthrough declaring no `- Id:` yields `aw check all --agent` -> `"findings":0`,
  exit 0, and `check_names`/`check_collisions` both `[]`; a MISMATCH yields `check.id6-identity-slot`.
  This test really is the repository's only guard for the missing-`- Id:` half, so marking it would
  trade a real coverage hole for a tripwire that subtraction already removes. The plan's OQ-01 is
  correctly resolved on evidence.
- F-8. Set analysis reproduces to the number: all 11 `LEGACY_WALKTHROUGHS` members return `None` from
  `_identity_slot_token`; the single `BULLETLESS_GRANDFATHERED` member carries slot `35xfvu` and
  declares nothing; neither set has a stale entry; 12 of 24 files reach the per-file comparison.

All probes were deleted and `git status --porcelain` is empty. No production or test file was
modified by this review.

THE BLOCKER IS NOT IN THE PLAN'S REASONING. IT IS AN OWNERSHIP COLLISION THE OVERLAP SURVEY MISSED.
`aisk5z` is ALREADY `approved` with an `- Approval:` attestation dated 2026-09-30, carries
`- Blocks-Release: next`, declares `tests/test_walkthrough_id6.py`, and its E-02 deletes the SAME two
assertions. F-9 missed it because the survey was scoped to Set `structpin` and the colliding plan
lives in Set `id6slotgate`. I enumerated every pending plan declaring that path: exactly two, these
two.

AND THE COLLISION IS WORSE THAN A RACE, WHICH IS WHY ORDERING ALONE WOULD NOT FIX IT. The two plans
disagree about the END STATE on two points. `aisk5z` E-02 DELETES `LEGACY_WALKTHROUGHS` (arguing the
loop's own `if not token: continue` is the shipped discriminator), where this plan's OQ-02
deliberately RETAINS it (arguing `nrqo90` E-06 required the grandfathering be stated). And `aisk5z`
E-07 ADDS an anti-vacuity floor computed from an INDEPENDENT name-shape rule, with E-09 proving it
fires under a simulated normalizer regression, where this plan's F-4 accepts the vacuity hole. Both
positions are defensible; they weigh a recorded decision against redundancy, and a hypothetical hole
against added mechanism, differently. Whichever plan runs second either reverts the other's decision
or lands on a file that no longer matches its own prose.

I DID NOT RESOLVE IT, AND THAT IS DELIBERATE. Every available resolution disposes of attested work:
retiring an APPROVED release-gated plan, retiring this one, or narrowing one and re-approving it. A
reviewer may not set `superseded` on an approved plan or silently reassign a release gate. So it is
escalated as BLOCKING OQ-03 carrying `- Finding: PR-001`, with the three options, their costs, and a
labelled recommendation (run `aisk5z`, which is already approved and a strict superset; retire this
plan `superseded` citing it; hand `zf1m48` off). `aw ipd lint` now reports `IPD-Q501` at every
checkpoint, which is exactly the fail-closed behavior that stops this plan executing into the
conflict.

TWO VALIDATION BARS WERE ALSO UNACHIEVABLE, and both would have stranded an executor on defects this
plan cannot cause: `aw check all --agent` CRASHES in this checkout, and the suite is not green. Both
are now unchanged-set deltas, with the narrow achievable claim (`check_collisions` returning zero)
kept separately so the item still asserts something real.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | C (architecture: duplicate paths); G (plan executability) | `.aw/records/plans/pending/20260929-id6slotgate-01-aisk5z-retire-the-walkthrough-identity-slot-defect-unpin-the-census.ipd.md` front matter (`- Status: approved`, `- Approval: 2026-09-30, recorded via aw ipd set: status set to approved`, `- Scope-Paths: tests/test_walkthrough_id6.py, ...`, `- Blocks-Release: next`) and its E-02, E-07, E-09; this plan's F-9 row | An ALREADY-APPROVED, release-gated plan in another Set declares this same file and deletes these same two assertions, and its intended end state CONTRADICTS this plan's on two points: `aisk5z` E-02 deletes `LEGACY_WALKTHROUGHS` where this plan's OQ-02 retains it, and `aisk5z` E-07 adds an anti-vacuity floor where this plan's F-4 accepts the hole. F-9 asserted no overlap, but surveyed only Set `structpin`; the collision is cross-Set. Whichever runs second reverts the other's decision or lands on a file that no longer matches its own prose. The two carriers are genuinely distinct (`zf1m48`, `mw0s1y`), so this is two real items converging on one guard, not a duplicate filing. | C:Medium-High; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | ESCALATED, NOT RESOLVED. Every fix disposes of attested work (retiring an approved release-gated plan, retiring this one, or narrowing and re-approving one), which is a maintainer decision under the approval contract and outside a reviewer's authority. Added BLOCKING OQ-03 carrying `- Finding: PR-001` with the measured facts, both points of disagreement, three options with costs, and a labelled recommendation (run `aisk5z`; retire this plan `superseded`; hand off `zf1m48`). F-9 corrected, F-11 added, Scope check carries a cross-plan row, the Deferred vacuity row notes the opposing disposition, and the gate paragraph leads with the block. `aw ipd lint` now reports `IPD-Q501`, which fails closed. `- Readiness: no-go`. |
| PR-002 | MEDIUM | IN-SCOPE | E (testing/verification); G | plan "Required tests / validation" item 6 and V-02(e); `agent_workflows/agent_schema.assert_valid_agent_record` | Validation item 6's bar is unachievable and one spelling of its command CRASHES. `aw check all --agent` raises `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next'` (the `next` hint embeds the worktree's absolute path); both `check all --agent` and plain `check all` exit 1; and the whole-tree `aw check` carries 51 pre-existing findings across 8 rules, so "the expected after-state is 0" cannot be met. An executor would chase a crash it did not cause or try to drive another party's findings to zero. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Item 6 rewritten: plain `aw check` with an unchanged RULE BREAKDOWN before and after, explicitly not requiring exit 0 or zero findings, with the crash recorded. The narrow claim the item was reaching for IS achievable and is kept as a separate assertion (`check_collisions(REPO_ROOT, include_retired=True)` returns 0 findings of every rule). V-02(e) reconciled. F-12 added. |
| PR-003 | MEDIUM | IN-SCOPE | E (testing/verification); G | plan "Required tests / validation" item 5 and V-02(e); `agent_workflows/backlog.py` (local clock) versus `agent_workflows/status_set.py` (UTC) | Item 5 frames the suite bar as a pass count "with no new failure" against a cited `3246 passed, 2 skipped`, but the tree is NOT green: `1 failed, 3457 passed, 2 skipped`, failing `test_release_exempt_setter_roundtrip_and_parity` on the pre-existing local-versus-UTC history-date skew (`TZ=UTC` passes; filed as `fnb8pl`, `lq2w86`, `2wae2x`, all release-gated). An executor would read that red as this plan's, or be tempted to fix a co-worker's gated test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Item 5 rewritten to an unchanged NAMED FAILURE SET re-derived before any edit, naming the pre-existing failure and its cause, forbidding both the fix and a `TZ` workaround under the shared-checkout rule, and demoting every written count to context. V-02(e) reconciled. F-13 added. |
| PR-004 | LOW | IN-SCOPE | G (plan executability) | plan F-9 row | F-9's claim is true of what it measured (Set `structpin`) and was stated as a general no-overlap conclusion supporting `Item-Dependencies: none`. That framing is what made PR-001 invisible: the row answers a narrower question than the one its consequence column claims to settle. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-9 retitled to state the scope it actually surveyed, with its consequence column corrected to say `Item-Dependencies: none` is correct for `structpin` and NOT sufficient, pointing at F-11. |
| PR-005 | LOW | IN-SCOPE | G (plan executability) | plan Scope check, Deferred row 3, approval gate | The BLOCKER touches claims restated in several places, and a correction is incomplete until every sibling is swept: the Scope check asserted a clean one-file scope, the Deferred vacuity row presented the accepted hole as unowned, and the gate paragraph's "no `- Readiness:` is written here" sentence became false once review wrote one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Swept: Scope check carries a CROSS-PLAN COLLISION row; the Deferred vacuity row records `aisk5z` E-07/E-09's opposing disposition and the vacuity trap it measured, with the carrier decline narrowed accordingly; the under-scope row points at the same; the gate paragraph now leads with the OQ-03 block, states the `IPD-Q501` consequence, and explains the `no-go` as reflecting the unresolved question rather than a defect in the plan's reasoning. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | An approved plan owns this file and wants a different end state. Pick a winner, or escalate? | ESCALATE as a BLOCKING open question with a labelled recommendation, and resolve nothing. | (a) Retire this plan `superseded` in favour of `aisk5z` - rejected as a REVIEWER act despite being my recommendation: it disposes of a reviewed plan and strands carrier `zf1m48`'s release gate, and `/plan-review` may not retire plans. (b) Retire or narrow `aisk5z` - rejected harder: it carries a human `- Approval:` attestation, and a reviewer editing an approved plan's scope would void an attestation it did not make. (c) Declare an `- Item-Dependencies:` edge and let both run - rejected on measurement: the two disagree on the END STATE (LEGACY_WALKTHROUGHS retained versus deleted; floor added versus declined), so ordering alone leaves the second plan's prose describing a file that no longer matches, which is how a plan comes to claim work it did not do. (d) Leave it in prose without a blocking question - rejected: prose gates nothing, and the lint gate is the only mechanism that actually stops dispatch. | `aisk5z` front matter and E-02/E-07/E-09 read at HEAD `a3e4d2c2`; enumeration of all pending plans declaring this path (exactly two); `plan-review` Step 4's escalation rule for an unfixed finding at or above the gate threshold; `IPD-Q501` confirmed firing after the edit. | yes |
| D-2 | `aw check all --agent` crashes and the suite is red at base. Relax the bars, or treat them as this plan's problem? | RELAX BOTH to unchanged-set deltas re-derived at execution, keeping the one narrow claim that IS achievable. | (a) Require the authored bars - rejected: both are unreachable through no fault of this plan, and holding them would either block a correct subtraction or pressure an executor into fixing another party's release-gated bug, which `AGENTS.md` forbids in a shared checkout. (b) Drop the two checks - rejected: item 6 is the only whole-tree conformance signal and item 5 the only whole-suite one; dropping them loses exactly the assurance a records-tree-touching plan needs, since its probes write under `.aw/records/walkthroughs/`. (c) File the `check all --agent` crash as a bug here - declined as scope: it is an unrelated sanitizer/record-shape defect in a different surface, this plan is a two-line subtraction, and recording the measurement in F-12 gives a later reader everything needed without widening an already-blocked plan. | measured `ValueError: Unsanitized absolute home path in field 'next'` from `assert_valid_agent_record`; exit 1 from both `check all` spellings; 51 findings across 8 rules from plain `aw check`; `1 failed, 3457 passed, 2 skipped` bare suite with `TZ=UTC` green on the narrowed run; `check_collisions(include_retired=True)` returning 0 findings. | yes |
| D-3 | One BLOCKER left OPEN. What verdict and readiness? | `REVIEWED - OPEN QUESTIONS` and `- Readiness: no-go`. | (a) `APPROVE WITH REVISIONS APPLIED` and `go-pending-approval` - rejected: a BLOCKER is unfixed and a BLOCKING question is open, which is precisely the `NO-GO` condition, and claiming otherwise would forge a clearance the review did not reach. (b) `REJECT - NEEDS REPLAN` - rejected: the plan's approach is SOUND and every one of its own measurements reproduced; the defect is an external ownership collision, which a maintainer answer resolves without any replanning. (c) Omit `- Readiness:` - rejected: absence is reserved for the exhausted orchestrator repair loop, and a consumer that finds no field cannot distinguish "no review ran" from "review said no", so writing `no-go` is the honest signal. | `plan-review` verdict and readiness vocabulary (an unresolved BLOCKING open question is a genuine not-ready condition); the `IPD-Q501` diagnostic confirming the gate fails closed; `review_findings_gate` absent from `.aw/config/project.json`, so the default `HIGH` threshold applies and a BLOCKER left OPEN must be escalated, which it is. | yes |
