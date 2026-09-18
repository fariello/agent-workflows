- Id: 10pcd5
- Status: open
- Blocks-Release: next
- Set: dirtygates
- Priority: medium
- Work-Kind: bug
- Summary: close_backlog_item cannot separate the tree the item moves in from the tree its release gate is evaluated against

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-16 created (aw backlog): found while executing dirtygates-03 (9iq461)

aw backlog set takes ONE --dir, and backlog.run_set derives BOTH of these from it via resolve_verb_repo_root:

  1. WHERE THE ITEM FILE MOVES (_resolve_backlog_root(repo_root) / new_status), and
  2. THE repo_root THE CLOSE-LEGITIMACY GATE EVALUATES AGAINST, because the --status done route calls check_engine.evaluate_blocking_close(repo_root, ...), which SCANS that tree for release-gate carriers (find_from_backlog_artifacts) and RESOLVES the --evidence citation in it (resolve_evidence_artifact).

So a caller that needs the move in one tree and the gate decision in another cannot express it. dirtygates-03 hit this: it performs the move in the lane worktree (so it rides the merge) while OQ-01 requires eligibility to be decided against main. It worked around it by taking the ELIGIBILITY decision itself in main before calling the setter, and by citing an evidence path valid in the lane.

MEASURED CONSEQUENCE OF THE COUPLING, from that plan's V-01 evidence: the same citation is asymmetric across the trees. The lane's executed/ path resolves in the lane and NOT in main; main's pending/ path resolves in main and NOT in the lane. So the SATISFIED arm's verdict for a release-gated item genuinely depends on which tree the setter ran against, which is a real (if currently benign) coupling between a filesystem layout and a release gate.

WHY IT IS CURRENTLY BENIGN, stated so nobody over-reacts: the runner cites the carrier path that exists in the tree the setter runs against, so the citation always resolves, and the HANDOFF arm is unaffected because find_from_backlog_artifacts keys on the - From-Backlog: FIELD rather than on the lifecycle bucket.

SUGGESTED FIX: give aw backlog set separate knobs, e.g. --dir for the move and a --gate-dir (defaulting to --dir) for the predicate, so a caller can state the split explicitly instead of encoding it in which path it cites. Touching check_engine/backlog is high blast radius (aw check and the pre-commit hook share the predicate), which is why 9iq461 deliberately did not.
