- Id: lsbd32
- Status: graduated
- Graduated-To: anycarrier
- Blocks-Release: next
- Set: anycarrier
- Priority: medium
- Work-Kind: bug
- Summary: The shared close predicate's HANDOFF arm closes on ANY executed carrier while the runner requires ALL of them, so the two disagree in one tree

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: 2o5wka
- 2026-09-28 created (aw backlog): The shared close predicate's HANDOFF arm closes on ANY executed carrier while the runner requires ALL of them, so the two disagree in one tree

MEASURED 2026-09-28 at HEAD fe6a1d1e in ONE tree, with NO lane and no --dir split involved, so this is NOT the 10pcd5 coupling and must not be folded into it.

Fixture: backlog item bbbbbb carrying '- Blocks-Release: next', with TWO From-Backlog IPD carriers at the same gate. Carrier cccccc sits in plans/executed/, carrier dddddd sits in plans/pending/.

  check_engine.evaluate_blocking_close(root, item, 'done')  -> legitimate=True
      reason: gate 'next' handed off to a From-Backlog plan or spec
  runner_shared.evaluate_backlog_close(root, 'bbbbbb', earned) -> close=False
      reason: IPD carrier(s) not executed: .aw/records/plans/pending/20260101-s-01-dddddd-p.ipd.md

So the two predicates apply DIFFERENT rules to the same facts. evaluate_blocking_close's HANDOFF arm RETURNS on the FIRST carrier it finds executed (its loop returns inside the for body, before any other carrier is examined), i.e. ANY-carrier semantics. runner_shared.evaluate_backlog_close collects every unexecuted IPD carrier and refuses if the list is non-empty, i.e. ALL-carrier semantics, and its own comment states the reason: 'measured at authoring, dh0uno has TWO carriers, so that rule would have closed it while half its work was unwritten.'

WHY THIS MATTERS. evaluate_blocking_close is the predicate that backs the SETTER, 'aw check' rule check.blocking-item-closed-without-gate, and the opt-in pre-commit hook. So a HAND close (an agent or human running 'aw backlog set <item> --status done' directly, with no runner) of a multi-carrier gated item is ACCEPTED as soon as one carrier executes, and the remaining carriers' work is never written. The runner is protected by its own stricter outer predicate; a hand close is not.

CORPUS MEASUREMENT at the same HEAD: 653 backlog items, 349 carrying Blocks-Release, 255 with at least one carrier, 31 with MORE than one carrier, and 16 with more than one carrier AND a release gate. Carrier-count distribution {1: 224, 2: 14, 3: 3, 4: 8, 5: 3, 6: 1, 9: 2}. So 16 live gated items are exposed to the permissive arm today, with a tail of 9.

RELATION TO rwhbci (done, closescope 2a6phj). That item raised the adjacent question of whether a carrier's SCOPE covers the whole item, and the maintainer's 2026-09-26 ruling added the executed-carrier requirement. The ruling made the arm require an executed carrier; it did not make it require EVERY carrier, which is the residual gap measured here. The refusal message the same function emits when NO carrier is executed already names every carrier it found, so the function has the full list in hand and returns early anyway.

SUGGESTED FIX: make the HANDOFF arm require every same-gate carrier to be executed/implemented, matching the runner, rather than returning on the first. That is a TIGHTENING of a release gate, so it needs a maintainer decision on whether to grandfather the existing 16 exposed items, and it touches the high-blast-radius shared predicate (setter, aw check, pre-commit hook), which is why it is filed rather than fixed opportunistically.
