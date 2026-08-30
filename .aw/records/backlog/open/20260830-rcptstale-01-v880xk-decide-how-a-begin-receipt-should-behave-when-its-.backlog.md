- Id: v880xk
- Status: open
- Set: rcptstale
- Priority: medium
- Kind: bug
- Summary: Decide how a begin receipt should behave when its frozen base goes stale: scope-drift emits ~1000 findings for plans that are not actually drifting

## Workflow history
- 2026-08-30 created (aw backlog): Decide how a begin receipt should behave when its frozen base goes stale: scope-drift emits ~1000 findings for plans that are not actually drifting

THIS ITEM IS AN EXPLORATION, NOT A FIX. Do not graduate it into a plan that implements receipt
expiration. The maintainer explicitly declined that as the presumed answer, and the reason is recorded
below under REJECTED FRAMING. The deliverable is a decision about what a frozen base MEANS once main
has moved, backed by evidence; the implementation follows from that decision.

OBSERVED 2026-08-30, with numbers. After merging 15 lane branches into main, `aw check all` went from
93 findings to 1106. 1013 of those 1013-vs-93 delta findings are ONE rule, `check.scope-drift`, spread
across exactly 16 plans at roughly 116 to 158 findings each. Measured per-plan counts: qcqhj7 158,
58ha43 154, 2c122z 154, rchpms 154, 1o4eif 148, j4v6ga 118, and ten more at 114 to 116.

MECHANISM (verified, not inferred). `aw ipd begin` writes `.aw/state/ipd-lifecycle/<id6>.receipt.json`
recording a `base_head` (the commit HEAD was at when execution was authorized), the actor, timestamp,
plan digest, and the plan's declared Scope-Paths. `check.scope-drift` asks, for any plan holding an
ACTIVE receipt, whether the paths changed since `base_head` fall outside that plan's Scope-Paths. The
rule emits one finding PER OFFENDING FILE. When main advances far past `base_head`, the diff from the
frozen base to HEAD becomes the whole intervening history, so a single stale receipt multiplies into
one finding per file in that history. Sample bases from the affected receipts: qcqhj7 froze at
762fd9de on 2026-08-29T19:37Z, af7i6p and 2ouj70 at be49ac47 on 2026-08-30T04:45Z, j4v6ga at d4d265b6
on 2026-08-30T07:14Z; HEAD is now many merges beyond all of them.

WHAT IS AND IS NOT BROKEN. The plans are unmodified and their Scope-Paths are correct. Nothing has
actually drifted. Equally, the rule is not simply wrong: it is answering the question it was asked,
and that question is genuinely useful for a plan mid-execution in a tree that is moving under it. The
defect is that the question stops being meaningful once the frozen base is no longer a plausible
baseline, and nothing in the system notices that transition.

VERIFIED NON-CAUSE, so the next investigator does not repeat the work. A finalized plan is NOT
scope-checked, so a leftover receipt for a plan already in `executed/` contributes ZERO findings.
Proven by experiment: 11 such receipts (15zvu6, 7nkcgp, plqjt7, c621h9, 8h9lap, w0ln4q, jxqdcw,
rygds7, i79rgh, uyd3lw, lbgzxg) were deleted and the counts did not move at all, staying at exactly
1025 for plans and 1106 for all. Every one of the 1013 findings comes from the 16 plans that are still
`approved` in `pending/` with unfilled V-items. This matters because the intuitive cleanup (sweep old
receipts) targets precisely the receipts that are harmless.

WHY THE OBVIOUS FIX IS NOT OBVIOUSLY RIGHT (REJECTED FRAMING). The first suggestion was to expire a
receipt when its base drifts too far from HEAD. The maintainer declined to accept that as the answer
without more thought, and there are concrete reasons it may be wrong. (1) A receipt IS execution
authority: `aw ipd finalize` refuses without a valid one, so expiring receipts silently revokes
permission for in-flight work, and 13 of these 16 belong to deferred lane branches plus the `wtiso`
stack that plan `wtisoland` (6knsrx) needs in order to resume. Expiry could strand exactly the work we
are trying to land. (2) "Too far" has no principled definition; commit distance, wall-clock age, and
semantic distance all disagree, and an arbitrary threshold turns a correctness gate into a heuristic.
(3) Expiry treats the SYMPTOM (noisy findings) rather than the question (what should a frozen base
mean when the tree has moved). (4) It interacts with worktree isolation: a lane's base is deliberately
NOT main's HEAD, so "far from HEAD" is the normal and correct state for an isolated turn.

QUESTIONS THE EXPLORATION MUST ANSWER, in rough priority order.
1. What is the frozen base actually FOR? Enumerate its consumers. At minimum it feeds
   `check.scope-drift`, `_paths_changed_by_this_execution` at finalize, and the intervening-commit
   collision check. Do they need the same base, or has one field been overloaded for three purposes?
2. Should scope-drift be evaluated against the frozen base at all, or against the merge-base of the
   frozen base and HEAD, or against the plan's own commits? Note plan `lbgzxg` (already executed) made
   a closely related change at the FINALIZE end, attributing by ownership rather than by mere
   dirtiness. The same reasoning may apply here, and its findings are worth reading first.
3. Should the rule emit one finding per file, or ONE finding per plan naming a count? The 116-to-158
   multiplication is what turns a real signal into unusable noise, independent of the base question.
4. Is a stale receipt a distinct STATE that deserves its own name and its own rule (for example
   `check.receipt-base-stale`, advisory), rather than being reported as drift? Reporting a stale
   baseline as scope drift is arguably a mislabelling, not just a volume problem.
5. What SHOULD happen when a plan holding a receipt is resumed after main moved? Re-issue silently,
   refuse and require an explicit re-begin, or re-base the receipt while preserving its attribution?
   Whatever is chosen must not strand the deferred lanes.
6. Does `aw doctor` or `aw attention` need to surface a stale-base receipt so it is visible before it
   turns into a thousand findings?

INTERIM DISPOSITION, so nobody "fixes" this by accident. The 20 remaining receipts are LEFT IN PLACE
deliberately. The finding count is cosmetic and resolves itself as the deferred lanes land. Do NOT
delete receipts for the 16 affected plans to quiet `aw check`; that would revoke authority for
unfinished work. Anyone reading a large scope-drift count on this repo should check first whether the
plan is unfinished with an old frozen base before treating it as a real violation.

RELATED. Plan lbgzxg, executed 2026-08-30, ownership-aware finalize attribution (the same class of
problem at the other end of the lifecycle). Plan wtisoland 6knsrx, which must resume the wtiso lanes
whose receipts are among the 16. Backlog xmqv5l, a different defect in the same receipt machinery
(begin freezes a whole-file digest so recording V evidence invalidates the receipt), which suggests
the receipt's contents deserve a broader look than this one rule.

DISCOVERED while triaging `aw check` after merging 15 lane branches by hand, following an overnight
run in which validation was disabled and 21 plans self-finalized inside their lanes without
integrating.
