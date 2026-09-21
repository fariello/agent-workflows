- Id: sklbrt
- Status: open
- Set: sklbrt
- Priority: low
- Work-Kind: chore
- Summary: 19 of 36 specs carry no - Id: bullet, so they are unreachable by id6 selector and cannot be the target of any id6-keyed join

## Workflow history
- 2026-09-20 created (aw backlog): 19 of 36 specs carry no - Id: bullet, so they are unreachable by id6 selector and cannot be the target of any id6-keyed join

MEASURED 2026-09-20 at HEAD 96e93f8c by research survey vkub9o (plan si24ia).

WHAT IS WRONG. 19 of the 36 specs in .aw/records/specs/ carry NO `- Id:` front-matter bullet. THREE of those 19 are non-terminal and therefore live:
  20260808-1958-01-prompt-purity-lint      (approved)
  20260725-0957-01-external-delivery-and-skills   (deferred)
  20260726-1239-01-clean-delta-and-tracking-modes (deferred)
The other 16 are terminal (implemented/superseded).

Reproduce: parse `^- Id:` across `find .aw/records/specs -name "*.spec.md"` and cross-check `^- Status:`.

WHY IT MATTERS, AND WHY IT IS NOT A CONFORMANCE BUG. Pre-cutover legacy spec names are GRANDFATHERED by design (AGENTS.md), and `aw specs check` passes clean (exit 0) at this HEAD, so these files are not malformed. The consequence is narrower: an id6-less spec cannot be named by an id6 selector, cannot be the target of `- From-Spec:`, and could not be the target of any future `<spec-id6>.<req-id>` requirement join key. The 3 live ones block that today; the 19 figure is what tells a maintainer whether an id6-keyed scheme could ever address the HISTORICAL corpus, which it could not without minting 19 ids.

WHY IT IS FILED RATHER THAN FIXED. Minting ids for grandfathered legacy specs is a records change that needs maintainer authorization: it rewrites tracked history for 19 artifacts, and `aw rename specs <legacy> --to-id6` exists for exactly this conversion but choosing to run it over the corpus is a policy call, not a chore an executing agent may take. Plan si24ia recorded it as OQ-03 and deliberately did not fix it.

RECOMMENDED SCOPE IF ACTIONED. Convert only the 3 LIVE specs (cheap, and it unblocks any id6-keyed work), and leave the 16 terminal ones grandfathered unless a concrete consumer needs them.
