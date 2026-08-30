- Id: gjadwm
- Status: open
- Set: gatejrnl
- Priority: medium
- Work-Kind: bug
- Summary: executed-transition pre-commit gate false-positives on any follow-up commit to a legitimately finalized plan, because the finalize journal it looks for is deleted on success

## Workflow history
- 2026-08-30 created (aw backlog): executed-transition pre-commit gate false-positives on any follow-up commit to a legitimately finalized plan, because the finalize journal it looks for is deleted on success

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
