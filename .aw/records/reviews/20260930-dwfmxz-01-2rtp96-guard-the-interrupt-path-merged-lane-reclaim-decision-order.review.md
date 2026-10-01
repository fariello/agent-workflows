# Review findings: plan 2rtp96

- Subject-Id: 2rtp96
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-701 (BLOCKER, fixed), PR-702 (MEDIUM, fixed), PR-703 (LOW, fixed), PR-704 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `9f6bdff78`. The plan file was committed and unmodified
before editing (`git status --short` empty), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) with ZERO diagnostics
and ZERO advisories, including no `IPD-Z602` density flag on any of the four E-items. This plan's own
first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

All probe work was done under the gitignored `tmp/` and removed afterwards. Two mutations were applied
to `agent_workflows/runner_shared.py` and REVERTED from a byte-level backup; `git status --short` is
empty and `git diff --stat agent_workflows/runner_shared.py` is empty. No production file and no test
was modified by this review.

THE DESIGN IS SOUND AND REVIEW CHANGED NO E-ITEM'S PURPOSE. I drove the real
`reclaim_lanes_on_interrupt` through BOTH host drivers on real git worktrees across all six lane
shapes rather than reading the plan's findings back, and the authored dispositions reproduce cell for
cell on both hosts:

```
IMPORT ORIGIN: <this worktree>/agent_workflows/__init__.py

===== HOST oc =====   (HOST agy identical on every row)
merged_accounted   action='reclaimed' holds_work=True merged=True dirty=False reclaimable=True wt_exists=False gate_calls=1 reason_codes=None reclaim_evs=1
    event keys: branch='aw/lane/merged' merged_into_target=True
merged_untracked   action='preserved' holds_work=True merged=True dirty=True  reclaimable=False wt_exists=True  gate_calls=0 reason_codes=None snapshot=True
    untracked file still on disk: True
merged_no_receipt  action='preserved' holds_work=True merged=True dirty=False reclaimable=True  wt_exists=True  gate_calls=1 reason_codes=['uncollected-submission']
merged_ignored     action='reclaimed' holds_work=True merged=True dirty=False reclaimable=True  wt_exists=False gate_calls=1 reason_codes=None reclaim_evs=1
    check-ignore rc=0 (0 == genuinely ignored)
empty_at_head      action='reclaimed' holds_work=False merged=True dirty=False reclaimable=True wt_exists=False gate_calls=0 reason_codes=None reclaim_evs=1
unmerged_dirty     action='preserved' holds_work=True merged=False dirty=True reclaimable=False wt_exists=True  gate_calls=0 snapshot=True
    stash list empty: True  dir exists: True
```

- F-01 REPRODUCES exactly. `19313eed` `--stat` shows `tests/test_worktree_lease_merged_reclaim.py |
  797 ----` and `tests/test_lane_retention.py | 1064 -----`; both are absent from disk. `rg` over
  `tests/` finds exactly ONE reference to `reclaim_lanes_on_interrupt`
  (`tests/test_oc_runipd.py:7027`) and ZERO to `lane_is_recovered_and_reclaimable`. I read that
  surviving test: it patches `driver._lane_reclaim_prompt` to return `"discard"` and asserts the
  worktree is removed, so it drives the operator-DISCARD branch and never the merged branch, exactly
  as F-01 says.
- F-02 REPRODUCES: the merged lane is simultaneously `merged_into_target=True`, `holds_work=True`,
  `dirty=False`, on both hosts. The defect's precondition holds.
- F-03 REPRODUCES: exactly one `lane-reclaimed-on-interrupt` record carrying `branch` and
  `merged_into_target=True`, on both hosts. The evidence E-02 will assert is producible.
- F-04 REPRODUCES in all four rows including the gate-spy counts, so the claim that only three of the
  four shapes reach the gate is confirmed by instrumentation rather than inference.
