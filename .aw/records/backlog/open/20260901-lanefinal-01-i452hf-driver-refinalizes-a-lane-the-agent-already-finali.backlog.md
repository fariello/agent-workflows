- Id: i452hf
- Status: open
- Set: lanefinal
- Priority: high
- Work-Kind: bug
- Summary: Driver self-finalize refuses with a STALE receipt because the agent already finalized in its lane: finalizing rewrites and moves the plan, invalidating the digest the driver froze from main, so completed work strands

## Workflow history
- 2026-09-01 triaged (opencode/its_direct/pt3-claude-opus-5-1m-us): DO NOT BUILD A NEW FIX. Found that approved plan `rchpms` (wtiso Phase 2, driver-owned lifecycle) already owns BOTH halves of this bug and named them in advance: its Concern cites stale-on-self-execution (backlog xmqv5l) AND 'NO WORKER-ROLE REFUSAL: nothing stops an in-lane aw ipd begin/finalize from forking a second receipt/run the driver cannot see', which is exactly the observed failure. Measured: rchpms is `approved`, passes `aw ipd lint --phase pre-execution` conforming, and its lane already holds TEN COMMITS of written work. So the action is LANDING existing reviewed work (via approved plan `6knsrx`, which covers five wtiso lanes and 26 unique commits), not authoring a competing design. If landing rchpms demonstrably fixes this, close this item citing the merge commit. What this item still uniquely adds and must keep: the measured field reproduction (both items of a real 2-item run hit it independently, $22.66 stranded, receipts verified byte-identical to main) and the note that evgi9n's E-07 test used --no-isolate-worktree and so never exercised the lane finalize path.
- 2026-09-01 created (aw backlog): Driver self-finalize refuses with a STALE receipt because the agent already finalized in its lane: finalizing rewrites and moves the plan, invalidating the digest the driver froze from main, so completed work strands

OBSERVED 2026-09-01 on run `run-20260901T042331Z-118022`, on BOTH items independently, so it is
systematic rather than a fluke. Cost: two finalizes refused after $22.66 of completed work, leaving
both plans in `pending/` with their work stranded on lanes.

WHAT HAPPENED, in order.

1. The driver ran `aw ipd begin` FROM MAIN, freezing `plan_content_digest` for each plan.
2. Each agent worked in its isolated lane, filled in the `E-*`/`V-*` state with evidence, and ran
   `aw ipd finalize` ITSELF. That succeeded: lane `aw/lane/m73aet` carries lifecycle commit
   `7df0564e` "lifecycle(m73aet): finalize m73aet -> executed", and the plan file in that lane now
   lives at `.aw/records/plans/executed/...`.
3. Finalizing REWRITES the plan (checked boxes, pasted `Observed evidence`, `- Status: executed`, a
   history line) and MOVES it to `executed/`.
4. The DRIVER then attempted its own self-finalize from main, recomputed the digest, and refused:
   "the begin receipt for m73aet is STALE: the plan content changed since begin".

THE GATE IS CORRECT; THE DESIGN INVITES THE MUTATION IT GUARDS AGAINST. Verified: both receipts match
MAIN's copy BYTE FOR BYTE (recomputed `ipd_lifecycle.plan_content_digest` against each receipt's own
`plan_path`), so nothing changed on main. The divergence is entirely lane-side, and it is the agent
doing exactly what it was told to do.

WHO TOLD THE AGENT TO FINALIZE, since this is the crux and not agent misbehavior:
- `.aw/records/plans/README.md:98` documents `aw ipd finalize ... --apply` as THE terminal transition.
- Every plan's own Approval-and-execution-gate section says so; `m73aet`'s reads: "the transition is
  performed by `aw ipd finalize`, never by hand."
- The executor PROMPT does NOT instruct it (grepped: the prompt mentions finalize only in the
  negative, "if the IPD cannot validly finalize, preserve partial work"), so the instruction comes
  from the repository contract the agent correctly read.
So both agents did the right thing per the contract, and the driver then duplicated the work and
failed on its own frozen fingerprint.

MEASURED CONSEQUENCE. Both items report `substantially-complete` with `worktree-preserved`, the plans
stay in `pending/` on main, and the actual product work is reachable only from the lane branches
(`aw/lane/m73aet`: `81c67a6f` implementation+tests, `98e15a15` plan-state, `7df0564e` lifecycle;
`aw/lane/6lu3rq` similarly). Nothing is lost, nothing is integrated, and a human merge is required -
which is the precise outcome `vju5ba` was fixed to eliminate.

RELATION TO `vju5ba`/`evgi9n`, and why that fix did not cover this. `evgi9n` made the integration GATE
reachable when validation is off, and it works: the predicate returns earned=True for a green suite.
But it addressed WHETHER the driver may finalize, not the case where the agent ALREADY DID. The
executed plan's own E-07 end-to-end test used `--no-isolate-worktree`, which never exercises the
lane-side finalize path, so this interaction was outside its coverage. That gap is recorded here rather
than being discovered a third time.

