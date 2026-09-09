- Id: gjadwm
- Status: graduated
- Blocks-Release: next
- Set: gatejrnl
- Priority: medium
- Work-Kind: bug
- Summary: executed-transition pre-commit gate false-positives on any follow-up commit to a legitimately finalized plan, because the finalize journal it looks for is deleted on success

## Workflow history
- 2026-09-08 note (opencode/its_direct/pt3-claude-opus-5-1m-us): CASE 2 REPRODUCED INDEPENDENTLY ON MAIN at HEAD 22364e27, during an `aw doctor` cleanup unrelated to this item, which matters because it shows the defect is hit by ORDINARY work and not only by a contrived path. I staged a body-only edit to `.aw/records/plans/executed/20260901-ctlroot-01-eulhzt-...ipd.md` (a citation rewrite inside a V-08 `Observed evidence` block, performed automatically by `aw rename backlog ... --apply` when it rewrote inbound references to a renamed backlog item) and the pre-commit hook REFUSED with `raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/`. That plan had been in `executed/` since 2026-09-01; the commit did not move it, did not touch its `- Status:` line, and changed its lifecycle in no way. MY DIAGNOSIS, reached by reading the detector before reading this item, MATCHES THE ONE RECORDED BELOW: `git diff --cached --name-status -M` emits `M<TAB><path>` for a plain edit, so the A/M/C branch at `executed_transition_gate.py:132-137` sets `old_path=None`, and `moved_into_executed` at `:146-148` is `_EXECUTED_SEGMENT in ("/" + new_path) and (old_path is None or ...)`, so the `old_path is None` disjunct ALONE satisfies it and an in-place edit is classified as a move INTO `executed/`. I also confirm the discriminator this item proposes as the safe fix: for that same edit the HEAD blob AT THE SAME PATH exists and `gained_executed` is False, so asking "was this path already under `executed/` at HEAD?" separates case 2 from every genuine transition. NO CODE CHANGED, per the graduation: plan `i4c0c3` owns this and is at `- Status: reviewed`. WHAT THE FALSE POSITIVE COST, recorded because it is this item's own stated risk ("a gate that false-positives on correct behavior TRAINS agents to bypass it"): the honest options at that moment were `--no-verify`, an out-of-scope commit, or dropping a legitimate edit. I chose to DROP the edit, so eulhzt's V-08 evidence block deliberately keeps a now-stale filename (arguably correct anyway, since it quotes what a tool printed at execution time). The gate did not prevent a bad commit here; it removed a good one.
- 2026-09-08 graduated (aw set): PARTIALLY OBSOLETE. Graduated ONLY CASE 2 to plan i4c0c3 (Set gatejrnl, .aw/records/plans/pending/20260908-gatejrnl-01-i4c0c3-...ipd.md), which carries From-Backlog: gjadwm and inherits this item's Blocks-Release: next. Status graduated (design handed off), NOT done. CASE 1 IS ALREADY OWNED AND IS NOT GRADUATED: approved plan 29wvmj (Set integpath, Order 01, From-Backlog: rnl3b7, - Status: approved) covers the lane-merge case completely. Its E-01 adds the merge-context detector resolving the git dir via 'git rev-parse --git-dir' (correctly handling a worktree, where .git is a FILE); E-02 adds the IN-TREE finalize-evidence predicate accepting a 'lifecycle(<id6>): finalize' commit reachable from the incoming side but not from HEAD, which is exactly this item's 'make the evidence portable' candidate; E-03 preserves four refusal cases including a hand-edit staged INSIDE a merge, answering this item's own warning that a blanket merge exemption would be wrong; E-04 makes the merge refusal actionable; E-05 tests through a real 'git merge --no-ff --no-commit'; and E-06 installs the gate on pre-merge-commit as well, closing an automated-merge hole this item did not know about. It is approved and will land before i4c0c3 runs, so re-implementing case 1 would be duplicated work. CASE 2 SURVIVES AND REPRODUCES, verified 2026-09-08 at HEAD 8b4e1570 in a throwaway repo: a plan committed in executed/, then a body-only edit and 'git add', makes hooks.executed_transition_gate.check() return rc 1 with 'raw plan->executed transition (moved into executed/) with NO matching finalize evidence in .aw/state/'. THIS ITEM'S DIAGNOSIS OF CASE 2 IS WRONG, and the correction shrinks the work from a durable-state redesign to a one-predicate fix, so it is recorded here to stop the next reader implementing the expensive version. The cause is NOT the journal being deleted on success. It is that 'git diff --cached --name-status -M' reports 'M<TAB><path>' for a plain edit, the detector's A/M/C branch therefore sets old_path=None (executed_transition_gate.py:120-126), and moved_into_executed is computed as '_EXECUTED_SEGMENT in ("/" + new_path) and (old_path is None or ...)' (:132-134), so 'old_path is None' satisfies the second clause and an ordinary edit is classified as a MOVE INTO executed/. Measured the discriminator that makes the fix safe and narrow: for that same edit the HEAD blob AT THE SAME PATH exists, and gained_executed evaluates False, so asking 'was this path already under executed/ at HEAD?' separates case 2 from every genuine transition. The two firing conditions are independent and OR'd (:141), so fixing the path test cannot disarm the in-place status-flip refusal, which keeps refusing via gained_executed (pinned by tests/test_executed_transition_gate.py:96-107). THEREFORE this item's options 1 and 3 (accept the begin receipt; retain a durable finalize completion record) are NOT NEEDED for case 2 and are recorded as deliberately dropped: no evidence of any kind is required, because no transition is occurring. This item's own option 4 anticipated the real cause ('the staged-rename detection may be over-broad') and is what i4c0c3 implements. Its option 5 (make the hook advisory / move enforcement to aw check) is left alone as a policy question, and its CONSTRAINT is honored: no refusal is weakened, and ten existing pinned behaviors must pass unmodified. Sibling items xmqv5l and v880xk remain open and are not mine to touch.
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

