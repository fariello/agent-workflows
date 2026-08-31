# IPD: Route a resumed turn whose lane already holds its work to verify-and-continue instead of re-executing from scratch

- Date: 2026-08-31
- Kind: child
- Concern: A resumed run re-executes work it already committed on its own lane, producing byte-identical duplicate commits and doubling spend, because the decision is delegated to the agent's judgment via the prompt rather than made by the driver from facts it already observes.
- Scope: Have the DRIVER classify a recovery turn's lane before dispatching it, and route a lane that already holds the plan's work to a verify-and-continue turn instead of a fresh execution turn. Consumes the shipped `worktree_lease.inspect_lane` classification and the shipped INTERRUPTED SNAPSHOT convention as the completeness signal. Does NOT remove or weaken the existing recovery prompt notice, does NOT add an acknowledgement gate, and does NOT change first-attempt behavior.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_resumedupe.py
- Item-Dependencies: none
- Status: to-review
- Set: resumedupe
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: txc9l1
- From-Backlog: k1nity

## Workflow history

- 2026-08-31 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `k1nity`. Its Q1 (put the lane's actual state in the prompt) is ALREADY BUILT and is therefore NOT this plan's remedy: `build_recovery_lane_notice` (`oc_runipd.py:3485`) already names the lane branch, its commit count, its dirty state and the snapshot convention, and the duplication was measured AFTER that landed. That finding is the whole justification for taking Q2 instead: the judgment moves to the driver, which already holds the facts. Q3's completeness signal is the shipped INTERRUPTED SNAPSHOT commit. No `Blocks-Release` gate: the item carries none, and it is wasted spend plus confusing history rather than a data-safety bug.
- 2026-08-31 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop paying for a full turn to redo work that is already committed. On at least three resumed runs the second attempt produced a byte-identical duplicate: on `ntf6sx` four commits where two were expected, with `git diff fb0774b2 7e9c4444` over the plan's own files EMPTY. Telling the agent it is resuming has already been tried and is demonstrably insufficient; this plan moves the decision to the driver, which can compare the lane against its frozen base without asking anyone.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: classify the lane before dispatching a recovery turn

- [ ] E-01 Add `classify_recovery_disposition(repo, item, state)` to `oc_runipd.py` returning a typed decision of `fresh-execution`, `verify-and-continue`, or `undetermined`, computed from the SHIPPED `worktree_lease.inspect_lane` reading (`worktree_lease.py:203`) which already reports `commits_ahead`, `dirty`, the lane's own base sha, and one of the five `LANE_STATES`. Decide `verify-and-continue` only when the lane holds at least one commit that is NOT an INTERRUPTED SNAPSHOT; decide `fresh-execution` when the lane is absent, empty, or holds only a snapshot; decide `undetermined` when the lane cannot be read. Pure function of an inspection result: no mutation, no git writes.
  - Depends on: none
  - Expected outcome: a lane with 2 real commits classifies `verify-and-continue`; an absent or empty lane classifies `fresh-execution`; a lane holding ONLY an INTERRUPTED SNAPSHOT commit classifies `fresh-execution`; an unreadable lane classifies `undetermined`.
  - Execution state: pending

- [ ] E-02 Distinguish a real commit from a preservation snapshot using the shipped message convention rather than a new marker: `worktree_lease.py:699-700` writes `WIP INTERRUPTED SNAPSHOT (not finished work): lane <id>`. Promote that literal to a module-level constant in `worktree_lease.py` and consume it in both places that currently hardcode the phrase in prose (`oc_runipd.py:3552`, `agy_runipd.py:2375`) plus the new classifier, so the driver's decision and the prompt's explanation can never disagree about what the marker is. This is the completeness signal the backlog item's Q3 asks for: a snapshot means work was preserved mid-edit, so redoing it IS correct.
  - Depends on: E-01
  - Expected outcome: the literal appears exactly once as a definition; `grep -c 'INTERRUPTED SNAPSHOT'` shows the two driver prose sites and the classifier all referencing the constant; a commit whose message carries it is never counted as finished work.
  - Execution state: pending

- [ ] E-03 Treat `undetermined` as fresh execution, and say so where it is decided. If the lane cannot be read the driver must NOT silently skip execution, because skipping risks leaving a plan unimplemented, which is a worse failure than paying for a duplicate turn. This is a deliberate fail-toward-doing-the-work choice and is the OPPOSITE of the fail-closed stance used for lifecycle gates; record the asymmetry in a comment so a later reader does not "fix" it into a refusal.
  - Depends on: E-01
  - Expected outcome: an unreadable lane produces a fresh-execution dispatch plus a recorded reason; no code path turns an inspection failure into a skipped item.
  - Execution state: pending

### Task group 2: dispatch the verify-and-continue turn

- [ ] E-04 When the disposition is `verify-and-continue`, dispatch a turn whose prompt asks the agent to VERIFY and COMPLETE what the lane already contains rather than to implement the plan, and pass it the lane's concrete facts: the commit shas, their subjects, and the diffstat against the frozen base. Build this as a variant of the EXISTING recovery branch, extending `build_recovery_lane_notice` (`oc_runipd.py:3485`) rather than adding a second prompt mechanism, and keep its stated constraints: no acknowledgement gate and no refusal path, because a refusal is one more way for an unattended run to stall. Apply the identical change to `agy_runipd.py:2375`'s twin, sharing one helper so a one-runner fix cannot leave the other duplicating.
  - Depends on: E-02, E-03
  - Expected outcome: a `verify-and-continue` prompt contains the lane's actual commit shas and diffstat and asks for verification-and-completion; a `fresh-execution` recovery prompt is UNCHANGED from today's text; a first-attempt prompt is unchanged.
  - Execution state: pending

- [ ] E-05 Record the routing decision and its inputs in the run's durable state and events, so an operator can see WHY a turn was routed as it was without re-deriving it. Include the disposition, the observed `commits_ahead`, whether a snapshot was present, and the reason string. Without this, a wrong routing decision is invisible after the fact, which is the same diagnosability gap that made the original duplication take three runs to notice.
  - Depends on: E-04
  - Expected outcome: the item's state carries the disposition and its inputs, and an event records the routing; a run that routed to `verify-and-continue` is distinguishable from one that re-executed, in state alone.
  - Execution state: pending

### Task group 3: falsifiable tests

- [ ] E-06 Add `tests/test_resumedupe.py` and SABOTAGE every assertion before trusting it. Required cases: (a) THE REGRESSION CASE, reconstructing the measured `ntf6sx` shape (a lane holding two real commits on resume) and asserting the driver routes `verify-and-continue`, NOT a fresh execution; (b) a snapshot-only lane routes `fresh-execution`, proving the completeness signal works and that the plan does not blanket-skip whenever commits exist; (c) an absent and an empty lane both route `fresh-execution`; (d) an unreadable lane routes `fresh-execution` with a reason (E-03); (e) a FIRST attempt is untouched; (f) both drivers agree across the whole matrix. Assert on the routing decision and on prompt CONTENT (the shas present in the verify prompt), not on the mere presence of the word "recovery", which appears in unrelated prose and would pass against a stub.
  - Depends on: E-05
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_resumedupe.py` passes, and each case was verified to FAIL when its branch is deliberately broken.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `worktree_lease.inspect_lane` (`:203`) is the non-mutating lane classifier and its docstring states it "never runs a write command". It already reports `commits_ahead`, `dirty`, the lane's own base sha and one of five `LANE_STATES` (`:103`), so the driver needs no new probing.
- The recovery prompt deliberately has NO acknowledgement gate and NO refusal path, stated in `build_recovery_lane_notice`'s docstring: "a refusal would be one more way for an unattended run to stall". Preserve that.
- The INTERRUPTED SNAPSHOT message is written in one place (`worktree_lease.py:699`) but its phrasing is hardcoded again as prose in both drivers (`oc_runipd.py:3552`, `agy_runipd.py:2375`).
- The two drivers duplicate this logic verbatim; the pending `rununify` Set exists to de-duplicate them, so new logic must be shared, not copied.
- Preserving work beats tidiness: `oc_runipd.py:2501` keeps a non-integrated lane on purpose under a "forward-progress rule: never discard work".

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **The item's own first suggestion (Q1, put the lane state in the prompt) IS ALREADY BUILT, so it cannot be the fix.** `build_recovery_lane_notice` (`oc_runipd.py:3485`) already renders the lane branch and path, "it HOLDS N commit(s) beyond its base", "its tree has uncommitted changes", and an explanation of the INTERRUPTED SNAPSHOT marker. The duplication was measured after `zwnjp3` E-11 landed that notice. | The function read in full at `oc_runipd.py:3485-3556`. |
| F-2 | **So this is decisive evidence that informing is necessary and NOT sufficient.** The agent was told it was resuming, was told its lane already held commits, and still redid the work. That is the argument for moving the judgment to the driver (the item's Q2) rather than strengthening the prose again. | F-1 plus the measured duplication on `ntf6sx`. |
| F-3 | **The driver already has every fact it needs, so this is a routing change and not new observation machinery.** `inspect_lane` is non-mutating by contract and already returns `commits_ahead`, `dirty`, the lane base and a five-value state classification. | `worktree_lease.py:203-214` and `LANE_STATES` at `:103`. |
| F-4 | **A blanket "skip if commits exist" would be WRONG, and the shipped snapshot commit is the signal that makes it safe.** A turn interrupted mid-edit may have committed something incomplete, in which case redoing it is correct. `worktree_lease.py:699` writes `WIP INTERRUPTED SNAPSHOT (not finished work)` for exactly that case, explicitly "NOT validated or reviewed work", which lets the classifier separate preserved-mid-edit from finished. | `worktree_lease.py:695-706`. |
| F-5 | **The marker's phrasing is duplicated as prose in both drivers, so it can drift.** `oc_runipd.py:3552` and `agy_runipd.py:2375` each hardcode the phrase in prompt text while `worktree_lease.py:699` writes the actual commit message. A classifier keying on a third copy would be a fourth place to drift; E-02 collapses this to one constant. | The three cited sites. |
| F-6 | **Measured cost, and the honest reason this is not urgent.** Roughly one full turn per resumed item, with a turn ranging about $3 to $30 in the observed runs. Nothing is lost and the resulting trees are correct, so this is wasted spend plus a lane history a human must read at merge time. It carries no `Blocks-Release` gate, unlike `vju5ba`. | Backlog `k1nity`; the item's own NOT A DATA-SAFETY BUG note. |
| F-7 | **This compounds `vju5ba`, which is why that one is sequenced first.** With validation off nothing self-finalizes, so lanes accumulate and resumes become more likely, which increases how often this bug fires. Fixing `vju5ba` reduces this bug's frequency without fixing its mechanism. | Backlog `k1nity` and `vju5ba` RELATED sections; `vju5ba` graduated as plan `evgi9n`. |

## Proposed changes (ordered, validatable)

1. A pure lane classifier over the shipped `inspect_lane` reading, returning a typed routing decision (E-01), with the snapshot marker collapsed to one shared constant (E-02) and an explicit fail-toward-executing choice for unreadable lanes (E-03).
2. A verify-and-continue dispatch carrying the lane's real shas and diffstat, extending the existing recovery notice in both drivers via one shared helper (E-04).
3. Durable recording of the routing decision and its inputs (E-05).
4. Sabotage-verified tests including a reconstruction of the measured duplication (E-06).

## Deferred / out of scope (with reason)

- **Strengthening the recovery prompt's prose further.** Explicitly rejected: F-1 shows the prompt already carries the lane facts and F-2 shows that was insufficient. More prose is the approach this plan exists to replace.
- **An acknowledgement gate requiring the agent to confirm it inspected the lane.** The maintainer chose the lightweight notice over exactly this, and `build_recovery_lane_notice`'s docstring records why: a refusal path is another way for an unattended run to stall. E-04 preserves that.
- **Automatically amending, squashing or discarding duplicate commits already on a lane.** Cleaning history is a separate concern from not creating the duplicate, and it conflicts with the shipped never-discard-work rule (`oc_runipd.py:2501`).
- **De-duplicating the two drivers.** Owned by the pending `rununify` Set; this plan adds a shared helper consumed by both.
- **Detecting duplication AFTER the fact and reporting it.** Would be useful diagnostics but does not save the spend, which is the item's point. E-05's recorded decision gives most of the diagnostic value for free.

## Scope check

- Over-scope: `worktree_lease.py` is edited by E-02 (promoting the message to a constant) but is NOT in Scope-Paths. Either add it before executing or have E-02 define the constant in a Scope-Paths module and consume it in `worktree_lease.py`; the reviewer should rule. Recorded rather than silently resolved because an out-of-scope edit is exactly what `finalize_precheck`'s scope comparison refuses.
- Under-scope: no third driver exists; the recovery-notice sites are exactly `oc_runipd.py:3485` and `agy_runipd.py:2375`.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_resumedupe.py` for per-test counts.
- The full suite BARE, `python3 -m pytest`, from the PRIMARY checkout, reconciled against the baseline `3864 passed, 3 skipped, 4 xfailed`. Validate in the primary checkout, never a scratch worktree (`dh0uno`).
- A real interrupted-then-resumed run showing the second turn did NOT re-commit the same work: paste the lane's `git log --oneline` proving no byte-identical duplicate pair, in the shape the `ntf6sx` measurement used (`git diff <first> <second>` over the plan's files being empty is the SYMPTOM being eliminated).
- `aw ipd lint --phase pre-transition` conforming on this plan.