- F-05 REPRODUCES and is STRONGER than authored. Mutating the reclaimer so the recovered branch no
  longer precedes the `holds_work` bail-out flips the merged lane to `action='preserved'`,
  `worktree_exists=True`, `reason_codes=None`, gate calls 1 -> 0, identically on both hosts. The bare
  suite under the mutation: `3558 passed, 2 skipped, 3 warnings in 71.56s` - FULLY GREEN, so the
  shipped fix really can be reverted with nothing in the tree noticing. (The decision order is at
  relative lines 95 and 155 of `reclaim_lanes_on_interrupt` at this HEAD, confirming the plan's
  description of the structure without relying on its line numbers.)
- F-07 REPRODUCES including the subtle part: the merged+untracked lane makes ZERO gate calls and
  carries `reason_codes=None`, so the `dirty` clause one level earlier is indeed what holds, and a
  case asserting a retention reason code for that shape would be asserting an unpopulated field.
- F-10's tooled-route claim holds; the item resolves, though now at `graduated` rather than `open`.

ONE AUTHORED FINDING DOES NOT REPRODUCE AS WRITTEN, AND IT IS THE REASON THIS REVIEW WAS WORTH
RUNNING (PR-701). F-06 claims that removing the `holds_work` clause flips the provably-empty lane from
`reclaimed`/gone to `preserved`/on-disk. I built E-04(1)'s fixture exactly as E-01 specifies - which
instructs the shared fixture to write a COMPLETE collection receipt - applied that mutation, and the
case DID NOT FAIL on either host:

```
oc  receipt=True  action='reclaimed' wt_exists=False codes=None
agy receipt=True  action='reclaimed' wt_exists=False codes=None
oc  receipt=False action='preserved' wt_exists=True  codes=['uncollected-submission']
agy receipt=False action='preserved' wt_exists=True  codes=['uncollected-submission']
```

The divert happens either way (gate spy calls 0 -> 1, so the mutation does take effect), but with a
complete receipt `LaneInventory.uncollected_submission` is False, the lane classifies, and the gate
tears it down anyway. So the LEAK IS REAL and F-06's conclusion stands, but ONLY for a lane with no
receipt - and the plan never stated that condition while simultaneously instructing the fixture to
write one. Built as specified, the case asserting `action == 'reclaimed'` is GREEN under the very
mutation it exists to catch, and V-04's mandated failure is unobtainable. That is BLOCKER severity
because the plan makes a required piece of evidence impossible to produce honestly: an executor would
either stall or fabricate it. Fixed in three places (E-01's fixture parameter, E-04(1)'s required
absence plus an asserted precondition, V-04's new precondition bullet and explicit do-not-proceed
instruction), and recorded as a new F-11 with the measurement.

I ALSO CONFIRMED THE `z8ex9f` FORK IS STILL UNLANDED, which is what makes E-04's measure-then-branch
instruction currently a no-op rather than a live hazard: at this HEAD `LaneInventory` exposes no
landing or unmerged attribute (`dirty_tracked`, `unknown_untracked`, `unknown_ignored`,
`uncollected_submission`, `readable`, `classified`, `discardable`, `reason`, `reason_codes`,
`submission_detail`, `lane_root`, `index`, `count`, `failure`, `as_dict`, `unknown`) and
`inventory_lane` takes no `branch` parameter. Its STATUS, however, is `reviewed` rather than the
authored `to-review` (PR-703), so it is one human sign-off from executable and the fork is more likely
to be exercised than the plan implies.