RELATION TO `xmqv5l` (finalize content-digest stale on self-execution), CHECKED rather than assumed:
it is the SAME ROOT CAUSE and a DIFFERENT trigger, so this is a sibling and not a duplicate.
`xmqv5l` names the general defect: `ipd_lifecycle.receipt_is_current` invalidates a receipt whenever
the plan text changes, while EXECUTING an IPD REQUIRES editing that same file (mark `E-*` performed,
fill `V-*` evidence). It is already `graduated` and referenced by the `wtiso` Set (`bl9q3d`, `58ha43`,
`1o4eif`). What it does NOT cover is the ISOLATED-LANE case observed here: two finalize attempts, one
in the lane by the agent and one from main by the driver, where the first legitimately MOVES the plan
to `executed/` and the second then measures a file that is no longer there. So a fix for `xmqv5l`
(frozen-region digest, or re-`begin` before finalize) is NECESSARY but NOT SUFFICIENT here: even with a
tolerant digest, the driver would still be attempting a SECOND finalize of an already-terminal plan.
Whoever fixes either should read both, and the ownership question below (who owns the terminal
transition under isolation) is the part `xmqv5l` does not answer.

DO NOT BUILD A NEW FIX FOR THIS: `rchpms` ALREADY OWNS IT, IS APPROVED, AND IS LARGELY WRITTEN.
Found 2026-09-01 while triaging this bug, and it changes the required action from "author a fix" to
"land existing work". `rchpms` is wtiso Phase 2, "driver-owned lifecycle", and its Concern names BOTH
halves of this bug BEFORE it happened:

  "(1) STALE-ON-SELF-EXECUTION (backlog xmqv5l): begin freezes a whole-file `plan_content_digest` ...
   and `receipt_is_current` invalidates the receipt whenever that byte digest changes; but a correct
   self-execution MUST edit the same plan (mark E performed, fill V evidence)"

  "(2) NO WORKER-ROLE REFUSAL: nothing stops an in-lane `aw ipd begin/finalize` from forking a second
   receipt/run the driver cannot see"

Item (2) is EXACTLY the failure observed on run `run-20260901T042331Z-118022`, described in advance.

STATUS OF THAT PLAN, measured: `- Status: approved`, `aw ipd lint --phase pre-execution` reports
CONFORMING, and its lane `aw/lane/rchpms` already holds TEN COMMITS of written work. So the fix exists
and passed review; it is unmerged, not unwritten.

WHAT THIS ITEM SHOULD BECOME, therefore: a pointer plus the fresh field evidence, NOT a competing
design. The action is to land the wtiso lane stack (approved plan `6knsrx` exists for exactly that,
covering five lanes and 26 unique commits, of which `rchpms` is one). If landing `rchpms` demonstrably
fixes this, CLOSE this item citing the merge commit rather than graduating it separately.

WHAT THIS ITEM STILL ADDS that `rchpms` does not have: the measured field reproduction (both items of a
real 2-item run hit it independently, $22.66 of work stranded, receipts verified byte-identical to
main), and the note that `evgi9n`'s E-07 end-to-end test used `--no-isolate-worktree` and therefore
never exercised the lane finalize path. Keep those; they are the regression evidence a fix should be
validated against.

WHAT TO SOLVE FOR, not prescribed.

1. WHO OWNS THE TERMINAL TRANSITION UNDER ISOLATION? The two candidates are mutually exclusive and the
   answer decides everything else: (a) the AGENT finalizes in-lane and the driver's job is to MERGE a
   lane that is already terminal, detecting that and skipping its own finalize; or (b) the DRIVER
   finalizes and the agent is told NOT to, which contradicts the repository contract every agent reads
   and would need that contract amended.
2. IF (a), the driver must DETECT an in-lane finalize rather than assuming failure. Cheap signals
   exist: the plan file's presence under `executed/` in the lane tree, a `lifecycle(<id6>): finalize`
   commit on the lane branch, or the lane-side finalize journal.
3. SHOULD THE RECEIPT DIGEST TOLERATE THE FINALIZE'S OWN EDITS? A frozen whole-file digest cannot, by
   construction, survive the transition it gates. Options: digest only the frozen REGION (scope,
   requirements) rather than the whole file; or re-`begin` immediately before finalize, which the
   `6knsrx` plan already prescribes for a different reason. Note a frozen-region digest weakens the
   tamper detection the whole-file digest provides, so this is a real trade rather than an obvious win.
4. DO NOT "FIX" THIS BY MAKING THE DRIVER FORCE THE TRANSITION. The refusal is the gate working. Any
   fix must keep a plan from reaching `executed/` without its evidence, which is the property that
   made the stale-receipt refusal correct here even though the outcome was inconvenient.

EVIDENCE. Run directory `.aw/records/runs/run-20260901T042331Z-118022/` (durable): `state.json`,
`events.jsonl` (2x `ipd-finalize-refused`, 2x `worktree-preserved`), and the per-item prompts. Lane
branches `aw/lane/m73aet` and `aw/lane/6lu3rq` hold the work. Receipts at
`.aw/state/ipd-lifecycle/{m73aet,6lu3rq}.receipt.json`, both frozen at base `26973ca6`.