## Spec / documentation sync

- No spec change: no shipped spec asserts how a recovery turn is dispatched.
- If the routing decision becomes operator-visible in the run report, the report's own documentation should name the three dispositions; otherwise N/A.

## Open questions

### OQ-01: Should `verify-and-continue` be allowed to conclude "already complete" and finalize without any further edit?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Proceeding with YES, because that is the case the whole plan targets: on `ntf6sx` the work was genuinely finished and the second turn changed nothing. The turn still passes through `aw ipd finalize`'s own independent fail-closed gate (`finalize_precheck`, `ipd_lifecycle.py:1055`), which requires a current begin receipt, every `E-*` performed, every `V-*` passing with non-empty evidence, and an in-scope diff, so "already complete" cannot become a way to skip validation.

### OQ-02: Should the classifier also compare the lane's diff against the plan's `Scope-Paths` to judge whether the work is THIS plan's?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Deferred as an enhancement, not adopted now. A lane is allocated per item and named for it (`worktree_lease.lane_branch_name`), so commits on it are already attributable without a path comparison, and `finalize_precheck` performs the authoritative scope reconciliation later anyway. Adding a second, weaker scope judgment here risks disagreeing with that one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the classifier's decision for four constructed lanes (2 real commits; absent; empty; snapshot-only) showing `verify-and-continue`, `fresh-execution`, `fresh-execution`, `fresh-execution` respectively. Confirm in prose that the classifier performed no git WRITE, citing that it consumes `inspect_lane`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the constant's definition site and the output of a grep proving every consumer (both driver prose sites and the classifier) references it rather than re-spelling the phrase; plus the classifier's decision on a snapshot-only lane showing the marker was honored.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the decision and recorded reason for a deliberately unreadable lane, showing `fresh-execution` rather than a skip, and quote the comment recording the deliberate asymmetry against the fail-closed lifecycle gates.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the generated `verify-and-continue` prompt showing the lane's ACTUAL commit shas and diffstat, alongside a `fresh-execution` recovery prompt diffed against today's text to prove it is unchanged, and a first-attempt prompt likewise unchanged. Also show both drivers produce the same prompt shape.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the durable state excerpt and the event record for one routed run, showing the disposition, `commits_ahead`, snapshot presence and reason; confirm a re-executed run and a verify-and-continue run are distinguishable from state alone.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the COMPLETE `python3 -m pytest -o addopts="" tests/test_resumedupe.py` output with per-test names and exit code, PLUS for each of the six cases the FAILING output produced when its branch is deliberately broken, then confirm each break was reverted. Also paste the bare full-suite summary line reconciled against the `3864 passed, 3 skipped, 4 xfailed` baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. It changes whether an item's work is executed at all on a resume, so the dangerous failure is NOT a duplicate commit but a SKIPPED implementation: E-03's fail-toward-executing choice and V-03 exist precisely to make that direction impossible, and neither may be waived.

Execution contract: commit only files this plan changed, path-scoped, and never push. Other agents and runs are ACTIVE in this shared checkout, so before every commit verify the staged set with `git diff --cached --name-only` and `git restore --staged` anything not yours. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`). Resolve the `worktree_lease.py` scope question recorded under Scope check BEFORE editing that file.

Post-gate lifecycle: on completion move this plan to `.aw/records/plans/executed/` with `- Status: executed`, per the `ipd-lifecycle` workflow, only after every `V-*` above carries pasted evidence.