OPEN QUESTIONS. All three are `Blocking: no` and `Status: resolved`, each answered from repository
evidence with its basis cited, and I re-checked all three rather than taking them on trust. OQ-01
(drive both hosts) holds: the shared body takes `lane_prompt` and `disable_prompt` as keyword-only
parameters with no default, and my probe confirms both hosts produce identical dispositions on all six
shapes, so the two-host table is both necessary and cheap. OQ-02 (assert the outcome, not the order)
holds and is reinforced by measurement: mutation (a) is caught by an `action` assertion and would NOT
be caught by a reason-code assertion, so the outcome assertion is strictly stronger here as the
question claims. OQ-03 (new module) holds: I read the surviving test and it does import one driver as
`driver` and patch `driver._lane_reclaim_prompt`, so it is single-host by construction as stated. No
new question was created; PR-701 was resolvable from repository evidence and is recorded as decision
D-1 rather than escalated.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | BLOCKER | IN-SCOPE | E. Testing and verification | plan E-01 ("write a COMPLETE collection receipt"), E-04(1), F-06, V-04; `agent_workflows/lane_containment.py` symbol `LaneInventory.classified` and `RETENTION_UNCOLLECTED_SUBMISSION` | E-04(1)'s case is VACUOUS as specified, and its mandated mutation demonstration is unobtainable. E-01 tells the shared fixture to write a COMPLETE collection receipt; E-04(1) then relies on the gate refusing the diverted empty lane for an UNCOLLECTED submission, which cannot happen when a complete receipt exists. Built that way with the `holds_work` clause removed, the lane IS diverted into the gate (spy 0 -> 1) and the gate tears it down: `action='reclaimed'`, `wt_exists=False`, `codes=None`, on BOTH hosts, so the case passes under the mutation it exists to catch. With no receipt: `action='preserved'`, `wt_exists=True`, `codes=['uncollected-submission']`, both hosts. V-04 therefore demands a failure the plan makes impossible, inviting a stall or a fabricated red | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 makes the receipt an explicit fixture parameter and states why two cases need it absent; E-04(1) requires NO receipt and asserts that absence as a precondition; F-06 rewritten with both receipt states measured; new F-11 records the non-reproduction; V-04 gains a precondition bullet and a do-not-proceed-on-green instruction; the gate's vacuous-guard warning now names both ways to build one |
| PR-702 | MEDIUM | IN-SCOPE | E. Testing and verification | plan F-09, Required tests, V-04, gate; bare suite at HEAD `9f6bdff78` | The suite baseline is asserted as a fixed fact (`1 failed, 3446 passed` at HEAD `94560471`) in four places, with the bar "the only failing node id must be the pre-existing one". Review's bare run is FULLY GREEN at `3558 passed, 2 skipped, 3 warnings in 116.38s` with that test PASSING, so the authored total drifted by 112 collected tests and the expected failure is conditional on the UTC clock, not a property of the tree. An executor holding the plan's bar would treat the ABSENCE of that failure as a discrepancy | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-09 rewritten to state the failure set as a live property carrying BOTH measurements; Required tests, V-04 and the gate's baseline paragraph and honesty rule all rewritten onto re-derive-then-compare-by-node-id, with the day-boundary test to be named only if it actually appears |
| PR-703 | LOW | IN-SCOPE | F. Honest documentation | plan F-08 and E-04; `.aw/records/plans/pending/20260930-nvymif-01-z8ex9f-...ipd.md` `- Status: reviewed` | F-08 and E-04 both describe `z8ex9f` as `- Status: to-review`. It is `reviewed`, so it is one human sign-off from executable rather than still awaiting critique. This understates the chance the fork lands before this plan executes, which is the only reason E-04's measure-then-branch instruction exists | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in F-08 and E-04, with the consequence stated (more likely to be exercised, same remedy); F-08 additionally records the review-HEAD proof that the fork is still UNLANDED (`LaneInventory` attribute census and `inventory_lane` signature), so the executor can tell which branch they are on |
| PR-704 | LOW | IN-SCOPE | F. Honest documentation | plan F-10; `.aw/records/backlog/graduated/20260929-dwfmxz-01-dwfmxz-reclaim-decision-order-unguarded.backlog.md` `- Status: graduated` | F-10 states the source item "resolves `open`" at an `open/` path. It is now `graduated` at a `graduated/` path, which is the correct state for an item handed off to a plan. A stale `open` claim invites an executor to think the handoff has not happened | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 corrected to record both states (open at authoring, graduated at review) and to restate that the executor must not transition it, consistent with the Scope check's fourth point |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-06's mutation demonstration does not fire with the fixture E-01 specifies. Is F-06 wrong, is the leak not real, or is the fixture wrong? | THE FIXTURE IS WRONG: the leak is real but requires NO collection receipt, so make the receipt an explicit fixture parameter and require its absence in E-04(1) with an asserted precondition. | (a) Delete F-06 and E-04(1) as unreproducible, rejected because the leak IS reproducible once the receipt is absent and it is the more serious of the two directions; (b) keep E-04(1) and let the executor discover the problem, rejected because V-04 mandates pasting a failure the plan makes impossible, which invites a fabricated red - the exact dishonesty the execution contract forbids; (c) weaken E-04(1) to assert the gate was reached rather than the disposition, rejected because that is the vacuous-guard failure mode the plan itself names (a reason-code or spy-count assertion is green under mutation (a)); (d) raise it as a blocking open question for the maintainer, rejected because the repository answered it: `LaneInventory.classified` is `readable and not unknown and not uncollected_submission`, so the receipt's presence fully determines the outcome and no human judgement is needed. | Probe across both receipt states on both hosts: `receipt=True -> action='reclaimed' wt_exists=False codes=None`; `receipt=False -> action='preserved' wt_exists=True codes=['uncollected-submission']`. Gate spy shows calls 0 -> 1 in both, proving the mutation took effect either way. `lane_containment.LaneInventory.classified` and `RETENTION_UNCOLLECTED_SUBMISSION` read. Recorded as F-11. | yes |
| D-2 | Two authored suite baselines now disagree with the tree (authoring `1 failed, 3446 passed`; review `3558 passed`, green). Pin the new number, or change the bar? | CHANGE THE BAR to re-derive-then-compare-by-node-id, and record BOTH measurements so the drift is visible rather than hidden behind a fresh constant. | (a) Pin `3558 passed`, rejected because it will drift exactly as 3446 did (112 in under a day, in a tree many lanes are changing); (b) keep the authored number and let the executor reconcile, rejected because the plan's bar makes the ABSENCE of the day-boundary failure look like a discrepancy; (c) tell the executor to ignore that test by name, rejected because a hard-coded exemption would mask a genuine future regression in it. | Bare run at `9f6bdff78`: `3558 passed, 2 skipped, 3 warnings in 116.38s` with `test_release_exempt_setter_roundtrip_and_parity` passing; the plan's own `1 failed, 3446 passed` at `94560471`. | yes |
| D-3 | Should the `z8ex9f` collision be converted into an `Item-Dependencies` edge now that the sibling is `reviewed` rather than `to-review`? | NO: keep the measure-then-branch instruction, and record the review-HEAD proof that the fork is unlanded so the executor can tell which branch they are on. | Declaring an `executed:` edge, rejected for the reason the plan already gives and which the status change does not overturn: the grammar offers no "prefer after", and gating a test-only plan behind an unrelated plan's full cycle costs more than the collision it avoids - especially as the measured remedy (adapt THIS module's fixture) is local and cheap. Dropping the instruction as speculative, rejected because the sibling is now one sign-off from executable, so the fork is MORE likely to be hit, not less. | `z8ex9f` front matter `- Status: reviewed` with `- Scope-Paths:` naming `agent_workflows/lane_containment.py`; review-HEAD census showing `LaneInventory` carries no landing attribute and `inventory_lane` no `branch` parameter; `runner_shared.lane_work_has_landed` reachable with a full `WorktreeHandle`. | yes |

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. Four findings, all FIXED, zero deferred, zero open. Structural lint
`conforming` with zero diagnostics and zero advisories at both `--phase author` and
`--phase review-finalize`. No unresolved blocking question, so readiness is `go-pending-approval`: the
plan passed review and awaits human sign-off.

A NOTE ON THE RELEASE GATE, since the plan invites a reviewer to disagree. I concur with its
judgement that no `- Blocks-Release:` is owed: the shipped behavior is CORRECT on both hosts for all
six shapes (measured above), so there is no live user-perceptible defect, only a missing guard, which
is latent risk. The plan states this honestly and cites measurements rather than a vibe, which is the
right way to make that call.