OBSERVED 2026-08-30, twice, in two different shapes.

THE GATE. The opt-in pre-commit hook `ipd-executed-transition-gate`
(`agent_workflows/hooks/executed_transition_gate.py`) refuses a commit that stages a plan file into
`.aw/records/plans/executed/` unless it can find a finalize-transaction JOURNAL for that plan id whose
recorded destination matches the staged path. Its purpose is real and worth keeping: it stops an agent
hand-editing or `git mv`-ing a plan into `executed/` to claim completion without passing the receipt,
scope, and attribution gates. It is a probability reducer against sloppiness and greenwashing, not a
security boundary.

THE DEFECT. The journal is a TRANSACTION artifact: finalize writes it while the two-phase transaction
is in flight and DELETES it on successful completion. So the evidence the gate requires is, by design,
absent exactly when the transition was most cleanly performed. Any commit that stages an
already-legitimately-finalized plan therefore trips the gate. Two real cases hit today:

CASE 1, merging a lane-finalized plan. Under worktree isolation the driver runs `aw ipd finalize`
INSIDE the lane, so the lifecycle commit (`lifecycle(<id6>): finalize <id6> -> executed`) lives on the
lane branch and the journal was consumed there hours earlier. Merging that lane into main stages the
`pending/` -> `executed/` rename, the gate sees no journal, and refuses. Reproduced while landing 15
lane branches by hand: `8h9lap` refused with "raw plan->executed transition (moved into executed/)
with NO matching finalize evidence in .aw/state/" even though `aw/lane/8h9lap` contains commit
fecd4a26 doing exactly the finalize the gate is asking for.

CASE 2, a follow-up commit to a plan already finalized in THIS tree. After `aw ipd finalize af7i6p`
completed (lifecycle commit 3b1df90f), a one-line correction to that same plan file was refused for
the identical reason. The plan was in `executed/`, the finalize was genuine and minutes old, and the
journal was already gone.

NOTE the gate is not merely unlucky about timing: a BEGIN receipt for the plan DID exist in both cases
(`.aw/state/ipd-lifecycle/<id6>.receipt.json`), and the module's own docstring explains why it
deliberately does not accept the receipt as proof (the receipt carries the pending-time digest and is
consumed only after the commit, so the journal was chosen as the present-at-commit-time proof). That
reasoning is sound for the single-tree, in-flight case and simply does not cover these two.

WORKAROUND USED, and its cost. Both commits went through with `--no-verify` under explicit maintainer
authorization scoped to this session's manual lane cleanup. That is exactly the wrong habit to
normalize: this repo has already seen an agent reach for `--no-verify` "accidentally", and a gate that
false-positives on correct behavior TRAINS agents to bypass it. The frequency matters more than the
individual case.

WHAT TO SOLVE FOR, not a prescribed fix.
1. What is the honest present-at-commit-time proof that a `pending` -> `executed` transition was
   performed by finalize rather than by hand? Candidates to evaluate, none obviously right: the
   lifecycle COMMIT in the staged history (greppable, but forgeable by a determined agent and awkward
   for a merge commit); a durable finalize RECEIPT or ledger entry written on success and retained
   rather than deleted; a signed or content-addressed marker inside the plan's own workflow history;
   or accepting a merge whose other parent contains a matching lifecycle commit.
2. Should the gate treat a MERGE COMMIT differently from a direct commit at all? Under worktree
   isolation, merging is the normal integration path and the finalize provably happened elsewhere.
   A merge-aware rule may be most of the fix.
3. Should finalize RETAIN a completion record instead of deleting the journal? Cheap, but it turns a
   transient transaction artifact into durable state that then needs its own lifecycle, and the
   machine-local `.aw/state/` tree is already the subject of relocation work (wtiso Phase 4, 58ha43).
4. What happens on a FOLLOW-UP commit to a plan already in `executed/` (case 2)? Arguably the gate
   should only fire on a transition INTO `executed/`, not on subsequent edits to a file already
   there; the staged-rename detection may be over-broad.
5. Is the local hook the right enforcement point at all, given it is skippable and not cloned by
   default, and `aw check`/`aw doctor` are described as the portable backstop? If the backstop is the
   real authority, the hook could be advisory and stop teaching bypass.

CONSTRAINT for whoever takes this. Do NOT weaken the gate into uselessness to quiet it. The hand-`git
mv` path it blocks is a genuine greenwashing vector and one this repo cares about. The goal is a proof
predicate that accepts a REAL finalize performed in another tree or at an earlier commit, while still
refusing a plan that simply appeared in `executed/` with no finalize anywhere.

RELATED. Backlog xmqv5l (begin freezes a whole-file digest, so recording V evidence invalidates the
receipt) is the same machinery failing for a neighbouring reason and was ALSO hit during the same
af7i6p finalize, forcing a re-issued begin. Backlog v880xk (a stale frozen base makes scope-drift emit
~1000 findings) is a third. Three independent defects in the receipt/journal layer in one session
suggests the whole finalize-evidence model deserves a single coherent look rather than three patches.
Plan wtisoland 6knsrx must merge more lane-finalized plans and will hit case 1 again.

DISCOVERED while hand-merging 15 lane branches after an overnight run in which validation was disabled,
so 21 plans self-finalized inside their lanes without integrating.
